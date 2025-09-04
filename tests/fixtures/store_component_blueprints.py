#!/usr/bin/env python3
"""
Test fixtures for Store component blueprints and test cases

This module provides various system blueprint configurations
for testing Store component connectivity fixes.
"""

from typing import Dict, Any, List

# Basic Store component system blueprint
BASIC_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "basic_store_system"
  description: "Simple system with Store component"
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

# Store component with transformer pipeline
PIPELINE_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "pipeline_store_system"
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

# Multiple Store components system
MULTIPLE_STORES_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "multiple_stores_system"
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

# API-Store system blueprint
API_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "api_store_system"
  description: "API system with Store component"
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

# Store component with anti-pattern (for testing error detection)
ANTI_PATTERN_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "anti_pattern_store_system"
  description: "System with Store anti-pattern"
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

# Isolated Store component (for testing orphaned component detection)
ISOLATED_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "isolated_store_system"
  description: "System with isolated Store component"
  components:
    - name: "isolated_store"
      type: "Store"
  bindings: []
"""

# Complex Store system with multiple patterns
COMPLEX_STORE_BLUEPRINT = """
schema_version: "1.0.0"
system:
  name: "complex_store_system"
  description: "Complex system with multiple Store components and patterns"
  components:
    - name: "event_source"
      type: "EventSource"
      outputs:
        - name: "events"
          schema: "common_object_schema"
    - name: "event_filter"
      type: "Filter"
      inputs:
        - name: "input"
          schema: "common_object_schema"
      outputs:
        - name: "filtered"
          schema: "common_object_schema"
    - name: "aggregator"
      type: "Aggregator"
      inputs:
        - name: "input1"
          schema: "common_object_schema"
        - name: "input2"
          schema: "common_object_schema"
      outputs:
        - name: "aggregated"
          schema: "common_object_schema"
    - name: "metrics_store"
      type: "Store"
      inputs:
        - name: "metrics"
          schema: "common_object_schema"
    - name: "event_store"
      type: "Store"
      inputs:
        - name: "events"
          schema: "common_object_schema"
    - name: "api_endpoint"
      type: "APIEndpoint"
      inputs:
        - name: "request"
          schema: "common_object_schema"
      outputs:
        - name: "response"
          schema: "common_object_schema"
  bindings:
    - from: "event_source.events"
      to: "event_filter.input"
    - from: "event_filter.filtered"
      to: ["aggregator.input1", "event_store.events"]
    - from: "api_endpoint.response"
      to: "aggregator.input2"
    - from: "aggregator.aggregated"
      to: "metrics_store.metrics"
