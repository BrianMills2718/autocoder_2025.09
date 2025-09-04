#!/usr/bin/env python3
"""
MOCKED INTEGRATION TESTS

These tests mock the complex blueprint parsing and LLM generation 
to focus on testing integration patterns. Full end-to-end tests 
without mocks are needed in Phase 2.

MOCKED: Blueprint parsing and LLM generation (SystemGenerator.generate_system_from_yaml)
TESTED: Validation, component integration, harness behavior
"""

import pytest
import anyio
import tempfile
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.validation.integration_validator import IntegrationValidator
from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc import SystemExecutionHarness


class MockGenerationResult:
    """Mock generation result that mimics real system generation output."""
    
    def __init__(self, components, scaffold):
        self.components = components
        self.scaffold = scaffold


class MockComponent:
    """Mock component that mimics generated component structure."""
    
    def __init__(self, name: str, component_type: str, implementation: str):
        self.name = name
        self.component_type = component_type
        self.implementation = implementation


class MockScaffold:
    """Mock scaffold that mimics generated scaffold structure."""
    
    def __init__(self, main_file_content: str):
        self.main_file_content = main_file_content


class TestReferenceIntegrationMocked:
    """
    MOCKED INTEGRATION TESTS
    
    These tests mock the complex blueprint parsing and LLM generation 
    to focus on testing integration patterns. Full end-to-end tests 
    without mocks are needed in Phase 2.
    
    MOCKED: SystemGenerator.generate_system_from_yaml()
    TESTED: Validation, component integration, harness behavior
    """
    
    def setup_method(self):
        """Setup test instances."""
        self.temp_dir = tempfile.mkdtemp()
        self.system_generator = SystemGenerator(output_dir=self.temp_dir)
        self.validator = IntegrationValidator()
        
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_system_generation_with_reference_patterns_MOCKED(self):
        """
        MOCKED TEST - LIMITED SCOPE
        
        This test mocks system generation to focus on testing integration patterns.
        
        MOCKED: SystemGenerator.generate_system_from_yaml() - returns reference-compliant components
        TESTED: Validation accepts reference patterns, component structure validation
        LIMITATIONS: Does not test actual blueprint parsing or LLM generation
        E2E REQUIRED: Full blueprint-to-component generation pipeline
        """
        
        # Mock reference-compliant Store component
        store_implementation = '''#!/usr/bin/env python3
"""Generated Store component using ComposedComponent patterns."""

from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any
import asyncio


class MockStoreComponent(ComposedComponent):
    """Store component with reference implementation patterns."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
        
    async def setup(self, harness_context=None):
        """Setup the store component."""
        await super().setup(harness_context)
        self.logger.info(f"Store {self.name} setup complete")
        
    async def process_item(self, item: Any) -> Any:
        """Process and store an item."""
        try:
            item_id = item.get("id", len(self._items))
            self._items[item_id] = item
            return {"status": "stored", "item_id": item_id}
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        """Cleanup the store component."""
        await super().cleanup()
        self.logger.info(f"Store {self.name} cleanup complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status."""
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "items_count": len(self._items)}
'''

        # Mock reference-compliant API component
        api_implementation = '''#!/usr/bin/env python3
"""Generated API component using ComposedComponent patterns."""

from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any
import asyncio


class MockAPIComponent(ComposedComponent):
    """API component with reference implementation patterns."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 8000)
        
    async def setup(self, harness_context=None):
        """Setup the API component."""
        await super().setup(harness_context)
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port}")
        
    async def process_item(self, item: Any) -> Any:
        """Process API request."""
        try:
            # Mock API processing
            return {"status": 200, "body": {"success": True, "data": item}}
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
        return {**base_health, "status": "healthy", "api_ready": True, "endpoint": f"{self.host}:{self.port}"}
'''

        # Mock scaffold with proper SystemExecutionHarness usage
        scaffold_main = '''#!/usr/bin/env python3
"""Generated system main file using reference patterns."""

import asyncio
from autocoder_cc import SystemExecutionHarness
from autocoder_cc.components.composed_base import ComposedComponent


async def main():
    """Main system execution using SystemExecutionHarness."""
    harness = SystemExecutionHarness()
    
    # Add components with reference patterns
    store = MockStoreComponent("TestStore", {"storage_type": "memory"})
    api = MockAPIComponent("TestAPI", {"host": "localhost", "port": 8000})
    
    harness.register_component("TestStore", store)
    harness.register_component("TestAPI", api)
    
    # Start the system
    await harness.run()  # This handles full lifecycle


if __name__ == "__main__":
    asyncio.run(main())
'''

        # Create mock components
        mock_components = [
            MockComponent("TestStore", "Store", store_implementation),
            MockComponent("TestAPI", "API", api_implementation)
        ]
        
        # Create mock scaffold
        mock_scaffold = MockScaffold(scaffold_main)
        
        # Create mock generation result
        mock_result = MockGenerationResult(mock_components, mock_scaffold)

        # Mock the system generator
        with patch.object(self.system_generator, 'generate_system_from_yaml', return_value=mock_result) as mock_gen:
            
            # Test system generation with mocked result
            blueprint_yaml = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: Mocked integration test system

