#!/usr/bin/env python3
"""
Centralized Test Blueprints and Fixtures
=========================================

This module provides standardized test blueprints and component configurations
for use across all phase testing scenarios.
"""

from typing import Dict, Any, List

# Basic valid blueprints for testing
MINIMAL_BLUEPRINT = """schema_version: "1.0.0"
system:
  name: "minimal_test"
  description: "Minimal test system"
  components:
    - name: "simple_source"
      type: "Source"
      configuration:
        source_type: "static"
        data: {"message": "hello"}
      outputs:
        - name: "data"
          type: "dict"

    - name: "simple_sink"
      type: "Sink"
      configuration:
        sink_type: "console"
      inputs:
        - name: "data"
          type: "dict"

  bindings:
    - from: "simple_source.data"
      to: "simple_sink.data"
"""

TODO_API_BLUEPRINT = """schema_version: "1.0.0"
system:
  name: "todo_api"
  description: "Complete todo API system"

components:
  - name: "todo_api_endpoint"
    type: "APIEndpoint"
    configuration:
      port: 8000
      endpoints:
        - path: "/todos"
          method: "GET"
        - path: "/todos"
          method: "POST"
        - path: "/todos/{id}"
          method: "DELETE"
    inputs:
      - name: "service_response"
        type: "dict"
    outputs:
      - name: "service_request"
        type: "dict"

  - name: "todo_service_controller"
    type: "Controller"
    configuration:
      business_logic: "todo_management"
    inputs:
      - name: "service_request"
        type: "dict"
    outputs:
      - name: "store_command"
        type: "dict"
      - name: "service_response"
        type: "dict"

  - name: "todo_items_store"
    type: "Sink"
    configuration:
      storage_type: "postgresql"
      connection_string: "postgresql://postgres:password@localhost:5432/todo_db"
    inputs:
      - name: "item_data"
        type: "dict"

bindings:
  - source: "todo_api_endpoint.service_request"
    target: "todo_service_controller.service_request"
  - source: "todo_service_controller.store_command"
    target: "todo_items_store.item_data"
  - source: "todo_service_controller.service_response"
    target: "todo_api_endpoint.service_response"
"""

USER_MANAGEMENT_BLUEPRINT = """schema_version: "1.0.0"
system:
  name: "user_management_api"
  description: "User management system with authentication"

components:
  - name: "user_api_endpoint"
    type: "APIEndpoint"
    configuration:
      port: 8001
      authentication: true
      endpoints:
        - path: "/users"
          method: "GET"
        - path: "/users"
          method: "POST"
        - path: "/users/{id}"
          method: "PUT"
        - path: "/users/{id}"
          method: "DELETE"
        - path: "/auth/login"
          method: "POST"
    inputs:
      - name: "auth_response"
        type: "dict"
      - name: "user_response"
        type: "dict"
    outputs:
      - name: "auth_request"
        type: "dict"
      - name: "user_request"
        type: "dict"

  - name: "authentication_service"
    type: "Transformer"
    configuration:
      service_type: "jwt_authentication"
      jwt_secret: "test-secret-key"
    inputs:
      - name: "auth_request"
        type: "dict"
    outputs:
      - name: "auth_response"
        type: "dict"

  - name: "user_management_service"
    type: "Controller"
    configuration:
      business_logic: "user_crud"
    inputs:
      - name: "user_request"
        type: "dict"
    outputs:
      - name: "user_store_command"
        type: "dict"
      - name: "user_response"
        type: "dict"

  - name: "user_data_store"
    type: "Store"
    configuration:
      storage_type: "postgresql"
      connection_string: "postgresql://postgres:password@localhost:5432/users_db"
      table_name: "users"
    inputs:
      - name: "user_data"
        type: "dict"
    outputs:
      - name: "stored_user"
        type: "dict"

bindings:
  - source: "user_api_endpoint.auth_request"
    target: "authentication_service.auth_request"
  - source: "authentication_service.auth_response"
    target: "user_api_endpoint.auth_response"
  - source: "user_api_endpoint.user_request"
    target: "user_management_service.user_request"
  - source: "user_management_service.user_store_command"
    target: "user_data_store.user_data"
  - source: "user_management_service.user_response"
    target: "user_api_endpoint.user_response"
"""

