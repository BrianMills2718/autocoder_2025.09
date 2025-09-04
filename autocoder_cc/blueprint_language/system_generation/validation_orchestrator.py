"""Validation orchestrator for system generation."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from autocoder_cc.observability import get_logger


@dataclass
class ValidationResult:
    """Result of validation orchestration."""
    success: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class ValidationOrchestrator:
    """Orchestrates validation across different stages of system generation."""
    
    def __init__(self):
        """Initialize validation orchestrator."""
        self.logger = get_logger("ValidationOrchestrator")
        self.validators = []
        
    async def validate_component(self, component_code: str, component_name: str) -> ValidationResult:
        """Validate a generated component.
        
        Args:
            component_code: Generated component code
            component_name: Name of the component
            
        Returns:
            ValidationResult with success status and any issues
        """
        errors = []
        warnings = []
        
        # Basic syntax validation
        try:
            compile(component_code, f"{component_name}.py", 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {component_name}: {e}")
            
        # Check for required methods
        if "async def process" not in component_code and "def process" not in component_code:
            warnings.append(f"Component {component_name} missing process method")
            
        if "async def setup" not in component_code and "def setup" not in component_code:
            warnings.append(f"Component {component_name} missing setup method")
            
        if "async def cleanup" not in component_code and "def cleanup" not in component_code:
            warnings.append(f"Component {component_name} missing cleanup method")
            
        success = len(errors) == 0
        
        if success:
            self.logger.info(f"✅ Validation passed for {component_name}")
        else:
            self.logger.error(f"❌ Validation failed for {component_name}: {errors}")
            
        return ValidationResult(
            success=success,
            errors=errors,
            warnings=warnings,
            metadata={"component_name": component_name}
        )
        
    async def validate_system(self, system_config: Dict[str, Any]) -> ValidationResult:
        """Validate an entire system configuration.
        
        Args:
            system_config: System configuration dictionary
            
        Returns:
            ValidationResult with system-level validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        if "components" not in system_config:
            errors.append("System configuration missing 'components' field")
            
        if "connections" not in system_config:
            warnings.append("System configuration missing 'connections' field")
            
        # Validate component references
        if "components" in system_config and "connections" in system_config:
            component_names = set(system_config["components"].keys())
            for connection in system_config.get("connections", []):
                if connection.get("from") not in component_names:
                    errors.append(f"Connection references unknown component: {connection.get('from')}")
                if connection.get("to") not in component_names:
                    errors.append(f"Connection references unknown component: {connection.get('to')}")
                    
        success = len(errors) == 0
        
        if success:
            self.logger.info("✅ System validation passed")
        else:
            self.logger.error(f"❌ System validation failed: {errors}")
            
        return ValidationResult(
            success=success,
            errors=errors,
            warnings=warnings,
            metadata={"system_config": system_config}
        )
        
    def register_validator(self, validator: Any):
        """Register a custom validator.
        
        Args:
            validator: Validator instance with validate method
        """
        self.validators.append(validator)
        self.logger.info(f"Registered validator: {validator.__class__.__name__}")
        
    async def run_all_validators(self, target: Any) -> List[ValidationResult]:
        """Run all registered validators on a target.
        
        Args:
            target: Target to validate (component, system, etc.)
            
        Returns:
            List of validation results from all validators
        """
        results = []
        for validator in self.validators:
            if hasattr(validator, 'validate'):
                try:
                    result = await validator.validate(target)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Validator {validator.__class__.__name__} failed: {e}")
                    results.append(ValidationResult(
                        success=False,
                        errors=[str(e)],
                        warnings=[],
                        metadata={"validator": validator.__class__.__name__}
                    ))
        return results
    
    def _validate_pre_generation(self, system_blueprint: Any) -> List[str]:
        """Validate system blueprint before generation.
        
        Args:
            system_blueprint: Blueprint to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation - check that blueprint has required structure
        if not hasattr(system_blueprint, 'system'):
            errors.append("Blueprint missing 'system' attribute")
            return errors
            
        system = system_blueprint.system
        
        # Check for components
        if not hasattr(system, 'components') or not system.components:
            errors.append("System has no components defined")
            
        # Check component structure
        if hasattr(system, 'components'):
            for idx, component in enumerate(system.components):
                if not hasattr(component, 'name'):
                    errors.append(f"Component {idx} missing 'name' attribute")
                if not hasattr(component, 'type'):
                    errors.append(f"Component {idx} missing 'type' attribute")
                    
        # Log validation result
        if errors:
            self.logger.warning(f"Pre-generation validation found {len(errors)} issues")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("✅ Pre-generation validation passed")
            
        return errors