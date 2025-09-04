#!/usr/bin/env python3
"""
Test script to verify schema healing and self-healing loop functionality
"""
import yaml
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.observability.structured_logging import get_logger

logger = get_logger(__name__)

def test_schema_healing():
    """Test that schema mismatches trigger healing and get resolved"""
    
    # Create a blueprint with intentional schema mismatch
    # Controller outputs "object" but Store expects "integer"
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_schema_healing"
  description: "Test system for schema healing"
  version: "1.0.0"
  
  components:
    - name: task_controller
      type: Controller
      description: "Task controller component"
      outputs:
        - name: task_data
          schema_type: "object"  # This will cause mismatch
          
    - name: task_store
      type: Store
      description: "Task storage component"
      inputs:
        - name: data
          schema_type: "integer"  # This expects integer, not object
  
  bindings:
    - from_component: task_controller
      from_port: task_data
      to_components: [task_store]
      to_ports: [data]
      description: "Controller to Store data flow"

policy:
  security:
    encryption_at_rest: true
    encryption_in_transit: true
    authentication_required: true
  resource_limits:
    max_memory_per_component: "512Mi"
    max_cpu_per_component: "500m"
  validation:
    strict_mode: true
"""
    
    logger.info("=== Testing Schema Healing ===")
    logger.info("Creating blueprint with intentional schema mismatch:")
    logger.info("- Controller outputs: object")
    logger.info("- Store expects: integer")
    logger.info("- Expected: Healing should fix this to 'any' type")
    
    # Parse with self-healing enabled
    parser = SystemBlueprintParser()
    
    try:
        # This should trigger healing and succeed
        blueprint = parser.parse_string(blueprint_yaml, max_healing_attempts=3)
        
        logger.info("✅ Blueprint parsing succeeded with healing!")
        
        # Verify the schema was healed
        store_component = None
        for comp in blueprint.system.components:
            if comp.name == "task_store":
                store_component = comp
                break
        
        if store_component:
            for input_port in store_component.inputs:
                if input_port.name == "data":
                    # Check both possible schema field names
                    schema_value = getattr(input_port, 'schema', None) or getattr(input_port, 'schema_type', None)
                    logger.info(f"Store input schema after healing: {schema_value}")
                    logger.info(f"Available attributes: {dir(input_port)}")
                    if schema_value == "any":
                        logger.info("✅ Schema healing worked! Changed from 'integer' to 'any'")
                        return True
                    else:
                        logger.error(f"❌ Schema healing failed - still {schema_value}, expected 'any'")
                        return False
        
        logger.error("❌ Could not find store component or data input port")
        return False
        
    except Exception as e:
        logger.error(f"❌ Blueprint parsing failed even with healing: {e}")
        return False

def test_healing_retry_loop():
    """Test that healing retry loop works with multiple attempts"""
    
    blueprint_yaml = """
schema_version: "1.0.0"

system:
  name: "test_healing_retry"
  description: "Test system for healing retry loop"
  version: "1.0.0"
  
  components:
    - name: data_source
      type: Source
      description: "Data source component"
      outputs:
        - name: output
          schema_type: "string"
          
    - name: data_sink
      type: Sink
      description: "Data sink component"
      inputs:
        - name: input
          schema_type: "integer"  # Mismatch: string -> integer
  
  bindings:
    - from_component: data_source
      from_port: output
      to_components: [data_sink]
      to_ports: [input]

policy:
  security:
    encryption_at_rest: true
    encryption_in_transit: true
    authentication_required: true
  resource_limits:
    max_memory_per_component: "512Mi"
    max_cpu_per_component: "500m"
  validation:
    strict_mode: true
"""
    
    logger.info("\n=== Testing Healing Retry Loop ===")
    logger.info("Creating blueprint with string->integer schema mismatch")
    logger.info("Testing multiple healing attempts...")
    
    parser = SystemBlueprintParser()
    
    try:
        # Test with limited attempts first (should succeed)
        blueprint = parser.parse_string(blueprint_yaml, max_healing_attempts=2)
        logger.info("✅ Healing retry loop succeeded!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Healing retry loop failed: {e}")
        return False

def main():
    """Run all schema healing tests"""
    
    logger.info("Starting Schema Healing Tests")
    logger.info("=" * 50)
    
    test1_result = test_schema_healing()
    test2_result = test_healing_retry_loop()
    
    logger.info("\n" + "=" * 50)
    logger.info("Test Results:")
    logger.info(f"Schema Healing: {'✅ PASS' if test1_result else '❌ FAIL'}")
    logger.info(f"Retry Loop: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        logger.info("🎉 ALL TESTS PASSED - Schema healing is working!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Schema healing needs more work")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)