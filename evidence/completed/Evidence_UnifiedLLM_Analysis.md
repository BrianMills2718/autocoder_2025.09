# Evidence: UnifiedLLMProvider API Analysis

**Date**: 2025-08-26  
**File Analyzed**: `autocoder_cc/llm_providers/unified_llm_provider.py`

## Main Class: UnifiedLLMProvider

### Constructor
```python
def __init__(self, config: Dict[str, Any] = None)
```
- Loads environment variables
- Configures fallback sequence
- Initializes LiteLLM

### Core Methods

#### 1. `generate(request: LLMRequest) -> LLMResponse` (async)
- **Purpose**: Generate response with automatic fallback
- **Input**: LLMRequest object
- **Output**: LLMResponse object
- **Features**: 
  - Automatic retry with fallback models
  - Timeout management via centralized timeout_manager
  - Support for JSON mode

#### 2. `generate_sync(request: LLMRequest) -> LLMResponse` (sync)
- **Note**: Not present in current implementation - needs to be added or use async

#### 3. `health_check() -> bool` (async)
- **Purpose**: Simple health check of primary model
- **Returns**: Boolean indicating service availability

#### 4. `get_available_models() -> List[str]`
- **Purpose**: Get list of configured models
- **Returns**: List of model names

## Request/Response Data Structures

### LLMRequest (from base_provider.py)
```python
@dataclass
class LLMRequest:
    system_prompt: str       # System instructions
    user_prompt: str        # User's query
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    json_mode: bool = False # For structured output
```

### LLMResponse (from base_provider.py)
```python
@dataclass
class LLMResponse:
    content: str            # Generated text
    provider: str           # Provider name (gemini, openai, etc)
    model: str             # Model identifier
    tokens_used: int       # Token count
    cost_usd: float        # Cost estimate
    response_time: float   # Generation time
    metadata: Dict[str, Any] = {}
```

## Configuration Requirements

### Environment Variables
- `OPENAI_API_KEY`: For OpenAI models
- `GEMINI_API_KEY`: For Google Gemini models
- `ANTHROPIC_API_KEY`: For Anthropic Claude models

### Config Dictionary (optional)
```python
{
    'enable_fallback': bool,  # Default: False (fail fast)
    'primary_model': str,     # Default: 'gemini_2_5_flash'
}
```

## Model Configuration
Three models configured:
1. **gemini_2_5_flash**: Primary model, supports structured output
2. **openai_gpt4o_mini**: Fallback 1, OpenAI mini model
3. **claude_sonnet_4**: Fallback 2, Anthropic Claude

## Key Features
- Uses LiteLLM for all provider interactions
- Centralized timeout management via `timeout_manager`
- Automatic fallback sequence (if enabled)
- Fail-fast mode by default
- Structured output support (JSON mode)

## Integration Requirements for natural_language_to_blueprint.py

### Current Issues to Fix:
1. Direct provider imports (openai, gemini, anthropic) - REMOVE
2. Manual provider detection logic - REMOVE
3. Custom retry logic - REPLACE with UnifiedLLMProvider
4. Manual response wrapping (GeminiWrapper) - REMOVE

### New Integration Pattern:
1. Import UnifiedLLMProvider and LLMRequest
2. Initialize UnifiedLLMProvider in __init__
3. Convert messages to LLMRequest format
4. Use async generate() or create sync wrapper
5. Handle LLMResponse format

## Compatibility Notes
- UnifiedLLMProvider is async by default
- Need to handle async/sync conversion for translate_to_intermediate
- Response format differs from OpenAI - needs wrapper for compatibility