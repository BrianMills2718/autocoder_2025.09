#!/usr/bin/env python3
"""
Unified LLM Component Generator - Simplified replacement
Eliminates hanging issues by using the unified LLM provider with LiteLLM
"""

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional
from .llm_generation.component_wrapper import wrap_component_with_boilerplate
from dotenv import load_dotenv

# Use new unified provider instead of problematic multi-provider system
from autocoder_cc.llm_providers.unified_llm_provider import UnifiedLLMProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest

from autocoder_cc.core.config import settings
from autocoder_cc.error_handling import ConsistentErrorHandler
from autocoder_cc.observability.structured_logging import get_logger
from autocoder_cc.observability.metrics import get_metrics_collector

# Keep existing extracted modules for validation and prompting
from .llm_generation.o3_specialized_prompts import O3PromptEngine
from .llm_generation.response_validator import ResponseValidator, ComponentGenerationError
from .llm_generation.prompt_engine import PromptEngine
from .llm_generation.retry_orchestrator import RetryOrchestrator, ErrorType
from .llm_generation.context_builder import ContextBuilder

load_dotenv()


class LLMComponentGenerator:
    """
    Unified LLM Component Generator with simplified architecture
    
    Key Changes:
    - Uses UnifiedLLMProvider instead of complex MultiProviderManager
    - Eliminates thread executor hanging issues
    - Maintains compatibility with existing modules
    - Uses asyncio.sleep() instead of time.sleep() to prevent blocking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with unified LLM provider"""
        
        # Initialize structured logger
        self.logger = get_logger(__name__, component="llm_component_generator_unified")
        
        # Initialize metrics collector
        self.metrics = get_metrics_collector("llm_component_generator_unified")
        
        # Use provided config or default
        self.config = config or {}
        
        # Initialize unified provider (eliminates hanging issues)
        self.llm_provider = UnifiedLLMProvider(self.config)
        
        self.logger.info("Unified LLM Component Generator initialized - no more hanging!")
        
        # Initialize extracted modules (keep existing functionality)
        self.o3_prompt_engine = O3PromptEngine()
        self.response_validator = ResponseValidator()
        self.prompt_engine = PromptEngine()
        self.retry_orchestrator = RetryOrchestrator(
            max_retries=settings.MAX_RETRIES,
            base_delay=settings.RETRY_DELAY
        )
        self.context_builder = ContextBuilder()
        
        # Error handling configuration
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60
        
        # Setup consistent error handler
        self.error_handler = ConsistentErrorHandler("LLMComponentGeneratorUnified")
        
        self.logger.info("Unified LLM Component Generator ready - all modules loaded")

    async def generate_component_implementation_enhanced(
        self, 
        component_type: str,
        component_name: str,
        component_description: str,
        component_config: Dict[str, Any],
        class_name: str,
        system_context: Optional[Dict[str, Any]] = None,
        blueprint: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate component implementation with enhanced context-aware prompting
        Uses unified provider to eliminate hanging issues
        """
        
        # Build enhanced context-aware prompt
        system_prompt = self.prompt_engine.get_system_prompt(
            component_type, 
            self.o3_prompt_engine.get_reasoning_prefix()
        )
        
        # Use enhanced prompting if system context is available
        if system_context:
            user_prompt = self.context_builder.build_context_aware_prompt(
                component_type, component_name, component_description, 
                component_config, class_name, system_context,
                self.prompt_engine.build_component_prompt, blueprint
            )
        else:
            # Fallback to original prompting for backward compatibility
            user_prompt = self.prompt_engine.build_component_prompt(
                component_type, component_name, component_description, 
                component_config, class_name, blueprint
            )
        
        return await self._generate_with_unified_provider(
            system_prompt, user_prompt, component_type, component_name, class_name
        )

    async def generate_component_implementation(
        self, 
        component_type: str,
        component_name: str,
        component_description: str,
        component_config: Dict[str, Any],
        class_name: str,
        blueprint: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete component implementation using unified LLM provider
        Eliminates hanging issues from the old multi-provider system
        """
        
        # Build detailed prompt based on component type
        system_prompt = self.prompt_engine.get_system_prompt(
            component_type, 
            self.o3_prompt_engine.get_reasoning_prefix()
        )
        user_prompt = self.prompt_engine.build_component_prompt(
            component_type, component_name, component_description, 
            component_config, class_name, blueprint
        )
        
        try:
            # Use unified provider with built-in fallback logic
            generated_code = await self._generate_with_unified_provider(
                system_prompt, user_prompt, component_type, component_name, class_name
            )
            
            # Save generated code to a debug file for inspection
            import tempfile
            debug_file = os.path.join(tempfile.gettempdir(), f"debug_{component_name}.py")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            print(f"Debug: Saved generated code to {debug_file}")
            
            return generated_code
            
        except Exception as e:
            raise ComponentGenerationError(
                f"Failed to generate component {component_name} via unified LLM provider: {e}\n"
                f"Component type: {component_type}\n"
                f"NO FALLBACKS - LLM generation is mandatory for ALL components."
            )
    
    async def _generate_with_unified_provider(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        component_type: str, 
        component_name: str, 
        class_name: str
    ) -> str:
        """Generate using unified provider with simplified retry logic"""
        
        # Check circuit breaker
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.logger.error("circuit_breaker_open", {
                "failures": self.circuit_breaker_failures,
                "threshold": self.circuit_breaker_threshold,
                "timeout": self.circuit_breaker_timeout
            })
            raise ComponentGenerationError(
                f"Circuit breaker open: LLM service unavailable "
                f"({self.circuit_breaker_failures} consecutive failures). "
                f"Try again in {self.circuit_breaker_timeout} seconds."
            )
        
        last_exception = None
        validation_feedback = ""
        
        # Log generation start
        generation_id = f"{component_name}_{int(time.time())}"
        self.logger.info("llm_generation_start", {
            "generation_id": generation_id,
            "component_type": component_type,
            "component_name": component_name,
            "class_name": class_name,
            "provider": "unified_llm_provider",
            "model": "automatic_fallback"
        })
        
        max_attempts = self.retry_orchestrator.retry_strategy.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                print(f"LLM call attempt {attempt + 1}/{max_attempts}")
                
                # Build adaptive prompt with validation feedback
                if attempt > 0 and validation_feedback:
                    adapted_user_prompt = self.retry_orchestrator.build_adaptive_prompt(
                        user_prompt, validation_feedback, attempt, 
                        self.o3_prompt_engine.get_reasoning_prefix()
                    )
                else:
                    adapted_user_prompt = user_prompt
                
                # Log attempt
                self.logger.info("llm_generation_attempt", {
                    "generation_id": generation_id,
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "has_validation_feedback": bool(validation_feedback),
                    "prompt_length": len(system_prompt) + len(adapted_user_prompt)
                })
                
                # Create LLM request
                request = LLMRequest(
                    system_prompt=system_prompt,
                    user_prompt=adapted_user_prompt,
                    max_tokens=8192,
                    temperature=0.3
                )
                
                # Make the unified provider call (eliminates hanging!)
                response = await self.llm_provider.generate(request)
                generated_code = response.content
                
                # Post-process the generated code
                generated_code = self._post_process_generated_code(generated_code, component_name)
                
                # Check if LLM followed instructions to generate only the class
                if "import " in generated_code or "from " in generated_code or "class ComposedComponent" in generated_code:
                    # LLM generated boilerplate despite instructions
                    print(f"Warning: LLM generated boilerplate. Extracting component class...")
                    # Try to extract just the component class
                    lines = generated_code.split('\n')
                    class_start = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith(f"class Generated{component_type}_"):
                            class_start = i
                            break
                    
                    if class_start is not None:
                        # Extract from the component class onwards
                        generated_code = '\n'.join(lines[class_start:])
                        print(f"Extracted component class starting at line {class_start}")
                    else:
                        raise ComponentGenerationError(
                            f"LLM did not follow instructions. Generated boilerplate and could not find component class.\n"
                            f"Expected class starting with: class Generated{component_type}_{component_name}"
                        )
                
                # Wrap component with boilerplate
                generated_code = wrap_component_with_boilerplate(
                    component_type=component_type,
                    component_name=component_name,
                    component_code=generated_code
                )
                
                # Validate generated code using extracted validator
                try:
                    self._validate_generated_code(generated_code, component_type, class_name)
                    
                    # Log success
                    self.logger.info("llm_generation_complete", {
                        "generation_id": generation_id,
                        "total_attempts": attempt + 1,
                        "success": True,
                        "provider": response.provider,
                        "model": response.model
                    })
                    
                    # Reset circuit breaker on success
                    self.circuit_breaker_failures = 0
                    print(f"✅ LLM generation successful with {response.provider} after {attempt + 1} attempt(s)")
                    
                    return generated_code
                    
                except ComponentGenerationError as validation_error:
                    # Classify error and prepare for retry
                    error_type = self.retry_orchestrator.classify_error(validation_error)
                    validation_feedback = self.retry_orchestrator.format_validation_feedback(validation_error)
                    print(f"❌ {error_type.value} on attempt {attempt + 1}: {validation_error}")
                    
                    # Log validation failure
                    self.logger.warning("llm_validation_failed", {
                        "generation_id": generation_id,
                        "attempt": attempt + 1,
                        "error_type": error_type.value,
                        "error_message": str(validation_error)
                    })
                    
                    # Check if we should retry
                    if not self.retry_orchestrator.should_retry(error_type, attempt):
                        raise ComponentGenerationError(
                            f"LLM generation failed validation after {attempt + 1} attempts. "
                            f"Final validation error: {validation_error}"
                        )
                    
                    # Wait before next attempt (use asyncio.sleep to avoid blocking!)
                    if attempt < max_attempts - 1:
                        delay = self.retry_orchestrator.get_retry_delay(attempt, error_type)
                        print(f"Retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)  # FIXED: Use asyncio.sleep instead of time.sleep
                    
                    continue
                
            except Exception as e:
                # API or network errors
                error_type = ErrorType.API_ERROR
                last_exception = e
                
                # Log API error
                self.logger.warning("llm_api_error", {
                    "generation_id": generation_id,
                    "attempt": attempt + 1,
                    "error_class": type(e).__name__,
                    "error_message": str(e)
                })
                
                # Increment circuit breaker counter
                self.circuit_breaker_failures += 1
                
                # Check if we should retry
                if not self.retry_orchestrator.should_retry(error_type, attempt):
                    break
                
                # Wait before retrying (use asyncio.sleep to avoid blocking!)
                if attempt < max_attempts - 1:
                    delay = self.retry_orchestrator.get_retry_delay(attempt, error_type)
                    print(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)  # FIXED: Use asyncio.sleep instead of time.sleep
        
        # All retries failed
        self.logger.error("llm_generation_exhausted", {
            "generation_id": generation_id,
            "total_attempts": max_attempts,
            "last_error": str(last_exception)
        })
        
        raise ComponentGenerationError(
            f"Unified LLM provider exhausted all attempts after {max_attempts} tries. "
            f"Last error: {last_exception}. "
            f"NO FALLBACKS AVAILABLE - LLM generation is mandatory."
        )
    
    def _post_process_generated_code(self, generated_code: str, component_name: str) -> str:
        """Post-process generated code to clean up formatting issues"""
        import re
        
        # Handle case where LLM doesn't follow instructions
        print(f"Debug: Raw generated code starts with: {repr(generated_code[:50])}")
        
        # Check if response contains markdown code blocks
        if "```python" in generated_code or "```" in generated_code:
            print("Debug: Detected code block markers in response")
            # Extract code from markdown
            lines = generated_code.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip() == "```python" or (line.strip() == "```" and not in_code):
                    in_code = True
                elif line.strip() == "```" and in_code:
                    in_code = False
                elif in_code:
                    code_lines.append(line)
            if code_lines:
                generated_code = '\n'.join(code_lines)
                print(f"Debug: Extracted {len(code_lines)} lines from code block")
        
        # Debug: Log first few lines of generated code
        print(f"\n--- Generated code preview for {component_name} ---")
        print(f"Total length: {len(generated_code)} chars")
        lines = generated_code.split('\n')[:15]  # Show more lines
        for i, line in enumerate(lines):
            if not line.strip():
                print(f"{i+1}: <empty line>")
            else:
                print(f"{i+1}: {line}")
        lines_count = len(generated_code.split('\n'))
        if lines_count > 15:
            print(f"... ({lines_count - 15} more lines)")
        print("--- End preview ---\n")
        
        return generated_code
    
    def _validate_generated_code(self, code: str, component_type: str, class_name: str) -> None:
        """Validate generated code using extracted validator modules"""
        
        # Use comprehensive functional validation
        if not self.response_validator.validate_functional_implementation(code):
            raise ComponentGenerationError(
                f"Generated code failed functional validation - contains placeholder patterns or insufficient business logic"
            )
        
        # Run component structure validation
        valid, issues = self.response_validator.validate_generated_component(code)
        if not valid:
            raise ComponentGenerationError(
                f"Generated component validation failed: {'; '.join(issues)}"
            )
        
        # Run AST validation
        valid, message = self.response_validator.validate_ast_syntax(code)
        if not valid:
            raise ComponentGenerationError(f"AST validation failed: {message}")
        
        # Run import validation
        valid, missing_imports = self.response_validator.validate_imports(code)
        if not valid:
            raise ComponentGenerationError(
                f"Import validation failed. Missing imports: {', '.join(missing_imports)}"
            )
        
        # Verify it compiles with external Python
        try:
            self.response_validator.validate_with_external_compilation(code)
        except ComponentGenerationError as e:
            raise e
    
    def validate_component_requirements(self, component_spec: Dict[str, Any]) -> bool:
        """Validate component specification before generation"""
        required_fields = ["name", "type", "inputs", "outputs"]
        
        for field in required_fields:
            if field not in component_spec:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate component type
        valid_types = ["Source", "Sink", "Controller", "Transformer", "Model", "Store", "APIEndpoint"]
        if component_spec["type"] not in valid_types:
            self.logger.error(f"Invalid component type: {component_spec['type']}")
            return False
        
        return True