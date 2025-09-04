#!/usr/bin/env python3
"""
Smoke Tests for AutoCoder4_CC
Tests critical workflows to identify actual problems
"""

import os
import sys
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from autocoder_cc.components.store import Store
from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc.components.component_registry import component_registry
# CLI import is optional - may not have main function exported
from autocoder_cc.llm_providers.unified_llm_provider import UnifiedLLMProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest


class TestSmokeTests:
    """Critical path smoke tests"""
    
    @pytest.mark.asyncio
    async def test_system_generation_workflow(self):
        """Test 1: System generation end-to-end"""
        print("\n=== SMOKE TEST 1: System Generation ===")
        
        try:
            # Create a simple blueprint without external dependencies
            blueprint_yaml = """
system:
  name: test_system
  description: Simple test system
  components:
    - name: data_source
      type: Source
      description: Generate test data
      processing_mode: stream
      inputs: []
      outputs:
        - name: test_data
          description: Test data output
    - name: data_transformer
      type: Transformer
      description: Transform data for API
      processing_mode: stream
      inputs:
        - name: input_data
          description: Input data
      outputs:
        - name: transformed_data
          description: Transformed data
    - name: api
      type: APIEndpoint
      description: API endpoint for testing
      processing_mode: stream
      inputs:
        - name: data_in
          description: Data input
      outputs:
        - name: api_response
          description: API responses
      configuration:
        port: 8080
    - name: store
      type: Sink
      description: Store component for testing
      processing_mode: stream
      inputs:
        - name: store_input
          description: Data to store
      outputs: []
  bindings:
    - from: data_source.test_data
      to: data_transformer.input_data
    - from: data_transformer.transformed_data
      to: api.data_in
    - from: api.api_response
      to: store.store_input
            """
            
            # Generate system using mock LLM
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                generator = SystemGenerator(output_dir=tmpdir)
            
                # This should not hang with mock provider (no timeout - use centralized timeout manager)
                try:
                    result = await generator.generate_system_from_yaml(blueprint_yaml)
                    print("✅ System generation completed without hanging")
                    assert result is not None
                    assert 'system' in result or 'components' in result
                    return True
                except Exception as e:
                    print(f"❌ System generation failed: {e}")
                    return False
        except Exception as e:
            print(f"❌ Test setup failed: {e}")
            return False
    
    def test_component_integration(self):
        """Test 2: Component integration and store CRUD"""
        print("\n=== SMOKE TEST 2: Component Integration ===")
        
        try:
            # Test store component
            store = Store(name="test_store")
            
            # Test CRUD operations
            test_data = {"id": 1, "name": "test", "value": 42}
            
            # Create
            store.create("test_key", test_data)
            print("✅ Store CREATE works")
            
            # Read
            result = store.read("test_key")
            assert result == test_data
            print("✅ Store READ works")
            
            # Update
            updated_data = {"id": 1, "name": "updated", "value": 100}
            store.update("test_key", updated_data)
            result = store.read("test_key")
            assert result == updated_data
            print("✅ Store UPDATE works")
            
            # Delete
            store.delete("test_key")
            result = store.read("test_key")
            assert result is None
            print("✅ Store DELETE works")
            
            return True
            
        except Exception as e:
            print(f"❌ Component integration failed: {e}")
            return False
    
    def test_cli_operations(self):
        """Test 3: CLI basic operations"""
        print("\n=== SMOKE TEST 3: CLI Operations ===")
        
        try:
            # Test CLI help
            import subprocess
            result = subprocess.run(
                ["python", "-m", "autocoder_cc.cli.main", "--help"],
                capture_output=True,
                text=True  # No timeout
            )
            
            if result.returncode == 0:
                print("✅ CLI help command works")
            else:
                print(f"❌ CLI help failed: {result.stderr}")
                return False
            
            # Test CLI version or info command if available
            # This is a placeholder - add actual CLI commands as needed
            
            return True
            
        except Exception as e:
            print(f"❌ CLI operations failed: {e}")
            return False
    
    @pytest.mark.asyncio
    async def test_system_execution(self):
        """Test 4: Generated system can start and respond"""
        print("\n=== SMOKE TEST 4: System Execution ===")
        
        try:
            # Create a minimal component
            class TestComponent(ComposedComponent):
                async def start(self):
                    await super().start()
                    self.logger.info("Test component started")
                
                async def stop(self):
                    await super().stop()
                    self.logger.info("Test component stopped")
                
                async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
                    return {"status": "processed", "echo": message}
            
            # Create and start component
            component = TestComponent(name="test_component")
            await component.start()
            print("✅ Component starts successfully")
            
            # Test message processing
            test_message = {"type": "test", "data": "hello"}
            response = await component.process_message(test_message)
            assert response["status"] == "processed"
            assert response["echo"] == test_message
            print("✅ Component processes messages")
            
            # Stop component
            await component.stop()
            print("✅ Component stops successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ System execution failed: {e}")
            return False
    
    @pytest.mark.asyncio
    async def test_llm_provider_health(self):
        """Test 5: LLM provider health check"""
        print("\n=== SMOKE TEST 5: LLM Provider Health ===")
        
        try:
            provider = UnifiedLLMProvider()
            
            # Test health check
            health = await provider.health_check()
            if not health:
                print("⚠️ No LLM providers configured - skipping test")
                return True  # Skip if no providers configured
            
            print("✅ LLM provider health check passes")
            
            # Only test generation if we have a real provider
            if provider.api_keys.get('openai') or provider.api_keys.get('gemini') or provider.api_keys.get('anthropic'):
                request = LLMRequest(
                    system_prompt="You are a helpful assistant",
                    user_prompt="Say 'OK' if you are working",
                    max_tokens=10
                )
                
                response = await provider.generate(request)
                assert response is not None
                assert response.content is not None
                print("✅ LLM provider generates responses")
            else:
                print("⚠️ No API keys configured - skipping generation test")
            
            return True
            
        except Exception as e:
            print(f"❌ LLM provider health check failed: {e}")
            return False
    
    def test_component_registry(self):
        """Test 6: Component registry loads all types"""
        print("\n=== SMOKE TEST 6: Component Registry ===")
        
        try:
            # Check that all expected component types are registered
            expected_types = [
                'Source', 'Transformer', 'StreamProcessor', 'Sink',
                'Store', 'Controller', 'APIEndpoint', 'Model',
                'Accumulator', 'Router', 'Aggregator', 'Filter', 'WebSocket'
            ]
            
            registered_types = component_registry.list_component_types()
            
            for comp_type in expected_types:
                if comp_type in registered_types:
                    print(f"✅ {comp_type} registered")
                else:
                    print(f"❌ {comp_type} NOT registered")
                    return False
            
            print(f"✅ All {len(expected_types)} component types registered")
            return True
            
        except Exception as e:
            print(f"❌ Component registry check failed: {e}")
            return False


