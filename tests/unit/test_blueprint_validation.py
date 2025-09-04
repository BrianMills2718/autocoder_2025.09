#!/usr/bin/env python3
"""
Unit tests for blueprint validation to understand requirements
"""
import pytest
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser

class TestBlueprintValidation:
    """Test blueprint parsing and validation"""
    
    def test_parser_parse_string_exists(self):
        """Verify parser has parse_string method"""
        parser = SystemBlueprintParser()
        assert hasattr(parser, 'parse_string'), "Parser missing parse_string method"
    
    def test_minimal_blueprint(self):
        """Test minimal blueprint with API and Store"""
        minimal = """
system:
  name: test
  description: test
  components:
    - name: api
      type: APIEndpoint
      description: API endpoint
    - name: store
      type: Store
      description: Data store
  bindings: []
        """
        parser = SystemBlueprintParser()
        try:
            result = parser.parse_string(minimal)
            print(f"Minimal blueprint parsed: {result}")
        except Exception as e:
            pytest.fail(f"Minimal blueprint failed: {e}")
    
    def test_blueprint_with_components(self):
        """Test blueprint with source and sink components"""
        with_components = """
system:
  name: test
  description: test
  components:
    - name: api
      type: APIEndpoint
      description: API endpoint
    - name: store
      type: Store
      description: Data store
  bindings: []
        """
        parser = SystemBlueprintParser()
        try:
            result = parser.parse_string(with_components)
            print(f"Blueprint with components parsed: {result}")
        except Exception as e:
            pytest.fail(f"Blueprint with components failed: {e}")
    
    def test_complete_blueprint(self):
        """Test with all fields from working example"""
        complete = """
metadata:
  version: 1.0.0
  
system:
  name: test_system
  description: Test system
  version: 1.0.0
  components:
    - name: api
      type: APIEndpoint
      description: API endpoint
    - name: store
      type: Store
      description: Store for data
  bindings: []
        """
        parser = SystemBlueprintParser()
        try:
            result = parser.parse_string(complete)
            print(f"Complete blueprint parsed: {result}")
            print(f"System name: {result.system.name}")
            print(f"Component count: {len(result.system.components)}")
        except Exception as e:
            pytest.fail(f"Complete blueprint failed: {e}")