#!/usr/bin/env python3
"""
PortBasedComponent - Base class for components using port-based architecture.
Phase 2 of the migration to port-based architecture.

Components inherit from this class and:
1. Declare their ports in configure_ports()
2. Process data in process() method
3. Use ports for all communication
"""
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, Any
from pydantic import BaseModel

from autocoder_cc.components.ports import InputPort, OutputPort, PortRegistry


class PortBasedComponent(ABC):
    """
    Abstract base class for port-based components.
    
    Components using this base class communicate exclusively through
    typed ports, ensuring type safety and clear data flow.
    """
    
    def __init__(self, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a port-based component.
        
        Args:
            name: Component name (defaults to class name)
            config: Optional configuration dictionary
        """
        self.name = name or self.__class__.__name__
        self.config = config or {}
        
        # Port registries
        self.input_ports: Dict[str, InputPort] = {}
        self.output_ports: Dict[str, OutputPort] = {}
        
        # Configure ports defined by subclass
        self.configure_ports()
        
        # Component state
        self._running = False
        self._setup_complete = False
    
    @abstractmethod
    def configure_ports(self):
        """
        Configure the component's input and output ports.
        
        Subclasses must implement this to declare their ports using:
        - self.add_input_port(name, schema)
        - self.add_output_port(name, schema)
        """
        pass
    
    def add_input_port(self, name: str, schema: Type[BaseModel], buffer_size: int = 1000) -> InputPort:
        """
        Add an input port to the component.
        
        Args:
            name: Port name
            schema: Pydantic model for validation
            buffer_size: Buffer size for backpressure
            
        Returns:
            Created input port
        """
        port = InputPort(name, schema, buffer_size)
        self.input_ports[name] = port
        return port
    
    def add_output_port(self, name: str, schema: Type[BaseModel], buffer_size: int = 1000) -> OutputPort:
        """
        Add an output port to the component.
        
        Args:
            name: Port name  
            schema: Pydantic model for validation
            buffer_size: Buffer size for backpressure
            
        Returns:
            Created output port
        """
        port = OutputPort(name, schema, buffer_size)
        self.output_ports[name] = port
        return port
    
    async def setup(self):
        """
        Setup the component before processing.
        
        Override this to add initialization logic.
        Always call super().setup() when overriding.
        """
        self._setup_complete = True
    
    async def cleanup(self):
        """
        Clean up the component after processing.
        
        Override this to add cleanup logic.
        Always call super().cleanup() when overriding.
        """
        # Close all ports
        for port in self.input_ports.values():
            await port.close()
        for port in self.output_ports.values():
            await port.close()
        
        self._running = False
        self._setup_complete = False
    
    async def process(self):
        """
        Main processing loop for the component.
        
        Override this to implement component logic.
        Typically iterates over input ports and sends to output ports.
        
        Example:
            async for data in self.input_ports["input"]:
                result = self.transform(data)
                await self.output_ports["output"].send(result)
        """
        # Default implementation for testing
        # Real components must override this
        pass
    
    async def run(self):
        """
        Run the component with proper lifecycle management.
        
        Handles setup, processing, and cleanup automatically.
        """
        try:
            # Setup
            if not self._setup_complete:
                await self.setup()
            
            # Mark as running
            self._running = True
            
            # Process
            await self.process()
            
        finally:
            # Always cleanup
            await self.cleanup()
    
    def is_running(self) -> bool:
        """Check if component is currently running"""
        return self._running
    
    def __str__(self) -> str:
        """String representation of component"""
        input_names = list(self.input_ports.keys())
        output_names = list(self.output_ports.keys())
        return (
            f"{self.__class__.__name__}(name='{self.name}', "
            f"inputs={input_names}, outputs={output_names})"
        )
    
    def __repr__(self) -> str:
        """Detailed representation of component"""
        return self.__str__()


class PassThroughComponent(PortBasedComponent):
    """
    Simple pass-through component for testing.
    Forwards input directly to output without modification.
    """
    
    def configure_ports(self):
        """Single input and output port"""
        # These will be configured by the user
        pass
    
    async def process(self):
        """Forward input to output"""
        if "input" in self.input_ports and "output" in self.output_ports:
            async for data in self.input_ports["input"]:
                await self.output_ports["output"].send(data)


class FilterComponent(PortBasedComponent):
    """
    Base class for components that filter data.
    """
    
    def configure_ports(self):
        """Input port and filtered output port"""
        # Subclasses should call super() and add their specific ports
        pass
    
    @abstractmethod
    async def should_pass(self, data: Any) -> bool:
        """
        Determine if data should pass through filter.
        
        Args:
            data: Input data to check
            
        Returns:
            True if data should pass, False otherwise
        """
        pass
    
    async def process(self):
        """Filter data based on should_pass method"""
        if "input" in self.input_ports and "output" in self.output_ports:
            async for data in self.input_ports["input"]:
                if await self.should_pass(data):
                    await self.output_ports["output"].send(data)


class TransformComponent(PortBasedComponent):
    """
    Base class for components that transform data.
    """
    
    def configure_ports(self):
        """Input and output ports for transformation"""
        # Subclasses should call super() and add their specific ports
        pass
    
    @abstractmethod
    async def transform(self, data: Any) -> Any:
        """
        Transform input data to output data.
        
        Args:
            data: Input data
            
        Returns:
            Transformed data
        """
        pass
    
    async def process(self):
        """Transform data using transform method"""
        if "input" in self.input_ports and "output" in self.output_ports:
            async for data in self.input_ports["input"]:
                result = await self.transform(data)
                await self.output_ports["output"].send(result)
