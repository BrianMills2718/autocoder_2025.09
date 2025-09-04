from autocoder_cc.observability.structured_logging import get_logger
"""
Level 2 Component Validation - REAL tests without mocking.
Uses in-memory implementations and actual data flow.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import tempfile
import sys
from dataclasses import dataclass
import anyio
from anyio import create_memory_object_stream

from autocoder_cc.orchestration.component import Component
from autocoder_cc.analysis import find_placeholders, analyze_code_quality


@dataclass 
class ComponentTestResult:
    """Result of testing a single component."""
    component_name: str
    component_type: str
    instantiation_passed: bool = False
    setup_passed: bool = False
    process_passed: bool = False
    cleanup_passed: bool = False
    data_flow_passed: bool = False
    no_placeholders: bool = False
    error_message: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    
    @property
    def passed(self) -> bool:
        """Component passes if all tests pass."""
        return all([
            self.instantiation_passed,
            self.setup_passed,
            self.process_passed,
            self.cleanup_passed,
            self.data_flow_passed,
            self.no_placeholders
        ])


class Level2RealValidator:
    """
    Level 2 validator that runs REAL component tests.
    NO mocking - uses actual in-memory implementations.
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def validate_component(self, 
                               component_path: Path,
                               component_spec: Dict[str, Any]) -> ComponentTestResult:
        """
        Validate a single component with real tests.
        
        Args:
            component_path: Path to component Python file
            component_spec: Component specification from blueprint
            
        Returns:
            ComponentTestResult with test outcomes
        """
        comp_name = component_spec.get('name', 'unknown')
        comp_type = component_spec.get('type', 'unknown')
        
        result = ComponentTestResult(
            component_name=comp_name,
            component_type=comp_type
        )
        
        try:
            # Check for placeholders using AST
            with open(component_path, 'r') as f:
                source_code = f.read()
            
            placeholders = find_placeholders(source_code)
            if placeholders:
                result.no_placeholders = False
                result.error_message = f"Found {len(placeholders)} placeholders: {[p.function_name for p in placeholders]}"
                return result
            else:
                result.no_placeholders = True
            
            # Load and instantiate component
            component = await self._load_and_instantiate(component_path, comp_name, component_spec)
            if not component:
                result.error_message = "Failed to instantiate component"
                return result
            
            result.instantiation_passed = True
            
            # Test setup
            try:
                await component.setup()
                result.setup_passed = True
            except Exception as e:
                result.error_message = f"Setup failed: {e}"
                return result
            
            # Test data processing with real data
            test_passed = await self._test_data_flow(component, comp_type)
            result.data_flow_passed = test_passed
            
            # Test process method
            try:
                # Run process for a short time
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._run_process_with_timeout, component, 2.0)
                result.process_passed = True
            except Exception as e:
                result.error_message = f"Process failed: {e}"
                result.process_passed = False
            
            # Test cleanup
            try:
                await component.cleanup()
                result.cleanup_passed = True
            except Exception as e:
                result.error_message = f"Cleanup failed: {e}"
                result.cleanup_passed = False
            
            return result
            
        except Exception as e:
            result.error_message = f"Validation error: {e}"
            return result
    
    async def _load_and_instantiate(self,
                                  component_path: Path,
                                  comp_name: str,
                                  comp_spec: Dict[str, Any]) -> Optional[Component]:
        """Load component module and instantiate it."""
        try:
            # Add parent directory to path
            sys.path.insert(0, str(component_path.parent))
            
            # Import module
            module_name = component_path.stem
            module = __import__(module_name)
            
            # Find component class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Component) and 
                    attr != Component):
                    
                    # Instantiate with config
                    config = comp_spec.get('config', {})
                    component = attr(comp_name, config)
                    
                    # Set up streams for testing
                    send_stream, receive_stream = create_memory_object_stream(100)
                    component.receive_streams = {'input': receive_stream}
                    component.send_streams = {'output': send_stream}
                    
                    return component
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load component: {e}")
            return None
        finally:
            # Clean up sys.path
            if str(component_path.parent) in sys.path:
                sys.path.remove(str(component_path.parent))
    
    async def _test_data_flow(self, component: Component, comp_type: str) -> bool:
        """Test actual data flow through component."""
        try:
            # Generate test data based on component type
            test_data = self._generate_test_data(comp_type)
            
            # Send test data to input stream
            if 'input' in component.receive_streams:
                await component.send_streams['output'].send(test_data)
                
                # Try to receive processed data
                async with anyio.move_on_after(1.0) as scope:
                    # Create a new stream to receive data
                    output_send, output_receive = create_memory_object_stream(100)
                    
                    # Connect component output to our receiver
                    if 'output' in component.send_streams:
                        # Process one item
                        await component.receive_streams['input'].send(test_data)
                        
                        # Run process briefly
                        async with anyio.create_task_group() as tg:
                            tg.start_soon(self._run_process_with_timeout, component, 0.5)
                        
                        # Check if we got output
                        try:
                            result = await output_receive.receive()
                            return isinstance(result, dict)
                        except:
                            pass
                
                if scope.cancelled_caught:
                    self.logger.warning("Data flow test timed out")
                    return False
            
            # For components without input (sources), just check they can run
            return True
            
        except Exception as e:
            self.logger.error(f"Data flow test error: {e}")
            return False
    
    async def _run_process_with_timeout(self, component: Component, timeout: float):
        """Run component process method with timeout."""
        try:
            async with anyio.move_on_after(timeout):
                await component.process()
        except Exception as e:
            # Some components might raise when streams close
            if "closed" not in str(e).lower():
                raise
    
    def _generate_test_data(self, comp_type: str) -> Dict[str, Any]:
        """Generate appropriate test data for component type."""
        base_data = {
            "test_id": "test123",
            "timestamp": "2023-01-01T00:00:00Z",
            "value": 42
        }
        
        # Customize based on component type
        if comp_type == "APIEndpoint":
            return {
                "method": "POST",
                "path": "/test",
                "body": base_data,
                "headers": {"Content-Type": "application/json"}
            }
        elif comp_type == "Transformer":
            return {
                "data": base_data,
                "metadata": {"source": "test"}
            }
        elif comp_type == "Store":
            return {
                "operation": "save",
                "key": "test_key",
                "value": base_data
            }
        else:
            return base_data


async def validate_all_components_real(
    components_dir: Path,
    blueprint: Dict[str, Any]
) -> Tuple[bool, List[ComponentTestResult]]:
    """
    Validate all components in a directory with REAL tests.
    
    Returns:
        Tuple of (all_passed, list_of_results)
    """
    validator = Level2RealValidator()
    results = []
    
    components = blueprint.get('system', {}).get('components', [])
    
    for comp_spec in components:
        comp_name = comp_spec.get('name')
        comp_file = components_dir / f"{comp_name}.py"
        
        if comp_file.exists():
            result = await validator.validate_component(comp_file, comp_spec)
            results.append(result)
        else:
            # Missing component file
            result = ComponentTestResult(
                component_name=comp_name,
                component_type=comp_spec.get('type', 'unknown'),
                error_message=f"Component file not found: {comp_file}"
            )
            results.append(result)
    
    all_passed = all(r.passed for r in results)
    return all_passed, results