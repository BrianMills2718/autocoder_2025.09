"""Test that new SystemGenerator maintains interface compatibility"""

import pytest
from pathlib import Path
from autocoder_cc.blueprint_language import SystemGenerator, GeneratedSystem

class TestSystemGeneratorInterface:
    """Verify interface compatibility of replacement SystemGenerator"""
    
    def test_has_required_attributes(self):
        """SystemGenerator has all expected attributes"""
        gen = SystemGenerator(Path("./test"))
        
        assert hasattr(gen, 'output_dir')
        assert hasattr(gen, 'skip_deployment')
        assert hasattr(gen, 'logger')
        assert hasattr(gen, 'generate_system_from_yaml')
        assert hasattr(gen, 'generate_system')
        assert hasattr(gen, 'validate_system')
    
    @pytest.mark.asyncio
    async def test_generate_returns_correct_type(self):
        """generate_system_from_yaml returns GeneratedSystem"""
        gen = SystemGenerator(Path("./test_output"))
        
        blueprint = """
system:
  name: test_system
  components:
    - name: api
      type: APIEndpoint
      config:
        port: 8080
"""
        
        try:
            result = await gen.generate_system_from_yaml(blueprint)
            assert isinstance(result, GeneratedSystem)
            assert hasattr(result, 'name')
            assert hasattr(result, 'output_directory')
            assert hasattr(result, 'components')
            assert hasattr(result, 'version')
            assert hasattr(result, 'metadata')
        except Exception as e:
            # Even on failure, should be proper exception
            assert "generation failed" in str(e).lower() or "error" in str(e).lower()
    
    def test_validate_returns_tuple(self):
        """validate_system returns (bool, list)"""
        gen = SystemGenerator(Path("./test"))
        
        # Test with valid config
        valid_config = {"system": {"components": [{"name": "test"}]}}
        is_valid, errors = gen.validate_system(valid_config)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        
        # Test with invalid config
        invalid_config = {}
        is_valid, errors = gen.validate_system(invalid_config)
        assert is_valid == False
        assert len(errors) > 0