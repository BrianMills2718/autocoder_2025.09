#!/usr/bin/env python3
"""
Architectural Test Cases - Comprehensive Test Data for Architectural Validation

This module provides comprehensive test cases for architectural validation,
including valid systems, invalid systems, and edge cases.
"""

from typing import Dict, Any, List

# Valid architectural patterns
VALID_ARCHITECTURES = {
    'simple_pipeline': """
    schema_version: "1.0.0"
    system:
      name: "simple_pipeline"
      description: "Simple linear pipeline"
      components:
        - name: "source"
          type: "Source"
          outputs:
            - name: "output"
              schema: "common_object_schema"
        - name: "transformer"
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
          to: "transformer.input"
        - from: "transformer.output"
          to: "sink.input"
    """,
    
    'api_system': """
    schema_version: "1.0.0"
    system:
      name: "api_system"
      description: "API-based system with controller and store"
      components:
        - name: "api_endpoint"
          type: "APIEndpoint"
          outputs:
            - name: "requests"
              schema: "common_object_schema"
        - name: "controller"
          type: "Controller"
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
        - from: "api_endpoint.requests"
          to: "controller.request"
        - from: "controller.response"
          to: "store.data"
    """,
    
    'fan_out_system': """
    schema_version: "1.0.0"
    system:
      name: "fan_out_system"
      description: "Fan-out system with router"
      components:
        - name: "source"
          type: "Source"
          outputs:
            - name: "output"
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
        - name: "sink1"
          type: "Sink"
          inputs:
            - name: "input"
              schema: "common_object_schema"
        - name: "sink2"
          type: "Sink"
          inputs:
            - name: "input"
              schema: "common_object_schema"
      bindings:
        - from: "source.output"
          to: "router.input"
        - from: "router.route1"
          to: "sink1.input"
        - from: "router.route2"
          to: "sink2.input"
    """,
    
    'fan_in_system': """
    schema_version: "1.0.0"
    system:
      name: "fan_in_system"
      description: "Fan-in system with aggregator"
      components:
        - name: "source1"
          type: "Source"
          outputs:
            - name: "output"
              schema: "common_object_schema"
        - name: "source2"
          type: "Source"
          outputs:
            - name: "output"
              schema: "common_object_schema"
        - name: "aggregator"
          type: "Aggregator"
          inputs:
            - name: "input1"
              schema: "common_object_schema"
            - name: "input2"
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
        - from: "source1.output"
          to: "aggregator.input1"
        - from: "source2.output"
          to: "aggregator.input2"
        - from: "aggregator.output"
          to: "sink.input"
    """
}

# Invalid architectural patterns
INVALID_ARCHITECTURES = {
    'source_to_source': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "invalid_source_to_source"
          components:
            - name: "source1"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "source2"
              type: "Source"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "source1.output"
              to: "source2.input"
        """,
        'expected_errors': ['invalid_connection'],
        'error_pattern': 'Source.*cannot connect to Source'
    },
    
    'sink_to_anything': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "invalid_sink_to_transformer"
          components:
            - name: "sink"
              type: "Sink"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "transformer"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "sink.output"
              to: "transformer.input"
        """,
        'expected_errors': ['invalid_connection'],
        'error_pattern': 'Sink.*cannot connect'
    },
    
    'store_to_source_antipattern': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "store_to_source_antipattern"
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
        """,
        'expected_errors': ['architectural_antipattern', 'invalid_connection'],
        'error_pattern': 'Store.*connecting to Source'
    },
    
    'circular_dependency': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "circular_dependency"
          components:
            - name: "transformer1"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "transformer2"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings:
            - from: "transformer1.output"
              to: "transformer2.input"
            - from: "transformer2.output"
              to: "transformer1.input"
        """,
        'expected_errors': ['circular_dependency'],
        'error_pattern': 'Circular dependency'
    }
}

