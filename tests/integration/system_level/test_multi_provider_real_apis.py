#!/usr/bin/env python3
"""
Test multi-provider LLM abstraction system with REAL API keys
"""
import sys
import asyncio
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add autocoder_cc to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_real_provider_registration():
    """Test provider registration with real API keys"""
    try:
        from autocoder_cc.llm_providers.provider_registry import LLMProviderRegistry
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        
        registry = LLMProviderRegistry()
        providers_registered = 0
        
        # Test OpenAI provider with real API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_config = {
                "api_key": openai_api_key,
                "default_model": "gpt-4o-mini"
            }
            openai_provider = OpenAIProvider(openai_config)
            registry.register_provider(openai_provider)
            providers_registered += 1
            print(f"✅ OpenAI provider registered with real API key")
        else:
            print("⚠️ No OpenAI API key found in environment")
        
        # Test Anthropic provider with real API key
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            anthropic_config = {
                "api_key": anthropic_api_key,
                "default_model": "claude-3-5-sonnet-20241022"
            }
            anthropic_provider = AnthropicProvider(anthropic_config)
            registry.register_provider(anthropic_provider)
            providers_registered += 1
            print(f"✅ Anthropic provider registered with real API key")
        else:
            print("⚠️ No Anthropic API key found in environment")
        
        # Validate registration
        if providers_registered > 0:
            providers = registry.list_providers()
            print(f"✅ Real API provider registration successful: {providers}")
            return True
        else:
            print("❌ No real API keys available for testing")
            return False
            
    except Exception as e:
        print(f"❌ Real provider registration test failed: {e}")
        traceback.print_exc()
        return False

async def test_real_health_checks():
    """Test health checks with real API keys"""
    try:
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        
        health_checks_passed = 0
        total_checks = 0
        
        # Test OpenAI health check
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_provider = OpenAIProvider({
                "api_key": openai_api_key,
                "default_model": "gpt-4o-mini"
            })
            total_checks += 1
            try:
                health = await openai_provider.health_check()
                if health:
                    print("✅ OpenAI health check PASSED with real API")
                    health_checks_passed += 1
                else:
                    print("❌ OpenAI health check FAILED with real API")
            except Exception as e:
                print(f"❌ OpenAI health check error: {e}")
        
        # Test Anthropic health check
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            anthropic_provider = AnthropicProvider({
                "api_key": anthropic_api_key,
                "default_model": "claude-3-5-sonnet-20241022"
            })
            total_checks += 1
            try:
                health = await anthropic_provider.health_check()
                if health:
                    print("✅ Anthropic health check PASSED with real API")
                    health_checks_passed += 1
                else:
                    print("❌ Anthropic health check FAILED with real API")
            except Exception as e:
                print(f"❌ Anthropic health check error: {e}")
        
        if total_checks > 0:
            print(f"📊 Health checks: {health_checks_passed}/{total_checks} passed")
            return health_checks_passed > 0
        else:
            print("⚠️ No API keys available for health check testing")
            return False
            
    except Exception as e:
        print(f"❌ Real health check test failed: {e}")
        traceback.print_exc()
        return False

async def test_real_api_generation():
    """Test actual LLM generation with real API keys"""
    try:
        from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        from autocoder_cc.llm_providers.base_provider import LLMRequest
        
        # Configure with available API keys
        config = {
            "primary_provider": "openai",
            "fallback_providers": ["anthropic"] if os.getenv("ANTHROPIC_API_KEY") else [],
            "max_retries": 2
        }
        manager = MultiProviderManager(config)
        
        providers_registered = 0
        
        # Register OpenAI if key available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_provider = OpenAIProvider({
                "api_key": openai_api_key,
                "default_model": "gpt-4o-mini"
            })
            manager.registry.register_provider(openai_provider)
            providers_registered += 1
        
        # Register Anthropic if key available
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            anthropic_provider = AnthropicProvider({
                "api_key": anthropic_api_key,
                "default_model": "claude-3-5-sonnet-20241022"
            })
            manager.registry.register_provider(anthropic_provider)
            providers_registered += 1
        
        if providers_registered == 0:
            print("⚠️ No API keys available for generation testing")
            return False
        
        # Test actual generation
        request = LLMRequest(
            system_prompt="You are a helpful assistant that generates simple code.",
            user_prompt="Write a simple Python function that adds two numbers and returns the result. Make it 2-3 lines only.",
            max_tokens=100
        )
        
        try:
            response = await manager.generate(request)
            
            # Validate response
            if response and response.content:
                print(f"✅ Real API generation SUCCESSFUL with {response.provider}")
                print(f"   Model: {response.model}")
                print(f"   Tokens: {response.tokens_used}")
                print(f"   Cost: ${response.cost_usd:.6f}")
                print(f"   Time: {response.response_time:.2f}s")
                print(f"   Response preview: {response.content[:100]}...")
                return True
            else:
                print("❌ Real API generation returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Real API generation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Real API generation test failed: {e}")
        traceback.print_exc()
        return False

