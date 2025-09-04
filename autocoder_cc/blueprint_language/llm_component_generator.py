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
from autocoder_cc.llm_providers.structured_outputs import GeneratedComponent, ComponentGenerationRequest, ComponentType

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
    - Uses UnifiedLLMProvider with direct LiteLLM integration
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
        
        # Use provided config or default with fallback enabled
        self.config = config or {}
        # Enable fallback by default for robustness
        if 'enable_fallback' not in self.config:
            self.config['enable_fallback'] = True
        
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
        
        # Error handling configuration - DISABLED BY DEFAULT
        self.circuit_breaker_enabled = False  # DISABLED - FAIL FAST
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 1  # FAIL IMMEDIATELY
        self.circuit_breaker_timeout = float('inf')  # No timeout
        
        # Setup consistent error handler
        self.error_handler = ConsistentErrorHandler("LLMComponentGeneratorUnified")
        
        self.logger.info("Unified LLM Component Generator ready - all modules loaded")

    async def generate_component_structured(
        self,
        component_type: str,
        component_name: str,
        component_description: str,
        component_config: Dict[str, Any],
        class_name: str,
        inputs: Optional[list] = None,
        outputs: Optional[list] = None,
        system_context: Optional[str] = None
    ) -> str:
        """
        Generate component using Gemini structured output for better reliability
        """
        self.logger.info(f"Generating component with structured output: {component_name} ({component_type})")
        
        # Map component type string to enum
        try:
            component_type_enum = ComponentType(component_type)
        except ValueError:
            # Fallback to most similar type
            component_type_enum = ComponentType.TRANSFORMER
        
        # Create structured request
        structured_request = ComponentGenerationRequest(
            component_type=component_type_enum,
            component_name=component_name,
            component_description=component_description,
            configuration=component_config,
            inputs=inputs or [],
            outputs=outputs or [],
            system_context=system_context
        )
        
        # Create prompt
        system_prompt = f"""You are an expert Python developer generating a component for the AutoCoder system.
Generate a structured component implementation following the exact schema provided.

Component Requirements:
- Type: {component_type}
- Name: {component_name}
- Description: {component_description}
- Configuration: {json.dumps(component_config, indent=2)}

The component should:
1. Properly handle the setup() method for initialization
2. Implement the process() method for the main logic
3. Include proper error handling and logging
4. Follow async/await patterns where appropriate
5. Use self.config to access configuration values
"""

        user_prompt = f"""Generate the implementation for this component:

{json.dumps(structured_request.dict(), indent=2)}

Focus on creating practical, working code that matches the component's purpose.
The base class (ComposedComponent) provides send_to_output() and receive_from_input() methods.
"""

        try:
            # Use structured output with Gemini
            request = LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=8192,
                temperature=0.3,
                response_schema=GeneratedComponent  # Use structured output!
            )
            
            response = await self.llm_provider.generate(request)
            
            # Parse structured response
            component_data = json.loads(response.content)
            
            # Build the component code from structured data
            return self._build_component_from_structured(component_data, class_name)
            
        except Exception as e:
            self.logger.error(f"Structured generation failed: {e}, falling back to regular generation")
            # Fallback to regular generation
            return await self.generate_component_implementation(
                component_type, component_name, component_description,
                component_config, class_name
            )
    
    def _build_component_from_structured(self, data: dict, class_name: str) -> str:
        """Build component code from structured data"""
        lines = []
        
        # Add additional imports if specified
        if data.get('additional_imports'):
            for imp in data['additional_imports']:
                lines.append(imp)
            lines.append('')
        
        # Class definition
        lines.append(f"class {class_name}({data.get('base_class', 'ComposedComponent')}):")
        
        # Docstring
        docstring = data.get('docstring', 'Generated component')
        lines.append(f'    """{docstring}"""')
        lines.append('')
        
        # __init__ method
        lines.append('    def __init__(self, name: str, config: Dict[str, Any]):')
        lines.append('        super().__init__(name, config)')
        
        # Add init attributes - handle both dict and string formats
        init_attrs = data.get('init_attributes', {})
        if isinstance(init_attrs, str) and init_attrs:
            try:
                import json
                init_attrs = json.loads(init_attrs)
            except json.JSONDecodeError:
                init_attrs = {}
        
        if isinstance(init_attrs, dict):
            for attr, value in init_attrs.items():
                if isinstance(value, str):
                    lines.append(f'        self.{attr} = "{value}"')
                else:
                    lines.append(f'        self.{attr} = {value}')
        lines.append('')
        
        # setup method
        lines.append('    async def setup(self):')
        lines.append('        """Initialize component resources"""')
        setup_body = data.get('setup_body', 'pass')
        # If the body already contains indentation, don't add more
        if setup_body.strip() and not setup_body.startswith(' '):
            # No indentation in body, add it
            for line in setup_body.split('\n'):
                lines.append(f'        {line}' if line.strip() else '')
        else:
            # Body already has indentation, use as-is
            for line in setup_body.split('\n'):
                lines.append(line if line else '')
        lines.append('')
        
        # process method
        lines.append('    async def process(self):')
        lines.append('        """Main processing logic"""')
        process_body = data.get('process_body', 'pass')
        # If the body already contains indentation, don't add more
        if process_body.strip() and not process_body.startswith(' '):
            # No indentation in body, add it
            for line in process_body.split('\n'):
                lines.append(f'        {line}' if line.strip() else '')
        else:
            # Body already has indentation, use as-is
            for line in process_body.split('\n'):
                lines.append(line if line else '')
        lines.append('')
        
        # cleanup method if provided
        if data.get('cleanup_body'):
            lines.append('    async def cleanup(self):')
            lines.append('        """Cleanup resources"""')
            cleanup_body = data['cleanup_body']
            # If the body already contains indentation, don't add more
            if cleanup_body.strip() and not cleanup_body.startswith(' '):
                # No indentation in body, add it
                for line in cleanup_body.split('\n'):
                    lines.append(f'        {line}' if line.strip() else '')
            else:
                # Body already has indentation, use as-is
                for line in cleanup_body.split('\n'):
                    lines.append(line if line else '')
            lines.append('')
        
        # health_check method if provided
        if data.get('health_check_body'):
            lines.append('    async def health_check(self) -> bool:')
            lines.append('        """Check component health"""')
            health_check_body = data['health_check_body']
            # If the body already contains indentation, don't add more
            if health_check_body.strip() and not health_check_body.startswith(' '):
                # No indentation in body, add it
                for line in health_check_body.split('\n'):
                    lines.append(f'        {line}' if line.strip() else '')
            else:
                # Body already has indentation, use as-is
                for line in health_check_body.split('\n'):
                    lines.append(line if line else '')
            lines.append('')
        
        # Helper methods if provided
        if data.get('helper_methods'):
            for method in data['helper_methods']:
                # Method signature - handle both 'signature' and 'parameters' formats
                if method.get('signature'):
                    # Use provided signature directly
                    signature = method['signature']
                    if not signature.startswith('self'):
                        signature = 'self, ' + signature
                else:
                    # Build from parameters list
                    params = method.get('parameters', ['self'])
                    if isinstance(params, list):
                        signature = ', '.join(params)
                    else:
                        signature = str(params)
                
                async_prefix = 'async ' if method.get('async_method', False) else ''
                lines.append(f'    {async_prefix}def {method["name"]}({signature}):')
                
                # Docstring
                if method.get('docstring'):
                    lines.append(f'        """{method["docstring"]}"""')
                
                # Method body
                method_body = method['body']
                # If the body already contains indentation, don't add more
                if method_body.strip() and not method_body.startswith(' '):
                    # No indentation in body, add it
                    for line in method_body.split('\n'):
                        lines.append(f'        {line}' if line.strip() else '')
                else:
                    # Body already has indentation, use as-is
                    for line in method_body.split('\n'):
                        lines.append(line if line else '')
                lines.append('')
        
        return '\n'.join(lines)

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
        
        # Check circuit breaker if enabled
        if self.circuit_breaker_enabled and self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.logger.error("circuit_breaker_open", {
                "failures": self.circuit_breaker_failures,
                "threshold": self.circuit_breaker_threshold,
                "timeout": self.circuit_breaker_timeout,
                "enabled": self.circuit_breaker_enabled
            })
            raise ComponentGenerationError(
                f"Circuit breaker open: LLM service unavailable "
                f"({self.circuit_breaker_failures} consecutive failures). "
                f"Circuit breaker is ENABLED - set circuit_breaker_enabled=False to disable."
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
                
                # Create LLM request - use original settings to see real issues
                request = LLMRequest(
                    system_prompt=system_prompt,
                    user_prompt=adapted_user_prompt,
                    max_tokens=8192,  # Original setting - no patches
                    temperature=0.3
                )
                
                # Make the unified provider call with timeout protection (eliminates hanging!)
                # Increased timeout to allow for slower LLM responses
                generation_timeout = float(os.getenv('COMPONENT_GENERATION_TIMEOUT', '300.0'))  # Default 5 minutes
                response = await asyncio.wait_for(
                    self.llm_provider.generate(request), 
                    timeout=generation_timeout
                )
                
                # Check if response and content are valid
                if not response:
                    raise ComponentGenerationError(f"LLM provider returned no response for component {component_name}")
                
                if not hasattr(response, 'content') or response.content is None:
                    raise ComponentGenerationError(
                        f"LLM provider returned response without content for component {component_name}. "
                        f"Response type: {type(response)}, Response: {response}"
                    )
                
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
                
            except asyncio.TimeoutError:
                # Handle LLM call timeout specifically
                error_type = ErrorType.API_ERROR
                last_exception = ComponentGenerationError(
                    f"LLM call timed out after 60 seconds for component {component_name}. "
                    f"This indicates a slow LLM provider or network issue."
                )
                print(f"⏰ TIMEOUT: Component {component_name} generation timed out after 60 seconds")
                
                # Log timeout error
                self.logger.warning("llm_timeout_error", {
                    "generation_id": generation_id,
                    "attempt": attempt + 1,
                    "component_name": component_name,
                    "timeout_seconds": 60
                })
                
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
        """Post-process generated code to clean up formatting issues and fix anti-patterns"""
        import re
        import ast
        import astor
        from autocoder_cc.blueprint_language.pattern_detector import AntiPatternDetector
        from autocoder_cc.healing.ast_transformers.message_envelope_transformer import MessageEnvelopeTransformer
        from autocoder_cc.healing.ast_transformers.communication_method_transformer import CommunicationMethodTransformer
        
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
        
        # CRITICAL FIX: Strip import statements that LLM adds despite instructions
        lines = generated_code.split('\n')
        cleaned_lines = []
        class_started = False
        
        for line in lines:
            # Skip import statements before class definition
            if not class_started:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    print(f"Debug: Stripping unauthorized import: {line.strip()}")
                    continue
                elif line.strip().startswith('class Generated'):
                    class_started = True
                    cleaned_lines.append(line)
                elif not line.strip():  # Keep empty lines
                    continue
                else:
                    # Keep any non-import, non-empty lines before class
                    if line.strip():
                        cleaned_lines.append(line)
            else:
                # After class starts, keep everything
                cleaned_lines.append(line)
        
        generated_code = '\n'.join(cleaned_lines)
        
        # CRITICAL FIX: Auto-repair common syntax issues from truncation
        generated_code = self._auto_repair_syntax(generated_code)
        
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
        
        # Apply pattern detection and AST transformation BEFORE returning
        detector = AntiPatternDetector()
        anti_patterns = detector.detect_anti_patterns(generated_code)
        
        if anti_patterns:
            print(f"Debug: Detected {len(anti_patterns)} anti-patterns in generated code, applying fixes...")
            for pattern, message in anti_patterns:
                print(f"  - {message}")
            
            try:
                # Parse and apply AST transformers
                tree = ast.parse(generated_code)
                tree = MessageEnvelopeTransformer().visit(tree)
                tree = CommunicationMethodTransformer().visit(tree)
                generated_code = astor.to_source(tree)
                
                # Verify fixes
                remaining = detector.detect_anti_patterns(generated_code)
                if remaining:
                    print(f"Debug: Warning - {len(remaining)} anti-patterns remain after transformation")
                else:
                    print(f"Debug: ✅ All anti-patterns fixed successfully")
            except Exception as e:
                print(f"Debug: Failed to apply AST transformers: {e}")
        
        return generated_code
    
    def _auto_repair_syntax(self, code: str) -> str:
        """Auto-repair common syntax issues from LLM generation"""
        import ast
        
        # First, try to parse to see if there are syntax errors
        try:
            ast.parse(code)
            return code  # No syntax errors, return as-is
        except SyntaxError as e:
            print(f"Debug: Syntax error detected: {e}")
            
        lines = code.split('\n')
        
        # Fix 1: Balance parentheses, brackets, and braces
        open_parens = code.count('(') - code.count(')')
        open_brackets = code.count('[') - code.count(']')
        open_braces = code.count('{') - code.count('}')
        
        if open_parens > 0:
            print(f"Debug: Adding {open_parens} closing parentheses")
            lines.append(')' * open_parens)
        if open_brackets > 0:
            print(f"Debug: Adding {open_brackets} closing brackets")
            lines.append(']' * open_brackets)
        if open_braces > 0:
            print(f"Debug: Adding {open_braces} closing braces")
            lines.append('}' * open_braces)
        
        # Fix 2: Check for unterminated strings and fix them
        for i, line in enumerate(lines):
            # Count quotes that aren't escaped
            single_quotes = 0
            double_quotes = 0
            triple_single = line.count("'''")
            triple_double = line.count('"""')
            
            # Remove triple quotes from count
            line_no_triple = line.replace("'''", "").replace('"""', "")
            
            j = 0
            while j < len(line_no_triple):
                if line_no_triple[j] == '"' and (j == 0 or line_no_triple[j-1] != '\\'):
                    double_quotes += 1
                elif line_no_triple[j] == "'" and (j == 0 or line_no_triple[j-1] != '\\'):
                    single_quotes += 1
                j += 1
            
            # Fix unterminated strings
            if single_quotes % 2 != 0:
                print(f"Debug: Fixing unterminated single quote on line {i+1}")
                lines[i] += "'"
            if double_quotes % 2 != 0:
                print(f"Debug: Fixing unterminated double quote on line {i+1}")
                lines[i] += '"'
            if triple_single % 2 != 0:
                print(f"Debug: Fixing unterminated triple single quote on line {i+1}")
                lines[i] += "'''"
            if triple_double % 2 != 0:
                print(f"Debug: Fixing unterminated triple double quote on line {i+1}")
                lines[i] += '"""'
        
        # Fix 3: Ensure the code ends properly if truncated
        if lines and not lines[-1].strip().endswith((':',  ')', ']', '}', 'pass', 'return', 'raise', 'break', 'continue')):
            # Add a pass statement to complete any hanging blocks
            if lines[-1].strip():
                print("Debug: Adding 'pass' to complete truncated code")
                lines.append("        pass")  # Assume some indentation
        
        repaired_code = '\n'.join(lines)
        
        # Verify the repair worked
        try:
            ast.parse(repaired_code)
            print("Debug: Syntax auto-repair successful!")
        except SyntaxError as e:
            print(f"Debug: Syntax still has issues after repair: {e}")
            # Return original if repair made it worse
            try:
                ast.parse(code)
                return code  # Return original if it's valid
            except:
                pass  # Return repaired version
        
        return repaired_code
    
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