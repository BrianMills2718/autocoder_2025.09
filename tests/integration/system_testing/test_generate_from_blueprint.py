#!/usr/bin/env python3
"""Test system generation from a blueprint file"""

import sys
import asyncio
from pathlib import Path
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser

async def test_blueprint_generation():
    """Test generating system from blueprint file"""
    
    # Use the fixed blueprint
    blueprint_file = Path("simple_test_blueprint_fixed.yaml")
    
    print(f"Testing system generation from: {blueprint_file}")
    print("="*60)
    
    # First test parsing
    parser = SystemBlueprintParser()
    
    try:
        print("1. Testing blueprint parsing...")
        parsed = parser.parse_file(blueprint_file)
        print(f"✅ Blueprint parsed successfully!")
        print(f"   System: {parsed.system.name}")
        print(f"   Components: {[c.name for c in parsed.system.components]}")
        print(f"   Bindings: {len(parsed.system.bindings)}")
    except Exception as e:
        print(f"❌ Blueprint parsing failed: {e}")
        return False
    
    # Now test generation
    try:
        print("\n2. Testing system generation...")
        with Path("test_output") as output_dir:
            generator = SystemGenerator(output_dir, verbose_logging=True)
            
            # Generate system
            result = await generator.generate_system(blueprint_file)
            
            print(f"✅ System generated successfully!")
            print(f"   Output: {result.output_directory}")
            print(f"   Components: {len(result.components)}")
            
            # Check component files
            components_dir = result.output_directory / "components"
            if components_dir.exists():
                component_files = list(components_dir.glob("*.py"))
                print(f"   Component files: {[f.name for f in component_files]}")
            
            return True
            
    except Exception as e:
        print(f"❌ System generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_blueprint_generation())
    sys.exit(0 if success else 1)