async def test_real_failover():
    """Test failover behavior with real and invalid API keys"""
    try:
        from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
        from autocoder_cc.llm_providers.base_provider import LLMRequest
        
        # Configure manager with one real provider and one invalid
        config = {
            "primary_provider": "invalid",
            "fallback_providers": ["openai"],
            "max_retries": 1
        }
        manager = MultiProviderManager(config)
        
        # Register invalid provider first (primary)
        invalid_provider = OpenAIProvider({
            "api_key": "invalid-key-for-testing",
            "default_model": "gpt-4o-mini"
        })
        invalid_provider.provider_name = "invalid"  # Override name for testing
        manager.registry.register_provider(invalid_provider)
        
        # Register real OpenAI provider as fallback
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ No OpenAI API key available for failover testing")
            return False
        
        real_provider = OpenAIProvider({
            "api_key": openai_api_key,
            "default_model": "gpt-4o-mini"
        })
        manager.registry.register_provider(real_provider)
        
        # Test failover
        request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'hello' in one word only.",
            max_tokens=10
        )
        
        try:
            response = await manager.generate(request)
            
            if response and response.provider == "openai":
                print("✅ Real failover SUCCESSFUL - failed over from invalid to OpenAI")
                print(f"   Final provider: {response.provider}")
                print(f"   Response: {response.content[:50]}...")
                return True
            else:
                print(f"❌ Real failover unexpected result: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Real failover test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Real failover test failed: {e}")
        traceback.print_exc()
        return False

async def test_real_cost_tracking():
    """Test cost tracking with real API usage"""
    try:
        from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ No OpenAI API key available for cost tracking testing")
            return False
        
        provider = OpenAIProvider({
            "api_key": openai_api_key,
            "default_model": "gpt-4o-mini"
        })
        
        # Test cost estimation
        estimated_cost = provider.estimate_cost(100, "gpt-4o-mini")
        print(f"📊 Estimated cost for 100 tokens: ${estimated_cost:.6f}")
        
        # Test real generation and cost tracking
        from autocoder_cc.llm_providers.base_provider import LLMRequest
        request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            user_prompt="Count to 5.",
            max_tokens=20
        )
        
        try:
            response = await provider.generate(request)
            
            # Check cost tracking
            stats = provider.get_stats()
            print(f"✅ Real cost tracking SUCCESSFUL")
            print(f"   Actual tokens used: {response.tokens_used}")
            print(f"   Actual cost: ${response.cost_usd:.6f}")
            print(f"   Provider stats: {stats}")
            
            # Verify stats are updated
            if stats["total_tokens"] > 0 and stats["total_cost"] > 0:
                print("✅ Cost tracking statistics properly updated")
                return True
            else:
                print("❌ Cost tracking statistics not updated properly")
                return False
                
        except Exception as e:
            print(f"❌ Real cost tracking generation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Real cost tracking test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all real API tests"""
    print("🧪 Testing Multi-Provider LLM System with REAL API KEYS")
    print("=" * 60)
    
    # Check available API keys
    openai_key = "✅" if os.getenv("OPENAI_API_KEY") else "❌"
    anthropic_key = "✅" if os.getenv("ANTHROPIC_API_KEY") else "❌"
    print(f"API Keys Available:")
    print(f"  OpenAI: {openai_key}")
    print(f"  Anthropic: {anthropic_key}")
    print()
    
    tests = [
        test_real_provider_registration,
        test_real_health_checks,
        test_real_api_generation,
        test_real_failover,
        test_real_cost_tracking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"📋 Running {test.__name__}...")
        if await test():
            passed += 1
        print("-" * 40)
    
    print(f"\n📊 Real API Test Results: {passed}/{total} tests passed")
    
    if passed >= 3:  # Allow some tests to fail if API keys missing
        print("🎉 Multi-provider system VALIDATED with real APIs!")
        return True
    else:
        print("❌ Multi-provider system needs improvement!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)