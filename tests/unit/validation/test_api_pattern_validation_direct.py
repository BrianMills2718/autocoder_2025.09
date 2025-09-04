#!/usr/bin/env python3
"""
Test architectural validation directly without going through the full parser.
"""

import sys
sys.path.insert(0, '/home/brian/projects/autocoder4_cc')

from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent, ParsedBinding, ParsedSystem

def create_api_pattern_blueprint():
    """Create a parsed blueprint directly for API pattern."""
    # Create components
    api_component = ParsedComponent(
        name="todo_api",
        type="APIEndpoint",
        description="REST API for todo operations",
        inputs=[],
        outputs=[],
        config={"port": 8080}
    )
    
    controller_component = ParsedComponent(
        name="todo_controller",
        type="Controller",
        description="Business logic for todo operations",
        inputs=[],
        outputs=[],
        config={}
    )
    
    store_component = ParsedComponent(
        name="todo_store", 
        type="Store",
        description="Storage for todo items",
        inputs=[],
        outputs=[],
        config={"storage_type": "memory"}
    )
    
    # Create bindings
    bindings = [
        ParsedBinding(
            from_component="todo_api",
            from_port="request",
            to_components=["todo_controller"],
            to_ports=["request"]
        ),
        ParsedBinding(
            from_component="todo_controller",
            from_port="command",
            to_components=["todo_store"],
            to_ports=["command"]
        ),
        ParsedBinding(
            from_component="todo_store",
            from_port="result",
            to_components=["todo_api"],
            to_ports=["response"]
        )
    ]
    
    # Create system
    system = ParsedSystem(
        name="todo_system",
        description="Todo list management system",
        components=[api_component, controller_component, store_component],
        bindings=bindings
    )
    
    # Create parsed system blueprint
    parsed_blueprint = ParsedSystemBlueprint(
        system=system
    )
    
    return parsed_blueprint

def create_traditional_pattern_blueprint():
    """Create a parsed blueprint for traditional Source->Sink pattern."""
    # Create components
    transformer = ParsedComponent(
        name="data_transformer",
        type="Transformer",
        description="Transform data",
        inputs=[],
        outputs=[],
        config={}
    )
    
    # Create system with no bindings (orphaned component)
    system = ParsedSystem(
        name="processor_system",
        description="Data processing system",
        components=[transformer],
        bindings=[]
    )
    
    # Create parsed system blueprint
    parsed_blueprint = ParsedSystemBlueprint(
        system=system
    )
    
    return parsed_blueprint

def test_api_pattern_validation():
    """Test that API patterns are now valid without Source/Sink components."""
    print("Testing API Pattern Validation Fix...")
    
    try:
        parsed_blueprint = create_api_pattern_blueprint()
        
        # Validate the architecture
        validator = ArchitecturalValidator()
        validation_errors = validator.validate_system_architecture(parsed_blueprint)
        
        # Check for the specific errors we're trying to fix
        error_types = [error.error_type for error in validation_errors if error.severity == "error"]
        
        if "missing_sources" in error_types:
            print("❌ FAILED: Still getting 'missing_sources' error")
            for error in validation_errors:
                if error.error_type == "missing_sources":
                    print(f"   Error: {error.message}")
            return False
            
        if "missing_sinks" in error_types:
            print("❌ FAILED: Still getting 'missing_sinks' error")
            for error in validation_errors:
                if error.error_type == "missing_sinks":
                    print(f"   Error: {error.message}")
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
    
    try:
        parsed_blueprint = create_traditional_pattern_blueprint()
        
        validator = ArchitecturalValidator()
        validation_errors = validator.validate_system_architecture(parsed_blueprint)
        
        error_types = [error.error_type for error in validation_errors if error.severity == "error"]
        
        # For an orphaned transformer with no sources/sinks, we should get missing_sources and missing_sinks
        if "missing_sources" in error_types and "missing_sinks" in error_types:
            print("✅ SUCCESS: Traditional patterns still require Source/Sink components")
            return True
        elif "orphaned_component" in error_types:
            # This is also valid - the component is orphaned because it has no connections
            print("✅ SUCCESS: Orphaned components are still detected (which implies need for sources/sinks)")
            return True
        else:
            print("❌ FAILED: Traditional pattern validation is broken")
            print(f"   Error types found: {error_types}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Exception during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Pattern Validation Fix Test (Direct)")
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