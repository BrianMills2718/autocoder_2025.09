#!/usr/bin/env python3
"""
Standalone test to demonstrate o4-mini model usage
"""
import os
import asyncio
from openai import AsyncOpenAI

async def test_o4_mini():
    """Test o4-mini model with correct parameters"""
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    try:
        # Test 1: Basic completion with o4-mini specific parameters
        print("Test 1: Basic o4-mini completion")
        response = await client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a simple Python function that adds two numbers."}
            ],
            max_completion_tokens=150  # o4-mini uses max_completion_tokens, not max_tokens
            # Note: NO temperature parameter for o4-mini
        )
        
        print(f"✅ Success! Response:")
        print(response.choices[0].message.content)
        print(f"\nTokens used: {response.usage.total_tokens}")
        
        # Test 2: Verify temperature is rejected
        print("\n\nTest 2: Verify temperature parameter is rejected")
        try:
            response = await client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,  # This should fail
                max_completion_tokens=50
            )
            print("❌ ERROR: Temperature parameter was accepted (should have been rejected)")
        except Exception as e:
            print(f"✅ Correct: Temperature parameter rejected with error: {e}")
        
        # Test 3: Verify max_tokens is rejected in favor of max_completion_tokens
        print("\n\nTest 3: Verify max_tokens vs max_completion_tokens")
        try:
            response = await client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=50  # This should fail or be ignored
            )
            print("⚠️  Warning: max_tokens parameter was accepted (should use max_completion_tokens)")
        except Exception as e:
            print(f"✅ Correct: max_tokens parameter rejected with error: {e}")
            
        # Test 4: Proper usage with reasoning effort
        print("\n\nTest 4: O4-mini with reasoning effort parameter")
        response = await client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "user", "content": "What is 25 * 37? Show your work."}
            ],
            max_completion_tokens=200,
            reasoning_effort="medium"  # O4 models support reasoning effort
        )
        print(f"✅ Success with reasoning effort!")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    print("Testing o4-mini model parameters...\n")
    asyncio.run(test_o4_mini())