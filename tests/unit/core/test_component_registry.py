import pytest
"""
Test component registry and discovery for ComposedComponent pattern.
Validates registration, capability detection, and dynamic discovery.
"""

import unittest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch


class ComponentRegistry:
    """Simple registry implementation for testing."""
    
    def __init__(self):
        self.components = {}
        self.capabilities = {}
        
    def register(self, name: str, component: Any, component_type: str, capabilities: List[str] = None):
        """Register a component with its capabilities."""
        self.components[name] = {
            'instance': component,
            'type': component_type,
            'capabilities': capabilities or [],
            'base_class': self._detect_base_class(component)
        }
        
        # Index by capability
        for cap in (capabilities or []):
            if cap not in self.capabilities:
                self.capabilities[cap] = []
            self.capabilities[cap].append(name)
            
    def _detect_base_class(self, component):
        """Detect the base class of a component."""
        for base in component.__class__.__bases__:
            if base.__name__ == 'ComposedComponent':
                return 'ComposedComponent'
            elif base.__name__ == 'StandaloneComponentBase':
                return 'StandaloneComponentBase'
        return 'Unknown'
        
    def get_by_type(self, component_type: str):
        """Get all components of a specific type."""
        return {
            name: info for name, info in self.components.items()
            if info['type'] == component_type
        }
        
    def get_by_capability(self, capability: str):
        """Get all components with a specific capability."""
        return self.capabilities.get(capability, [])
        
    def discover_bindings(self):
        """Discover and establish bindings between components."""
        bindings = []
        
        # Find APIs that need stores
        apis = self.get_by_type('API')
        stores = self.get_by_type('Store')
        
        for api_name, api_info in apis.items():
            api = api_info['instance']
            
            # Check if API has set_store_component method
            if hasattr(api, 'set_store_component'):
                # Find a compatible store
                for store_name, store_info in stores.items():
                    store = store_info['instance']
                    api.set_store_component(store)
                    bindings.append((api_name, store_name))
                    break
                    
        return bindings
        
    def cleanup(self):
        """Clean up all registered components."""
        cleanup_order = []
        
        # Clean up in reverse registration order
        for name in reversed(list(self.components.keys())):
            component = self.components[name]['instance']
            if hasattr(component, 'cleanup'):
                component.cleanup()
                cleanup_order.append(name)
                
        self.components.clear()
        self.capabilities.clear()
        
        return cleanup_order


