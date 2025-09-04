"""Model Registry for LLM Providers

Centralizes model capabilities and requirements to enable dynamic provider
selection and request adaptation. Part of P1.0 Foundation Stabilization.
"""
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import os
from ..observability.structured_logging import get_logger

logger = get_logger(__name__)


class ModelCapability(Enum):
    """Capabilities that models may or may not support"""
    TEMPERATURE = "temperature"
    MAX_TOKENS = "max_tokens"
    TOP_P = "top_p"
    TOP_K = "top_k"
    FREQUENCY_PENALTY = "frequency_penalty"
    PRESENCE_PENALTY = "presence_penalty"
    STOP_SEQUENCES = "stop_sequences"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    REASONING_EFFORT = "reasoning_effort"
    JSON_MODE = "json_mode"
    SYSTEM_PROMPT = "system_prompt"
    IMAGE_INPUT = "image_input"
    LONG_CONTEXT = "long_context"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: str
    model_id: str
    display_name: str
    max_context_tokens: int
    max_output_tokens: int
    supports_temperature: bool = True
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_reasoning_effort: bool = False
    supports_json_mode: bool = False
    supports_system_prompt: bool = True
    supports_image_input: bool = False
    token_param_name: str = "max_tokens"  # Some models use different names
    temperature_range: tuple[float, float] = (0.0, 2.0)
    default_temperature: float = 0.7
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    capabilities: Set[ModelCapability] = field(default_factory=set)
    parameter_mappings: Dict[str, str] = field(default_factory=dict)
    notes: Optional[str] = None


