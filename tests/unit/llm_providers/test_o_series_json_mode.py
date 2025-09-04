#!/usr/bin/env python3
"""
Standalone script demonstrating O3/O4 models using JSON mode (structured outputs)
This script shows how to use OpenAI's O-series models with JSON mode enabled.
"""

import os
import json
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import OpenAI client
try:
    import openai
except ImportError:
    print("Please install openai: pip install openai")
    exit(1)


async def test_o_series_json_mode():
    """Test O3/O4 models with JSON mode (structured outputs)"""
    
    # Get API key and model from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "o4-mini")  # Default to o4-mini
    
    if not api_key:
        print("Error: OPENAI_API_KEY not set in environment")
        return
    
    # Initialize client
    client = openai.AsyncOpenAI(api_key=api_key)
    
    print(f"Testing {model} with JSON mode (structured outputs)")
    print("-" * 60)
    
    # Define the schema we want the model to follow
    schema_description = """
    Generate a JSON object with the following structure:
    {
        "task": "string - the task being performed",
        "model": "string - the model being used",
        "reasoning_steps": ["array of strings - step by step reasoning"],
        "result": {
            "success": "boolean",
            "confidence": "number between 0 and 1",
            "explanation": "string"
        },
        "metadata": {
            "timestamp": "ISO 8601 timestamp",
            "version": "string"
        }
    }
    """
    
    # Example prompts to test JSON generation
    test_prompts = [
        {
            "name": "Math Problem",
            "prompt": "Solve this problem: What is 15% of 240? Show your reasoning steps."
        },
        {
            "name": "Code Analysis",
            "prompt": "Analyze this Python code: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
        },
        {
            "name": "Data Structure",
            "prompt": "Design a simple user profile structure for a social media app"
        }
    ]
    
    for test in test_prompts:
        print(f"\n## Test: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print("\nResponse:")
        
        try:
            # Prepare the request based on model type
            if model.startswith("o3") or model.startswith("o4"):
                # O-series models: use max_completion_tokens, no temperature
                # JSON mode is supported
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a helpful assistant that always responds with valid JSON. {schema_description}"
                        },
                        {
                            "role": "user", 
                            "content": test['prompt']
                        }
                    ],
                    max_completion_tokens=2000,
                    response_format={"type": "json_object"}  # Enable JSON mode
                )
            else:
                # Standard models: use max_tokens and temperature
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a helpful assistant that always responds with valid JSON. {schema_description}"
                        },
                        {
                            "role": "user", 
                            "content": test['prompt']
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3,
                    response_format={"type": "json_object"}  # Enable JSON mode if supported
                )
            
            # Extract and parse the JSON response
            json_response = response.choices[0].message.content
            
            # Pretty print the JSON
            try:
                parsed = json.loads(json_response)
                print(json.dumps(parsed, indent=2))
                
                # Validate structure
                print("\n✅ Valid JSON structure")
                if all(key in parsed for key in ["task", "model", "reasoning_steps", "result", "metadata"]):
                    print("✅ All required fields present")
                else:
                    print("⚠️ Some required fields missing")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                print(f"Raw response: {json_response}")
            
            # Show token usage
            if hasattr(response, 'usage'):
                print(f"\nTokens used: {response.usage.total_tokens}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Check if it's a model availability error
            if "model" in str(e).lower() and "does not exist" in str(e).lower():
                print(f"\n⚠️ Model '{model}' not available. Set OPENAI_MODEL to a valid model.")
                print("Available O-series models might include: o3-mini, o4-mini")
                print("Standard models: gpt-4o, gpt-4o-mini, gpt-4-turbo")


async def test_structured_output_with_schema():
    """Test with explicit schema definition (if O-series supports it)"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "o4-mini")
    
    if not api_key:
        return
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    print(f"\n\n## Testing Structured Output with Schema")
    print("-" * 60)
    
    # Define a more complex schema
    system_prompt = """You are a component analyzer. Analyze the given component and return a JSON object with this exact structure:
{
  "component_analysis": {
    "name": "string",
    "type": "string", 
    "complexity": "low|medium|high",
    "dependencies": ["array of strings"],
    "interfaces": {
      "inputs": ["array of input descriptions"],
      "outputs": ["array of output descriptions"]
    },
    "implementation_notes": ["array of important notes"],
    "estimated_lines_of_code": "number"
  }
}"""

    user_prompt = """Analyze this component specification:
Component: InventoryTracker
Type: Store
Description: Tracks product inventory levels, handles stock updates, and generates low-stock alerts
Configuration: 
  - database: PostgreSQL
  - cache: Redis
  - alert_threshold: 10 units"""

    try:
        if model.startswith("o3") or model.startswith("o4"):
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        
        # Parse and display
        json_response = response.choices[0].message.content
        parsed = json.loads(json_response)
        print(json.dumps(parsed, indent=2))
        
        # Validate the structure matches our schema
        if "component_analysis" in parsed:
            analysis = parsed["component_analysis"]
            required_fields = ["name", "type", "complexity", "dependencies", "interfaces", "implementation_notes", "estimated_lines_of_code"]
            
            missing = [field for field in required_fields if field not in analysis]
            if missing:
                print(f"\n⚠️ Missing fields: {missing}")
            else:
                print("\n✅ All required fields present in schema")
                
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests"""
    
    print("=" * 60)
    print("O-Series Models JSON Mode (Structured Outputs) Test")
    print("=" * 60)
    print(f"Environment: OPENAI_MODEL={os.getenv('OPENAI_MODEL', 'o4-mini')}")
    print(f"API Key Set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print("=" * 60)
    
    # Run basic JSON mode test
    await test_o_series_json_mode()
    
    # Run structured output with schema test
    await test_structured_output_with_schema()
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    
    # Show configuration tips
    print("\nConfiguration Tips:")
    print("1. Set OPENAI_API_KEY in your .env file")
    print("2. Set OPENAI_MODEL to one of: o3-mini, o4-mini, gpt-4o, gpt-4o-mini")
    print("3. O-series models use max_completion_tokens instead of max_tokens")
    print("4. O-series models don't support temperature parameter")
    print("5. JSON mode ensures structured output without prompt engineering")


if __name__ == "__main__":
    asyncio.run(main())