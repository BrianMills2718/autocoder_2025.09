#!/usr/bin/env python3
"""
Test LLM connection with improved timeout settings
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_llm_connection():
    """Test OpenAI API connection with various timeout settings"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    client = OpenAI(api_key=api_key)
    
    # Test with different timeouts
    for timeout in [30, 60, 120]:
        print(f"\n🔄 Testing with {timeout}s timeout...")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, World!' in Python"}
                ],
                max_tokens=100,
                timeout=timeout
            )
            
            if response.choices and response.choices[0].message.content:
                print(f"✅ Success with {timeout}s timeout!")
                print(f"   Response: {response.choices[0].message.content[:50]}...")
                return True
            else:
                print(f"❌ Empty response with {timeout}s timeout")
        
        except Exception as e:
            print(f"❌ Failed with {timeout}s timeout: {e}")
    
    return False

if __name__ == "__main__":
    print("🔌 Testing LLM API Connection...")
    success = test_llm_connection()
    
    if success:
        print("\n✅ LLM connection test passed! You can try running the system generation again.")
    else:
        print("\n❌ LLM connection test failed. Please check:")
        print("   1. Your OPENAI_API_KEY is correctly set")
        print("   2. Your internet connection is stable") 
        print("   3. OpenAI API service status")
        print("   4. Consider using a different model or provider")