#!/usr/bin/env python3
"""
Configuration Requirement Specification
========================================

Defines the structure for component configuration requirements with support
for conditional dependencies, semantic types, and validation functions.

Philosophy: Every component must explicitly declare its configuration needs
to enable validation and self-healing at build time rather than runtime.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Callable
from enum import Enum


class ConfigType(str, Enum):
    """Semantic types for configuration values to guide LLM generation"""
    # Storage types
    STORAGE_URL = "storage_url"  # s3://, gs://, file://, hdfs://
    S3_BUCKET = "s3_bucket"
    FILE_PATH = "file_path"
    
    # Database types
    DATABASE_URL = "database_url"  # postgres://, mysql://, mongodb://
    POSTGRESQL_URL = "postgresql_url"
    MYSQL_URL = "mysql_url"
    MONGODB_URL = "mongodb_url"
    REDIS_URL = "redis_url"
    
    # Network types
    CONNECTION_URL = "connection_url"
    NETWORK_PORT = "network_port"
    KAFKA_BROKER = "kafka_broker"
    HTTP_ENDPOINT = "http_endpoint"
    WEBSOCKET_URL = "websocket_url"
    
    # Basic types
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    
    # Special types
    REGEX_PATTERN = "regex_pattern"
    CRON_EXPRESSION = "cron_expression"
    JSON_SCHEMA = "json_schema"


@dataclass
class ConfigRequirement:
    """
    Specification for a configuration field requirement.
    
    This dataclass defines what configuration a component needs,
    enabling validation at build time and LLM-based self-healing.
    """
    
    # Core fields
    name: str
    """The configuration field name (e.g., 'output_destination')"""
    
    type: str
    """Python type or ConfigType enum value"""
    
    description: str
    """Human-readable description for LLM understanding"""
    
    # Optional fields with defaults
    required: bool = True
    """Whether this field is required (can be conditional via depends_on)"""
    
    default: Optional[Any] = None
    """Default value if not required or for fallback"""
    
    validator: Optional[Callable[[Any], bool]] = None
    """Custom validation function returning True if valid"""
    
    example: Optional[str] = None
    """Example value to guide LLM generation"""
    
    semantic_type: Optional[str] = None
    """ConfigType value for semantic understanding"""
    
    # Dependency fields
    depends_on: Optional[Dict[str, Any]] = None
    """Conditional requirement: {field: value} that must be met"""
    
    conflicts_with: Optional[List[str]] = None
    """Fields that cannot coexist with this one"""
    
    requires: Optional[List[str]] = None
    """Other fields that must be present if this one is"""
    
    # Constraint fields
    options: Optional[List[Any]] = None
    """Valid options for enum-like fields"""
    
    min_value: Optional[float] = None
    """Minimum value for numeric fields"""
    
    max_value: Optional[float] = None
    """Maximum value for numeric fields"""
    
    pattern: Optional[str] = None
    """Regex pattern for string validation"""
    
    # Metadata
    environment_specific: bool = False
    """Whether this config varies by environment (dev/staging/prod)"""
    
    deployment_specific: bool = False
    """Whether this config varies by deployment (local/docker/k8s)"""
    
    sensitive: bool = False
    """Whether this contains sensitive data (passwords, keys, etc)"""
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this requirement.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check type
        if self.type in ["int", "integer"]:
            if not isinstance(value, int):
                return False, f"Expected integer, got {type(value).__name__}"
        elif self.type in ["str", "string"]:
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"
        elif self.type == "bool":
            if not isinstance(value, bool):
                return False, f"Expected boolean, got {type(value).__name__}"
        elif self.type == "list":
            if not isinstance(value, list):
                return False, f"Expected list, got {type(value).__name__}"
        elif self.type == "dict":
            if not isinstance(value, dict):
                return False, f"Expected dict, got {type(value).__name__}"
                
        # Check constraints
        if self.options and value not in self.options:
            return False, f"Value must be one of {self.options}"
            
        if self.min_value is not None and isinstance(value, (int, float)):
            if value < self.min_value:
                return False, f"Value must be >= {self.min_value}"
                
        if self.max_value is not None and isinstance(value, (int, float)):
            if value > self.max_value:
                return False, f"Value must be <= {self.max_value}"
                
        if self.pattern and isinstance(value, str):
            import re
            if not re.match(self.pattern, value):
                return False, f"Value must match pattern {self.pattern}"
                
        # Run custom validator
        if self.validator:
            try:
                if not self.validator(value):
                    return False, "Custom validation failed"
            except Exception as e:
                return False, f"Validation error: {e}"
                
        return True, None
    
    def is_required_for_config(self, config: Dict[str, Any]) -> bool:
        """
        Check if this requirement is needed given the current config.
        
        Takes into account conditional dependencies.
        """
        # If has depends_on, check if conditions are met
        if self.depends_on:
            conditions_met = True
            for field, expected in self.depends_on.items():
                actual = config.get(field)
                if isinstance(expected, list):
                    if actual not in expected:
                        conditions_met = False
                        break
                else:
                    if actual != expected:
                        conditions_met = False
                        break
            # If conditions are met, this field becomes required (even if normally optional)
            # If conditions not met, field is not required
            return conditions_met
            
        # No conditions, use base required flag
        return self.required
    
    def check_conflicts(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Check if this field conflicts with others in the config.
        
        Returns:
            Error message if conflict found, None otherwise
        """
        if self.conflicts_with and self.name in config:
            for conflict_field in self.conflicts_with:
                if conflict_field in config:
                    return f"{self.name} conflicts with {conflict_field}"
        return None
    
    def check_dependencies(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Check if required dependencies are present.
        
        Returns:
            Error message if dependencies missing, None otherwise
        """
        if self.requires and self.name in config:
            for required_field in self.requires:
                if required_field not in config:
                    return f"{self.name} requires {required_field} to also be set"
        return None
    
    def to_llm_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a prompt fragment for LLM to understand this requirement.
        
        Args:
            context: Optional context about environment, pipeline, etc.
            
        Returns:
            Prompt text describing this requirement
        """
        prompt = f"Field: {self.name}\n"
        prompt += f"Type: {self.semantic_type or self.type}\n"
        prompt += f"Description: {self.description}\n"
        
        if self.required:
            prompt += "Required: Yes\n"
        else:
            prompt += f"Required: No (default: {self.default})\n"
            
        if self.example:
            prompt += f"Example: {self.example}\n"
            
        if self.options:
            prompt += f"Valid options: {', '.join(str(o) for o in self.options)}\n"
            
        if self.min_value is not None or self.max_value is not None:
            prompt += f"Range: {self.min_value or 'any'} to {self.max_value or 'any'}\n"
            
        if self.pattern:
            prompt += f"Pattern: {self.pattern}\n"
            
        if context:
            if self.environment_specific and 'environment' in context:
                prompt += f"Environment: {context['environment']}\n"
            if self.deployment_specific and 'deployment' in context:
                prompt += f"Deployment: {context['deployment']}\n"
                
        return prompt


def validate_config_requirements(
    config: Dict[str, Any],
    requirements: List[ConfigRequirement]
) -> tuple[bool, List[str]]:
    """
    Validate a configuration against a list of requirements.
    
    Args:
        config: The configuration to validate
        requirements: List of ConfigRequirement objects
        
    Returns:
        Tuple of (all_valid, list_of_errors)
    """
    errors = []
    
    for req in requirements:
        # Check if required
        if req.is_required_for_config(config) and req.name not in config:
            errors.append(f"Missing required field: {req.name} - {req.description}")
            continue
            
        # If field is present, validate it
        if req.name in config:
            value = config[req.name]
            is_valid, error = req.validate(value)
            if not is_valid:
                errors.append(f"{req.name}: {error}")
                
            # Check conflicts
            conflict_error = req.check_conflicts(config)
            if conflict_error:
                errors.append(conflict_error)
                
            # Check dependencies
            dep_error = req.check_dependencies(config)
            if dep_error:
                errors.append(dep_error)
    
    return len(errors) == 0, errors


# Example usage for documentation
if __name__ == "__main__":
    # Example: DataSink requirements
    datasink_requirements = [
        ConfigRequirement(
            name="output_destination",
            type="str",
            semantic_type=ConfigType.STORAGE_URL,
            description="Where to write output data (S3, GCS, file path)",
            required=True,
            example="s3://my-bucket/output/",
            validator=lambda x: x.startswith(("s3://", "gs://", "file://", "hdfs://")),
            environment_specific=True
        ),
        ConfigRequirement(
            name="format",
            type="str",
            description="Output file format",
            required=True,
            default="json",
            options=["json", "parquet", "csv", "avro"]
        ),
        ConfigRequirement(
            name="schema",
            type="dict",
            semantic_type=ConfigType.JSON_SCHEMA,
            description="Schema definition for structured formats",
            required=False,
            depends_on={"format": ["parquet", "avro"]}
        ),
        ConfigRequirement(
            name="compression",
            type="str",
            description="Compression algorithm",
            required=False,
            options=["none", "gzip", "snappy", "lz4"],
            default="none"
        )
    ]
    
    # Test validation
    test_config = {
        "output_destination": "s3://my-data/results/",
        "format": "parquet"
        # Note: schema is missing but required when format=parquet
    }
    
    is_valid, errors = validate_config_requirements(test_config, datasink_requirements)
    
    if not is_valid:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")