#!/usr/bin/env python3
"""
Simple script to test P1.5 system recovery fixes
"""
import asyncio
from pathlib import Path
import sys
import tempfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.observability.pipeline_metrics import pipeline_metrics


async def test_system_recovery():
    """Test the complete pipeline after P1.5 fixes"""
    
    print("=" * 60)
    print("P1.5 SYSTEM RECOVERY TEST")
    print("=" * 60)
    
    try:
        # Test 1: Generate blueprint from natural language
        print("\n1. Testing Natural Language to Blueprint Conversion...")
        converter = NaturalLanguageToPydanticTranslator()
        
        test_description = "Simple data processing system with API endpoint"
        blueprint_yaml = converter.generate_full_blueprint(test_description)
        
        print("✅ Blueprint generated successfully!")
        print(f"   Length: {len(blueprint_yaml)} characters")
        
        # Check schema_version position
        lines = blueprint_yaml.split('\n')
        if lines[0].startswith('schema_version:'):
            print("✅ schema_version correctly positioned at root")
        else:
            print("❌ schema_version NOT at root position!")
            return False
        
        # Test 2: Parse the blueprint
        print("\n2. Testing Blueprint Parsing with Healing...")
        parser = SystemBlueprintParser()
        parsed = parser.parse_string(blueprint_yaml)
        
        print("✅ Blueprint parsed successfully!")
        print(f"   System name: {parsed.system.name}")
        print(f"   Components: {len(parsed.system.components)}")
        
        # Test 3: Check pipeline metrics
        print("\n3. Checking Pipeline Metrics...")
        summary = pipeline_metrics.get_pipeline_summary()
        
        if summary['critical_errors']:
            print("❌ Critical errors detected!")
            return False
        else:
            print("✅ No critical errors in pipeline")
        
        print(f"   Stages completed: {summary['stages_completed']}")
        print(f"   Total duration: {summary['total_duration_seconds']:.2f}s")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - System recovery successful!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test"""
    success = asyncio.run(test_system_recovery())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()