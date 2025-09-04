#!/usr/bin/env python3
"""
Simple Integration Test to Systematically Find Phase 2A Bugs
============================================================
"""

import subprocess
import tempfile
import time
import os
from pathlib import Path


def test_system_generation():
    """Test if we can generate a complete system"""
    print("🧪 TESTING: System Generation")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run([
            "python", "-m", "autocoder_cc.cli.main", "generate",
            "A simple todo application with API endpoints for CRUD operations",
            "-o", temp_dir
        ], capture_output=True, text=True, cwd="/home/brian/projects/autocoder4_cc")
        
        print(f"Return code: {result.returncode}")
        print(f"STDERR: {result.stderr[-1000:]}")  # Last 1000 chars
        
        if result.returncode != 0:
            print("❌ SYSTEM GENERATION FAILED")
            return None
        
        # Find generated system directory
        system_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "main.py" in files:
                system_dir = root
                break
        
        if system_dir:
            print(f"✅ SYSTEM GENERATION SUCCEEDED: {system_dir}")
            return system_dir
        else:
            print("❌ NO MAIN.PY FOUND")
            return None


def test_import_bug():
    """Test for the known import bug"""
    print("\\n🧪 TESTING: Import Bug Detection")
    print("-" * 40)
    
    # Use our existing generated system
    system_dir = "/home/brian/projects/autocoder4_cc/test_integration_system/scaffolds/todo_app_system"
    
    if not Path(system_dir).exists():
        print("❌ NO EXISTING SYSTEM TO TEST")
        return False
    
    components_dir = Path(system_dir, "components")
    if not components_dir.exists():
        print("❌ NO COMPONENTS DIRECTORY")
        return False
    
    # Check for import bugs
    import_bugs = []
    for py_file in components_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        
        content = py_file.read_text()
        if "from autocoder_cc.components.composed_base import ComposedComponent" in content:
            import_bugs.append(str(py_file))
    
    if import_bugs:
        print(f"✅ IMPORT BUG CONFIRMED in {len(import_bugs)} files:")
        for file in import_bugs:
            print(f"   - {file}")
        return True
    else:
        print("❌ NO IMPORT BUGS FOUND (unexpected)")
        return False


def test_import_fix():
    """Test fixing the import bug"""
    print("\\n🧪 TESTING: Import Bug Fix")
    print("-" * 40)
    
    system_dir = "/home/brian/projects/autocoder4_cc/test_integration_system/scaffolds/todo_app_system"
    components_dir = Path(system_dir, "components")
    
    if not components_dir.exists():
        print("❌ NO COMPONENTS DIRECTORY")
        return False
    
    # Fix the imports
    fixed_files = []
    for py_file in components_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        
        content = py_file.read_text()
        if "from autocoder_cc.components.composed_base import ComposedComponent" in content:
            new_content = content.replace(
                "from autocoder_cc.components.composed_base import ComposedComponent",
                "from .observability import ComposedComponent"
            )
            py_file.write_text(new_content)
            fixed_files.append(str(py_file))
    
    if fixed_files:
        print(f"✅ FIXED IMPORTS in {len(fixed_files)} files:")
        for file in fixed_files:
            print(f"   - {Path(file).name}")
        return True
    else:
        print("❌ NO FILES TO FIX")
        return False


def test_system_startup():
    """Test if the system can start after import fix"""
    print("\\n🧪 TESTING: System Startup")
    print("-" * 40)
    
    system_dir = "/home/brian/projects/autocoder4_cc/test_integration_system/scaffolds/todo_app_system"
    
    if not Path(system_dir, "main.py").exists():
        print("❌ NO MAIN.PY FOUND")
        return False
    
    # Try to start the system with a timeout
    process = subprocess.Popen([
        "python", "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       cwd=system_dir, text=True)
    
    try:
        # Wait a few seconds
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ SYSTEM STARTED SUCCESSFULLY")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            # Process exited, get the error
            stdout, stderr = process.communicate()
            print(f"❌ SYSTEM STARTUP FAILED")
            print(f"STDERR: {stderr[-500:]}")  # Last 500 chars
            return False
            
    except Exception as e:
        print(f"❌ SYSTEM STARTUP ERROR: {e}")
        process.terminate()
        return False


def run_simple_integration_tests():
    """Run all simple integration tests"""
    print("🚀 AUTOCODER4_CC SIMPLE INTEGRATION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test 1: System Generation
    results["generation"] = test_system_generation()
    
    # Test 2: Import Bug Detection
    results["import_bug"] = test_import_bug()
    
    # Test 3: Import Bug Fix
    results["import_fix"] = test_import_fix()
    
    # Test 4: System Startup
    results["startup"] = test_system_startup()
    
    # Summary
    print("\\n" + "=" * 60)
    print("📋 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"✅ PASSED: {passed}/{total} tests")
    print(f"❌ FAILED: {total - passed}/{total} tests")
    
    print("\\n📋 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    return results


if __name__ == "__main__":
    run_simple_integration_tests()