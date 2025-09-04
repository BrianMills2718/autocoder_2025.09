#!/usr/bin/env python3
"""
Debug LLM provider detection
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/brian/autocoder4_cc/autocoder_cc')

from autocoder_cc.core.config import settings

def test_provider_detection():
    """Test which LLM provider is being selected"""
    
    print("=== Environment Variables ===")
    print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'Not set')}")
    print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'Not set')}")
    print(f"ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY', 'Not set')}")
    print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'Not set')}")
    print(f"GEMINI_MODEL: {os.getenv('GEMINI_MODEL', 'Not set')}")
    
    print("\n=== Settings Configuration ===")
    print(f"settings.OPENAI_API_KEY: {settings.OPENAI_API_KEY}")
    print(f"settings.GEMINI_API_KEY: {settings.GEMINI_API_KEY}")
    print(f"settings.ANTHROPIC_API_KEY: {settings.ANTHROPIC_API_KEY}")
    print(f"settings.OPENAI_MODEL: {settings.OPENAI_MODEL}")
    print(f"settings.GEMINI_MODEL: {settings.GEMINI_MODEL}")
    
    print("\n=== Provider Detection Results ===")
    print(f"get_llm_api_key(): {settings.get_llm_api_key()}")
    print(f"get_llm_provider(): {settings.get_llm_provider()}")
    print(f"get_llm_model(): {settings.get_llm_model()}")

if __name__ == "__main__":
    test_provider_detection()