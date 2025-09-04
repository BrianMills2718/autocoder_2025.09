#!/usr/bin/env python3
"""Robust, portable component generation test suite."""

import sys
import os
from pathlib import Path
import time
import traceback

# Portable path handling
project_root = Path(__file__).parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_component_generation_comprehensive():
    """Test component generation with comprehensive validation."""
    generator = LLMComponentGenerator()
    
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
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Test {i}/12: {test_case['type']} - {test_case['name']} ===")
        
        try:
            start_time = time.time()
            
            # Use generator's own validation methods
            generated_code = generator.generate_component_implementation(
                test_case["type"],
                test_case["name"],
                f"A {test_case['type']} component for {test_case['name']}",
                {},
                test_case["expected"]
            )
            
            generation_time = time.time() - start_time
            
            # Validate using generator's methods
            is_valid = generator.validate_no_placeholders(generated_code)
            
            if is_valid and test_case["expected"] in generated_code:
                print(f"✅ SUCCESS: {test_case['type']} {test_case['name']} generated successfully")
                results.append({
                    "test": test_case,
                    "success": True,
                    "code_length": len(generated_code),
                    "generation_time": generation_time,
                    "validation_message": "All validations passed"
                })
            else:
                print(f"❌ FAILED: {test_case['type']} {test_case['name']} - validation failed")
                results.append({
                    "test": test_case,
                    "success": False,
                    "error": "Validation failed or class name mismatch",
                    "code_preview": generated_code[:200] + "..." if len(generated_code) > 200 else generated_code,
                    "generation_time": generation_time
                })
                
        except Exception as e:
            print(f"❌ ERROR: {test_case['type']} {test_case['name']} - {str(e)}")
            results.append({
                "test": test_case,
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "generation_time": 0
            })
    
    # Calculate honest statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"\n" + "="*50)
    print(f"COMPONENT GENERATION TEST RESULTS")
    print(f"="*50)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Failures: {total_tests - successful_tests}")
    
    # Document failures honestly
    failures = [r for r in results if not r["success"]]
    if failures:
        print(f"\n=== DETAILED FAILURE ANALYSIS ===")
        for i, failure in enumerate(failures, 1):
            print(f"\nFailure {i}: {failure['test']['type']} {failure['test']['name']}")
            print(f"Error: {failure['error']}")
            if 'code_preview' in failure:
                print(f"Code preview: {failure['code_preview']}")
    
    # Calculate statistics by component type
    type_stats = {}
    for result in results:
        comp_type = result["test"]["type"]
        if comp_type not in type_stats:
            type_stats[comp_type] = {"total": 0, "successful": 0}
        type_stats[comp_type]["total"] += 1
        if result["success"]:
            type_stats[comp_type]["successful"] += 1
    
    print(f"\n=== SUCCESS RATE BY COMPONENT TYPE ===")
    for comp_type, stats in type_stats.items():
        success_rate = (stats["successful"] / stats["total"]) * 100
        print(f"{comp_type}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
    
    return results

def test_store_sink_confusion():
    """Specific test for Store/Sink confusion issue."""
    print(f"\n=== STORE/SINK CONFUSION TEST ===")
    
    generator = LLMComponentGenerator()
    
    # Test Store component generation
    print("Testing Store component generation...")
    try:
        store_code = generator.generate_component_implementation(
            "Store", 
            "todo_store", 
            "A Store component for todo items",
            {},
            "GeneratedStore_todo_store"
        )
        
        if "GeneratedStore_todo_store" in store_code:
            print("✅ Store component generated with correct class name")
            if "GeneratedSink_" in store_code:
                print("❌ WARNING: Store component contains Sink references")
            else:
                print("✅ Store component contains no Sink references")
        else:
            print("❌ Store component generated with incorrect class name")
            if "GeneratedSink_todo_store" in store_code:
                print("❌ CRITICAL: Store component generated as Sink!")
        
    except Exception as e:
        print(f"❌ Store component generation failed: {e}")
    
    # Test Sink component generation
    print("\nTesting Sink component generation...")
    try:
        sink_code = generator.generate_component_implementation(
            "Sink",
            "todo_sink",
            "A Sink component for todo items",
            {},
            "GeneratedSink_todo_sink"
        )
        
        if "GeneratedSink_todo_sink" in sink_code:
            print("✅ Sink component generated with correct class name")
            if "GeneratedStore_" in sink_code:
                print("❌ WARNING: Sink component contains Store references")
            else:
                print("✅ Sink component contains no Store references")
        else:
            print("❌ Sink component generated with incorrect class name")
            if "GeneratedStore_todo_sink" in sink_code:
                print("❌ CRITICAL: Sink component generated as Store!")
        
    except Exception as e:
        print(f"❌ Sink component generation failed: {e}")

def test_validation_robustness():
    """Test validation system robustness."""
    print(f"\n=== VALIDATION ROBUSTNESS TEST ===")
    
    generator = LLMComponentGenerator()
    
    # Test with code that should fail validation
    failing_code = '''
from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any, Optional

class GeneratedSource_test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # TODO: Implement initialization
    
    async def process_item(self, item: Any = None) -> Any:
        raise NotImplementedError("This method needs implementation")
        pass  # Placeholder
    '''
    
    try:
        generator.validate_no_placeholders(failing_code)
        print("❌ Validation should have failed but passed")
    except ValueError as e:
        print(f"✅ Validation correctly failed: {e}")
    except Exception as e:
        print(f"❌ Validation failed with unexpected error: {e}")

if __name__ == "__main__":
    print("Starting Robust Component Generation Test Suite...")
    print("="*50)
    
    # Run comprehensive test
    results = test_component_generation_comprehensive()
    
    # Run specific tests
    test_store_sink_confusion()
    test_validation_robustness()
    
    # Calculate overall success
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"\n" + "="*50)
    print(f"FINAL RESULTS")
    print(f"="*50)
    print(f"Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate < 80:
        print("⚠️  SUCCESS RATE BELOW 80% - SYSTEM NEEDS IMPROVEMENT")
    elif success_rate < 90:
        print("⚠️  SUCCESS RATE BELOW 90% - MINOR IMPROVEMENTS NEEDED")
    else:
        print("✅ SUCCESS RATE ABOVE 90% - SYSTEM PERFORMING WELL")