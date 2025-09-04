#!/usr/bin/env python3
import asyncio
import os
import openai

async def test_openai_models():
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.AsyncOpenAI(api_key=api_key)
    
    models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "o3-mini", "o3", "o4-mini"]
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            print(f"✅ {model} works!")
        except openai.NotFoundError as e:
            print(f"❌ {model} not found: {e}")
        except openai.BadRequestError as e:
            print(f"❌ {model} bad request: {e}")
        except Exception as e:
            print(f"❌ {model} error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_models())