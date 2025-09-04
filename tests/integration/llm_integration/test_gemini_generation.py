#!/usr/bin/env python3
"""Test Gemini's raw component generation to debug syntax errors"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "autocoder_cc"))

from autocoder_cc.llm_providers.gemini_provider import GeminiProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest

async def test_gemini_generation():
    """Test Gemini's raw generation capabilities"""
    
    print("=== Testing Gemini Raw Generation ===\n")
    
    # Initialize Gemini provider
    config = {}  # Use default config
    provider = GeminiProvider(config)
    
    # Simple component generation prompt
    system_prompt = """You are an expert Python developer. Generate complete, working Python code.
The code must be syntactically correct and executable.
Do not include any explanations or markdown - just pure Python code."""
    
    user_prompt = """Generate a simple Python class called TicketStore that:
1. Has an __init__ method that initializes a dictionary to store tickets
2. Has a process_item method that takes a data dict and stores it with a UUID key
3. Has proper error handling with try/except blocks
4. Uses logging for errors

The code should be complete and syntactically correct."""
    
    request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,  # Low temperature for more deterministic output
        max_tokens=1000
    )
    
    try:
        print("Sending request to Gemini...")
        response = await provider.generate(request)
        
        print("✅ Received response")
        print(f"Response length: {len(response.content)} characters")
        print("\n--- Generated Code ---")
        print(response.content)
        print("--- End Generated Code ---\n")
        
        # Try to parse it
        try:
            compile(response.content, '<string>', 'exec')
            print("✅ Code compiles successfully!")
        except SyntaxError as e:
            print(f"❌ Syntax Error: {e}")
            print(f"   Line {e.lineno}: {e.text}")
            print(f"   {' ' * (e.offset - 1)}^")
            
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_generation())