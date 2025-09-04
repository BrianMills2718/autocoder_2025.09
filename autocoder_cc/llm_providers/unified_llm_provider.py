#!/usr/bin/env python3
"""
Unified LLM Provider - Simplified replacement for multi-provider system
Based on universal_model_tester working pattern to eliminate hanging issues

Replaces the problematic thread executor pattern with direct LiteLLM calls
that handle timeouts and cancellation correctly.
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from dotenv import load_dotenv
from litellm import completion, acompletion
import litellm

# Phase 2B: Import centralized timeout management
from autocoder_cc.core.timeout_manager import get_timeout_manager, TimeoutType, TimeoutError

from .base_provider import LLMRequest, LLMResponse, LLMProviderError

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    name: str
    litellm_name: str
    supports_structured_output: bool
    max_tokens: int

class UnifiedLLMProvider:
    """
    Unified LLM provider using LiteLLM for all models
    Eliminates the hanging issues from thread executor patterns
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize unified provider with OPTIONAL fallback logic"""
        load_dotenv()
        
        self.config = config or {}
        self.timeout = 3600  # 1 hour timeout (effectively no timeout for LLM calls)
        
        # FALLBACK DISABLED BY DEFAULT - FAIL FAST
        self.enable_fallback = self.config.get('enable_fallback', False)
        
        # Load API keys from environment
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY'), 
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
        
        # Define model configurations (similar to universal_model_tester)
        self.models = self._load_model_configs()
        
        # Configure LiteLLM with API keys
        self._configure_litellm()
        
        # Determine fallback sequence based on configuration
        if self.enable_fallback:
            # Use full fallback sequence if enabled
            self.fallback_sequence = [
                'gemini_2_5_flash',  # Primary: Fast and reliable
                'openai_gpt4o_mini', # Fallback 1: OpenAI o4-mini equivalent
                'claude_sonnet_4'    # Fallback 2: Anthropic Claude
            ]
            logger.info("Fallback ENABLED - will try multiple models on failure")
        else:
            # FAIL FAST - only use primary model
            primary_model = self.config.get('primary_model', 'gemini_2_5_flash')
            self.fallback_sequence = [primary_model]
            logger.info(f"Fallback DISABLED - will only use {primary_model} (fail fast on error)")
        
        logger.info(f"Unified LLM Provider initialized with models: {list(self.models.keys())}")
    
    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """Load model configurations optimized for autocoder usage"""
        return {
            'gemini_2_5_flash': ModelConfig(
                name='gemini_2_5_flash',
                litellm_name='gemini/gemini-2.5-flash',
                supports_structured_output=True,
                max_tokens=8192
            ),
            'openai_gpt4o_mini': ModelConfig(
                name='openai_gpt4o_mini', 
                litellm_name='gpt-4o-mini',
                supports_structured_output=True,
                max_tokens=16384
            ),
            'claude_sonnet_4': ModelConfig(
                name='claude_sonnet_4',
                litellm_name='claude-3-5-sonnet-20241022',
                supports_structured_output=True,
                max_tokens=4096
            )
        }
    
    def _configure_litellm(self):
        """Configure LiteLLM with API keys"""
        if self.api_keys['openai']:
            os.environ['OPENAI_API_KEY'] = self.api_keys['openai']
        if self.api_keys['gemini']:
            os.environ['GEMINI_API_KEY'] = self.api_keys['gemini']
        if self.api_keys['anthropic']:
            os.environ['ANTHROPIC_API_KEY'] = self.api_keys['anthropic']
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response with automatic fallback
        Uses the proven working pattern from universal_model_tester
        """
        start_time = time.time()
        
        # Try each model in fallback sequence
        last_error = None
        
        for attempt, model_name in enumerate(self.fallback_sequence):
            if model_name not in self.models:
                logger.warning(f"Model {model_name} not configured, skipping")
                continue
                
            model_config = self.models[model_name]
            
            try:
                logger.info(f"Attempt {attempt + 1}: Trying {model_config.litellm_name}")
                
                # Prepare messages for LiteLLM
                messages = [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt}
                ]
                
                # Prepare completion params
                params = {
                    "model": model_config.litellm_name,
                    "messages": messages,
                    "max_tokens": request.max_tokens or model_config.max_tokens,
                    "temperature": request.temperature or 0.3,
                    "timeout": self.timeout
                }
                
                # Handle JSON mode if requested
                if request.json_mode and model_config.supports_structured_output:
                    params["response_format"] = {"type": "json_object"}
                
                # Phase 2B: Use centralized timeout management for LLM calls
                timeout_manager = get_timeout_manager()
                operation_id = f"llm_call_{model_config.name}_{int(time.time() * 1000)}"
                
                async def make_llm_call():
                    return await acompletion(**params)
                
                # Make the LiteLLM call with centralized timeout management
                response = await timeout_manager.run_with_timeout(
                    operation=make_llm_call,
                    operation_id=operation_id,
                    timeout_type=TimeoutType.LLM_GENERATION,
                    custom_timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                # Debug logging
                logger.debug(f"Raw response: {response}")
                logger.debug(f"Response choices: {response.choices}")
                
                # Extract content from LiteLLM response
                if not response.choices or not response.choices[0] or not response.choices[0].message:
                    raise Exception(f"Invalid LLM response structure: no choices/message found")
                
                content = response.choices[0].message.content
                logger.debug(f"Extracted content: {content}")
                
                # Check if content is None or empty
                if content is None:
                    raise Exception(f"LLM returned empty content (None) from {model_config.litellm_name}")
                
                if not content.strip():
                    raise Exception(f"LLM returned empty content (blank) from {model_config.litellm_name}")
                
                # Estimate tokens (LiteLLM should provide usage if available)
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                else:
                    # Fallback token estimation
                    tokens_used = len(request.system_prompt.split()) + len(request.user_prompt.split()) + len(content.split())
                
                logger.info(f"✅ Success with {model_config.litellm_name} in {response_time:.2f}s")
                
                return LLMResponse(
                    content=content,
                    provider=model_config.name,
                    model=model_config.litellm_name,
                    tokens_used=tokens_used,
                    cost_usd=0.0,  # Cost calculation can be added later
                    response_time=response_time,
                    metadata={
                        "attempt": attempt + 1,
                        "fallback_sequence": self.fallback_sequence
                    }
                )
                
            except (asyncio.TimeoutError, TimeoutError) as e:
                last_error = e
                if isinstance(e, TimeoutError):
                    logger.warning(f"❌ Centralized timeout with {model_config.litellm_name} "
                                 f"after {e.elapsed_time:.2f}s (limit: {e.timeout_value}s)")
                else:
                    logger.warning(f"❌ Async timeout with {model_config.litellm_name} after {self.timeout}s")
                
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Error with {model_config.litellm_name}: {e}")
            
            # Short delay before trying next model
            if attempt < len(self.fallback_sequence) - 1:
                await asyncio.sleep(1)
        
        # All models failed
        total_time = time.time() - start_time
        
        if self.enable_fallback:
            logger.error(f"All models in fallback sequence failed after {total_time:.2f}s")
            error_msg = (
                f"All models in fallback sequence failed. "
                f"Last error: {last_error}. "
                f"Tried: {self.fallback_sequence}"
            )
        else:
            logger.error(f"Primary model failed after {total_time:.2f}s (fallback disabled)")
            error_msg = (
                f"Primary model {self.fallback_sequence[0]} failed. "
                f"Error: {last_error}. "
                f"Fallback is DISABLED (enable_fallback=False). "
                f"Set enable_fallback=True in config to try other models."
            )
        
        raise LLMProviderError(error_msg)
    
    def generate_sync(self, request: LLMRequest) -> LLMResponse:
        """
        Synchronous wrapper for generate() method.
        Uses litellm.completion() directly for synchronous execution.
        """
        start_time = time.time()
        
        # Try each model in fallback sequence
        last_error = None
        
        for attempt, model_name in enumerate(self.fallback_sequence):
            model_config = self.models.get(model_name)
            if not model_config:
                logger.warning(f"Model {model_name} not configured, skipping")
                continue
                
            try:
                # Build messages
                messages = []
                if request.system_prompt:
                    messages.append({"role": "system", "content": request.system_prompt})
                messages.append({"role": "user", "content": request.user_prompt})
                
                # Build kwargs for litellm.completion
                kwargs = {
                    "model": model_config.litellm_name,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    # Add timeout back with proper value
                    "timeout": self.timeout if self.timeout else 30.0
                }
                
                # Add response_format if json_mode is True
                if request.json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                
                # Use litellm.completion directly for synchronous call with timeout handling
                import signal
                
                class TimeoutException(Exception):
                    pass
                
                def timeout_handler(signum, frame):
                    raise TimeoutException(f"LLM call timed out after {self.timeout}s")
                
                # Set alarm for timeout (Unix only)
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(self.timeout) if self.timeout else 30)
                
                try:
                    response = litellm.completion(**kwargs)
                finally:
                    # Cancel alarm
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
                
                # Extract content and tokens
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                response_time = time.time() - start_time
                
                logger.info(f"✅ {model_config.litellm_name} responded in {response_time:.2f}s")
                
                # Determine provider from model name
                if "gemini" in model_config.litellm_name.lower():
                    provider = "gemini"
                elif "gpt" in model_config.litellm_name.lower():
                    provider = "openai"
                elif "claude" in model_config.litellm_name.lower():
                    provider = "anthropic"
                else:
                    provider = "unknown"
                
                return LLMResponse(
                    content=content,
                    provider=provider,
                    model=model_config.litellm_name,
                    tokens_used=tokens_used,
                    cost_usd=0.0,  # Cost calculation can be added later
                    response_time=response_time,
                    metadata={
                        "attempt": attempt + 1,
                        "fallback_sequence": self.fallback_sequence
                    }
                )
            
            except TimeoutException as e:
                last_error = e
                logger.warning(f"⏱️ Timeout with {model_config.litellm_name}: {e}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Error with {model_config.litellm_name}: {e}")
            
            # Short delay before trying next model
            if attempt < len(self.fallback_sequence) - 1:
                time.sleep(1)
        
        # All models failed
        total_time = time.time() - start_time
        
        if self.enable_fallback:
            logger.error(f"All models in fallback sequence failed after {total_time:.2f}s")
            error_msg = (
                f"All models in fallback sequence failed. "
                f"Last error: {last_error}. "
                f"Tried: {self.fallback_sequence}"
            )
        else:
            logger.error(f"Primary model failed after {total_time:.2f}s (fallback disabled)")
            error_msg = (
                f"Primary model {self.fallback_sequence[0]} failed. "
                f"Error: {last_error}. "
                f"Fallback is DISABLED (enable_fallback=False). "
                f"Set enable_fallback=True in config to try other models."
            )
        
        raise LLMProviderError(error_msg)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.models.keys())
    
    async def health_check(self) -> bool:
        """
        Simple health check using primary model with centralized timeout management
        
        Phase 2B Enhancement: Uses dedicated health check timeout type
        """
        try:
            request = LLMRequest(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'OK' if you can respond.",
                max_tokens=10,
                temperature=0.0
            )
            
            # Use centralized timeout management for health checks
            timeout_manager = get_timeout_manager()
            operation_id = f"health_check_{int(time.time() * 1000)}"
            
            async def perform_health_check():
                return await self.generate(request)
            
            response = await timeout_manager.run_with_timeout(
                operation=perform_health_check,
                operation_id=operation_id,
                timeout_type=TimeoutType.HEALTH_CHECK
            )
            
            return "ok" in response.content.lower()
            
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False


# Compatibility function for existing code
async def create_llm_provider(config: Dict[str, Any] = None) -> UnifiedLLMProvider:
    """Factory function to create unified LLM provider"""
    return UnifiedLLMProvider(config)