# Architectural anti-patterns
ARCHITECTURAL_ANTIPATTERNS = {
    'excessive_fan_out': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "excessive_fan_out"
          components:
            - name: "source"
              type: "Source"
              outputs:
                - name: "output1"
                  schema: "common_object_schema"
                - name: "output2"
                  schema: "common_object_schema"
                - name: "output3"
                  schema: "common_object_schema"
                - name: "output4"
                  schema: "common_object_schema"
                - name: "output5"
                  schema: "common_object_schema"
            - name: "sink1"
              type: "Sink"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
            - name: "sink2"
              type: "Sink"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
            - name: "sink3"
              type: "Sink"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
            - name: "sink4"
              type: "Sink"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
            - name: "sink5"
              type: "Sink"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "source.output1"
              to: "sink1.input"
            - from: "source.output2"
              to: "sink2.input"
            - from: "source.output3"
              to: "sink3.input"
            - from: "source.output4"
              to: "sink4.input"
            - from: "source.output5"
              to: "sink5.input"
        """,
        'expected_errors': ['excessive_fan_out'],
        'error_pattern': 'high fan-out'
    },
    
    'data_flow_dead_end': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "data_flow_dead_end"
          components:
            - name: "source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "transformer"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "dead_end"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings:
            - from: "source.output"
              to: "transformer.input"
            - from: "transformer.output"
              to: "dead_end.input"
        """,
        'expected_errors': ['missing_sinks'],
        'error_pattern': 'no sink components'
    }
}

# Edge cases and boundary conditions
EDGE_CASES = {
    'single_component': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "single_component"
          components:
            - name: "lonely_source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings: []
        """,
        'expected_errors': ['missing_sinks'],
        'error_pattern': 'no sink components'
    },
    
    'orphaned_component': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "orphaned_component"
          components:
            - name: "source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "orphaned_transformer"
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
        'expected_errors': ['orphaned_component'],
        'error_pattern': 'orphaned.*no input or output connections'
    },
    
    'schema_mismatch': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "schema_mismatch"
          components:
            - name: "source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_string_schema"
            - name: "transformer"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_number_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings:
            - from: "source.output"
              to: "transformer.input"
        """,
        'expected_errors': ['schema_compatibility'],
        'error_pattern': 'schema mismatch'
    }
}

# Component connectivity matrix tests
CONNECTIVITY_MATRIX_TESTS = [
    # Valid connections
    {'from': 'Source', 'to': 'Transformer', 'valid': True},
    {'from': 'Source', 'to': 'Filter', 'valid': True},
    {'from': 'Source', 'to': 'Router', 'valid': True},
    {'from': 'Source', 'to': 'Sink', 'valid': True},
    {'from': 'Source', 'to': 'Store', 'valid': True},
    {'from': 'Source', 'to': 'APIEndpoint', 'valid': True},
    
    {'from': 'Transformer', 'to': 'Transformer', 'valid': True},
    {'from': 'Transformer', 'to': 'Filter', 'valid': True},
    {'from': 'Transformer', 'to': 'Router', 'valid': True},
    {'from': 'Transformer', 'to': 'Sink', 'valid': True},
    {'from': 'Transformer', 'to': 'Store', 'valid': True},
    {'from': 'Transformer', 'to': 'APIEndpoint', 'valid': True},
    
    {'from': 'Router', 'to': 'Transformer', 'valid': True},
    {'from': 'Router', 'to': 'Filter', 'valid': True},
    {'from': 'Router', 'to': 'Router', 'valid': True},
    {'from': 'Router', 'to': 'Sink', 'valid': True},
    {'from': 'Router', 'to': 'Store', 'valid': True},
    {'from': 'Router', 'to': 'APIEndpoint', 'valid': True},
    
    {'from': 'Controller', 'to': 'Store', 'valid': True},
    {'from': 'Controller', 'to': 'Sink', 'valid': True},
    {'from': 'Controller', 'to': 'APIEndpoint', 'valid': True},
    {'from': 'Controller', 'to': 'Transformer', 'valid': True},
    
    {'from': 'Store', 'to': 'APIEndpoint', 'valid': True},
    
    # Invalid connections
    {'from': 'Source', 'to': 'Source', 'valid': False},
    {'from': 'Sink', 'to': 'Transformer', 'valid': False},
    {'from': 'Sink', 'to': 'Source', 'valid': False},
    {'from': 'Sink', 'to': 'Sink', 'valid': False},
    {'from': 'Store', 'to': 'Source', 'valid': False},
    {'from': 'Store', 'to': 'Transformer', 'valid': False},
    {'from': 'Store', 'to': 'Sink', 'valid': False},
    {'from': 'EventSource', 'to': 'EventSource', 'valid': False},
]