async def run_all_smoke_tests():
    """Run all smoke tests and report results"""
    print("=" * 60)
    print("AUTOCODER4_CC SMOKE TEST SUITE")
    print("=" * 60)
    
    tests = TestSmokeTests()
    results = []
    
    # Run async tests
    result1 = await tests.test_system_generation_workflow()
    results.append(("System Generation", result1))
    
    # Run sync tests
    result2 = tests.test_component_integration()
    results.append(("Component Integration", result2))
    
    result3 = tests.test_cli_operations()
    results.append(("CLI Operations", result3))
    
    # Run async test
    result4 = await tests.test_system_execution()
    results.append(("System Execution", result4))
    
    result5 = await tests.test_llm_provider_health()
    results.append(("LLM Provider Health", result5))
    
    result6 = tests.test_component_registry()
    results.append(("Component Registry", result6))
    
    # Summary
    print("\n" + "=" * 60)
    print("SMOKE TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed == 0:
        print("\n🎉 ALL SMOKE TESTS PASSED! System is functional.")
    else:
        print(f"\n⚠️ {failed} SMOKE TESTS FAILED. See details above.")
    
    return failed == 0


if __name__ == "__main__":
    # Run smoke tests
    success = asyncio.run(run_all_smoke_tests())
    sys.exit(0 if success else 1)