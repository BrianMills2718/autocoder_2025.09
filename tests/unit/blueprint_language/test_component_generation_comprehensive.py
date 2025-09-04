#!/usr/bin/env python3
"""
Comprehensive, portable component generation test suite.
Tests N≥12 components for statistical significance without hardcoded paths.
"""

import sys
import os
from pathlib import Path
import json
import time
import traceback

# Portable path handling
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_component_generation_comprehensive():
    """Test component generation with comprehensive validation."""
    
    # Initialize generator
    try:
        generator = LLMComponentGenerator()
        print("✅ LLMComponentGenerator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LLMComponentGenerator: {e}")
        return False
    
    # Test cases for statistical significance (N=12)
    test_cases = [
        {"type": "Source", "name": "user_generator", "expected": "GeneratedSource_user_generator"},
        {"type": "Source", "name": "order_generator", "expected": "GeneratedSource_order_generator"},
        {"type": "Store", "name": "user_store", "expected": "GeneratedStore_user_store"},
        {"type": "Store", "name": "order_store", "expected": "GeneratedStore_order_store"},
        {"type": "Store", "name": "product_store", "expected": "GeneratedStore_product_store"},
        {"type": "Sink", "name": "user_sink", "expected": "GeneratedSink_user_sink"},
        {"type": "Sink", "name": "order_sink", "expected": "GeneratedSink_order_sink"},
        {"type": "APIEndpoint", "name": "user_api", "expected": "GeneratedAPIEndpoint_user_api"},
        {"type": "APIEndpoint", "name": "order_api", "expected": "GeneratedAPIEndpoint_order_api"},
        {"type": "Transformer", "name": "user_processor", "expected": "GeneratedTransformer_user_processor"},
        {"type": "Transformer", "name": "order_processor", "expected": "GeneratedTransformer_order_processor"},
        {"type": "Controller", "name": "user_controller", "expected": "GeneratedController_user_controller"},
    ]
    
    results = []
    
    print(f"🧪 Testing {len(test_cases)} components for statistical significance...")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['type']} {test_case['name']}")
        
        try:
            start_time = time.time()
            
            # Generate component using the generator's own methods
            generated_code = generator.generate_component_implementation(
                test_case["type"],
                test_case["name"],
                f"A {test_case['type']} component for {test_case['name']}",
                {},
                test_case["expected"]
            )
            
            generation_time = time.time() - start_time
            
            # Validate using generator's own validation methods
            validation_start = time.time()
            
            # Use the generator's internal validation
            generator._validate_generated_code(generated_code, test_case["type"], test_case["expected"])
            
            validation_time = time.time() - validation_start
            
            # Check for correct class name
            if test_case["expected"] in generated_code:
                results.append({
                    "test": test_case,
                    "success": True,
                    "code_length": len(generated_code),
                    "generation_time": generation_time,
                    "validation_time": validation_time,
                    "lines_generated": len(generated_code.split('\n'))
                })
                print(f"   ✅ Success - {len(generated_code)} chars, {generation_time:.2f}s generation, {validation_time:.2f}s validation")
            else:
                results.append({
                    "test": test_case,
                    "success": False,
                    "error": f"Expected class name '{test_case['expected']}' not found in generated code",
                    "code_preview": generated_code[:200] + "..." if len(generated_code) > 200 else generated_code,
                    "generation_time": generation_time
                })
                print(f"   ❌ Failed - Expected class name not found")
                
        except Exception as e:
            results.append({
                "test": test_case,
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "generation_time": time.time() - start_time if 'start_time' in locals() else 0
            })
            print(f"   ❌ Exception: {e}")
    
    # Calculate honest statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = (successful_tests / total_tests) * 100
    
    print()
    print("=" * 60)
    print("COMPONENT GENERATION TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Failures: {total_tests - successful_tests}")
    print()
    
    # Calculate performance metrics
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        avg_generation_time = sum(r["generation_time"] for r in successful_results) / len(successful_results)
        avg_validation_time = sum(r.get("validation_time", 0) for r in successful_results) / len(successful_results)
        avg_code_length = sum(r["code_length"] for r in successful_results) / len(successful_results)
        avg_lines = sum(r["lines_generated"] for r in successful_results) / len(successful_results)
        
        print("PERFORMANCE METRICS (Successful Tests Only):")
        print(f"Average Generation Time: {avg_generation_time:.2f}s")
        print(f"Average Validation Time: {avg_validation_time:.2f}s")
        print(f"Average Code Length: {avg_code_length:.0f} characters")
        print(f"Average Lines Generated: {avg_lines:.0f} lines")
        print()
    
    # Component type breakdown
    print("RESULTS BY COMPONENT TYPE:")
    component_types = {}
    for result in results:
        comp_type = result["test"]["type"]
        if comp_type not in component_types:
            component_types[comp_type] = {"total": 0, "successful": 0}
        component_types[comp_type]["total"] += 1
        if result["success"]:
            component_types[comp_type]["successful"] += 1
    
    for comp_type, stats in component_types.items():
        success_rate = (stats["successful"] / stats["total"]) * 100
        print(f"  {comp_type}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
    
    print()
    
    # Document failures honestly
    failures = [r for r in results if not r["success"]]
    if failures:
        print("FAILURE ANALYSIS:")
        for i, failure in enumerate(failures, 1):
            print(f"  {i}. {failure['test']['type']} {failure['test']['name']}")
            print(f"     Error: {failure['error']}")
            if 'traceback' in failure:
                print(f"     Traceback: {failure['traceback'][:200]}...")
            print()
    
    # Critical thresholds
    print("CRITICAL ASSESSMENT:")
    if success_rate >= 90:
        print("✅ EXCELLENT: Success rate >= 90%")
    elif success_rate >= 75:
        print("⚠️  GOOD: Success rate >= 75%")
    elif success_rate >= 50:
        print("⚠️  NEEDS IMPROVEMENT: Success rate >= 50%")
    else:
        print("❌ CRITICAL: Success rate < 50%")
    
    # Store/Sink specific analysis
    store_tests = [r for r in results if r["test"]["type"] == "Store"]
    sink_tests = [r for r in results if r["test"]["type"] == "Sink"]
    
    print()
    print("STORE/SINK CONFUSION ANALYSIS:")
    store_success = sum(1 for r in store_tests if r["success"])
    sink_success = sum(1 for r in sink_tests if r["success"])
    
    print(f"Store Components: {store_success}/{len(store_tests)} successful")
    print(f"Sink Components: {sink_success}/{len(sink_tests)} successful")
    
    # Check for Store/Sink confusion in failures
    confusion_detected = False
    for failure in failures:
        if failure["test"]["type"] == "Store" and "GeneratedSink_" in failure.get("code_preview", ""):
            print(f"❌ Store/Sink confusion detected in {failure['test']['name']}")
            confusion_detected = True
        elif failure["test"]["type"] == "Sink" and "GeneratedStore_" in failure.get("code_preview", ""):
            print(f"❌ Sink/Store confusion detected in {failure['test']['name']}")
            confusion_detected = True
    
    if not confusion_detected:
        print("✅ No Store/Sink confusion detected")
    
    # Save detailed results for evidence
    results_file = Path("component_generation_test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "test_timestamp": time.time(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "component_type_breakdown": component_types,
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n📊 Detailed results saved to: {results_file}")
    
    return success_rate >= 75  # Return True if success rate is acceptable

if __name__ == "__main__":
    success = test_component_generation_comprehensive()
    sys.exit(0 if success else 1)