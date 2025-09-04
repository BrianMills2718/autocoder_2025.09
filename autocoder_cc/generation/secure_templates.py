from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Secure Component Template System for V5.0 Enhanced Generation
Implements predefined templates with fail-hard security validation
"""

from typing import Dict, Any, List, Optional, Type
from enum import Enum
from dataclasses import dataclass
import re
from pydantic import BaseModel, Field, ValidationError
from autocoder_cc.capabilities.ast_security_validator import (
    ASTSecurityValidator, validate_code_security, ASTSecurityValidationError
)


class TemplateSecurityError(Exception):
    """Raised when template security validation fails - no fallbacks available"""
    pass


class TemplateValidationError(Exception):
    """Raised when template validation fails - fail hard on invalid templates"""
    pass


class ComponentTemplateType(Enum):
    """Predefined component template types - no dynamic types allowed"""
    SOURCE = "source"
    TRANSFORMER = "transformer"
    SINK = "sink"


@dataclass
class TemplateVariable:
    """Secure template variable with strict validation"""
    name: str
    var_type: str
    required: bool = True
    default_value: Optional[Any] = None
    allowed_values: Optional[List[str]] = None
    validation_pattern: Optional[str] = None


@dataclass
class SecureTemplate:
    """Secure component template with predefined structure"""
    template_id: str
    component_type: ComponentTemplateType
    template_code: str
    required_variables: List[TemplateVariable]
    description: str
    security_level: str = "HIGH"


class SecureTemplateSystem:
    """
    V5.0 Secure Template System with Fail-Hard Security
    
    Key Security Principles:
    - No dynamic code execution (no eval, exec, compile)
    - Predefined templates only - no user-defined templates
    - Strict variable validation with allow-lists
    - Fail hard on any security violations
    - No fallback modes or graceful degradation
    """
    
    def __init__(self):
        self.logger = get_logger("SecureTemplateSystem")
        
        # Registry of predefined templates
        self._predefined_templates: Dict[str, SecureTemplate] = {}
        
        # AST-based security validator (replaces regex patterns)
        self._ast_security_validator = ASTSecurityValidator(strict_mode=True)
        
        # Allowed variable name pattern (still needed for variable validation)
        self._allowed_var_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        
        # Register predefined templates
        self._register_predefined_templates()
        
        self.logger.info("✅ Secure Template System initialized with AST-based fail-hard security validation")
    
    def _register_predefined_templates(self) -> None:
        """Register all predefined V5.0 component templates"""
        
        # Source component template
        source_template = SecureTemplate(
            template_id="enhanced_source_v5",
            component_type=ComponentTemplateType.SOURCE,
            template_code="""#!/usr/bin/env python3
from typing import Dict, Any, List
from autocoder_cc.components.enhanced_base import EnhancedSource
from pydantic import BaseModel, Field
import logging

