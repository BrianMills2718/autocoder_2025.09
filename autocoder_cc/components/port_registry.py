"""Port registry for discovery and connection management."""
from typing import Dict, List, Any, Optional, Tuple
from autocoder_cc.components.primitives import Primitive
from autocoder_cc.observability import get_logger

class PortInfo:
    """Information about a port."""
    def __init__(self, direction: str, data_type: str, required: bool = True, buffer_size: int = 1024):
        self.direction = direction  # "input" or "output"
        self.data_type = data_type
        self.required = required
        self.buffer_size = buffer_size

class PortRegistry:
    """Central registry for port discovery."""
    
    def __init__(self):
        self.components = {}
        self.connections = []
        self.logger = get_logger("PortRegistry")
    
    def register_component(self, component: Primitive) -> None:
        """Register a component and its ports."""
        # Components should implement get_port_manifest()
        if hasattr(component, 'get_port_manifest'):
            manifest = component.get_port_manifest()
        else:
            # Discover ports by inspection
            manifest = self._discover_ports(component)
        
        self.components[component.name] = {
            "instance": component,
            "ports": manifest
        }
        self.logger.info(f"Registered component {component.name} with {len(manifest)} ports")
    
    def _discover_ports(self, component: Primitive) -> Dict[str, PortInfo]:
        """Discover ports by inspecting component attributes."""
        ports = {}
        for attr_name in dir(component):
            if attr_name.startswith('in_'):
                ports[attr_name] = PortInfo("input", "Any")
            elif attr_name.startswith('out_'):
                ports[attr_name] = PortInfo("output", "Any")
            elif attr_name.startswith('err_'):
                ports[attr_name] = PortInfo("output", "Error")
        return ports
    
    def discover_ports(self, component_name: Optional[str] = None) -> Dict:
        """Discover available ports."""
        if component_name:
            return self.components.get(component_name, {}).get("ports", {})
        return {name: comp["ports"] for name, comp in self.components.items()}
    
    def find_compatible_ports(self, source_component: str, source_port: str) -> List[Tuple[str, str]]:
        """Find ports compatible with the given output port."""
        compatible = []
        source_info = self.components.get(source_component, {}).get("ports", {}).get(source_port)
        
        if not source_info or source_info.direction != "output":
            return compatible
        
        for comp_name, comp_info in self.components.items():
            if comp_name == source_component:
                continue
            for port_name, port_info in comp_info["ports"].items():
                if port_info.direction == "input":
                    # Check type compatibility
                    if self._are_types_compatible(source_info.data_type, port_info.data_type):
                        compatible.append((comp_name, port_name))
        
        return compatible
    
    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if two types are compatible."""
        if target_type == "Any":
            return True
        if source_type == target_type:
            return True
        # Add more sophisticated type checking here
        return False