# System completeness tests
SYSTEM_COMPLETENESS_TESTS = {
    'api_without_endpoint': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "api_without_endpoint"
          description: "This system provides REST API functionality"
          components:
            - name: "controller"
              type: "Controller"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "store"
              type: "Store"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
          bindings:
            - from: "controller.output"
              to: "store.input"
        """,
        'expected_errors': ['missing_essential_component'],
        'error_pattern': 'API.*no APIEndpoint'
    },
    
    'storage_without_store': {
        'yaml': """
        schema_version: "1.0.0"
        system:
          name: "storage_without_store"
          description: "This system persists data to storage"
          components:
            - name: "source"
              type: "Source"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
            - name: "transformer"
              type: "Transformer"
              inputs:
                - name: "input"
                  schema: "common_object_schema"
              outputs:
                - name: "output"
                  schema: "common_object_schema"
          bindings:
            - from: "source.output"
              to: "transformer.input"
        """,
        'expected_errors': ['missing_essential_component'],
        'error_pattern': 'storage.*no Store'
    }
}

def get_test_case(category: str, name: str) -> Dict[str, Any]:
    """Get a specific test case by category and name"""
    test_cases = {
        'valid': VALID_ARCHITECTURES,
        'invalid': INVALID_ARCHITECTURES,
        'antipatterns': ARCHITECTURAL_ANTIPATTERNS,
        'edge_cases': EDGE_CASES,
        'completeness': SYSTEM_COMPLETENESS_TESTS
    }
    
    if category not in test_cases:
        raise ValueError(f"Unknown category: {category}")
    
    if name not in test_cases[category]:
        raise ValueError(f"Unknown test case: {name} in category {category}")
    
    return test_cases[category][name]

def get_all_test_cases(category: str) -> Dict[str, Any]:
    """Get all test cases in a category"""
    test_cases = {
        'valid': VALID_ARCHITECTURES,
        'invalid': INVALID_ARCHITECTURES,
        'antipatterns': ARCHITECTURAL_ANTIPATTERNS,
        'edge_cases': EDGE_CASES,
        'completeness': SYSTEM_COMPLETENESS_TESTS
    }
    
    if category not in test_cases:
        raise ValueError(f"Unknown category: {category}")
    
    return test_cases[category]

def create_connectivity_test_yaml(from_type: str, to_type: str) -> str:
    """Create a YAML test case for connectivity validation"""
    return f"""
    schema_version: "1.0.0"
    system:
      name: "connectivity_test_{from_type.lower()}_to_{to_type.lower()}"
      components:
        - name: "from_component"
          type: "{from_type}"
          outputs:
            - name: "output"
              schema: "common_object_schema"
        - name: "to_component"
          type: "{to_type}"
          inputs:
            - name: "input"
              schema: "common_object_schema"
      bindings:
        - from: "from_component.output"
          to: "to_component.input"
    """

def get_connectivity_matrix_tests() -> List[Dict[str, Any]]:
    """Get all connectivity matrix test cases"""
    return CONNECTIVITY_MATRIX_TESTS