#!/usr/bin/env python3
"""
Test Script for Architectural Validation

This script tests the architectural validation functionality with various
blueprint configurations to ensure it catches architectural issues.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator

def test_valid_blueprint():
    """Test with a valid blueprint that should pass architectural validation."""
    
    print("=== Testing Valid Blueprint ===")
    
    valid_blueprint = """
system:
  name: "simple_todo_system"
  description: "A simple todo application"
  version: "1.0.0"
  components:
    - name: "todo_api"
      type: "APIEndpoint"
      description: "REST API for todo operations"
      inputs:
        - name: "request"
          schema: "http_request"
          required: true
      outputs:
        - name: "response"
          schema: "http_response"
          required: true
    - name: "todo_controller"
      type: "Controller"
      description: "Business logic for todo operations"
      inputs:
        - name: "api_request"
          schema: "http_request"
          required: true
      outputs:
        - name: "data_command"
          schema: "todo_data"
          required: true
    - name: "todo_store"
      type: "Store"
      description: "Database for todo items"
      inputs:
        - name: "data"
          schema: "todo_data"
          required: true
  bindings:
    - from: "todo_api.response"
      to: "todo_controller.api_request"
    - from: "todo_controller.data_command"
      to: "todo_store.data"
policy:
  version: "1.0.0"
schemas:
  http_request:
    type: "object"
  http_response:
    type: "object"
  todo_data:
    type: "object"
"""
    
    try:
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_string(valid_blueprint)
        print("✅ Valid blueprint parsed successfully")
        print(f"   System: {system_blueprint.system.name}")
        print(f"   Components: {len(system_blueprint.system.components)}")
        print(f"   Bindings: {len(system_blueprint.system.bindings)}")
        
        # Test architectural validation directly
        validator = ArchitecturalValidator()
        arch_errors = validator.validate_system_architecture(system_blueprint)
        
        print(f"   Architectural errors: {len(arch_errors)}")
        for error in arch_errors:
            print(f"     - {error.severity}: {error.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Valid blueprint failed: {e}")
        return False

def test_invalid_blueprint():
    """Test with an invalid blueprint that should fail architectural validation."""
    
    print("\n=== Testing Invalid Blueprint ===")
    
    invalid_blueprint = """
system:
  name: "invalid_system"
  description: "A system with architectural issues"
  version: "1.0.0"
  components:
    - name: "orphaned_component"
      type: "Transformer"
      description: "A component with no connections"
      inputs:
        - name: "input"
          schema: "data"
          required: true
      outputs:
        - name: "output"
          schema: "data"
          required: true
    - name: "store_to_source"
      type: "Store"
      description: "Store that incorrectly connects to source"
      inputs:
        - name: "data"
          schema: "data"
          required: true
      outputs:
        - name: "bad_output"
          schema: "data"
          required: true
    - name: "bad_source"
      type: "Source"
      description: "Source that receives from store"
      outputs:
        - name: "data"
          schema: "data"
          required: true
  bindings:
    - from: "store_to_source.bad_output"
      to: "bad_source.input"
policy:
  version: "1.0.0"
schemas:
  data:
    type: "object"
"""
    
    try:
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_string(invalid_blueprint)
        print("✅ Invalid blueprint parsed successfully")
        
        # Test architectural validation directly
        validator = ArchitecturalValidator()
        arch_errors = validator.validate_system_architecture(system_blueprint)
        
        print(f"   Architectural errors: {len(arch_errors)}")
        for error in arch_errors:
            print(f"     - {error.severity}: {error.message}")
            if error.suggestion:
                print(f"       Suggestion: {error.suggestion}")
        
        # This should have architectural errors
        if len(arch_errors) > 0:
            print("✅ Architectural validation correctly identified issues")
            return True
        else:
            print("❌ Architectural validation failed to identify issues")
            return False
        
    except Exception as e:
        print(f"❌ Invalid blueprint test failed: {e}")
        return False

def test_missing_components():
    """Test with a blueprint missing essential components."""
    
    print("\n=== Testing Missing Components ===")
    
    missing_components_blueprint = """
system:
  name: "incomplete_system"
  description: "A system missing essential components"
  version: "1.0.0"
  components:
    - name: "lonely_transformer"
      type: "Transformer"
      description: "A transformer with no sources or sinks"
      inputs:
        - name: "input"
          schema: "data"
          required: true
      outputs:
        - name: "output"
          schema: "data"
          required: true
  bindings: []
policy:
  version: "1.0.0"
schemas:
  data:
    type: "object"
"""
    
    try:
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_string(missing_components_blueprint)
        print("✅ Missing components blueprint parsed successfully")
        
        # Test architectural validation directly
        validator = ArchitecturalValidator()
        arch_errors = validator.validate_system_architecture(system_blueprint)
        
        print(f"   Architectural errors: {len(arch_errors)}")
        for error in arch_errors:
            print(f"     - {error.severity}: {error.message}")
            if error.suggestion:
                print(f"       Suggestion: {error.suggestion}")
        
        # This should have architectural errors
        if len(arch_errors) > 0:
            print("✅ Architectural validation correctly identified missing components")
            return True
        else:
            print("❌ Architectural validation failed to identify missing components")
            return False
        
    except Exception as e:
        print(f"❌ Missing components test failed: {e}")
        return False

def main():
    """Run all architectural validation tests."""
    
    print("🧪 ARCHITECTURAL VALIDATION TESTS")
    print("=" * 50)
    
    results = []
    
    # Test valid blueprint
    results.append(test_valid_blueprint())
    
    # Test invalid blueprint
    results.append(test_invalid_blueprint())
    
    # Test missing components
    results.append(test_missing_components())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("✅ All architectural validation tests passed!")
        return 0
    else:
        print("❌ Some architectural validation tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())