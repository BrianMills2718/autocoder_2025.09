"""Real port implementation with async message passing."""
import anyio
from typing import Optional, List, Any, Callable
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from autocoder_cc.observability import get_logger

class Port(ABC):
    """Abstract base class for ports."""
    
    def __init__(self, name: str, max_queue_size: int = 1000):
        self.name = name
        self.logger = get_logger(f"Port.{name}")
        self.connected_ports: List['Port'] = []
        self.max_queue_size = max_queue_size
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_dropped': 0,
            'connection_time': None
        }
    
    @abstractmethod
    async def connect(self, other_port: 'Port') -> bool:
        """Connect to another port."""
        pass
    
    def disconnect(self):
        """Disconnect from all ports."""
        for port in self.connected_ports:
            if self in port.connected_ports:
                port.connected_ports.remove(self)
        self.connected_ports.clear()
        self.logger.info(f"Port {self.name} disconnected")
    
    def is_connected(self) -> bool:
        """Check if port is connected."""
        return len(self.connected_ports) > 0


class InputPort(Port):
    """Input port that receives messages."""
    
    def __init__(self, name: str, max_queue_size: int = 1000):
        super().__init__(name, max_queue_size)
        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(max_buffer_size=max_queue_size)
        self.handler: Optional[Callable] = None
        self._receiver_task = None
        
    async def connect(self, output_port: 'OutputPort') -> bool:
        """Connect to an output port."""
        if not isinstance(output_port, OutputPort):
            self.logger.error(f"Cannot connect InputPort to {type(output_port)}")
            return False
        
        # Let the output port handle the connection
        return await output_port.connect(self)
    
    async def receive(self) -> Any:
        """Receive next message from queue."""
        try:
            # Use receive_nowait() for true non-blocking receive
            message = self.receive_stream.receive_nowait()
            self.stats['messages_received'] += 1
            return message
        except anyio.WouldBlock:
            return None
        except anyio.ClosedResourceError:
            # Stream was closed
            return None
    
    async def _put_message(self, message: Any) -> bool:
        """Internal method for OutputPort to send messages."""
        try:
            # Try non-blocking send
            self.send_stream.send_nowait(message)
            self.stats['messages_received'] += 1
            return True
        except anyio.WouldBlock:  # This exists for send_nowait!
            self.stats['messages_dropped'] += 1
            self.logger.warning(f"Queue full on {self.name}, dropping message")
            return False
        except anyio.ClosedResourceError:
            self.logger.error(f"Port {self.name} is closed")
            return False
    
    def set_handler(self, handler: Callable):
        """Set message handler callback."""
        self.handler = handler
        self.logger.debug(f"Handler set for {self.name}")
    
    def queue_size(self) -> int:
        """Get current queue size."""
        # Memory streams don't expose queue size directly
        # Return 0 for now (this is a limitation of anyio memory streams)
        return 0  # TODO: Track manually if size is critical


class OutputPort(Port):
    """Output port that sends messages."""
    
    def __init__(self, name: str):
        super().__init__(name)
        
    async def connect(self, input_port: InputPort) -> bool:
        """Connect to an input port."""
        if not isinstance(input_port, InputPort):
            self.logger.error(f"OutputPort can only connect to InputPort, not {type(input_port)}")
            return False
        
        if input_port not in self.connected_ports:
            self.connected_ports.append(input_port)
            if self not in input_port.connected_ports:
                input_port.connected_ports.append(self)
            
            self.stats['connection_time'] = datetime.now()
            self.logger.info(f"Connected {self.name} → {input_port.name}")
            return True
        
        return False
    
    async def send(self, message: Any) -> int:
        """Send message to all connected input ports."""
        if not self.connected_ports:
            self.logger.warning(f"No connections on {self.name}, message dropped")
            self.stats['messages_dropped'] += 1
            return 0
        
        sent_count = 0
        for port in self.connected_ports:
            if isinstance(port, InputPort):
                success = await port._put_message(message)
                if success:
                    sent_count += 1
                    self.stats['messages_sent'] += 1
        
        return sent_count
    
    async def broadcast(self, message: Any) -> int:
        """Broadcast message to all connected ports."""
        return await self.send(message)
    
    def connected_count(self) -> int:
        """Get number of connected ports."""
        return len(self.connected_ports)