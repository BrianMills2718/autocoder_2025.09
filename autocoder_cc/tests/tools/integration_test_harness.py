#!/usr/bin/env python3
"""
Integration Test Harness - Tests components as connected systems
NO MOCKS - Components communicate with actual instances
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import importlib.util
import sys

from autocoder_cc.observability import get_logger

class AsyncMessageBus:
    """Real message bus for inter-component communication"""
    
    def __init__(self):
        self.components = {}
        self.logger = get_logger("AsyncMessageBus")
    
    def register_component(self, name: str, instance: Any):
        """Register a component instance"""
        self.components[name] = instance
        self.logger.info(f"Registered component: {name}")
    
    async def send(self, source: str, target: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to actual target component"""
        if target not in self.components:
            return {"status": "error", "message": f"Component {target} not found"}
        
        target_component = self.components[target]
        self.logger.debug(f"Routing message from {source} to {target}")
        
        # Call the actual component's process_item method
        if hasattr(target_component, 'process_item'):
            return await target_component.process_item(message)
        else:
            return {"status": "error", "message": f"Component {target} has no process_item method"}

class IntegrationTestHarness:
    """Test harness that runs actual components together"""
    
    def __init__(self):
        self.message_bus = AsyncMessageBus()
        self.components = {}
        self.logger = get_logger("IntegrationTestHarness")
    
    async def load_system(self, components_dir: Path) -> bool:
        """Load and wire all components from a system"""
        try:
            # Add the components directory to path so imports work
            if str(components_dir) not in sys.path:
                sys.path.insert(0, str(components_dir))
            
            # First, import communication module to make MessageEnvelope available
            comm_file = components_dir / "communication.py"
            if comm_file.exists():
                spec = importlib.util.spec_from_file_location("communication", comm_file)
                if spec and spec.loader:
                    comm_module = importlib.util.module_from_spec(spec)
                    sys.modules["communication"] = comm_module
                    spec.loader.exec_module(comm_module)
            
            # Find all component files
            component_files = [
                f for f in components_dir.glob("*.py")
                if f.name not in ['__init__.py', 'observability.py', 'communication.py']
            ]
            
            for component_file in component_files:
                # Load the component module
                spec = importlib.util.spec_from_file_location(
                    f"component_{component_file.stem}",
                    component_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module  # Register module
                    spec.loader.exec_module(module)
                    
                    # Find and instantiate component class
                    component_instance = self._instantiate_component(module, component_file.stem)
                    if component_instance:
                        # Register with message bus
                        self.message_bus.register_component(component_file.stem, component_instance)
                        self.components[component_file.stem] = component_instance
                        
                        # Inject a method for inter-component communication
                        def send_to_component_method(target: str, data: Dict[str, Any]):
                            """Synchronous wrapper for component communication"""
                            return asyncio.create_task(
                                self.message_bus.send(component_file.stem, target, data)
                            )
                        
                        # Attach the communication method to the component
                        component_instance.send_to_component = send_to_component_method
            
            self.logger.info(f"Loaded {len(self.components)} components")
            
            # Initialize all components
            for name, component in self.components.items():
                if hasattr(component, 'setup'):
                    await component.setup()
                    self.logger.info(f"Initialized component: {name}")
            
            return len(self.components) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to load system: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _instantiate_component(self, module, component_name: str):
        """Instantiate a component from its module"""
        # Find the component class - prioritize Generated classes
        candidates = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type):
                # Prioritize Generated classes first
                if 'Generated' in name:
                    candidates.insert(0, (name, obj))  # Add to beginning
                elif 'Component' in name and name != 'ComposedComponent':
                    candidates.append((name, obj))  # Add to end
        
        # Try to instantiate the best candidate
        for name, obj in candidates:
            config = self._create_config_for_component(name, component_name)
            try:
                self.logger.info(f"Attempting to instantiate {name}")
                instance = obj(name=component_name, config=config)
                self.logger.info(f"Successfully instantiated {name}")
                return instance
            except Exception as e:
                self.logger.warning(f"Failed to instantiate {name}: {e}")
        
        self.logger.error(f"Could not instantiate any component from {component_name}")
        return None
    
    def _create_config_for_component(self, class_name: str, component_name: str) -> Dict[str, Any]:
        """Create appropriate config for component type"""
        config = {
            "test_mode": False,
            "storage_type": "in_memory",
            "port": 8080,
            "host": "localhost",
            "timeout": 30,
            "max_retries": 3
        }
        
        # Add component-specific configs based on the component type
        if "controller" in component_name.lower() or "Controller" in class_name:
            # Controllers need to know their store
            config["store_name"] = self._find_store_component()
            config["store_component_name"] = self._find_store_component()
        
        # Add default name if not provided
        config["name"] = component_name
        
        return config
    
    def _find_store_component(self) -> str:
        """Find the store component name in the system"""
        for name in self.components.keys():
            if "store" in name.lower():
                return name
        return "todo_store"  # Default fallback
    
    async def test_component_in_system(self, component_name: str, test_data: List[Dict]) -> Dict[str, Any]:
        """Test a component within the live system context"""
        if component_name not in self.components:
            return {"success": False, "error": f"Component {component_name} not found"}
        
        component = self.components[component_name]
        results = []
        
        for test_case in test_data:
            try:
                result = await component.process_item(test_case)
                results.append({"success": True, "result": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "component": component_name,
            "total_tests": len(test_data),
            "passed": success_count,
            "success_rate": success_count / len(test_data) * 100,
            "results": results
        }
    
    async def cleanup(self):
        """Clean up all components"""
        for name, component in self.components.items():
            if hasattr(component, 'cleanup'):
                await component.cleanup()
            elif hasattr(component, 'teardown'):
                await component.teardown()

class MessageBusAdapter:
    """Adapter to make message bus look like a communicator"""
    
    def __init__(self, message_bus: AsyncMessageBus, source_name: str):
        self.message_bus = message_bus
        self.source_name = source_name
    
    async def send_to_component(self, target: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send via message bus"""
        return await self.message_bus.send(self.source_name, target, data)
    
    async def query_component(self, target: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query via message bus"""
        return await self.message_bus.send(self.source_name, target, query)