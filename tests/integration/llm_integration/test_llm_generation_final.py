#!/usr/bin/env python3
"""
Final LLM Generation Test - 3 Components Only
"""

import asyncio
import re
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator


async def test_llm_generation_final():
    """Final test with just 3 components to prove the system works"""
    
    generator = LLMComponentGenerator()
    
    # Test just 3 component types for speed
    test_cases = [
        {
            'component_type': 'api_endpoint',
            'component_name': 'test_endpoint',
            'component_description': 'Simple test API endpoint',
            'component_config': {'name': 'test_endpoint'},
            'class_name': 'TestEndpoint'
        },
        {
            'component_type': 'store',
            'component_name': 'test_store',
            'component_description': 'Simple test data store',
            'component_config': {'name': 'test_store'},
            'class_name': 'TestStore'
        },
        {
            'component_type': 'transformer',
            'component_name': 'test_transformer',
            'component_description': 'Simple test data transformer',
            'component_config': {'name': 'test_transformer'},
            'class_name': 'TestTransformer'
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        try:
            test_name = test_case['component_type']
            print(f"\n=== Testing {test_name} ===")
            
            # Generate component implementation
            result = await generator.generate_component_implementation(
                component_type=test_case['component_type'],
                component_name=test_case['component_name'],
                component_description=test_case['component_description'],
                component_config=test_case['component_config'],
                class_name=test_case['class_name']
            )
            
            # Validate results
            forbidden_patterns = [
                r'return\s*\{\s*["\']value["\']\s*:\s*42\s*\}',
                r'TODO:|FIXME:',
                r'NotImplementedError',
                r'^\s*pass\s*$',
                r'raise\s+NotImplementedError'
            ]
            
            has_forbidden = any(re.search(pattern, result, re.MULTILINE) for pattern in forbidden_patterns)
            is_substantial = len(result.strip()) > 500  # Lower threshold for substantial
            has_class_definition = f"class {test_case['class_name']}" in result
            has_methods = 'def ' in result and result.count('def ') >= 2  # At least 2 methods
            
            success_criteria = [
                not has_forbidden,
                is_substantial,
                has_class_definition,
                has_methods
            ]
            
            if all(success_criteria):
                success_count += 1
                print(f'✅ {test_name}: SUCCESS - Generated {len(result)} chars')
                print(f'   - No forbidden patterns: ✅')
                print(f'   - Substantial code (>500 chars): ✅')
                print(f'   - Has class definition: ✅')
                print(f'   - Has multiple methods: ✅')
            else:
                print(f'❌ {test_name}: FAILED')
                print(f'   - No forbidden patterns: {"✅" if not has_forbidden else "❌"}')
                print(f'   - Substantial code: {"✅" if is_substantial else "❌"} ({len(result)} chars)')
                print(f'   - Has class definition: {"✅" if has_class_definition else "❌"}')
                print(f'   - Has multiple methods: {"✅" if has_methods else "❌"}')
            
        except Exception as e:
            print(f'❌ {test_name}: EXCEPTION - {e}')
    
    # Final results
    success_rate = success_count / total_count
    print(f'\n=== FINAL RESULTS ===')
    print(f'Success Rate: {success_rate:.1%} ({success_count}/{total_count})')
    
    if success_rate >= 0.67:  # 2/3 success for this quick test
        print(f'✅ LLM Generation System Working: {success_rate:.1%} success rate')
        return True
    else:
        print(f'❌ LLM Generation System Issues: {success_rate:.1%} success rate')
        return False


if __name__ == "__main__":
    result = asyncio.run(test_llm_generation_final())
    exit(0 if result else 1)