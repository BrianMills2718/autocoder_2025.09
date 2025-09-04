#!/usr/bin/env python3
"""
Enhanced System Startup Validator
Provides detailed diagnosis of system startup failures
"""
import asyncio
import subprocess
import time
import requests
import sys
from pathlib import Path

async def validate_system_startup(system_path: str):
    """Comprehensive system startup validation with detailed logging."""
    print(f"🔍 Validating system startup: {system_path}")
    
    # Step 1: Validate file structure
    main_py = Path(system_path) / "main.py"
    if not main_py.exists():
        print(f"❌ main.py not found at {main_py}")
        return False
    
    # Step 2: Component registration validation
    print("\n📂 Testing component discovery...")
    component_result = subprocess.run([
        "python", "diagnostic_component_loading.py", 
        f"{system_path}/components"
    ], capture_output=True, text=True)
    
    print(f"Component diagnostic output:\n{component_result.stdout}")
    if component_result.stderr:
        print(f"Component diagnostic errors:\n{component_result.stderr}")
    
    # Step 3: Dependency installation
    print("\n📦 Installing dependencies...")
    requirements_file = Path(system_path) / "requirements.txt"
    if requirements_file.exists():
        install_result = subprocess.run([
            "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if install_result.returncode != 0:
            print(f"❌ Dependency installation failed:\n{install_result.stderr}")
            return False
        print("✅ Dependencies installed successfully")
    else:
        print("⚠️ No requirements.txt found, skipping dependency installation")
    
    # Step 4: System startup test
    print("\n🚀 Starting system...")
    # Change to system directory for relative imports
    original_cwd = Path.cwd()
    system_dir = Path(system_path)
    
    try:
        # Change to system directory
        import os
        os.chdir(system_dir)
        
        process = subprocess.Popen([
            "python", "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for startup
        print("⏳ Waiting for system to start (10 seconds)...")
        time.sleep(10)
        
        # Step 5: Health check validation
        print("\n🏥 Testing health endpoints...")
        try:
            health_response = requests.get("http://localhost:8000/health", timeout=5)
            print(f"Health check status: {health_response.status_code}")
            print(f"Health response: {health_response.text}")
            
            ready_response = requests.get("http://localhost:8000/ready", timeout=5)
            print(f"Ready check status: {ready_response.status_code}")
            print(f"Ready response: {ready_response.text}")
            
            success = health_response.status_code == 200 and ready_response.status_code == 200
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            success = False
        
        # Step 6: Cleanup
        print("\n🛑 Stopping system...")
        process.terminate()
        process.wait(timeout=10)
        
        if process.stdout:
            stdout = process.stdout.read()
            if stdout:
                print(f"System stdout:\n{stdout}")
        
        if process.stderr:
            stderr = process.stderr.read()
            if stderr:
                print(f"System stderr:\n{stderr}")
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
    
    return success

if __name__ == "__main__":
    system_path = sys.argv[1] if len(sys.argv) > 1 else "generated_systems/latest"
    success = asyncio.run(validate_system_startup(system_path))
    print(f"\n{'✅' if success else '❌'} System validation {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)