system:
  name: mocked_test_system
  description: System for testing mocked integration
  version: 1.0.0
  components:
    - name: TestStore
      type: Store
      description: Test storage component
    - name: TestAPI  
      type: API
      description: Test API component
"""
            
            generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
            
            # Verify mock was called
            mock_gen.assert_called_once_with(blueprint_yaml)
            
            # Test the mocked result has expected structure
            assert generation_result is not None
            assert hasattr(generation_result, 'components')
            assert hasattr(generation_result, 'scaffold')
            
            # Validate generated components follow reference patterns
            generated_components = generation_result.components
            assert len(generated_components) == 2
            
            for component in generated_components:
                assert hasattr(component, 'implementation')
                assert hasattr(component, 'component_type')
                
                component_code = component.implementation
                component_type = component.component_type
                
                # Verify reference patterns are present
                assert "ComposedComponent" in component_code
                assert "StandaloneComponentBase" not in component_code
                assert "async def setup" in component_code
                assert "async def process_item" in component_code
                assert "async def cleanup" in component_code
                assert "get_health_status" in component_code
                
                # Test validation accepts the component
                validation_result = self.validator.validate_component_integration(component_code, component_type)
                assert validation_result['valid'], f"Validation failed for {component.name}: {validation_result.get('errors', [])}"
            
            # Validate scaffold uses reference patterns
            scaffold = generation_result.scaffold
            main_content = scaffold.main_file_content
            
            assert "SystemExecutionHarness" in main_content
            assert "ComposedComponent" in main_content
            assert "harness.register_component" in main_content
            assert "harness.run()" in main_content

    @pytest.mark.asyncio  
    async def test_component_validation_integration_MOCKED(self):
        """
        MOCKED TEST - LIMITED SCOPE
        
        This test mocks component generation to focus on validation integration.
        
        MOCKED: Component generation - uses hand-crafted reference components
        TESTED: Validation pipeline accepts reference patterns, integration validator behavior
        LIMITATIONS: Does not test actual LLM-generated code validation
        E2E REQUIRED: Validation of real LLM-generated components
        """
        
        # Hand-crafted reference-compliant component
        reference_store_code = '''
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any


class ValidatedStoreComponent(ComposedComponent):
    """Reference implementation for validation testing."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._storage = {}
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        self.logger.info("Validated store setup")
        
    async def process_item(self, item: Any) -> Any:
        item_id = item.get("id", len(self._storage))
        self._storage[item_id] = item
        return {"status": "stored", "item_id": item_id}
        
    async def cleanup(self):
        await super().cleanup()
        self._storage.clear()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "items_stored": len(self._storage)}
'''

        # Test validation accepts reference patterns
        validation_result = self.validator.validate_component_integration(reference_store_code, 'Store')
        assert validation_result['valid'], f"Reference component validation failed: {validation_result.get('errors', [])}"
        
        # Test validation rejects non-reference patterns
        invalid_component_code = '''
class InvalidComponent:
    """Non-ComposedComponent implementation."""
    
    def process(self, data):
        return data
