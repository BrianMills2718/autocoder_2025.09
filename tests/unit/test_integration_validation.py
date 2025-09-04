#!/usr/bin/env python3
"""
Test integration validation for reference implementation patterns.

This test suite ensures that the validation pipeline accepts reference implementation
patterns and validates ComposedComponent-based components correctly.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc.validation.integration_validator import IntegrationValidator


class TestIntegrationValidation:
    """Test that validation pipeline accepts reference implementation patterns."""
    
    def setup_method(self):
        """Setup test instances."""
        self.validator = IntegrationValidator()
        
    def test_pipeline_validates_composed_component(self):
        """Test pipeline validation accepts ComposedComponent patterns."""
        # Create a reference component code snippet
        component_code = '''
class GeneratedStore_TestStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None):
        """Initialize component resources."""
        await super().setup(harness_context)
        self.setup_called = True
    
    async def process_item(self, item: Any) -> Any:
        """Process a single item."""
        return {"status": "success", "processed": item}
    
    async def cleanup(self):
        """Clean up component resources."""
        await super().cleanup()
        self.cleanup_called = True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return component health status."""
        base_health = ComposedComponent.get_health_status(self)
        return {
            **base_health,
            "items_processed": 0
        }
'''
        
        # Test that validation accepts this component
        result = self.validator.validate_component_integration(component_code, 'Store')
        
        assert result['valid'], f"Validation failed: {result.get('errors', [])}"
        assert 'ComposedComponent' not in str(result.get('errors', []))
        
    def test_binding_validation_with_reference_patterns(self):
        """Test binding validation works with reference patterns."""
        # Mock Store component
        store_config = {
            "type": "Store",
            "class_name": "GeneratedStore_TestStore",
            "base_class": "ComposedComponent"
        }
        
        # Mock API component
        api_config = {
            "type": "API",
            "class_name": "GeneratedAPI_TestAPI", 
            "base_class": "ComposedComponent"
        }
        
        # Test binding validation
        binding_config = {
            "source": "GeneratedStore_TestStore",
            "target": "GeneratedAPI_TestAPI",
            "binding_type": "data_flow"
        }
        
        result = self.validator.validate_binding(store_config, api_config, binding_config)
        
        # Should accept reference pattern bindings
        assert result['valid'], f"Binding validation failed: {result.get('errors', [])}"
        
    def test_health_check_validation_updated(self):
        """Test health check validation accepts reference health format."""
        # Reference health status format from ComposedComponent
        health_status = {
            'name': 'test_component',
            'healthy': True,
            'component_type': 'Store',
            'capabilities': {
                'retry': {'status': 'active'},
                'metrics': {'status': 'active'}
            },
            'composition_model': 'capability_based'
        }
        
        result = self.validator.validate_health_status(health_status)
        
        assert result['valid'], f"Health validation failed: {result.get('errors', [])}"
        assert 'composition_model' in health_status
        assert health_status['composition_model'] == 'capability_based'
        
    def test_lifecycle_validation_matches_reference(self):
        """Test lifecycle validation expects setup/cleanup/get_health_status."""
        # Reference component with correct lifecycle methods
        component_methods = [
            "__init__",
            "setup", 
            "process_item",
            "cleanup",
            "get_health_status"
        ]
        
        result = self.validator.validate_lifecycle_methods(component_methods)
        
        assert result['valid'], f"Lifecycle validation failed: {result.get('errors', [])}"
        
        # Should NOT require deprecated methods
        deprecated_methods = ["teardown", "start", "stop"]
        for method in deprecated_methods:
            assert method not in result.get('required_methods', [])
            
        # Should require reference methods
        required_methods = ["setup", "cleanup", "get_health_status"]
        for method in required_methods:
            assert method in result.get('required_methods', [])
            
    def test_rejects_deprecated_patterns(self):
        """Test validation rejects deprecated StandaloneComponentBase patterns."""
        # Deprecated component code
        deprecated_code = '''
class GeneratedStore_TestStore(StandaloneComponentBase):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    def teardown(self):
        """Deprecated teardown method."""
        pass