"""

# Store component configurations for parameterized tests
STORE_TEST_CONFIGURATIONS = [
    {
        'name': 'basic_store',
        'description': 'Basic Store component test',
        'blueprint': BASIC_STORE_BLUEPRINT,
        'expected_components': 2,
        'expected_bindings': 1,
        'expected_stores': 1,
        'should_pass_validation': True
    },
    {
        'name': 'pipeline_store',
        'description': 'Pipeline with Store component',
        'blueprint': PIPELINE_STORE_BLUEPRINT,
        'expected_components': 3,
        'expected_bindings': 2,
        'expected_stores': 1,
        'should_pass_validation': True
    },
    {
        'name': 'multiple_stores',
        'description': 'Multiple Store components',
        'blueprint': MULTIPLE_STORES_BLUEPRINT,
        'expected_components': 4,
        'expected_bindings': 3,
        'expected_stores': 2,
        'should_pass_validation': True
    },
    {
        'name': 'api_store',
        'description': 'API with Store component',
        'blueprint': API_STORE_BLUEPRINT,
        'expected_components': 3,
        'expected_bindings': 2,
        'expected_stores': 1,
        'should_pass_validation': True
    },
    {
        'name': 'anti_pattern_store',
        'description': 'Store anti-pattern test',
        'blueprint': ANTI_PATTERN_STORE_BLUEPRINT,
        'expected_components': 2,
        'expected_bindings': 1,
        'expected_stores': 1,
        'should_pass_validation': False,
        'expected_error_types': ['architectural_antipattern']
    },
    {
        'name': 'isolated_store',
        'description': 'Isolated Store component',
        'blueprint': ISOLATED_STORE_BLUEPRINT,
        'expected_components': 1,
        'expected_bindings': 0,
        'expected_stores': 1,
        'should_pass_validation': False,
        'expected_error_types': ['orphaned_component']
    },
    {
        'name': 'complex_store',
        'description': 'Complex Store system',
        'blueprint': COMPLEX_STORE_BLUEPRINT,
        'expected_components': 6,
        'expected_bindings': 4,
        'expected_stores': 2,
        'should_pass_validation': True
    }
]

# Test cases for Store component connectivity matrix validation
STORE_CONNECTIVITY_MATRIX_TESTS = [
    {
        'name': 'store_from_source',
        'description': 'Store receiving from Source',
        'from_type': 'Source',
        'to_type': 'Store',
        'should_be_valid': True
    },
    {
        'name': 'store_from_transformer',
        'description': 'Store receiving from Transformer',
        'from_type': 'Transformer',
        'to_type': 'Store',
        'should_be_valid': True
    },
    {
        'name': 'store_from_controller',
        'description': 'Store receiving from Controller',
        'from_type': 'Controller',
        'to_type': 'Store',
        'should_be_valid': True
    },
    {
        'name': 'store_from_api',
        'description': 'Store receiving from APIEndpoint',
        'from_type': 'APIEndpoint',
        'to_type': 'Store',
        'should_be_valid': True
    },
    {
        'name': 'store_to_api',
        'description': 'Store connecting to APIEndpoint',
        'from_type': 'Store',
        'to_type': 'APIEndpoint',
        'should_be_valid': True
    },
    {
        'name': 'store_to_transformer',
        'description': 'Store connecting to Transformer (should be invalid)',
        'from_type': 'Store',
        'to_type': 'Transformer',
        'should_be_valid': False
    },
    {
        'name': 'store_to_source',
        'description': 'Store connecting to Source (anti-pattern)',
        'from_type': 'Store',
        'to_type': 'Source',
        'should_be_valid': False
    }
]

# Expected connectivity matrix for Store components
EXPECTED_STORE_CONNECTIVITY_MATRIX = {
    'Store': {
        'can_connect_to': ['APIEndpoint'],
        'can_receive_from': ['Source', 'Transformer', 'Controller', 'APIEndpoint'],
        'expected_inputs': 1,
        'expected_outputs': 0,
        'is_terminal': True,
        'is_source': False
    }
}

def get_store_blueprint_by_name(name: str) -> str:
    """Get a Store blueprint by name"""
    blueprint_map = {
        'basic': BASIC_STORE_BLUEPRINT,
        'pipeline': PIPELINE_STORE_BLUEPRINT,
        'multiple': MULTIPLE_STORES_BLUEPRINT,
        'api': API_STORE_BLUEPRINT,
        'anti_pattern': ANTI_PATTERN_STORE_BLUEPRINT,
        'isolated': ISOLATED_STORE_BLUEPRINT,
        'complex': COMPLEX_STORE_BLUEPRINT
    }
    return blueprint_map.get(name, BASIC_STORE_BLUEPRINT)

def get_store_test_configuration(name: str) -> Dict[str, Any]:
    """Get a Store test configuration by name"""
    for config in STORE_TEST_CONFIGURATIONS:
        if config['name'] == name:
            return config
    return STORE_TEST_CONFIGURATIONS[0]  # Return basic config as default

def get_all_store_blueprints() -> List[str]:
    """Get all Store component blueprints"""
    return [
        BASIC_STORE_BLUEPRINT,
        PIPELINE_STORE_BLUEPRINT,
        MULTIPLE_STORES_BLUEPRINT,
        API_STORE_BLUEPRINT,
        ANTI_PATTERN_STORE_BLUEPRINT,
        ISOLATED_STORE_BLUEPRINT,
        COMPLEX_STORE_BLUEPRINT
    ]

def get_valid_store_blueprints() -> List[str]:
    """Get only valid Store component blueprints (should pass validation)"""
    return [
        BASIC_STORE_BLUEPRINT,
        PIPELINE_STORE_BLUEPRINT,
        MULTIPLE_STORES_BLUEPRINT,
        API_STORE_BLUEPRINT,
        COMPLEX_STORE_BLUEPRINT
    ]

def get_invalid_store_blueprints() -> List[str]:
    """Get invalid Store component blueprints (should fail validation)"""
    return [
        ANTI_PATTERN_STORE_BLUEPRINT,
        ISOLATED_STORE_BLUEPRINT
    ]