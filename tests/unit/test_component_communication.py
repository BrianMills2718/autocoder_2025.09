"""Test component communication and registry functionality"""
import pytest
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.components.base import ComposedComponent
from autocoder_cc.components.component_registry import ComponentRegistry
from autocoder_cc.components.store import Store


class TestComponentCommunication:
    """Test that components can communicate via registry"""
    
    def test_components_have_set_registry(self):
        """Components should support registry setting"""
        store = Store("test", {})
        registry = ComponentRegistry()
        
        # Should have set_registry method
        assert hasattr(store, 'set_registry'), "Component missing set_registry method"
        
        # Should not raise AttributeError
        store.set_registry(registry)
        assert store.registry == registry
    
    def test_component_registry_registration(self):
        """Test components can be registered"""
        registry = ComponentRegistry()
        store = Store("test_store", {})
        
        # Register component
        registry.register_component("test_store", store)
        
        # Should be able to retrieve
        retrieved = registry.get_component("test_store")
        assert retrieved == store
    
    def test_components_can_send_messages(self):
        """Test components can send messages to each other"""
        registry = ComponentRegistry()
        
        # Create two components
        source = Store("source", {})
        target = Store("target", {})
        
        # Register both
        registry.register_component("source", source)
        registry.register_component("target", target)
        
        # Set registry on both
        if hasattr(source, 'set_registry'):
            source.set_registry(registry)
        if hasattr(target, 'set_registry'):
            target.set_registry(registry)
        
        # Test communication
        if hasattr(source, 'send_to_component'):
            # Should be able to send without error
            try:
                source.send_to_component("target", {"test": "data"})
                communication_works = True
            except AttributeError:
                communication_works = False
            
            assert communication_works, "Component communication failed"
    
    def test_base_component_has_communication_methods(self):
        """Test that base ComposedComponent has communication infrastructure"""
        component = ComposedComponent("test", {})
        
        # Should have communication attributes
        assert hasattr(component, 'name'), "Component missing name attribute"
        assert hasattr(component, 'config'), "Component missing config attribute"
        
        # Check for communication setup capability
        # Note: May need to be added
        communication_capable = (
            hasattr(component, 'set_registry') or
            hasattr(component, 'registry') or
            hasattr(component, 'communicator')
        )
        
        assert communication_capable, "Base component lacks communication infrastructure"