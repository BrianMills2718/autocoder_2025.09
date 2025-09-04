#!/usr/bin/env python3
"""
Test LiteLLM acompletion directly to verify it works.
"""

import asyncio
import os
from dotenv import load_dotenv
from litellm import acompletion

# Load environment variables
load_dotenv()

async def test_direct_acompletion():
    """Test acompletion directly."""
    print("Testing LiteLLM acompletion directly...")
    
    try:
        # Make sure we have API key
        if not os.environ.get('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY not set")
            return False
            
        # Try with a higher max_tokens since it's hitting the length limit
        response = await acompletion(
            model="gemini/gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello world!' and nothing else."}
            ],
            max_tokens=100,  # Increased from 20
            temperature=0.0,
            timeout=10
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response id: {response.id}")
        print(f"Response model: {response.model}")
        print(f"Usage: {response.usage}")
        print(f"Finish reason: {response.choices[0].finish_reason if response.choices else 'NO CHOICES'}")
        
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            print(f"Choice: {choice}")
            message = choice.message
            print(f"Message: {message}")
            print(f"Message content: {message.content}")
            
            # Check if content is in a different field
            if hasattr(message, '__dict__'):
                print(f"Message attributes: {message.__dict__}")
            
            content = message.content
            if content:
                print(f"✅ Content: {content}")
                return True
            else:
                print("❌ Content is None")
                return False
        else:
            print("❌ No choices in response")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_direct_acompletion()
    print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())