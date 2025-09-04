#!/usr/bin/env python3
"""
Comprehensive LLM Generation Testing
Tests the actual effectiveness of LLM generation with specific success criteria
"""

import asyncio
import re
import traceback
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator


async def test_llm_generation_effectiveness():
    """Test LLM generation with comprehensive validation"""
    
    generator = LLMComponentGenerator()
    
    # Define test cases with different component types
    test_cases = [
        {
            'component_type': 'api_endpoint',
            'component_name': 'user_registration_endpoint',
            'component_description': 'API endpoint for user registration with validation',
            'component_config': {'name': 'user_registration_endpoint', 'port': 8080},
            'class_name': 'UserRegistrationEndpoint'
        },
        {
            'component_type': 'store',
            'component_name': 'user_data_store',
            'component_description': 'Store component for persistent user data storage',
            'component_config': {'name': 'user_data_store', 'database_type': 'postgresql'},
            'class_name': 'UserDataStore'
        },
        {
            'component_type': 'transformer',
            'component_name': 'data_enricher',
            'component_description': 'Transform and enrich incoming data streams',
            'component_config': {'name': 'data_enricher', 'enrichment_rules': []},
            'class_name': 'DataEnricher'
        },
        {
            'component_type': 'sink',
            'component_name': 'audit_log_sink',
            'component_description': 'Sink component that writes audit logs to external system',
            'component_config': {'name': 'audit_log_sink', 'destination': 'file'},
            'class_name': 'AuditLogSink'
        },
        {
            'component_type': 'source',
            'component_name': 'event_stream_source',
            'component_description': 'Source component that reads from event stream',
            'component_config': {'name': 'event_stream_source', 'stream_type': 'kafka'},
            'class_name': 'EventStreamSource'
        }
    ]
    
    success_count = 0
    total_count = len(test_cases) * 4  # Test each type 4 times
    results = []
    
    for test_case in test_cases:
        for i in range(4):  # Test each component type 4 times
            try:
                test_name = f"{test_case['component_type']}_{i}"
                print(f"Testing {test_name}...")
                
                # Generate component implementation
                result = await generator.generate_component_implementation(
                    component_type=test_case['component_type'],
                    component_name=f"{test_case['component_name']}_{i}",
                    component_description=test_case['component_description'],
                    component_config=test_case['component_config'],
                    class_name=f"{test_case['class_name']}{i}"
                )
                
                # Check for forbidden patterns with regex
                forbidden_patterns = [
                    r'return\s*\{\s*["\']value["\']\s*:\s*42\s*\}',  # return {"value": 42}
                    r'TODO:|FIXME:',  # TODO or FIXME comments
                    r'NotImplementedError',  # NotImplementedError
                    r'^\s*pass\s*$',  # standalone pass statements
                    r'raise\s+NotImplementedError',  # raise NotImplementedError
                    r'def\s+\w+\([^)]*\):\s*pass\s*$',  # empty method definitions
                ]
                
                has_forbidden = any(re.search(pattern, result, re.MULTILINE) for pattern in forbidden_patterns)
                is_substantial = len(result.strip()) > 100  # Ensure substantial implementation
                has_class_definition = f"class {test_case['class_name']}{i}" in result
                has_imports = any(keyword in result for keyword in ['import', 'from'])
                has_methods = 'def ' in result
                
                success_criteria = [
                    not has_forbidden,
                    is_substantial,
                    has_class_definition,
                    has_imports,
                    has_methods
                ]
                
                if all(success_criteria):
                    success_count += 1
                    status = '✅'
                    print(f'✅ {test_name}: Functional implementation generated')
                else:
                    status = '❌'
                    failed_criteria = []
                    if has_forbidden:
                        failed_criteria.append("contains_forbidden_patterns")
                    if not is_substantial:
                        failed_criteria.append("too_short")
                    if not has_class_definition:
                        failed_criteria.append("no_class_definition")
                    if not has_imports:
                        failed_criteria.append("no_imports")
                    if not has_methods:
                        failed_criteria.append("no_methods")
                    
                    print(f'❌ {test_name}: Failed criteria: {", ".join(failed_criteria)}')
                
                results.append({
                    'test_name': test_name,
                    'status': status,
                    'success': all(success_criteria),
                    'code_length': len(result),
                    'has_forbidden': has_forbidden,
                    'has_class_definition': has_class_definition
                })
                
            except Exception as e:
                print(f'❌ {test_name}: Generation failed - {e}')
                print(f'   Error details: {traceback.format_exc()}')
                results.append({
                    'test_name': test_name,
                    'status': '❌',
                    'success': False,
                    'error': str(e)
                })
    
    # Calculate and report results
    success_rate = success_count / total_count
    print(f'\n=== FINAL RESULTS ===')
    print(f'Success Rate: {success_rate:.1%} ({success_count}/{total_count})')
    
    # Detailed breakdown
    by_component_type = {}
    for result in results:
        component_type = result['test_name'].split('_')[0]
        if component_type not in by_component_type:
            by_component_type[component_type] = {'success': 0, 'total': 0}
        by_component_type[component_type]['total'] += 1
        if result['success']:
            by_component_type[component_type]['success'] += 1
    
    print(f'\n=== BREAKDOWN BY COMPONENT TYPE ===')
    for component_type, stats in by_component_type.items():
        rate = stats['success'] / stats['total']
        print(f'{component_type}: {rate:.1%} ({stats["success"]}/{stats["total"]})')
    
    # Final assessment
    if success_rate >= 0.9:
        print(f'\n✅ LLM Generation Quality Meets 90% Threshold: {success_rate:.1%}')
        return True
    else:
        print(f'\n❌ LLM Generation Quality Below Threshold: {success_rate:.1%}')
        return False


if __name__ == "__main__":
    result = asyncio.run(test_llm_generation_effectiveness())
    exit(0 if result else 1)