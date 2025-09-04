"""
Test Fixtures Package
====================

Centralized test fixtures, blueprints, and mock data for AutoCoder4_CC testing.
"""

from .test_blueprints import (
    MINIMAL_BLUEPRINT,
    TODO_API_BLUEPRINT,
    USER_MANAGEMENT_BLUEPRINT,
    COMPLEX_MICROSERVICES_BLUEPRINT,
    INVALID_BLUEPRINTS,
    COMPONENT_CONFIGS,
    SYSTEM_CONFIGS,
    PERFORMANCE_TEST_CONFIGS,
    get_blueprint_by_name,
    get_invalid_blueprint_by_name,
    get_component_config_by_type,
    get_system_config_by_name,
    get_all_blueprint_names,
    get_all_invalid_blueprint_names,
    get_all_component_types,
    get_all_system_config_names,
    get_performance_test_config
)

__all__ = [
    "MINIMAL_BLUEPRINT",
    "TODO_API_BLUEPRINT", 
    "USER_MANAGEMENT_BLUEPRINT",
    "COMPLEX_MICROSERVICES_BLUEPRINT",
    "INVALID_BLUEPRINTS",
    "COMPONENT_CONFIGS",
    "SYSTEM_CONFIGS",
    "PERFORMANCE_TEST_CONFIGS",
    "get_blueprint_by_name",
    "get_invalid_blueprint_by_name",
    "get_component_config_by_type",
    "get_system_config_by_name",
    "get_all_blueprint_names",
    "get_all_invalid_blueprint_names",
    "get_all_component_types",
    "get_all_system_config_names",
    "get_performance_test_config"
]