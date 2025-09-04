# ADR 027: LLM Provider Abstraction Layer (MVP)

*   **Status**: APPROVED (MVP Scope)
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: LLM Integration Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

The current system's LLM client is tightly coupled to a single provider and endpoint. This creates vendor lock-in and makes it difficult to experiment with different models (e.g., OpenAI, Anthropic, local on-prem models) or to add resilience patterns like failover.

## Decision Drivers

*   We need to avoid vendor lock-in and maintain flexibility in our choice of LLM provider.
*   The architecture should support routing requests to different models based on cost, performance, or capability.
*   We need a consistent interface for interacting with different LLMs.

## Considered Options

*   Full abstraction layer with provider plugins and dynamic routing.
*   Simple configuration-based provider switching.
*   Remote-only abstraction with thin SPI.

## Decision Outcome

**APPROVED (MVP Scope)**: Remote-only MVP with thin SPI and provider registration via entry points:

### MVP Boundaries
- **Remote-only**: No local model support in MVP
- **Thin SPI**: Minimal abstraction layer
- **Provider registration**: Via Python entry points
- **Static configuration**: No dynamic provider discovery

### LLM Provider SPI
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass
```

### Provider Registration
```python
# setup.py
entry_points={
    'autocoder.llm_providers': [
        'openai = autocoder.providers.openai:OpenAIProvider',
        'anthropic = autocoder.providers.anthropic:AnthropicProvider',
        'gemini = autocoder.providers.gemini:GeminiProvider',
    ],
}
```

### Configuration
```yaml
# config.yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  fallback_provider: "anthropic"
```

### Manager Capability
```python
class LLMManagerCapability(Capability):
    async def get_provider(self, model: str) -> LLMProvider:
        """Get provider for specified model."""
        return self.provider_registry.get_provider(model)
```

## Consequences

### Positive
- Avoids vendor lock-in
- Enables provider experimentation
- Consistent interface across providers
- Extensible for future providers

### Negative
- Limited to remote providers in MVP
- Additional abstraction layer complexity
- Provider-specific configuration management

### Neutral
- Maintains architectural flexibility
- Enables future local model support
- Provides clear provider boundaries 