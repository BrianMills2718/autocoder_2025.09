#!/usr/bin/env python3
"""Test component generation directly"""

import asyncio
import os
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

async def test_component_generation():
    # Force Gemini provider
    os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', '')
    
    generator = LLMComponentGenerator({
        'llm_providers': {
            'primary_provider': 'gemini',
            'fallback_providers': [],
            'max_retries': 3
        }
    })
    
    # Test a simple APIEndpoint component
    component_type = "APIEndpoint"
    component_name = "hello_world_endpoint"
    component_description = "Simple Hello World API endpoint that returns a greeting message"
    component_config = {
        "port": 8080,
        "message": "Hello, World!"
    }
    class_name = "GeneratedAPIEndpoint_hello_world_endpoint"
    
    print(f"Testing component generation for {component_type}: {component_name}")
    print(f"Description: {component_description}")
    print(f"Config: {component_config}")
    print("\n" + "="*80 + "\n")
    
    try:
        # Generate the component
        generated_code = await generator.generate_component_implementation(
            component_type=component_type,
            component_name=component_name,
            component_description=component_description,
            component_config=component_config,
            class_name=class_name
        )
        
        print("Generated code:")
        print(generated_code)
        
        # Check the size
        print(f"\n{'='*80}")
        print(f"Generated code size: {len(generated_code)} characters")
        print(f"Generated code lines: {len(generated_code.splitlines())}")
        
        # Save to file for inspection
        with open("test_generated_component.py", "w") as f:
            f.write(generated_code)
        print(f"\nSaved to test_generated_component.py")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_component_generation())