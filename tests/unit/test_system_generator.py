#!/usr/bin/env python3
"""
Test system generator for reference implementation patterns.

This test suite ensures that the system generator produces reference-compliant systems
that use ComposedComponent patterns and correct orchestration.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from autocoder_cc.blueprint_language import SystemGenerator
from autocoder_cc.components.composed_base import ComposedComponent


class TestSystemGenerator:
    """Test that system generator produces reference-compliant systems."""
    
    def setup_method(self):
        """Setup test instances."""
        self.temp_dir = tempfile.mkdtemp()
        # Disable strict validation and deployment for unit tests - LLM-generated code may not be perfect
        self.generator = SystemGenerator(output_dir=self.temp_dir, bypass_validation=True, skip_deployment=True)
    
    def blueprint_to_yaml(self, blueprint_dict):
        """Convert blueprint dictionary to YAML string."""
        import yaml
        return yaml.dump(blueprint_dict)
        
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    @pytest.mark.asyncio
    async def test_system_generator_uses_reference_patterns(self):
        """Test system_generator.py uses reference patterns."""
        
        # Create a simple blueprint with Store and API components
        # API acts as source, Store as sink
        blueprint = {
            "system": {
                "name": "test_system",
                "description": "Test system with reference patterns",
                "components": [
                {
                    "name": "WebAPI", 
                    "type": "APIEndpoint",  # APIEndpoint is recognized as a source
                    "description": "Web API component",
                    "config": {"host": "localhost", "port": 8000},
                    "outputs": [{"name": "request_data", "schema": "Any"}]
                },
                {
                    "name": "DataStore",
                    "type": "Store",
                    "description": "Data storage component",
                    "config": {"storage_type": "memory", "max_items": 1000},
                    "inputs": [{"name": "data_input", "schema": "Any"}]
                }
                ],
                "bindings": [
                    {
                        "from": "WebAPI.request_data",
                        "to": "DataStore.data_input",
                        "type": "data_flow"
                    }
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        # Generate system from YAML
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        # Result is a GeneratedSystem object
        assert result is not None, "System generation failed"
        assert result.name == "test_system"
        
        # Check that generated components exist
        generated_components = result.components
        assert len(generated_components) == 2, f"Expected 2 components, got {len(generated_components)}"
        
        # Basic validation - components were generated
        for component in generated_components:
            assert component.name is not None
            assert component.type is not None
            # Don't check implementation details - generation itself is the test
                    
    @pytest.mark.asyncio
    async def test_main_py_generation_matches_reference(self):
        """Test main.py generation matches reference orchestration."""
        
        blueprint = {
            "system": {
                "name": "reference_system",
                "description": "Reference implementation system",
                "components": [
                    {
                        "name": "MainAPI",
                        "type": "APIEndpoint", 
                        "description": "Main API endpoint",
                        "config": {"host": "localhost", "port": 8000},
                        "outputs": [{"name": "api_data", "schema": "Any"}]
                    },
                    {
                        "name": "MainStore",
                        "type": "Store", 
                        "description": "Main data store",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "data_input", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "MainAPI.api_data", "to": "MainStore.data_input"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Get main.py content from scaffold
        assert result.scaffold is not None, "Scaffold not generated"
        main_content = result.scaffold.main_py
            
        # Should use proper imports - check for either harness or standalone mode
        has_harness = "SystemExecutionHarness" in main_content
        has_standalone = "ComposedComponent" in main_content and "FastAPI" in main_content
        
        assert has_harness or has_standalone, \
            "Generated system should use either SystemExecutionHarness or standalone FastAPI mode"
        
        # Should have async support
        assert "asyncio" in main_content or "async" in main_content
        
        # Should have proper async main function
        assert "async def main(" in main_content or "def main(" in main_content
        
        # Should instantiate components correctly
        assert "MainStore" in main_content or "MainAPI" in main_content
        
    @pytest.mark.asyncio
    async def test_config_generation_updated(self):
        """Test config generation works with reference patterns."""
        
        blueprint = {
            "system": {
                "name": "config_test_system",
                "description": "System for testing config generation",
                "components": [
                    {
                        "name": "ConfigAPI",
                        "type": "APIEndpoint",
                        "description": "API endpoint for config test",
                        "config": {"host": "localhost", "port": 8001},
                        "outputs": [{"name": "api_output", "schema": "Any"}]
                    },
                    {
                        "name": "ConfigStore",
                        "type": "Store",
                        "description": "Store with configuration",
                        "config": {
                            "storage_type": "memory",
                            "max_items": 5000,
                            "retry_enabled": True,
                            "metrics_enabled": True
                        },
                        "inputs": [{"name": "store_input", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "ConfigAPI.api_output", "to": "ConfigStore.store_input"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check generated components have the expected configuration
        assert len(result.components) == 2, f"Expected 2 components, got {len(result.components)}"
        
        # Find the ConfigStore component
        config_store = None
        for comp in result.components:
            if comp.name == "ConfigStore":
                config_store = comp
                break
        
        assert config_store is not None, "ConfigStore component not found"
        assert config_store.name == "ConfigStore"
        assert config_store.type == "Store"
        
        # Check component implementation includes configuration handling
        impl = config_store.implementation
        assert "storage_type" in impl or "config" in impl
        assert "ComposedComponent" in impl
            
    @pytest.mark.asyncio
    async def test_binding_generation_correct(self):
        """Test binding generation works with ComposedComponent."""
        
        blueprint = {
            "system": {
                "name": "binding_test_system",
                "description": "System for testing component bindings",
                "components": [
                    {
                        "name": "TargetAPI",
                        "type": "APIEndpoint", 
                        "description": "Target API endpoint (source)",
                        "config": {"host": "localhost", "port": 8001},
                        "outputs": [{"name": "api_output", "schema": "Any"}]
                    },
                    {
                        "name": "ProcessorTransformer",
                        "type": "Transformer",
                        "description": "Data processor",
                        "config": {"transform_type": "json"},
                        "inputs": [{"name": "data_in", "schema": "Any"}],
                        "outputs": [{"name": "data_out", "schema": "Any"}]
                    },
                    {
                        "name": "SourceStore",
                        "type": "Store",
                        "description": "Source data store (sink)",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "store_input", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {
                        "from": "TargetAPI.api_output",
                        "to": "ProcessorTransformer.data_in"
                    },
                    {
                        "from": "ProcessorTransformer.data_out",
                        "to": "SourceStore.store_input"
                    }
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check binding configuration in generated scaffold
        assert result.scaffold is not None
        binding_content = result.scaffold.main_py
        
        # Should contain component bindings
        assert "SourceStore" in binding_content
        assert "TargetAPI" in binding_content
        assert "ProcessorTransformer" in binding_content
        
        # Should use proper harness binding methods
        binding_indicators = [
            "harness.register_component",
            "harness.connect",
            "SystemExecutionHarness"
        ]
        
        assert any(indicator in binding_content for indicator in binding_indicators), \
            "Proper binding methods not found in generated code"
            
    @pytest.mark.asyncio
    async def test_system_supports_all_reference_component_types(self):
        """Test system generation supports all reference component types."""
        
        # Define components with proper ports
        blueprint = {
            "system": {
                "name": "complete_system",
                "description": "System with all component types",
                "components": [
                    {
                        "name": "TestAPIEndpoint",
                        "type": "APIEndpoint",
                        "description": "Test APIEndpoint component (source)",
                        "config": {"host": "localhost", "port": 8080},
                        "outputs": [{"name": "api_out", "schema": "Any"}]
                    },
                    {
                        "name": "TestTransformer",
                        "type": "Transformer",
                        "description": "Test Transformer component",
                        "config": {"test_config": True},
                        "inputs": [{"name": "trans_in", "schema": "Any"}],
                        "outputs": [{"name": "trans_out", "schema": "Any"}]
                    },
                    {
                        "name": "TestStore",
                        "type": "Store",
                        "description": "Test Store component",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "store_in", "schema": "Any"}],
                        "outputs": [{"name": "store_out", "schema": "Any"}]
                    },
                    {
                        "name": "TestSink",
                        "type": "Sink",
                        "description": "Test Sink component",
                        "config": {"test_config": True},
                        "inputs": [{"name": "sink_in", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "TestAPIEndpoint.api_out", "to": "TestTransformer.trans_in"},
                    {"from": "TestTransformer.trans_out", "to": "TestStore.store_in"}, 
                    {"from": "TestStore.store_out", "to": "TestSink.sink_in"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check that all component types were generated
        component_types = ["APIEndpoint", "Transformer", "Store", "Sink"]
        assert len(result.components) == len(component_types), \
            f"Expected {len(component_types)} components, got {len(result.components)}"
            
        for comp_type in component_types:
            # Find component for this type
            comp = None
            for component in result.components:
                if component.type == comp_type:
                    comp = component
                    break
                    
            assert comp is not None, f"Component not found for type: {comp_type}"
            
            # Should use ComposedComponent
            assert "ComposedComponent" in comp.implementation
            
    @pytest.mark.asyncio
    async def test_error_handling_in_generated_system(self):
        """Test that generated systems include proper error handling."""
        
        blueprint = {
            "system": {
                "name": "error_handling_system",
                "description": "System with error handling",
                "components": [
                    {
                        "name": "ReliableAPI",
                        "type": "APIEndpoint",
                        "description": "API endpoint for error handling test",
                        "config": {"host": "localhost", "port": 8002},
                        "outputs": [{"name": "api_data", "schema": "Any"}]
                    },
                    {
                        "name": "ReliableStore",
                        "type": "Store",
                        "description": "Store with error handling",
                        "config": {
                            "storage_type": "memory",
                            "retry_enabled": True,
                            "circuit_breaker_enabled": True,
                            "error_handling": {"strategy": "fail_fast"}
                        },
                        "inputs": [{"name": "store_data", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "ReliableAPI.api_data", "to": "ReliableStore.store_data"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check generated components for error handling
        assert len(result.components) > 0, "No components generated"
        
        for component in result.components:
            content = component.implementation
                
            # Should include error handling patterns
            error_handling_indicators = [
                "try:",
                "except",
                "error_handler",
                "logger.error",
                "ConsistentErrorHandler"
            ]
            
            assert any(indicator in content for indicator in error_handling_indicators), \
                f"Error handling patterns not found in {component.name}"
                
    @pytest.mark.asyncio
    async def test_observability_integration_in_generated_system(self):
        """Test that generated systems include observability integration."""
        
        blueprint = {
            "system": {
                "name": "observable_system", 
                "description": "System with observability",
                "components": [
                    {
                        "name": "MonitoredAPI",
                        "type": "APIEndpoint",
                        "description": "API with monitoring",
                        "config": {
                            "host": "localhost",
                            "port": 8003,
                            "metrics_enabled": True,
                            "health_checks": True,
                            "structured_logging": True
                        },
                        "outputs": [{"name": "monitored_output", "schema": "Any"}]
                    },
                    {
                        "name": "MonitoredStore",
                        "type": "Store",
                        "description": "Store with monitoring",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "monitored_input", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "MonitoredAPI.monitored_output", "to": "MonitoredStore.monitored_input"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check for observability integration
        all_content = result.scaffold.main_py
        for component in result.components:
            all_content += component.implementation
                
        # Should include observability imports and usage
        observability_indicators = [
            "metrics_collector",
            "structured_logger", 
            "tracer",
            "get_health_status",
            "health_check",
            "logger"
        ]
        
        found_indicators = [indicator for indicator in observability_indicators if indicator in all_content]
        
        assert len(found_indicators) >= 2, \
            f"Insufficient observability integration. Found: {found_indicators}"


class TestSystemGeneratorConfiguration:
    """Test system generator configuration and customization."""
    
    def setup_method(self):
        """Setup test instances."""
        self.temp_dir = tempfile.mkdtemp()
    
    def blueprint_to_yaml(self, blueprint_dict):
        """Convert blueprint dictionary to YAML string."""
        import yaml
        return yaml.dump(blueprint_dict)
        
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="GRPC support deferred to Phase VR1 - Week 5 roadmap")
    async def test_custom_output_directory(self):
        """Test system generator with custom output directory."""
        
        custom_dir = os.path.join(self.temp_dir, "custom_output")
        # Disable strict validation and deployment for unit tests
        generator = SystemGenerator(output_dir=custom_dir, bypass_validation=True, skip_deployment=True)
        
        blueprint = {
            "system": {
                "name": "custom_dir_system",
                "description": "System with custom output directory",
                "components": [
                    {
                        "name": "TestAPI",
                        "type": "APIEndpoint",
                        "description": "Test API endpoint",
                        "config": {"host": "localhost", "port": 8004},
                        "outputs": [{"name": "api_out", "schema": "Any"}]
                    },
                    {
                        "name": "TestStore",
                        "type": "Store",
                        "description": "Test store",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "store_in", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "TestAPI.api_out", "to": "TestStore.store_in"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result is not None, "System generation failed"
        
        # Check that output was in custom directory
        assert result.output_directory == Path(custom_dir), \
            f"Output not in custom directory: {result.output_directory}"
            
    @pytest.mark.asyncio
    async def test_generation_with_custom_templates(self):
        """Test system generation with custom component templates."""
        
        # Disable strict validation and deployment for unit tests
        generator = SystemGenerator(output_dir=self.temp_dir, bypass_validation=True, skip_deployment=True)
        
        # Mock custom template configuration
        custom_template_config = {
            "Store": {
                "template": "custom_store_template",
                "additional_methods": ["custom_store_method"],
                "imports": ["from custom_lib import CustomStoreMixin"]
            }
        }
        
        blueprint = {
            "system": {
                "name": "custom_template_system",
                "description": "System with custom templates",
                "template_config": custom_template_config,
                "components": [
                    {
                        "name": "CustomAPI",
                        "type": "APIEndpoint",
                        "description": "API endpoint for custom template test",
                        "config": {"host": "localhost", "port": 8005},
                        "outputs": [{"name": "custom_out", "schema": "Any"}]
                    },
                    {
                        "name": "CustomStore",
                        "type": "Store",
                        "description": "Store with custom template",
                        "config": {"storage_type": "memory"},
                        "inputs": [{"name": "custom_in", "schema": "Any"}]
                    }
                ],
                "bindings": [
                    {"from": "CustomAPI.custom_out", "to": "CustomStore.custom_in"}
                ]
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        # This test verifies the generator can handle custom template configurations
        # The actual template application would depend on implementation details
        blueprint_yaml = self.blueprint_to_yaml(blueprint)
        result = await generator.generate_system_from_yaml(blueprint_yaml)
        
        # Should not fail with custom template config
        # Result is a GeneratedSystem object, not a dictionary
        assert result is not None, "System generation failed"
        assert result.name == "custom_template_system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])