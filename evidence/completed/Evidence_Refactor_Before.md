# Evidence: Code Before Refactoring

**Date**: 2025-08-26  
**File**: `autocoder_cc/blueprint_language/natural_language_to_blueprint.py`

## Current Implementation Issues

### 1. Direct Provider Imports (Lines 7-8, 74)
```python
from openai import OpenAI
import google.generativeai as genai
# ...
import anthropic  # Line 74
```

### 2. Manual Provider Detection and Initialization (Lines 33-81)
```python
def __init__(self, llm_client=None):
    self.provider = settings.get_llm_provider()
    self.model = settings.get_llm_model()
    
    if llm_client:
        self.llm_client = llm_client
    else:
        # Manual API key detection for each provider
        api_key = settings.get_llm_api_key()
        if not api_key:
            if self.provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif self.provider == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY")
            elif self.provider == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Manual client initialization per provider
        if self.provider == "openai":
            self.llm_client = OpenAI(api_key=api_key)
        elif self.provider == "gemini":
            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel(self.model)
        elif self.provider == "anthropic":
            import anthropic
            self.llm_client = anthropic.Anthropic(api_key=api_key)
```

### 3. Complex Provider-Specific Call Logic (Lines 897-989)
```python
def _call_llm_with_retries(self, completion_params: Dict[str, Any]):
    # Custom circuit breaker logic
    if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
        raise NaturalLanguageTranslationError(...)
    
    for attempt in range(self.max_retries + 1):
        try:
            # Provider-specific API calls
            if self.provider == "gemini":
                # Complex Gemini-specific message formatting
                messages = completion_params.get("messages", [])
                prompt_parts = []
                for msg in messages:
                    if msg['role'] == 'system':
                        prompt_parts.append(f"INSTRUCTIONS:\n{msg['content']}\n")
                    elif msg['role'] == 'user':
                        prompt_parts.append(f"USER REQUEST:\n{msg['content']}\n")
                prompt = "\n".join(prompt_parts) + "\nRESPONSE (JSON only):"
                
                response = self.llm_client.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=8192,
                    )
                )
                
                # Custom wrapper to match OpenAI format
                class GeminiWrapper:
                    class Choice:
                        class Message:
                            def __init__(self, content):
                                self.content = content
                                self.refusal = None
                        def __init__(self, content):
                            self.message = self.Message(content)
                    def __init__(self, text):
                        self.choices = [self.Choice(text)]
                
                response = GeminiWrapper(response.text)
            else:
                # OpenAI/Anthropic API
                response = self.llm_client.chat.completions.create(**params_with_timeout)
            
            # Custom retry logic with exponential backoff
            # ...
```

## Problems Identified

1. **Duplicate Logic**: Provider detection, API key handling, and retry logic duplicate what's in UnifiedLLMProvider
2. **Manual Wrapping**: GeminiWrapper class manually converts responses - error-prone
3. **No Litellm**: Doesn't leverage litellm's unified interface
4. **Complex Error Handling**: Custom circuit breaker and retry logic that could fail
5. **JSON Parsing Issues**: Gemini responses fail to parse correctly (as reported in error)

## Files That Need Changes

1. **natural_language_to_blueprint.py**:
   - Remove lines 7-8 (OpenAI and Gemini imports)
   - Remove line 74 (Anthropic import)
   - Replace __init__ method (lines 33-81)
   - Replace _call_llm_with_retries method (lines 897-989)
   - Update translate_to_intermediate to work with new response format

## Code to Remove
- ~500 lines of provider-specific code
- GeminiWrapper class
- Circuit breaker implementation
- Manual retry logic
- Provider detection code