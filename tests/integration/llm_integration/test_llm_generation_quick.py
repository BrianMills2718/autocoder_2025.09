#!/usr/bin/env python3
"""
Quick LLM Generation Test
Tests a smaller sample to assess effectiveness quickly
"""

import asyncio
import re
import traceback
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator


async def test_llm_generation_quick():
    """Quick test of LLM generation effectiveness"""
    
    generator = LLMComponentGenerator()
    
    # Define 5 simple test cases
    test_cases = [
        {
            'component_type': 'api_endpoint',
            'component_name': 'simple_endpoint',
            'component_description': 'Simple API endpoint that returns status',
            'component_config': {'name': 'simple_endpoint'},
            'class_name': 'SimpleEndpoint'
        },
        {
            'component_type': 'store',
            'component_name': 'basic_store',
            'component_description': 'Basic store for data persistence',
            'component_config': {'name': 'basic_store'},
            'class_name': 'BasicStore'
        },
        {
            'component_type': 'transformer',
            'component_name': 'data_transformer',
            'component_description': 'Transform data between formats',
            'component_config': {'name': 'data_transformer'},
            'class_name': 'DataTransformer'
        },
        {
            'component_type': 'sink',
            'component_name': 'log_sink',
            'component_description': 'Write data to log files',
            'component_config': {'name': 'log_sink'},
            'class_name': 'LogSink'
        },
        {
            'component_type': 'source',
            'component_name': 'file_source',
            'component_description': 'Read data from files',
            'component_config': {'name': 'file_source'},
            'class_name': 'FileSource'
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    results = []
    
    for test_case in test_cases:
        try:
            test_name = test_case['component_type']
            print(f"Testing {test_name}...")
            
            # Generate component implementation
            result = await generator.generate_component_implementation(
                component_type=test_case['component_type'],
                component_name=test_case['component_name'],
                component_description=test_case['component_description'],
                component_config=test_case['component_config'],
                class_name=test_case['class_name']
            )
            
            # Check for forbidden patterns
            forbidden_patterns = [
                r'return\s*\{\s*["\']value["\']\s*:\s*42\s*\}',
                r'TODO:|FIXME:',
                r'NotImplementedError',
                r'^\s*pass\s*$',
                r'raise\s+NotImplementedError'
            ]
            
            has_forbidden = any(re.search(pattern, result, re.MULTILINE) for pattern in forbidden_patterns)
            is_substantial = len(result.strip()) > 100
            has_class_definition = f"class {test_case['class_name']}" in result
            
            if not has_forbidden and is_substantial and has_class_definition:
                success_count += 1
                status = '✅'
                print(f'✅ {test_name}: Generated {len(result)} chars')
            else:
                status = '❌'
                issues = []
                if has_forbidden:
                    issues.append("forbidden_patterns")
                if not is_substantial:
                    issues.append("too_short")
                if not has_class_definition:
                    issues.append("no_class")
                print(f'❌ {test_name}: Issues: {", ".join(issues)}')
            
            results.append({
                'test_name': test_name,
                'status': status,
                'success': status == '✅',
                'code_length': len(result)
            })
            
        except Exception as e:
            print(f'❌ {test_name}: Generation failed - {e}')
            results.append({
                'test_name': test_name,
                'status': '❌',
                'success': False,
                'error': str(e)
            })
    
    # Calculate results
    success_rate = success_count / total_count
    print(f'\n=== QUICK TEST RESULTS ===')
    print(f'Success Rate: {success_rate:.1%} ({success_count}/{total_count})')
    
    for result in results:
        print(f'{result["status"]} {result["test_name"]}: {result.get("code_length", "N/A")} chars')
    
    # Assessment
    if success_rate >= 0.8:  # 80% threshold for quick test
        print(f'\n✅ LLM Generation Shows Good Quality: {success_rate:.1%}')
        return True
    else:
        print(f'\n❌ LLM Generation Quality Issues: {success_rate:.1%}')
        return False


if __name__ == "__main__":
    result = asyncio.run(test_llm_generation_quick())
    exit(0 if result else 1)