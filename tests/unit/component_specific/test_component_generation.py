import asyncio
import tempfile
from pathlib import Path
import pytest
from autocoder_cc.blueprint_language.system_generator import SystemGenerator

@pytest.mark.asyncio
async def test_generation():
    # Create simple test blueprint
    blueprint_yaml = '''
schema_version: "1.0.0"
metadata:
  version: 1.0.0
  author: Test
  description: Simple test system
  autocoder_version: 3.3.0
  natural_language_description: Create a simple test API

system:
  name: test_system
  description: Simple test system
  version: 1.0.0
  
  components:
    - name: test_api
      type: APIEndpoint
      ports:
        response:
          semantic_class: data_out
          direction: output
          data_schema:
            id: schemas.api.APIResponse
            version: 1
          description: HTTP response data
      inputs: []
      outputs: []
      processing_mode: stream
      resources:
        ports:
          - port: 8080
            protocol: HTTP
            public: true
      observability:
        level: detailed
      description: Simple test API endpoint
      
  bindings: []
'''
    
    # Test generation
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = SystemGenerator(output_dir)
        
        # Save blueprint to file
        blueprint_file = output_dir / "test.yaml"
        with open(blueprint_file, 'w') as f:
            f.write(blueprint_yaml)
        
        # Test generation
        try:
            system = await generator.generate_system_with_timeout(blueprint_file)
            print(f"✅ System generated: {system.name}")
            print(f"✅ Components: {len(system.components)}")
            return True
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_generation())
    print(f"Test result: {'✅ SUCCESS' if success else '❌ FAILED'}")