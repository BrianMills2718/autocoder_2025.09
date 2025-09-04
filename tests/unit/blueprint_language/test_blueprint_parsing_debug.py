#!/usr/bin/env python3
"""Debug blueprint parsing issue"""

from pathlib import Path
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser

def test_simple_blueprint():
    """Test parsing the simple blueprint to see exact error"""
    
    print("Testing blueprint parsing...")
    
    # Read the simple test blueprint
    blueprint_file = Path("simple_test_blueprint_fixed.yaml")
    
    if not blueprint_file.exists():
        print(f"Blueprint file not found: {blueprint_file}")
        return
    
    # Create parser
    parser = SystemBlueprintParser()
    
    try:
        # Parse the blueprint
        print(f"Parsing: {blueprint_file}")
        parsed = parser.parse_file(blueprint_file)
        print("✅ Blueprint parsing successful!")
        print(f"System name: {parsed.system.name}")
        print(f"Components: {[c.name for c in parsed.system.components]}")
        print(f"Bindings: {len(parsed.system.bindings)}")
        
        # Show binding details
        for i, binding in enumerate(parsed.system.bindings):
            print(f"\nBinding {i+1}:")
            print(f"  From: {binding.from_component}.{binding.from_port}")
            print(f"  To: {binding.to_components} ports {binding.to_ports}")
            
    except Exception as e:
        print(f"❌ Blueprint parsing failed: {e}")
        
        # Check validation errors
        if parser.validation_errors:
            print("\nValidation errors:")
            for error in parser.validation_errors:
                print(f"  - {error.path}: {error.message}")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_blueprint()