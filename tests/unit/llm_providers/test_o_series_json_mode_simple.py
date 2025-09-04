#!/usr/bin/env python3
"""
Simple synchronous script demonstrating O3/O4 models with JSON mode
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_json_mode():
    """Simple test of JSON mode with O-series models"""
    
    # Initialize client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "o4-mini")
    
    print(f"Testing {model} with JSON mode")
    print("-" * 40)
    
    # Simple schema request
    system_prompt = """Return a JSON object with this structure:
    {
        "analysis": "your analysis",
        "confidence": 0.0 to 1.0,
        "key_points": ["point1", "point2", ...],
        "recommendation": "your recommendation"
    }"""
    
    user_prompt = "Analyze the benefits of using structured outputs in LLM applications"
    
    try:
        # Call with JSON mode enabled
        if model.startswith("o3") or model.startswith("o4"):
            # O-series specific parameters
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=1000,  # O-series uses this instead of max_tokens
                response_format={"type": "json_object"}  # Enable JSON mode
            )
        else:
            # Standard model parameters
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}  # Enable JSON mode
            )
        
        # Parse and display result
        result = json.loads(response.choices[0].message.content)
        print(json.dumps(result, indent=2))
        
        # Validate structure
        expected_keys = ["analysis", "confidence", "key_points", "recommendation"]
        missing_keys = [k for k in expected_keys if k not in result]
        
        if not missing_keys:
            print("\n✅ All expected fields present")
        else:
            print(f"\n⚠️ Missing fields: {missing_keys}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if "does not exist" in str(e):
            print("\nMake sure OPENAI_MODEL is set to a valid model like:")
            print("- o3-mini, o4-mini (O-series)")
            print("- gpt-4o, gpt-4o-mini (standard models)")


if __name__ == "__main__":
    test_json_mode()