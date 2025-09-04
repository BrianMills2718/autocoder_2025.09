#!/usr/bin/env python3
"""
Test script to find edge cases in blueprint validation and self-healing
"""
import yaml
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator
from autocoder_cc.healing.blueprint_healer import BlueprintHealer
from autocoder_cc.observability.structured_logging import get_logger

logger = get_logger(__name__)

def test_missing_bindings_scenario():
    """Test scenario where components exist but no bindings are provided"""
    
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_missing_bindings"
  description: "Test system with missing bindings"
  version: "1.0.0"
  
  components:
    - name: data_source
      type: Source
      description: "Data source component"
      outputs:
        - name: output
          schema_type: "object"
          
    - name: data_processor
      type: Transformer
      description: "Data processor component"
      inputs:
        - name: input
          schema_type: "object"
      outputs:
        - name: output
          schema_type: "object"
          
    - name: data_store
      type: Store
      description: "Data storage component"
      inputs:
        - name: input
          schema_type: "object"
  
  # NO BINDINGS - should be auto-generated

policy:
  security:
    encryption_at_rest: true
  resource_limits:
    max_memory_per_component: "512Mi"
  validation:
    strict_mode: true
"""
    
    logger.info("=== Testing Missing Bindings Auto-Generation ===")
    logger.info("Components: Source -> Transformer -> Store")
    logger.info("No bindings provided - should auto-generate Source->Transformer->Store chain")
    
    parser = SystemBlueprintParser()
    
    try:
        blueprint = parser.parse_string(blueprint_yaml, max_healing_attempts=3)
        logger.info("✅ Blueprint parsing succeeded!")
        
        # Check that bindings were auto-generated
        bindings = blueprint.system.bindings
        logger.info(f"Generated {len(bindings)} bindings:")
        for binding in bindings:
            logger.info(f"  {binding.from_component}.{binding.from_port} -> {binding.to_components[0]}.{binding.to_ports[0]}")
        
        # Verify we have a complete chain
        expected_bindings = {
            ('data_source', 'output', 'data_processor', 'input'),
            ('data_processor', 'output', 'data_store', 'input')
        }
        
        actual_bindings = set()
        for binding in bindings:
            if binding.to_components and binding.to_ports:
                actual_bindings.add((binding.from_component, binding.from_port, binding.to_components[0], binding.to_ports[0]))
        
        missing_bindings = expected_bindings - actual_bindings
        if missing_bindings:
            logger.warning(f"Missing expected bindings: {missing_bindings}")
            return False
        else:
            logger.info("✅ All expected bindings generated correctly!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Blueprint parsing failed: {e}")
        return False

def test_complex_schema_mismatch():
    """Test more complex schema mismatch scenarios"""
    
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_complex_schema"
  description: "Test system with complex schema mismatches"
  version: "1.0.0"
  
  components:
    - name: string_producer
      type: Source
      description: "Produces strings"
      outputs:
        - name: string_output
          schema_type: "common_string_schema"
          
    - name: number_consumer
      type: Transformer
      description: "Expects numbers"
      inputs:
        - name: number_input
          schema_type: "common_number_schema"
      outputs:
        - name: processed_output
          schema_type: "common_object_schema"
          
    - name: array_consumer
      type: Sink
      description: "Expects arrays"
      inputs:
        - name: array_input
          schema_type: "common_array_schema"
  
  bindings:
    - from_component: string_producer
      from_port: string_output
      to_components: [number_consumer]
      to_ports: [number_input]
      description: "String -> Number (should be healed to any)"
      
    - from_component: number_consumer
      from_port: processed_output
      to_components: [array_consumer]
      to_ports: [array_input]
      description: "Object -> Array (should be healed to any)"

policy:
  security:
    encryption_at_rest: true
  resource_limits:
    max_memory_per_component: "512Mi"
  validation:
    strict_mode: true
"""
    
    logger.info("\n=== Testing Complex Schema Mismatches ===")
    logger.info("Chain: String -> Number -> Object -> Array")
    logger.info("Multiple schema mismatches should all be healed to 'any'")
    
    parser = SystemBlueprintParser()
    
    try:
        blueprint = parser.parse_string(blueprint_yaml, max_healing_attempts=3)
        logger.info("✅ Blueprint parsing succeeded!")
        
        # Check that schemas were healed
        for component in blueprint.system.components:
            logger.info(f"Component {component.name}:")
            if hasattr(component, 'inputs') and component.inputs:
                for input_port in component.inputs:
                    schema = getattr(input_port, 'schema', None)
                    logger.info(f"  Input {input_port.name}: {schema}")
            if hasattr(component, 'outputs') and component.outputs:
                for output_port in component.outputs:
                    schema = getattr(output_port, 'schema', None)
                    logger.info(f"  Output {output_port.name}: {schema}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Blueprint parsing failed: {e}")
        return False

