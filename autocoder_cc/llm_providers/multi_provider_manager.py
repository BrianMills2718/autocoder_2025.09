import asyncio
import random
import time
from typing import Dict, Any, List, Optional
from .base_provider import LLMProviderInterface, LLMRequest, LLMResponse, LLMProviderError, LLMProviderUnavailableError, LLMProviderRateLimitError
from .provider_registry import LLMProviderRegistry
from ..observability.cost_controls import CostCircuitBreaker, create_cost_circuit_breaker, CostLimits
from ..observability.monitoring_alerts import ProductionMonitor, create_production_monitor
from .circuit_breaker import get_circuit_breaker
from .model_registry import get_model_registry, ModelCapability
import logging

class MultiProviderManager:
    """Manages multiple LLM providers with intelligent failover"""
    
    def __init__(self, config: Dict[str, Any]):
        self.registry = LLMProviderRegistry()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.primary_provider = config.get("primary_provider", "gemini")
        self.fallback_providers = config.get("fallback_providers", ["openai", "anthropic"])
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        
        # Health check cache to avoid repeated checks during retries
        self._health_cache = {}  # provider_name -> (is_healthy, timestamp)
        self._health_cache_ttl = 300  # 5 minutes cache TTL
        
        # Initialize cost circuit breaker
        environment = config.get("environment", "development")
        cost_limits = config.get("cost_limits")
        if cost_limits:
            custom_limits = CostLimits(**cost_limits)
            self.cost_breaker = CostCircuitBreaker(custom_limits)
        else:
            self.cost_breaker = create_cost_circuit_breaker(environment)
        
        # Initialize production monitoring
        monitoring_config = config.get("monitoring", {})
        self.monitor = create_production_monitor(monitoring_config)
        
        # Initialize circuit breaker for health checks
        self.circuit_breaker = get_circuit_breaker()
        
        # Initialize model registry
        self.model_registry = get_model_registry()
    
    async def _check_provider_health(self, provider_name: str, provider: LLMProviderInterface, skip_cache: bool = False) -> bool:
        """Check provider health with caching and circuit breaker protection"""
        import time
        
        # Check circuit breaker first
        can_attempt, reason = self.circuit_breaker.can_attempt(provider_name)
        if not can_attempt:
            self.logger.warning(f"Circuit breaker blocking health check for {provider_name}: {reason}")
            return False
        
        # Check cache unless explicitly skipped
        if not skip_cache and provider_name in self._health_cache:
            is_healthy, timestamp = self._health_cache[provider_name]
            if time.time() - timestamp < self._health_cache_ttl:
                return is_healthy
        
        # Perform actual health check with timeout
        try:
            # Use timeout from settings
            health_check_timeout = getattr(provider, 'health_check_timeout', 5)
            is_healthy = await asyncio.wait_for(
                provider.health_check(),
                timeout=health_check_timeout
            )
            
            # Record success in circuit breaker
            if is_healthy:
                self.circuit_breaker.record_success(provider_name)
            else:
                self.circuit_breaker.record_failure(provider_name)
                
            self._health_cache[provider_name] = (is_healthy, time.time())
            return is_healthy
            
        except asyncio.TimeoutError:
            self.logger.error(f"Health check timed out for {provider_name} after {health_check_timeout}s")
            self.circuit_breaker.record_failure(provider_name, Exception("Health check timeout"))
            self._health_cache[provider_name] = (False, time.time())
            return False
            
        except Exception as e:
            self.logger.error(f"Health check failed for {provider_name}: {e}")
            self.circuit_breaker.record_failure(provider_name, e)
            self._health_cache[provider_name] = (False, time.time())
            return False
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response with automatic failover and cost controls"""
        # Use dynamic provider selection based on task requirements
        providers_to_try = self._select_providers_for_task(request)
        
        for attempt in range(self.max_retries):
            for provider_name in providers_to_try:
                provider = self.registry.get_provider(provider_name)
                if not provider:
                    self.logger.warning(f"Provider {provider_name} not registered")
                    continue
                
                try:
                    # Estimate cost before making request
                    estimated_cost = provider.estimate_cost(
                        len(request.system_prompt + request.user_prompt), 
                        request.model_override or provider.default_model
                    )
                    
                    # Check cost circuit breaker
                    allowed, reason = self.cost_breaker.check_request_allowed(estimated_cost, provider_name)
                    if not allowed:
                        self.logger.warning(f"Request blocked by cost controls: {reason}")
                        self.cost_breaker.record_failure(f"Cost limit exceeded: {reason}")
                        continue
                    
                    # Check provider health before using (use cache on retries to avoid blocking)
                    skip_cache = (attempt == 0)  # Only do fresh health check on first attempt
                    if not await self._check_provider_health(provider_name, provider, skip_cache=skip_cache):
                        self.logger.debug(f"Provider {provider_name} failed health check, trying next provider")
                        continue
                    
                    # Adapt request for provider/model capabilities
                    model = request.model_override or getattr(provider, 'default_model', None) or 'gpt-4-turbo'
                    adapted_request = self._adapt_request_for_provider(request, provider_name, model)
                    
                    self.logger.info(f"Attempting generation with {provider_name} (attempt {attempt + 1}, estimated cost: ${estimated_cost:.6f})")
                    
                    response = await provider.generate(adapted_request)
                    
                    # Record actual cost after successful generation
                    self.cost_breaker.record_request(response.cost_usd, provider_name)
                    
                    self.logger.info(f"Successful generation with {provider_name} (actual cost: ${response.cost_usd:.6f})")
                    return response
                    
                except LLMProviderRateLimitError as e:
                    self.logger.warning(f"Rate limit hit for {provider_name}: {e}")
                    self.monitor.metrics.record_rate_limit(provider_name)
                    # Try next provider immediately for rate limits
                    continue
                    
                except LLMProviderUnavailableError as e:
                    self.logger.warning(f"Provider {provider_name} unavailable: {e}")
                    continue
                    
                except LLMProviderError as e:
                    self.logger.error(f"Provider {provider_name} error: {e}")
                    continue
            
            # If we've tried all providers and failed, wait before retry
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                self.logger.info(f"All providers failed, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
        
        raise LLMProviderError("All providers failed after maximum retries")
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers"""
        stats = {}
        for provider_name in self.registry.list_providers():
            provider = self.registry.get_provider(provider_name)
            if provider:
                stats[provider_name] = provider.get_stats()
        return stats
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary across all providers with circuit breaker status"""
        total_cost = 0.0
        total_tokens = 0
        total_requests = 0
        
        for provider_name in self.registry.list_providers():
            provider = self.registry.get_provider(provider_name)
            if provider:
                total_cost += provider.total_cost
                total_tokens += provider.total_tokens
                total_requests += provider.request_count
        
        # Include cost circuit breaker usage information
        usage_summary = self.cost_breaker.get_usage_summary()
        
        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "avg_cost_per_token": total_cost / max(total_tokens, 1),
            "avg_cost_per_request": total_cost / max(total_requests, 1),
            "cost_controls": usage_summary
        }
    
    def get_cost_usage_status(self) -> Dict[str, Any]:
        """Get detailed cost usage and limits status"""
        return self.cost_breaker.get_usage_summary()
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get comprehensive system health status with monitoring"""
        # Get provider stats
        provider_stats = self.get_provider_stats()
        
        # Get cost information
        cost_summary = self.get_cost_summary()
        cost_usage = self.get_cost_usage_status()
        
        # Collect rate limiting data
        rate_limit_data = self.monitor.metrics.rate_limit_hits
        
        # Create comprehensive health status
        system_stats = {
            'providers': provider_stats,
            'cost_controls': cost_usage,
            'cost_summary': cost_summary,
            'rate_limits': rate_limit_data,
            'generation': {
                'success_rate': self.monitor.metrics.generation_success_rate,
                'avg_time': self.monitor.metrics.avg_generation_time,
                'total_requests': self.monitor.metrics.total_requests,
                'failed_requests': self.monitor.metrics.failed_requests
            }
        }
        
        # Run monitoring checks
        self.monitor.monitor_system_health(system_stats)
        
        # Add monitoring summary
        system_stats['monitoring'] = self.monitor.get_monitoring_summary()
        
        return system_stats
    
    def _select_providers_for_task(self, request: LLMRequest) -> List[str]:
        """Dynamically select providers based on task requirements"""
        required_capabilities = set()
        
        # Analyze request to determine required capabilities
        if request.json_mode:
            required_capabilities.add(ModelCapability.JSON_MODE)
        
        if request.streaming:
            required_capabilities.add(ModelCapability.STREAMING)
        
        if hasattr(request, 'images') and request.images:
            required_capabilities.add(ModelCapability.IMAGE_INPUT)
        
        if hasattr(request, 'functions') and request.functions:
            required_capabilities.add(ModelCapability.FUNCTION_CALLING)
        
        # Calculate estimated token count
        estimated_tokens = len(request.system_prompt + request.user_prompt) // 4
        
        # Find suitable models
        suitable_providers = []
        
        for provider_name in [self.primary_provider] + self.fallback_providers:
            provider = self.registry.get_provider(provider_name)
            if not provider:
                continue
                
            # Check if provider has models with required capabilities
            provider_models = self.model_registry.get_models_by_provider(provider_name)
            
            for model_config in provider_models:
                # Check capabilities
                if required_capabilities.issubset(model_config.capabilities):
                    # Check context size
                    if model_config.max_context_tokens >= estimated_tokens:
                        suitable_providers.append(provider_name)
                        break
        
        # If no suitable providers found, fall back to default list
        if not suitable_providers:
            self.logger.warning(
                f"No providers found with required capabilities: {required_capabilities}. "
                "Using default provider list."
            )
            return [self.primary_provider] + self.fallback_providers
        
        return suitable_providers
    
    def _adapt_request_for_provider(self, request: LLMRequest, provider_name: str, model: str) -> LLMRequest:
        """Adapt request parameters based on provider and model capabilities"""
        # Get model configuration
        model_config = self.model_registry.get_model(provider_name, model)
        if not model_config:
            # Unknown model, return request as-is
            return request
        
        # Create a copy of the request
        adapted_request = LLMRequest(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            model_override=request.model_override,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            json_mode=request.json_mode,
            streaming=request.streaming
        )
        
        # Copy any additional attributes
        for attr in dir(request):
            if not attr.startswith('_') and attr not in ['system_prompt', 'user_prompt', 
                                                         'model_override', 'temperature', 
                                                         'max_tokens', 'json_mode', 'streaming']:
                if hasattr(request, attr):
                    setattr(adapted_request, attr, getattr(request, attr))
        
        # Adapt based on model capabilities
        if not model_config.supports_temperature:
            adapted_request.temperature = None
        elif adapted_request.temperature is not None:
            # Clamp temperature to model's range
            min_temp, max_temp = model_config.temperature_range
            adapted_request.temperature = max(min_temp, min(adapted_request.temperature, max_temp))
        
        if not model_config.supports_streaming:
            adapted_request.streaming = False
        
        if not model_config.supports_json_mode:
            adapted_request.json_mode = False
        
        # Ensure max tokens doesn't exceed model limit
        if adapted_request.max_tokens and adapted_request.max_tokens > model_config.max_output_tokens:
            self.logger.info(
                f"Capping max_tokens from {adapted_request.max_tokens} to "
                f"{model_config.max_output_tokens} for {model}"
            )
            adapted_request.max_tokens = model_config.max_output_tokens
        
        # Apply parameter name mappings from model config
        if model_config.parameter_mappings:
            # Create a dict of all request attributes
            request_dict = {}
            for attr in ['system_prompt', 'user_prompt', 'max_tokens', 'temperature', 
                        'top_p', 'top_k', 'frequency_penalty', 'presence_penalty',
                        'stop_sequences', 'json_mode', 'streaming']:
                if hasattr(adapted_request, attr):
                    value = getattr(adapted_request, attr)
                    if value is not None:
                        request_dict[attr] = value
            
            # Apply mappings
            for standard_name, model_name in model_config.parameter_mappings.items():
                if standard_name in request_dict:
                    # Set the model-specific parameter name
                    setattr(adapted_request, model_name, request_dict[standard_name])
                    # Remove the standard name if different
                    if model_name != standard_name:
                        setattr(adapted_request, standard_name, None)
                    
                    self.logger.debug(
                        f"Mapped parameter '{standard_name}' to '{model_name}' "
                        f"for model {model}"
                    )
        
        return adapted_request
    
