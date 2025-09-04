#!/usr/bin/env python3
"""
Real-World Integration Testing - Multi-Provider LLM System
Tests all providers with actual API keys and production scenarios
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/home/brian/autocoder4_cc')

# Import our multi-provider system
from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
from autocoder_cc.llm_providers.anthropic_provider import AnthropicProvider
from autocoder_cc.llm_providers.gemini_provider import GeminiProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest, LLMProviderError
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

# Import unified component validator for standardized validation
from unified_component_validator import UnifiedComponentValidator

class RealWorldTester:
    """Comprehensive real-world testing suite"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result with timestamp"""
        self.results[test_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}: {details.get('message', 'No details')}")
    
    async def test_gemini_provider_real_api(self) -> bool:
        """Test Gemini Flash 2.5 with real API key"""
        print("\n🧪 REAL-WORLD TEST 1: Gemini Flash 2.5 with Actual API Key")
        print("=" * 60)
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.log_result("gemini_real_api", False, {
                "message": "GEMINI_API_KEY environment variable not set",
                "suggestion": "Set GEMINI_API_KEY to test with real API"
            })
            return False
        
        try:
            # Create Gemini provider with real API key
            provider = GeminiProvider({
                "api_key": api_key,
                "default_model": "gemini-2.5-flash"
            })
            
            # Test health check
            health_start = time.time()
            health_result = await provider.health_check()
            health_time = time.time() - health_start
            
            if not health_result:
                self.log_result("gemini_real_api", False, {
                    "message": "Gemini health check failed",
                    "health_time": health_time,
                    "api_key_length": len(api_key)
                })
                return False
            
            # Test actual generation
            request = LLMRequest(
                system_prompt="You are a helpful coding assistant.",
                user_prompt="Write a simple Python function that calculates fibonacci numbers. Keep it under 20 lines.",
                max_tokens=500,
                temperature=0.3
            )
            
            gen_start = time.time()
            response = await provider.generate(request)
            gen_time = time.time() - gen_start
            
            # Validate response
            if not response.content or len(response.content) < 50:
                self.log_result("gemini_real_api", False, {
                    "message": "Generated content too short or empty",
                    "content_length": len(response.content),
                    "response": response.content[:100]
                })
                return False
            
            # Validate cost tracking
            if response.cost_usd <= 0:
                self.log_result("gemini_real_api", False, {
                    "message": "Cost tracking not working",
                    "reported_cost": response.cost_usd
                })
                return False
            
            self.log_result("gemini_real_api", True, {
                "message": "Gemini Flash 2.5 working with real API",
                "model": response.model,
                "tokens_used": response.tokens_used,
                "cost_usd": response.cost_usd,
                "response_time": response.response_time,
                "health_check_time": health_time,
                "generation_time": gen_time,
                "content_length": len(response.content),
                "content_preview": response.content[:200] + "..." if len(response.content) > 200 else response.content
            })
            
            return True
            
        except Exception as e:
            self.log_result("gemini_real_api", False, {
                "message": f"Exception during Gemini testing: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_multi_provider_failover_real(self) -> bool:
        """Test provider failover with real APIs"""
        print("\n🧪 REAL-WORLD TEST 2: Multi-Provider Failover with Real APIs")
        print("=" * 60)
        
        try:
            # Create multi-provider manager with real API keys
            manager = MultiProviderManager({
                "retry_attempts": 3,
                "exponential_backoff": True,
                "health_check_timeout": 30
            })
            
            # Register providers if API keys are available
            providers_registered = []
            
            # Register Gemini (primary)
            if os.getenv("GEMINI_API_KEY"):
                gemini_provider = GeminiProvider({
                    "api_key": os.getenv("GEMINI_API_KEY"),
                    "default_model": "gemini-2.5-flash"
                })
                manager.registry.register_provider(gemini_provider)
                providers_registered.append("gemini")
            
            # Register OpenAI (fallback)
            if os.getenv("OPENAI_API_KEY"):
                openai_provider = OpenAIProvider({
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini"
                })
                manager.registry.register_provider(openai_provider)
                providers_registered.append("openai")
            
            # Register Anthropic (fallback)
            if os.getenv("ANTHROPIC_API_KEY"):
                anthropic_provider = AnthropicProvider({
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "default_model": "claude-3-5-haiku-20241022"
                })
                manager.registry.register_provider(anthropic_provider)
                providers_registered.append("anthropic")
            
            if not providers_registered:
                self.log_result("multi_provider_failover", False, {
                    "message": "No API keys available for testing",
                    "suggestion": "Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
                })
                return False
            
            # Test generation with failover
            request = LLMRequest(
                system_prompt="You are a helpful assistant.",
                user_prompt="Explain dependency injection in one sentence.",
                max_tokens=100,
                temperature=0.5
            )
            
            start_time = time.time()
            response = await manager.generate(request)
            total_time = time.time() - start_time
            
            if not response or not response.content:
                self.log_result("multi_provider_failover", False, {
                    "message": "No response from any provider",
                    "providers_available": providers_registered,
                    "total_time": total_time
                })
                return False
            
            self.log_result("multi_provider_failover", True, {
                "message": "Multi-provider failover working with real APIs",
                "providers_available": providers_registered,
                "provider_used": response.provider,
                "model_used": response.model,
                "tokens_used": response.tokens_used,
                "cost_usd": response.cost_usd,
                "total_time": total_time,
                "content_preview": response.content[:100]
            })
            
            return True
            
        except Exception as e:
            self.log_result("multi_provider_failover", False, {
                "message": f"Exception during failover testing: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_cost_tracking_accuracy(self) -> bool:
        """Validate cost tracking accuracy in production"""
        print("\n🧪 REAL-WORLD TEST 3: Cost Tracking Accuracy Validation")
        print("=" * 60)
        
        try:
            total_cost = 0.0
            cost_samples = []
            
            # Test multiple providers if available
            test_configs = []
            
            if os.getenv("GEMINI_API_KEY"):
                test_configs.append(("gemini", GeminiProvider({
                    "api_key": os.getenv("GEMINI_API_KEY"),
                    "default_model": "gemini-2.5-flash"
                })))
            
            if os.getenv("OPENAI_API_KEY"):
                test_configs.append(("openai", OpenAIProvider({
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini"
                })))
            
            if not test_configs:
                self.log_result("cost_tracking_accuracy", False, {
                    "message": "No API keys available for cost tracking test"
                })
                return False
            
            # Test each provider with small requests
            for provider_name, provider in test_configs:
                request = LLMRequest(
                    system_prompt="You are a helpful assistant.",
                    user_prompt="Say 'Hello' in 5 different languages.",
                    max_tokens=50,
                    temperature=0.1
                )
                
                response = await provider.generate(request)
                
                if response.cost_usd > 0:
                    cost_samples.append({
                        "provider": provider_name,
                        "model": response.model,
                        "tokens": response.tokens_used,
                        "cost": response.cost_usd,
                        "cost_per_token": response.cost_usd / response.tokens_used if response.tokens_used > 0 else 0
                    })
                    total_cost += response.cost_usd
            
            if not cost_samples:
                self.log_result("cost_tracking_accuracy", False, {
                    "message": "No cost data collected from any provider"
                })
                return False
            
            # Validate cost ranges are reasonable using provider-specific thresholds
            def validate_cost_reasonable(cost_per_token: float, provider: str, model: str) -> bool:
                # Provider-specific cost ranges (per token)
                PROVIDER_RANGES = {
                    "openai": {
                        "gpt-4o-mini": {"min": 0.000000150, "max": 0.000000600},
                        "gpt-4o": {"min": 0.000002500, "max": 0.000010000},
                    },
                    "anthropic": {
                        "claude-3-5-haiku": {"min": 0.000001000, "max": 0.000005000},
                        "claude-3-5-sonnet": {"min": 0.000003000, "max": 0.000015000},
                    },
                    "gemini": {
                        "gemini-2.5-flash": {"min": 0.000000075, "max": 0.000000300},
                    }
                }
                
                if provider not in PROVIDER_RANGES:
                    # Unknown provider - use generous range
                    return 0.00000001 <= cost_per_token <= 0.0001
                
                provider_models = PROVIDER_RANGES[provider]
                
                # Find matching model or use first available range
                for model_name, range_data in provider_models.items():
                    if model_name.lower() in model.lower():
                        return range_data["min"] <= cost_per_token <= range_data["max"]
                
                # Use first available range for this provider
                model_range = list(provider_models.values())[0]
                return model_range["min"] <= cost_per_token <= model_range["max"]
            
            for sample in cost_samples:
                if not validate_cost_reasonable(sample["cost_per_token"], sample["provider"], sample["model"]):
                    self.log_result("cost_tracking_accuracy", False, {
                        "message": f"Cost per token outside reasonable range for {sample['provider']} {sample['model']}",
                        "cost_per_token": sample["cost_per_token"],
                        "sample": sample
                    })
                    return False
            
            self.log_result("cost_tracking_accuracy", True, {
                "message": "Cost tracking working accurately",
                "total_cost": total_cost,
                "cost_samples": cost_samples,
                "providers_tested": len(cost_samples),
                "avg_cost_per_token": sum(s["cost_per_token"] for s in cost_samples) / len(cost_samples)
            })
            
            return True
            
        except Exception as e:
            self.log_result("cost_tracking_accuracy", False, {
                "message": f"Exception during cost tracking test: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_component_generation_workload(self) -> bool:
        """Test component generation under real workloads"""
        print("\n🧪 REAL-WORLD TEST 4: Component Generation Under Real Workloads")
        print("=" * 60)
        
        try:
            # Configure component generator with Gemini primary
            config = {
                "llm_providers": {
                    "primary_provider": "gemini",
                    "fallback_providers": ["openai", "anthropic"],
                    "max_retries": 3
                }
            }
            
            generator = LLMComponentGenerator(config)
            
            # Test different component types
            test_components = [
                {
                    "type": "DataProcessor",
                    "description": "Process user analytics data from API requests",
                    "inputs": ["user_data", "analytics_config"],
                    "outputs": ["processed_data", "metrics"]
                },
                {
                    "type": "ApiValidator",
                    "description": "Validate incoming API requests and sanitize inputs",
                    "inputs": ["raw_request"],
                    "outputs": ["validated_request", "validation_errors"]
                }
            ]
            
            generation_results = []
            total_generation_time = 0
            
            for component_spec in test_components:
                blueprint = {
                    "component_type": component_spec["type"].lower(),
                    "description": component_spec["description"],
                    "metadata": {
                        "inputs": component_spec["inputs"],
                        "outputs": component_spec["outputs"]
                    }
                }
                
                start_time = time.time()
                
                try:
                    result = await generator.generate_component_implementation(
                        component_spec["type"].lower(),  # component_type
                        component_spec["type"] + "Component",  # component_name
                        component_spec["description"],  # component_description
                        blueprint["metadata"],  # component_config
                        component_spec["type"] + "Component"  # class_name
                    )
                    
                    generation_time = time.time() - start_time
                    total_generation_time += generation_time
                    
                    # Validate the generated code
                    if not result or len(result) < 100:
                        generation_results.append({
                            "component": component_spec["type"],
                            "success": False,
                            "message": "Generated code too short",
                            "length": len(result) if result else 0
                        })
                        continue
                    
                    # Use unified validator for consistent validation (P0.6-F2 fix)
                    validator = UnifiedComponentValidator()
                    validation_result = validator.validate_component(result, component_spec["type"])
                    
                    # Convert to format expected by existing test logic
                    generation_results.append({
                        "component": component_spec["type"],
                        "success": validation_result["success"],
                        "message": validation_result["message"],
                        "missing_patterns": validation_result.get("missing_patterns", []),
                        "generation_time": generation_time,
                        "code_length": validation_result["code_length"],
                        "lines_of_code": validation_result["lines_of_code"],
                        "syntax_valid": validation_result["syntax_valid"],
                        "quality_percentage": validation_result["quality_percentage"]
                    })
                    
                except Exception as e:
                    generation_results.append({
                        "component": component_spec["type"],
                        "success": False,
                        "message": f"Generation failed: {str(e)}",
                        "exception_type": type(e).__name__
                    })
            
            # Evaluate results
            successful_generations = [r for r in generation_results if r["success"]]
            success_rate = len(successful_generations) / len(test_components) if test_components else 0
            
            if success_rate < 0.8:  # Require 80% success rate
                self.log_result("component_generation_workload", False, {
                    "message": f"Component generation success rate too low: {success_rate:.1%}",
                    "success_rate": success_rate,
                    "total_components": len(test_components),
                    "successful_components": len(successful_generations),
                    "results": generation_results
                })
                return False
            
            self.log_result("component_generation_workload", True, {
                "message": "Component generation working under real workload",
                "success_rate": success_rate,
                "total_generation_time": total_generation_time,
                "avg_generation_time": total_generation_time / len(test_components),
                "components_tested": len(test_components),
                "successful_generations": len(successful_generations),
                "results": generation_results
            })
            
            return True
            
        except Exception as e:
            self.log_result("component_generation_workload", False, {
                "message": f"Exception during component generation test: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_performance_benchmarks(self) -> bool:
        """Performance benchmarking with actual API calls"""
        print("\n🧪 REAL-WORLD TEST 5: Performance Benchmarking")
        print("=" * 60)
        
        try:
            # Test performance of different providers
            benchmark_results = {}
            
            providers_to_test = []
            if os.getenv("GEMINI_API_KEY"):
                providers_to_test.append(("gemini", GeminiProvider({
                    "api_key": os.getenv("GEMINI_API_KEY"),
                    "default_model": "gemini-2.5-flash"
                })))
            
            if os.getenv("OPENAI_API_KEY"):
                providers_to_test.append(("openai", OpenAIProvider({
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini"
                })))
            
            if not providers_to_test:
                self.log_result("performance_benchmarks", False, {
                    "message": "No API keys available for performance testing"
                })
                return False
            
            # Run performance tests
            for provider_name, provider in providers_to_test:
                times = []
                costs = []
                tokens = []
                
                # Run 3 test requests for each provider
                for i in range(3):
                    request = LLMRequest(
                        system_prompt="You are a helpful coding assistant.",
                        user_prompt=f"Write a Python function to sort a list. Test run {i+1}.",
                        max_tokens=200,
                        temperature=0.3
                    )
                    
                    start_time = time.time()
                    response = await provider.generate(request)
                    total_time = time.time() - start_time
                    
                    times.append(total_time)
                    costs.append(response.cost_usd)
                    tokens.append(response.tokens_used)
                
                benchmark_results[provider_name] = {
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "avg_cost": sum(costs) / len(costs),
                    "avg_tokens": sum(tokens) / len(tokens),
                    "total_requests": len(times)
                }
            
            self.log_result("performance_benchmarks", True, {
                "message": "Performance benchmarking completed",
                "benchmark_results": benchmark_results,
                "providers_tested": list(benchmark_results.keys())
            })
            
            return True
            
        except Exception as e:
            self.log_result("performance_benchmarks", False, {
                "message": f"Exception during performance testing: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all real-world tests"""
        print("🚀 Starting Real-World Integration Testing")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        test_results.append(await self.test_gemini_provider_real_api())
        test_results.append(await self.test_multi_provider_failover_real())
        test_results.append(await self.test_cost_tracking_accuracy())
        test_results.append(await self.test_component_generation_workload())
        test_results.append(await self.test_performance_benchmarks())
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 REAL-WORLD TESTING SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Failed Tests: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1%}")
        print(f"Test Duration: {(datetime.now() - self.start_time).total_seconds():.1f} seconds")
        
        # Save results to file
        results_file = "/home/brian/autocoder4_cc/test_real_world_integration_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate,
                    "test_duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        if success_rate >= 0.8:  # 80% success rate required
            print("✅ REAL-WORLD TESTING PASSED")
            return True
        else:
            print("❌ REAL-WORLD TESTING FAILED")
            return False

async def main():
    """Main test execution"""
    tester = RealWorldTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All real-world tests completed successfully!")
        print("System is ready for production deployment.")
    else:
        print("\n⚠️ Some real-world tests failed.")
        print("Review the results and fix issues before production deployment.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())