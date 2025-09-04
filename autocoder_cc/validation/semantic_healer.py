import os
import hashlib
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from autocoder_cc.validation.config_requirement import ConfigRequirement
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError
from autocoder_cc.validation.exceptions import HealingFailure
from autocoder_cc.validation.healing_strategies import (
    DefaultValueStrategy,
    ExampleBasedStrategy,
    ContextBasedStrategy
)

logger = logging.getLogger(__name__)

class SemanticHealer:
    """
    Heals configuration issues using multiple strategies.
    Order of precedence: Default → Example → Context → LLM
    """
    
    def __init__(self, validator=None):
        """
        Initialize with optional validator to avoid circular dependency.
        
        Args:
            validator: ConfigurationValidator instance (optional)
        """
        self.validator = validator  # Injected to avoid circular dependency
        self.model = self._initialize_gemini()
        self.healing_cache = {}
        
        # Initialize strategies in order of precedence
        self.strategies = [
            DefaultValueStrategy(),
            ExampleBasedStrategy(),
            ContextBasedStrategy()
        ]
        
    def _initialize_gemini(self):
        """Initialize Gemini model with API key"""
        try:
            # Check for various possible API key environment variables
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_KEY")
            if not api_key:
                logger.warning("No Gemini/Google API key found - LLM healing disabled")
                return None  # Don't create model without API key
            genai.configure(api_key=api_key)
            # Only create model if we have a valid API key
            model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini model initialized successfully")
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
            return None
    
    async def heal_configuration(
        self,
        context: PipelineContext,
        requirements: List[ConfigRequirement],
        errors: List[ValidationError]
    ) -> Dict[str, Any]:
        """
        Heal configuration issues using multiple strategies.
        
        Returns healed configuration or raises HealingFailure.
        """
        # Check cache first
        cache_key = self._generate_cache_key(context, errors)
        if cache_key in self.healing_cache:
            logger.info(f"Using cached healing for {context.component_name}")
            return self.healing_cache[cache_key]
        
        # Start with existing config
        healed_config = dict(context.existing_config)
        unhealed_errors = []
        
        # Try non-LLM strategies first
        for error in errors:
            healed = await self._try_non_llm_healing(error, requirements, context)
            if healed is not None:
                healed_config[error.field] = healed
                logger.info(f"Healed {error.field} using non-LLM strategy")
            else:
                unhealed_errors.append(error)
        
        # If errors remain and we have LLM, try LLM healing
        if unhealed_errors and self.model:
            try:
                llm_healed = await self._try_llm_healing(
                    context, requirements, unhealed_errors, healed_config
                )
                healed_config.update(llm_healed)
            except Exception as e:
                logger.error(f"LLM healing failed: {e}")
                raise HealingFailure(
                    f"Could not heal {len(unhealed_errors)} errors",
                    attempts=3,
                    errors=[e.message for e in unhealed_errors]
                )
        elif unhealed_errors:
            # No LLM available and errors remain
            raise HealingFailure(
                f"Could not heal {len(unhealed_errors)} errors (no LLM)",
                attempts=0,
                errors=[e.message for e in unhealed_errors]
            )
        
        # Validate healed configuration if validator available
        if self.validator:
            validation_errors = self.validator.validate_component_config(
                context.component_type,
                healed_config,
                context,
                requirements
            )
            
            if validation_errors:
                logger.warning(f"Healed config still has {len(validation_errors)} errors")
                # Try one more time with LLM if available
                if self.model:
                    healed_config = await self._refine_healing(
                        context, requirements, healed_config, validation_errors
                    )
        
        # Cache successful healing
        self.healing_cache[cache_key] = healed_config
        logger.info(f"Successfully healed configuration for {context.component_name}")
        
        return healed_config
    
    async def _try_non_llm_healing(
        self,
        error: ValidationError,
        requirements: List[ConfigRequirement],
        context: PipelineContext
    ) -> Optional[Any]:
        """Try to heal using non-LLM strategies"""
        # Find the requirement for this field
        requirement = next(
            (r for r in requirements if r.name == error.field),
            None
        )
        
        # Try each strategy in order
        for strategy in self.strategies:
            if strategy.can_heal(error, requirement):
                try:
                    return strategy.heal(error, requirement, context)
                except Exception as e:
                    logger.debug(f"Strategy {strategy.__class__.__name__} failed: {e}")
                    continue
        
        return None
    
    async def _try_llm_healing(
        self,
        context: PipelineContext,
        requirements: List[ConfigRequirement],
        errors: List[ValidationError],
        partial_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to heal remaining errors with retry logic"""
        max_attempts = 3
        wait_times = [2, 4, 8]  # Exponential backoff
        
        for attempt in range(max_attempts):
            try:
                prompt = self._generate_healing_prompt(context, requirements, errors, partial_config)
                response = await self._call_gemini(prompt)
                healed_fields = self._parse_healed_config(response)
                return healed_fields
            except Exception as e:
                if attempt < max_attempts - 1:
                    wait_time = wait_times[attempt]
                    logger.warning(f"LLM healing attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise HealingFailure("LLM healing failed after all attempts", attempts=max_attempts, errors=[])
    
    def _generate_cache_key(
        self,
        context: PipelineContext,
        errors: List[ValidationError]
    ) -> str:
        """Generate deterministic cache key"""
        # Sort errors for consistency
        sorted_errors = sorted(errors, key=lambda e: (e.component, e.field))
        
        key_data = {
            "component": context.component_name,
            "component_type": context.component_type,
            "errors": [e.to_dict() for e in sorted_errors],
            "existing_config": sorted(context.existing_config.items())
        }
        
        # Use JSON with sorted keys for deterministic output
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _generate_healing_prompt(
        self,
        context: PipelineContext,
        requirements: List[ConfigRequirement],
        errors: List[ValidationError],
        partial_config: Dict[str, Any]
    ) -> str:
        """Generate prompt for Gemini to heal configuration"""
        # Format requirements
        req_text = []
        for req in requirements:
            if any(e.field == req.name for e in errors):
                req_text.append(f"- {req.name} ({req.type}): {req.description}")
                if req.example:
                    req_text.append(f"  Example: {req.example}")
                if req.semantic_type:
                    req_text.append(f"  Type: {req.semantic_type}")
        
        # Format errors
        error_text = [f"- {e.field}: {e.message}" for e in errors]
        
        prompt = f"""You are a configuration expert for a data processing system.

System Context:
{context.to_prompt_context()}

Missing/Invalid Configuration Fields:
{chr(10).join(req_text)}

Current Errors:
{chr(10).join(error_text)}

Partial Configuration (already healed/valid):
{json.dumps(partial_config, indent=2)}

Generate ONLY the missing configuration fields as JSON. Include ONLY the fields that have errors.
Do not include fields that are already in the partial configuration.

Return a valid JSON object with the missing fields:
"""
        return prompt
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini model with prompt"""
        if not self.model:
            raise HealingFailure("Gemini model not initialized", attempts=0, errors=[])
        
        response = await self.model.generate_content_async(prompt)
        return response.text
    
    def _parse_healed_config(self, response: str) -> Dict[str, Any]:
        """Parse JSON configuration from Gemini response"""
        # Extract JSON from response
        try:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try parsing entire response
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response}")
            return {}
    
    async def _refine_healing(
        self,
        context: PipelineContext,
        requirements: List[ConfigRequirement],
        healed_config: Dict[str, Any],
        validation_errors: List[ValidationError]
    ) -> Dict[str, Any]:
        """Refine healing with additional LLM attempt"""
        logger.info(f"Refining healing for {len(validation_errors)} remaining errors")
        
        refined = await self._try_llm_healing(
            context, requirements, validation_errors, healed_config
        )
        
        healed_config.update(refined)
        return healed_config