COMPLEX_MICROSERVICES_BLUEPRINT = """schema_version: "1.0.0"
system:
  name: "complex_microservices"
  description: "Complex microservices architecture with multiple APIs"

components:
  - name: "api_gateway"
    type: "APIEndpoint"
    configuration:
      port: 8080
      gateway: true
      routes:
        - path: "/api/v1/orders/*"
          target: "orders_service"
        - path: "/api/v1/inventory/*"
          target: "inventory_service"
        - path: "/api/v1/users/*"
          target: "users_service"
    inputs:
      - name: "service_responses"
        type: "dict"
    outputs:
      - name: "service_requests"
        type: "dict"

  - name: "orders_service"
    type: "Controller"
    configuration:
      service_type: "orders_management"
      database: "orders_db"
    inputs:
      - name: "order_requests"
        type: "dict"
    outputs:
      - name: "order_events"
        type: "dict"
      - name: "order_responses"
        type: "dict"

  - name: "inventory_service"
    type: "Controller"
    configuration:
      service_type: "inventory_management"
      database: "inventory_db"
    inputs:
      - name: "inventory_requests"
        type: "dict"
      - name: "order_events"
        type: "dict"
    outputs:
      - name: "inventory_updates"
        type: "dict"
      - name: "inventory_responses"
        type: "dict"

  - name: "users_service"
    type: "Controller"
    configuration:
      service_type: "user_management"
      database: "users_db"
    inputs:
      - name: "user_requests"
        type: "dict"
    outputs:
      - name: "user_responses"
        type: "dict"

  - name: "event_bus"
    type: "Transformer"
    configuration:
      bus_type: "kafka"
      topics: ["orders", "inventory", "users"]
    inputs:
      - name: "events"
        type: "dict"
    outputs:
      - name: "distributed_events"
        type: "dict"

  - name: "orders_database"
    type: "Store"
    configuration:
      storage_type: "postgresql"
      connection_string: "postgresql://postgres:password@localhost:5432/orders_db"
    inputs:
      - name: "order_data"
        type: "dict"

  - name: "inventory_database"
    type: "Store"
    configuration:
      storage_type: "postgresql"
      connection_string: "postgresql://postgres:password@localhost:5432/inventory_db"
    inputs:
      - name: "inventory_data"
        type: "dict"

bindings:
  - source: "api_gateway.service_requests"
    target: "orders_service.order_requests"
  - source: "api_gateway.service_requests"
    target: "inventory_service.inventory_requests"
  - source: "api_gateway.service_requests"
    target: "users_service.user_requests"
  - source: "orders_service.order_events"
    target: "event_bus.events"
  - source: "orders_service.order_events"
    target: "inventory_service.order_events"
  - source: "orders_service.order_responses"
    target: "api_gateway.service_responses"
  - source: "inventory_service.inventory_responses"
    target: "api_gateway.service_responses"
  - source: "users_service.user_responses"
    target: "api_gateway.service_responses"
"""

