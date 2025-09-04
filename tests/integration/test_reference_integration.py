#!/usr/bin/env python3
"""
Test complete integration with reference implementation patterns.

This test suite validates the complete system integration using reference
implementation patterns and ensures end-to-end functionality.
"""

import pytest
import anyio
import tempfile
import os
import yaml
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.validation.integration_validator import IntegrationValidator
from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc import SystemExecutionHarness


class TestReferenceIntegration:
    """Test complete system integration with reference patterns."""
    
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
    async def test_complete_system_generation_and_validation(self):
        """Test complete system generation and validation with reference patterns."""
        
        # Define a comprehensive blueprint
        blueprint = {
            "metadata": {
                "version": "1.0.0",
                "author": "Test Suite",
                "description": "Reference integration test system"
            },
            "system": {
                "name": "ReferenceIntegrationSystem",
                "description": "Complete system for reference integration testing",
                "version": "1.0.0",
                "components": [
                {
                    "name": "UserStore",
                    "type": "Store",
                    "description": "User data storage component",
                    "config": {
                        "storage_type": "memory",
                        "max_items": 10000,
                        "retry_enabled": True,
                        "metrics_enabled": True
                    }
                },
                {
                    "name": "UserAPI",
                    "type": "API",
                    "description": "User management API",
                    "config": {
                        "host": "localhost",
                        "port": 8000,
                        "cors_enabled": True,
                        "metrics_enabled": True
                    }
                },
                {
                    "name": "DataTransformer",
                    "type": "Transformer", 
                    "description": "User data transformation component",
                    "config": {
                        "transform_type": "json",
                        "batch_size": 50,
                        "metrics_enabled": True
                    }
                },
                {
                    "name": "NotificationSink",
                    "type": "Sink",
                    "description": "User notification output component",
                    "config": {
                        "output_format": "email",
                        "batch_notifications": True,
                        "metrics_enabled": True
                    }
                }
                ]
            }
        }
        
        # Add connections to the system section if the format requires it  
        blueprint["system"]["connections"] = [
                {
                    "from": "UserStore",
                    "to": "UserAPI",
                    "type": "data_flow",
                    "description": "Store provides user data to API"
                },
                {
                    "from": "UserAPI",
                    "to": "DataTransformer",
                    "type": "data_flow",
                    "description": "API sends requests to transformer"
                },
                {
                    "from": "DataTransformer",
                    "to": "NotificationSink",
                    "type": "data_flow",
                    "description": "Transformer sends processed data to notifications"
                }
            ]
        
        # Convert blueprint to YAML and generate the complete system
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        
        assert generation_result is not None, "System generation returned None"
        assert hasattr(generation_result, 'components'), f"Generation result missing components: {generation_result}"
        
        # Validate each generated component
        generated_components = generation_result.components
        assert len(generated_components) == 4, f"Expected 4 components, got {len(generated_components)}"
        
        for component in generated_components:
            # Check component has required attributes
            assert hasattr(component, 'implementation'), f"Component missing implementation: {component}"
            assert hasattr(component, 'component_type'), f"Component missing type: {component}"
            
            component_code = component.implementation
            component_type = component.component_type
                
            # Validate each component uses reference patterns
            assert "ComposedComponent" in component_code, f"Component doesn't use ComposedComponent: {component.name}"
            assert "StandaloneComponentBase" not in component_code, f"Component uses deprecated base: {component.name}"
                
            # Validate component integration
            validation_result = self.validator.validate_component_integration(component_code, component_type)
            assert validation_result['valid'], f"Component validation failed for {component.name}: {validation_result.get('errors', [])}"
        
        # Validate scaffold contains proper main.py setup
        scaffold = generation_result.scaffold
        assert hasattr(scaffold, 'main_file_content'), f"Scaffold missing main file: {scaffold}"
        
        main_content = scaffold.main_file_content
            
        # Should use reference patterns in main.py
        assert "SystemExecutionHarness" in main_content, "Main file doesn't use SystemExecutionHarness"
        assert "ComposedComponent" in main_content, "Main file doesn't reference ComposedComponent"
        
    @pytest.mark.asyncio
    async def test_generated_system_runtime_behavior(self):
        """Test that generated system can actually run with reference patterns."""
        
        # Create a simple test system
        blueprint = {
            "metadata": {
                "version": "1.0.0",
                "author": "Test Suite",
                "description": "Runtime test system"
            },
            "system": {
                "name": "runtime_test_system",
                "description": "Simple system for runtime testing",
                "version": "1.0.0",
                "components": [
                    {
                        "name": "test_store",
                        "type": "Store",
                        "description": "Test storage component",
                        "processing_mode": "stream",
                        "inputs": [
                            {
                                "name": "store_requests",
                                "schema": "StoreRequestSchema",
                                "description": "Store operation requests"
                            }
                        ],
                        "outputs": [
                            {
                                "name": "store_data",
                                "schema": "StoreDataSchema", 
                                "description": "Stored data for API"
                            }
                        ],
                        "config": {"storage_type": "memory"}
                    },
                    {
                        "name": "test_api",
                        "type": "APIEndpoint", 
                        "description": "Test API component",
                        "processing_mode": "stream",
                        "inputs": [
                            {
                                "name": "store_data",
                                "schema": "StoreDataSchema",
                                "description": "Data from store"
                            }
                        ],
                        "outputs": [],
                        "config": {"host": "localhost", "port": 8001}
                    }
                ],
                "bindings": [
                    {
                        "from": {
                            "component": "test_store",
                            "output": "store_data"
                        },
                        "to": {
                            "component": "test_api",
                            "input": "store_data"
                        }
                    }
                ]
            }
        }
        
        # Generate system  
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        assert generation_result is not None, f"Generation failed: {generation_result}"
        
        # Mock the actual system execution to test harness integration
        harness = SystemExecutionHarness()
        
        # Create mock components that follow reference patterns
        class MockStore(ComposedComponent):
            def __init__(self, name: str, config: Dict[str, Any] = None):
                super().__init__(name, config)
                self._items = {}
                self.setup_called = False
                self.cleanup_called = False
                
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
                base_health = ComposedComponent.get_health_status(self)
                return {**base_health, "items_count": len(self._items)}
        
        class MockAPI(ComposedComponent):
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
                base_health = ComposedComponent.get_health_status(self)
                return {**base_health, "api_ready": True}
        
        # Add components to harness
        store = MockStore("TestStore", {"storage_type": "memory"})
        api = MockAPI("TestAPI", {"host": "localhost", "port": 8001})
        
        harness.add_component("TestStore", store)
        harness.add_component("TestAPI", api)
        
        # Test harness lifecycle with reference components
        await harness.setup_all_components()
        
        assert store.setup_called, "Store setup not called"
        assert api.setup_called, "API setup not called"
        
        # Test health monitoring
        health = await harness.get_system_health()
        assert "components" in health
        assert "TestStore" in health["components"]
        assert "TestAPI" in health["components"]
        
        # Test component health format
        store_health = health["components"]["TestStore"]
        assert "healthy" in store_health
        assert "composition_model" in store_health
        assert store_health["composition_model"] == "capability_based"
        
        # Test cleanup
        await harness.cleanup_all_components()
        
        assert store.cleanup_called, "Store cleanup not called"
        assert api.cleanup_called, "API cleanup not called"
        
    @pytest.mark.asyncio
    async def test_system_configuration_integration(self):
        """Test system configuration integrates with reference patterns."""
        
        blueprint = {
            "system_name": "ConfigIntegrationSystem",
            "description": "System for configuration integration testing",
            "components": [
                {
                    "name": "ConfigurableStore",
                    "type": "Store",
                    "description": "Highly configurable store component",
                    "config": {
                        "storage_type": "file",
                        "db_path": "/tmp/test_store.db",
                        "max_items": 50000,
                        "retry_enabled": True,
                        "retry_attempts": 3,
                        "retry_delay": 1.0,
                        "metrics_enabled": True,
                        "circuit_breaker_enabled": True,
                        "circuit_breaker_threshold": 5,
                        "health_check_interval": 30,
                        "structured_logging": True,
                        "log_level": "INFO"
                    }
                }
            ],
            "connections": []
        }
        
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        assert generation_result is not None, f"Config system generation failed: {generation_result}"
        
        # Find the generated component
        generated_components = generation_result.components
        assert len(generated_components) == 1, "Should generate exactly one component"
        
        component = generated_components[0]
        component_code = component.implementation
            
        # Validate configuration handling
        assert "self.config" in component_code, "Component doesn't access config"
        assert "storage_type" in component_code, "Component doesn't use storage_type config"
        
        # Check that capabilities are referenced
        capability_indicators = ["retry_enabled", "metrics_enabled", "has_capability"]
        found_indicators = [indicator for indicator in capability_indicators if indicator in component_code]
        assert len(found_indicators) > 0, f"No capability indicators found in component. Expected one of: {capability_indicators}"
        
        # Validate component follows reference patterns
        validation_result = self.validator.validate_component_integration(component_code, 'Store')
        assert validation_result['valid'], f"Configurable component validation failed: {validation_result.get('errors', [])}"
        
    @pytest.mark.asyncio
    async def test_binding_integration_with_reference_patterns(self):
        """Test component binding integration with reference patterns."""
        
        blueprint = {
            "system_name": "BindingIntegrationSystem", 
            "description": "System for testing component binding integration",
            "components": [
                {
                    "name": "SourceStore",
                    "type": "Store",
                    "description": "Source data store",
                    "config": {"storage_type": "memory"}
                },
                {
                    "name": "MiddleTransformer",
                    "type": "Transformer",
                    "description": "Data transformation component",
                    "config": {"transform_type": "json"}
                },
                {
                    "name": "TargetSink",
                    "type": "Sink",
                    "description": "Data output component", 
                    "config": {"output_format": "json"}
                }
            ],
            "connections": [
                {
                    "from": "SourceStore",
                    "to": "MiddleTransformer", 
                    "type": "data_flow",
                    "description": "Store feeds data to transformer"
                },
                {
                    "from": "MiddleTransformer",
                    "to": "TargetSink",
                    "type": "data_flow", 
                    "description": "Transformer feeds processed data to sink"
                }
            ]
        }
        
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        assert generation_result is not None, f"Binding system generation failed: {generation_result}"
        
        # Validate binding configuration in scaffold
        scaffold = generation_result.scaffold
        main_content = scaffold.main_file_content
            
        # Check for proper binding setup
        binding_indicators = [
            "harness.add_component",
            "harness.bind_components",
            "add_binding",
            "SourceStore",
            "MiddleTransformer", 
            "TargetSink"
        ]
        
        for indicator in binding_indicators:
            assert indicator in main_content, f"Missing binding indicator in main.py: {indicator}"
            
        # Validate all components were generated
        generated_components = generation_result.components
        assert len(generated_components) == 3, f"Expected 3 components, got {len(generated_components)}"
        
        # Validate each component individually
        for component in generated_components:
            component_code = component.implementation
            component_type = component.component_type
                
            # Should use ComposedComponent
            assert "ComposedComponent" in component_code
                
            # Validate component
            validation_result = self.validator.validate_component_integration(component_code, component_type)
            assert validation_result['valid'], f"Component validation failed for {component.name}: {validation_result.get('errors', [])}"
            
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling integration with reference patterns."""
        
        blueprint = {
            "system_name": "ErrorHandlingSystem",
            "description": "System with comprehensive error handling",
            "components": [
                {
                    "name": "RobustStore",
                    "type": "Store",
                    "description": "Store with error handling",
                    "config": {
                        "storage_type": "file",
                        "retry_enabled": True,
                        "circuit_breaker_enabled": True,
                        "error_handling": {
                            "strategy": "fail_fast",
                            "max_retries": 3,
                            "backoff_factor": 2.0
                        }
                    }
                }
            ],
            "connections": []
        }
        
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        assert generation_result is not None, f"Error handling system generation failed: {generation_result}"
        
        generated_components = generation_result.components
        assert len(generated_components) == 1, "Should generate one robust component"
        
        component = generated_components[0]
        component_code = component.implementation
            
        # Check for error handling patterns
        error_handling_patterns = [
            "try:",
            "except",
            "error",
            "logger",
            "ConsistentErrorHandler"
        ]
        
        found_patterns = [pattern for pattern in error_handling_patterns if pattern in component_code]
        assert len(found_patterns) >= 2, f"Insufficient error handling patterns. Found: {found_patterns}"
        
        # Should still follow reference patterns
        assert "ComposedComponent" in component_code
        validation_result = self.validator.validate_component_integration(component_code, 'Store')
        assert validation_result['valid'], f"Robust component validation failed: {validation_result.get('errors', [])}"
        
    @pytest.mark.asyncio
    async def test_observability_integration(self):
        """Test observability integration with reference patterns."""
        
        blueprint = {
            "system_name": "ObservabilitySystem",
            "description": "System with full observability",
            "components": [
                {
                    "name": "MonitoredAPI",
                    "type": "API",
                    "description": "API with full monitoring",
                    "config": {
                        "host": "localhost",
                        "port": 8080,
                        "metrics_enabled": True,
                        "structured_logging": True,
                        "health_checks": True,
                        "distributed_tracing": True,
                        "prometheus_metrics": True
                    }
                }
            ],
            "connections": []
        }
        
        blueprint_yaml = yaml.dump(blueprint)
        generation_result = await self.system_generator.generate_system_from_yaml(blueprint_yaml)
        assert generation_result is not None, f"Observability system generation failed: {generation_result}"
        
        # Validate observability integration in generated content
        all_content = ""
        for component in generation_result.components:
            all_content += component.implementation
        all_content += generation_result.scaffold.main_file_content
                
        # Check for observability patterns
        observability_patterns = [
            "metrics",
            "logger",
            "health",
            "tracer",
            "get_health_status"
        ]
        
        found_patterns = [pattern for pattern in observability_patterns if pattern in all_content]
        assert len(found_patterns) >= 3, f"Insufficient observability integration. Found: {found_patterns}"
        
        # Validate the component
        generated_components = generation_result.components
        assert len(generated_components) == 1
        
        component = generated_components[0]
        component_code = component.implementation
            
        validation_result = self.validator.validate_component_integration(component_code, 'API')
        assert validation_result['valid'], f"Monitored component validation failed: {validation_result.get('errors', [])}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])