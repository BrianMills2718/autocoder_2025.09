"""
Schema Validator
JSON Schema validation for architecture and deployment blueprints
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..core.exceptions import ValidationError


class ValidationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SchemaValidationError:
    """Schema validation error with context"""
    level: ValidationLevel
    message: str
    path: str
    schema_path: Optional[str] = None
    value: Any = None
    component: str = "SchemaValidator"


class SchemaValidator:
    """JSON Schema validator for blueprint files"""
    
    def __init__(self, schema_dir: Optional[Path] = None):
        self.schema_dir = schema_dir or Path(__file__).parent.parent.parent / "schemas"
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.validation_errors: List[SchemaValidationError] = []
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all JSON schemas from schema directory"""
        if not self.schema_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {self.schema_dir}")
        
        schema_files = [
            "architecture.schema.json",
            "deployment.schema.json"
        ]
        
        for schema_file in schema_files:
            schema_path = self.schema_dir / schema_file
            if schema_path.exists():
                try:
                    with open(schema_path, 'r') as f:
                        schema_data = json.load(f)
                    
                    # Validate the schema itself
                    jsonschema.Draft7Validator.check_schema(schema_data)
                    
                    # Store schema
                    schema_name = schema_file.replace('.schema.json', '')
                    self.schemas[schema_name] = schema_data
                    
                except Exception as e:
                    self.validation_errors.append(SchemaValidationError(
                        level=ValidationLevel.ERROR,
                        message=f"Failed to load schema {schema_file}: {str(e)}",
                        path=str(schema_path)
                    ))
    
    def validate_architecture_blueprint(self, blueprint_data: Dict[str, Any]) -> List[SchemaValidationError]:
        """Validate architecture blueprint against schema"""
        return self._validate_blueprint(blueprint_data, "architecture")
    
    def validate_deployment_blueprint(self, blueprint_data: Dict[str, Any]) -> List[SchemaValidationError]:
        """Validate deployment blueprint against schema"""
        return self._validate_blueprint(blueprint_data, "deployment")
    
    def validate_blueprint_file(self, file_path: Path, blueprint_type: str) -> List[SchemaValidationError]:
        """Validate blueprint file against schema"""
        self.validation_errors.clear()
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() == '.json':
                    blueprint_data = json.load(f)
                else:
                    import yaml
                    blueprint_data = yaml.safe_load(f)
            
            return self._validate_blueprint(blueprint_data, blueprint_type)
            
        except Exception as e:
            return [SchemaValidationError(
                level=ValidationLevel.ERROR,
                message=f"Failed to load blueprint file: {str(e)}",
                path=str(file_path)
            )]
    
    def _validate_blueprint(self, blueprint_data: Dict[str, Any], blueprint_type: str) -> List[SchemaValidationError]:
        """Validate blueprint data against schema"""
        errors = []
        
        if blueprint_type not in self.schemas:
            errors.append(SchemaValidationError(
                level=ValidationLevel.ERROR,
                message=f"Schema not found for blueprint type: {blueprint_type}",
                path=f"schema.{blueprint_type}"
            ))
            return errors
        
        schema = self.schemas[blueprint_type]
        
        try:
            # Create validator
            validator = jsonschema.Draft7Validator(schema)
            
            # Validate and collect errors
            validation_errors = sorted(validator.iter_errors(blueprint_data), key=lambda e: e.path)
            
            for error in validation_errors:
                # Convert JSON schema error to our error format
                error_path = '.'.join(str(p) for p in error.path) if error.path else "root"
                schema_path = '.'.join(str(p) for p in error.schema_path) if error.schema_path else None
                
                # Determine error level based on error type
                level = ValidationLevel.ERROR
                if "required" in error.message.lower():
                    level = ValidationLevel.CRITICAL
                elif "additional" in error.message.lower():
                    level = ValidationLevel.WARNING
                
                errors.append(SchemaValidationError(
                    level=level,
                    message=error.message,
                    path=error_path,
                    schema_path=schema_path,
                    value=error.instance
                ))
            
        except jsonschema.SchemaError as e:
            errors.append(SchemaValidationError(
                level=ValidationLevel.ERROR,
                message=f"Invalid schema: {str(e)}",
                path="schema"
            ))
        except Exception as e:
            errors.append(SchemaValidationError(
                level=ValidationLevel.ERROR,
                message=f"Validation failed: {str(e)}",
                path="validation"
            ))
        
        return errors
    
    def validate_all_blueprints(self, blueprint_dir: Path) -> Dict[str, List[SchemaValidationError]]:
        """Validate all blueprint files in directory"""
        results = {}
        
        # Find all blueprint files
        architecture_files = list(blueprint_dir.glob("**/architecture.yaml")) + list(blueprint_dir.glob("**/architecture.yml"))
        deployment_files = list(blueprint_dir.glob("**/deployment.yaml")) + list(blueprint_dir.glob("**/deployment.yml"))
        
        # Validate architecture blueprints
        for file_path in architecture_files:
            results[str(file_path)] = self.validate_blueprint_file(file_path, "architecture")
        
        # Validate deployment blueprints
        for file_path in deployment_files:
            results[str(file_path)] = self.validate_blueprint_file(file_path, "deployment")
        
        return results
    
    def get_schema_info(self, blueprint_type: str) -> Dict[str, Any]:
        """Get schema information for blueprint type"""
        if blueprint_type not in self.schemas:
            # FAIL FAST - No graceful degradation
            raise ValueError(
                f"CRITICAL: Blueprint type '{blueprint_type}' not found in schemas. "
                f"Available types: {list(self.schemas.keys())}. "
                "Cannot proceed without valid schema."
            )
        
        schema = self.schemas[blueprint_type]
        return {
            "title": schema.get("title", ""),
            "description": schema.get("description", ""),
            "version": schema.get("version", ""),
            "required_properties": schema.get("required", []),
            "properties": list(schema.get("properties", {}).keys())
        }
    
    def has_critical_errors(self, errors: List[SchemaValidationError]) -> bool:
        """Check if any errors are critical"""
        return any(error.level == ValidationLevel.CRITICAL for error in errors)
    
    def has_errors(self, errors: List[SchemaValidationError]) -> bool:
        """Check if any errors are error level or higher"""
        return any(error.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL] for error in errors)
    
    def format_errors(self, errors: List[SchemaValidationError]) -> str:
        """Format validation errors for display"""
        if not errors:
            return "No validation errors"
        
        lines = []
        for error in errors:
            level_icon = {
                ValidationLevel.INFO: "ℹ️",
                ValidationLevel.WARNING: "⚠️",
                ValidationLevel.ERROR: "❌",
                ValidationLevel.CRITICAL: "🔥"
            }.get(error.level, "❓")
            
            lines.append(f"{level_icon} {error.level.value.upper()}: {error.message}")
            if error.path:
                lines.append(f"   Path: {error.path}")
            if error.schema_path:
                lines.append(f"   Schema: {error.schema_path}")
            if error.value is not None:
                lines.append(f"   Value: {error.value}")
            lines.append("")
        
        return "\n".join(lines)


