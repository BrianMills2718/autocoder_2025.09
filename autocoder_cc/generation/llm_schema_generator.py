#!/usr/bin/env python3
"""
LLM-Powered Schema Generator
Generates Pydantic schemas for components based on their description and configuration
"""

import json
import re
import time
import random
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from autocoder_cc.observability.structured_logging import get_logger

import os
from dotenv import load_dotenv
from autocoder_cc.core.config import settings
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.capabilities.ast_security_validator import ASTSecurityValidator, ASTSecurityValidationError
from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
from autocoder_cc.llm_providers.base_provider import LLMRequest, LLMResponse

# Load environment variables
load_dotenv()


class SchemaGenerationError(Exception):
    """Raised when schema generation fails - no fallbacks"""
    pass


class LLMSchemaGenerator:
    """
    Generate Pydantic schemas using LLM based on component descriptions
    
    Key Responsibilities:
    - Generate context-aware schemas from component descriptions
    - Create appropriate fields based on component type
    - Ensure schemas are valid Python code
    - Handle domain-specific schema requirements
    """
    
    def __init__(self):
        self.logger = get_logger("LLMSchemaGenerator")
        
        # Initialize multi-provider LLM manager with fallback
        try:
            provider_config = {
                "primary_provider": "gemini",
                "fallback_providers": ["openai", "anthropic"],
                "environment": "development",
                "max_retries": 3,
                "retry_delay": 1.0
            }
            self.llm_manager = MultiProviderManager(provider_config)
            
            # Register providers like llm_component_generator does
            # Import provider classes
            # Only import providers if their modules are available
            providers_imported = []
            
            try:
                from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
                providers_imported.append("openai")
            except ImportError:
                self.logger.warning("OpenAI provider not available - install openai module")
                OpenAIProvider = None
            
            try:
                from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
                providers_imported.append("anthropic")
            except ImportError:
                self.logger.warning("Anthropic provider not available - install anthropic module")
                AnthropicProvider = None
                
            try:
                from autocoder_cc.llm_providers.gemini_provider import GeminiProvider
                providers_imported.append("gemini")
            except ImportError:
                self.logger.warning("Gemini provider not available - install google-generativeai module")
                GeminiProvider = None
            
            # Register providers based on configuration
            if os.getenv("OPENAI_API_KEY") and OpenAIProvider is not None:
                try:
                    openai_config = {
                        "api_key": os.getenv("OPENAI_API_KEY"),
                        "default_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                    }
                    openai_provider = OpenAIProvider(openai_config)
                    self.llm_manager.registry.register_provider(openai_provider)
                    self.logger.info("Registered OpenAI provider")
                except Exception as e:
                    self.logger.warning(f"Failed to register OpenAI provider: {e}")
                    
            if os.getenv("ANTHROPIC_API_KEY") and AnthropicProvider is not None:
                try:
                    anthropic_config = {"api_key": os.getenv("ANTHROPIC_API_KEY")}
                    anthropic_provider = AnthropicProvider(anthropic_config)
                    self.llm_manager.registry.register_provider(anthropic_provider)
                    self.logger.info("Registered Anthropic provider")
                except Exception as e:
                    self.logger.warning(f"Failed to register Anthropic provider: {e}")
                    
            if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and GeminiProvider is not None:
                try:
                    gemini_config = {"api_key": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")}
                    gemini_provider = GeminiProvider(gemini_config)
                    self.llm_manager.registry.register_provider(gemini_provider)
                    self.logger.info("Registered Gemini provider")
                except Exception as e:
                    self.logger.warning(f"Failed to register Gemini provider: {e}")
            
            # Ensure at least one provider is available
            if not providers_imported:
                raise SchemaGenerationError(
                    "No LLM providers available. Install at least one of: openai, anthropic, google-generativeai"
                )
            
            self.logger.info(f"Available LLM providers: {providers_imported}")
                    
        except Exception as e:
            raise SchemaGenerationError(f"Failed to initialize LLM providers: {e}")
        
        # Error handling configuration
        self.max_retries = settings.MAX_RETRIES if hasattr(settings, 'MAX_RETRIES') else 3
        self.retry_delay = settings.RETRY_DELAY if hasattr(settings, 'RETRY_DELAY') else 2
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60  # seconds
        
        # Setup consistent error handler
        self.error_handler = ConsistentErrorHandler("LLMSchemaGenerator")
        
    def generate_schema(self, 
                       component_name: str,
                       component_type: str,
                       description: str,
                       configuration: Dict[str, Any],
                       schema_type: str) -> str:
        """
        Generate a Pydantic schema using LLM with self-healing
        
        Args:
            component_name: Name of the component (e.g., "inventory_api")
            component_type: Type of component (e.g., "APIEndpoint")
            description: Natural language description of the component
            configuration: Component configuration from blueprint
            schema_type: Type of schema to generate (e.g., "request", "response")
            
        Returns:
            Python code for the Pydantic schema class
            
        Raises:
            SchemaGenerationError: If schema generation fails after healing attempts
        """
        max_healing_attempts = 3
        last_error = None
        last_generated_code = None
        
        for healing_attempt in range(max_healing_attempts):
            try:
                # Build comprehensive prompt
                prompt = self._build_schema_prompt(
                    component_name, component_type, description, 
                    configuration, schema_type
                )
                
                # Add healing context if this is a retry
                if healing_attempt > 0 and last_error:
                    healing_prompt = self._add_healing_context(prompt, last_error, last_generated_code)
                    prompt = healing_prompt
                
                # Generate schema using LLM
                schema_code = self._generate_with_llm(prompt)
                last_generated_code = schema_code  # Save for debugging
                
                # Validate and clean the generated code
                cleaned_code = self._validate_and_clean_schema(schema_code)
                
                self.logger.info(f"✅ Generated {schema_type} schema for {component_name} (attempt {healing_attempt + 1})")
                return cleaned_code
                
            except ValueError as e:
                last_error = str(e)
                self.logger.warning(f"Schema validation failed (attempt {healing_attempt + 1}/{max_healing_attempts}): {e}")
                
                # If this is a syntax error, try to heal it
                if "syntax error" in str(e).lower() and healing_attempt < max_healing_attempts - 1:
                    self.logger.info("Attempting to heal syntax error in next iteration")
                    continue
                elif healing_attempt == max_healing_attempts - 1:
                    # Final attempt failed - include the generated code in error
                    raise SchemaGenerationError(
                        f"Failed to generate {schema_type} schema for {component_name} after {max_healing_attempts} attempts: {str(e)}\n"
                        f"Last generated code:\n{last_generated_code}\n"
                        f"NO FALLBACKS - this requires LLM configuration"
                    )
            except Exception as e:
                # Non-validation errors should fail immediately with context
                raise SchemaGenerationError(
                    f"Failed to generate {schema_type} schema for {component_name}: {str(e)}\n"
                    f"Generated code (if any):\n{last_generated_code if last_generated_code else 'No code generated'}\n"
                    f"NO FALLBACKS - this requires LLM configuration"
                )
    
    def _build_schema_prompt(self, 
                           component_name: str,
                           component_type: str,
                           description: str,
                           configuration: Dict[str, Any],
                           schema_type: str) -> str:
        """Build a comprehensive prompt for schema generation"""
        
        # Convert component_name to PascalCase for class name
        class_base = ''.join(word.capitalize() for word in component_name.split('_'))
        
        # Map schema type to appropriate class name
        schema_class_mapping = {
            'config': f"{class_base}ConfigSchema",
            'request': f"{class_base}RequestSchema",
            'response': f"{class_base}ResponseSchema",
            'input': f"{class_base}InputSchema",
            'output': f"{class_base}OutputSchema",
            'data': f"{class_base}DataSchema",
            'entity': f"{class_base}EntitySchema",
            'query': f"{class_base}QuerySchema"
        }
        
        schema_class_name = schema_class_mapping.get(schema_type, f"{class_base}Schema")
        
        prompt = f"""Generate a Pydantic schema for a {component_type} component.

Component Details:
- Name: {component_name}
- Type: {component_type}
- Description: {description}
- Configuration: {json.dumps(configuration, indent=2) if configuration else "None"}

Generate a Pydantic schema named: {schema_class_name}
Schema Type: {schema_type}

Requirements:
1. Import statements must include: from pydantic import BaseModel, Field, validator
2. Use appropriate field types based on the component's purpose
3. Include field descriptions using Field(description="...")
4. Add validators where appropriate for data integrity
5. For {schema_type} schema, include fields that make sense for {description}

Guidelines by schema type:
- config: Configuration parameters the component needs
- request: Data structure for incoming API requests
- response: Data structure for API responses
- input/output: Data flowing through the component
- entity: Domain objects stored/retrieved
- query: Parameters for querying data

Generate ONLY the Python code for the Pydantic model class.
Do not include explanations or markdown formatting.
The code should be immediately executable Python.

CRITICAL: Do not use 'pass' statements anywhere in the code. 
All methods and validators must have complete implementations with actual logic.
If a validator or method has no logic, simply omit it entirely.

Example format:
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class {schema_class_name}(BaseModel):
    \"\"\"Schema description here\"\"\"
    
    field_name: str = Field(..., description="Field description")
    optional_field: Optional[int] = Field(None, description="Optional field")
    
    @validator('field_name')
    def validate_field_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("field_name must be a non-empty string")
        return v
"""
        
        return prompt
    
    def _add_healing_context(self, original_prompt: str, error: str, failed_code: str) -> str:
        """Add healing context to the prompt based on the previous error"""
        healing_instructions = f"""
IMPORTANT: The previous attempt to generate this schema failed with the following error:
{error}

The code that failed was:
```python
{failed_code}
```

Please fix the issue and generate a correct Pydantic schema. Common issues to check:
1. Unterminated string literals - ensure all strings are properly closed
2. Missing colons after class/method definitions
3. Incorrect indentation
4. Missing imports
5. Invalid field definitions

Generate the corrected schema code:
"""
        return healing_instructions + "\n\n" + original_prompt
    
    def _generate_with_llm(self, prompt: str) -> str:
        """Generate schema code using the LLM with robust error handling"""
        return self._call_llm_with_retries(prompt)
    
    @handle_errors("LLMSchemaGenerator", operation="llm_call")
    def _call_llm_with_retries(self, prompt: str) -> str:
        """Call LLM with robust error handling, retries, and circuit breaker."""
        
        # Check circuit breaker
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            raise SchemaGenerationError(
                f"Circuit breaker open: LLM service unavailable "
                f"({self.circuit_breaker_failures} consecutive failures). "
                f"Try again in {self.circuit_breaker_timeout} seconds."
            )
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"LLM schema generation attempt {attempt + 1}/{self.max_retries + 1}")
                
                # Use multi-provider manager with fallback
                system_message = ("You are a Python developer specializing in Pydantic schemas. "
                                "Generate clean, well-structured Pydantic model classes based on requirements. "
                                "CRITICAL: Respond with ONLY Python code. Do NOT include any explanatory text or markdown formatting. "
                                "Do NOT wrap code in ```python``` blocks. Start directly with imports and class definition.")
                
                # Create LLM request
                request = LLMRequest(
                    system_prompt=system_message,
                    user_prompt=prompt,
                    max_tokens=8192,  # Increased from 2000 to match component generator
                    temperature=0.1
                )
                
                # Try to generate with fallback between providers
                import asyncio
                try:
                    # Check if we're already in an async context
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're already in an async context, need to run in a separate thread
                        import concurrent.futures
                        import threading
                        
                        def run_async_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self.llm_manager.generate(request))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            response = future.result(timeout=30)
                    else:
                        # No event loop running, use asyncio.run
                        response: LLMResponse = asyncio.run(self.llm_manager.generate(request))
                except RuntimeError as e:
                    if "asyncio.run() cannot be called from a running event loop" in str(e):
                        # Fallback: run in a separate thread
                        import concurrent.futures
                        import threading
                        
                        def run_async_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self.llm_manager.generate(request))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            response = future.result(timeout=30)
                    else:
                        raise
                
                # Validate response
                if not response.content or not response.content.strip():
                    raise SchemaGenerationError("Empty response from LLM")
                
                generated_code = response.content.strip()
                
                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0
                
                return generated_code
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"LLM schema generation attempt {attempt + 1} failed: {e}")
                self.logger.warning(f"Exception type: {type(e).__name__}")
                self.logger.warning(f"Full exception details: {repr(e)}")
                
                # Increment circuit breaker counter
                self.circuit_breaker_failures += 1
                
                # Handle specific errors with fallback logic
                if "rate limit" in str(e).lower():
                    if attempt < self.max_retries:
                        # Longer delay for rate limiting
                        delay = self.retry_delay * (3 ** attempt) + random.uniform(0, 2)
                        self.logger.info(f"Rate limited - retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                elif "timeout" in str(e).lower():
                    if attempt < self.max_retries:
                        # Shorter delay for timeouts
                        delay = self.retry_delay * (1.5 ** attempt) + random.uniform(0, 0.5)
                        self.logger.info(f"Timeout - retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                elif attempt < self.max_retries:
                    # Standard exponential backoff for other errors
                    delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    # All retries exhausted
                    break
        
        # FAIL HARD - NO FALLBACKS, NO TEMPLATES
        # If we exhaust all retries with all LLM providers, the system must fail
        self.logger.error(f"LLM service completely unavailable after {self.max_retries + 1} attempts with all providers")
        self.logger.error(f"Last error: {last_exception}")
        
        # All attempts failed - FAIL HARD AND LOUD
        raise SchemaGenerationError(
            f"CRITICAL: LLM service unavailable after {self.max_retries + 1} attempts. "
            f"All providers (gemini, openai, anthropic) failed or unavailable. "
            f"Last error: {last_exception}\n"
            f"NO FALLBACKS - System requires working LLM provider for schema generation. "
            f"Check API keys and provider status."
        )
    
    
    def _validate_and_clean_schema(self, schema_code: str) -> str:
        """Validate and clean generated schema code with security validation"""
        # Debug output - use logger instead of print
        self.logger.debug(f"Raw generated code starts with: {repr(schema_code[:50])}")
        
        # Remove any markdown formatting if present
        code = schema_code.strip()
        
        # Check if response contains markdown code blocks
        if "```python" in code or "```" in code:
            self.logger.debug("Detected code block markers in response")
            # Extract code from markdown
            lines = code.split('\n')
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
                code = '\n'.join(code_lines)
                self.logger.debug(f"Extracted {len(code_lines)} lines from code block")
        
        # Check if response starts with explanatory text
        first_line = code.strip().split('\n')[0] if code.strip() else ""
        if first_line and not (first_line.startswith(('import ', 'from ', '#', '"""')) or first_line.strip() == ""):
            self.logger.debug(f"Detected explanatory text at start: {repr(first_line[:50])}")
            # Try to find where the actual code starts
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ', '#', '"""', 'class ')):
                    code = '\n'.join(lines[i:])
                    self.logger.debug(f"Found code starting at line {i+1}")
                    break
            
        code = code.strip()
        
        # Basic validation - check for class definition
        if not re.search(r'class\s+\w+\s*\(BaseModel\)', code):
            raise ValueError("Generated code does not contain a valid Pydantic model class")
            
        # Check for imports
        if 'from pydantic import' not in code and 'import pydantic' not in code:
            # Add basic imports if missing
            code = "from pydantic import BaseModel, Field\nfrom typing import Optional, List, Dict, Any\n\n" + code
        
        # Validate Python syntax by attempting to compile
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            # Include a snippet of the problematic code for debugging
            error_line = e.lineno if hasattr(e, 'lineno') else None
            code_snippet = ""
            if error_line:
                lines = code.split('\n')
                start = max(0, error_line - 3)
                end = min(len(lines), error_line + 2)
                code_snippet = "\n".join(f"{i+1}: {lines[i]}" for i in range(start, end))
            raise ValueError(f"Generated code has syntax errors: {str(e)}\nCode around error:\n{code_snippet}")
        
        # AST Security Validation for LLM-generated code (with graceful handling)
        try:
            # Use permissive mode for schema code - schemas typically use safe Python constructs
            security_validator = ASTSecurityValidator(strict_mode=False)
            violations = security_validator.validate_code(code)
            
            # Check for critical violations only
            critical_violations = [v for v in violations if v.severity == "critical"]
            
            if critical_violations:
                self.logger.error(f"Critical security violations in schema: {[v.description for v in critical_violations]}")
                raise ValueError(
                    f"Generated schema has critical security violations: "
                    f"{[v.description for v in critical_violations[:3]]}"
                )
            
            # Allow non-critical violations in schema code (like IfExp)
            if violations:
                safe_violations = ["IfExp", "ListComp", "DictComp", "Lambda"]
                non_critical_safe = [v for v in violations if any(safe in v.description for safe in safe_violations)]
                if non_critical_safe:
                    self.logger.info(f"Allowing safe constructs in schema: {[v.description for v in non_critical_safe]}")
            
            self.logger.info(f"AST security validation passed for generated schema")
            
        except ASTSecurityValidationError as e:
            # For permissive mode, this should rarely happen, but handle gracefully
            critical_only = [v for v in e.violations if v.severity == "critical"]
            if critical_only:
                self.logger.error(f"Critical AST security validation failed: {e}")
                raise ValueError(
                    f"Generated code has critical security violations. "
                    f"Found {len(critical_only)} critical issues: "
                    f"{[v.description for v in critical_only[:3]]}"
                )
            else:
                # Only non-critical violations - allow with warning
                self.logger.warning(f"Non-critical security validation issues: {[v.description for v in e.violations]}")
                self.logger.info("Proceeding with schema generation - no critical security issues found")
        
        return code
    
    def generate_schemas_for_component(self,
                                     component_name: str,
                                     component_type: str,
                                     description: str,
                                     configuration: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all necessary schemas for a component based on its type
        
        Returns:
            Dictionary mapping schema names to generated Python code
        """
        schemas = {}
        
        # All components need a config schema
        schemas[f"{component_name}_config"] = self.generate_schema(
            component_name, component_type, description, configuration, "config"
        )
        
        # Type-specific schemas
        if component_type == "APIEndpoint":
            schemas[f"{component_name}_request"] = self.generate_schema(
                component_name, component_type, description, configuration, "request"
            )
            schemas[f"{component_name}_response"] = self.generate_schema(
                component_name, component_type, description, configuration, "response"
            )
            
        elif component_type == "Source":
            schemas[f"{component_name}_output"] = self.generate_schema(
                component_name, component_type, description, configuration, "output"
            )
            
        elif component_type == "Sink":
            schemas[f"{component_name}_input"] = self.generate_schema(
                component_name, component_type, description, configuration, "input"
            )
            
        elif component_type == "Transformer":
            schemas[f"{component_name}_input"] = self.generate_schema(
                component_name, component_type, description, configuration, "input"
            )
            schemas[f"{component_name}_output"] = self.generate_schema(
                component_name, component_type, description, configuration, "output"
            )
            
        elif component_type == "Store":
            schemas[f"{component_name}_entity"] = self.generate_schema(
                component_name, component_type, description, configuration, "entity"
            )
            schemas[f"{component_name}_query"] = self.generate_schema(
                component_name, component_type, description, configuration, "query"
            )
            
        elif component_type in ["Controller", "StreamProcessor"]:
            schemas[f"{component_name}_input"] = self.generate_schema(
                component_name, component_type, description, configuration, "input"
            )
            schemas[f"{component_name}_output"] = self.generate_schema(
                component_name, component_type, description, configuration, "output"
            )
        
        return schemas