class ModelRegistry:
    """Registry of all supported models and their capabilities"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the registry with known models"""
        
        # Register environment-configured OpenAI model if set
        openai_model = os.getenv("OPENAI_MODEL")
        if openai_model:
            self._register_openai_model_from_env(openai_model)
        
        # OpenAI Models
        self.register_model(ModelConfig(
            provider="openai",
            model_id="o4-mini",
            display_name="O4 Mini",
            max_context_tokens=128000,
            max_output_tokens=16384,
            supports_temperature=False,  # O4 doesn't support temperature
            supports_streaming=False,
            supports_reasoning_effort=True,
            supports_json_mode=True,
            token_param_name="max_completion_tokens",
            capabilities={
                ModelCapability.MAX_TOKENS,
                ModelCapability.REASONING_EFFORT,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.STOP_SEQUENCES
            },
            parameter_mappings={
                "max_tokens": "max_completion_tokens"
            },
            cost_per_input_token=0.00003,
            cost_per_output_token=0.00012,
            notes="O4 model with reasoning capabilities, no temperature support"
        ))
        
        self.register_model(ModelConfig(
            provider="openai",
            model_id="o3",
            display_name="O3",
            max_context_tokens=128000,
            max_output_tokens=16384,
            supports_temperature=False,
            supports_streaming=False,
            supports_reasoning_effort=True,
            supports_json_mode=True,
            token_param_name="max_completion_tokens",
            capabilities={
                ModelCapability.MAX_TOKENS,
                ModelCapability.REASONING_EFFORT,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.STOP_SEQUENCES
            },
            parameter_mappings={
                "max_tokens": "max_completion_tokens"
            },
            cost_per_input_token=0.00005,
            cost_per_output_token=0.00020,
            notes="O3 model with advanced reasoning"
        ))
        
        self.register_model(ModelConfig(
            provider="openai",
            model_id="gpt-4-turbo",
            display_name="GPT-4 Turbo",
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.FREQUENCY_PENALTY,
                ModelCapability.PRESENCE_PENALTY,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.00001,
            cost_per_output_token=0.00003
        ))
        
        self.register_model(ModelConfig(
            provider="openai",
            model_id="gpt-4o",
            display_name="GPT-4 Optimized",
            max_context_tokens=128000,
            max_output_tokens=16384,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.FREQUENCY_PENALTY,
                ModelCapability.PRESENCE_PENALTY,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.0000025,
            cost_per_output_token=0.00001
        ))
        
        # Anthropic Models
        self.register_model(ModelConfig(
            provider="anthropic",
            model_id="claude-sonnet-4-20250514",
            display_name="Claude 3.5 Sonnet",
            max_context_tokens=200000,
            max_output_tokens=8192,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.TOP_K,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.000003,
            cost_per_output_token=0.000015
        ))
        
        self.register_model(ModelConfig(
            provider="anthropic",
            model_id="claude-opus-4-20250514",
            display_name="Claude 3 Opus",
            max_context_tokens=200000,
            max_output_tokens=4096,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.TOP_K,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.000015,
            cost_per_output_token=0.000075
        ))
        
        # Gemini Models
        self.register_model(ModelConfig(
            provider="gemini",
            model_id="gemini-2.5-flash",
            display_name="Gemini 2.5 Flash",
            max_context_tokens=1048576,  # 1M context
            max_output_tokens=8192,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.TOP_K,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.00000025,
            cost_per_output_token=0.0000005
        ))
        
        self.register_model(ModelConfig(
            provider="gemini",
            model_id="gemini-2.5-pro",
            display_name="Gemini 2.5 Pro",
            max_context_tokens=2097152,  # 2M context
            max_output_tokens=8192,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_image_input=True,
            capabilities={
                ModelCapability.TEMPERATURE,
                ModelCapability.MAX_TOKENS,
                ModelCapability.TOP_P,
                ModelCapability.TOP_K,
                ModelCapability.STOP_SEQUENCES,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.SYSTEM_PROMPT,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.LONG_CONTEXT
            },
            cost_per_input_token=0.00000125,
            cost_per_output_token=0.000005
        ))
    
    def _register_openai_model_from_env(self, model_id: str):
        """Register an OpenAI model from environment configuration"""
        # Check if already registered
        if self.get_model("openai", model_id):
            return
            
        # Determine capabilities based on model name
        if model_id.startswith("o3") or model_id.startswith("o4"):
            # O-series models have specific capabilities
            config = ModelConfig(
                provider="openai",
                model_id=model_id,
                display_name=f"{model_id.upper()} (Environment)",
                max_context_tokens=128000,
                max_output_tokens=16384,
                supports_temperature=False,
                supports_streaming=False,
                supports_reasoning_effort=True,
                supports_json_mode=True,
                token_param_name="max_completion_tokens",
                capabilities={
                    ModelCapability.MAX_TOKENS,
                    ModelCapability.REASONING_EFFORT,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_PROMPT,
                    ModelCapability.STOP_SEQUENCES
                },
                parameter_mappings={
                    "max_tokens": "max_completion_tokens"
                }
            )
        else:
            # Standard OpenAI models
            config = ModelConfig(
                provider="openai",
                model_id=model_id,
                display_name=f"{model_id} (Environment)",
                max_context_tokens=128000,
                max_output_tokens=4096,
                supports_temperature=True,
                supports_streaming=True,
                capabilities={
                    ModelCapability.TEMPERATURE,
                    ModelCapability.MAX_TOKENS,
                    ModelCapability.TOP_P,
                    ModelCapability.FREQUENCY_PENALTY,
                    ModelCapability.PRESENCE_PENALTY,
                    ModelCapability.STOP_SEQUENCES,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_PROMPT
                }
            )
        
        self.register_model(config)
        logger.info(f"Registered environment model: {model_id}")
    
    def register_model(self, config: ModelConfig):
        """Register a model configuration"""
        key = f"{config.provider}:{config.model_id}"
        self.models[key] = config
        logger.info(f"Registered model: {key} ({config.display_name})")
    
    def get_model(self, provider: str, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration"""
        key = f"{provider}:{model_id}"
        return self.models.get(key)
    
    def get_models_by_provider(self, provider: str) -> List[ModelConfig]:
        """Get all models for a provider"""
        return [
            config for key, config in self.models.items()
            if config.provider == provider
        ]
    
    def get_models_with_capability(self, capability: ModelCapability) -> List[ModelConfig]:
        """Get all models that support a specific capability"""
        return [
            config for config in self.models.values()
            if capability in config.capabilities
        ]
    
    def find_cheapest_model(self, required_capabilities: Set[ModelCapability]) -> Optional[ModelConfig]:
        """Find the cheapest model that supports all required capabilities"""
        suitable_models = [
            config for config in self.models.values()
            if required_capabilities.issubset(config.capabilities)
        ]
        
        if not suitable_models:
            return None
        
        # Sort by average cost (input + output)
        return min(
            suitable_models,
            key=lambda m: (m.cost_per_input_token + m.cost_per_output_token) / 2
        )
    
    def find_model_for_context_size(self, required_tokens: int) -> Optional[ModelConfig]:
        """Find a model that can handle the required context size"""
        suitable_models = [
            config for config in self.models.values()
            if config.max_context_tokens >= required_tokens
        ]
        
        if not suitable_models:
            return None
        
        # Return cheapest suitable model
        return min(
            suitable_models,
            key=lambda m: (m.cost_per_input_token + m.cost_per_output_token) / 2
        )
    
    def adapt_request_parameters(self, provider: str, model_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt request parameters based on model capabilities"""
        config = self.get_model(provider, model_id)
        if not config:
            logger.warning(f"Unknown model {provider}:{model_id}, returning params as-is")
            return params
        
        adapted = params.copy()
        
        # Handle parameter name mappings
        for standard_name, model_name in config.parameter_mappings.items():
            if standard_name in adapted:
                adapted[model_name] = adapted.pop(standard_name)
        
        # Remove unsupported parameters
        if not config.supports_temperature and "temperature" in adapted:
            logger.info(f"Removing temperature parameter for {model_id}")
            adapted.pop("temperature")
        
        if not config.supports_streaming and adapted.get("stream", False):
            logger.info(f"Disabling streaming for {model_id}")
            adapted["stream"] = False
        
        # Validate parameter ranges
        if "temperature" in adapted and config.supports_temperature:
            min_temp, max_temp = config.temperature_range
            if adapted["temperature"] < min_temp or adapted["temperature"] > max_temp:
                logger.warning(
                    f"Temperature {adapted['temperature']} out of range "
                    f"[{min_temp}, {max_temp}] for {model_id}, using default"
                )
                adapted["temperature"] = config.default_temperature
        
        # Ensure max tokens doesn't exceed model limit
        token_param = config.token_param_name
        if token_param in adapted:
            if adapted[token_param] > config.max_output_tokens:
                logger.warning(
                    f"Requested {token_param}={adapted[token_param]} exceeds "
                    f"model limit {config.max_output_tokens}, capping"
                )
                adapted[token_param] = config.max_output_tokens
        
        return adapted


# Global registry instance
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry