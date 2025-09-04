#!/usr/bin/env python3
"""
Port infrastructure for typed, validated component communication.
Ports wrap anyio streams with schema validation using Pydantic.

This is Phase 1 of the migration to port-based architecture.
"""
from typing import TypeVar, Generic, Type, Optional, Any
from pydantic import BaseModel, ValidationError
import anyio
from anyio import create_memory_object_stream
from anyio.abc import ObjectSendStream, ObjectReceiveStream


# Type variable for generic port schemas
T = TypeVar('T', bound=BaseModel)


class PortError(Exception):
    """Base exception for port-related errors"""
    pass


class PortValidationError(PortError):
    """Raised when data fails schema validation"""
    pass


class PortClosedError(PortError):
    """Raised when trying to use a closed port"""
    pass


class Port(Generic[T]):
    """
    Base Port class - a typed, validated interface to a stream.
    
    Ports enforce contracts that raw streams don't care about:
    - Type validation using Pydantic schemas
    - Data transformation and coercion
    - Error handling and reporting
    """
    
    def __init__(self, 
                 name: str,
                 schema: Type[T],
                 buffer_size: int = 1000):
        """
        Initialize a port.
        
        Args:
            name: Port identifier
            schema: Pydantic model for validation
            buffer_size: Maximum items in buffer (for backpressure)
        """
        self.name = name
        self.schema = schema
        self.buffer_size = buffer_size
        self.stream: Optional[Any] = None  # Will be ObjectSendStream or ObjectReceiveStream
        self._closed = False
    
    def __str__(self) -> str:
        """String representation of port"""
        return f"Port({self.name}, {self.schema.__name__})"
    
    def __eq__(self, other) -> bool:
        """Ports are equal if they have same name and schema"""
        if not isinstance(other, Port):
            return False
        return self.name == other.name and self.schema == other.schema
    
    def _validate_data(self, data: Any) -> T:
        """
        Validate and coerce data to schema.
        
        Args:
            data: Data to validate
            
        Returns:
            Validated data as schema instance
            
        Raises:
            PortValidationError: If validation fails
        """
        if isinstance(data, self.schema):
            return data
        
        try:
            # Try to coerce to correct type
            if isinstance(data, dict):
                return self.schema(**data)
            else:
                return self.schema(data)
        except (ValidationError, TypeError) as e:
            raise PortValidationError(
                f"Port {self.name}: Failed to validate data against {self.schema.__name__}: {e}"
            )


class OutputPort(Port[T]):
    """
    Output port for sending data.
    Validates data before sending through stream.
    """
    
    def __init__(self, 
                 name: str,
                 schema: Type[T],
                 buffer_size: int = 1000):
        super().__init__(name, schema, buffer_size)
        self.stream: Optional[ObjectSendStream] = None
    
    async def send(self, data: Any) -> None:
        """
        Send data through port with validation.
        
        Args:
            data: Data to send (will be validated against schema)
            
        Raises:
            PortValidationError: If data doesn't match schema
            PortClosedError: If port is closed
            AttributeError: If stream not connected
        """
        if self._closed:
            raise PortClosedError(f"Port {self.name} is closed")
        
        # Validate data
        validated_data = self._validate_data(data)
        
        # Send through stream
        if self.stream is None:
            raise AttributeError(f"Port {self.name} has no connected stream")
        
        await self.stream.send(validated_data)
    
    async def close(self) -> None:
        """Close the output port"""
        if self.stream and not self._closed:
            await self.stream.aclose()
        self._closed = True


