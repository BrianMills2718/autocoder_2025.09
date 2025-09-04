#!/usr/bin/env python3
"""
Test Store/Sink component generation to verify the fixes are working
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "autocoder_cc"
sys.path.insert(0, str(project_root))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_store_component_generation():
    """Test that Store components are generated correctly"""
    generator = LLMComponentGenerator()
    
    print("Testing Store component generation...")
    
    # Test case 1: Store component
    store_code = generator.generate_component_implementation(
        component_type="Store",
        component_name="todo_store",
        component_description="A Store component that persists todo items to a database",
        component_config={"storage_type": "postgresql"},
        class_name="GeneratedStore_todo_store"
    )
    
    # Check the generated code
    if "GeneratedStore_todo_store" in store_code:
        print("✅ Store component has correct class name")
    else:
        print("❌ Store component has wrong class name")
        if "GeneratedSink_" in store_code:
            print("   ERROR: Generated Sink instead of Store!")
    
    # Test case 2: Sink component
    print("\nTesting Sink component generation...")
    
    sink_code = generator.generate_component_implementation(
        component_type="Sink",
        component_name="alert_sink",
        component_description="A Sink component that sends alerts to external services",
        component_config={"alert_type": "email"},
        class_name="GeneratedSink_alert_sink"
    )
    
    # Check the generated code
    if "GeneratedSink_alert_sink" in sink_code:
        print("✅ Sink component has correct class name")
    else:
        print("❌ Sink component has wrong class name")
        if "GeneratedStore_" in sink_code:
            print("   ERROR: Generated Store instead of Sink!")
    
    return store_code, sink_code

if __name__ == "__main__":
    try:
        store_code, sink_code = test_store_component_generation()
        
        # Save generated code for inspection
        with open("test_generated_store.py", "w") as f:
            f.write(store_code)
        
        with open("test_generated_sink.py", "w") as f:
            f.write(sink_code)
        
        print("\nGenerated code saved to test_generated_store.py and test_generated_sink.py")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()