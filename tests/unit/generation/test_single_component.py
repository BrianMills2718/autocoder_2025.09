#!/usr/bin/env python3
"""
Test Single Component Generation - Track import sources
"""

import asyncio
from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedComponent, ParsedPort, ParsedSystemBlueprint, ParsedSystem
from pathlib import Path
import tempfile

async def test_single_component():
    print("🔍 Testing Single Component Generation")
    print("=" * 50)
    
    # Create test component
    test_component = ParsedComponent(
        name="test_component",
        type="Store", 
        description="Test component",
        processing_mode="batch",
        inputs=[ParsedPort(name="input", schema="ItemSchema", required=True, description="Input")],
        outputs=[ParsedPort(name="output", schema="ItemSchema", required=True, description="Output")],
        properties=[],
        contracts=[],
        resources=[],
        config={"storage_type": "file"},
        dependencies=[],
        implementation={},
        observability={}
    )
    
    # Create minimal system blueprint
    system_blueprint = ParsedSystemBlueprint(
        system=ParsedSystem(
            name="test_system",
            description="Test",
            version="1.0.0",
            components=[test_component],
            bindings=[],
            configuration={},
            deployment={},
            validation={}
        ),
        metadata={},
        schemas={},
        policy={},
        source_file=None,
        raw_blueprint={}
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Temp directory: {temp_dir}")
        
        # Initialize component generator
        generator = ComponentLogicGenerator(Path(temp_dir) / "scaffolds")
        
        try:
            # Generate the component
            print("📝 Generating component...")
            generated_component = await generator._generate_store_component(test_component, system_blueprint)
            
            print("✅ Component generated successfully")
            print(f"📊 Component info:")
            print(f"   • Name: {generated_component.name}")
            print(f"   • Type: {generated_component.type}")
            print(f"   • Implementation length: {len(generated_component.implementation)} chars")
            print(f"   • Dependencies: {generated_component.dependencies}")
            print(f"   • Imports: {generated_component.imports}")
            
            print("\\n" + "="*60)
            print("📄 RAW LLM IMPLEMENTATION:")
            print("="*60)
            lines = generated_component.implementation.split('\\n')
            for i, line in enumerate(lines[:30], 1):
                print(f"{i:3d}: {line}")
            if len(lines) > 30:
                print(f"... ({len(lines) - 30} more lines)")
            
            # Now write the component to see final file
            print("\\n" + "="*60)
            print("📝 WRITING COMPONENT FILE:")
            print("="*60)
            
            generator._write_component_file("test_system", generated_component)
            
            # Read the final written file
            written_file = Path(temp_dir) / "scaffolds" / "test_system" / "components" / f"{generated_component.name}.py"
            if written_file.exists():
                content = written_file.read_text()
                print(f"📄 Final written file ({len(content.split(chr(10)))} lines):")
                final_lines = content.split('\\n')
                for i, line in enumerate(final_lines[:40], 1):
                    print(f"{i:3d}: {line}")
            else:
                print("❌ Written file not found")
                
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_component())