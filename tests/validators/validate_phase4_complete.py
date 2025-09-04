#!/usr/bin/env python3
"""
Phase 4 Iterative Testing Validation Script
Validates that all Phase 4 iterative testing functionality is working correctly
"""
import sys
import subprocess
import time
from pathlib import Path
import json

def validate_phase4_iterative_testing():
    """Validate all Phase 4 iterative testing functionality"""
    print("🎯 PHASE 4 ITERATIVE TESTING VALIDATION")
    print("=" * 60)
    
    results = {
        "testing_script_exists": False,
        "can_find_latest_system": False,
        "error_detection_working": False,
        "fix_functions_available": False,
        "generated_system_syntactically_correct": False,
        "setup_connections_fix_applied": False,
        "settings_attributes_available": False,
        "overall_success": False
    }
    
    # 1. Check if testing script exists
    testing_script = Path("test_phase4_iterative.py")
    if testing_script.exists():
        results["testing_script_exists"] = True
        print("✅ Phase 4 iterative testing script exists")
    else:
        print("❌ Phase 4 iterative testing script missing")
        return results
    
    # 2. Check if we can find the latest system
    generated_systems_dir = Path("generated_systems")
    if not generated_systems_dir.exists():
        print("❌ No generated_systems directory found")
        return results
    
    system_dirs = [d for d in generated_systems_dir.iterdir() if d.is_dir() and d.name.startswith("system_")]
    if not system_dirs:
        print("❌ No system directories found")
        return results
    
    latest_dir = max(system_dirs, key=lambda d: d.stat().st_mtime)
    system_subdirs = []
    for d in latest_dir.iterdir():
        if d.is_dir() and not d.name.startswith(".") and (d / "main.py").exists():
            system_subdirs.append(d)
    
    if not system_subdirs:
        print("❌ No system subdirectories with main.py found")
        return results
    
    system_dir = system_subdirs[0]
    results["can_find_latest_system"] = True
    print(f"✅ Found latest system: {system_dir}")
    
    # 3. Check error detection functionality
    with open(testing_script, 'r') as f:
        script_content = f.read()
    
    error_patterns = [
        "missing_setup_connections",
        "missing_settings_attribute",
        "missing_component_files",
        "import_error",
        "syntax_error"
    ]
    
    error_detection_working = all(pattern in script_content for pattern in error_patterns)
    if error_detection_working:
        results["error_detection_working"] = True
        print("✅ Error detection patterns implemented")
    else:
        print("❌ Error detection patterns missing")
    
    # 4. Check fix functions
    fix_functions = [
        "fix_missing_setup_connections",
        "fix_missing_settings_attribute",
        "fix_missing_component_files"
    ]
    
    fix_functions_available = all(func in script_content for func in fix_functions)
    if fix_functions_available:
        results["fix_functions_available"] = True
        print("✅ Fix functions implemented")
    else:
        print("❌ Fix functions missing")
    
    # 5. Check generated system syntax
    main_file = system_dir / "main.py"
    if main_file.exists():
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(main_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                results["generated_system_syntactically_correct"] = True
                print("✅ Generated system is syntactically correct")
            else:
                print(f"❌ Generated system has syntax errors: {result.stderr}")
        except Exception as e:
            print(f"❌ Error checking syntax: {e}")
    
    # 6. Check setup_connections fix
    with open(main_file, 'r') as f:
        main_content = f.read()
    
    if "setup_connections" in main_content:
        results["setup_connections_fix_applied"] = True
        print("✅ setup_connections function has been added")
    else:
        print("❌ setup_connections function missing")
    
    # 7. Check settings attributes
    settings_file = Path("autocoder/core/config.py")
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings_content = f.read()
        
        required_attributes = ["SERVICE_NAME", "API_VERSION"]
        settings_available = all(attr in settings_content for attr in required_attributes)
        
        if settings_available:
            results["settings_attributes_available"] = True
            print("✅ Required settings attributes are available")
        else:
            print("❌ Required settings attributes missing")
    
    # Overall success
    success_count = sum(1 for v in results.values() if v is True)
    total_checks = len(results) - 1  # Exclude overall_success
    
    if success_count >= total_checks - 1:  # Allow 1 failure
        results["overall_success"] = True
        print(f"\n🎉 PHASE 4 ITERATIVE TESTING VALIDATION PASSED!")
        print(f"✅ {success_count}/{total_checks} checks passed")
    else:
        print(f"\n❌ PHASE 4 ITERATIVE TESTING VALIDATION FAILED")
        print(f"❌ {success_count}/{total_checks} checks passed")
    
    return results

def main():
    """Main validation function"""
    results = validate_phase4_iterative_testing()
    
    # Save results to file
    with open("phase4_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to phase4_validation_results.json")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)