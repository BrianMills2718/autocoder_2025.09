#!/usr/bin/env python3
"""
Test that architectural validation now supports API patterns without requiring Source/Sink components.
"""

import sys
sys.path.insert(0, '/home/brian/projects/autocoder4_cc')

from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser, ParsedSystemBlueprint, ParsedComponent, ParsedBinding

def create_todo_app_blueprint():
    """Create a simple todo app blueprint with API pattern."""
    # Create the blueprint YAML
    blueprint_yaml = """
name: "TodoApp"  
description: "A simple todo list application"
version: "1.0.0"

system:
  name: "todo_system"
  description: "Todo list management system"
  
  components:
    - name: "todo_api"
      type: "APIEndpoint"
      description: "REST API for todo operations"
      config:
        port: 8080
        endpoints:
          - path: "/todos"
            method: "GET"
            description: "Get all todos"
          - path: "/todos"
            method: "POST"
            description: "Create a new todo"
      outputs:
        - name: "request"
          schema: '{"type": "object"}'
      inputs:
        - name: "response"
          schema: '{"type": "object"}'
        - name: "data"
          schema: '{"type": "object"}'
        - name: "control"
          schema: '{"type": "object"}'
    
    - name: "todo_controller"
      type: "Controller"
      description: "Business logic for todo operations"
      inputs:
        - name: "request"
          schema: '{"type": "object"}'
      outputs:
        - name: "command"
          schema: '{"type": "object"}'
    
    - name: "todo_store"
      type: "Store"
      description: "Storage for todo items"
      config:
        storage_type: "memory"
      inputs:
        - name: "command"
          schema: '{"type": "object"}'
        - name: "query"
          schema: '{"type": "object"}'
        - name: "control"
          schema: '{"type": "object"}'
      outputs:
        - name: "result"
          schema: '{"type": "object"}'
        - name: "response"
          schema: '{"type": "object"}'
  
  bindings:
    - from_component: "todo_api"
      from_port: "request"
      to_components: ["todo_controller"]
      to_ports: ["request"]
      description: "API forwards requests to controller"
    
    - from_component: "todo_controller"
      from_port: "command"
      to_components: ["todo_store"]
      to_ports: ["command"]
      description: "Controller sends commands to store"
    
    - from_component: "todo_store"
      from_port: "result"
      to_components: ["todo_api"]
      to_ports: ["response"]
      description: "Store sends results back to API"
"""
    return blueprint_yaml

def test_api_pattern_validation():
    """Test that API patterns are now valid without Source/Sink components."""
    print("Testing API Pattern Validation Fix...")
    
    # Parse the blueprint
    parser = SystemBlueprintParser()
    blueprint_yaml = create_todo_app_blueprint()
    
    try:
        parsed_blueprint = parser.parse_string(blueprint_yaml)
        print("✅ Blueprint parsed successfully")
        
        # Validate the architecture
        validator = ArchitecturalValidator()
        validation_errors = validator.validate_system_architecture(parsed_blueprint)
        
        # Check for the specific errors we're trying to fix
        error_types = [error.error_type for error in validation_errors if error.severity == "error"]
        
        if "missing_sources" in error_types:
            print("❌ FAILED: Still getting 'missing_sources' error")
            print("This means the API pattern detection is not working")
            return False
            
        if "missing_sinks" in error_types:
            print("❌ FAILED: Still getting 'missing_sinks' error")
            print("This means the API pattern detection is not working")
            return False
        
        # Check if we have any critical errors
        critical_errors = [e for e in validation_errors if e.severity == "error"]
        if critical_errors:
            print(f"❌ FAILED: Got {len(critical_errors)} critical errors:")
            for error in critical_errors:
                print(f"  - {error.error_type}: {error.message}")
            return False
        
        print("✅ SUCCESS: API pattern validated without Source/Sink requirement!")
        
        # Show any warnings for completeness
        warnings = [e for e in validation_errors if e.severity == "warning"]
        if warnings:
            print(f"\nℹ️  Got {len(warnings)} warnings (non-critical):")
            for warning in warnings:
                print(f"  - {warning.error_type}: {warning.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_traditional_pattern_still_validated():
    """Ensure traditional Source->Sink patterns still require sources and sinks."""
    print("\nTesting Traditional Pattern Still Requires Sources/Sinks...")
    
    # Create a blueprint with Transformer but no Source/Sink
    blueprint_yaml = """
name: "DataProcessor"
description: "A data processing system"
version: "1.0.0"

system:
  name: "processor_system"
  description: "Data processing system"
  
  components:
    - name: "data_transformer"
      type: "Transformer"
      description: "Transform data"
      inputs:
        - name: "input"
          schema: '{"type": "object"}'
      outputs:
        - name: "output"
          schema: '{"type": "object"}'
  
  bindings: []
"""
    
    parser = SystemBlueprintParser()
    
    try:
        parsed_blueprint = parser.parse_string(blueprint_yaml)
        validator = ArchitecturalValidator()
        validation_errors = validator.validate_system_architecture(parsed_blueprint)
        
        error_types = [error.error_type for error in validation_errors if error.severity == "error"]
        
        if "missing_sources" in error_types and "missing_sinks" in error_types:
            print("✅ SUCCESS: Traditional patterns still require Source/Sink components")
            return True
        else:
            print("❌ FAILED: Traditional pattern validation is broken")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Exception during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Pattern Validation Fix Test")
    print("=" * 60)
    
    # Test 1: API patterns should be valid
    test1_passed = test_api_pattern_validation()
    
    # Test 2: Traditional patterns should still be validated
    test2_passed = test_traditional_pattern_still_validated()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  API Pattern Support: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Traditional Pattern Validation: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED - Architectural validation fix is working!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Fix needs more work")
        sys.exit(1)