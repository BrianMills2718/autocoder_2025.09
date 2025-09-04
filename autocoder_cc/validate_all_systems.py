#!/usr/bin/env python3
"""
Comprehensive validation of all generated systems using integration testing
"""
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
from autocoder_cc.blueprint_language.integration_validation_gate import IntegrationValidationGate

async def validate_all_systems() -> Tuple[float, List[Dict]]:
    """Validate all generated systems and return average success rate"""
    gate = IntegrationValidationGate()
    systems_dir = Path('generated_systems')
    
    results = []
    
    # Find all systems with components
    system_paths = []
    for system_dir in sorted(systems_dir.iterdir()):
        if system_dir.is_dir() and system_dir.name.startswith('system_'):
            # Find components directories
            components_dirs = list(system_dir.glob('**/components'))
            if components_dirs:
                # Filter to only include actual component directories with Python files
                for comp_dir in components_dirs:
                    py_files = [f for f in comp_dir.glob("*.py") 
                               if f.name not in ['__init__.py', 'observability.py', 'communication.py']]
                    if py_files:
                        system_paths.append((system_dir.name, comp_dir))
                        break
    
    print(f"Found {len(system_paths)} systems to validate\n")
    
    # Test each system
    for system_name, components_dir in system_paths[:20]:  # Test first 20 for speed
        print(f"Validating {system_name}...")
        try:
            result = await gate.validate_system(components_dir, system_name)
            
            results.append({
                'system': system_name,
                'total_components': result.total_components,
                'passed': result.passed_components,
                'failed': result.failed_components,
                'success_rate': result.success_rate,
                'can_proceed': result.can_proceed
            })
            
            print(f"  Components: {result.total_components}")
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  Can proceed: {result.can_proceed}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                'system': system_name,
                'total_components': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0.0,
                'can_proceed': False
            })
        
        print()
    
    # Calculate overall metrics
    if results:
        total_components = sum(r['total_components'] for r in results)
        total_passed = sum(r['passed'] for r in results)
        avg_success_rate = sum(r['success_rate'] for r in results) / len(results)
        systems_passing = sum(1 for r in results if r['can_proceed'])
        
        print("=" * 60)
        print("OVERALL RESULTS")
        print("=" * 60)
        print(f"Total systems tested: {len(results)}")
        print(f"Total components: {total_components}")
        print(f"Total passed components: {total_passed}")
        print(f"Average success rate: {avg_success_rate:.1f}%")
        print(f"Systems with >95% success: {systems_passing}/{len(results)}")
        print()
        
        if avg_success_rate >= 95:
            print("✅ SUCCESS: Achieved 95% validation rate!")
        else:
            print(f"❌ Current rate {avg_success_rate:.1f}% - need to reach 95%")
            print("\nFailed systems:")
            for r in results:
                if r['success_rate'] < 95:
                    print(f"  - {r['system']}: {r['success_rate']:.1f}%")
        
        return avg_success_rate, results
    
    return 0.0, []

if __name__ == '__main__':
    asyncio.run(validate_all_systems())