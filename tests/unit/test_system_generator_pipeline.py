#!/usr/bin/env python3
"""
Test that the system generation pipeline works end-to-end.
These tests use real LLM and verify the pipeline executes without errors.
"""

import pytest
import tempfile
import os
from pathlib import Path

from autocoder_cc.blueprint_language import SystemGenerator


class TestSystemGeneratorPipeline:
    """Test the generation pipeline works with real LLM."""
    
    def setup_method(self):
        """Setup test instances."""
        self.temp_dir = tempfile.mkdtemp()
        # Disable strict validation for these tests
        os.environ['AUTOCODER_VALIDATION_MODE'] = 'lenient'
        self.generator = SystemGenerator(output_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        # Reset validation mode
        os.environ.pop('AUTOCODER_VALIDATION_MODE', None)
    
    @pytest.mark.asyncio
    async def test_minimal_system_generation(self):
        """Test that a minimal system generates without errors."""
        
        # Minimal valid blueprint
        blueprint_yaml = '''
system:
  name: minimal_test
  description: Minimal test system
  components:
    - name: SimpleAPI
      type: APIEndpoint
      description: Simple API endpoint
      config:
        port: 8080
        host: localhost
      outputs:
        - name: data_out
          schema: Any
    - name: SimpleStore  
      type: Store
      description: Simple store
      config:
        storage_type: memory
      inputs:
        - name: data_in
          schema: Any
  bindings:
    - from: SimpleAPI.data_out
      to: SimpleStore.data_in
      type: data_flow
metadata:
  version: "1.0.0"
'''
        
        # Should complete without exceptions
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        # Basic assertions - pipeline completed
        assert result is not None
        assert result.name == "minimal_test"
        assert len(result.components) == 2
        
        # Check files were created
        scaffold_dir = Path(self.temp_dir) / "scaffolds" / "minimal_test"
        assert scaffold_dir.exists()
        assert (scaffold_dir / "main.py").exists()
        assert (scaffold_dir / "components").exists()
    
    @pytest.mark.asyncio
    async def test_generation_creates_expected_structure(self):
        """Test that generation creates the expected file structure."""
        
        blueprint_yaml = '''
system:
  name: structure_test
  description: Test file structure
  components:
    - name: TestEndpoint
      type: APIEndpoint
      config:
        port: 9090
      outputs:
        - name: output
          schema: Any
metadata:
  version: "1.0.0"
'''
        
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        # Check directory structure
        base_dir = Path(self.temp_dir) / "scaffolds" / "structure_test"
        
        expected_files = [
            "main.py",
            "requirements.txt", 
            "Dockerfile",
            "components/__init__.py",
            "components/observability.py",
            "components/communication.py",
            "config/system_config.yaml"
        ]
        
        for file_path in expected_files:
            full_path = base_dir / file_path
            assert full_path.exists(), f"Expected file not found: {file_path}"
    
    @pytest.mark.asyncio
    async def test_generator_handles_complex_blueprint(self):
        """Test generator handles a more complex blueprint."""
        
        blueprint_yaml = '''
system:
  name: complex_test
  description: Complex test system
  components:
    - name: DataIngestion
      type: APIEndpoint
      description: Data ingestion endpoint
      config:
        port: 8080
        host: 0.0.0.0
      outputs:
        - name: raw_data
          schema: Any
    - name: DataProcessor
      type: Transformer
      description: Process incoming data
      inputs:
        - name: input_data
          schema: Any
      outputs:
        - name: processed_data
          schema: Any
    - name: DataStorage
      type: Store
      description: Store processed data
      config:
        storage_type: memory
        max_items: 5000
      inputs:
        - name: data
          schema: Any
  bindings:
    - from: DataIngestion.raw_data
      to: DataProcessor.input_data
    - from: DataProcessor.processed_data
      to: DataStorage.data
metadata:
  version: "1.0.0"
  description: Test complex system generation
'''
        
        result = await self.generator.generate_system_from_yaml(blueprint_yaml)
        
        assert result.name == "complex_test"
        assert len(result.components) == 3
        
        # Verify component types
        component_types = {c.component_type for c in result.components}
        assert component_types == {"APIEndpoint", "Transformer", "Store"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])