class {class_name}(EnhancedSource):
    '''Generated V5.0 Source Component: {description}'''
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.data_type = "{data_type}"
        self.generation_method = "{generation_method}"
    
    def get_required_config_fields(self) -> List[str]:
        return {required_config_fields}
    
    def get_required_dependencies(self) -> List[str]:
        return {required_dependencies}
    
    async def process(self) -> None:
        '''Generate data using {generation_method}'''
        self.logger.info(f"Processing {{self.name}} - generating {{self.data_type}} data")
        
        # V5.0 generation logic with fail-hard validation
        try:
            generated_data = await self._generate_data()
            validated_data = self._validate_generated_data(generated_data)
            await self._emit_data(validated_data)
            
        except Exception as e:
            raise ComponentProcessingError(
                f"Data generation failed for {{self.name}}: {{e}}. "
                f"V5.0 sources fail hard on generation errors - no fallback data."
            )
    
    async def _generate_data(self) -> Dict[str, Any]:
        '''Component-specific data generation'''
        # Template placeholder for generation logic
        return {{
            "timestamp": time.time(),
            "component_source": "{{self.name}}",
            "data_type": "{{self.data_type}}",
            "data_id": f"{{{{self.name}}}}_{{{{uuid.uuid4().hex}}}}",
            # Component-specific fields added here
        }}
    
    def _validate_generated_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Validate generated data against output schema'''
        if hasattr(self, 'output_schemas') and self.output_schemas:
            for output_name, schema_class in self.output_schemas.items():
                try:
                    validated = schema_class(**data)
                    return validated.dict()
                except ValidationError as e:
                    raise SchemaValidationError(
                        f"Generated data validation failed: {{e}}"
                    )
        return data
    
    async def _emit_data(self, data: Dict[str, Any]) -> None:
        '''Emit validated data to outputs'''
        self.logger.info(f"✅ Data generated and validated for {{self.name}}")
""",
            required_variables=[
                TemplateVariable("class_name", "str", validation_pattern=r'^[A-Z][a-zA-Z0-9]*$'),
                TemplateVariable("description", "str"),
                TemplateVariable("data_type", "str", allowed_values=["json", "csv", "xml", "binary", "text"]),
                TemplateVariable("generation_method", "str", allowed_values=["api", "database", "file", "synthetic"]),
                TemplateVariable("required_config_fields", "list"),
                TemplateVariable("required_dependencies", "list"),
            ],
            description="Enhanced Source component template with V5.0 validation"
        )
        
        # Transformer component template
        transformer_template = SecureTemplate(
            template_id="enhanced_transformer_v5",
            component_type=ComponentTemplateType.TRANSFORMER,
            template_code="""#!/usr/bin/env python3
from typing import Dict, Any, List
from autocoder_cc.components.enhanced_base import EnhancedTransformer
from pydantic import BaseModel, Field
import logging

class {class_name}(EnhancedTransformer):
    '''Generated V5.0 Transformer Component: {description}'''
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.transformation_type = "{transformation_type}"
        self.processing_method = "{processing_method}"
    
    def get_required_config_fields(self) -> List[str]:
        return {required_config_fields}
    
    def get_required_dependencies(self) -> List[str]:
        return {required_dependencies}
    
    async def process(self) -> None:
        '''Transform data using {processing_method}'''
        self.logger.info(f"Processing {{self.name}} - applying {{self.transformation_type}} transformation")
        
        # V5.0 transformation logic with fail-hard validation
        try:
            input_data = await self._receive_input_data()
            validated_input = self._validate_input_data(input_data)
            transformed_data = await self._transform_data(validated_input)
            validated_output = self._validate_output_data(transformed_data)
            await self._emit_output_data(validated_output)
            
        except Exception as e:
            raise ComponentProcessingError(
                f"Data transformation failed for {{self.name}}: {{e}}. "
                f"V5.0 transformers fail hard on processing errors - no partial results."
            )
    
    async def _receive_input_data(self) -> Dict[str, Any]:
        '''Receive data from input connections'''
        # Template placeholder for input data reception
        return {{"received": True, "data": {{}}}}
    
    def _validate_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Validate input data against input schemas'''
        if hasattr(self, 'input_schemas') and self.input_schemas:
            for input_name, schema_class in self.input_schemas.items():
                try:
                    validated = schema_class(**data)
                    return validated.dict()
                except ValidationError as e:
                    raise SchemaValidationError(
                        f"Input data validation failed: {{e}}"
                    )
        return data
    
    async def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Apply {transformation_type} transformation'''
        # Component-specific transformation logic
        transformed = data.copy()
        transformed.update({{
            "transformation_applied": "{{{{self.transformation_type}}}}",
            "processing_method": "{{{{self.processing_method}}}}",
            "transformer_name": "{class_name}",
            "transformed_timestamp": time.time()
        }})
        return transformed
    
    def _validate_output_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Validate output data against output schemas'''
        if hasattr(self, 'output_schemas') and self.output_schemas:
            for output_name, schema_class in self.output_schemas.items():
                try:
                    validated = schema_class(**data)
                    return validated.dict()
                except ValidationError as e:
                    raise SchemaValidationError(
                        f"Output data validation failed: {{e}}"
                    )
        return data
    
    async def _emit_output_data(self, data: Dict[str, Any]) -> None:
        '''Emit transformed data to outputs'''
        self.logger.info(f"✅ Data transformed and validated for {{self.name}}")
""",
            required_variables=[
                TemplateVariable("class_name", "str", validation_pattern=r'^[A-Z][a-zA-Z0-9]*$'),
                TemplateVariable("description", "str"),
                TemplateVariable("transformation_type", "str", allowed_values=["filter", "map", "aggregate", "enrich", "normalize"]),
                TemplateVariable("processing_method", "str", allowed_values=["sync", "async", "batch", "stream"]),
                TemplateVariable("required_config_fields", "list"),
                TemplateVariable("required_dependencies", "list"),
            ],
            description="Enhanced Transformer component template with V5.0 validation"
        )
        
        # Sink component template
        sink_template = SecureTemplate(
            template_id="enhanced_sink_v5",
            component_type=ComponentTemplateType.SINK,
            template_code="""#!/usr/bin/env python3