'''
        
        result = self.validator.validate_component_integration(deprecated_code, 'Store')
        
        # Should reject deprecated patterns
        assert not result['valid'], "Should reject deprecated StandaloneComponentBase"
        assert any('StandaloneComponentBase' in str(error) for error in result.get('errors', []))
        
    def test_validates_import_statements(self):
        """Test validation accepts correct import statements for reference patterns."""
        # Correct imports for reference implementation
        correct_imports = [
            "from autocoder_cc.components.composed_base import ComposedComponent",
            "from typing import Dict, Any, Optional",
            "import asyncio"
        ]
        
        for import_stmt in correct_imports:
            result = self.validator.validate_import_statement(import_stmt)
            assert result['valid'], f"Import validation failed for: {import_stmt}"
            
        # Incorrect/deprecated imports  
        incorrect_imports = [
            "from autocoder_cc.components.standalone_base import StandaloneComponentBase",
            "from autocoder_cc.components import Component"  # Wrong package name
        ]
        
        for import_stmt in incorrect_imports:
            result = self.validator.validate_import_statement(import_stmt)
            assert not result['valid'], f"Should reject deprecated import: {import_stmt}"


class TestValidationPipelineIntegration:
    """Test complete validation pipeline with reference patterns."""
    
    def setup_method(self):
        """Setup validation pipeline."""
        self.validator = IntegrationValidator()
        
    def test_complete_component_validation_pipeline(self):
        """Test complete validation pipeline for reference component."""
        # Complete reference component
        component_definition = {
            "type": "Store",
            "name": "TestStore",
            "class_name": "GeneratedStore_TestStore",
            "base_class": "ComposedComponent",
            "methods": ["__init__", "setup", "process_item", "cleanup", "get_health_status"],
            "imports": [
                "from autocoder_cc.components.composed_base import ComposedComponent",
                "from typing import Dict, Any, Optional"
            ],
            "implementation": '''
class GeneratedStore_TestStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None):
        await super().setup(harness_context)
        self.setup_called = True
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success", "processed": item}
    
    async def cleanup(self):
        await super().cleanup()
        self.cleanup_called = True
    
    def get_health_status(self) -> Dict[str, Any]:
        base_health = ComposedComponent.get_health_status(self)
        return {**base_health, "items_processed": 0}
'''
        }
        
        # Run complete validation pipeline
        result = self.validator.validate_complete_component(component_definition)
        
        assert result['valid'], f"Complete validation failed: {result.get('errors', [])}"
        assert result['component_type'] == 'Store'
        assert result['base_class'] == 'ComposedComponent'
        
    def test_system_level_validation(self):
        """Test system-level validation with multiple reference components."""
        # Define a simple system with Store and API components
        system_definition = {
            "components": [
                {
                    "type": "Store", 
                    "name": "DataStore",
                    "class_name": "GeneratedStore_DataStore",
                    "base_class": "ComposedComponent"
                },
                {
                    "type": "API",
                    "name": "WebAPI", 
                    "class_name": "GeneratedAPI_WebAPI",
                    "base_class": "ComposedComponent"
                }
            ],
            "bindings": [
                {
                    "source": "GeneratedStore_DataStore",
                    "target": "GeneratedAPI_WebAPI",
                    "binding_type": "data_flow"
                }
            ]
        }
        
        result = self.validator.validate_system_definition(system_definition)
        
        assert result['valid'], f"System validation failed: {result.get('errors', [])}"
        assert len(result['validated_components']) == 2
        assert len(result['validated_bindings']) == 1
        
    def test_error_reporting_format(self):
        """Test that validation errors are reported in correct format."""
        # Invalid component missing required methods
        invalid_component_code = '''
class GeneratedStore_TestStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    # Missing setup, cleanup, get_health_status methods
'''
        
        result = self.validator.validate_component_integration(invalid_component_code, 'Store')
        
        assert not result['valid']
        assert 'errors' in result
        assert isinstance(result['errors'], list)
        assert len(result['errors']) > 0
        
        # Check error format
        for error in result['errors']:
            assert isinstance(error, (str, dict))
            if isinstance(error, dict):
                assert 'message' in error
                assert 'severity' in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])