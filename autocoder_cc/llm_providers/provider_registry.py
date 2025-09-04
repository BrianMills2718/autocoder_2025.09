from typing import Dict, List, Optional
from .base_provider import LLMProviderInterface
import logging

class LLMProviderRegistry:
    """Registry for managing multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProviderInterface] = {}
        self.logger = logging.getLogger(__name__)
        
    def register_provider(self, provider: LLMProviderInterface):
        """Register a new LLM provider"""
        self.providers[provider.provider_name] = provider
        self.logger.info(f"Registered LLM provider: {provider.provider_name}")
    
    def get_provider(self, provider_name: str) -> Optional[LLMProviderInterface]:
        """Get provider by name"""
        return self.providers.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return list(self.providers.keys())
    
    async def get_healthy_providers(self) -> List[str]:
        """Get list of healthy provider names"""
        healthy = []
        for name, provider in self.providers.items():
            try:
                if await provider.health_check():
                    healthy.append(name)
            except Exception as e:
                self.logger.warning(f"Health check failed for {name}: {e}")
        return healthy