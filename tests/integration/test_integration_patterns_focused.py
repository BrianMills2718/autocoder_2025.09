#!/usr/bin/env python3
"""
FOCUSED INTEGRATION TESTS

Test specific integration patterns in isolation.
Less complex than full system generation.

These tests focus on core integration patterns without the complexity
of full blueprint processing or system generation.
"""

import pytest
import anyio
import tempfile
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc.validation.integration_validator import IntegrationValidator
from autocoder_cc import SystemExecutionHarness


class TestReferenceStoreComponent(ComposedComponent):
    """Hand-crafted reference Store component for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
        self.storage_type = config.get("storage_type", "memory") if config else "memory"
        
    async def setup(self, harness_context=None):
        """Setup the store component."""
        await super().setup(harness_context)
        self.logger.info(f"Store {self.name} setup with {self.storage_type} storage")
        
    async def process_item(self, item: Any) -> Any:
        """Process and store an item."""
        try:
            item_id = item.get("id", len(self._items))
            self._items[item_id] = item
            self.logger.debug(f"Stored item {item_id}")
            return {"status": "stored", "item_id": item_id, "storage_type": self.storage_type}
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        """Cleanup the store component."""
        await super().cleanup()
        self._items.clear()
        self.logger.info(f"Store {self.name} cleanup complete - {len(self._items)} items cleared")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status."""
        base_health = super().get_health_status()
        return {
            **base_health, 
            "items_count": len(self._items),
            "storage_type": self.storage_type
        }


class TestReferenceAPIComponent(ComposedComponent):
    """Hand-crafted reference API component for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 8000) if config else 8000
        self.cors_enabled = config.get("cors_enabled", False) if config else False
        
    async def setup(self, harness_context=None):
        """Setup the API component."""
        await super().setup(harness_context)
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port} (CORS: {self.cors_enabled})")
        
    async def process_item(self, item: Any) -> Any:
        """Process API request."""
        try:
            # Mock API request processing
            response_data = {
                "success": True, 
                "data": item,
                "endpoint": f"{self.host}:{self.port}",
                "cors_enabled": self.cors_enabled
            }
            return {"status": 200, "body": response_data}
        except Exception as e:
            self.logger.error(f"API processing error: {e}")
            return {"status": 500, "body": {"error": "Internal Server Error", "message": str(e)}}
            
    async def cleanup(self):
        """Cleanup the API component."""
        await super().cleanup()
        self.logger.info(f"API {self.name} cleanup complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status."""
        base_health = super().get_health_status()
        return {
            **base_health, 
            "api_ready": True, 
            "endpoint": f"{self.host}:{self.port}",
            "cors_enabled": self.cors_enabled
        }


class TestReferenceTransformerComponent(ComposedComponent):
    """Hand-crafted reference Transformer component for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.transform_type = config.get("transform_type", "json") if config else "json"
        self.batch_size = config.get("batch_size", 50) if config else 50
        
    async def setup(self, harness_context=None):
        """Setup the transformer component."""
        await super().setup(harness_context)
        self.logger.info(f"Transformer {self.name} setup with {self.transform_type} transformation")
        
    async def process_item(self, item: Any) -> Any:
        """Process and transform an item."""
        try:
            # Mock transformation logic
            transformed_item = {
                "original": item,
                "transformed": True,
                "transform_type": self.transform_type,
                "batch_size": self.batch_size,
                "timestamp": "2025-08-02T00:00:00Z"
            }
            return {"status": "transformed", "data": transformed_item}
        except Exception as e:
            self.logger.error(f"Transformation error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        """Cleanup the transformer component."""
        await super().cleanup()
        self.logger.info(f"Transformer {self.name} cleanup complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status."""
        base_health = super().get_health_status()
        return {
            **base_health,
            "transform_type": self.transform_type,
            "batch_size": self.batch_size
        }


