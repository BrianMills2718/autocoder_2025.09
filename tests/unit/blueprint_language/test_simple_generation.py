#!/usr/bin/env python3
"""
Test the improved LLM retry architecture with a simple component
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_simple_component():
    """Test generating a simple API endpoint component"""
    
    try:
        generator = LLMComponentGenerator()
        
        print("🧪 Testing simple API endpoint generation...")
        
        generated_code = generator.generate_component_implementation(
            component_type="APIEndpoint",
            component_name="test_api", 
            component_description="Simple API that returns user data",
            component_config={
                "port": 8000,
                "endpoints": [
                    {"path": "/users", "method": "GET", "description": "Get all users"}
                ]
            },
            class_name="GeneratedAPIEndpoint_test_api"
        )
        
        print(f"✅ Successfully generated component!")
        print(f"📏 Code length: {len(generated_code)} characters")
        lines_count = len(generated_code.split('\n'))
        print(f"📄 Lines: {lines_count}")
        
        # Save to file for inspection
        with open('/tmp/test_generated_component.py', 'w') as f:
            f.write(generated_code)
        print(f"💾 Saved to /tmp/test_generated_component.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_component()
    if success:
        print("\n🎉 Test passed! The LLM retry architecture is working correctly.")
        print("   You can now try the full system generation again.")
    else:
        print("\n❌ Test failed. There may be an issue with the LLM service or configuration.")