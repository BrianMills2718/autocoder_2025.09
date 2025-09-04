#!/usr/bin/env python3
"""
Blueprint Structure Contract Definition and Enforcement.

This module defines THE authoritative blueprint structure contract that all
components MUST follow. Any deviation is a bug.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class BlueprintContract:
    """
    The authoritative blueprint structure contract.
    This is THE single source of truth.
    """
    
    # Required top-level keys
    REQUIRED_TOP_LEVEL_KEYS = ["system"]
    
    # Optional top-level keys
    OPTIONAL_TOP_LEVEL_KEYS = ["metadata", "schemas", "policy"]
    
    # Required system-level keys
    REQUIRED_SYSTEM_KEYS = ["components"]
    
    # Optional system-level keys
    OPTIONAL_SYSTEM_KEYS = ["name", "description", "version", "connections", "bindings", "configuration", "deployment", "validation"]
    
    # Component required fields
    REQUIRED_COMPONENT_FIELDS = ["name", "type"]
    
    # Component optional fields
    OPTIONAL_COMPONENT_FIELDS = ["description", "configuration", "config", "inputs", "outputs", "processing_mode", "dependencies", "implementation", "resources"]
    
    @classmethod
    def validate_structure(cls, blueprint: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a blueprint against the contract.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check top-level structure
        if "system" not in blueprint:
            errors.append("Missing required top-level key: 'system'")
            return False, errors
        
        # Check system structure
        system = blueprint["system"]
        if not isinstance(system, dict):
            errors.append("'system' must be a dictionary")
            return False, errors
        
        if "components" not in system:
            errors.append("Missing required system key: 'components'")
        
        # Check components structure
        if "components" in system:
            if not isinstance(system["components"], list):
                errors.append("'components' must be a list")
            else:
                for i, component in enumerate(system["components"]):
                    if not isinstance(component, dict):
                        errors.append(f"Component {i} must be a dictionary")
                        continue
                    
                    # Check required component fields
                    for field in cls.REQUIRED_COMPONENT_FIELDS:
                        if field not in component:
                            errors.append(f"Component {i} missing required field: '{field}'")
        
        # Check for connections OR bindings (at least one should exist for multi-component systems)
        if "components" in system and len(system["components"]) > 1:
            if "connections" not in system and "bindings" not in system:
                errors.append("Multi-component system should have 'connections' or 'bindings'")
        
        return len(errors) == 0, errors
    
    @classmethod
    def is_nested_structure(cls, blueprint: Dict[str, Any]) -> bool:
        """Check if blueprint uses nested structure (production format)"""
        return "system" in blueprint and "components" in blueprint.get("system", {})
    
    @classmethod
    def is_flat_structure(cls, blueprint: Dict[str, Any]) -> bool:
        """Check if blueprint uses flat structure (legacy format)"""
        return "components" in blueprint and "system" not in blueprint
    
    @classmethod
    def normalize_to_nested(cls, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert any blueprint to nested structure.
        This is the canonical transformation.
        """
        if cls.is_nested_structure(blueprint):
            return blueprint
        
        if cls.is_flat_structure(blueprint):
            # Convert flat to nested
            return {
                "system": {
                    "name": blueprint.get("name", "unnamed_system"),
                    "description": blueprint.get("description", ""),
                    "version": blueprint.get("version", "1.0.0"),
                    "components": blueprint.get("components", []),
                    "connections": blueprint.get("connections", []),
                    "bindings": blueprint.get("bindings", [])
                },
                "metadata": blueprint.get("metadata", {}),
                "schemas": blueprint.get("schemas", {}),
                "policy": blueprint.get("policy", {})
            }
        
        # Unknown structure - wrap it
        return {
            "system": blueprint,
            "metadata": {},
            "schemas": {},
            "policy": {}
        }
    
    @classmethod
    def get_components(cls, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get components from blueprint regardless of structure.
        This is the canonical way to access components.
        """
        if cls.is_nested_structure(blueprint):
            return blueprint["system"].get("components", [])
        elif cls.is_flat_structure(blueprint):
            return blueprint.get("components", [])
        return []
    
    @classmethod
    def get_connections(cls, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get connections/bindings from blueprint regardless of structure.
        This is the canonical way to access connections.
        """
        if cls.is_nested_structure(blueprint):
            system = blueprint["system"]
            # Prefer connections, fall back to bindings
            return system.get("connections", system.get("bindings", []))
        elif cls.is_flat_structure(blueprint):
            return blueprint.get("connections", blueprint.get("bindings", []))
        return []
    
    @classmethod
    def find_component(cls, blueprint: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
        """
        Find a component by name regardless of structure.
        This is the canonical way to find components.
        """
        components = cls.get_components(blueprint)
        for component in components:
            if component.get("name") == name:
                return component
        return None


class BlueprintTestFixture:
    """
    Generate test fixtures that comply with the contract.
    All test fixtures MUST be generated through this class.
    """
    
    @staticmethod
    def create_minimal() -> Dict[str, Any]:
        """Create minimal valid blueprint"""
        blueprint = {
            "system": {
                "components": []
            }
        }
        valid, errors = BlueprintContract.validate_structure(blueprint)
        assert valid, f"Minimal blueprint invalid: {errors}"
        return blueprint
    
    @staticmethod
    def create_single_component(name: str = "test_component", 
                               component_type: str = "Source") -> Dict[str, Any]:
        """Create blueprint with single component"""
        blueprint = {
            "system": {
                "components": [
                    {
                        "name": name,
                        "type": component_type,
                        "configuration": {}
                    }
                ]
            }
        }
        valid, errors = BlueprintContract.validate_structure(blueprint)
        assert valid, f"Single component blueprint invalid: {errors}"
        return blueprint
    
    @staticmethod
    def create_pipeline(num_components: int = 3) -> Dict[str, Any]:
        """Create pipeline blueprint with N components"""
        components = []
        connections = []
        
        for i in range(num_components):
            component_type = "Source" if i == 0 else "Sink" if i == num_components - 1 else "Transformer"
            components.append({
                "name": f"component_{i}",
                "type": component_type,
                "configuration": {}
            })
            
            if i > 0:
                connections.append({
                    "from": f"component_{i-1}.output",
                    "to": f"component_{i}.input"
                })
        
        blueprint = {
            "system": {
                "name": f"pipeline_with_{num_components}_components",
                "components": components,
                "connections": connections
            }
        }
        
        valid, errors = BlueprintContract.validate_structure(blueprint)
        assert valid, f"Pipeline blueprint invalid: {errors}"
        return blueprint
    
    @staticmethod
    def from_real_output(file_path: str) -> Dict[str, Any]:
        """
        Load and validate a blueprint from actual system output.
        This ensures our fixtures match reality.
        """
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                blueprint = json.load(f)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                import yaml
                blueprint = yaml.safe_load(f)
            else:
                raise ValueError(f"Unknown file type: {file_path}")
        
        # Normalize to nested structure
        blueprint = BlueprintContract.normalize_to_nested(blueprint)
        
        # Validate
        valid, errors = BlueprintContract.validate_structure(blueprint)
        if not valid:
            raise ValueError(f"Real output blueprint invalid: {errors}")
        
        return blueprint


def enforce_contract_in_test(test_func):
    """
    Decorator to enforce blueprint contract in tests.
    Any blueprint used in the test will be validated.
    """
    def wrapper(*args, **kwargs):
        # Intercept blueprint arguments
        for key, value in kwargs.items():
            if 'blueprint' in key.lower() and isinstance(value, dict):
                valid, errors = BlueprintContract.validate_structure(value)
                if not valid:
                    raise AssertionError(f"Test using invalid blueprint: {errors}")
        
        return test_func(*args, **kwargs)
    
    return wrapper


# Usage example for all tests:
"""
from tests.contracts.blueprint_structure_contract import (
    BlueprintContract,
    BlueprintTestFixture,
    enforce_contract_in_test
)

@enforce_contract_in_test
def test_my_component(blueprint=None):
    # Use contract-compliant fixtures
    if blueprint is None:
        blueprint = BlueprintTestFixture.create_pipeline()
    
    # Use contract methods to access data
    components = BlueprintContract.get_components(blueprint)
    connections = BlueprintContract.get_connections(blueprint)
    
    # Your test logic here
    assert len(components) > 0
"""