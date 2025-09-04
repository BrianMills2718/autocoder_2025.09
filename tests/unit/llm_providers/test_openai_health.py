#!/usr/bin/env python3
import asyncio
import os
from autocoder_cc.llm_providers.openai_provider import OpenAIProvider

async def test_openai_health():
    # Create provider with config
    config = {
        "api_key": os.getenv("OPENAI_API_KEY", "test-key"),
        "default_model": "gpt-3.5-turbo"
    }
    
    provider = OpenAIProvider(config)
    
    print("Testing OpenAI health check...")
    print(f"API Key: {'***' + config['api_key'][-4:] if len(config['api_key']) > 4 else '***'}")
    print(f"Default Model: {provider.default_model}")
    
    try:
        result = await provider.health_check()
        print(f"Health check result: {result}")
    except Exception as e:
        print(f"Health check raised exception: {type(e).__name__}: {e}")
    
    # Also test the actual call to see what error we get
    print("\nTesting actual API call...")
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=config["api_key"])
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        print(f"API call successful! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"API call failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_health())