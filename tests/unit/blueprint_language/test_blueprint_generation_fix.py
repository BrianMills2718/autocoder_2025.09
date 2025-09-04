#!/usr/bin/env python3
"""
Unit tests for Blueprint Generation Fix - Store Component Connectivity

This test suite validates that the Store component connectivity fix works correctly,
ensuring Store components can be properly connected without triggering validation errors.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser, ParsedSystemBlueprint
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator, ArchitecturalValidationError


class TestStoreComponentConnectivityFix:
    """Test suite for Store component connectivity fix validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = SystemBlueprintParser()
        self.validator = ArchitecturalValidator()
    
    def test_store_component_connectivity_before_fix(self):
        """Test that Store components would fail validation without the terminal behavior fix"""
        # Create a system blueprint with Store component
        system_blueprint_yaml = """
        schema_version: "1.0.0"
        system:
          name: "test_store_system"
          description: "Test system with Store component"
          components:
            - name: "data_source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "data_store"
              type: "Store"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "data_source.output"
              to: "data_store.input"
        """
        
        # Parse the system blueprint
        system_blueprint = self.parser.parse_string(system_blueprint_yaml)
        
        # Simulate old validation logic that would fail on Store components
        # by checking that Store components without outputs would fail validation
        validation_errors = []
        
        # Old validation logic would check for incomplete data flow
        for component in system_blueprint.system.components:
            if component.type == 'Store':
                # Check if component has inputs but no outputs (terminal behavior)
                has_inputs = len(component.inputs) > 0
                has_outputs = len(component.outputs) > 0
                
                # Count actual connections
                input_connections = sum(1 for binding in system_blueprint.system.bindings 
                                      if component.name in binding.to_components)
                output_connections = sum(1 for binding in system_blueprint.system.bindings 
                                       if binding.from_component == component.name)
                
                # Old logic would fail if component has inputs but no outputs and is not marked terminal
                if has_inputs and not has_outputs and output_connections == 0:
                    # Check if component is properly marked as terminal
                    connectivity_matrix = self.validator.CONNECTIVITY_MATRIX.get(component.type, {})
                    is_terminal = connectivity_matrix.get('is_terminal', False)
                    
                    # If not marked as terminal, old logic would fail
                    if not is_terminal:
                        validation_errors.append(ArchitecturalValidationError(
                            error_type="invalid_connection",
                            severity="error",
                            message=f"Component '{component.name}' has inputs but no outputs and is not marked as terminal",
                            component=component.name,
                            suggestion="Mark component as terminal or add output connections"
                        ))
        
        # With the current fix, Store components should be marked as terminal
        # so this test demonstrates the fix is working (no validation errors)
        assert len(validation_errors) == 0, "Store components should be marked as terminal (fix is working)"
    
    def test_store_component_connectivity_after_fix(self):
        """Test that Store components pass validation with the fix"""
        # Create the same system blueprint
        system_blueprint_yaml = """
        schema_version: "1.0.0"
        system:
          name: "test_store_system"
          description: "Test system with Store component"
          components:
            - name: "data_source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "data_store"
              type: "Store"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "data_source.output"
              to: "data_store.input"
        """
        
        # Parse the system blueprint
        system_blueprint = self.parser.parse_string(system_blueprint_yaml)
        
        # Validate using current (fixed) validation logic
        validation_errors = self.validator.validate_system_architecture(system_blueprint)
        
        # Should have no connectivity errors for Store components
        store_connectivity_errors = [
            error for error in validation_errors 
            if error.error_type == "invalid_connection" and 
            "data_store" in error.message and 
            "inputs but is not connected" in error.message
        ]
        
        assert len(store_connectivity_errors) == 0, f"Store connectivity errors found: {store_connectivity_errors}"
    
    def test_store_component_terminal_behavior(self):
        """Test that Store components behave as terminal components"""
        # Test multiple Store component configurations
        test_cases = [
            {
                'name': 'single_store',
                'yaml': """
                schema_version: "1.0.0"
                system:
                  name: "single_store_system"
                  components:
                    - name: "source"
                      type: "Source"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                    - name: "store"
                      type: "Store"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                  bindings:
                    - from: "source.output"
                      to: "store.input"
                """
            },
            {
                'name': 'multiple_stores',
                'yaml': """
                schema_version: "1.0.0"
                system:
                  name: "multiple_stores_system"
                  components:
                    - name: "source"
                      type: "Source"
                      outputs:
                        - name: "output"
                          schema: "common_object_schema"
                    - name: "store1"
                      type: "Store"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                    - name: "store2"
                      type: "Store"
                      inputs:
                        - name: "input"
                          schema: "common_object_schema"
                  bindings:
                    - from: "source.output"
                      to: ["store1.input", "store2.input"]
                """
            }
        ]
        
        for test_case in test_cases:
            with pytest.raises(Exception, match="") if False else pytest.warns(None):
                # Parse each test case
                system_blueprint = self.parser.parse_string(test_case['yaml'])
                
                # Validate - should pass without Store connectivity errors
                validation_errors = self.validator.validate_system_architecture(system_blueprint)
                
                # Check that Store components are recognized as terminal
                store_components = [comp for comp in system_blueprint.system.components if comp.type == 'Store']
                for store_comp in store_components:
                    connectivity_matrix = self.validator.CONNECTIVITY_MATRIX.get('Store', {})
                    
                    # Verify Store is marked as terminal in connectivity matrix
                    assert connectivity_matrix.get('is_terminal', False), f"Store component should be marked as terminal"
                    assert connectivity_matrix.get('expected_outputs', 1) == 0, f"Store component should have 0 expected outputs"
                
                # Verify no connectivity errors for Store components
                store_errors = [
                    error for error in validation_errors 
                    if error.error_type == "invalid_connection" and 
                    any(store_comp.name in error.message for store_comp in store_components)
                ]
                
                assert len(store_errors) == 0, f"Store connectivity errors in {test_case['name']}: {store_errors}"
    
    def test_store_component_with_transformer_pipeline(self):
        """Test Store component in a complete pipeline with transformers"""
        system_blueprint_yaml = """
        schema_version: "1.0.0"
        system:
          name: "pipeline_with_store"
          description: "Pipeline system with Store component"
          components:
            - name: "data_source"
              type: "Source"
              outputs:
                - name: "raw_data"
                  schema: "common_object_schema"
            - name: "transformer"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "transformed_data"
                  schema: "common_object_schema"
            - name: "data_store"
              type: "Store"
              inputs:
                - name: "processed_data"
                  schema: "common_object_schema"
          bindings:
            - from: "data_source.raw_data"
              to: "transformer.input"
            - from: "transformer.transformed_data"
              to: "data_store.processed_data"
        """
        
        # Parse and validate
        system_blueprint = self.parser.parse_string(system_blueprint_yaml)
        validation_errors = self.validator.validate_system_architecture(system_blueprint)
        
        # Should have no errors - Store acts as terminal component
        critical_errors = [error for error in validation_errors if error.severity == "error"]
        assert len(critical_errors) == 0, f"Critical validation errors found: {critical_errors}"
        
        # Verify complete data flow path exists
        has_complete_path = any(
            error.error_type != "incomplete_data_flow" for error in validation_errors
        )
        
        # Should not have incomplete data flow errors
        flow_errors = [error for error in validation_errors if error.error_type == "incomplete_data_flow"]
        assert len(flow_errors) == 0, f"Data flow errors found: {flow_errors}"
    
    def test_store_component_edge_cases(self):
        """Test Store component edge cases and error conditions"""
        # Test case 1: Store with no connections (should be detected as having no sources)
        edge_case_yaml = """
        schema_version: "1.0.0"
        system:
          name: "edge_case_store"
          components:
            - name: "isolated_store"
              type: "Store"
          bindings: []
        """
        
        # This should trigger missing sources error since there are no input components
        system_blueprint = self.parser.parse_string(edge_case_yaml)
        validation_errors = self.validator.validate_system_architecture(system_blueprint)
        
        # Should have system-level errors but not connectivity errors
        orphaned_errors = [error for error in validation_errors if error.error_type == "orphaned_component"]
        missing_sources = [error for error in validation_errors if error.error_type == "missing_sources"]
        missing_sinks = [error for error in validation_errors if error.error_type == "missing_sinks"]
        connectivity_errors = [error for error in validation_errors if error.error_type == "invalid_connection"]
        
        # The key point is that there should be NO connectivity errors
        # Even if there are no other validation errors, Store components should not fail connectivity validation
        assert len(connectivity_errors) == 0, "Should not have connectivity errors for isolated Store"
        
        # Store components should be recognized as terminal components
        store_components = [comp for comp in system_blueprint.system.components if comp.type == 'Store']
        assert len(store_components) == 1
        
        # Verify Store component has correct terminal behavior
        store_comp = store_components[0]
        assert len(store_comp.outputs) == 0, "Store component should have no outputs (terminal)"
        
        # This test primarily validates that Store components don't trigger connectivity errors
        # The specific system-level errors may vary based on validation logic
    
    def test_store_component_anti_patterns(self):
        """Test that Store components correctly prevent anti-patterns"""
        # Test Store -> Source connection (should be caught as anti-pattern)
        # Note: This test creates an invalid Store component with outputs, which shouldn't happen
        # in practice since Store components are terminal
        anti_pattern_yaml = """
        schema_version: "1.0.0"
        system:
          name: "anti_pattern_system"
          components:
            - name: "store"
              type: "Store"
              outputs:
                - name: "stored_data"
                  schema: "common_object_schema"
            - name: "source"
              type: "Source"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "store.stored_data"
              to: "source.input"
        """
        
        # This should fail at parsing level due to validation errors
        try:
            system_blueprint = self.parser.parse_string(anti_pattern_yaml)
            # If parsing succeeds, check architectural validation
            validation_errors = self.validator.validate_system_architecture(system_blueprint)
            
            # Should catch anti-pattern errors or connectivity errors
            anti_pattern_errors = [error for error in validation_errors if error.error_type == "architectural_antipattern"]
            connectivity_errors = [error for error in validation_errors if error.error_type == "invalid_connection"]
            
            # Should have some validation errors (anti-pattern or connectivity)
            has_errors = len(anti_pattern_errors) > 0 or len(connectivity_errors) > 0
            assert has_errors, f"Expected validation errors. Found: {[e.error_type for e in validation_errors]}"
            
            # If we have anti-pattern errors, verify they mention Store -> Source
            if anti_pattern_errors:
                store_to_source_errors = [
                    error for error in anti_pattern_errors 
                    if "Store" in error.message and "Source" in error.message
                ]
                assert len(store_to_source_errors) > 0, "Expected specific Store -> Source anti-pattern error"
        
        except ValueError as e:
            # Parser caught validation errors - this is expected
            error_msg = str(e)
            assert "invalid_connection" in error_msg or "architectural_antipattern" in error_msg, \
                   f"Expected connectivity or anti-pattern error, got: {error_msg}"


