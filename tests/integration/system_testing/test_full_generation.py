#!/usr/bin/env python3
"""
Full end-to-end system generation test
This attempts to generate a complete system from natural language
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.observability.pipeline_metrics import PipelineStageMetrics, PipelineStage
import yaml


async def test_full_generation():
    """Test complete system generation from natural language"""
    
    print("=" * 60)
    print("FULL END-TO-END SYSTEM GENERATION TEST")
    print("=" * 60)
    
    # Initialize metrics
    metrics = PipelineStageMetrics()
    
    # Test description
    description = """
    Create a simple data processing pipeline with the following components:
    1. A CSV file reader that monitors a directory for new files
    2. A data transformer that validates and cleans the data
    3. A database writer that stores the processed data
    """
    
    print(f"\nSystem Description:")
    print(description.strip())
    print("\n" + "-" * 60)
    
    # Create temporary output directory
    output_dir = Path(tempfile.mkdtemp(prefix="test_generation_"))
    print(f"\nOutput Directory: {output_dir}")
    
    try:
        # Step 1: Natural Language to Blueprint
        print("\n📝 Step 1: Converting natural language to blueprint...")
        metrics.start_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION)
        
        converter = NaturalLanguageToPydanticTranslator()
        blueprint_yaml = converter.generate_full_blueprint(description)
        
        # Save blueprint
        blueprint_file = output_dir / "system_blueprint.yaml"
        with open(blueprint_file, 'w') as f:
            f.write(blueprint_yaml)
        
        print(f"✅ Blueprint generated: {blueprint_file}")
        print(f"   Size: {len(blueprint_yaml)} characters")
        
        # Show blueprint preview
        lines = blueprint_yaml.split('\n')[:20]
        print("\nBlueprint Preview:")
        for line in lines:
            print(f"   {line}")
        if len(blueprint_yaml.split('\n')) > 20:
            print(f"   ... ({len(blueprint_yaml.split('\n')) - 20} more lines)")
        
        metrics.end_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION, success=True)
        
        # Step 2: Parse Blueprint
        print("\n🔍 Step 2: Parsing blueprint...")
        metrics.start_stage(PipelineStage.BLUEPRINT_PARSING)
        
        parser = SystemBlueprintParser()
        parsed_blueprint = parser.parse_string(blueprint_yaml)
        
        print(f"✅ Blueprint parsed successfully")
        print(f"   System: {parsed_blueprint.system.name}")
        print(f"   Components: {len(parsed_blueprint.system.components)}")
        for comp in parsed_blueprint.system.components:
            print(f"     - {comp.name} ({comp.type})")
        
        metrics.end_stage(PipelineStage.BLUEPRINT_PARSING, success=True)
        
        # Step 3: Generate System (if API keys are available)
        print("\n🚀 Step 3: Generating system components...")
        
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            print("⚠️  No API keys found - skipping component generation")
            print("   Set OPENAI_API_KEY or GEMINI_API_KEY to enable full generation")
            return
        
        metrics.start_stage(PipelineStage.COMPONENT_GENERATION)
        
        generator = SystemGenerator(output_dir)
        
        # Use a timeout for generation
        print("   Generating components (this may take a minute)...")
        
        try:
            # The actual generation method might vary - adjust as needed
            # Use centralized timeout manager instead of hardcoded timeout
            result = await generator.generate_system_from_yaml(blueprint_yaml)
            
            print(f"✅ System generated successfully!")
            
            # List generated files
            component_dir = output_dir / "components"
            if component_dir.exists():
                component_files = list(component_dir.glob("*.py"))
                print(f"\n   Generated Components ({len(component_files)}):")
                for comp_file in component_files:
                    size = comp_file.stat().st_size
                    print(f"     - {comp_file.name} ({size} bytes)")
            
            metrics.end_stage(PipelineStage.COMPONENT_GENERATION, success=True)
            
        except asyncio.TimeoutError:
            print("❌ Generation timed out after 2 minutes")
            metrics.end_stage(PipelineStage.COMPONENT_GENERATION, success=False)
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            metrics.end_stage(PipelineStage.COMPONENT_GENERATION, success=False)
        
        # Summary
        print("\n" + "=" * 60)
        print("GENERATION SUMMARY")
        print("=" * 60)
        
        summary = metrics.get_pipeline_summary()
        print(f"Stages Completed: {summary['stages_completed']}")
        print(f"Stages Failed: {summary['stages_failed']}")
        print(f"Critical Errors: {'Yes' if summary['critical_errors'] else 'No'}")
        
        if summary['stages_completed'] >= 2:
            print("\n✅ Core pipeline functioning correctly!")
            print("   - Natural language → Blueprint: WORKING")
            print("   - Blueprint parsing: WORKING")
            if summary['stages_completed'] >= 3:
                print("   - Component generation: WORKING")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Keep output directory for inspection
        print(f"\n📁 Output preserved at: {output_dir}")
        print("   You can inspect the generated files there")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_full_generation())