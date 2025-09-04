#!/usr/bin/env python3
"""Comprehensive validation script for system generation"""

import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from autocoder_cc.tests.tools.component_test_runner import ComponentTestRunner, ComponentTestConfig
from autocoder_cc.tests.tools.component_analyzer import ComponentAnalyzer


async def test_component(runner: ComponentTestRunner, component_path: Path) -> Tuple[str, bool, str]:
    """Test a single component"""
    analyzer = ComponentAnalyzer()
    
    # Detect the actual class name
    class_name = analyzer.detect_component_class(component_path)
    if not class_name:
        # Try to guess from filename
        if 'store' in component_path.name:
            class_name = f"GeneratedStore_{component_path.stem}"
        elif 'controller' in component_path.name:
            class_name = f"GeneratedController_{component_path.stem}"
        elif 'api_endpoint' in component_path.name:
            class_name = f"GeneratedAPIEndpoint_{component_path.stem}"
        else:
            return component_path.name, False, "Could not detect class name"
    
    config = ComponentTestConfig(
        component_path=component_path,
        component_class_name=class_name
    )
    
    try:
        result = await runner.run_component_tests(config)
        details = f"{len([e for e in result.functional_errors if 'passed' in str(e)])}/3 tests passed"
        return component_path.name, result.functional_test_passed, details
    except Exception as e:
        return component_path.name, False, f"Error: {str(e)}"


async def validate_generation(generation_dir: Path) -> bool:
    """Validate all components in a generation"""
    runner = ComponentTestRunner()
    
    # Find all component files
    component_files = []
    for pattern in ['*_store.py', '*_controller.py', '*_api_endpoint.py']:
        component_files.extend(generation_dir.glob(f'**/components/{pattern}'))
    
    if not component_files:
        print(f"❌ No components found in {generation_dir}")
        return False
    
    print(f"Found {len(component_files)} components to test")
    
    # Test all components
    results = []
    for comp_file in component_files:
        if comp_file.name in ['communication.py', 'observability.py']:
            continue  # Skip non-component files
        
        name, passed, details = await test_component(runner, comp_file)
        results.append((name, passed, details))
        
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {details}")
    
    # Calculate success
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n=== Summary ===")
    print(f"Total components: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {success_rate:.1f}%")
    
    # Success if at least 2/3 of components pass
    return passed >= (total * 2 / 3)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        generation_dir = Path(sys.argv[1])
    else:
        # Find the latest generation
        import glob
        from datetime import datetime
        
        today = datetime.now().strftime("%Y%m%d")
        patterns = glob.glob(f"generated_systems/system_{today}_*")
        if not patterns:
            print("❌ No generations found for today")
            sys.exit(1)
        
        generation_dir = Path(sorted(patterns)[-1])
    
    print(f"Validating generation: {generation_dir}")
    
    success = asyncio.run(validate_generation(generation_dir))
    
    if success:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()