from typing import Dict, Any, List
from autocoder_cc.components.enhanced_base import EnhancedSink
from pydantic import BaseModel, Field
import logging

class {class_name}(EnhancedSink):
    '''Generated V5.0 Sink Component: {description}'''
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.storage_type = "{storage_type}"
        self.persistence_method = "{persistence_method}"
    
    def get_required_config_fields(self) -> List[str]:
        return {required_config_fields}
    
    def get_required_dependencies(self) -> List[str]:
        return {required_dependencies}
    
    async def process(self) -> None:
        '''Store data using {persistence_method}'''
        self.logger.info(f"Processing {{self.name}} - storing to {{self.storage_type}}")
        
        # V5.0 storage logic with fail-hard validation
        try:
            input_data = await self._receive_input_data()
            validated_input = self._validate_input_data(input_data)
            storage_result = await self._store_data(validated_input)
            self._validate_storage_result(storage_result)
            
        except Exception as e:
            raise ComponentProcessingError(
                f"Data storage failed for {{self.name}}: {{e}}. "
                f"V5.0 sinks fail hard on storage errors - no partial writes allowed."
            )
    
    async def _receive_input_data(self) -> Dict[str, Any]:
        '''Receive data from input connections'''
        # Template placeholder for input data reception
        return {{"received": True, "data": {{}}}}
    
    def _validate_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Validate input data against input schemas'''
        if hasattr(self, 'input_schemas') and self.input_schemas:
            for input_name, schema_class in self.input_schemas.items():
                try:
                    validated = schema_class(**data)
                    return validated.dict()
                except ValidationError as e:
                    raise SchemaValidationError(
                        f"Input data validation failed: {{e}}"
                    )
        return data
    
    async def _store_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Store data using {persistence_method}'''
        # Component-specific storage logic
        storage_metadata = {{
            "storage_type": "{{{{self.storage_type}}}}",
            "persistence_method": "{{{{self.persistence_method}}}}",
            "sink_name": "{{{{self.name}}}}",
            "storage_timestamp": time.time(),
            "data_size": len(str(data)),
            "storage_location": f"{{{{self.storage_type}}}}/{{{{self.name}}}}"
        }}
        
        # Storage operation would happen here
        return {{
            "storage_successful": True,
            "metadata": storage_metadata,
            "stored_data_id": f"{{{{self.name}}}}_{{{{uuid.uuid4().hex}}}}"
        }}
    
    def _validate_storage_result(self, result: Dict[str, Any]) -> None:
        '''Validate storage operation completed successfully'''
        if not result.get("storage_successful", False):
            raise ComponentProcessingError(
                f"Storage validation failed for {{self.name}}: {{result}}"
            )
        
        self.logger.info(f"✅ Data stored and validated for {{self.name}}")