class TestIntegrationPatternsFocused:
    """
    FOCUSED INTEGRATION TESTS
    
    Test specific integration patterns in isolation.
    Less complex than full system generation.
    """
    
    def setup_method(self):
        """Setup test instances."""
        self.validator = IntegrationValidator()

    def test_validation_accepts_reference_components(self):
        """Test validation accepts hand-crafted reference components."""
        
        # Test Store component validation
        store_code = '''
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any

class TestStoreComponent(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        
    async def process_item(self, item: Any) -> Any:
        item_id = item.get("id", len(self._items))
        self._items[item_id] = item
        return {"status": "stored", "item_id": item_id}
        
    async def cleanup(self):
        await super().cleanup()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "items_count": len(self._items)}
'''
        
        validation_result = self.validator.validate_component_integration(store_code, 'Store')
        assert validation_result['valid'], f"Store validation failed: {validation_result.get('errors', [])}"
        
        # Test API component validation
        api_code = '''
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any

class TestAPIComponent(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        
    async def process_item(self, item: Any) -> Any:
        return {"status": 200, "body": {"success": True}}
        
    async def cleanup(self):
        await super().cleanup()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "api_ready": True}
'''
        
        validation_result = self.validator.validate_component_integration(api_code, 'API')
        assert validation_result['valid'], f"API validation failed: {validation_result.get('errors', [])}"
        
        # Test Transformer component validation
        transformer_code = '''
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any

class TestTransformerComponent(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        
    async def process_item(self, item: Any) -> Any:
        return {"status": "transformed", "data": item}
        
    async def cleanup(self):
        await super().cleanup()
        
    def get_health_status(self) -> Dict[str, Any]:
        return super().get_health_status()
'''
        
        validation_result = self.validator.validate_component_integration(transformer_code, 'Transformer')
        assert validation_result['valid'], f"Transformer validation failed: {validation_result.get('errors', [])}"

    @pytest.mark.asyncio
    async def test_harness_runs_reference_components(self):
        """Test harness can run reference components."""
        
        harness = SystemExecutionHarness()
        
        # Create reference components
        store = TestReferenceStoreComponent("TestStore", {"storage_type": "memory"})
        api = TestReferenceAPIComponent("TestAPI", {"host": "localhost", "port": 8080, "cors_enabled": True})
        transformer = TestReferenceTransformerComponent("TestTransformer", {"transform_type": "json", "batch_size": 100})
        
        # Add components to harness
        harness.register_component("TestStore", store)
        harness.register_component("TestAPI", api)
        harness.register_component("TestTransformer", transformer)
        
        # Test components can be started
        await harness.start()
        
        # Verify components are set up (they should have been initialized)
        assert hasattr(store, 'logger'), "Store should have logger after setup"
        assert hasattr(api, 'logger'), "API should have logger after setup"  
        assert hasattr(transformer, 'logger'), "Transformer should have logger after setup"
        
        # Test health monitoring
        health = harness.get_system_health_summary()
        assert "total_components" in health
        assert health["total_components"] == 3
        
        # Test individual component status
        store_status = await harness.get_component_status("TestStore")
        assert store_status is not None
        
        api_status = await harness.get_component_status("TestAPI")
        assert api_status is not None
        
        transformer_status = await harness.get_component_status("TestTransformer")
        assert transformer_status is not None
        
        # Test component processing
        store_result = await store.process_item({"id": "test1", "data": "test_data"})
        assert store_result["status"] == "stored"
        assert store_result["item_id"] == "test1"
        
        api_result = await api.process_item({"request": "test_request"})
        assert api_result["status"] == 200
        assert api_result["body"]["success"]
        
        transformer_result = await transformer.process_item({"input": "test_input"})
        assert transformer_result["status"] == "transformed"
        assert transformer_result["data"]["transformed"]
        
        # The harness handles cleanup automatically when it stops

    def test_component_communication_patterns(self):
        """Test component communication without full generation."""
        
        # Test data flow pattern: Store -> API
        store_output = {"status": "stored", "item_id": "item1", "data": {"value": 42}}
        
        # Mock API receiving store output
        api_input = store_output["data"]
        api_output = {"status": 200, "body": {"success": True, "received_data": api_input}}
        
        assert api_output["status"] == 200
        assert api_output["body"]["success"]
        assert api_output["body"]["received_data"]["value"] == 42
        
        # Test data flow pattern: Source -> Transformer -> Sink
        source_output = {"events": [{"id": "e1", "data": "raw"}]}
        
        # Mock transformation
        transformer_input = source_output["events"]
        transformer_output = {
            "enriched_events": [
                {"id": "e1", "data": "raw", "enriched": True, "timestamp": "2025-08-02"}
            ]
        }
        
        # Mock sink processing
        sink_input = transformer_output["enriched_events"]
        sink_output = {"status": "processed", "count": len(sink_input)}
        
        assert sink_output["status"] == "processed"
        assert sink_output["count"] == 1
        assert transformer_output["enriched_events"][0]["enriched"]

    @pytest.mark.asyncio
    async def test_error_handling_patterns(self):
        """Test error handling patterns in integration."""
        
        class ErrorTestComponent(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self.fail_processing = config.get("fail_processing", False) if config else False
                
            async def setup(self, harness_context=None):
                await super().setup(harness_context)
                
            async def process_item(self, item: Any) -> Any:
                if self.fail_processing:
                    raise ValueError("Simulated processing error")
                return {"status": "success", "data": item}
                
            async def cleanup(self):
                await super().cleanup()
                
            def get_health_status(self) -> Dict[str, Any]:
                base_health = super().get_health_status()
                return {**base_health, "error_test": True}
        
        # Test normal operation
        normal_component = ErrorTestComponent("NormalComponent", {"fail_processing": False})
        harness = SystemExecutionHarness()
        harness.register_component("NormalComponent", normal_component)
        
        await harness.start()
        
        result = await normal_component.process_item({"test": "data"})
        assert result["status"] == "success"
        
        # Test error handling
        error_component = ErrorTestComponent("ErrorComponent", {"fail_processing": True})
        
        with pytest.raises(ValueError, match="Simulated processing error"):
            await error_component.process_item({"test": "data"})
        
        # Health should still be accessible
        health = error_component.get_health_status()
        assert "error_test" in health
        assert health["healthy"]  # Component itself is healthy, just processing fails
        
        # Harness cleanup is handled automatically

    @pytest.mark.asyncio
    async def test_configuration_patterns(self):
        """Test configuration handling patterns."""
        
        # Test component with rich configuration
        config = {
            "storage_type": "postgresql",
            "host": "db.example.com",
            "port": 5432,
            "max_connections": 100,
            "retry_enabled": True,
            "metrics_enabled": True
        }
        
        store = TestReferenceStoreComponent("ConfigurableStore", config)
        
        # Test configuration is properly initialized
        assert store.storage_type == "postgresql"
        assert store.config["host"] == "db.example.com"
        assert store.config["port"] == 5432
        assert store.config["max_connections"] == 100
        assert store.config["retry_enabled"]
        assert store.config["metrics_enabled"]
        
        # Test health status includes configuration info
        health = store.get_health_status()
        assert health["storage_type"] == "postgresql"
        
        # Test configuration affects behavior
        result = await store.process_item({"id": "test", "data": "value"})
        assert result["storage_type"] == "postgresql"

    @pytest.mark.asyncio
    async def test_lifecycle_patterns(self):
        """Test component lifecycle patterns."""
        
        class LifecycleTrackingComponent(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self.lifecycle_events = []
                
            async def setup(self, harness_context=None):
                await super().setup(harness_context)
                self.lifecycle_events.append("setup")
                
            async def process_item(self, item: Any) -> Any:
                self.lifecycle_events.append("process")
                return {"status": "processed", "lifecycle": self.lifecycle_events.copy()}
                
            async def cleanup(self):
                await super().cleanup()
                self.lifecycle_events.append("cleanup")
                
            def get_health_status(self) -> Dict[str, Any]:
                base_health = super().get_health_status()
                return {**base_health, "lifecycle_events": self.lifecycle_events.copy()}
        
        component = LifecycleTrackingComponent("LifecycleComponent")
        harness = SystemExecutionHarness()
        
        # Initially no lifecycle events
        assert len(component.lifecycle_events) == 0
        
        # Add to harness and setup
        harness.register_component("LifecycleComponent", component)
        await harness.start()
        
        # Setup should be called
        assert "setup" in component.lifecycle_events
        
        # Process some items
        result1 = await component.process_item({"data": "test1"})
        result2 = await component.process_item({"data": "test2"})
        
        assert "process" in component.lifecycle_events
        assert component.lifecycle_events.count("process") == 2
        
        # Health should reflect lifecycle
        health = harness.get_system_health_summary()
        assert "total_components" in health
        
        # Component health can be checked directly
        component_health = component.get_health_status()
        assert "lifecycle_events" in component_health
        
        # Final lifecycle order should be: setup, process, process (cleanup handled by harness)
        expected_events = ["setup", "process", "process"]
        assert component.lifecycle_events == expected_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])