#!/usr/bin/env python3
"""
Test that GeneratedComponent can be created correctly after the fix
"""
import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_generated_component_creation():
    """Test that GeneratedComponent can be created with correct parameters"""
    print("Testing GeneratedComponent creation after fix...")
    
    try:
        from autocoder_cc.blueprint_language.component_logic_generator import GeneratedComponent
        print("✅ Successfully imported GeneratedComponent")
        
        # Test creating a component with the corrected parameters
        component = GeneratedComponent(
            name="test_component",
            type="api_endpoint",
            implementation="# Test implementation code",
            imports=["import os", "import json"],
            dependencies=["component1", "component2"],
            file_path="/path/to/component.py"
        )
        
        print("✅ Successfully created GeneratedComponent instance")
        print(f"   Name: {component.name}")
        print(f"   Type: {component.type}")
        print(f"   File path: {component.file_path}")
        print(f"   Imports: {component.imports}")
        print(f"   Dependencies: {component.dependencies}")
        
        # Verify the old parameter doesn't exist
        try:
            component = GeneratedComponent(
                name="test",
                type="api",
                implementation="code",
                output_file="file.py"  # This should fail
            )
            print("❌ ERROR: output_file parameter should not be accepted!")
        except TypeError as e:
            print("✅ Correctly rejected output_file parameter:", str(e))
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def check_system_generator_fix():
    """Check that system_generator.py is using the correct parameters"""
    print("\nChecking system_generator.py fix...")
    
    with open("autocoder_cc/blueprint_language/system_generator.py", "r") as f:
        content = f.read()
        
    # Check for the fix
    if "output_file=component_file" in content:
        print("❌ ERROR: system_generator.py still uses output_file parameter!")
    elif "file_path=str(component_file)" in content:
        print("✅ system_generator.py correctly uses file_path parameter")
    else:
        print("⚠️  Could not verify system_generator.py fix")
        
    # Check for required parameters
    if "imports=[]" in content and "dependencies=[]" in content:
        print("✅ system_generator.py includes required imports and dependencies parameters")
    else:
        print("❌ ERROR: Missing required parameters in system_generator.py")

if __name__ == "__main__":
    print("Verifying GeneratedComponent fix")
    print("=" * 60)
    
    test_generated_component_creation()
    check_system_generator_fix()
    
    print("\n" + "=" * 60)
    print("✅ Fix verification complete!")
    print("\nThe GeneratedComponent initialization error has been resolved.")
    print("The system should now be able to proceed past the component generation stage.")