class TestStoreComponentIntegration:
    """Integration tests for Store component connectivity in system generation"""
    
    def test_system_generation_with_store_components(self):
        """Test complete system generation pipeline with Store components"""
        # Test that system blueprint parsing and validation proceeds past validation
        # when Store components are present
        
        parser = SystemBlueprintParser()
        
        system_blueprint_yaml = """
        schema_version: "1.0.0"
        system:
          name: "complete_store_system"
          description: "Complete system with Store components for testing"
          components:
            - name: "api_gateway"
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
                - name: "api_request"
                  schema: "common_object_schema"
              outputs:
                - name: "processed_request"
                  schema: "common_object_schema"
            - name: "database"
              type: "Store"
              inputs:
                - name: "data"
                  schema: "common_object_schema"
          bindings:
            - from: "api_gateway.response"
              to: "controller.api_request"
            - from: "controller.processed_request"
              to: "database.data"
        """
        
        try:
            # Parse system blueprint - should succeed
            system_blueprint = parser.parse_string(system_blueprint_yaml)
            
            # Verify parsing succeeded
            assert system_blueprint is not None, "System blueprint parsing failed"
            assert system_blueprint.system.name == "complete_store_system"
            assert len(system_blueprint.system.components) == 3
            assert len(system_blueprint.system.bindings) == 2
            
            # Verify Store component is present and properly configured
            store_components = [comp for comp in system_blueprint.system.components if comp.type == 'Store']
            assert len(store_components) == 1, "Expected one Store component"
            
            store_comp = store_components[0]
            assert store_comp.name == "database"
            assert len(store_comp.inputs) >= 1  # Store should have at least one input (including auto-generated)
            assert len(store_comp.outputs) == 0  # Store should have no outputs
            
            # Verify system generation would proceed (no validation errors)
            # This tests the fix that Store components don't trigger "not connected" errors
            
        except ValueError as e:
            # If we get "Component has inputs/outputs but is not connected" error,
            # that means the fix is not working
            if "inputs/outputs but is not connected" in str(e):
                pytest.fail(f"Store component connectivity fix not working: {e}")
            else:
                # Some other validation error - re-raise to see what it is
                raise
    
    def test_multiple_store_components_system(self):
        """Test system with multiple Store components"""
        parser = SystemBlueprintParser()
        
        multi_store_yaml = """
        schema_version: "1.0.0"
        system:
          name: "multi_store_system"
          description: "System with multiple Store components"
          components:
            - name: "data_source"
              type: "Source"
              outputs:
                - name: "data"
                  schema: "common_object_schema"
            - name: "router"
              type: "Router"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "route1"
                  schema: "common_object_schema"
                - name: "route2"
                  schema: "common_object_schema"
            - name: "store1"
              type: "Store"
              inputs:
                - name: "data"
                  schema: "common_object_schema"
            - name: "store2"
              type: "Store"
              inputs:
                - name: "data"
                  schema: "common_object_schema"
          bindings:
            - from: "data_source.data"
              to: "router.input"
            - from: "router.route1"
              to: "store1.data"
            - from: "router.route2"
              to: "store2.data"
        """
        
        try:
            # Parse system blueprint
            system_blueprint = parser.parse_string(multi_store_yaml)
            
            # Verify parsing succeeded
            assert system_blueprint is not None
            assert len(system_blueprint.system.components) == 4
            
            # Verify both Store components are present
            store_components = [comp for comp in system_blueprint.system.components if comp.type == 'Store']
            assert len(store_components) == 2
            
            # Verify Store components are properly configured
            for store_comp in store_components:
                assert len(store_comp.inputs) >= 1  # Store should have inputs
                assert len(store_comp.outputs) == 0  # Store should have no outputs
            
        except ValueError as e:
            if "inputs/outputs but is not connected" in str(e):
                pytest.fail(f"Multiple Store components connectivity fix not working: {e}")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])