#!/usr/bin/env python3
"""
Schema Validator Capability
===========================

Provides schema validation functionality for components.
Used by ComposedComponent via composition.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError
import logging
from autocoder_cc.observability.structured_logging import get_logger


class SchemaValidator:
    """Validates data against Pydantic schemas"""
    
    def __init__(self, schemas: Dict[str, BaseModel] = None, strict_mode: bool = True):
        self.schemas = schemas or {}
        self.strict_mode = strict_mode
        
        # Statistics
        self.validation_count = 0
        self.validation_errors = 0
        self.error_details = []
        
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def register_schema(self, name: str, schema: BaseModel):
        """Register a schema for validation"""
        self.schemas[name] = schema
    
    def validate(self, data: Dict[str, Any], schema_name: str = None) -> bool:
        """Validate data against registered schema"""
        self.validation_count += 1
        
        if not schema_name:
            # If no schema specified, just check if data is valid dict
            if isinstance(data, dict):
                return True
            else:
                self.validation_errors += 1
                return False
        
        if schema_name not in self.schemas:
            if self.strict_mode:
                self.validation_errors += 1
                error_msg = f"Schema '{schema_name}' not found"
                self.error_details.append(error_msg)
                self.logger.error(error_msg)
                return False
            else:
                # In non-strict mode, pass through if schema not found
                return True
        
        try:
            schema_class = self.schemas[schema_name]
            validated_data = schema_class(**data)
            return True
            
        except ValidationError as e:
            self.validation_errors += 1
            error_msg = f"Validation failed for schema '{schema_name}': {e}"
            self.error_details.append(error_msg)
            
            if self.strict_mode:
                self.logger.error(error_msg)
                return False
            else:
                self.logger.warning(error_msg)
                return True
        
        except Exception as e:
            self.validation_errors += 1
            error_msg = f"Unexpected validation error for schema '{schema_name}': {e}"
            self.error_details.append(error_msg)
            self.logger.error(error_msg)
            return False
    
    def validate_and_parse(self, data: Dict[str, Any], schema_name: str) -> Optional[BaseModel]:
        """Validate data and return parsed model instance"""
        if schema_name not in self.schemas:
            if self.strict_mode:
                raise ValueError(f"Schema '{schema_name}' not found")
            return None
        
        try:
            schema_class = self.schemas[schema_name]
            return schema_class(**data)
        except ValidationError as e:
            if self.strict_mode:
                raise e
            else:
                self.logger.warning(f"Validation failed for schema '{schema_name}': {e}")
                return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get schema validator status"""
        return {
            'registered_schemas': list(self.schemas.keys()),
            'schema_count': len(self.schemas),
            'validation_count': self.validation_count,
            'validation_errors': self.validation_errors,
            'error_rate': self.validation_errors / self.validation_count if self.validation_count > 0 else 0,
            'strict_mode': self.strict_mode,
            'recent_errors': self.error_details[-10:]  # Last 10 errors
        }
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_count = 0
        self.validation_errors = 0
        self.error_details.clear()
    
    def reconfigure(self, config: Dict[str, Any]):
        """Reconfigure schema validator"""
        self.strict_mode = config.get('strict_mode', self.strict_mode)
        
        # Add new schemas if provided
        if 'schemas' in config:
            self.schemas.update(config['schemas'])