# Invalid blueprints for error testing
INVALID_BLUEPRINTS = {
    "malformed_yaml": """schema_version: "1.0.0"
system:
  name: "test"
  invalid_yaml: [unclosed bracket
components: []
""",
    
    "missing_system_section": """schema_version: "1.0.0"
components:
  - name: "test_component"
    type: "Source"
    configuration: {}
""",
    
    "missing_component_type": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "test_component"
    configuration: {}
""",
    
    "invalid_component_type": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "invalid_component"
    type: "NonExistentComponentType"
    configuration: {}
""",
    
    "circular_binding": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "comp1"
    type: "Transformer"
    inputs:
      - name: "input"
        type: "dict"
    outputs:
      - name: "output"
        type: "dict"
  - name: "comp2"
    type: "Transformer"
    inputs:
      - name: "input"
        type: "dict"
    outputs:
      - name: "output"
        type: "dict"
bindings:
  - source: "comp1.output"
    target: "comp2.input"
  - source: "comp2.output"
    target: "comp1.input"
""",
    
    "orphaned_component": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "connected_comp"
    type: "Source"
    outputs:
      - name: "output"
        type: "dict"
  - name: "orphaned_comp"
    type: "Transformer"
    inputs:
      - name: "input"
        type: "dict"
    outputs:
      - name: "output"
        type: "dict"
  - name: "sink_comp"
    type: "Sink"
    inputs:
      - name: "input"
        type: "dict"
bindings:
  - source: "connected_comp.output"
    target: "sink_comp.input"
""",
    
    "missing_binding_source": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "source_comp"
    type: "Source"
    outputs:
      - name: "output"
        type: "dict"
  - name: "sink_comp"
    type: "Sink"
    inputs:
      - name: "input"
        type: "dict"
bindings:
  - source: "nonexistent_comp.output"
    target: "sink_comp.input"
""",
    
    "type_mismatch_binding": """schema_version: "1.0.0"
system:
  name: "test"
  description: "Test"
components:
  - name: "source_comp"
    type: "Source"
    outputs:
      - name: "output"
        type: "string"
  - name: "sink_comp"
    type: "Sink"
    inputs:
      - name: "input"
        type: "integer"
bindings:
  - source: "source_comp.output"
    target: "sink_comp.input"
"""
}

# Component configurations for testing
COMPONENT_CONFIGS = {
    "api_endpoint": {
        "name": "test_api",
        "type": "APIEndpoint",
        "configuration": {
            "port": 8000,
            "endpoints": [
                {"path": "/health", "method": "GET"},
                {"path": "/data", "method": "POST"}
            ]
        },
        "inputs": [{"name": "response_data", "type": "dict"}],
        "outputs": [{"name": "request_data", "type": "dict"}]
    },
    
    "controller": {
        "name": "test_controller",
        "type": "Controller",
        "configuration": {
            "business_logic": "data_processing"
        },
        "inputs": [{"name": "input_data", "type": "dict"}],
        "outputs": [{"name": "processed_data", "type": "dict"}]
    },
    
    "store": {
        "name": "test_store",
        "type": "Store",
        "configuration": {
            "storage_type": "postgresql",
            "connection_string": "postgresql://test:test@localhost:5432/testdb"
        },
        "inputs": [{"name": "data_to_store", "type": "dict"}],
        "outputs": [{"name": "stored_data", "type": "dict"}]
    },
    
    "sink": {
        "name": "test_sink",
        "type": "Sink",
        "configuration": {
            "sink_type": "console"
        },
        "inputs": [{"name": "data_to_output", "type": "dict"}]
    },
    
    "source": {
        "name": "test_source",
        "type": "Source",
        "configuration": {
            "source_type": "static",
            "data": {"test": "data"}
        },
        "outputs": [{"name": "source_data", "type": "dict"}]
    },
    
    "transformer": {
        "name": "test_transformer",
        "type": "Transformer",
        "configuration": {
            "transformation_type": "data_mapping"
        },
        "inputs": [{"name": "input_data", "type": "dict"}],
        "outputs": [{"name": "transformed_data", "type": "dict"}]
    }
}

# System configurations for different testing scenarios
SYSTEM_CONFIGS = {
    "minimal": {
        "name": "minimal_test_system",
        "description": "Minimal system for basic testing",
        "components": ["source", "sink"],
        "expected_files": [
            "main.py",
            "components/__init__.py",
            "components/test_source.py",
            "components/test_sink.py"
        ]
    },
    
    "todo_api": {
        "name": "todo_api_system",
        "description": "Todo API system for comprehensive testing",
        "components": ["api_endpoint", "controller", "store"],
        "expected_files": [
            "main.py",
            "components/__init__.py",
            "components/todo_api_endpoint.py",
            "components/todo_service_controller.py",
            "components/todo_items_store.py"
        ]
    },
    
    "complex": {
        "name": "complex_microservices_system",
        "description": "Complex microservices for stress testing",
        "components": ["api_endpoint", "controller", "transformer", "store"],
        "expected_files": [
            "main.py",
            "components/__init__.py",
            "components/api_gateway.py",
            "components/orders_service.py",
            "components/inventory_service.py",
            "components/users_service.py",
            "components/event_bus.py",
            "components/orders_database.py",
            "components/inventory_database.py"
        ]
    }
}

def get_blueprint_by_name(name: str) -> str:
    """Get a blueprint by name"""
    blueprints = {
        "minimal": MINIMAL_BLUEPRINT,
        "todo_api": TODO_API_BLUEPRINT,
        "user_management": USER_MANAGEMENT_BLUEPRINT,
        "complex": COMPLEX_MICROSERVICES_BLUEPRINT
    }
    
    if name not in blueprints:
        raise ValueError(f"Unknown blueprint: {name}. Available: {list(blueprints.keys())}")
    
    return blueprints[name]

def get_invalid_blueprint_by_name(name: str) -> str:
    """Get an invalid blueprint by name for error testing"""
    if name not in INVALID_BLUEPRINTS:
        raise ValueError(f"Unknown invalid blueprint: {name}. Available: {list(INVALID_BLUEPRINTS.keys())}")
    
    return INVALID_BLUEPRINTS[name]

def get_component_config_by_type(component_type: str) -> Dict[str, Any]:
    """Get a component configuration by type"""
    type_mapping = {
        "APIEndpoint": "api_endpoint",
        "Controller": "controller", 
        "Store": "store",
        "Sink": "sink",
        "Source": "source",
        "Transformer": "transformer"
    }
    
    config_key = type_mapping.get(component_type, component_type.lower())
    
    if config_key not in COMPONENT_CONFIGS:
        raise ValueError(f"Unknown component type: {component_type}. Available: {list(type_mapping.keys())}")
    
    return COMPONENT_CONFIGS[config_key].copy()

def get_system_config_by_name(name: str) -> Dict[str, Any]:
    """Get a system configuration by name"""
    if name not in SYSTEM_CONFIGS:
        raise ValueError(f"Unknown system config: {name}. Available: {list(SYSTEM_CONFIGS.keys())}")
    
    return SYSTEM_CONFIGS[name].copy()

def get_all_blueprint_names() -> List[str]:
    """Get all available blueprint names"""
    return ["minimal", "todo_api", "user_management", "complex"]

def get_all_invalid_blueprint_names() -> List[str]:
    """Get all available invalid blueprint names"""
    return list(INVALID_BLUEPRINTS.keys())

def get_all_component_types() -> List[str]:
    """Get all available component types"""
    return ["APIEndpoint", "Controller", "Store", "Sink", "Source", "Transformer"]

def get_all_system_config_names() -> List[str]:
    """Get all available system config names"""
    return list(SYSTEM_CONFIGS.keys())

# Performance testing configurations
PERFORMANCE_TEST_CONFIGS = {
    "small": {
        "components": 3,
        "bindings": 2,
        "max_generation_time": 30,
        "blueprint_name": "minimal"
    },
    
    "medium": {
        "components": 5,
        "bindings": 4,
        "max_generation_time": 60,
        "blueprint_name": "todo_api"
    },
    
    "large": {
        "components": 10,
        "bindings": 12,
        "max_generation_time": 120,
        "blueprint_name": "complex"
    }
}

def get_performance_test_config(size: str) -> Dict[str, Any]:
    """Get performance test configuration by size"""
    if size not in PERFORMANCE_TEST_CONFIGS:
        raise ValueError(f"Unknown performance test size: {size}. Available: {list(PERFORMANCE_TEST_CONFIGS.keys())}")
    
    return PERFORMANCE_TEST_CONFIGS[size].copy()