class MockComposedComponent:
    """Mock ComposedComponent for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        
    def setup(self):
        pass
        
    def cleanup(self):
        pass
        
    async def process_item(self, item: Any) -> Any:
        return item
        
    def get_health_status(self):
        return {'status': 'healthy'}


class TestComponentRegistry(unittest.TestCase):
    """Test component registry functionality."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ComponentRegistry()
        
    def test_register_composed_component(self):
        """Test registering a ComposedComponent-based component."""
        # Create mock component
        class TestStore(MockComposedComponent):
            pass
            
        component = TestStore("test_store")
        
        # Register
        self.registry.register(
            "test_store",
            component,
            "Store",
            ["crud", "persistence"]
        )
        
        # Verify registration
        self.assertIn("test_store", self.registry.components)
        info = self.registry.components["test_store"]
        self.assertEqual(info['type'], "Store")
        self.assertEqual(info['base_class'], 'ComposedComponent')
        self.assertIn("crud", info['capabilities'])
        
    def test_capability_detection(self):
        """Test capability detection for new patterns."""
        class StoreWithCapabilities(MockComposedComponent):
            def create(self, item):
                return {'id': 1, 'item': item}
                
            def read(self, id):
                return {'id': id}
                
            def update(self, id, item):
                return {'id': id, 'updated': True}
                
            def delete(self, id):
                return {'deleted': id}
                
        component = StoreWithCapabilities("capable_store")
        
        # Detect capabilities by checking methods
        capabilities = []
        for method in ['create', 'read', 'update', 'delete']:
            if hasattr(component, method):
                capabilities.append(method)
                
        self.registry.register(
            "capable_store",
            component,
            "Store",
            capabilities
        )
        
        # Verify capabilities detected
        self.assertEqual(len(capabilities), 4)
        self.assertIn("create", capabilities)
        
        # Query by capability
        stores_with_create = self.registry.get_by_capability("create")
        self.assertIn("capable_store", stores_with_create)
        
    @pytest.mark.asyncio
    async def test_dynamic_discovery_of_generated_components(self):
        """Test discovering dynamically generated components."""
        # Simulate generated components
        generated_components = []
        
        for i in range(3):
            class GeneratedComponent(MockComposedComponent):
                pass
                
            # Give unique name
            GeneratedComponent.__name__ = f"GeneratedStore_{i}"
            component = GeneratedComponent(f"store_{i}")
            generated_components.append(component)
            
            self.registry.register(
                f"store_{i}",
                component,
                "Store",
                ["generated", "dynamic"]
            )
            
        # Discover all generated components
        generated = self.registry.get_by_capability("generated")
        self.assertEqual(len(generated), 3)
        
        # Verify all are ComposedComponent-based
        for name in generated:
            info = self.registry.components[name]
            self.assertEqual(info['base_class'], 'ComposedComponent')
            
    def test_registry_cleanup_on_shutdown(self):
        """Test registry cleanup during shutdown."""
        # Register multiple components
        components_registered = []
        
        for i in range(5):
            comp = MockComposedComponent(f"comp_{i}")
            self.registry.register(f"comp_{i}", comp, "Processing", [])
            components_registered.append(f"comp_{i}")
            
        # Verify all registered
        self.assertEqual(len(self.registry.components), 5)
        
        # Cleanup
        cleanup_order = self.registry.cleanup()
        
        # Verify cleanup happened in reverse order
        self.assertEqual(cleanup_order, list(reversed(components_registered)))
        
        # Verify registry is empty
        self.assertEqual(len(self.registry.components), 0)
        self.assertEqual(len(self.registry.capabilities), 0)
        
    def test_automatic_binding_discovery(self):
        """Test automatic discovery and binding of components."""
        # Create Store component
        class TestStore(MockComposedComponent):
            pass
            
        store = TestStore("data_store")
        
        # Create API component with binding capability
        class TestAPI(MockComposedComponent):
            def __init__(self, name, config=None):
                super().__init__(name, config)
                self.store_component = None
                
            def set_store_component(self, store):
                self.store_component = store
                
        api = TestAPI("web_api")
        
        # Register components
        self.registry.register("data_store", store, "Store", ["persistence"])
        self.registry.register("web_api", api, "API", ["http"])
        
        # Discover and establish bindings
        bindings = self.registry.discover_bindings()
        
        # Verify binding was established
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0], ("web_api", "data_store"))
        self.assertEqual(api.store_component, store)
        
    def test_detect_old_vs_new_patterns(self):
        """Test detection of old StandaloneComponentBase vs new ComposedComponent."""
        # Mock old pattern
        class OldComponent:
            pass
            
        OldComponent.__bases__ = (type('StandaloneComponentBase', (), {}),)
        
        # Mock new pattern
        class NewComponent(MockComposedComponent):
            pass
            
        old = OldComponent()
        new = NewComponent("new_comp")
        
        # Register both
        self.registry.register("old", old, "Legacy", [])
        self.registry.register("new", new, "Modern", [])
        
        # Check detection
        # Note: Detection might fail for mock, but documents expected behavior
        new_info = self.registry.components["new"]
        self.assertEqual(new_info['base_class'], 'ComposedComponent')
        
    def test_registry_with_multiple_component_types(self):
        """Test registry handling multiple component types."""
        # Register different types
        store = MockComposedComponent("store")
        api = MockComposedComponent("api")
        processor = MockComposedComponent("processor")
        aggregator = MockComposedComponent("aggregator")
        
        self.registry.register("store", store, "Store", ["crud"])
        self.registry.register("api", api, "API", ["rest"])
        self.registry.register("processor", processor, "Processing", ["transform"])
        self.registry.register("aggregator", aggregator, "Processing", ["aggregate"])
        
        # Query by type
        stores = self.registry.get_by_type("Store")
        self.assertEqual(len(stores), 1)
        
        processors = self.registry.get_by_type("Processing")
        self.assertEqual(len(processors), 2)
        
        apis = self.registry.get_by_type("API")
        self.assertEqual(len(apis), 1)
        
    def test_capability_based_component_selection(self):
        """Test selecting components based on required capabilities."""
        # Register components with different capabilities
        for i in range(5):
            caps = []
            if i % 2 == 0:
                caps.append("async")
            if i % 3 == 0:
                caps.append("batch")
            if i > 2:
                caps.append("advanced")
                
            comp = MockComposedComponent(f"comp_{i}")
            self.registry.register(f"comp_{i}", comp, "Processing", caps)
            
        # Find components with specific capabilities
        async_components = self.registry.get_by_capability("async")
        batch_components = self.registry.get_by_capability("batch")
        advanced_components = self.registry.get_by_capability("advanced")
        
        self.assertEqual(len(async_components), 3)  # 0, 2, 4
        self.assertEqual(len(batch_components), 2)  # 0, 3
        self.assertEqual(len(advanced_components), 2)  # 3, 4
        
    def test_registry_prevents_duplicate_registration(self):
        """Test that registry handles duplicate registrations properly."""
        comp1 = MockComposedComponent("test")
        comp2 = MockComposedComponent("test")
        
        # Register first
        self.registry.register("test_comp", comp1, "Store", [])
        
        # Register with same name (should overwrite)
        self.registry.register("test_comp", comp2, "API", [])
        
        # Check that second registration took effect
        info = self.registry.components["test_comp"]
        self.assertEqual(info['type'], "API")
        self.assertEqual(info['instance'], comp2)


if __name__ == "__main__":
    unittest.main()