from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Union
from dataclasses import dataclass, field
import time
from pydantic import BaseModel

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    provider: str
    model: str
    tokens_used: int
    cost_usd: float
    response_time: float
    metadata: Dict[str, Any]

@dataclass 
class LLMRequest:
    """Standardized LLM request format"""
    system_prompt: str
    user_prompt: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    model_override: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    json_mode: bool = False
    streaming: bool = False
    response_schema: Optional[Union[Type[BaseModel], List[Type[BaseModel]], Dict[str, Any]]] = None

class LLMProviderError(Exception):
    """Base exception for LLM provider errors"""
    pass

class LLMProviderUnavailableError(LLMProviderError):
    """Provider is temporarily unavailable"""
    pass

class LLMProviderRateLimitError(LLMProviderError):
    """Provider rate limit exceeded"""
    pass

class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        self.provider_name = provider_name
        self.config = config
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for given tokens and model"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and available"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider usage statistics"""
        return {
            "provider": self.provider_name,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "request_count": self.request_count,
            "avg_cost_per_request": self.total_cost / max(self.request_count, 1)
        }