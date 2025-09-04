#!/usr/bin/env python3
"""
Test Component Loading - Verify component registry and loading
Part of the CLAUDE.md critical fixes verification
"""
import pytest
import sys
import os

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestComponentLoading:
    """Verify component loading and registry works correctly"""
    
    def test_component_registry_initialized(self):
        """Test component registry is properly initialized"""
        from autocoder_cc.components.component_registry import component_registry
        
        assert component_registry is not None
        assert hasattr(component_registry, 'components')
        assert len(component_registry.components) > 0
        
    def test_built_in_components_registered(self):
        """Test all built-in component types are registered"""
        from autocoder_cc.components.component_registry import component_registry
        
        expected_components = [
            'Source', 'Sink', 'Transformer', 'Store', 
            'Controller', 'APIEndpoint', 'Model',
            'Router', 'Aggregator', 'Filter', 'Accumulator',
            'StreamProcessor', 'WebSocket'
        ]
        
        for component_type in expected_components:
            assert component_type in component_registry.components, \
                f"Component type '{component_type}' not registered"
                
    def test_component_instantiation(self):
        """Test components can be instantiated"""
        from autocoder_cc.components.component_registry import component_registry
        
        # Test Source component
        source_class = component_registry.get_component_class('Source')
        assert source_class is not None
        
        # Create instance
        source = source_class(name="test_source", config={})
        assert source.name == "test_source"
        assert hasattr(source, 'setup')
        assert hasattr(source, 'process')
        assert hasattr(source, 'cleanup')
        
    def test_component_registry_methods(self):
        """Test component registry methods work correctly"""
        from autocoder_cc.components.component_registry import component_registry
        
        # Test get_component_class
        transformer_class = component_registry.get_component_class('Transformer')
        assert transformer_class is not None
        
        # Test get_all_component_types
        all_types = component_registry.get_all_component_types()
        assert isinstance(all_types, list)
        assert 'Source' in all_types
        assert 'Sink' in all_types
        
    def test_composed_component(self):
        """Test ComposedComponent base class"""
        from autocoder_cc.components.composed_base import ComposedComponent
        
        # Create a test composed component
        class TestComponent(ComposedComponent):
            pass
            
        component = TestComponent(name="test", config={})
        assert component.name == "test"
        assert hasattr(component, 'receive_streams')
        assert hasattr(component, 'send_streams')
        
    def test_component_capabilities(self):
        """Test component capability detection"""
        from autocoder_cc.components.component_registry import component_registry
        
        # APIEndpoint should have REST capability
        api_class = component_registry.get_component_class('APIEndpoint')
        assert api_class is not None
        
        # Store should have persistence capability
        store_class = component_registry.get_component_class('Store')
        assert store_class is not None
        
    def test_dynamic_component_loading(self):
        """Test dynamic component loading functionality"""
        from autocoder_cc.orchestration.dynamic_loader import DynamicComponentLoader
        
        loader = DynamicComponentLoader()
        assert loader is not None
        
        # Test loader can find built-in components
        source_path = loader._find_component_class('Source')
        assert source_path is not None
        
    def test_component_validation(self):
        """Test component validation in registry"""
        from autocoder_cc.components.component_registry import component_registry
        
        # Test invalid component type
        invalid_class = component_registry.get_component_class('InvalidType')
        assert invalid_class is None
        
        # Test case sensitivity
        source_lower = component_registry.get_component_class('source')
        assert source_lower is None  # Should be case sensitive
        
    def test_standalone_component_base(self):
        """Test StandaloneComponentBase detection"""
        from autocoder_cc.tests.tools.component_test_runner import ComponentTestRunner
        
        runner = ComponentTestRunner()
        
        # Create a mock module with StandaloneComponentBase
        class MockModule:
            class StandaloneComponentBase:
                pass
                
            class TestComponent(StandaloneComponentBase):
                pass
                
        # Test component finder recognizes StandaloneComponentBase
        found = runner._find_component_class(MockModule)
        assert found == 'TestComponent'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])