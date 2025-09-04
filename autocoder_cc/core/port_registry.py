#!/usr/bin/env python3
"""
Port Registry - Centralized port management for system generation
Implements Phase 2A: Single source of truth for port allocation and coordination
"""

import random
import threading
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass, field
from autocoder_cc.observability import get_logger

logger = get_logger(__name__)

@dataclass
class PortAllocation:
    """Represents a port allocation for a component"""
    component_name: str
    port: int
    allocated_at: float
    system_id: Optional[str] = None
    component_type: Optional[str] = None
    
    def __post_init__(self):
        import time
        if not hasattr(self, 'allocated_at') or self.allocated_at is None:
            self.allocated_at = time.time()

class PortRegistry:
    """
    Centralized port allocation and management system
    
    Features:
    - Thread-safe port allocation
    - Conflict detection and resolution
    - Port availability validation
    - Cleanup on system generation failure
    - Reserved port ranges for different component types
    """
    
    def __init__(self, 
                 port_range_start: int = 8000,
                 port_range_end: int = 65535,
                 reserved_ports: Optional[Set[int]] = None):
        """
        Initialize port registry with configurable port ranges
        
        Args:
            port_range_start: Starting port for allocation range
            port_range_end: Ending port for allocation range  
            reserved_ports: Set of ports that should never be allocated
        """
        self.port_range_start = port_range_start
        self.port_range_end = port_range_end
        self.reserved_ports = reserved_ports or {
            22, 80, 443, 3306, 5432, 6379, 8080, 9090, 9200, 9300
        }
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._allocated_ports: Dict[int, PortAllocation] = {}
        self._component_ports: Dict[str, int] = {}
        self._system_ports: Dict[str, List[int]] = {}
        
        logger.info(f"PortRegistry initialized: range {port_range_start}-{port_range_end}, "
                   f"reserved {len(self.reserved_ports)} ports")
    
    def allocate_port(self, 
                     component_name: str,
                     component_type: Optional[str] = None,
                     system_id: Optional[str] = None,
                     preferred_port: Optional[int] = None) -> int:
        """
        Allocate a unique port for a component
        
        Args:
            component_name: Name of the component requesting port
            component_type: Type of component (APIEndpoint, WebSocket, etc.)
            system_id: ID of the system this component belongs to
            preferred_port: Preferred port number (if available)
            
        Returns:
            Allocated port number
            
        Raises:
            RuntimeError: If no ports are available
        """
        with self._lock:
            # Check if component already has a port allocated
            if component_name in self._component_ports:
                existing_port = self._component_ports[component_name]
                logger.info(f"Component '{component_name}' already has port {existing_port}")
                return existing_port
            
            # Try preferred port first
            if preferred_port and self._is_port_available(preferred_port):
                port = preferred_port
                logger.info(f"Allocated preferred port {port} for {component_name}")
            else:
                # Find next available port
                port = self._find_available_port(component_type)
                if port is None:
                    raise RuntimeError(f"No available ports for component '{component_name}'")
                
                logger.info(f"Allocated port {port} for {component_name} ({component_type})")
            
            # Record allocation
            allocation = PortAllocation(
                component_name=component_name,
                port=port,
                allocated_at=0,  # Will be set in __post_init__
                system_id=system_id,
                component_type=component_type
            )
            
            self._allocated_ports[port] = allocation
            self._component_ports[component_name] = port
            
            # Track system-level allocations
            if system_id:
                if system_id not in self._system_ports:
                    self._system_ports[system_id] = []
                self._system_ports[system_id].append(port)
            
            return port
    
    def deallocate_port(self, port: int) -> bool:
        """
        Deallocate a specific port
        
        Args:
            port: Port number to deallocate
            
        Returns:
            True if port was deallocated, False if not allocated
        """
        with self._lock:
            if port not in self._allocated_ports:
                logger.warning(f"Attempted to deallocate unallocated port {port}")
                return False
            
            allocation = self._allocated_ports[port]
            component_name = allocation.component_name
            system_id = allocation.system_id
            
            # Remove from all tracking structures
            del self._allocated_ports[port]
            if component_name in self._component_ports:
                del self._component_ports[component_name]
            
            if system_id and system_id in self._system_ports:
                if port in self._system_ports[system_id]:
                    self._system_ports[system_id].remove(port)
                if not self._system_ports[system_id]:
                    del self._system_ports[system_id]
            
            logger.info(f"Deallocated port {port} from component '{component_name}'")
            return True
    
    def deallocate_component(self, component_name: str) -> bool:
        """
        Deallocate port for a specific component
        
        Args:
            component_name: Name of component to deallocate
            
        Returns:
            True if component port was deallocated, False if not found
        """
        with self._lock:
            if component_name not in self._component_ports:
                logger.warning(f"Component '{component_name}' has no allocated port")
                return False
            
            port = self._component_ports[component_name]
            return self.deallocate_port(port)
    
    def cleanup_system(self, system_id: str) -> int:
        """
        Clean up all port allocations for a system
        
        Args:
            system_id: System ID to clean up
            
        Returns:
            Number of ports deallocated
        """
        with self._lock:
            if system_id not in self._system_ports:
                logger.info(f"No ports allocated for system '{system_id}'")
                return 0
            
            ports_to_cleanup = self._system_ports[system_id].copy()
            deallocated_count = 0
            
            for port in ports_to_cleanup:
                if self.deallocate_port(port):
                    deallocated_count += 1
            
            logger.info(f"Cleaned up {deallocated_count} ports for system '{system_id}'")
            return deallocated_count
    
    def get_component_port(self, component_name: str) -> Optional[int]:
        """
        Get allocated port for a component
        
        Args:
            component_name: Name of component
            
        Returns:
            Port number if allocated, None otherwise
        """
        with self._lock:
            return self._component_ports.get(component_name)
    
    def get_system_ports(self, system_id: str) -> List[int]:
        """
        Get all allocated ports for a system
        
        Args:
            system_id: System ID
            
        Returns:
            List of allocated port numbers
        """
        with self._lock:
            return self._system_ports.get(system_id, []).copy()
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available for allocation
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        with self._lock:
            return self._is_port_available(port)
    
    def get_allocation_info(self, port: int) -> Optional[PortAllocation]:
        """
        Get allocation information for a port
        
        Args:
            port: Port number
            
        Returns:
            PortAllocation object if port is allocated, None otherwise
        """
        with self._lock:
            return self._allocated_ports.get(port)
    
    def get_allocated_ports(self) -> Dict[int, PortAllocation]:
        """
        Get all currently allocated ports
        
        Returns:
            Dictionary mapping port numbers to PortAllocation objects
        """
        with self._lock:
            return self._allocated_ports.copy()
    
    def validate_port_availability(self, ports: List[int]) -> Tuple[List[int], List[int]]:
        """
        Validate availability of multiple ports
        
        Args:
            ports: List of port numbers to validate
            
        Returns:
            Tuple of (available_ports, unavailable_ports)
        """
        with self._lock:
            available = []
            unavailable = []
            
            for port in ports:
                if self._is_port_available(port):
                    available.append(port)
                else:
                    unavailable.append(port)
            
            return available, unavailable
    
    def _is_port_available(self, port: int) -> bool:
        """Internal method to check port availability (not thread-safe)"""
        if port < self.port_range_start or port > self.port_range_end:
            return False
        if port in self.reserved_ports:
            return False
        if port in self._allocated_ports:
            return False
        return True
    
    def _find_available_port(self, component_type: Optional[str] = None) -> Optional[int]:
        """
        Find next available port in range
        
        Args:
            component_type: Component type for port range optimization
            
        Returns:
            Available port number or None if no ports available
        """
        # Component type specific port ranges for better organization
        if component_type == "APIEndpoint":
            search_start = 8000
            search_end = 8999
        elif component_type == "WebSocket":
            search_start = 9000
            search_end = 9999
        else:
            search_start = self.port_range_start
            search_end = self.port_range_end
        
        # Ensure search range is within overall range
        search_start = max(search_start, self.port_range_start)
        search_end = min(search_end, self.port_range_end)
        
        # Random starting point to avoid clustering
        start_port = random.randint(search_start, search_end)
        
        # Search from random start to end of range
        for port in range(start_port, search_end + 1):
            if self._is_port_available(port):
                return port
        
        # Search from beginning of range to random start
        for port in range(search_start, start_port):
            if self._is_port_available(port):
                return port
        
        return None
    
    def __str__(self) -> str:
        """String representation of port registry status"""
        with self._lock:
            allocated_count = len(self._allocated_ports)
            systems_count = len(self._system_ports)
            return (f"PortRegistry(allocated={allocated_count}, "
                   f"systems={systems_count}, "
                   f"range={self.port_range_start}-{self.port_range_end})")


# Global port registry instance
_port_registry: Optional[PortRegistry] = None
_registry_lock = threading.Lock()

def get_port_registry() -> PortRegistry:
    """
    Get global port registry instance (singleton pattern)
    
    Returns:
        Global PortRegistry instance
    """
    global _port_registry
    
    if _port_registry is None:
        with _registry_lock:
            if _port_registry is None:
                _port_registry = PortRegistry()
                logger.info("Global PortRegistry instance created")
    
    return _port_registry

def reset_port_registry() -> None:
    """
    Reset global port registry (primarily for testing)
    """
    global _port_registry
    
    with _registry_lock:
        _port_registry = None
        logger.info("Global PortRegistry instance reset")