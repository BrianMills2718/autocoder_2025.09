#!/usr/bin/env python3
"""Test script to debug component generation issues"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "autocoder_cc"))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
from autocoder_cc.llm_providers.base_provider import LLMRequest

async def test_component_generation():
    """Test component generation with a simple example"""
    
    # Initialize generator
    generator = LLMComponentGenerator()
    
    # Create a simple component specification
    component_spec = {
        "name": "hello_api",
        "type": "APIEndpoint",
        "config": {
            "port": 8080,
            "endpoints": [
                {
                    "path": "/hello",
                    "method": "GET",
                    "handler": "get_hello"
                }
            ]
        }
    }
    
    # Test generation
    print("=== Testing Component Generation ===\n")
    print(f"Component: {component_spec['name']} ({component_spec['type']})")
    print("-" * 50)
    
    try:
        # Enable debug mode to see what's happening
        generator.response_validator.debug_mode = True
        
        result = await generator.generate_component_implementation_enhanced(
            component_type=component_spec['type'],
            component_name=component_spec['name'],
            component_description="A simple hello world API endpoint",
            component_config=component_spec['config']
        )
        
        print("✅ Generation successful!")
        print(f"Generated code length: {len(result)} characters")
        print("\n--- First 500 characters ---")
        print(result[:500])
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_component_generation())