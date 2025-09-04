from typing import List, Dict, Any
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError
from autocoder_cc.validation.exceptions import ValidationException

class ConfigurationValidator:
    """Validates component configurations against requirements"""
    
    def validate_component_config(
        self,
        component_type: str,
        config: Dict[str, Any],
        context: PipelineContext,
        requirements: List[ConfigRequirement]
    ) -> List[ValidationError]:
        """Validate configuration against requirements"""
        errors = []
        
        # Check required fields
        errors.extend(self.check_required_fields(requirements, config, context))
        
        # Validate field types
        errors.extend(self.validate_field_types(requirements, config, context))
        
        # Check conditional requirements
        errors.extend(self.check_conditional_requirements(requirements, config, context))
        
        # Run custom validators
        errors.extend(self.run_custom_validators(requirements, config, context))
        
        return errors
    
    def check_required_fields(
        self,
        requirements: List[ConfigRequirement],
        config: Dict[str, Any],
        context: PipelineContext
    ) -> List[ValidationError]:
        """Check all required fields are present"""
        errors = []
        
        for req in requirements:
            if req.name not in config:
                # Check if field is required OR has a default/example that should be applied
                if req.required or req.default is not None or req.example is not None:
                    # Check if conditionally required
                    if req.depends_on:
                        # Check if dependency condition is met
                        condition_met = all(
                            config.get(k) == v for k, v in req.depends_on.items()
                        )
                        if not condition_met:
                            continue  # Not required in this case
                    
                    # Build appropriate message based on what's available
                    message = f"Field '{req.name}' is missing"
                    if req.default is not None:
                        message += f" (has default: {req.default})"
                    elif req.required:
                        message = f"Required field '{req.name}' is missing"
                    
                    # Build suggestion
                    suggestion = None
                    if req.example is not None:
                        suggestion = f"Add '{req.name}': {req.example}"
                    elif req.default is not None:
                        suggestion = f"Add '{req.name}': {req.default}"
                    
                    errors.append(ValidationError(
                        component=context.component_name,
                        field=req.name,
                        error_type="missing",
                        message=message,
                        suggestion=suggestion
                    ))
                
        return errors
    
    def validate_field_types(
        self,
        requirements: List[ConfigRequirement],
        config: Dict[str, Any],
        context: PipelineContext
    ) -> List[ValidationError]:
        """Validate field types match requirements"""
        errors = []
        
        for req in requirements:
            if req.name in config:
                value = config[req.name]
                expected_type = self._get_python_type(req.type)
                
                if expected_type and not isinstance(value, expected_type):
                    errors.append(ValidationError(
                        component=context.component_name,
                        field=req.name,
                        error_type="invalid",
                        message=f"Field '{req.name}' has wrong type. Expected {req.type}, got {type(value).__name__}",
                        suggestion=f"Convert to {req.type}"
                    ))
                    
        return errors
    
    def check_conditional_requirements(
        self,
        requirements: List[ConfigRequirement],
        config: Dict[str, Any],
        context: PipelineContext
    ) -> List[ValidationError]:
        """Check depends_on and conflicts_with conditions"""
        errors = []
        
        for req in requirements:
            if req.name not in config:
                continue
                
            # Check conflicts
            if req.conflicts_with:
                for conflicting_field in req.conflicts_with:
                    if conflicting_field in config:
                        errors.append(ValidationError(
                            component=context.component_name,
                            field=req.name,
                            error_type="conflict",
                            message=f"Field '{req.name}' conflicts with '{conflicting_field}'",
                            suggestion=f"Remove either '{req.name}' or '{conflicting_field}'"
                        ))
            
            # Check required companions
            if req.requires:
                for required_field in req.requires:
                    if required_field not in config:
                        errors.append(ValidationError(
                            component=context.component_name,
                            field=required_field,
                            error_type="missing",
                            message=f"Field '{required_field}' is required when '{req.name}' is present",
                            suggestion=f"Add '{required_field}' field"
                        ))
                        
        return errors
    
    def run_custom_validators(
        self,
        requirements: List[ConfigRequirement],
        config: Dict[str, Any],
        context: PipelineContext
    ) -> List[ValidationError]:
        """Run custom validator functions"""
        errors = []
        
        for req in requirements:
            if req.name in config and req.validator:
                value = config[req.name]
                try:
                    if not req.validator(value):
                        errors.append(ValidationError(
                            component=context.component_name,
                            field=req.name,
                            error_type="invalid",
                            message=f"Field '{req.name}' failed validation",
                            suggestion=req.example if req.example else None
                        ))
                except Exception as e:
                    errors.append(ValidationError(
                        component=context.component_name,
                        field=req.name,
                        error_type="invalid",
                        message=f"Validator error for '{req.name}': {str(e)}",
                        suggestion=None
                    ))
                    
        return errors
    
    def _get_python_type(self, type_str: str):
        """Convert string type to Python type"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        return type_map.get(type_str)