def validate_blueprint_file(file_path: str, blueprint_type: str) -> None:
    """CLI function to validate a blueprint file"""
    validator = SchemaValidator()
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    errors = validator.validate_blueprint_file(file_path_obj, blueprint_type)
    
    if not errors:
        print(f"✅ {blueprint_type.title()} blueprint is valid: {file_path}")
    else:
        print(f"❌ {blueprint_type.title()} blueprint validation failed: {file_path}")
        print(validator.format_errors(errors))
        
        if validator.has_critical_errors(errors):
            exit(1)
        elif validator.has_errors(errors):
            exit(1)


def validate_all_blueprints(blueprint_dir: str) -> None:
    """CLI function to validate all blueprints in directory"""
    validator = SchemaValidator()
    
    blueprint_dir_obj = Path(blueprint_dir)
    if not blueprint_dir_obj.exists():
        print(f"❌ Directory not found: {blueprint_dir}")
        return
    
    results = validator.validate_all_blueprints(blueprint_dir_obj)
    
    if not results:
        print(f"ℹ️ No blueprint files found in: {blueprint_dir}")
        return
    
    total_errors = 0
    critical_errors = 0
    
    for file_path, errors in results.items():
        if not errors:
            print(f"✅ Valid: {file_path}")
        else:
            print(f"❌ Invalid: {file_path}")
            print(validator.format_errors(errors))
            
            total_errors += len(errors)
            critical_errors += sum(1 for error in errors if error.level == ValidationLevel.CRITICAL)
    
    print(f"\n📊 Summary: {len(results)} files validated, {total_errors} errors found")
    if critical_errors > 0:
        print(f"🔥 {critical_errors} critical errors found")
        exit(1)
    elif total_errors > 0:
        print(f"❌ {total_errors} errors found")
        exit(1)
    else:
        print("✅ All blueprints valid")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python schema_validator.py <command> [args]")
        print("Commands:")
        print("  validate-file <file> <type>  - Validate single blueprint file")
        print("  validate-all <directory>     - Validate all blueprints in directory")
        exit(1)
    
    command = sys.argv[1]
    
    if command == "validate-file":
        if len(sys.argv) < 4:
            print("Usage: python schema_validator.py validate-file <file> <type>")
            print("Types: architecture, deployment")
            exit(1)
        
        file_path = sys.argv[2]
        blueprint_type = sys.argv[3]
        validate_blueprint_file(file_path, blueprint_type)
    
    elif command == "validate-all":
        if len(sys.argv) < 3:
            print("Usage: python schema_validator.py validate-all <directory>")
            exit(1)
        
        blueprint_dir = sys.argv[2]
        validate_all_blueprints(blueprint_dir)
    
    else:
        print(f"Unknown command: {command}")
        exit(1)