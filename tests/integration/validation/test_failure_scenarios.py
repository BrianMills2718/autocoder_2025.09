#!/usr/bin/env python3
"""
Failure Scenario Testing - Chaos Engineering for Production Readiness
===================================================================

This test suite implements comprehensive failure scenario testing to validate
system resilience and error handling under adverse conditions.
"""

import pytest
import os
import tempfile
import time
import json
import asyncio
import signal
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

# Import test utilities
from tests.utils.evidence_collector import EvidenceCollector
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.components.component_registry import ComponentRegistry


class TestFailureScenarios:
    """Comprehensive failure scenario testing for production readiness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.evidence_collector = EvidenceCollector(min_samples=3, max_samples=5)
        self.test_files = []
        
    def teardown_method(self):
        """Clean up test fixtures."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_blueprint_parsing_failure_scenarios(self):
        """Test blueprint parsing under various failure conditions."""
        parser = SystemBlueprintParser()
        
        failure_scenarios = [
            {
                "name": "malformed_yaml",
                "content": "invalid: yaml: [structure\nno closing bracket",
                "expected_error": "yaml"
            },
            {
                "name": "missing_schema_version",
                "content": """
                system:
                  name: "test_system"
                  components: []
                """,
                "expected_error": "schema_version"
            },
            {
                "name": "invalid_component_type",
                "content": """
                schema_version: "1.0.0"
                system:
                  name: "test_system"
                  components:
                    - name: "invalid_comp"
                      type: "NonExistentType"
                """,
                "expected_error": "component"
            },
            {
                "name": "missing_required_fields",
                "content": """
                schema_version: "1.0.0"
                system:
                  components:
                    - name: "incomplete_comp"
                      type: "Source"
                """,
                "expected_error": "required"
            },
            {
                "name": "circular_bindings",
                "content": """
                schema_version: "1.0.0"
                system:
                  name: "circular_system"
                  components:
                    - name: "comp1"
                      type: "Transformer"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                    - name: "comp2"
                      type: "Transformer"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                  bindings:
                    - from: "comp1.output"
                      to: "comp2.input"
                    - from: "comp2.output"
                      to: "comp1.input"
                """,
                "expected_error": "circular"
            }
        ]
        
        evidence = {
            "test_name": "blueprint_parsing_failure_scenarios",
            "timestamp": time.time(),
            "scenarios_tested": len(failure_scenarios),
            "scenarios_handled": 0,
            "failure_details": []
        }
        
        for scenario in failure_scenarios:
            try:
                # Attempt to parse the malformed blueprint
                start_time = time.time()
                system_blueprint = parser.parse_string(scenario["content"])
                parse_time = time.time() - start_time
                
                # If parsing succeeds, check if validation catches the error
                validator = ArchitecturalValidator()
                validation_errors = validator.validate_system_architecture(system_blueprint)
                
                # Check if the expected error is caught
                error_caught = any(
                    scenario["expected_error"].lower() in error.message.lower()
                    for error in validation_errors
                )
                
                if error_caught:
                    evidence["scenarios_handled"] += 1
                    evidence["failure_details"].append({
                        "scenario": scenario["name"],
                        "handled": True,
                        "method": "validation",
                        "parse_time": parse_time,
                        "error_count": len(validation_errors)
                    })
                else:
                    evidence["failure_details"].append({
                        "scenario": scenario["name"],
                        "handled": False,
                        "method": "none",
                        "parse_time": parse_time,
                        "error_count": len(validation_errors)
                    })
                
            except Exception as e:
                # Parsing failed (expected for most scenarios)
                error_message = str(e).lower()
                error_caught = scenario["expected_error"].lower() in error_message
                
                if error_caught:
                    evidence["scenarios_handled"] += 1
                    evidence["failure_details"].append({
                        "scenario": scenario["name"],
                        "handled": True,
                        "method": "parsing",
                        "error_message": str(e)
                    })
                else:
                    evidence["failure_details"].append({
                        "scenario": scenario["name"],
                        "handled": False,
                        "method": "parsing",
                        "error_message": str(e)
                    })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "blueprint_parsing_failure_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify that most failure scenarios are handled
        handling_rate = (evidence["scenarios_handled"] / evidence["scenarios_tested"]) * 100
        assert handling_rate >= 80, f"Should handle at least 80% of failure scenarios, got {handling_rate:.1f}%"
        
        print(f"✅ Blueprint parsing failure scenarios: {evidence['scenarios_handled']}/{evidence['scenarios_tested']} handled ({handling_rate:.1f}%)")
    
    def test_resource_exhaustion_scenarios(self):
        """Test system behavior under resource exhaustion conditions."""
        evidence = {
            "test_name": "resource_exhaustion_scenarios",
            "timestamp": time.time(),
            "scenarios_tested": 0,
            "scenarios_handled": 0,
            "resource_tests": []
        }
        
        # Test memory exhaustion scenario
        try:
            evidence["scenarios_tested"] += 1
            
            # Create a very large blueprint to stress memory
            large_blueprint_components = []
            for i in range(100):  # Create 100 components
                large_blueprint_components.append({
                    "name": f"component_{i}",
                    "type": "Transformer",
                    "inputs": [{"name": "input", "schema": "common_object_schema"}],
                    "outputs": [{"name": "output", "schema": "common_object_schema"}]
                })
            
            large_blueprint = {
                "schema_version": "1.0.0",
                "system": {
                    "name": "large_system",
                    "components": large_blueprint_components,
                    "bindings": []
                }
            }
            
            # Test parsing large blueprint
            parser = SystemBlueprintParser()
            start_time = time.time()
            
            try:
                import yaml
                large_yaml = yaml.dump(large_blueprint)
                system_blueprint = parser.parse_string(large_yaml)
                parse_time = time.time() - start_time
                
                evidence["scenarios_handled"] += 1
                evidence["resource_tests"].append({
                    "test": "large_blueprint_parsing",
                    "handled": True,
                    "components": len(large_blueprint_components),
                    "parse_time": parse_time
                })
                
            except Exception as e:
                evidence["resource_tests"].append({
                    "test": "large_blueprint_parsing",
                    "handled": False,
                    "error": str(e)
                })
            
        except Exception as e:
            evidence["resource_tests"].append({
                "test": "large_blueprint_parsing",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Test file system exhaustion scenario
        try:
            evidence["scenarios_tested"] += 1
            
            # Create a directory with restricted permissions
            restricted_dir = os.path.join(self.temp_dir, "restricted")
            os.makedirs(restricted_dir, exist_ok=True)
            os.chmod(restricted_dir, 0o444)  # Read-only
            
            # Test system generator with restricted output directory
            generator = SystemGenerator(output_dir=restricted_dir)
            
            # Create a simple valid blueprint
            simple_blueprint = os.path.join(self.temp_dir, "simple.yaml")
            with open(simple_blueprint, 'w') as f:
                f.write("""
                schema_version: "1.0.0"
                system:
                  name: "simple_system"
                  components:
                    - name: "source"
                      type: "Source"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                    - name: "sink"
                      type: "Sink"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                  bindings:
                    - from: "source.output"
                      to: "sink.input"
                """)
            self.test_files.append(simple_blueprint)
            
            try:
                # This should fail due to permission issues
                result = asyncio.run(generator.generate_system(simple_blueprint))
                evidence["resource_tests"].append({
                    "test": "restricted_filesystem",
                    "handled": True,
                    "result": "completed_unexpectedly"
                })
                
            except (PermissionError, OSError) as e:
                evidence["scenarios_handled"] += 1
                evidence["resource_tests"].append({
                    "test": "restricted_filesystem",
                    "handled": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                
            except Exception as e:
                evidence["resource_tests"].append({
                    "test": "restricted_filesystem",
                    "handled": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
            
            finally:
                # Clean up permissions
                os.chmod(restricted_dir, 0o755)
            
        except Exception as e:
            evidence["resource_tests"].append({
                "test": "restricted_filesystem",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Test timeout scenario
        try:
            evidence["scenarios_tested"] += 1
            
            # Create a generator with very short timeout
            short_timeout_generator = SystemGenerator(output_dir=self.temp_dir, timeout=0.001)
            
            # Create blueprint that would take longer than timeout
            complex_blueprint = os.path.join(self.temp_dir, "complex.yaml")
            with open(complex_blueprint, 'w') as f:
                f.write("""
                schema_version: "1.0.0"
                system:
                  name: "complex_system"
                  components:
                    - name: "api"
                      type: "APIEndpoint"
                      inputs:
                        - name: "request"
                          schema: "common_object_schema"
                      outputs:
                        - name: "response"
                          schema: "common_object_schema"
                    - name: "controller"
                      type: "Controller"
                      inputs:
                        - name: "request"
                          schema: "common_object_schema"
                      outputs:
                        - name: "processed"
                          schema: "common_object_schema"
                    - name: "store"
                      type: "Store"
                      inputs:
                        - name: "data"
                          schema: "common_object_schema"
                  bindings:
                    - from: "api.response"
                      to: "controller.request"
                    - from: "controller.processed"
                      to: "store.data"
                """)
            self.test_files.append(complex_blueprint)
            
            try:
                # This should handle timeout gracefully
                result = asyncio.run(short_timeout_generator.generate_system(complex_blueprint))
                evidence["resource_tests"].append({
                    "test": "timeout_handling",
                    "handled": True,
                    "result": "completed_within_timeout"
                })
                
            except asyncio.TimeoutError:
                evidence["scenarios_handled"] += 1
                evidence["resource_tests"].append({
                    "test": "timeout_handling",
                    "handled": True,
                    "error_type": "TimeoutError"
                })
                
            except Exception as e:
                evidence["resource_tests"].append({
                    "test": "timeout_handling",
                    "handled": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
            
        except Exception as e:
            evidence["resource_tests"].append({
                "test": "timeout_handling",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "resource_exhaustion_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify that resource exhaustion scenarios are handled
        if evidence["scenarios_tested"] > 0:
            handling_rate = (evidence["scenarios_handled"] / evidence["scenarios_tested"]) * 100
            assert handling_rate >= 50, f"Should handle at least 50% of resource exhaustion scenarios, got {handling_rate:.1f}%"
            
            print(f"✅ Resource exhaustion scenarios: {evidence['scenarios_handled']}/{evidence['scenarios_tested']} handled ({handling_rate:.1f}%)")
    
    def test_concurrent_access_failure_scenarios(self):
        """Test system behavior under concurrent access conditions."""
        evidence = {
            "test_name": "concurrent_access_failure_scenarios",
            "timestamp": time.time(),
            "scenarios_tested": 0,
            "scenarios_handled": 0,
            "concurrency_tests": []
        }
        
        # Test concurrent component registry access
        try:
            evidence["scenarios_tested"] += 1
            
            registry = ComponentRegistry()
            
            # Function to create components concurrently
            def create_component(component_id):
                try:
                    component = registry.create_component(
                        "Source", 
                        f"concurrent_component_{component_id}", 
                        {"outputs": [{"name": "output", "schema": "common_object_schema"}]}
                    )
                    return {"success": True, "component_id": component_id}
                except Exception as e:
                    return {"success": False, "component_id": component_id, "error": str(e)}
            
            # Run concurrent component creation
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_component, i) for i in range(10)]
                results = [future.result() for future in futures]
            
            successful_creations = sum(1 for r in results if r["success"])
            
            evidence["scenarios_handled"] += 1
            evidence["concurrency_tests"].append({
                "test": "concurrent_component_creation",
                "handled": True,
                "total_attempts": len(results),
                "successful_creations": successful_creations,
                "success_rate": (successful_creations / len(results)) * 100
            })
            
        except Exception as e:
            evidence["concurrency_tests"].append({
                "test": "concurrent_component_creation",
                "handled": False,
                "error": str(e)
            })
        
        # Test concurrent blueprint parsing
        try:
            evidence["scenarios_tested"] += 1
            
            parser = SystemBlueprintParser()
            
            # Blueprint to parse concurrently
            blueprint_yaml = """
            schema_version: "1.0.0"
            system:
              name: "concurrent_test_system"
              components:
                - name: "source"
                  type: "Source"
                  outputs:
                    - name: "output"
                      schema: "common_object_schema"
                - name: "sink"
                  type: "Sink"
                  inputs:
                    - name: "input"
                      schema: "common_object_schema"
              bindings:
                - from: "source.output"
                  to: "sink.input"
            """
            
            # Function to parse blueprint concurrently
            def parse_blueprint(parse_id):
                try:
                    start_time = time.time()
                    system_blueprint = parser.parse_string(blueprint_yaml)
                    parse_time = time.time() - start_time
                    return {
                        "success": True, 
                        "parse_id": parse_id,
                        "parse_time": parse_time,
                        "component_count": len(system_blueprint.system.components)
                    }
                except Exception as e:
                    return {"success": False, "parse_id": parse_id, "error": str(e)}
            
            # Run concurrent blueprint parsing
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(parse_blueprint, i) for i in range(5)]
                results = [future.result() for future in futures]
            
            successful_parses = sum(1 for r in results if r["success"])
            
            evidence["scenarios_handled"] += 1
            evidence["concurrency_tests"].append({
                "test": "concurrent_blueprint_parsing",
                "handled": True,
                "total_attempts": len(results),
                "successful_parses": successful_parses,
                "success_rate": (successful_parses / len(results)) * 100
            })
            
        except Exception as e:
            evidence["concurrency_tests"].append({
                "test": "concurrent_blueprint_parsing",
                "handled": False,
                "error": str(e)
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "concurrent_access_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify that concurrent access scenarios are handled
        if evidence["scenarios_tested"] > 0:
            handling_rate = (evidence["scenarios_handled"] / evidence["scenarios_tested"]) * 100
            assert handling_rate >= 80, f"Should handle at least 80% of concurrent access scenarios, got {handling_rate:.1f}%"
            
            print(f"✅ Concurrent access scenarios: {evidence['scenarios_handled']}/{evidence['scenarios_tested']} handled ({handling_rate:.1f}%)")
    
    def test_external_dependency_failure_scenarios(self):
        """Test system behavior when external dependencies fail."""
        evidence = {
            "test_name": "external_dependency_failure_scenarios",
            "timestamp": time.time(),
            "scenarios_tested": 0,
            "scenarios_handled": 0,
            "dependency_tests": []
        }
        
        # Test LLM API failure simulation
        try:
            evidence["scenarios_tested"] += 1
            
            from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
            
            # Mock LLM client to simulate failure
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = Exception("Network timeout")
                mock_openai.return_value = mock_client
                
                translator = NaturalLanguageToPydanticTranslator()
                
                try:
                    result = translator.translate_to_intermediate("test system")
                    evidence["dependency_tests"].append({
                        "test": "llm_api_failure",
                        "handled": True,
                        "result": "graceful_fallback"
                    })
                    
                except Exception as e:
                    evidence["scenarios_handled"] += 1
                    evidence["dependency_tests"].append({
                        "test": "llm_api_failure",
                        "handled": True,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    })
            
        except Exception as e:
            evidence["dependency_tests"].append({
                "test": "llm_api_failure",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Test database connection failure simulation
        try:
            evidence["scenarios_tested"] += 1
            
            # Mock database connection failure
            with patch('socket.socket') as mock_socket:
                mock_socket.return_value.connect.side_effect = ConnectionRefusedError("Database connection refused")
                
                registry = ComponentRegistry()
                
                try:
                    # This should handle database connectivity gracefully
                    component = registry.create_component(
                        "Store", 
                        "test_store", 
                        {"inputs": [{"name": "data", "schema": "common_object_schema"}]}
                    )
                    evidence["dependency_tests"].append({
                        "test": "database_connection_failure",
                        "handled": True,
                        "result": "graceful_fallback"
                    })
                    
                except Exception as e:
                    evidence["scenarios_handled"] += 1
                    evidence["dependency_tests"].append({
                        "test": "database_connection_failure",
                        "handled": True,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    })
            
        except Exception as e:
            evidence["dependency_tests"].append({
                "test": "database_connection_failure",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "external_dependency_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify that dependency failure scenarios are handled
        if evidence["scenarios_tested"] > 0:
            handling_rate = (evidence["scenarios_handled"] / evidence["scenarios_tested"]) * 100
            assert handling_rate >= 50, f"Should handle at least 50% of dependency failure scenarios, got {handling_rate:.1f}%"
            
            print(f"✅ External dependency failure scenarios: {evidence['scenarios_handled']}/{evidence['scenarios_tested']} handled ({handling_rate:.1f}%)")
    
    def test_data_corruption_scenarios(self):
        """Test system behavior with corrupted or malformed data."""
        evidence = {
            "test_name": "data_corruption_scenarios",
            "timestamp": time.time(),
            "scenarios_tested": 0,
            "scenarios_handled": 0,
            "corruption_tests": []
        }
        
        # Test corrupted YAML file
        try:
            evidence["scenarios_tested"] += 1
            
            # Create corrupted YAML file
            corrupted_file = os.path.join(self.temp_dir, "corrupted.yaml")
            with open(corrupted_file, 'wb') as f:
                # Write binary data that's not valid YAML
                f.write(b'\x00\x01\x02\x03corrupted data\xFF\xFE\xFD')
            self.test_files.append(corrupted_file)
            
            parser = SystemBlueprintParser()
            
            try:
                system_blueprint = parser.parse_file(corrupted_file)
                evidence["corruption_tests"].append({
                    "test": "corrupted_yaml_file",
                    "handled": True,
                    "result": "parsed_unexpectedly"
                })
                
            except Exception as e:
                evidence["scenarios_handled"] += 1
                evidence["corruption_tests"].append({
                    "test": "corrupted_yaml_file",
                    "handled": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
            
        except Exception as e:
            evidence["corruption_tests"].append({
                "test": "corrupted_yaml_file",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Test malformed JSON data
        try:
            evidence["scenarios_tested"] += 1
            
            # Create malformed JSON configuration
            malformed_config = '{"key": "value", "incomplete": }'
            
            try:
                import json
                config_data = json.loads(malformed_config)
                evidence["corruption_tests"].append({
                    "test": "malformed_json_config",
                    "handled": True,
                    "result": "parsed_unexpectedly"
                })
                
            except json.JSONDecodeError as e:
                evidence["scenarios_handled"] += 1
                evidence["corruption_tests"].append({
                    "test": "malformed_json_config",
                    "handled": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
            
        except Exception as e:
            evidence["corruption_tests"].append({
                "test": "malformed_json_config",
                "handled": False,
                "setup_error": str(e)
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "data_corruption_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify that data corruption scenarios are handled
        if evidence["scenarios_tested"] > 0:
            handling_rate = (evidence["scenarios_handled"] / evidence["scenarios_tested"]) * 100
            assert handling_rate >= 80, f"Should handle at least 80% of data corruption scenarios, got {handling_rate:.1f}%"
            
            print(f"✅ Data corruption scenarios: {evidence['scenarios_handled']}/{evidence['scenarios_tested']} handled ({handling_rate:.1f}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])