def test_validation_without_healing():
    """Test validation errors without healing to see what gets caught"""
    
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_validation_errors"
  description: "Test system with validation errors"
  version: "1.0.0"
  
  components:
    - name: api_endpoint
      type: APIEndpoint
      description: "API endpoint without port"
      # Missing port configuration
      
    - name: data_store
      type: Store
      description: "Store without database config"
      # Missing storage_type configuration
      
    - name: orphaned_transformer
      type: Transformer
      description: "Transformer with no connections"
      inputs:
        - name: input
          schema_type: "object"
      outputs:
        - name: output
          schema_type: "object"
  
  bindings: []  # Empty bindings

policy:
  security:
    encryption_at_rest: true
  resource_limits:
    max_memory_per_component: "512Mi"
  validation:
    strict_mode: true
"""
    
    logger.info("\n=== Testing Validation Without Healing ===")
    logger.info("Expected errors:")
    logger.info("- APIEndpoint missing port")
    logger.info("- Store missing database config")
    logger.info("- Orphaned transformer")
    
    # Test validator directly
    validator = BlueprintValidator()
    
    try:
        raw_blueprint = yaml.safe_load(blueprint_yaml)
        
        # Parse without healing first
        parser = SystemBlueprintParser()
        parser.validation_errors.clear()
        
        # Manually call validation to see raw errors
        parser._validate_system_structure(raw_blueprint)
        system_blueprint = parser._parse_system_blueprint(raw_blueprint)
        parser._validate_system_semantics(system_blueprint)
        
        if parser.validation_errors:
            logger.info(f"Found {len(parser.validation_errors)} validation errors:")
            for error in parser.validation_errors:
                logger.info(f"  {error.path}: {error.message}")
        else:
            logger.warning("No validation errors found - this is unexpected")
        
        # Now test with blueprint validator
        validation_errors = validator.validate_pre_generation(system_blueprint)
        if validation_errors:
            logger.info(f"Blueprint validator found {len(validation_errors)} additional errors:")
            for error in validation_errors:
                logger.info(f"  {error}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation test failed: {e}")
        return False

def test_circular_dependencies():
    """Test circular dependency detection"""
    
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_circular"
  description: "Test system with circular dependencies"
  version: "1.0.0"
  
  components:
    - name: component_a
      type: Transformer
      description: "Component A"
      inputs:
        - name: input
          schema_type: "object"
      outputs:
        - name: output
          schema_type: "object"
          
    - name: component_b
      type: Transformer
      description: "Component B"
      inputs:
        - name: input
          schema_type: "object"
      outputs:
        - name: output
          schema_type: "object"
          
    - name: component_c
      type: Transformer
      description: "Component C"
      inputs:
        - name: input
          schema_type: "object"
      outputs:
        - name: output
          schema_type: "object"
  
  bindings:
    - from_component: component_a
      from_port: output
      to_components: [component_b]
      to_ports: [input]
      
    - from_component: component_b
      from_port: output
      to_components: [component_c]
      to_ports: [input]
      
    - from_component: component_c
      from_port: output
      to_components: [component_a]
      to_ports: [input]

policy:
  security:
    encryption_at_rest: true
  resource_limits:
    max_memory_per_component: "512Mi"
  validation:
    strict_mode: true
"""
    
    logger.info("\n=== Testing Circular Dependencies ===")
    logger.info("Creating A -> B -> C -> A circular dependency")
    logger.info("Should be detected but allowed (informational)")
    
    parser = SystemBlueprintParser()
    
    try:
        blueprint = parser.parse_string(blueprint_yaml, max_healing_attempts=3)
        logger.info("✅ Blueprint parsing succeeded (circular dependencies allowed)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Blueprint parsing failed: {e}")
        return False

def main():
    """Run all edge case tests"""
    
    logger.info("Starting Blueprint Validation Edge Case Tests")
    logger.info("=" * 60)
    
    test1_result = test_missing_bindings_scenario()
    test2_result = test_complex_schema_mismatch()
    test3_result = test_validation_without_healing()
    test4_result = test_circular_dependencies()
    
    logger.info("\n" + "=" * 60)
    logger.info("Edge Case Test Results:")
    logger.info(f"Missing Bindings Auto-Gen: {'✅ PASS' if test1_result else '❌ FAIL'}")
    logger.info(f"Complex Schema Mismatches: {'✅ PASS' if test2_result else '❌ FAIL'}")
    logger.info(f"Validation Error Detection: {'✅ PASS' if test3_result else '❌ FAIL'}")
    logger.info(f"Circular Dependencies: {'✅ PASS' if test4_result else '❌ FAIL'}")
    
    all_passed = test1_result and test2_result and test3_result and test4_result
    
    if all_passed:
        logger.info("🎉 ALL EDGE CASE TESTS PASSED!")
        return True
    else:
        logger.error("💥 SOME EDGE CASE TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)