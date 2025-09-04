#!/usr/bin/env python3
"""
Test different import fix approaches for Bug #2
"""

import subprocess
import time
from pathlib import Path


def test_absolute_import_fix():
    """Test fixing the relative import by using absolute imports"""
    print("🧪 TESTING: Absolute Import Fix")
    print("-" * 40)
    
    system_dir = "/home/brian/projects/autocoder4_cc/test_integration_system/scaffolds/todo_app_system"
    components_dir = Path(system_dir, "components")
    
    if not components_dir.exists():
        print("❌ NO COMPONENTS DIRECTORY")
        return False
    
    # Try absolute imports (without the dot)
    fixed_files = []
    for py_file in components_dir.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name in ["observability.py", "communication.py"]:
            continue
        
        content = py_file.read_text()
        if "from .observability import ComposedComponent" in content:
            # Try absolute import approach
            new_content = content.replace(
                "from .observability import ComposedComponent",
                "from observability import ComposedComponent"
            )
            py_file.write_text(new_content)
            fixed_files.append(str(py_file))
    
    if not fixed_files:
        print("❌ NO FILES TO FIX")
        return False
    
    print(f"✅ APPLIED ABSOLUTE IMPORTS to {len(fixed_files)} files")
    
    # Test if the system can start now
    process = subprocess.Popen([
        "python", "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       cwd=system_dir, text=True)
    
    try:
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ ABSOLUTE IMPORT FIX WORKS - System started")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ ABSOLUTE IMPORT FIX FAILED")
            print(f"STDERR (last 500 chars): {stderr[-500:]}")
            return False
            
    except Exception as e:
        print(f"❌ ABSOLUTE IMPORT TEST ERROR: {e}")
        process.terminate()
        return False


def test_sys_path_fix():
    """Test fixing imports by modifying the main.py to add components to sys.path"""
    print("\\n🧪 TESTING: sys.path Fix Approach")
    print("-" * 40)
    
    system_dir = "/home/brian/projects/autocoder4_cc/test_integration_system/scaffolds/todo_app_system"
    main_py_path = Path(system_dir, "main.py")
    
    if not main_py_path.exists():
        print("❌ NO MAIN.PY FOUND")
        return False
    
    # Read current main.py
    content = main_py_path.read_text()
    
    # Check if we need to add sys.path modification
    if "sys.path.append" not in content:
        # Add sys.path modification after imports
        lines = content.split("\\n")
        import_end_idx = 0
        
        # Find where imports end
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_end_idx = i
        
        # Insert sys.path modification
        insert_lines = [
            "",
            "# Add components directory to Python path for imports",
            "import sys",
            "components_path = os.path.join(os.path.dirname(__file__), 'components')",
            "if components_path not in sys.path:",
            "    sys.path.insert(0, components_path)"
        ]
        
        lines[import_end_idx+1:import_end_idx+1] = insert_lines
        new_content = "\\n".join(lines)
        main_py_path.write_text(new_content)
        print("✅ ADDED sys.path modification to main.py")
    
    # Test if the system can start now
    process = subprocess.Popen([
        "python", "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       cwd=system_dir, text=True)
    
    try:
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ sys.path FIX WORKS - System started")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ sys.path FIX FAILED")
            print(f"STDERR (last 500 chars): {stderr[-500:]}")
            return False
            
    except Exception as e:
        print(f"❌ sys.path TEST ERROR: {e}")
        process.terminate()
        return False


if __name__ == "__main__":
    print("🚀 TESTING IMPORT FIX APPROACHES")
    print("=" * 60)
    
    # Test 1: Absolute imports
    result1 = test_absolute_import_fix()
    
    # Test 2: sys.path modification  
    result2 = test_sys_path_fix()
    
    print("\\n" + "=" * 60)
    print("📋 IMPORT FIX TEST RESULTS")
    print("=" * 60)
    print(f"Absolute imports: {'✅ WORKS' if result1 else '❌ FAILS'}")
    print(f"sys.path approach: {'✅ WORKS' if result2 else '❌ FAILS'}")
    
    if result1 or result2:
        print("\\n✅ AT LEAST ONE IMPORT FIX APPROACH WORKS!")
    else:
        print("\\n❌ BOTH IMPORT FIX APPROACHES FAILED")