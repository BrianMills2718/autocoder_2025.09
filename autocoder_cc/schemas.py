"""
Autocoder Schema System
Implements schema validation, evolution, and type checking for Autocoder 5.2+ components.

Schema Mapping Between Blueprint and Runtime
===========================================

This module defines the runtime schema validation system that works in conjunction
with the blueprint YAML schema definitions. The mapping between blueprint schemas
and runtime schemas ensures consistency across the entire generation and execution pipeline.

Blueprint Schema (YAML) -> Runtime Schema (Python) Mapping:
----------------------------------------------------------

1. **Component Port Schemas**:
   Blueprint: component.inputs[].schema and component.outputs[].schema reference strings
   Runtime: Corresponding BaseSchema subclasses validate actual data flow
   
   Example:
   ```yaml
   # In blueprint
   inputs:
     - name: transaction_data
       schema: FraudDetectionSchema
   ```
   ```python
   # At runtime
   schema_registry.validate_data("FraudDetectionSchema", transaction_data)
   ```

2. **Common Schema Definitions**:
   Blueprint: schemas section defines reusable schema objects
   Runtime: BaseSchema implementations provide validation logic
   
   Example:
   ```yaml
   # In blueprint
   schemas:
     CustomDataSchema:
       type: object
       properties:
         id: {type: string}
         value: {type: number}
   ```
   ```python
   # Runtime equivalent
   class CustomDataSchema(BaseSchema):
       def get_fields(self) -> Dict[str, Type]:
           return {"id": str, "value": float}
   ```

3. **Component Type Constraints**:
   Blueprint: component.properties[] and component.contracts[] define validation rules
   Runtime: Schema validation enforces these rules during data processing
   
4. **System-Level Schemas**:
   Blueprint: System configuration and resource definitions
   Runtime: Harness and orchestration validation schemas

Key Components:
--------------

- **BaseSchema**: Abstract base for all runtime schemas
- **SchemaRegistry**: Central registry mapping schema names to implementations  
- **SchemaMapper**: Utility class for blueprint-to-runtime schema conversion
- **ValidationError**: Detailed error reporting with field paths

Usage Patterns:
--------------

1. **Component Data Validation**:
   Components receive data through streams and validate against registered schemas
   
2. **Inter-Component Communication**:
   Stream data is validated at send/receive boundaries using schema references
   
3. **Configuration Validation**:
   Component and system configuration validated against defined schemas

4. **Error Handling**:
   Schema validation failures include detailed field paths and expected vs actual values

This ensures that blueprint-time schema definitions are enforced at runtime,
providing end-to-end type safety and data integrity across the entire system.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Callable
from datetime import datetime
from enum import Enum


class ValidationError(Exception):
    """Raised when schema validation fails"""
    def __init__(self, message: str, field_path: str = "", expected: Any = None, actual: Any = None):
        self.message = message
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        super().__init__(f"{field_path}: {message}")


class SchemaVersion(Enum):
    """Schema version compatibility levels"""
    V1_0 = "1.0"
    V1_1 = "1.1" 
    V2_0 = "2.0"


class CompatibilityLevel(Enum):
    """Schema compatibility levels"""
    FORWARD = "forward"      # New schema can read old data
    BACKWARD = "backward"    # Old schema can read new data  
    BOTH = "both"           # Full bidirectional compatibility
    NONE = "none"           # Breaking change


@dataclass
class SchemaMigration:
    """Schema migration definition"""
    from_version: str
    to_version: str
    transform: Callable[[Dict[str, Any]], Dict[str, Any]]
    description: str


class BaseSchema(ABC):
    """Base class for all Autocoder schemas"""
    
    def __init__(self, version: str = "1.0", compatibility: CompatibilityLevel = CompatibilityLevel.BOTH):
        self.version = version
        self.compatibility = compatibility
        self.migrations: List[SchemaMigration] = []
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data against this schema"""
        pass
    
    @abstractmethod
    def get_fields(self) -> Dict[str, Type]:
        """Get field definitions for this schema"""
        pass
    
    def migrate(self, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate data between schema versions"""
        for migration in self.migrations:
            if migration.from_version == from_version and migration.to_version == to_version:
                return migration.transform(data)
        raise ValidationError(f"No migration path from {from_version} to {to_version}")
    
    def validate_with_path(self, data: Any, field_path: str = "") -> None:
        """Validate with detailed field path for error reporting"""
        if not self.validate(data):
            raise ValidationError(f"Schema validation failed", field_path, self, data)


class SchemaRef:
    """Reference to a schema with optional constraints"""
    
    def __init__(self, schema_type: Type[BaseSchema], constraints: Optional[Dict[str, Any]] = None):
        self.schema_type = schema_type
        self.constraints = constraints or {}
    
    def validate(self, data: Any) -> bool:
        """Validate data against referenced schema"""
        schema = self.schema_type()
        return schema.validate(data)


class ErrorSchema(BaseSchema):
    """Standard error schema for all components"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "error_code": str,
            "message": str,
            "timestamp": str,
            "component": str,
            "details": dict,
            "retry_after": Optional[int]
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        
        required_fields = ["error_code", "message", "timestamp", "component"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate timestamp format
        try:
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
            
        return True


class ItemSchema(BaseSchema):
    """Schema for individual items in accumulator input"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "id": str,
            "timestamp": str,
            "value": Union[int, float, str],
            "metadata": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["id", "timestamp", "value"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate timestamp
        try:
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
            
        return True


class AggregateSchema(BaseSchema):
    """Schema for accumulator aggregate output"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "aggregate_value": Union[int, float],
            "count": int,
            "timestamp": str,
            "window_start": Optional[str],
            "window_end": Optional[str],
            "metadata": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["aggregate_value", "count", "timestamp"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate count is non-negative
        if not isinstance(data["count"], int) or data["count"] < 0:
            return False
            
        return True


class EventSchema(BaseSchema):
    """Schema for event sourcing events"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "event_id": str,
            "event_type": str,
            "timestamp": str,
            "aggregate_id": str,
            "version": int,
            "data": dict,
            "metadata": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["event_id", "event_type", "timestamp", "aggregate_id", "version", "data"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate version is positive
        if not isinstance(data["version"], int) or data["version"] <= 0:
            return False
            
        return True


class SignalSchema(BaseSchema):
    """Schema for control signals"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "signal_type": str,
            "timestamp": str,
            "source": str,
            "target": Optional[str],
            "payload": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["signal_type", "timestamp", "source"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate signal_type
        valid_signals = ["reset", "pause", "resume", "shutdown", "configure"]
        if data["signal_type"] not in valid_signals:
            return False
            
        return True


class ComponentLinkSchema(BaseSchema):
    """Schema for component links and references"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "component_name": str,
            "component_type": str,
            "port_name": str,
            "connection_type": str,
            "metadata": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["component_name", "component_type", "port_name"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate component_type
        valid_types = ["Source", "Transformer", "Accumulator", "Store", "Controller", 
                      "Sink", "StreamProcessor", "Model", "APIEndpoint", "Router"]
        if data["component_type"] not in valid_types:
            return False
            
        return True


class APIRequestSchema(BaseSchema):
    """Schema for API requests"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "method": str,
            "path": str,
            "headers": dict,
            "body": Optional[dict],
            "query_params": dict,
            "timestamp": str
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["method", "path", "headers", "timestamp"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate HTTP method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if data["method"] not in valid_methods:
            return False
            
        return True


class APIResponseSchema(BaseSchema):
    """Schema for API responses"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "status": int,
            "headers": dict,
            "body": Optional[dict],
            "timestamp": str,
            "processing_time_ms": float
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["status", "headers", "timestamp"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate HTTP status code
        if not isinstance(data["status"], int) or data["status"] < 100 or data["status"] >= 600:
            return False
            
        return True


class FraudDetectionSchema(BaseSchema):
    """Domain-specific schema for fraud detection data"""
    
    def get_fields(self) -> Dict[str, Type]:
        return {
            "transaction_id": str,
            "user_id": str,
            "amount": float,
            "currency": str,
            "timestamp": str,
            "merchant_id": str,
            "fraud_score": Optional[float],
            "risk_level": Optional[str],
            "features": dict
        }
    
    def validate(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
            
        required_fields = ["transaction_id", "user_id", "amount", "timestamp"]
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate amount is positive
        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            return False
            
        # Validate fraud_score if present
        if "fraud_score" in data and data["fraud_score"] is not None:
            if not isinstance(data["fraud_score"], (int, float)) or not (0 <= data["fraud_score"] <= 1):
                return False
                
        # Validate risk_level if present
        if "risk_level" in data and data["risk_level"] is not None:
            valid_levels = ["low", "medium", "high", "critical"]
            if data["risk_level"] not in valid_levels:
                return False
                
        return True


class SchemaMapper:
    """
    Utility class for mapping between blueprint YAML schema definitions and runtime BaseSchema classes.
    
    This class bridges the gap between compile-time blueprint validation and runtime data validation,
    ensuring consistency across the entire system generation and execution pipeline.
    """
    
    @staticmethod
    def blueprint_to_runtime_schema(blueprint_schema: Dict[str, Any], schema_name: str) -> Type[BaseSchema]:
        """
        Convert a blueprint schema definition to a runtime BaseSchema class.
        
        Args:
            blueprint_schema: Schema definition from blueprint YAML
            schema_name: Name for the generated schema class
            
        Returns:
            Dynamically generated BaseSchema subclass
            
        Example:
            blueprint_def = {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "value": {"type": "number"},
                    "required": True
                },
                "required": ["id", "value"]
            }
            
            schema_class = SchemaMapper.blueprint_to_runtime_schema(blueprint_def, "MySchema")
            schema = schema_class()
            is_valid = schema.validate({"id": "test", "value": 42.0})
        """
        
        def get_python_type(yaml_type: str) -> Type:
            """Map YAML schema types to Python types"""
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
                "object": dict,
                "array": list
            }
            return type_mapping.get(yaml_type, str)
        
        def extract_fields(properties: Dict[str, Any]) -> Dict[str, Type]:
            """Extract field definitions from blueprint properties"""
            fields = {}
            for field_name, field_def in properties.items():
                if isinstance(field_def, dict) and "type" in field_def:
                    python_type = get_python_type(field_def["type"])
                    # Handle optional fields
                    if field_name not in blueprint_schema.get("required", []):
                        from typing import Optional
                        python_type = Optional[python_type]
                    fields[field_name] = python_type
                else:
                    fields[field_name] = str  # Default to string for complex types
            return fields
        
        def create_validation_method(schema_def: Dict[str, Any]):
            """Create validation method based on schema definition"""
            def validate(self, data: Any) -> bool:
                if not isinstance(data, dict):
                    return False
                
                # Check required fields
                required_fields = schema_def.get("required", [])
                for field in required_fields:
                    if field not in data:
                        return False
                
                # Validate field types
                properties = schema_def.get("properties", {})
                for field_name, field_def in properties.items():
                    if field_name in data:
                        value = data[field_name]
                        expected_type = get_python_type(field_def.get("type", "string"))
                        
                        # Type checking
                        if not isinstance(value, expected_type):
                            # Allow number/integer flexibility
                            if expected_type in (int, float) and isinstance(value, (int, float)):
                                continue
                            return False
                        
                        # Additional constraints
                        if "minimum" in field_def and isinstance(value, (int, float)):
                            if value < field_def["minimum"]:
                                return False
                        
                        if "maximum" in field_def and isinstance(value, (int, float)):
                            if value > field_def["maximum"]:
                                return False
                        
                        if "pattern" in field_def and isinstance(value, str):
                            import re
                            if not re.match(field_def["pattern"], value):
                                return False
                
                return True
            
            return validate
        
        def create_get_fields_method(schema_def: Dict[str, Any]):
            """Create get_fields method based on schema definition"""
            def get_fields(self) -> Dict[str, Type]:
                properties = schema_def.get("properties", {})
                return extract_fields(properties)
            
            return get_fields
        
        # Create dynamic class
        class_attrs = {
            'validate': create_validation_method(blueprint_schema),
            'get_fields': create_get_fields_method(blueprint_schema),
            '_blueprint_schema': blueprint_schema,
            '_schema_name': schema_name
        }
        
        # Create the dynamic class
        dynamic_class = type(schema_name, (BaseSchema,), class_attrs)
        
        return dynamic_class
    
    @staticmethod
    def validate_schema_consistency(blueprint_schema: Dict[str, Any], runtime_schema: BaseSchema) -> List[str]:
        """
        Validate that a runtime schema is consistent with its blueprint definition.
        
        Returns:
            List of consistency errors (empty if consistent)
        """
        errors = []
        
        try:
            # Get runtime fields
            runtime_fields = runtime_schema.get_fields()
            
            # Get blueprint properties
            blueprint_properties = blueprint_schema.get("properties", {})
            blueprint_required = set(blueprint_schema.get("required", []))
            
            # Check for missing fields in runtime
            for bp_field in blueprint_properties:
                if bp_field not in runtime_fields:
                    errors.append(f"Runtime schema missing field '{bp_field}' defined in blueprint")
            
            # Check for extra fields in runtime
            for rt_field in runtime_fields:
                if rt_field not in blueprint_properties:
                    errors.append(f"Runtime schema has extra field '{rt_field}' not in blueprint")
            
            # Check required fields
            for required_field in blueprint_required:
                if required_field in runtime_fields:
                    # Check if field is properly marked as required (not Optional)
                    field_type = runtime_fields[required_field]
                    # This is a simplified check - in practice, you'd need more sophisticated Optional detection
                    if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                        if type(None) in field_type.__args__:
                            errors.append(f"Required field '{required_field}' is marked as Optional in runtime schema")
        
        except Exception as e:
            errors.append(f"Error validating schema consistency: {e}")
        
        return errors
    
    @staticmethod
    def generate_blueprint_from_runtime(runtime_schema: BaseSchema, schema_name: str) -> Dict[str, Any]:
        """
        Generate a blueprint schema definition from a runtime BaseSchema.
        
        This is useful for reverse-engineering existing schemas or ensuring consistency.
        """
        fields = runtime_schema.get_fields()
        
        properties = {}
        required = []
        
        for field_name, field_type in fields.items():
            # Handle Optional types
            is_optional = False
            actual_type = field_type
            
            if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                if type(None) in field_type.__args__:
                    is_optional = True
                    # Get the non-None type
                    actual_type = next(arg for arg in field_type.__args__ if arg is not type(None))
            
            # Map Python types to YAML schema types
            type_mapping = {
                str: "string",
                int: "integer", 
                float: "number",
                bool: "boolean",
                dict: "object",
                list: "array"
            }
            
            yaml_type = "string"  # default
            for py_type, yaml_name in type_mapping.items():
                if actual_type is py_type:
                    yaml_type = yaml_name
                    break
            
            properties[field_name] = {"type": yaml_type}
            
            if not is_optional:
                required.append(field_name)
        
        blueprint_schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            blueprint_schema["required"] = required
        
        return blueprint_schema


class SchemaRegistry:
    """Registry for managing schemas and their relationships"""
    
    def __init__(self):
        self.schemas: Dict[str, Type[BaseSchema]] = {}
        self.blueprint_mappings: Dict[str, Dict[str, Any]] = {}
        self.register_default_schemas()
    
    def register_default_schemas(self):
        """Register all default schemas"""
        self.schemas.update({
            "ErrorSchema": ErrorSchema,
            "ItemSchema": ItemSchema,
            "AggregateSchema": AggregateSchema,
            "EventSchema": EventSchema,
            "SignalSchema": SignalSchema,
            "ComponentLinkSchema": ComponentLinkSchema,
            "APIRequestSchema": APIRequestSchema,
            "APIResponseSchema": APIResponseSchema,
            "FraudDetectionSchema": FraudDetectionSchema
        })
    
    def register(self, name: str, schema_class: Type[BaseSchema]):
        """Register a new schema"""
        self.schemas[name] = schema_class
    
    def register_from_blueprint(self, name: str, blueprint_schema: Dict[str, Any]):
        """Register a schema from blueprint definition"""
        schema_class = SchemaMapper.blueprint_to_runtime_schema(blueprint_schema, name)
        self.schemas[name] = schema_class
        self.blueprint_mappings[name] = blueprint_schema
    
    def get(self, name: str) -> Type[BaseSchema]:
        """Get a schema by name"""
        if name not in self.schemas:
            raise ValidationError(f"Schema '{name}' not found in registry")
        return self.schemas[name]
    
    def get_blueprint_mapping(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the blueprint definition for a schema"""
        return self.blueprint_mappings.get(name)
    
    def validate_data(self, schema_name: str, data: Any) -> bool:
        """Validate data against a named schema"""
        schema_class = self.get(schema_name)
        schema = schema_class()
        return schema.validate(data)
    
    def validate_consistency(self) -> Dict[str, List[str]]:
        """
        Validate consistency between all registered schemas and their blueprint mappings.
        
        Returns:
            Dictionary mapping schema names to lists of consistency errors
        """
        consistency_errors = {}
        
        for schema_name in self.schemas:
            if schema_name in self.blueprint_mappings:
                schema_class = self.schemas[schema_name]
                blueprint_def = self.blueprint_mappings[schema_name]
                schema_instance = schema_class()
                
                errors = SchemaMapper.validate_schema_consistency(blueprint_def, schema_instance)
                if errors:
                    consistency_errors[schema_name] = errors
        
        return consistency_errors


# Global schema registry instance
schema_registry = SchemaRegistry()


def validate_against_schema(data: Any, schema_name: str) -> None:
    """Convenience function to validate data against a named schema"""
    if not schema_registry.validate_data(schema_name, data):
        raise ValidationError(f"Data validation failed against schema '{schema_name}'")


def create_schema_ref(schema_name: str, constraints: Optional[Dict[str, Any]] = None) -> SchemaRef:
    """Create a schema reference by name"""
    schema_class = schema_registry.get(schema_name)
    return SchemaRef(schema_class, constraints)