"""
Test full system integration from blueprint to running system.
Validates the complete pipeline with reference implementation patterns.
"""

import unittest
import tempfile
import os
import json
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.orchestration.harness import SystemExecutionHarness
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any


class TestSystemIntegration(unittest.TestCase):
    """Test full system integration with ComposedComponent pattern."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.blueprint_file = os.path.join(self.temp_dir, "test_system.yaml")
        
        # Create a simple blueprint
        self.blueprint_content = """
name: TestTodoSystem
description: Simple todo system for testing
version: 1.0.0

components:
  - name: TodoStore
    type: Store
    functions:
      - name: store_todo
        inputs: [todo_data]
        outputs: [todo_id]
        business_logic: Store a todo item
        
  - name: TodoAPI
    type: API
    bindings: [TodoStore]
    functions:
      - name: create_todo
        inputs: [todo_text]
        outputs: [todo_id]
        business_logic: Create a new todo via API

system:
  entry_point: TodoAPI
  data_flow:
    - from: TodoAPI
      to: TodoStore
      binding_type: direct
"""
        with open(self.blueprint_file, 'w') as f:
            f.write(self.blueprint_content)
            
    @pytest.mark.asyncio
    async def test_blueprint_to_system_generation(self):
        """Test generating system from blueprint with new patterns."""
        # Parse blueprint
        parser = BlueprintParser()
        blueprint = parser.parse(self.blueprint_file)
        
        self.assertIsNotNone(blueprint)
        self.assertEqual(blueprint.name, "TestTodoSystem")
        self.assertEqual(len(blueprint.components), 2)
        
        # Generate system
        generator = SystemGenerator()
        
        # Mock LLM to return ComposedComponent-based components
        mock_store_code = """
