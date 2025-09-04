#!/usr/bin/env python3
"""
Test the system by starting it in background and checking health
"""

import sys
import subprocess
import time
import signal
import os
from pathlib import Path

def test_system_background():
    """Test system by starting in background"""
    system_dir = Path("generated_systems/system_20250715_094442/simple_to_do_app")
    
    if not system_dir.exists():
        print(f"❌ System directory not found: {system_dir}")
        return False
    
    main_file = system_dir / "main.py"
    if not main_file.exists():
        print(f"❌ main.py not found in {system_dir}")
        return False
    
    print(f"✅ Found system: {system_dir}")
    
    # Start system in background
    print("🚀 Starting system in background...")
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=system_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for system to start
    print("⏰ Waiting for system to start...")
    time.sleep(5)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"❌ System failed to start:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False
    
    print("✅ System appears to be running")
    
    # Test health endpoint
    print("🔍 Testing health endpoint...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint responded correctly")
            print(f"Response: {response.json()}")
            success = True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            success = False
    except Exception as e:
        print(f"❌ Failed to test health endpoint: {e}")
        success = False
    
    # Clean up - kill the process
    print("🧹 Cleaning up...")
    try:
        process.terminate()
        process.wait(timeout=5)
        print("✅ System stopped gracefully")
    except subprocess.TimeoutExpired:
        print("⚠️  System didn't stop gracefully, force killing...")
        process.kill()
        process.wait()
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
    
    return success

if __name__ == "__main__":
    print("🎯 Testing System with Background Start")
    print("=" * 50)
    
    success = test_system_background()
    
    if success:
        print("\n🎉 System test passed!")
    else:
        print("\n❌ System test failed!")
        sys.exit(1)