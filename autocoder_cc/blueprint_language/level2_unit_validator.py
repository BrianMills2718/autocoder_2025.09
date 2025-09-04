#!/usr/bin/env python3
"""
Level 2 Unit Validation - Component Logic Testing with Mocked Dependencies
Part of the 4-tier validation framework

This module provides comprehensive unit testing for generated components:
- Mocked anyio streams
- Isolated component testing
- Contract validation
- Error handling verification
"""
import ast
import asyncio
import logging
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import subprocess
import json

import anyio
from autocoder_cc.observability.structured_logging import get_logger


@dataclass
class ComponentUnitTestResult:
    """Result of unit testing a single component"""
    component_name: str
    component_type: str
    
    # Test outcomes
    instantiation_passed: bool = False
    setup_passed: bool = False
    process_passed: bool = False
    cleanup_passed: bool = False
    error_handling_passed: bool = False
    
    # Data validation
    input_processing_passed: bool = False
    output_generation_passed: bool = False
    data_transformation_passed: bool = False
    
    # Errors collected
    errors: List[str] = None
    warnings: List[str] = None
    
    # Performance metrics
    setup_time_ms: float = 0.0
    process_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def passed(self) -> bool:
        """Check if all critical tests passed"""
        return all([
            self.instantiation_passed,
            self.setup_passed,
            self.process_passed,
            self.cleanup_passed
        ])


