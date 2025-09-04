#!/usr/bin/env python3
"""
Simple test to validate the iterative testing approach
"""
import sys
import subprocess
import time
from pathlib import Path

def test_simple_iterative():
    """Test basic functionality of iterative testing"""
    print("🧪 Testing iterative Phase 4 fixes...")
    
    # Find the latest generated system
    generated_systems_dir = Path("generated_systems")
    if not generated_systems_dir.exists():
        print("❌ No generated_systems directory found")
        return False
    
    # Find all system directories
    system_dirs = [d for d in generated_systems_dir.iterdir() if d.is_dir() and d.name.startswith("system_")]
    
    if not system_dirs:
        print("❌ No system directories found")
        return False
    
    # Sort by modification time and get the latest
    latest_dir = max(system_dirs, key=lambda d: d.stat().st_mtime)
    
    # Find the actual system directory inside
    system_subdirs = []
    for d in latest_dir.iterdir():
        if d.is_dir() and not d.name.startswith(".") and (d / "main.py").exists():
            system_subdirs.append(d)
    
    if not system_subdirs:
        print(f"❌ No system subdirectories with main.py found in {latest_dir}")
        return False
    
    system_dir = system_subdirs[0]
    print(f"✅ Found latest system: {system_dir}")
    
    # Check if main.py exists
    main_file = system_dir / "main.py"
    if not main_file.exists():
        print(f"❌ main.py not found in {system_dir}")
        return False
    
    # Check if the setup_connections function exists
    with open(main_file, 'r') as f:
        content = f.read()
    
    if "setup_connections" not in content:
        print("❌ setup_connections function missing - this would be fixed by iterative testing")
        return False
    
    print("✅ setup_connections function exists")
    
    # Test basic syntax validation
    try:
        result = subprocess.run([
            sys.executable, "-m", "py_compile", str(main_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Syntax error in main.py: {result.stderr}")
            return False
        
        print("✅ main.py syntax is valid")
        
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False
    
    print("✅ Basic iterative testing validation passed")
    return True

if __name__ == "__main__":
    success = test_simple_iterative()
    sys.exit(0 if success else 1)