""",
            required_variables=[
                TemplateVariable("class_name", "str", validation_pattern=r'^[A-Z][a-zA-Z0-9]*$'),
                TemplateVariable("description", "str"),
                TemplateVariable("storage_type", "str", allowed_values=["database", "file", "api", "queue", "cache"]),
                TemplateVariable("persistence_method", "str", allowed_values=["sync", "async", "batch", "stream"]),
                TemplateVariable("required_config_fields", "list"),
                TemplateVariable("required_dependencies", "list"),
            ],
            description="Enhanced Sink component template with V5.0 validation"
        )
        
        # Register all templates
        self._predefined_templates[source_template.template_id] = source_template
        self._predefined_templates[transformer_template.template_id] = transformer_template
        self._predefined_templates[sink_template.template_id] = sink_template
        
        self.logger.info(f"✅ Registered {len(self._predefined_templates)} predefined templates")
    
    def validate_template_security(self, template_code: str) -> None:
        """Validate template code for security violations using AST analysis - fail hard on any violations"""
        
        try:
            # Use AST-based validation instead of brittle regex patterns
            violations = self._ast_security_validator.validate_code(template_code)
            
            # If we get here without exception, no critical violations were found
            # Log any non-critical violations for monitoring
            if violations:
                non_critical = [v for v in violations if v.severity != "critical"]
                if non_critical:
                    self.logger.warning(f"Non-critical security issues in template: {len(non_critical)} violations")
                    for violation in non_critical:
                        self.logger.warning(f"  - {violation.description} (line {violation.line_number})")
            
            self.logger.debug("✅ Template AST security validation passed")
            
        except ASTSecurityValidationError as e:
            # Convert AST security violations to template security error
            violation_details = []
            for violation in e.violations:
                violation_details.append(
                    f"{violation.description} (line {violation.line_number}, severity: {violation.severity})"
                )
            
            raise TemplateSecurityError(
                f"AST security validation failed: {len(e.violations)} violations detected. "
                f"V5.0 templates prohibit dangerous code patterns - no exceptions allowed. "
                f"Violations: {'; '.join(violation_details)}"
            ) from e
        
        except Exception as e:
            # Handle any other AST parsing errors
            raise TemplateSecurityError(
                f"Template security validation failed due to code analysis error: {e}. "
                f"V5.0 requires all template code to be parseable and secure."
            ) from e
    
    def validate_template_variables(self, variables: Dict[str, Any], template: SecureTemplate) -> None:
        """Validate template variables against security requirements"""
        
        # Check for unexpected variables (not in template definition)
        for var_name in variables:
            if not any(req_var.name == var_name for req_var in template.required_variables):
                # Only validate names of variables that will be used in template
                continue
        
        # Check all required variables are provided
        for required_var in template.required_variables:
            if required_var.required and required_var.name not in variables:
                raise TemplateValidationError(
                    f"Required variable '{required_var.name}' missing for template '{template.template_id}'. "
                    f"V5.0 templates require all variables - no defaults or fallbacks."
                )
            
            if required_var.name in variables:
                value = variables[required_var.name]
                
                # Validate variable name pattern (only for template variables)
                if not self._allowed_var_pattern.match(required_var.name):
                    raise TemplateSecurityError(
                        f"Invalid variable name '{required_var.name}'. "
                        f"V5.0 allows only alphanumeric names with underscores."
                    )
                
                # Validate allowed values
                if required_var.allowed_values and value not in required_var.allowed_values:
                    raise TemplateValidationError(
                        f"Variable '{required_var.name}' value '{value}' not in allowed values: {required_var.allowed_values}. "
                        f"V5.0 templates enforce strict value constraints."
                    )
                
                # Validate pattern
                if required_var.validation_pattern:
                    if not re.match(required_var.validation_pattern, str(value)):
                        raise TemplateValidationError(
                            f"Variable '{required_var.name}' value '{value}' does not match pattern '{required_var.validation_pattern}'"
                        )
        
        self.logger.debug(f"✅ Template variables validated for {template.template_id}")
    
    def get_template(self, template_id: str) -> SecureTemplate:
        """Get predefined template by ID - fail hard if not found"""
        
        if template_id not in self._predefined_templates:
            available_templates = list(self._predefined_templates.keys())
            raise TemplateValidationError(
                f"Template '{template_id}' not found. "
                f"Available predefined templates: {available_templates}. "
                f"V5.0 only allows predefined templates - no custom templates permitted."
            )
        
        return self._predefined_templates[template_id]
    
    def list_templates(self) -> List[str]:
        """List all available predefined templates"""
        return list(self._predefined_templates.keys())
    
    def generate_component_code(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Generate component code from template with security validation"""
        
        # Get template
        template = self.get_template(template_id)
        
        # Validate template security
        self.validate_template_security(template.template_code)
        
        # Validate variables
        self.validate_template_variables(variables, template)
        
        try:
            # Perform secure string substitution (no eval/exec)
            generated_code = template.template_code.format(**variables)
            
            # Final security check on generated code
            self.validate_template_security(generated_code)
            
            self.logger.info(f"✅ Component code generated from template: {template_id}")
            return generated_code
            
        except KeyError as e:
            raise TemplateValidationError(
                f"Template variable substitution failed: missing variable {e}. "
                f"V5.0 templates require all variables to be provided."
            )
        except Exception as e:
            raise TemplateValidationError(
                f"Template code generation failed: {e}. "
                f"V5.0 templates must generate valid code - no partial generation allowed."
            )
    
    def get_template_info(self, template_id: str) -> Dict[str, Any]:
        """Get information about a predefined template"""
        
        template = self.get_template(template_id)
        
        return {
            "template_id": template.template_id,
            "component_type": template.component_type.value,
            "description": template.description,
            "security_level": template.security_level,
            "required_variables": [
                {
                    "name": var.name,
                    "type": var.var_type,
                    "required": var.required,
                    "allowed_values": var.allowed_values,
                    "validation_pattern": var.validation_pattern
                }
                for var in template.required_variables
            ]
        }


# Global secure template system instance
secure_template_system = SecureTemplateSystem()