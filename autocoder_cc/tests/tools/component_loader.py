"""Load and wire components for testing."""
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from autocoder_cc.observability import get_logger
from autocoder_cc.tests.tools.message_bus import MessageBus

class ComponentLoader:
    """Load and wire components dynamically."""
    
    def __init__(self, message_bus: Optional[MessageBus] = None):
        self.logger = get_logger("ComponentLoader")
        self.message_bus = message_bus or MessageBus()
        self.components: Dict[str, Any] = {}
        
    def load_component_from_file(self, file_path: Path, 
                                 component_name: str) -> Any:
        """Load a component from a Python file."""
        self.logger.info(f"Loading {component_name} from {file_path}")
        
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(
            component_name, file_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find component class (assumes it matches component_name)
        component_class = getattr(module, component_name, None)
        if not component_class:
            # Try to find any class that looks like a component
            for name, obj in module.__dict__.items():
                if (isinstance(obj, type) and 
                    name.lower() == component_name.lower()):
                    component_class = obj
                    break
        
        if not component_class:
            raise ValueError(f"Cannot find component {component_name} in {file_path}")
        
        # Instantiate component
        component = component_class(component_name, {})
        self.components[component_name] = component
        
        return component
    
    def wire_components(self, connections: List[Tuple[str, str]]):
        """Wire components together based on connection list."""
        for source_name, target_name in connections:
            source = self.components.get(source_name)
            target = self.components.get(target_name)
            
            if not source or not target:
                self.logger.error(f"Cannot wire {source_name} → {target_name}")
                continue
            
            # Connect via message bus
            topic = f"{source_name}_to_{target_name}"
            
            # Source publishes to topic
            if hasattr(source, 'set_output_handler'):
                source.set_output_handler(
                    lambda msg: self.message_bus.publish(topic, msg)
                )
            
            # Target subscribes to topic
            if hasattr(target, 'set_input_handler'):
                self.message_bus.subscribe(topic, target.process)
            
            self.logger.info(f"Wired {source_name} → {target_name}")
    
    def get_component(self, name: str) -> Any:
        """Get loaded component by name."""
        return self.components.get(name)
    
    def list_components(self) -> List[str]:
        """List all loaded components."""
        return list(self.components.keys())