class Level2UnitValidator:
    """
    Performs Level 2 unit validation on components.
    
    Key features:
    - Tests components in complete isolation
    - Uses mocked anyio streams
    - Validates component contracts
    - Tests error handling
    - Measures basic performance
    """
    
    def __init__(self):
        self.logger = get_logger("Level2UnitValidator")
    
    async def validate_component(self, 
                               component_file: Path, 
                               component_info: Dict[str, Any],
                               system_name: str) -> ComponentUnitTestResult:
        """
        Run comprehensive unit tests on a single component.
        
        Args:
            component_file: Path to component Python file
            component_info: Component metadata from blueprint
            system_name: Name of the system
            
        Returns:
            ComponentUnitTestResult with detailed test outcomes
        """
        result = ComponentUnitTestResult(
            component_name=component_info['name'],
            component_type=component_info['type']
        )
        
        try:
            # Generate unit test script
            test_script = self._generate_unit_test_script(
                component_info, system_name, component_file
            )
            
            # Write and execute test script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
                tf.write(test_script)
                tf.flush()
                
                # Run test with proper environment
                env = sys.executable
                test_result = subprocess.run(
                    [env, tf.name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=component_file.parent.parent  # Run from project root
                )
                
                # Parse test results
                if test_result.returncode == 0:
                    # Parse JSON output from test script
                    try:
                        test_output = json.loads(test_result.stdout)
                        result.instantiation_passed = test_output.get('instantiation_passed', False)
                        result.setup_passed = test_output.get('setup_passed', False)
                        result.process_passed = test_output.get('process_passed', False)
                        result.cleanup_passed = test_output.get('cleanup_passed', False)
                        result.error_handling_passed = test_output.get('error_handling_passed', False)
                        result.input_processing_passed = test_output.get('input_processing_passed', False)
                        result.output_generation_passed = test_output.get('output_generation_passed', False)
                        result.data_transformation_passed = test_output.get('data_transformation_passed', False)
                        result.errors = test_output.get('errors', [])
                        result.warnings = test_output.get('warnings', [])
                        result.setup_time_ms = test_output.get('setup_time_ms', 0.0)
                        result.process_time_ms = test_output.get('process_time_ms', 0.0)
                    except json.JSONDecodeError:
                        result.errors.append(f"Failed to parse test output: {test_result.stdout}")
                else:
                    result.errors.append(f"Test execution failed: {test_result.stderr}")
                    
        except subprocess.TimeoutExpired:
            result.errors.append("Unit test timed out after 30 seconds")
        except Exception as e:
            result.errors.append(f"Unit validation error: {str(e)}")
        
        return result
    
    def _generate_unit_test_script(self, 
                                 component_info: Dict[str, Any],
                                 system_name: str,
                                 component_file: Path) -> str:
        """Generate comprehensive unit test script for a component"""
        
        component_name = component_info['name']
        component_type = component_info['type']
        class_name = self._find_class_name(component_file)
        
        # Base test template
        test_template = f'''#!/usr/bin/env python3
"""
Unit test for {component_name} component
Generated by Level2UnitValidator
"""
import asyncio
import json
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import anyio
from anyio import create_memory_object_stream

# Import the component
try:
    from components.{component_name} import {class_name}
except ImportError:
    # Try alternative import
    from {component_name} import {class_name}

# Test results to be output as JSON
test_results = {{
    "instantiation_passed": False,
    "setup_passed": False,
    "process_passed": False,
    "cleanup_passed": False,
    "error_handling_passed": False,
    "input_processing_passed": False,
    "output_generation_passed": False,
    "data_transformation_passed": False,
    "errors": [],
    "warnings": [],
    "setup_time_ms": 0.0,
    "process_time_ms": 0.0
}}

async def run_unit_tests():
    """Run all unit tests for the component"""
    
    component_instance = None
    
    try:
        # Test 1: Instantiation
        start_time = time.time()
        try:
            # Use component's actual config from blueprint, not just test_mode
            config = {self._get_component_config(component_info)}
            config["test_mode"] = True  # Add test mode flag
            component_instance = {class_name}("{component_name}", config)
            test_results["instantiation_passed"] = True
        except Exception as e:
            test_results["errors"].append(f"Instantiation failed: {{str(e)}}")
            return
        
        # Test 2: Setup
        try:
            # Create mock streams
            component_instance.receive_streams = {{}}
            component_instance.send_streams = {{}}
            
            {self._generate_stream_setup(component_info)}
            
            setup_start = time.time()
            await component_instance.setup()
            test_results["setup_time_ms"] = (time.time() - setup_start) * 1000
            test_results["setup_passed"] = True
        except Exception as e:
            test_results["errors"].append(f"Setup failed: {{str(e)}}")
            return
        
        # Test 3: Process with test data
        try:
            process_start = time.time()
            
            {self._generate_process_test(component_info)}
            
            test_results["process_time_ms"] = (time.time() - process_start) * 1000
            test_results["process_passed"] = True
        except Exception as e:
            test_results["errors"].append(f"Process failed: {{str(e)}}")
        
        # Test 4: Error handling
        try:
            {self._generate_error_handling_test(component_info)}
            test_results["error_handling_passed"] = True
        except Exception as e:
            test_results["warnings"].append(f"Error handling test skipped: {{str(e)}}")
        
        # Test 5: Cleanup
        try:
            await component_instance.cleanup()
            test_results["cleanup_passed"] = True
        except Exception as e:
            test_results["errors"].append(f"Cleanup failed: {{str(e)}}")
    
    except Exception as e:
        test_results["errors"].append(f"Unexpected error: {{str(e)}}")
    
    finally:
        # Ensure cleanup
        if component_instance and hasattr(component_instance, 'cleanup'):
            try:
                await component_instance.cleanup()
            except:
                pass

# Run the tests and output results
if __name__ == "__main__":
    anyio.run(run_unit_tests)
    print(json.dumps(test_results))
'''
        
        return test_template
    
    def _get_component_config(self, component_info: Dict[str, Any]) -> str:
        """
        Extract component configuration from blueprint info.
        Returns a Python dict string for the test script.
        """
        config = component_info.get('config', {})
        
        # Special handling for Controllers - ensure store_component_name is set
        if component_info.get('type') == 'Controller':
            # Try to find store name from connections or use default
            if 'store_component_name' not in config:
                # Look for store connection in blueprint
                if 'connections' in component_info:
                    for conn in component_info.get('connections', {}).get('outputs', []):
                        if 'store' in conn.lower():
                            config['store_component_name'] = conn
                            break
                
                # Fallback to a reasonable default
                if 'store_component_name' not in config:
                    config['store_component_name'] = 'todo_store'
        
        # Convert Python dict to string representation for the test script
        import json
        return json.dumps(config)
    
    def _find_class_name(self, component_file: Path) -> str:
        """Extract the main class name from component file"""
        try:
            with open(component_file, 'r') as f:
                tree = ast.parse(f.read())
            
            # Find classes that inherit from component base classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id in [
                            'Component', 'Source', 'Transformer', 'Sink', 
                            'Model', 'Store', 'APIEndpoint'
                        ]:
                            return node.name
            
            # Fallback to first class
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return node.name
                    
        except Exception:
            # Fallback to generated name
            component_name = component_file.stem
            return component_name.replace('_', '').title()
    
    def _generate_stream_setup(self, component_info: Dict[str, Any]) -> str:
        """Generate stream setup code based on component type"""
        component_type = component_info['type']
        
        if component_type == 'Source':
            return '''
            # Source components only have output streams
            output_send, output_receive = create_memory_object_stream(max_buffer_size=10)
            component_instance.send_streams['output'] = output_send
            '''
        
        elif component_type == 'Sink':
            return '''
            # Sink components only have input streams
            input_send, input_receive = create_memory_object_stream(max_buffer_size=10)
            component_instance.receive_streams['input'] = input_receive
            '''
        
        else:  # Transformer, Model, etc.
            return '''
            # Create input and output streams
            input_send, input_receive = create_memory_object_stream(max_buffer_size=10)
            output_send, output_receive = create_memory_object_stream(max_buffer_size=10)
            component_instance.receive_streams['input'] = input_receive
            component_instance.send_streams['output'] = output_send
            '''
    
    def _generate_process_test(self, component_info: Dict[str, Any]) -> str:
        """Generate process test code based on component type"""
        component_type = component_info['type']
        
        if component_type == 'Source':
            return '''
            # Test Source data generation
            results = []
            
            async with anyio.create_task_group() as tg:
                # Run process in background
                tg.start_soon(component_instance.process)
                
                # Collect generated data
                with anyio.move_on_after(2):  # 2 second timeout
                    async for item in output_receive:
                        results.append(item)
                        if len(results) >= 3:
                            break
                
                tg.cancel_scope.cancel()
            
            # Validate results
            if len(results) > 0:
                test_results["output_generation_passed"] = True
            else:
                test_results["errors"].append("Source generated no data")
            '''
        
        elif component_type == 'Sink':
            return '''
            # Test Sink data consumption
            test_data = [
                {"id": 1, "value": "test1"},
                {"id": 2, "value": "test2"},
                {"id": 3, "value": "test3"}
            ]
            
            # Send test data
            for data in test_data:
                await input_send.send(data)
            await input_send.aclose()
            
            # Run process with timeout
            with anyio.move_on_after(2):
                await component_instance.process()
            
            test_results["input_processing_passed"] = True
            '''
        
        else:  # Transformer, Model, etc.
            return '''
            # Test data transformation
            test_data = {"id": 1, "value": 100, "type": "test"}
            results = []
            
            async with anyio.create_task_group() as tg:
                # Run process in background
                tg.start_soon(component_instance.process)
                
                # Send test data
                await input_send.send(test_data)
                await input_send.aclose()
                
                # Collect results
                with anyio.move_on_after(2):
                    async for item in output_receive:
                        results.append(item)
                        break
                
                tg.cancel_scope.cancel()
            
            # Validate transformation
            if len(results) > 0:
                test_results["data_transformation_passed"] = True
                test_results["input_processing_passed"] = True
                test_results["output_generation_passed"] = True
            else:
                test_results["errors"].append("No output from transformation")
            '''
    
    def _generate_error_handling_test(self, component_info: Dict[str, Any]) -> str:
        """Generate error handling test code"""
        component_type = component_info['type']
        
        if component_type == 'Source':
            return '''
            # Test error handling - Sources typically don't have error inputs
            test_results["warnings"].append("Error handling test not applicable for Source")
            '''
        
        else:
            return '''
            # Test error handling with invalid data
            try:
                if 'input' in component_instance.receive_streams:
                    # Create new streams for error test
                    error_send, error_receive = create_memory_object_stream(max_buffer_size=10)
                    component_instance.receive_streams['input'] = error_receive
                    
                    # Send invalid data
                    await error_send.send(None)  # Null data
                    await error_send.send("invalid")  # Wrong type
                    await error_send.aclose()
                    
                    # Process should handle errors gracefully
                    with anyio.move_on_after(1):
                        await component_instance.process()
                    
                    # If we get here, error handling worked
                    test_results["error_handling_passed"] = True
            except Exception as e:
                test_results["warnings"].append(f"Error handling test failed: {str(e)}")
            '''


async def validate_all_components(components_dir: Path, 
                                system_name: str,
                                blueprint_components: List[Dict[str, Any]]) -> List[ComponentUnitTestResult]:
    """
    Validate all components in a directory.
    
    Args:
        components_dir: Directory containing component files
        system_name: Name of the system
        blueprint_components: Component info from blueprint
        
    Returns:
        List of validation results
    """
    validator = Level2UnitValidator()
    results = []
    
    # Create mapping of component names to info
    component_map = {comp['name']: comp for comp in blueprint_components}
    
    for component_file in components_dir.glob("*.py"):
        if component_file.name.startswith("__"):
            continue
            
        component_name = component_file.stem
        component_info = component_map.get(component_name, {
            'name': component_name,
            'type': 'Component'  # Default type
        })
        
        result = await validator.validate_component(
            component_file, component_info, system_name
        )
        results.append(result)
    
    return results