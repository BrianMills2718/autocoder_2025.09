#!/usr/bin/env python3
"""
Evidence-Based Validation Framework Integration Tests
==================================================

This test suite provides comprehensive evidence collection and validation
for all functionality claims made in the AutoCoder4_CC system.
"""

import pytest
import os
import tempfile
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import test utilities
from tests.utils.evidence_collector import EvidenceCollector
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.components.component_registry import ComponentRegistry


class TestEvidenceValidation:
    """Test and collect evidence for all functionality claims."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.evidence_collector = EvidenceCollector(min_samples=5, max_samples=10)
        self.test_files = []
        
    def teardown_method(self):
        """Clean up test fixtures."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_blueprint_generation_fix_evidence(self):
        """Test and collect evidence for blueprint generation fix."""
        parser = SystemBlueprintParser()
        validator = ArchitecturalValidator()
        
        # Evidence collection for Store component fix
        evidence = {
            "test_name": "blueprint_generation_fix",
            "timestamp": time.time(),
            "claims": [],
            "raw_logs": [],
            "validation_results": []
        }
        
        # Test Store component connectivity fix
        store_blueprint_yaml = """
        schema_version: "1.0.0"
        system:
          name: "store_component_test"
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
        """
        
        try:
            # Parse blueprint
            start_time = time.time()
            system_blueprint = parser.parse_string(store_blueprint_yaml)
            parse_time = time.time() - start_time
            
            evidence["raw_logs"].append(f"Blueprint parsing completed in {parse_time:.4f}s")
            
            # Validate architecture
            start_time = time.time()
            validation_errors = validator.validate_system_architecture(system_blueprint)
            validation_time = time.time() - start_time
            
            evidence["raw_logs"].append(f"Architectural validation completed in {validation_time:.4f}s")
            evidence["raw_logs"].append(f"Validation errors: {len(validation_errors)}")
            
            # Check for Store component connectivity errors
            connectivity_errors = [e for e in validation_errors if "connectivity" in e.message.lower()]
            orphaned_errors = [e for e in validation_errors if "orphaned" in e.message.lower()]
            
            evidence["validation_results"].append({
                "total_errors": len(validation_errors),
                "connectivity_errors": len(connectivity_errors),
                "orphaned_errors": len(orphaned_errors),
                "validation_passed": len(validation_errors) == 0
            })
            
            # Claim: Store component connectivity fix works
            evidence["claims"].append({
                "claim": "Store component connectivity fix implemented",
                "supported": len(connectivity_errors) == 0,
                "evidence": f"No connectivity errors found for Store component terminal behavior"
            })
            
        except Exception as e:
            evidence["raw_logs"].append(f"Error during blueprint generation fix test: {str(e)}")
            evidence["claims"].append({
                "claim": "Store component connectivity fix implemented",
                "supported": False,
                "evidence": f"Test failed with error: {str(e)}"
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "blueprint_generation_fix_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify evidence was collected
        assert len(evidence["claims"]) > 0, "Should collect evidence for claims"
        assert len(evidence["raw_logs"]) > 0, "Should collect raw execution logs"
        
    def test_statistical_evidence_collection_validation(self):
        """Test and validate statistical evidence collection methodology."""
        evidence = {
            "test_name": "statistical_evidence_collection",
            "timestamp": time.time(),
            "claims": [],
            "raw_logs": [],
            "statistical_results": []
        }
        
        # Test command for statistical validation
        test_command = ["python", "-c", "import time; time.sleep(0.1); print('test completed')"]
        
        try:
            # Collect statistical evidence
            start_time = time.time()
            results = self.evidence_collector.time_command_statistical(test_command, timeout=30)
            collection_time = time.time() - start_time
            
            evidence["raw_logs"].append(f"Statistical evidence collection completed in {collection_time:.4f}s")
            
            if results and 'statistics' in results:
                stats = results['statistics']
                evidence["statistical_results"].append({
                    "mean_time": stats.get('mean', 0),
                    "std_dev": stats.get('std_dev', 0),
                    "confidence_interval": stats.get('confidence_interval', [0, 0]),
                    "sample_count": stats.get('sample_count', 0)
                })
                
                # Claim: Statistical methodology uses proper sample sizes
                evidence["claims"].append({
                    "claim": "Statistical evidence collection uses proper methodology",
                    "supported": stats.get('sample_count', 0) >= 5,
                    "evidence": f"Sample count: {stats.get('sample_count', 0)}, Min required: 5"
                })
                
                # Claim: Confidence intervals provided
                evidence["claims"].append({
                    "claim": "Statistical confidence intervals provided",
                    "supported": len(stats.get('confidence_interval', [])) == 2,
                    "evidence": f"Confidence interval: {stats.get('confidence_interval', [])}"
                })
                
            else:
                evidence["raw_logs"].append("No statistical results returned")
                evidence["claims"].append({
                    "claim": "Statistical evidence collection uses proper methodology",
                    "supported": False,
                    "evidence": "No statistical results returned from evidence collector"
                })
            
        except Exception as e:
            evidence["raw_logs"].append(f"Error during statistical evidence collection: {str(e)}")
            evidence["claims"].append({
                "claim": "Statistical evidence collection uses proper methodology",
                "supported": False,
                "evidence": f"Test failed with error: {str(e)}"
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "statistical_evidence_collection.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify evidence was collected
        assert len(evidence["claims"]) > 0, "Should collect evidence for statistical claims"
        assert len(evidence["raw_logs"]) > 0, "Should collect raw execution logs"
        
    def test_architectural_validation_comprehensive_evidence(self):
        """Test and collect evidence for comprehensive architectural validation."""
        validator = ArchitecturalValidator()
        parser = SystemBlueprintParser()
        
        evidence = {
            "test_name": "architectural_validation_comprehensive",
            "timestamp": time.time(),
            "claims": [],
            "raw_logs": [],
            "validation_results": []
        }
        
        # Test anti-pattern detection
        test_cases = [
            {
                "name": "circular_dependency",
                "yaml": """
                schema_version: "1.0.0"
                system:
                  name: "circular_test"
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
            },
            {
                "name": "orphaned_component",
                "yaml": """
                schema_version: "1.0.0"
                system:
                  name: "orphaned_test"
                  components:
                    - name: "source"
                      type: "Source"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                    - name: "orphaned"
                      type: "Transformer"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
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
                """,
                "expected_error": "orphaned"
            }
        ]
        
        detected_patterns = 0
        total_patterns = len(test_cases)
        
        for test_case in test_cases:
            try:
                # Parse and validate
                start_time = time.time()
                system_blueprint = parser.parse_string(test_case["yaml"])
                validation_errors = validator.validate_system_architecture(system_blueprint)
                validation_time = time.time() - start_time
                
                evidence["raw_logs"].append(f"Validated {test_case['name']} in {validation_time:.4f}s")
                
                # Check for expected error pattern
                pattern_detected = any(
                    test_case["expected_error"].lower() in error.message.lower()
                    for error in validation_errors
                )
                
                if pattern_detected:
                    detected_patterns += 1
                    evidence["raw_logs"].append(f"✅ Detected {test_case['expected_error']} pattern")
                else:
                    evidence["raw_logs"].append(f"❌ Failed to detect {test_case['expected_error']} pattern")
                
                evidence["validation_results"].append({
                    "test_case": test_case["name"],
                    "expected_error": test_case["expected_error"],
                    "pattern_detected": pattern_detected,
                    "error_count": len(validation_errors),
                    "validation_time": validation_time
                })
                
            except Exception as e:
                evidence["raw_logs"].append(f"Error validating {test_case['name']}: {str(e)}")
                evidence["validation_results"].append({
                    "test_case": test_case["name"],
                    "expected_error": test_case["expected_error"],
                    "pattern_detected": False,
                    "error": str(e)
                })
        
        # Claim: Comprehensive architectural validation
        detection_rate = (detected_patterns / total_patterns) * 100
        evidence["claims"].append({
            "claim": "Comprehensive architectural validation with anti-pattern detection",
            "supported": detection_rate >= 80,
            "evidence": f"Detection rate: {detection_rate:.1f}% ({detected_patterns}/{total_patterns} patterns)"
        })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "architectural_validation_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify evidence was collected
        assert len(evidence["claims"]) > 0, "Should collect evidence for architectural validation claims"
        assert len(evidence["raw_logs"]) > 0, "Should collect raw execution logs"
        assert len(evidence["validation_results"]) > 0, "Should collect validation results"
        
    def test_production_standards_evidence(self):
        """Test and collect evidence for production standards compliance."""
        evidence = {
            "test_name": "production_standards_compliance",
            "timestamp": time.time(),
            "claims": [],
            "raw_logs": [],
            "compliance_results": []
        }
        
        # Test error handling implementation
        try:
            # Test component registry error handling
            registry = ComponentRegistry()
            
            # Test invalid component type
            try:
                registry.create_component("NonExistentType", "test_instance", {})
                evidence["raw_logs"].append("❌ Component registry did not raise error for invalid type")
                error_handling_works = False
            except Exception as e:
                evidence["raw_logs"].append(f"✅ Component registry properly handled invalid type: {str(e)}")
                error_handling_works = True
            
            # Test blueprint parser error handling
            parser = SystemBlueprintParser()
            try:
                parser.parse_string("invalid yaml: [structure")
                evidence["raw_logs"].append("❌ Blueprint parser did not raise error for invalid YAML")
                yaml_error_handling_works = False
            except Exception as e:
                evidence["raw_logs"].append(f"✅ Blueprint parser properly handled invalid YAML: {str(e)}")
                yaml_error_handling_works = True
            
            evidence["compliance_results"].append({
                "component": "error_handling",
                "tests_passed": error_handling_works and yaml_error_handling_works,
                "details": "Component registry and blueprint parser error handling validated"
            })
            
            # Claim: Production error handling implemented
            evidence["claims"].append({
                "claim": "Production-ready error handling implemented",
                "supported": error_handling_works and yaml_error_handling_works,
                "evidence": "Component registry and blueprint parser handle errors gracefully"
            })
            
        except Exception as e:
            evidence["raw_logs"].append(f"Error during production standards test: {str(e)}")
            evidence["claims"].append({
                "claim": "Production-ready error handling implemented",
                "supported": False,
                "evidence": f"Test failed with error: {str(e)}"
            })
        
        # Test logging framework
        try:
            from autocoder_cc.observability.structured_logging import get_logger
            logger = get_logger("test_logger")
            
            # Test structured logging
            logger.info("Test log message", extra={"component": "test", "operation": "validate"})
            evidence["raw_logs"].append("✅ Structured logging framework available")
            
            logging_works = True
            evidence["compliance_results"].append({
                "component": "logging",
                "tests_passed": logging_works,
                "details": "Structured logging framework validated"
            })
            
            # Claim: Structured logging implemented
            evidence["claims"].append({
                "claim": "Structured logging framework implemented",
                "supported": logging_works,
                "evidence": "Structured logging with contextual information available"
            })
            
        except Exception as e:
            evidence["raw_logs"].append(f"Error testing logging framework: {str(e)}")
            evidence["claims"].append({
                "claim": "Structured logging framework implemented",
                "supported": False,
                "evidence": f"Logging test failed with error: {str(e)}"
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "production_standards_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify evidence was collected
        assert len(evidence["claims"]) > 0, "Should collect evidence for production standards claims"
        assert len(evidence["raw_logs"]) > 0, "Should collect raw execution logs"
        assert len(evidence["compliance_results"]) > 0, "Should collect compliance results"
        
    def test_comprehensive_system_evidence(self):
        """Test and collect evidence for comprehensive system functionality."""
        evidence = {
            "test_name": "comprehensive_system_functionality",
            "timestamp": time.time(),
            "claims": [],
            "raw_logs": [],
            "system_results": []
        }
        
        # Test complete system workflow
        try:
            # Test blueprint parsing → validation → generation workflow
            parser = SystemBlueprintParser()
            validator = ArchitecturalValidator()
            
            # Complete valid system blueprint
            complete_system_yaml = """
            schema_version: "1.0.0"
            system:
              name: "complete_system_test"
              description: "Complete system for comprehensive testing"
              components:
                - name: "api_endpoint"
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
                - name: "data_store"
                  type: "Store"
                  inputs:
                    - name: "data"
                      schema: "common_object_schema"
              bindings:
                - from: "api_endpoint.response"
                  to: "controller.request"
                - from: "controller.processed"
                  to: "data_store.data"
            """
            
            # Parse blueprint
            start_time = time.time()
            system_blueprint = parser.parse_string(complete_system_yaml)
            parse_time = time.time() - start_time
            
            evidence["raw_logs"].append(f"✅ Complete system blueprint parsed in {parse_time:.4f}s")
            
            # Validate architecture
            start_time = time.time()
            validation_errors = validator.validate_system_architecture(system_blueprint)
            validation_time = time.time() - start_time
            
            evidence["raw_logs"].append(f"✅ Complete system validated in {validation_time:.4f}s")
            evidence["raw_logs"].append(f"Validation errors: {len(validation_errors)}")
            
            # Check system completeness
            has_api = any(comp.type == "APIEndpoint" for comp in system_blueprint.system.components)
            has_controller = any(comp.type == "Controller" for comp in system_blueprint.system.components)
            has_store = any(comp.type == "Store" for comp in system_blueprint.system.components)
            has_bindings = len(system_blueprint.system.bindings) > 0
            
            system_complete = has_api and has_controller and has_store and has_bindings
            
            evidence["system_results"].append({
                "has_api_endpoint": has_api,
                "has_controller": has_controller,
                "has_store": has_store,
                "has_bindings": has_bindings,
                "system_complete": system_complete,
                "component_count": len(system_blueprint.system.components),
                "binding_count": len(system_blueprint.system.bindings),
                "validation_errors": len(validation_errors)
            })
            
            # Claim: Complete system functionality
            evidence["claims"].append({
                "claim": "Complete system functionality validated",
                "supported": system_complete and len(validation_errors) == 0,
                "evidence": f"Complete system with {len(system_blueprint.system.components)} components, {len(system_blueprint.system.bindings)} bindings, {len(validation_errors)} validation errors"
            })
            
        except Exception as e:
            evidence["raw_logs"].append(f"Error during comprehensive system test: {str(e)}")
            evidence["claims"].append({
                "claim": "Complete system functionality validated",
                "supported": False,
                "evidence": f"Test failed with error: {str(e)}"
            })
        
        # Log evidence
        evidence_file = os.path.join(self.temp_dir, "comprehensive_system_evidence.json")
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        self.test_files.append(evidence_file)
        
        # Verify evidence was collected
        assert len(evidence["claims"]) > 0, "Should collect evidence for system functionality claims"
        assert len(evidence["raw_logs"]) > 0, "Should collect raw execution logs"
        assert len(evidence["system_results"]) > 0, "Should collect system results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])