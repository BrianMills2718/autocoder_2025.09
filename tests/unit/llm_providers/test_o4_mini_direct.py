#!/usr/bin/env python3
"""
Test o4-mini directly with OpenAI client to debug response handling
"""
import asyncio
import os
import openai

async def test_o4_mini_direct():
    """Test o4-mini directly with OpenAI client"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    try:
        print("🔄 Making direct request to o4-mini...")
        response = await client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "user", "content": "Hello! Please respond with: 'o4-mini is working'"}
            ],
            max_completion_tokens=1000  # o4-mini uses max_completion_tokens
        )
        
        print(f"✅ Success! Response: '{response.choices[0].message.content}'")
        print(f"✅ Finish reason: {response.choices[0].finish_reason}")
        print(f"✅ Total tokens: {response.usage.total_tokens}")
        print(f"✅ Model: {response.model}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_o4_mini_direct())