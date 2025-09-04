"""Connection manager for port-based component wiring."""
from typing import Dict, List, Any, Optional, Tuple
import anyio
from anyio import create_memory_object_stream
from autocoder_cc.components.port_registry import PortRegistry, PortInfo
from autocoder_cc.components.primitives import Primitive
from autocoder_cc.observability import get_logger

class Connection:
    """Represents a connection between two ports."""
    
    def __init__(self, source_component: str, source_port: str, 
                 target_component: str, target_port: str,
                 buffer_size: int = 1024):
        self.source = (source_component, source_port)
        self.target = (target_component, target_port)
        self.send_stream, self.receive_stream = create_memory_object_stream(buffer_size)
        self.active = False
        self.messages_sent = 0
        self.messages_received = 0
        
    async def send(self, message: Any):
        """Send message through connection."""
        await self.send_stream.send(message)
        self.messages_sent += 1
        
    async def receive(self):
        """Receive message from connection."""
        message = await self.receive_stream.receive()
        self.messages_received += 1
        return message
        
    def close(self):
        """Close the connection."""
        self.send_stream.close()
        self.receive_stream.close()
        self.active = False

class ConnectionManager:
    """Manages connections between component ports."""
    
    def __init__(self):
        self.registry = PortRegistry()
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.logger = get_logger("ConnectionManager")
        
    def register_component(self, component: Primitive):
        """Register a component with the manager."""
        self.registry.register_component(component)
        self.logger.info(f"Registered component: {component.name}")
        
    async def connect_ports(self, source_component: str, source_port: str,
                           target_component: str, target_port: str,
                           buffer_size: int = 1024) -> Connection:
        """Create a connection between two ports."""
        # Validate ports exist and are compatible
        source_ports = self.registry.discover_ports(source_component)
        target_ports = self.registry.discover_ports(target_component)
        
        if not source_ports or source_port not in source_ports:
            raise ValueError(f"Source port {source_component}.{source_port} not found")
        if not target_ports or target_port not in target_ports:
            raise ValueError(f"Target port {target_component}.{target_port} not found")
            
        # Check compatibility
        compatible = self.registry.find_compatible_ports(source_component, source_port)
        if (target_component, target_port) not in compatible:
            self.logger.warning(f"Ports may not be compatible: {source_port} -> {target_port}")
            
        # Create connection
        conn = Connection(source_component, source_port, target_component, target_port, buffer_size)
        conn.active = True
        
        # Store connection
        key = (f"{source_component}.{source_port}", f"{target_component}.{target_port}")
        self.connections[key] = conn
        
        self.logger.info(f"Connected: {source_component}.{source_port} -> {target_component}.{target_port}")
        return conn
        
    def get_connection(self, source_component: str, source_port: str,
                       target_component: str, target_port: str) -> Optional[Connection]:
        """Get an existing connection."""
        key = (f"{source_component}.{source_port}", f"{target_component}.{target_port}")
        return self.connections.get(key)
        
    def disconnect_all(self):
        """Disconnect all connections."""
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()
        self.logger.info("All connections closed")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        stats = {
            "total_connections": len(self.connections),
            "active_connections": sum(1 for c in self.connections.values() if c.active),
            "total_messages": sum(c.messages_sent for c in self.connections.values()),
            "connections": []
        }
        
        for key, conn in self.connections.items():
            stats["connections"].append({
                "route": f"{key[0]} -> {key[1]}",
                "active": conn.active,
                "sent": conn.messages_sent,
                "received": conn.messages_received
            })
            
        return stats