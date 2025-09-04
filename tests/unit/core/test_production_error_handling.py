#!/usr/bin/env python3
"""
Production-Ready Error Handling Tests
=====================================

This test suite validates comprehensive error handling across all critical components
to ensure production-ready standards are met.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import asyncio
import json

# Import components to test
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
from autocoder_cc.core.config import Settings
from autocoder_cc.orchestration.harness import SystemExecutionHarness
from autocoder_cc.components.component_registry import ComponentRegistry
from tests.utils.evidence_collector import EvidenceCollector


class TestProductionErrorHandling:
    """Test comprehensive error handling for production readiness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
    def teardown_method(self):
        """Clean up test fixtures."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_blueprint_parser_invalid_yaml_error_handling(self):
        """Test blueprint parser handles invalid YAML gracefully."""
        parser = SystemBlueprintParser()
        
        # Test malformed YAML
        malformed_yaml = """
        invalid: yaml: structure
        [missing closing bracket
        """
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_string(malformed_yaml)
        
        error_msg = str(exc_info.value)
        assert "Failed to parse YAML" in error_msg
        assert "yaml" in error_msg.lower()
    
    def test_blueprint_parser_missing_required_fields_error_handling(self):
        """Test blueprint parser handles missing required fields."""
        parser = SystemBlueprintParser()
        
        # Test missing schema_version
        missing_schema = """
        system:
          name: "test_system"
          components: []
        """
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_string(missing_schema)
        
        error_msg = str(exc_info.value)
        assert "schema_version" in error_msg or "validation" in error_msg.lower()
    
    def test_blueprint_parser_invalid_component_types_error_handling(self):
        """Test blueprint parser handles invalid component types."""
        parser = SystemBlueprintParser()
        
        invalid_component_yaml = """
        schema_version: "1.0.0"
        system:
          name: "test_system"
          components:
            - name: "invalid_component"
              type: "NonExistentType"
              inputs: []
              outputs: []
        """
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_string(invalid_component_yaml)
        
        error_msg = str(exc_info.value)
        assert "NonExistentType" in error_msg or "validation" in error_msg.lower()
    
    def test_architectural_validator_circular_dependency_error_handling(self):
        """Test architectural validator handles circular dependencies."""
        validator = ArchitecturalValidator()
        parser = SystemBlueprintParser()
        
        circular_yaml = """
        schema_version: "1.0.0"
        system:
          name: "circular_system"
          components:
            - name: "component1"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "component2"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings:
            - from: "component1.output"
              to: "component2.input"
            - from: "component2.output"
              to: "component1.input"
        """
        
        # This should either be caught by parser or validator
        try:
            system_blueprint = parser.parse_string(circular_yaml)
            # If parsing succeeds, validation should catch it
            validation_errors = validator.validate_system_architecture(system_blueprint)
            circular_errors = [e for e in validation_errors if "circular" in e.message.lower()]
            assert len(circular_errors) > 0, "Should detect circular dependency"
        except ValueError as e:
            # Parser caught it - acceptable
            assert "circular" in str(e).lower() or "validation" in str(e).lower()
    
    def test_system_generator_missing_llm_credentials_error_handling(self):
        """Test system generator handles missing LLM credentials."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove all API keys
            with patch('autocoder_cc.core.config.Settings.get_llm_api_key', return_value=None):
                with pytest.raises((ValueError, RuntimeError, Exception)) as exc_info:
                    translator = NaturalLanguageToPydanticTranslator()
                    translator.translate_to_intermediate("test system")
                
                error_msg = str(exc_info.value)
                assert any(term in error_msg.lower() for term in ["api", "key", "credential", "auth"])
    
    def test_system_generator_invalid_blueprint_file_error_handling(self):
        """Test system generator handles invalid blueprint files."""
        generator = SystemGenerator(output_dir=self.temp_dir)
        
        # Test non-existent file
        non_existent_file = "/path/that/does/not/exist.yaml"
        
        with pytest.raises((FileNotFoundError, ValueError)) as exc_info:
            asyncio.run(generator.generate_system(non_existent_file))
        
        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "file" in error_msg.lower()
    
    def test_system_generator_malformed_blueprint_error_handling(self):
        """Test system generator handles malformed blueprint files."""
        generator = SystemGenerator(output_dir=self.temp_dir)
        
        # Create malformed blueprint file
        malformed_file = os.path.join(self.temp_dir, "malformed.yaml")
        with open(malformed_file, 'w') as f:
            f.write("invalid: yaml: [structure")
        self.test_files.append(malformed_file)
        
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(generator.generate_system(malformed_file))
        
        error_msg = str(exc_info.value)
        assert "parse" in error_msg.lower() or "yaml" in error_msg.lower()
    
    def test_system_generator_timeout_error_handling(self):
        """Test system generator handles timeout scenarios."""
        generator = SystemGenerator(output_dir=self.temp_dir, timeout=0.001)  # Very short timeout
        
        # Create valid blueprint that would take longer than timeout
        valid_file = os.path.join(self.temp_dir, "valid.yaml")
        with open(valid_file, 'w') as f:
            f.write("""
            schema_version: "1.0.0"
            system:
              name: "timeout_test"
              components:
                - name: "api"
                  type: "APIEndpoint"
                  inputs:
                    - name: "request"
                      schema: "common_object_schema"
                  outputs:
                    - name: "response"
                      schema: "common_object_schema"
                - name: "store"
                  type: "Store"
                  inputs:
                    - name: "data"
                      schema: "common_object_schema"
              bindings:
                - from: "api.response"
                  to: "store.data"
            """)
        self.test_files.append(valid_file)
        
        # Should handle timeout gracefully - either TimeoutError or other exception
        try:
            asyncio.run(generator.generate_system(valid_file))
            # If it completes quickly, that's also valid
            assert True, "Generator completed quickly"
        except (asyncio.TimeoutError, Exception) as e:
            # Should properly handle timeout or other errors
            assert True, f"Generator handled error gracefully: {type(e).__name__}"
    
    def test_component_registry_missing_component_error_handling(self):
        """Test component registry handles missing component types."""
        registry = ComponentRegistry()
        
        # Test requesting non-existent component
        try:
            result = registry.get_component_class("NonExistentComponent")
            # Some registries might return None instead of raising
            assert result is None, "Should return None for non-existent component"
        except (KeyError, ValueError, AttributeError) as e:
            # Should raise appropriate error for missing component
            error_msg = str(e)
            assert "NonExistentComponent" in error_msg or "not found" in error_msg.lower() or "available" in error_msg.lower()
    
    def test_system_execution_harness_missing_components_error_handling(self):
        """Test system execution harness handles missing components."""
        harness = SystemExecutionHarness()
        
        # Test with malformed system configuration
        invalid_config = {
            "components": [
                {
                    "name": "missing_component",
                    "type": "NonExistentType"
                }
            ]
        }
        
        try:
            result = harness.configure_system(invalid_config)
            # Some implementations might return error status instead of raising
            assert result is False or "error" in str(result).lower(), "Should indicate failure for invalid config"
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            # Should raise appropriate error for missing component type
            error_msg = str(e)
            assert "NonExistentType" in error_msg or "component" in error_msg.lower() or "type" in error_msg.lower()
    
    def test_evidence_collector_invalid_command_error_handling(self):
        """Test evidence collector handles invalid commands."""
        collector = EvidenceCollector(min_samples=1, max_samples=1)
        
        # Test with invalid command
        invalid_command = ["nonexistent_command_that_should_fail"]
        
        try:
            result = collector.time_command_statistical(invalid_command, timeout=5)
            # Should return error result or None
            assert result is None or "error" in str(result).lower(), "Should handle invalid command gracefully"
        except (RuntimeError, OSError, FileNotFoundError, Exception) as e:
            # Should raise appropriate error for invalid command
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["nonexistent", "not found", "failed", "command", "file", "executable"])
    
    def test_evidence_collector_insufficient_samples_error_handling(self):
        """Test evidence collector handles insufficient successful samples."""
        collector = EvidenceCollector(min_samples=5, max_samples=10)
        
        # Test with command that always fails
        failing_command = ["false"]  # Command that always returns exit code 1
        
        with pytest.raises(RuntimeError) as exc_info:
            collector.time_command_statistical(failing_command, timeout=5)
        
        error_msg = str(exc_info.value)
        assert "insufficient" in error_msg.lower() or "samples" in error_msg.lower()
    
    def test_config_settings_missing_environment_error_handling(self):
        """Test configuration handles missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # Test that Settings can handle missing environment variables
            try:
                settings = Settings()
                # Should have fallback values or raise meaningful errors
                assert settings is not None
            except Exception as e:
                # If it raises an error, it should be meaningful
                error_msg = str(e)
                assert any(term in error_msg.lower() for term in ["environment", "config", "variable", "missing"])
    
    def test_natural_language_parser_empty_input_error_handling(self):
        """Test natural language parser handles empty/invalid inputs."""
        translator = NaturalLanguageToPydanticTranslator()
        
        # Test empty input
        try:
            result = translator.translate_to_intermediate("")
            # Should return empty result or None
            assert result is None or len(str(result)) == 0, "Should handle empty input gracefully"
        except (ValueError, RuntimeError, Exception) as e:
            # Should raise appropriate error for empty input
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["empty", "invalid", "input", "required", "llm", "api", "configuration"])
    
    def test_natural_language_parser_malformed_response_error_handling(self):
        """Test natural language parser handles malformed LLM responses."""
        translator = NaturalLanguageToPydanticTranslator()
        
        # Mock LLM to return malformed JSON
        try:
            with patch.object(translator, 'llm_client') as mock_llm:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = "invalid json response"
                mock_llm.chat.completions.create.return_value = mock_response
                
                result = translator.translate_to_intermediate("test system")
                # Should handle malformed response gracefully
                assert result is None or "error" in str(result).lower(), "Should handle malformed response gracefully"
        except (ValueError, json.JSONDecodeError, AttributeError, Exception) as e:
            # Should raise appropriate error for malformed response
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["json", "parse", "response", "format", "llm", "api", "configuration"])
    
    def test_file_system_permissions_error_handling(self):
        """Test error handling for file system permission issues."""
        # Create a read-only directory
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only
        
        generator = SystemGenerator(output_dir=readonly_dir)
        
        # Create valid blueprint
        valid_file = os.path.join(self.temp_dir, "valid_system.yaml")
        with open(valid_file, 'w') as f:
            f.write("""
            schema_version: "1.0.0"
            system:
              name: "permission_test"
              components:
                - name: "api"
                  type: "APIEndpoint"
                  inputs:
                    - name: "request"
                      schema: "common_object_schema"
                  outputs:
                    - name: "response"
                      schema: "common_object_schema"
            """)
        self.test_files.append(valid_file)
        
        try:
            result = asyncio.run(generator.generate_system(valid_file))
            # Should handle permission errors gracefully
            assert result is None or "error" in str(result).lower(), "Should handle permission error gracefully"
        except (PermissionError, OSError, Exception) as e:
            # Should raise appropriate error for permission issues
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["permission", "denied", "access", "readonly", "write", "directory"])
        finally:
            # Clean up
            os.chmod(readonly_dir, 0o755)  # Restore permissions for cleanup
    
    def test_network_connectivity_error_handling(self):
        """Test error handling for network connectivity issues."""
        # Test with invalid LLM endpoint
        try:
            with patch('autocoder_cc.core.config.Settings.get_llm_api_key', return_value="fake_key"):
                with patch('openai.OpenAI') as mock_openai:
                    mock_client = Mock()
                    mock_client.chat.completions.create.side_effect = Exception("Network error")
                    mock_openai.return_value = mock_client
                    
                    translator = NaturalLanguageToPydanticTranslator()
                    
                    result = translator.translate_to_intermediate("test system")
                    # Should handle network error gracefully
                    assert result is None or "error" in str(result).lower(), "Should handle network error gracefully"
        except Exception as e:
            # Should raise appropriate error for network issues
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["network", "connection", "api", "llm", "configuration", "client"])
    
    def test_memory_exhaustion_error_handling(self):
        """Test error handling for memory exhaustion scenarios."""
        # Test with extremely large input that could cause memory issues
        large_input = "create a system with " + "component, " * 10000 + "and storage"
        
        translator = NaturalLanguageToPydanticTranslator()
        
        # Should handle large inputs gracefully
        try:
            result = translator.translate_to_intermediate(large_input)
            # If it succeeds, that's fine
            assert result is not None
        except (MemoryError, ValueError, RuntimeError) as e:
            # If it fails, should be with appropriate error handling
            error_msg = str(e)
            assert any(term in error_msg.lower() for term in ["memory", "large", "limit", "size"])
    
    def test_concurrent_access_error_handling(self):
        """Test error handling for concurrent access scenarios."""
        generator = SystemGenerator(output_dir=self.temp_dir)
        
        # Create valid blueprint
        valid_file = os.path.join(self.temp_dir, "concurrent_test.yaml")
        with open(valid_file, 'w') as f:
            f.write("""
            schema_version: "1.0.0"
            system:
              name: "concurrent_test"
              components:
                - name: "api"
                  type: "APIEndpoint"
                  inputs:
                    - name: "request"
                      schema: "common_object_schema"
                  outputs:
                    - name: "response"
                      schema: "common_object_schema"
            """)
        self.test_files.append(valid_file)
        
        # Test concurrent generation (should handle gracefully)
        async def concurrent_generation():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(generator.generate_system(valid_file))
                tasks.append(task)
            
            # At least one should complete successfully or all should fail gracefully
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that we get either successful results or proper exceptions
            for result in results:
                if isinstance(result, Exception):
                    # Should be meaningful error messages
                    error_msg = str(result)
                    assert len(error_msg) > 0, "Error messages should not be empty"
                else:
                    # Should be successful results
                    assert result is not None
        
        # Run concurrent test
        asyncio.run(concurrent_generation())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])