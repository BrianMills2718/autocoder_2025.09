import anthropic
import time
import asyncio
from typing import Dict, Any, List
from .base_provider import LLMProviderInterface, LLMRequest, LLMResponse, LLMProviderError, LLMProviderUnavailableError, LLMProviderRateLimitError

class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude provider implementation"""
    
    # Cost per 1M tokens (input/output)
    MODEL_COSTS = {
        "claude-3-5-sonnet-20241022": (3.0, 15.0),
        "claude-3-5-haiku-20241022": (1.0, 5.0),
        "claude-3-opus-20240229": (15.0, 75.0)
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("anthropic", config)
        self.api_key = config.get("api_key")
        self.default_model = config.get("default_model", "claude-3-5-sonnet-20241022")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.timeout = float('inf')  # No timeout
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API"""
        start_time = time.time()
        model = request.model_override or self.default_model
        
        try:
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=model,
                    max_tokens=request.max_tokens or 4096,
                    temperature=request.temperature,
                    system=request.system_prompt,
                    messages=[
                        {"role": "user", "content": request.user_prompt}
                    ]
                ),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self.estimate_cost(tokens_used, model)
            
            # Update statistics
            self.total_tokens += tokens_used
            self.total_cost += cost
            self.request_count += 1
            
            return LLMResponse(
                content=response.content[0].text,
                provider="anthropic",
                model=model,
                tokens_used=tokens_used,
                cost_usd=cost,
                response_time=response_time,
                metadata={
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
            )
            
        except asyncio.TimeoutError:
            raise LLMProviderError(f"Anthropic request timed out after {self.timeout} seconds")
        except anthropic.RateLimitError as e:
            raise LLMProviderRateLimitError(f"Anthropic rate limit: {e}")
        except anthropic.APIError as e:
            raise LLMProviderUnavailableError(f"Anthropic API error: {e}")
        except Exception as e:
            raise LLMProviderError(f"Anthropic error: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return list(self.MODEL_COSTS.keys())
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Anthropic request"""
        if model not in self.MODEL_COSTS:
            return 0.0
        
        # Assume 70% input, 30% output tokens
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost, output_cost = self.MODEL_COSTS[model]
        
        return (input_tokens * input_cost / 1000000) + (output_tokens * output_cost / 1000000)
    
    async def health_check(self) -> bool:
        """Check Anthropic API health"""
        try:
            await self.client.messages.create(
                model=self.default_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False