#!/usr/bin/env python3
"""
Test o4-mini model with OpenAI provider to ensure proper parameter handling
"""
import asyncio
import os
from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest

async def test_o4_mini_provider():
    """Test that o4-mini works correctly with the OpenAI provider"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Test with o4-mini as default model
    config = {
        "api_key": api_key,
        "default_model": "o4-mini"
    }
    
    provider = OpenAIProvider(config)
    print(f"✅ Provider initialized with default model: {provider.default_model}")
    print(f"✅ o4-mini in O3_MODELS: {'o4-mini' in provider.O3_MODELS}")
    
    # Test a simple request
    request = LLMRequest(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say 'Hello from o4-mini' and nothing else.",
        max_tokens=50,
        temperature=0.3
    )
    
    try:
        print("🔄 Making request with o4-mini...")
        response = await provider.generate(request)
        print(f"✅ Success! Response: '{response.content}'")
        print(f"✅ Provider: {response.provider}, Model: {response.model}")
        print(f"✅ Tokens used: {response.tokens_used}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_o4_mini_provider())