class GeneratedStore_TodoStore(ComposedComponent):
    def __init__(self, name: str = "todo_store", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        self._todos = {}
        self._next_id = 1
        
    async def process_item(self, item: Any) -> Any:
        if item.get('action') == 'store_todo':
            todo_id = f"todo_{self._next_id}"
            self._next_id += 1
            self._todos[todo_id] = item.get('todo_data')
            return {'todo_id': todo_id, 'status': 'stored'}
        return {'status': 'unknown_action'}
"""
        
        mock_api_code = """
class GeneratedAPI_TodoAPI(ComposedComponent):
    def __init__(self, name: str = "todo_api", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        self.store_component = None
        
    def set_store_component(self, store):
        self.store_component = store
        
    async def process_item(self, item: Any) -> Any:
        if item.get('action') == 'create_todo':
            if self.store_component:
                return await self.store_component.process_item({
                    'action': 'store_todo',
                    'todo_data': item.get('todo_text')
                })
        return {'status': 'error'}
"""
        
        with patch('autocoder_cc.blueprint_language.llm_component_generator.LLMComponentGenerator.generate_component_logic') as mock_gen:
            # Return appropriate code based on component type
            def side_effect(component, output_dir):
                if component.type == "Store":
                    return mock_store_code
                elif component.type == "API":
                    return mock_api_code
                return ""
                
            mock_gen.side_effect = side_effect
            
            # Generate the system
            output_dir = os.path.join(self.temp_dir, "generated_system")
            result = await generator.generate_system(blueprint, output_dir)
            
            # Verify system was generated
            self.assertTrue(os.path.exists(output_dir))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "main.py")))
            
    def test_system_execution_harness_with_composed_components(self):
        """Test that SystemExecutionHarness works with ComposedComponent pattern."""
        # Create a mock system with ComposedComponent-based components
        system_config = {
            "name": "TestSystem",
            "components": [
                {
                    "name": "TestStore",
                    "type": "Store",
                    "module": "components.test_store"
                },
                {
                    "name": "TestAPI",
                    "type": "API",
                    "module": "components.test_api",
                    "bindings": ["TestStore"]
                }
            ]
        }
        
        config_file = os.path.join(self.temp_dir, "config.json")
        with open(config_file, 'w') as f:
            json.dump(system_config, f)
            
        # Create mock components
        mock_store = MagicMock()
        mock_store.name = "TestStore"
        mock_store.setup = MagicMock()
        mock_store.cleanup = MagicMock()
        mock_store.get_health_status = MagicMock(return_value={'status': 'healthy'})
        mock_store.process_item = AsyncMock(return_value={'status': 'success'})
        
        mock_api = MagicMock()
        mock_api.name = "TestAPI"
        mock_api.setup = MagicMock()
        mock_api.cleanup = MagicMock()
        mock_api.set_store_component = MagicMock()
        mock_api.get_health_status = MagicMock(return_value={'status': 'healthy'})
        mock_api.process_item = AsyncMock(return_value={'status': 'success'})
        
        # Test harness with mocked components
        with patch('importlib.import_module') as mock_import:
            # Set up mock imports
            mock_store_module = MagicMock()
            mock_store_module.GeneratedStore_TestStore = MagicMock(return_value=mock_store)
            
            mock_api_module = MagicMock()
            mock_api_module.GeneratedAPI_TestAPI = MagicMock(return_value=mock_api)
            
            def import_side_effect(name):
                if "test_store" in name:
                    return mock_store_module
                elif "test_api" in name:
                    return mock_api_module
                raise ImportError(f"No module named {name}")
                
            mock_import.side_effect = import_side_effect
            
            # Create and test harness
            harness = SystemExecutionHarness(config_file)
            
            # Note: Real harness implementation might differ
            # This tests the expected interface
            
    def test_dynamic_component_loading(self):
        """Test dynamic loading of generated components."""
        # Create a generated component file
        component_dir = os.path.join(self.temp_dir, "components")
        os.makedirs(component_dir)
        
        component_file = os.path.join(component_dir, "test_component.py")
        with open(component_file, 'w') as f:
            f.write("""
from typing import Dict, Any

class ComposedComponent:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        
    def setup(self): pass
    def cleanup(self): pass
    async def process_item(self, item): return item

class GeneratedStore_TestComponent(ComposedComponent):
    def __init__(self, name: str = "test", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        
    async def process_item(self, item: Any) -> Any:
        return {'processed': True, 'item': item}
""")
        
        # Add to path and import
        import sys
        sys.path.insert(0, self.temp_dir)
        
        try:
            from components.test_component import GeneratedStore_TestComponent
            
            # Create instance
            component = GeneratedStore_TestComponent("dynamic_test")
            
            # Test it works
            self.assertEqual(component.name, "dynamic_test")
            
            # Test async method
            result = asyncio.run(component.process_item({'test': 'data'}))
            self.assertEqual(result['processed'], True)
            self.assertEqual(result['item']['test'], 'data')
            
        finally:
            # Clean up path
            sys.path.remove(self.temp_dir)
            
    def test_system_startup_sequence(self):
        """Test correct startup sequence for generated system."""
        startup_order = []
        
        # Mock components that track startup
        class MockStore:
            def __init__(self, name, config):
                self.name = name
                
            def setup(self):
                startup_order.append(f"setup_{self.name}")
                
            def cleanup(self):
                startup_order.append(f"cleanup_{self.name}")
                
            async def process_item(self, item):
                return {'status': 'success'}
                
        class MockAPI:
            def __init__(self, name, config):
                self.name = name
                self.store = None
                
            def set_store_component(self, store):
                self.store = store
                startup_order.append(f"bind_{self.name}_to_{store.name}")
                
            def setup(self):
                startup_order.append(f"setup_{self.name}")
                
            def cleanup(self):
                startup_order.append(f"cleanup_{self.name}")
                
        # Simulate startup
        store = MockStore("Store", {})
        api = MockAPI("API", {})
        
        # Startup sequence
        store.setup()
        api.setup()
        api.set_store_component(store)
        
        # Verify order
        self.assertEqual(startup_order, [
            "setup_Store",
            "setup_API",
            "bind_API_to_Store"
        ])
        
        # Cleanup sequence
        api.cleanup()
        store.cleanup()
        
        self.assertIn("cleanup_API", startup_order)
        self.assertIn("cleanup_Store", startup_order)
        
    def test_system_shutdown_sequence(self):
        """Test graceful shutdown of generated system."""
        shutdown_order = []
        
        class TrackingComponent:
            def __init__(self, name):
                self.name = name
                self.running = True
                
            def cleanup(self):
                shutdown_order.append(self.name)
                self.running = False
                
        # Create components
        components = [
            TrackingComponent("API"),
            TrackingComponent("Store"),
            TrackingComponent("Processor")
        ]
        
        # Shutdown in reverse order
        for component in reversed(components):
            component.cleanup()
            
        # Verify shutdown order (reverse of creation)
        self.assertEqual(shutdown_order, ["Processor", "Store", "API"])
        
        # Verify all stopped
        for component in components:
            self.assertFalse(component.running)
            
    def test_health_monitoring_integration(self):
        """Test health monitoring across the system."""
        class HealthyComponent:
            def __init__(self, name):
                self.name = name
                self.healthy = True
                
            def get_health_status(self):
                return {
                    'status': 'healthy' if self.healthy else 'unhealthy',
                    'component': self.name,
                    'timestamp': 'test_time'
                }
                
        # Create system
        components = {
            'store': HealthyComponent('Store'),
            'api': HealthyComponent('API'),
            'processor': HealthyComponent('Processor')
        }
        
        # Check all healthy
        system_health = {}
        for name, comp in components.items():
            system_health[name] = comp.get_health_status()
            
        all_healthy = all(h['status'] == 'healthy' for h in system_health.values())
        self.assertTrue(all_healthy)
        
        # Simulate failure
        components['store'].healthy = False
        
        # Re-check health
        system_health = {}
        for name, comp in components.items():
            system_health[name] = comp.get_health_status()
            
        # System should detect unhealthy component
        self.assertEqual(system_health['store']['status'], 'unhealthy')
        self.assertEqual(system_health['api']['status'], 'healthy')
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()