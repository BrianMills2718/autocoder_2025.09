#!/usr/bin/env python3
"""
Test the ComposedComponent base class.
This defines the contract that ALL components must follow.
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from autocoder_cc.components.composed_base import ComposedComponent


class TestComposedComponentContract:
    """Test the base component contract that all components must follow"""
    
    def test_component_can_be_instantiated(self):
        """Test that ComposedComponent can be instantiated with name and config"""
        config = {"test": "value"}
        component = ComposedComponent("test_component", config)
        
        assert component.name == "test_component"
        assert component.config == config
        assert hasattr(component, 'logger')
        assert hasattr(component, 'error_handler')
        assert hasattr(component, 'metrics_collector')
    
    def test_component_has_required_methods(self):
        """Test that component has all required lifecycle methods"""
        component = ComposedComponent("test", {})
        
        # Required async methods
        assert hasattr(component, 'setup')
        assert asyncio.iscoroutinefunction(component.setup)
        
        assert hasattr(component, 'process')
        assert asyncio.iscoroutinefunction(component.process)
        
        assert hasattr(component, 'cleanup')
        assert asyncio.iscoroutinefunction(component.cleanup)
        
        # DO NOT check for teardown - it doesn't exist!
        assert not hasattr(component, 'teardown'), "Component should NOT have teardown method"
    
    @pytest.mark.asyncio
    async def test_setup_method_signature(self):
        """Test that setup method accepts harness_context parameter"""
        component = ComposedComponent("test", {})
        
        # Should accept optional harness_context
        harness_context = {"components": {}, "config": {}}
        
        # This should not raise an error
        await component.setup(harness_context)
        
        # Should also work without context
        await component.setup()
        await component.setup(None)
    
    @pytest.mark.asyncio
    async def test_process_method_signature(self):
        """Test that process method has correct signature"""
        component = ComposedComponent("test", {})
        
        # process() takes no arguments (besides self)
        # This should not raise an error
        await component.process()
    
    @pytest.mark.asyncio
    async def test_cleanup_method_signature(self):
        """Test that cleanup method has correct signature"""
        component = ComposedComponent("test", {})
        
        # cleanup() takes no arguments (besides self)
        await component.cleanup()
    
    def test_component_has_observability(self):
        """Test that component has observability features"""
        component = ComposedComponent("test", {})
        
        # Should have logger
        assert hasattr(component, 'logger')
        assert component.logger is not None
        
        # Should have metrics collector
        assert hasattr(component, 'metrics_collector')
        assert component.metrics_collector is not None
        
        # Should have error handler
        assert hasattr(component, 'error_handler')
        assert component.error_handler is not None
        
        # Should have tracer
        assert hasattr(component, 'tracer')
        assert component.tracer is not None
    
    def test_component_capabilities(self):
        """Test that component can have capabilities"""
        config = {
            "retry_enabled": True,
            "circuit_breaker_enabled": False,
            "rate_limiter_enabled": False,
            "metrics_enabled": True
        }
        component = ComposedComponent("test", config)
        
        assert hasattr(component, 'capabilities')
        assert isinstance(component.capabilities, dict)
    
    def test_metrics_collector_increment(self):
        """Test that metrics collector has correct increment signature"""
        component = ComposedComponent("test", {})
        
        if component.metrics_collector and hasattr(component.metrics_collector, 'increment'):
            # Should accept name and optional tags
            # Should NOT require a value parameter
            try:
                # This is the correct usage
                component.metrics_collector.increment('test_metric')
                component.metrics_collector.increment('test_metric', {'tag': 'value'})
            except TypeError as e:
                pytest.fail(f"Metrics increment has wrong signature: {e}")


class TestComponentImplementation:
    """Test that components following the reference pattern work correctly"""
    
    @pytest.mark.asyncio
    async def test_reference_store_pattern(self):
        """Test that a Store component following reference pattern works"""
        # Import our reference Store to test
        from tests.unit.core.test_store_reference import TaskStore
        
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        
        # Verify it's a ComposedComponent
        assert isinstance(store, ComposedComponent)
        
        # Test lifecycle
        await store.setup()
        assert store.running == True
        
        # Test it has process_item for data handling
        assert hasattr(store, 'process_item')
        
        # Test data operation
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Test'}
        })
        assert result['status'] == 'success'
        assert 'id' in result
        
        # Test cleanup
        await store.cleanup()
        assert store.running == False
    
    @pytest.mark.asyncio
    async def test_reference_api_pattern(self):
        """Test that an API component following reference pattern works"""
        from tests.unit.core.test_api_reference import TaskAPI
        
        config = {"port": 8081, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Verify it's a ComposedComponent
        assert isinstance(api, ComposedComponent)
        
        # Test it has required attributes
        assert hasattr(api, 'app')  # FastAPI app
        assert api.port == 8081
        assert api.host == "127.0.0.1"
        
        # Test lifecycle methods exist
        assert hasattr(api, 'setup')
        assert hasattr(api, 'process')
        assert hasattr(api, 'cleanup')
        
        # Test setup
        await api.setup()
        assert api.server is not None
        
        # Cleanup
        await api.cleanup()


class TestComponentValidation:
    """Tests that validate whether a component is correctly implemented"""
    
    def validate_component_structure(self, component_class):
        """Validate that a component class has correct structure"""
        # Should inherit from ComposedComponent
        assert issubclass(component_class, ComposedComponent), \
            f"{component_class.__name__} must inherit from ComposedComponent"
        
        # Should have correct __init__ signature
        import inspect
        sig = inspect.signature(component_class.__init__)
        params = list(sig.parameters.keys())
        
        # Should have self, name, and config parameters
        assert 'self' in params, "Missing self parameter"
        assert 'name' in params or params[1] == 'name', "Second parameter should be 'name'"
        assert 'config' in params or params[2] == 'config', "Third parameter should be 'config'"
        
        return True
    
    def validate_lifecycle_methods(self, component_instance):
        """Validate that a component instance has correct lifecycle methods"""
        # Must have setup, process, cleanup
        assert hasattr(component_instance, 'setup'), "Missing setup method"
        assert hasattr(component_instance, 'process'), "Missing process method"
        assert hasattr(component_instance, 'cleanup'), "Missing cleanup method"
        
        # Must NOT have teardown
        assert not hasattr(component_instance, 'teardown'), \
            "Should not have teardown method, use cleanup instead"
        
        # Methods must be async
        assert asyncio.iscoroutinefunction(component_instance.setup), \
            "setup must be async"
        assert asyncio.iscoroutinefunction(component_instance.process), \
            "process must be async"
        assert asyncio.iscoroutinefunction(component_instance.cleanup), \
            "cleanup must be async"
        
        return True
    
    def test_validate_reference_store(self):
        """Validate that reference TaskStore meets requirements"""
        from tests.unit.core.test_store_reference import TaskStore
        
        # Validate class structure
        assert self.validate_component_structure(TaskStore)
        
        # Validate instance
        store = TaskStore("test", {})
        assert self.validate_lifecycle_methods(store)
    
    def test_validate_reference_api(self):
        """Validate that reference TaskAPI meets requirements"""
        from tests.unit.core.test_api_reference import TaskAPI
        
        # Validate class structure
        assert self.validate_component_structure(TaskAPI)
        
        # Validate instance
        api = TaskAPI("test", {})
        assert self.validate_lifecycle_methods(api)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])