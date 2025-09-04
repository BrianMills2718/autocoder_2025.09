#!/usr/bin/env python3
"""
Test LLM Integration Timeout
Verifies that LLM calls complete within 30 seconds and don't hang
"""
import asyncio
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser

async def test_llm_timeout():
    """Test that LLM component generation completes within timeout"""
    print("=== Testing LLM Integration Timeout ===\n")
    
    # Create test blueprint
    test_blueprint_yaml = """
schema_version: "1.0.0"

policy:
  security:
    encryption_at_rest: true
    encryption_in_transit: true

system:
  name: test_system
  description: Simple test system
  version: 1.0.0
  
  components:
    - name: todo_api
      type: APIEndpoint
      description: API endpoint for managing todos
      inputs:
        - name: request
          schema: request_schema
      outputs:
        - name: response
          schema: response_schema
      configuration:
        port: 8080
  
  bindings: []  # No bindings for this simple test
  
schemas:
  request_schema:
    type: object
    properties:
      action:
        type: string
      data:
        type: object
  response_schema:
    type: object
    properties:
      status:
        type: string
      data:
        type: object
"""
    
    try:
        # Parse blueprint
        parser = SystemBlueprintParser()
        parsed_blueprint = parser.parse_string(test_blueprint_yaml)
        
        # Create component generator
        generator = LLMComponentGenerator()
        
        # Test component generation with timeout
        component = parsed_blueprint.system.components[0]
        
        print(f"Generating component: {component.name} ({component.type})")
        print(f"Description: {component.description}")
        
        start_time = time.time()
        
        # Generate component (should complete within timeout)
        generated_code = await generator.generate_component_implementation(
            component_type=component.type,
            component_name=component.name,
            component_description=component.description,
            component_config=component.config,
            class_name=f"Generated{component.type}_{component.name}"
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Component generated in {elapsed_time:.2f} seconds")
        print(f"   Generated code length: {len(generated_code)} characters")
        
        # Verify it completed within timeout
        if elapsed_time < 30:
            print(f"✅ PASSED: Generation completed within 30 second timeout")
            return True
        else:
            print(f"❌ FAILED: Generation took {elapsed_time:.2f} seconds (> 30s timeout)")
            return False
            
    except asyncio.TimeoutError:
        print("❌ FAILED: LLM request timed out")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_timeout())
    sys.exit(0 if success else 1)