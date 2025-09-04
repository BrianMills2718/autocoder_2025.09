"""Simple test for system generator without external dependencies."""
import pytest
import tempfile
import os
from autocoder_cc.blueprint_language import SystemGenerator


class TestSystemGeneratorSimple:
    """Test system generation without external API calls."""
    
    def setup_method(self):
        """Setup test instances."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_simple_generation_no_external_apis(self):
        """Test that basic generation works without external API calls."""
        
        # No need to mock benchmark collector anymore - we removed that feature!
        
        # Create generator with bypass validation and skip deployment
        generator = SystemGenerator(
            output_dir=self.temp_dir,
            bypass_validation=True,
            skip_deployment=True
        )
        
        # Simple blueprint with minimal components
        blueprint_yaml = """
system:
  name: simple_test_system
  description: Simple test system
  components:
    - name: TestAPI
      type: APIEndpoint
      description: Test API endpoint
      config:
        host: localhost
        port: 8080
      outputs:
        - name: api_out
          schema: Any
    - name: TestStore
      type: Store
      description: Test data store
      config:
        storage_type: memory
      inputs:
        - name: store_in
          schema: Any
  bindings:
    - from: TestAPI.api_out
      to: TestStore.store_in
metadata:
  version: "1.0.0"
"""
        
        # Generate system
        result = await generator.generate_system_from_yaml(blueprint_yaml)
        
        # Basic assertions
        assert result is not None, "System generation should succeed"
        assert len(result.components) == 2, "Should generate 2 components"
        
        # Check component names
        component_names = {c.name for c in result.components}
        assert "TestAPI" in component_names or "testapi" in component_names.union({c.name.lower() for c in result.components}), \
            "Should have TestAPI component"
        assert "TestStore" in component_names or "teststore" in component_names.union({c.name.lower() for c in result.components}), \
            "Should have TestStore component"
        
        # Check scaffold was generated
        assert result.scaffold is not None, "Should generate scaffold"
        assert result.scaffold.main_py is not None, "Should generate main.py"
        
        # Success - no external APIs were needed!
        print("✅ Simple generation test passed without external API calls")