class InputPort(Port[T]):
    """
    Input port for receiving data.
    Validates received data matches expected schema.
    Implements async iteration for easy consumption.
    """
    
    def __init__(self, 
                 name: str,
                 schema: Type[T],
                 buffer_size: int = 1000):
        super().__init__(name, schema, buffer_size)
        self.stream: Optional[ObjectReceiveStream] = None
    
    def __aiter__(self):
        """Make InputPort async iterable"""
        return self
    
    async def __anext__(self) -> T:
        """Get next item from stream for async iteration"""
        try:
            return await self.receive()
        except PortClosedError:
            raise StopAsyncIteration
    
    async def receive(self, timeout: Optional[float] = None) -> T:
        """
        Receive data from port.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Validated data matching schema
            
        Raises:
            PortClosedError: If port is closed or stream ends
            TimeoutError: If timeout expires
            AttributeError: If stream not connected
        """
        if self._closed:
            raise PortClosedError(f"Port {self.name} is closed")
        
        if self.stream is None:
            raise AttributeError(f"Port {self.name} has no connected stream")
        
        try:
            if timeout is not None:
                # Use anyio's move_on_after for timeout
                with anyio.move_on_after(timeout) as cancel_scope:
                    raw_data = await self.stream.receive()
                
                if cancel_scope.cancelled_caught:
                    raise TimeoutError(f"Receive timeout on port {self.name}")
            else:
                raw_data = await self.stream.receive()
        except (anyio.ClosedResourceError, anyio.EndOfStream):
            raise PortClosedError(f"Port {self.name} stream closed")
        
        # Validate received data
        return self._validate_data(raw_data)
    
    async def close(self) -> None:
        """Close the input port"""
        if self.stream and not self._closed:
            await self.stream.aclose()
        self._closed = True


def create_connected_ports(output_port: OutputPort[T], 
                          input_port: InputPort[T],
                          buffer_size: Optional[int] = None) -> None:
    """
    Connect an output port to an input port via anyio streams.
    
    Args:
        output_port: Port to send data from
        input_port: Port to receive data at
        buffer_size: Optional buffer size (uses port's buffer_size if not specified)
    """
    # Use the smaller of the two port buffer sizes if not specified
    if buffer_size is None:
        buffer_size = min(output_port.buffer_size, input_port.buffer_size)
    
    # Create anyio memory object stream pair
    send_stream, receive_stream = create_memory_object_stream(max_buffer_size=buffer_size)
    
    # Connect streams to ports
    output_port.stream = send_stream
    input_port.stream = receive_stream


class PortRegistry:
    """
    Registry for managing ports in a component.
    Helps with port discovery and management.
    """
    
    def __init__(self):
        self.input_ports: dict[str, InputPort] = {}
        self.output_ports: dict[str, OutputPort] = {}
    
    def add_input_port(self, name: str, schema: Type[BaseModel], buffer_size: int = 1000) -> InputPort:
        """
        Add an input port to the registry.
        
        Args:
            name: Port name
            schema: Pydantic schema for validation
            buffer_size: Buffer size for backpressure
            
        Returns:
            Created input port
        """
        port = InputPort(name, schema, buffer_size)
        self.input_ports[name] = port
        return port
    
    def add_output_port(self, name: str, schema: Type[BaseModel], buffer_size: int = 1000) -> OutputPort:
        """
        Add an output port to the registry.
        
        Args:
            name: Port name
            schema: Pydantic schema for validation
            buffer_size: Buffer size for backpressure
            
        Returns:
            Created output port
        """
        port = OutputPort(name, schema, buffer_size)
        self.output_ports[name] = port
        return port
    
    def get_input_port(self, name: str) -> Optional[InputPort]:
        """Get input port by name"""
        return self.input_ports.get(name)
    
    def get_output_port(self, name: str) -> Optional[OutputPort]:
        """Get output port by name"""
        return self.output_ports.get(name)
    
    async def close_all(self) -> None:
        """Close all ports in registry"""
        for port in self.input_ports.values():
            await port.close()
        for port in self.output_ports.values():
            await port.close()


def create_port_pair(name: str, schema: Type[T], buffer_size: int = 1000) -> tuple[OutputPort[T], InputPort[T]]:
    """
    Create a connected pair of ports (output and input).
    
    This creates the underlying anyio memory object stream and wraps
    both ends in appropriate port objects.
    
    Args:
        name: Base name for the ports
        schema: Pydantic schema for validation (or dict for unvalidated)
        buffer_size: Size of the buffer between ports
        
    Returns:
        Tuple of (output_port, input_port) that are connected
    """
    from anyio import create_memory_object_stream
    
    # Create the underlying stream
    send_stream, receive_stream = create_memory_object_stream(buffer_size)
    
    # Create ports wrapping the streams
    output_port = OutputPort(f"{name}_out", schema, buffer_size)
    input_port = InputPort(f"{name}_in", schema, buffer_size)
    
    # Connect the streams
    output_port.stream = send_stream
    input_port.stream = receive_stream
    
    return output_port, input_port
