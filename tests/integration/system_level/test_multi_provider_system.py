#!/usr/bin/env python3
"""
Test multi-provider LLM abstraction system
"""
import sys
import asyncio
import traceback
from pathlib import Path

# Add autocoder_cc to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_provider_registration():
    """Test provider registration and health checks"""
    try:
        from autocoder_cc.llm_providers.provider_registry import LLMProviderRegistry
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        
        registry = LLMProviderRegistry()
        
        # Test OpenAI provider registration
        openai_config = {
            "api_key": "test-key",
            "default_model": "gpt-4o-mini"
        }
        openai_provider = OpenAIProvider(openai_config)
        registry.register_provider(openai_provider)
        
        # Test Anthropic provider registration
        anthropic_config = {
            "api_key": "test-key",
            "default_model": "claude-3-5-sonnet-20241022"
        }
        anthropic_provider = AnthropicProvider(anthropic_config)
        registry.register_provider(anthropic_provider)
        
        # Validate registration
        providers = registry.list_providers()
        if "openai" in providers and "anthropic" in providers:
            print("✅ Provider registration successful")
            return True
        else:
            print(f"❌ Provider registration failed: {providers}")
            return False
            
    except Exception as e:
        print(f"❌ Provider registration test failed: {e}")
        traceback.print_exc()
        return False

async def test_failover_logic():
    """Test automatic failover between providers"""
    try:
        from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        from autocoder_cc.llm_providers.base_provider import LLMRequest
        
        # Create manager with failover configuration
        config = {
            "primary_provider": "openai",
            "fallback_providers": ["anthropic"],
            "max_retries": 2
        }
        manager = MultiProviderManager(config)
        
        # Register mock providers (they will fail health checks with test keys)
        openai_provider = OpenAIProvider({"api_key": "test-key"})
        anthropic_provider = AnthropicProvider({"api_key": "test-key"})
        
        manager.registry.register_provider(openai_provider)
        manager.registry.register_provider(anthropic_provider)
        
        # Test request
        request = LLMRequest(
            system_prompt="You are a helpful assistant",
            user_prompt="Say hello",
            max_tokens=10
        )
        
        try:
            # This should fail due to invalid API keys, testing failover logic
            await manager.generate(request)
            print("❌ Expected failover test to fail with invalid keys")
            return False
        except Exception as e:
            if "All providers failed" in str(e):
                print("✅ Failover logic working (correctly failed with invalid keys)")
                return True
            else:
                print(f"❌ Unexpected failover error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failover test failed: {e}")
        traceback.print_exc()
        return False

async def test_cost_tracking():
    """Test cost tracking and statistics"""
    try:
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider({
            "api_key": "test-key",
            "default_model": "gpt-4o-mini"
        })
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, "gpt-4o-mini")
        if cost > 0:
            print(f"✅ Cost estimation working: ${cost:.6f} for 1000 tokens")
        else:
            print("❌ Cost estimation failed")
            return False
        
        # Test statistics
        stats = provider.get_stats()
        expected_keys = ["provider", "total_tokens", "total_cost", "request_count"]
        if all(key in stats for key in expected_keys):
            print("✅ Statistics tracking working")
            return True
        else:
            print(f"❌ Statistics missing keys: {stats}")
            return False
            
    except Exception as e:
        print(f"❌ Cost tracking test failed: {e}")
        traceback.print_exc()
        return False

async def test_component_generator_integration():
    """Test integration with component generator"""
    try:
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        
        # Test with multi-provider configuration
        config = {
            'llm_providers': {
                'primary_provider': 'openai', 
                'fallback_providers': ['anthropic'],
                'max_retries': 2
            },
            'openai_api_key': 'test-key',
            'anthropic_api_key': 'test-key'
        }
        
        generator = LLMComponentGenerator(config)
        
        # Verify multi-provider system is initialized
        if hasattr(generator, 'multi_provider') and generator.multi_provider:
            print("✅ Component generator multi-provider integration working")
            
            # Check provider registration
            providers = generator.multi_provider.registry.list_providers()
            if providers:
                print(f"✅ Providers registered: {providers}")
                return True
            else:
                print("❌ No providers registered in component generator")
                return False
        else:
            print("❌ Multi-provider system not initialized in component generator")
            return False
            
    except Exception as e:
        print(f"❌ Component generator integration test failed: {e}")
        traceback.print_exc()
        return False

async def test_model_availability():
    """Test that providers report available models"""
    try:
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        
        # Test OpenAI models
        openai_provider = OpenAIProvider({"api_key": "test-key"})
        openai_models = openai_provider.get_available_models()
        if openai_models and "gpt-4o-mini" in openai_models:
            print(f"✅ OpenAI models available: {openai_models}")
        else:
            print(f"❌ OpenAI models not available: {openai_models}")
            return False
        
        # Test Anthropic models
        anthropic_provider = AnthropicProvider({"api_key": "test-key"})
        anthropic_models = anthropic_provider.get_available_models()
        if anthropic_models and "claude-3-5-sonnet-20241022" in anthropic_models:
            print(f"✅ Anthropic models available: {anthropic_models}")
            return True
        else:
            print(f"❌ Anthropic models not available: {anthropic_models}")
            return False
            
    except Exception as e:
        print(f"❌ Model availability test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all multi-provider tests"""
    print("🧪 Testing Multi-Provider LLM Abstraction System")
    print("=" * 50)
    
    tests = [
        test_provider_registration,
        test_failover_logic,
        test_cost_tracking,
        test_component_generator_integration,
        test_model_availability
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n📋 Running {test.__name__}...")
        if await test():
            passed += 1
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All multi-provider tests PASSED!")
        return True
    else:
        print("❌ Some multi-provider tests FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)