#!/usr/bin/env python3
"""
Focused Real-World Testing - Multi-Provider LLM System
Tests the working aspects with available API keys
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

class FocusedRealWorldTester:
    """Focused real-world testing for working components"""
    
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
    
    async def test_multi_provider_failover_comprehensive(self) -> bool:
        """Comprehensive test of multi-provider failover"""
        print("\n🧪 REAL-WORLD TEST: Comprehensive Multi-Provider Failover")
        print("=" * 60)
        
        try:
            # Create multi-provider manager
            manager = MultiProviderManager({
                "retry_attempts": 3,
                "exponential_backoff": True,
                "health_check_timeout": 30
            })
            
            # Register available providers
            providers_registered = []
            
            # Register OpenAI (should work)
            if os.getenv("OPENAI_API_KEY"):
                openai_provider = OpenAIProvider({
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini"
                })
                manager.registry.register_provider(openai_provider)
                providers_registered.append("openai")
            
            # Register Anthropic (should work)
            if os.getenv("ANTHROPIC_API_KEY"):
                anthropic_provider = AnthropicProvider({
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "default_model": "claude-3-5-haiku-20241022"
                })
                manager.registry.register_provider(anthropic_provider)
                providers_registered.append("anthropic")
            
            # Register Gemini (might fail but should gracefully failover)
            if os.getenv("GEMINI_API_KEY"):
                try:
                    gemini_provider = GeminiProvider({
                        "api_key": os.getenv("GEMINI_API_KEY"),
                        "default_model": "gemini-2.5-flash"
                    })
                    manager.registry.register_provider(gemini_provider)
                    providers_registered.append("gemini")
                except Exception as e:
                    print(f"Note: Gemini registration failed: {e}")
            
            if not providers_registered:
                self.log_result("multi_provider_comprehensive", False, {
                    "message": "No API keys available for testing",
                    "suggestion": "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
                })
                return False
            
            # Test multiple generations with different complexities
            test_prompts = [
                {
                    "name": "simple_response",
                    "system": "You are a helpful assistant.",
                    "user": "Say hello in exactly 3 words.",
                    "max_tokens": 20
                },
                {
                    "name": "code_generation",
                    "system": "You are a Python coding assistant.",
                    "user": "Write a function to reverse a string. Keep it simple.",
                    "max_tokens": 200
                },
                {
                    "name": "structured_output", 
                    "system": "You provide structured responses.",
                    "user": "List 3 benefits of dependency injection in JSON format.",
                    "max_tokens": 300
                }
            ]
            
            test_results = []
            total_cost = 0.0
            total_tokens = 0
            
            for test_prompt in test_prompts:
                request = LLMRequest(
                    system_prompt=test_prompt["system"],
                    user_prompt=test_prompt["user"],
                    max_tokens=test_prompt["max_tokens"],
                    temperature=0.3
                )
                
                start_time = time.time()
                response = await manager.generate(request)
                response_time = time.time() - start_time
                
                if response and response.content:
                    test_results.append({
                        "test": test_prompt["name"],
                        "success": True,
                        "provider": response.provider,
                        "model": response.model,
                        "tokens": response.tokens_used,
                        "cost": response.cost_usd,
                        "response_time": response_time,
                        "content_length": len(response.content)
                    })
                    total_cost += response.cost_usd
                    total_tokens += response.tokens_used
                else:
                    test_results.append({
                        "test": test_prompt["name"],
                        "success": False,
                        "error": "No response received"
                    })
            
            # Calculate success metrics
            successful_tests = [r for r in test_results if r.get("success", False)]
            success_rate = len(successful_tests) / len(test_prompts) if test_prompts else 0
            
            # Get provider usage statistics
            provider_stats = {}
            for result in successful_tests:
                provider = result.get("provider", "unknown")
                if provider not in provider_stats:
                    provider_stats[provider] = {"count": 0, "total_cost": 0.0, "total_tokens": 0}
                provider_stats[provider]["count"] += 1
                provider_stats[provider]["total_cost"] += result.get("cost", 0.0)
                provider_stats[provider]["total_tokens"] += result.get("tokens", 0)
            
            self.log_result("multi_provider_comprehensive", success_rate >= 0.8, {
                "message": f"Multi-provider system working with {success_rate:.1%} success rate",
                "providers_registered": providers_registered,
                "total_tests": len(test_prompts),
                "successful_tests": len(successful_tests),
                "success_rate": success_rate,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "provider_stats": provider_stats,
                "test_results": test_results
            })
            
            return success_rate >= 0.8
            
        except Exception as e:
            self.log_result("multi_provider_comprehensive", False, {
                "message": f"Exception during comprehensive testing: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_component_generation_production(self) -> bool:
        """Test component generation under production conditions"""
        print("\n🧪 REAL-WORLD TEST: Production Component Generation")
        print("=" * 60)
        
        try:
            # Configure component generator with realistic settings
            config = {
                "llm_providers": {
                    "primary_provider": "gemini",
                    "fallback_providers": ["openai", "anthropic"],
                    "max_retries": 2  # Reduced for faster testing
                }
            }
            
            generator = LLMComponentGenerator(config)
            
            # Test realistic component generation scenarios
            test_scenarios = [
                {
                    "type": "EmailProcessor",
                    "description": "Process incoming email messages, extract key information, and route to appropriate handlers",
                    "config": {
                        "inputs": ["raw_email", "routing_rules"],
                        "outputs": ["processed_email", "routing_decision", "extracted_metadata"],
                        "complexity": "medium"
                    }
                },
                {
                    "type": "PaymentValidator",
                    "description": "Validate payment transactions, check fraud patterns, and approve or reject payments",
                    "config": {
                        "inputs": ["payment_request", "user_profile", "fraud_rules"],
                        "outputs": ["validation_result", "fraud_score", "approval_decision"],
                        "complexity": "high"
                    }
                }
            ]
            
            generation_results = []
            total_generation_time = 0
            total_generation_cost = 0
            
            for scenario in test_scenarios:
                start_time = time.time()
                
                try:
                    result = await generator.generate_component_implementation(
                        scenario["type"].lower(),  # component_type
                        scenario["type"] + "Component",  # component_name
                        scenario["description"],  # component_description
                        scenario["config"],  # component_config
                        scenario["type"] + "Component"  # class_name
                    )
                    
                    generation_time = time.time() - start_time
                    total_generation_time += generation_time
                    
                    # Validate generated code quality
                    if not result or len(result) < 500:
                        generation_results.append({
                            "component": scenario["type"],
                            "success": False,
                            "message": "Generated code too short",
                            "length": len(result) if result else 0
                        })
                        continue
                    
                    # Use unified validator for consistent validation (P0.6-F2 fix)
                    validator = UnifiedComponentValidator()
                    validation_result = validator.validate_component(result, scenario["type"])
                    
                    # Convert to format expected by existing test logic
                    generation_results.append({
                        "component": scenario["type"],
                        "success": validation_result["success"],
                        "generation_time": generation_time,
                        "code_length": validation_result["code_length"],
                        "lines_of_code": validation_result["lines_of_code"],
                        "syntax_valid": validation_result["syntax_valid"],
                        "contains_async": "async def process_item" in result,  # Use correct method name
                        "contains_logging": "logger" in result.lower(),
                        "contains_error_handling": "try:" in result and "except" in result,
                        "quality_percentage": validation_result["quality_percentage"],
                        "message": validation_result["message"]
                    })
                    
                except Exception as e:
                    generation_results.append({
                        "component": scenario["type"],
                        "success": False,
                        "message": f"Generation failed: {str(e)}",
                        "exception_type": type(e).__name__
                    })
            
            # Evaluate results
            successful_generations = [r for r in generation_results if r.get("success", False)]
            success_rate = len(successful_generations) / len(test_scenarios) if test_scenarios else 0
            
            # Calculate quality metrics
            if successful_generations:
                avg_generation_time = sum(r.get("generation_time", 0) for r in successful_generations) / len(successful_generations)
                avg_code_length = sum(r.get("code_length", 0) for r in successful_generations) / len(successful_generations)
                avg_lines_of_code = sum(r.get("lines_of_code", 0) for r in successful_generations) / len(successful_generations)
            else:
                avg_generation_time = 0
                avg_code_length = 0
                avg_lines_of_code = 0
            
            self.log_result("component_generation_production", success_rate >= 0.8, {
                "message": f"Component generation working with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "total_scenarios": len(test_scenarios),
                "successful_generations": len(successful_generations),
                "total_generation_time": total_generation_time,
                "avg_generation_time": avg_generation_time,
                "avg_code_length": avg_code_length,
                "avg_lines_of_code": avg_lines_of_code,
                "results": generation_results
            })
            
            return success_rate >= 0.8
            
        except Exception as e:
            self.log_result("component_generation_production", False, {
                "message": f"Exception during component generation test: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def test_cost_tracking_production(self) -> bool:
        """Test cost tracking accuracy with production workloads"""
        print("\n🧪 REAL-WORLD TEST: Production Cost Tracking")
        print("=" * 60)
        
        try:
            cost_samples = []
            
            # Test with available providers
            if os.getenv("OPENAI_API_KEY"):
                openai_provider = OpenAIProvider({
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini"
                })
                
                # Test different request sizes
                test_requests = [
                    {"prompt": "Hello", "max_tokens": 10, "expected_range": (0.000001, 0.001)},
                    {"prompt": "Write a short poem about coding", "max_tokens": 100, "expected_range": (0.00001, 0.01)},
                    {"prompt": "Explain machine learning in detail with examples", "max_tokens": 500, "expected_range": (0.0001, 0.1)}
                ]
                
                for i, test_req in enumerate(test_requests):
                    request = LLMRequest(
                        system_prompt="You are a helpful assistant.",
                        user_prompt=test_req["prompt"],
                        max_tokens=test_req["max_tokens"],
                        temperature=0.3
                    )
                    
                    response = await openai_provider.generate(request)
                    
                    cost_sample = {
                        "provider": "openai",
                        "model": response.model,
                        "tokens": response.tokens_used,
                        "cost": response.cost_usd,
                        "cost_per_token": response.cost_usd / response.tokens_used if response.tokens_used > 0 else 0,
                        "prompt_length": len(test_req["prompt"]),
                        "max_tokens": test_req["max_tokens"],
                        "actual_response_length": len(response.content),
                        "response_time": response.response_time,
                        "expected_range": test_req["expected_range"]
                    }
                    
                    # Validate cost is in expected range
                    if not (test_req["expected_range"][0] <= response.cost_usd <= test_req["expected_range"][1]):
                        cost_sample["cost_anomaly"] = True
                    
                    cost_samples.append(cost_sample)
            
            if not cost_samples:
                self.log_result("cost_tracking_production", False, {
                    "message": "No providers available for cost tracking test"
                })
                return False
            
            # Analyze cost tracking quality
            total_cost = sum(s["cost"] for s in cost_samples)
            total_tokens = sum(s["tokens"] for s in cost_samples)
            avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            
            # Check for cost anomalies
            anomalies = [s for s in cost_samples if s.get("cost_anomaly", False)]
            
            # Validate reasonable cost per token ranges
            # Provider-specific cost validation using corrected thresholds
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
            
            reasonable_costs = all(validate_cost_reasonable(s["cost_per_token"], s["provider"], s["model"]) for s in cost_samples if s["cost_per_token"] > 0)
            
            self.log_result("cost_tracking_production", reasonable_costs and len(anomalies) == 0, {
                "message": "Cost tracking working accurately in production",
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "avg_cost_per_token": avg_cost_per_token,
                "cost_samples": len(cost_samples),
                "cost_anomalies": len(anomalies),
                "reasonable_costs": reasonable_costs,
                "cost_details": cost_samples
            })
            
            return reasonable_costs and len(anomalies) == 0
            
        except Exception as e:
            self.log_result("cost_tracking_production", False, {
                "message": f"Exception during cost tracking test: {str(e)}",
                "exception_type": type(e).__name__
            })
            return False
    
    async def run_focused_tests(self) -> bool:
        """Run focused real-world tests"""
        print("🚀 Starting Focused Real-World Integration Testing")
        print("=" * 80)
        
        # Run focused tests
        test_results = []
        
        test_results.append(await self.test_multi_provider_failover_comprehensive())
        test_results.append(await self.test_component_generation_production())
        test_results.append(await self.test_cost_tracking_production())
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 FOCUSED REAL-WORLD TESTING SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Failed Tests: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1%}")
        print(f"Test Duration: {(datetime.now() - self.start_time).total_seconds():.1f} seconds")
        
        # Save results to file
        results_file = "/home/brian/autocoder4_cc/test_focused_real_world_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate,
                    "test_duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                    "focus": "working_components_validation"
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        if success_rate >= 0.8:  # 80% success rate required
            print("✅ FOCUSED REAL-WORLD TESTING PASSED")
            return True
        else:
            print("❌ FOCUSED REAL-WORLD TESTING FAILED")
            return False

async def main():
    """Main test execution"""
    tester = FocusedRealWorldTester()
    success = await tester.run_focused_tests()
    
    if success:
        print("\n🎉 Focused real-world tests completed successfully!")
        print("Multi-provider system is working correctly with available APIs.")
    else:
        print("\n⚠️ Some focused tests failed.")
        print("Review the results and fix issues before production deployment.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())