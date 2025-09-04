"""Port-based test runner for component validation."""
from typing import Dict, List, Any, Optional
import asyncio
import anyio
from pathlib import Path
from autocoder_cc.components.connection_manager import ConnectionManager
from autocoder_cc.components.primitives.base import Primitive
from autocoder_cc.observability import get_logger

class PortBasedTestRunner:
    """Test runner for port-based components."""
    
    def __init__(self, test_data_dir: Optional[Path] = None):
        self.manager = ConnectionManager()
        self.logger = get_logger("PortBasedTestRunner")
        self.test_data_dir = test_data_dir or Path("test_data")
        self.results = []
        
    async def load_component(self, component_path: Path) -> Primitive:
        """Dynamically load a component from file."""
        # Import component module
        import importlib.util
        spec = importlib.util.spec_from_file_location("component", component_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find component class (should be only one)
        for name, obj in module.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, Primitive) and obj != Primitive:
                # Instantiate component
                component = obj(name.lower(), {})
                await component.setup()
                self.manager.register_component(component)
                return component
                
        raise ValueError(f"No Primitive subclass found in {component_path}")
        
    async def test_component(self, component: Primitive, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test a component with given test cases."""
        results = {
            "component": component.name,
            "type": component.__class__.__name__,
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, test_case in enumerate(test_cases):
            try:
                # Run test based on component type
                if hasattr(component, 'transform'):
                    output = await component.transform(test_case["input"])
                elif hasattr(component, 'generate'):
                    outputs = []
                    async for item in component.generate():
                        outputs.append(item)
                        if len(outputs) >= test_case.get("max_items", 10):
                            break
                    output = outputs
                elif hasattr(component, 'consume'):
                    await component.consume(test_case["input"])
                    output = {"consumed": True}
                elif hasattr(component, 'split'):
                    output = await component.split(test_case["input"])
                elif hasattr(component, 'merge'):
                    output = await component.merge(test_case["input"])
                else:
                    raise ValueError(f"Unknown component type: {component.__class__.__name__}")
                
                # Check expected output if provided
                if "expected" in test_case:
                    if output == test_case["expected"]:
                        results["passed"] += 1
                        self.logger.info(f"Test {i+1}: PASSED")
                    else:
                        results["failed"] += 1
                        results["errors"].append({
                            "test": i+1,
                            "expected": test_case["expected"],
                            "actual": output
                        })
                        self.logger.warning(f"Test {i+1}: FAILED")
                else:
                    # Just check it didn't error
                    results["passed"] += 1
                    self.logger.info(f"Test {i+1}: PASSED (no error)")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "test": i+1,
                    "error": str(e)
                })
                self.logger.error(f"Test {i+1}: ERROR - {e}")
                
        await component.cleanup()
        return results
        
    async def run_pipeline_test(self, components: List[Primitive], test_data: List[Any]) -> Dict[str, Any]:
        """Test a pipeline of connected components."""
        results = {
            "pipeline": [c.name for c in components],
            "total_messages": len(test_data),
            "processed": 0,
            "dropped": 0,
            "errors": []
        }
        
        # Wire up components (assume linear pipeline for now)
        connections = []
        for i in range(len(components) - 1):
            source = components[i]
            target = components[i + 1]
            
            # Find compatible ports - check if components have get_port_manifest
            if hasattr(source, 'get_port_manifest') and hasattr(target, 'get_port_manifest'):
                source_ports = source.get_port_manifest()
                target_ports = target.get_port_manifest()
                
                # Find first output port from source
                source_port = None
                for port_name, port_info in source_ports.items():
                    if hasattr(port_info, 'direction') and port_info.direction == "output":
                        source_port = port_name
                        break
                    elif "out" in port_name.lower():  # Fallback heuristic
                        source_port = port_name
                        break
                
                # Find first input port from target
                target_port = None
                for port_name, port_info in target_ports.items():
                    if hasattr(port_info, 'direction') and port_info.direction == "input":
                        target_port = port_name
                        break
                    elif "in" in port_name.lower():  # Fallback heuristic
                        target_port = port_name
                        break
                
                if source_port and target_port:
                    conn = await self.manager.connect_ports(
                        source.name, source_port,
                        target.name, target_port
                    )
                    connections.append(conn)
                else:
                    self.logger.warning(f"Could not find compatible ports between {source.name} and {target.name}")
                
        # Process test data through pipeline
        for data in test_data:
            try:
                # Process through pipeline
                current = data
                for component in components:
                    if hasattr(component, 'transform'):
                        current = await component.transform(current)
                        if current is None:
                            results["dropped"] += 1
                            break
                else:
                    results["processed"] += 1
                    
            except Exception as e:
                results["errors"].append(str(e))
                
        # Cleanup
        self.manager.disconnect_all()
        
        return results