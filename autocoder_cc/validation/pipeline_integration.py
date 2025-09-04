import logging
from typing import Dict, Any
from autocoder_cc.validation.config_validator import ConfigurationValidator
from autocoder_cc.validation.semantic_healer import SemanticHealer
from autocoder_cc.validation.pipeline_context import PipelineContext
from autocoder_cc.validation.context_builder import PipelineContextBuilder
from autocoder_cc.validation.exceptions import ValidationException, HealingFailure
from autocoder_cc.components.component_registry import component_registry

logger = logging.getLogger(__name__)

class StrictValidationPipeline:
    """
    Strict validation pipeline: Heal completely or fail with clear errors.
    No partial fixes, no best-effort - deterministic behavior only.
    """
    
    def __init__(self):
        self.validator = ConfigurationValidator()
        self.healer = SemanticHealer(validator=self.validator)
        self.context_builder = PipelineContextBuilder()
        
    async def validate_and_heal_or_fail(
        self,
        component_name: str,
        component_type: str,
        config: Dict[str, Any],
        blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate configuration, heal if needed, validate again, or fail.
        
        Returns:
            Fully valid configuration
            
        Raises:
            ValidationException: If configuration cannot be made valid
        """
        # Step 1: Build context
        try:
            context = self.context_builder.build_from_blueprint(blueprint, component_name)
            context.existing_config = config
        except Exception as e:
            raise ValidationException(
                f"Cannot build context for {component_name}: {e}\n"
                f"Blueprint structure may be invalid"
            )
        
        # Step 2: Get requirements
        component_class = component_registry.components.get(component_type)
        if not component_class or not hasattr(component_class, 'get_config_requirements'):
            logger.warning(f"No requirements defined for {component_type}, skipping validation")
            return config
            
        try:
            # Pass component_type to get_config_requirements since all components use ComposedComponent
            requirements = component_class.get_config_requirements(component_type)
        except Exception as e:
            raise ValidationException(
                f"Cannot get requirements for {component_type}: {e}\n"
                f"Component may have broken get_config_requirements method"
            )
        
        # Step 3: Initial validation
        initial_errors = self.validator.validate_component_config(
            component_type, config, context, requirements
        )
        
        if not initial_errors:
            logger.info(f"✅ Configuration already valid for {component_name}")
            return config
        
        # Step 4: Log initial problems
        logger.info(f"Found {len(initial_errors)} validation errors for {component_name}")
        for error in initial_errors:
            logger.debug(f"  - {error.field}: {error.message}")
        
        # Step 5: Attempt healing
        try:
            healed_config = await self.healer.heal_configuration(
                context, requirements, initial_errors
            )
            logger.info(f"🔧 Healed configuration for {component_name}")
        except HealingFailure as e:
            # Healing failed - provide clear error message
            error_details = self._format_errors(initial_errors)
            raise ValidationException(
                f"❌ Cannot heal configuration for {component_name}\n\n"
                f"Component Type: {component_type}\n"
                f"Validation Errors:\n{error_details}\n\n"
                f"Healing Failed: {e}\n\n"
                f"Action Required: Fix these fields in your blueprint:\n"
                f"{self._suggest_fixes(initial_errors, requirements)}"
            )
        
        # Step 6: Validate healed configuration
        final_errors = self.validator.validate_component_config(
            component_type, healed_config, context, requirements
        )
        
        if final_errors:
            # Healing didn't fully work - this should be rare
            initial_details = self._format_errors(initial_errors)
            final_details = self._format_errors(final_errors)
            
            raise ValidationException(
                f"❌ Healed configuration still invalid for {component_name}\n\n"
                f"Original Errors:\n{initial_details}\n\n"
                f"After Healing, Still Have Errors:\n{final_details}\n\n"
                f"This indicates a bug in the healing logic.\n"
                f"Please report this issue with the above details."
            )
        
        # Step 7: Success!
        logger.info(f"✅ Configuration valid after healing for {component_name}")
        return healed_config
    
    def _format_errors(self, errors):
        """Format validation errors for clear display"""
        if not errors:
            return "  None"
        
        formatted = []
        for error in errors:
            formatted.append(f"  • {error.field} ({error.error_type}): {error.message}")
            if error.suggestion:
                formatted.append(f"    Suggestion: {error.suggestion}")
        
        return "\n".join(formatted)
    
    def _suggest_fixes(self, errors, requirements):
        """Generate actionable fix suggestions"""
        suggestions = []
        
        for error in errors:
            req = next((r for r in requirements if r.name == error.field), None)
            if req:
                if req.example:
                    suggestions.append(f"  {error.field}: {req.example}")
                elif req.default is not None:
                    suggestions.append(f"  {error.field}: {req.default}")
                else:
                    suggestions.append(f"  {error.field}: <provide {req.type} value>")
        
        return "\n".join(suggestions) if suggestions else "  Check component documentation"