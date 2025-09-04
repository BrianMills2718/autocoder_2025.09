import openai
import os
import time
import asyncio
from typing import Dict, Any, List
from .base_provider import LLMProviderInterface, LLMRequest, LLMResponse, LLMProviderError, LLMProviderUnavailableError, LLMProviderRateLimitError

class OpenAIProvider(LLMProviderInterface):
    """OpenAI provider implementation"""
    
    # Cost per 1K tokens (input/output)
    MODEL_COSTS = {
        "gpt-4o": (0.0025, 0.01),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "o3-mini": (0.0025, 0.01),  # o3-mini pricing (estimate)
        "o3": (0.03, 0.06),         # o3 pricing (estimate)
        # Note: Additional models can be configured via environment
    }
    
    # O3/O4 models that require special parameter handling (no temperature, max_completion_tokens)
    O3_MODELS = ["o3", "o3-mini"]
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("openai", config)
        self.api_key = config.get("api_key")
        self.default_model = config.get("default_model", os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.timeout = float('inf')  # No timeout
        
        # Add environment model to O3_MODELS if it's an O-series model
        env_model = os.getenv("OPENAI_MODEL")
        if env_model and (env_model.startswith("o3") or env_model.startswith("o4")):
            if env_model not in self.O3_MODELS:
                self.O3_MODELS = self.O3_MODELS + [env_model]
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API with o3 model support"""
        start_time = time.time()
        model = request.model_override or self.default_model
        
        try:
            # Prepare request parameters based on model type
            if model in self.O3_MODELS:
                # O3 models use different parameters
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": request.system_prompt},
                            {"role": "user", "content": request.user_prompt}
                        ],
                        max_completion_tokens=request.max_tokens  # O3 uses max_completion_tokens
                        # Note: O3 models don't support temperature - they use reasoning
                    ),
                    timeout=self.timeout
                )
            else:
                # Standard models use regular parameters
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": request.system_prompt},
                            {"role": "user", "content": request.user_prompt}
                        ],
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    ),
                    timeout=self.timeout
                )
            
            response_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost = self.estimate_cost(tokens_used, model)
            
            # Update statistics
            self.total_tokens += tokens_used
            self.total_cost += cost
            self.request_count += 1
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=model,
                tokens_used=tokens_used,
                cost_usd=cost,
                response_time=response_time,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.dict()
                }
            )
            
        except asyncio.TimeoutError:
            raise LLMProviderError(f"OpenAI request timed out after {self.timeout} seconds")
        except openai.RateLimitError as e:
            raise LLMProviderRateLimitError(f"OpenAI rate limit: {e}")
        except openai.APIError as e:
            raise LLMProviderUnavailableError(f"OpenAI API error: {e}")
        except Exception as e:
            raise LLMProviderError(f"OpenAI error: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        models = list(self.MODEL_COSTS.keys())
        # Add environment model if not already in list
        env_model = os.getenv("OPENAI_MODEL")
        if env_model and env_model not in models:
            models.append(env_model)
        return models
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for OpenAI request"""
        if model not in self.MODEL_COSTS:
            # Use default estimate for unknown models
            # For O-series models, use o3-mini pricing as baseline
            if model.startswith("o3") or model.startswith("o4"):
                input_cost, output_cost = 0.0025, 0.01
            else:
                # Use gpt-3.5-turbo pricing as baseline for other models
                input_cost, output_cost = 0.0015, 0.002
        else:
            input_cost, output_cost = self.MODEL_COSTS[model]
        
        # Assume 70% input, 30% output tokens
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        return (input_tokens * input_cost / 1000) + (output_tokens * output_cost / 1000)
    
    async def health_check(self) -> bool:
        """Check OpenAI API health"""
        try:
            await self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except:
            return False