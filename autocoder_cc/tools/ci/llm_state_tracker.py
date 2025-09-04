"""
LLM State Tracker
Tracks LLM sampling parameters and state for reproducible builds
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Simple logger for testing
def get_logger(name: str):
    """Simple logger for testing"""
    import logging
    return logging.getLogger(name)


@dataclass
class LLMConfiguration:
    """LLM configuration for reproducible builds"""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: List[str]
    seed: Optional[int] = None
    deterministic_mode: bool = True


@dataclass
class LLMState:
    """Complete LLM state for reproducible builds"""
    configurations: Dict[str, LLMConfiguration]
    global_seed: Optional[int]
    deterministic_mode: bool
    tokenizer_versions: Dict[str, str]
    model_versions: Dict[str, str]
    api_versions: Dict[str, str]
    sampling_hash: str = ""


class LLMStateTracker:
    """Tracks and manages LLM state for reproducible builds"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    def capture_llm_state(self) -> LLMState:
        """Capture complete LLM state"""
        self.logger.info("Capturing LLM state for reproducible builds")
        
        configurations = {
            "openai": self._get_openai_configuration(),
            "anthropic": self._get_anthropic_configuration(),
            "huggingface": self._get_huggingface_configuration()
        }
        
        state = LLMState(
            configurations=configurations,
            global_seed=self._get_global_seed(),
            deterministic_mode=self._get_deterministic_mode(),
            tokenizer_versions=self._get_tokenizer_versions(),
            model_versions=self._get_model_versions(),
            api_versions=self._get_api_versions()
        )
        
        # Generate sampling hash
        state.sampling_hash = self._generate_sampling_hash(state)
        
        self.logger.info(f"LLM state captured with hash: {state.sampling_hash}")
        return state
    
    def _get_openai_configuration(self) -> LLMConfiguration:
        """Get OpenAI configuration"""
        return LLMConfiguration(
            provider="openai",
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
            top_p=float(os.getenv("OPENAI_TOP_P", "1.0")),
            frequency_penalty=float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.0")),
            stop_sequences=self._parse_stop_sequences(os.getenv("OPENAI_STOP", "")),
            seed=self._parse_seed(os.getenv("OPENAI_SEED")),
            deterministic_mode=os.getenv("OPENAI_DETERMINISTIC", "true").lower() == "true"
        )
    
    def _get_anthropic_configuration(self) -> LLMConfiguration:
        """Get Anthropic configuration"""
        return LLMConfiguration(
            provider="anthropic",
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.0")),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
            top_p=float(os.getenv("ANTHROPIC_TOP_P", "1.0")),
            frequency_penalty=0.0,  # Anthropic doesn't have frequency penalty
            presence_penalty=0.0,   # Anthropic doesn't have presence penalty
            stop_sequences=self._parse_stop_sequences(os.getenv("ANTHROPIC_STOP", "")),
            seed=self._parse_seed(os.getenv("ANTHROPIC_SEED")),
            deterministic_mode=os.getenv("ANTHROPIC_DETERMINISTIC", "true").lower() == "true"
        )
    
    def _get_huggingface_configuration(self) -> LLMConfiguration:
        """Get Hugging Face configuration"""
        return LLMConfiguration(
            provider="huggingface",
            model=os.getenv("HF_MODEL", "microsoft/DialoGPT-medium"),
            temperature=float(os.getenv("HF_TEMPERATURE", "0.0")),
            max_tokens=int(os.getenv("HF_MAX_TOKENS", "1024")),
            top_p=float(os.getenv("HF_TOP_P", "1.0")),
            frequency_penalty=float(os.getenv("HF_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("HF_PRESENCE_PENALTY", "0.0")),
            stop_sequences=self._parse_stop_sequences(os.getenv("HF_STOP", "")),
            seed=self._parse_seed(os.getenv("HF_SEED")),
            deterministic_mode=os.getenv("HF_DETERMINISTIC", "true").lower() == "true"
        )
    
    def _parse_stop_sequences(self, stop_str: str) -> List[str]:
        """Parse stop sequences from environment variable"""
        if not stop_str or stop_str.lower() == "null":
            return []
        
        # Try to parse as JSON array
        try:
            return json.loads(stop_str)
        except json.JSONDecodeError:
            # Fall back to comma-separated
            return [s.strip() for s in stop_str.split(",") if s.strip()]
    
    def _parse_seed(self, seed_str: Optional[str]) -> Optional[int]:
        """Parse seed from environment variable"""
        if not seed_str or seed_str.lower() == "null":
            return None
        
        try:
            return int(seed_str)
        except ValueError:
            return None
    
    def _get_global_seed(self) -> Optional[int]:
        """Get global seed for reproducibility"""
        return self._parse_seed(os.getenv("LLM_GLOBAL_SEED", "42"))
    
    def _get_deterministic_mode(self) -> bool:
        """Get global deterministic mode setting"""
        return os.getenv("LLM_DETERMINISTIC", "true").lower() == "true"
    
    def _get_tokenizer_versions(self) -> Dict[str, str]:
        """Get tokenizer versions"""
        versions = {}
        
        # OpenAI tokenizer (tiktoken)
        try:
            import tiktoken
            versions["tiktoken"] = tiktoken.__version__
            
            # Get specific encoding versions
            for model in ["gpt-4", "gpt-3.5-turbo", "text-davinci-003"]:
                try:
                    encoding = tiktoken.encoding_for_model(model)
                    versions[f"tiktoken_{model}"] = encoding.name
                except Exception:
                    pass
        except ImportError:
            pass
        
        # Hugging Face tokenizers
        try:
            import transformers
            versions["transformers"] = transformers.__version__
            
            # Get tokenizer versions for specific models
            try:
                import tokenizers
                versions["tokenizers"] = tokenizers.__version__
            except ImportError:
                pass
        except ImportError:
            pass
        
        return versions
    
    def _get_model_versions(self) -> Dict[str, str]:
        """Get model versions and hashes"""
        versions = {}
        
        # OpenAI models (API-based, version from API)
        try:
            import openai
            versions["openai_client"] = openai.__version__
        except ImportError:
            pass
        
        # Anthropic models (API-based, version from API)
        try:
            import anthropic
            versions["anthropic_client"] = anthropic.__version__
        except ImportError:
            pass
        
        # Hugging Face models (local cache versions)
        try:
            from transformers import AutoModel, AutoTokenizer
            
            # Get cached model info
            cache_dir = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
            if os.path.exists(cache_dir):
                versions["hf_cache_dir"] = cache_dir
        except ImportError:
            pass
        
        return versions
    
    def _get_api_versions(self) -> Dict[str, str]:
        """Get API client versions"""
        versions = {}
        
        # OpenAI API version
        try:
            import openai
            versions["openai"] = openai.__version__
            
            # Try to get API version from client
            try:
                # This would require an API call in practice
                versions["openai_api"] = os.getenv("OPENAI_API_VERSION", "2023-12-01")
            except Exception:
                pass
        except ImportError:
            pass
        
        # Anthropic API version
        try:
            import anthropic
            versions["anthropic"] = anthropic.__version__
            
            # Try to get API version
            try:
                versions["anthropic_api"] = os.getenv("ANTHROPIC_API_VERSION", "2023-06-01")
            except Exception:
                pass
        except ImportError:
            pass
        
        # Hugging Face API version
        try:
            import transformers
            versions["transformers"] = transformers.__version__
            
            try:
                import datasets
                versions["datasets"] = datasets.__version__
            except ImportError:
                pass
        except ImportError:
            pass
        
        return versions
    
    def _generate_sampling_hash(self, state: LLMState) -> str:
        """Generate deterministic hash of sampling parameters"""
        # Create a deterministic representation of the sampling state
        hash_data = {
            "configurations": {
                provider: {
                    "provider": config.provider,
                    "model": config.model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "top_p": config.top_p,
                    "frequency_penalty": config.frequency_penalty,
                    "presence_penalty": config.presence_penalty,
                    "stop_sequences": config.stop_sequences,
                    "seed": config.seed,
                    "deterministic_mode": config.deterministic_mode
                }
                for provider, config in state.configurations.items()
            },
            "global_seed": state.global_seed,
            "deterministic_mode": state.deterministic_mode,
            "tokenizer_versions": state.tokenizer_versions,
            "model_versions": state.model_versions,
            "api_versions": state.api_versions
        }
        
        # Convert to deterministic JSON string
        json_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def save_llm_state(self, state: LLMState, output_path: Path):
        """Save LLM state to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        state_dict = {
            "configurations": {
                provider: {
                    "provider": config.provider,
                    "model": config.model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "top_p": config.top_p,
                    "frequency_penalty": config.frequency_penalty,
                    "presence_penalty": config.presence_penalty,
                    "stop_sequences": config.stop_sequences,
                    "seed": config.seed,
                    "deterministic_mode": config.deterministic_mode
                }
                for provider, config in state.configurations.items()
            },
            "global_seed": state.global_seed,
            "deterministic_mode": state.deterministic_mode,
            "tokenizer_versions": state.tokenizer_versions,
            "model_versions": state.model_versions,
            "api_versions": state.api_versions,
            "sampling_hash": state.sampling_hash
        }
        
        with open(output_path, 'w') as f:
            json.dump(state_dict, f, indent=2, sort_keys=True)
        
        self.logger.info(f"LLM state saved to: {output_path}")
    
    def validate_reproducibility(self, state1: LLMState, state2: LLMState) -> bool:
        """Validate that two LLM states are reproducible"""
        return (
            state1.global_seed == state2.global_seed and
            state1.deterministic_mode == state2.deterministic_mode and
            state1.tokenizer_versions == state2.tokenizer_versions and
            state1.model_versions == state2.model_versions and
            state1.api_versions == state2.api_versions and
            state1.sampling_hash == state2.sampling_hash and
            self._compare_configurations(state1.configurations, state2.configurations)
        )
    
    def _compare_configurations(self, configs1: Dict[str, LLMConfiguration], 
                              configs2: Dict[str, LLMConfiguration]) -> bool:
        """Compare two sets of LLM configurations"""
        if set(configs1.keys()) != set(configs2.keys()):
            return False
        
        for provider in configs1:
            config1 = configs1[provider]
            config2 = configs2[provider]
            
            if (config1.provider != config2.provider or
                config1.model != config2.model or
                config1.temperature != config2.temperature or
                config1.max_tokens != config2.max_tokens or
                config1.top_p != config2.top_p or
                config1.frequency_penalty != config2.frequency_penalty or
                config1.presence_penalty != config2.presence_penalty or
                config1.stop_sequences != config2.stop_sequences or
                config1.seed != config2.seed or
                config1.deterministic_mode != config2.deterministic_mode):
                return False
        
        return True
    
    def set_deterministic_mode(self, enabled: bool = True):
        """Set deterministic mode for all LLM providers"""
        env_vars = [
            "LLM_DETERMINISTIC",
            "OPENAI_DETERMINISTIC", 
            "ANTHROPIC_DETERMINISTIC",
            "HF_DETERMINISTIC"
        ]
        
        for var in env_vars:
            os.environ[var] = "true" if enabled else "false"
        
        # Set seeds for reproducibility
        if enabled:
            os.environ.setdefault("LLM_GLOBAL_SEED", "42")
            os.environ.setdefault("OPENAI_SEED", "42")
            os.environ.setdefault("ANTHROPIC_SEED", "42")
            os.environ.setdefault("HF_SEED", "42")
            
            # Set temperature to 0 for deterministic output
            os.environ.setdefault("OPENAI_TEMPERATURE", "0.0")
            os.environ.setdefault("ANTHROPIC_TEMPERATURE", "0.0")
            os.environ.setdefault("HF_TEMPERATURE", "0.0")
        
        self.logger.info(f"Deterministic mode {'enabled' if enabled else 'disabled'}")


def validate_llm_state_tracking():
    """Validate LLM state tracking functionality"""
    print("Validating LLM state tracking...")
    
    tracker = LLMStateTracker()
    
    # Enable deterministic mode
    tracker.set_deterministic_mode(True)
    
    # Capture state
    state = tracker.capture_llm_state()
    
    print(f"✅ LLM State Hash: {state.sampling_hash}")
    print(f"✅ Global Seed: {state.global_seed}")
    print(f"✅ Deterministic Mode: {state.deterministic_mode}")
    print(f"✅ Configurations: {list(state.configurations.keys())}")
    print(f"✅ Tokenizer Versions: {len(state.tokenizer_versions)} tracked")
    print(f"✅ Model Versions: {len(state.model_versions)} tracked")
    print(f"✅ API Versions: {len(state.api_versions)} tracked")
    
    # Test reproducibility
    state2 = tracker.capture_llm_state()
    is_reproducible = tracker.validate_reproducibility(state, state2)
    print(f"✅ Reproducibility Test: {'PASS' if is_reproducible else 'FAIL'}")
    
    # Save state
    output_path = Path("llm_state_test.json")
    tracker.save_llm_state(state, output_path)
    print(f"✅ LLM state saved to: {output_path}")
    
    # Test configuration details
    for provider, config in state.configurations.items():
        print(f"✅ {provider.upper()}: {config.model} (temp={config.temperature}, seed={config.seed})")
    
    return state


if __name__ == "__main__":
    validate_llm_state_tracking()