'''
        
        invalid_result = self.validator.validate_component_integration(invalid_component_code, 'Store')
        assert not invalid_result['valid'], "Validation should reject non-ComposedComponent implementations"
        
        # Test validation handles edge cases
        empty_code = ""
        empty_result = self.validator.validate_component_integration(empty_code, 'Store')
        assert not empty_result['valid'], "Validation should reject empty code"

    @pytest.mark.asyncio
    async def test_harness_integration_with_generated_components_MOCKED(self):
        """
        MOCKED TEST - LIMITED SCOPE
        
        This test mocks component generation to focus on harness integration.
        
        MOCKED: Component generation - uses mock ComposedComponent instances
        TESTED: SystemExecutionHarness lifecycle, component management, health monitoring
        LIMITATIONS: Does not test harness with real generated components
        E2E REQUIRED: Harness integration with actual LLM-generated components
        """
        
        # Create mock components that follow ComposedComponent patterns
        class MockHarnessStore(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self.setup_called = False
                self.cleanup_called = False
                self._items = {}
                
            async def setup(self, harness_context=None):
                await super().setup(harness_context)
                self.setup_called = True
                
            async def process_item(self, item: Any) -> Any:
                self._items[item.get("id", len(self._items))] = item
                return {"status": "stored", "item_id": item.get("id")}
                
            async def cleanup(self):
                await super().cleanup()
                self.cleanup_called = True
                
            def get_health_status(self) -> Dict[str, Any]:
                base_health = super().get_health_status()
                return {**base_health, "status": "healthy", "items_count": len(self._items)}

        class MockHarnessAPI(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self.setup_called = False
                self.cleanup_called = False
                
            async def setup(self, harness_context=None):
                await super().setup(harness_context)
                self.setup_called = True
                
            async def process_item(self, item: Any) -> Any:
                return {"status": 200, "body": {"success": True}}
                
            async def cleanup(self):
                await super().cleanup()
                self.cleanup_called = True
                
            def get_health_status(self) -> Dict[str, Any]:
                base_health = super().get_health_status()
                return {**base_health, "status": "healthy", "api_ready": True}

        # Test harness integration
        harness = SystemExecutionHarness()
        
        # Create mock components
        store = MockHarnessStore("MockStore", {"storage_type": "memory"})
        api = MockHarnessAPI("MockAPI", {"host": "localhost", "port": 8001})
        
        # Add components to harness
        harness.register_component("MockStore", store)
        harness.register_component("MockAPI", api)
        
        # Test harness lifecycle management (using start method to initialize components)
        await harness.start()
        
        # For testing, we need to verify components can be started
        # Since start() starts in background, we'll test the health monitoring directly
        
        # Test health monitoring integration
        health = harness.get_system_health_summary()
        assert "total_components" in health
        assert health["total_components"] == 2
        
        # Test individual component health
        store_status = await harness.get_component_status("MockStore")
        assert store_status is not None
        
        api_status = await harness.get_component_status("MockAPI")
        assert api_status is not None

    @pytest.mark.asyncio
    async def test_integration_error_handling_MOCKED(self):
        """
        MOCKED TEST - LIMITED SCOPE
        
        This test mocks error scenarios to test integration error handling.
        
        MOCKED: Component behavior - uses components that simulate errors
        TESTED: Error handling integration, graceful degradation, error propagation
        LIMITATIONS: Does not test real error scenarios from generated components  
        E2E REQUIRED: Error handling with actual generated component failures
        """
        
        class ErrorMockComponent(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self.should_fail_setup = config.get("fail_setup", False)
                self.should_fail_processing = config.get("fail_processing", False)
                
            async def setup(self, harness_context=None):
                if self.should_fail_setup:
                    raise RuntimeError("Mock setup failure")
                await super().setup(harness_context)
                
            async def process_item(self, item: Any) -> Any:
                if self.should_fail_processing:
                    raise ValueError("Mock processing failure")
                return {"status": "success"}
                
            def get_health_status(self) -> Dict[str, Any]:
                base_health = super().get_health_status()
                return {**base_health, "mock_component": True}

        harness = SystemExecutionHarness()
        
        # Test setup error handling
        failing_component = ErrorMockComponent("FailingComponent", {"fail_setup": True})
        harness.register_component("FailingComponent", failing_component)
        
        # Test that component itself fails during setup
        with pytest.raises(RuntimeError, match="Mock setup failure"):
            await failing_component.setup()
        
        # Test processing error handling  
        harness = SystemExecutionHarness()  # Fresh harness
        processing_fail_component = ErrorMockComponent("ProcessingFailComponent", {"fail_processing": True})
        harness.register_component("ProcessingFailComponent", processing_fail_component)
        
        await harness.start()  # This should succeed
        
        # Test error during processing
        with pytest.raises(ValueError, match="Mock processing failure"):
            await processing_fail_component.process_item({"test": "data"})
        
        # Health should still work
        health = harness.get_system_health_summary()
        assert "total_components" in health
        assert health["total_components"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])