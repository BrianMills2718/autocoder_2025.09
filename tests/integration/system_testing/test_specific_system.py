#!/usr/bin/env python3
"""
Test the specific working system from system_20250715_094442
"""

import sys
import subprocess
import time
from pathlib import Path

def test_specific_system():
    """Test the specific working system"""
    system_dir = Path("generated_systems/system_20250715_094442/simple_to_do_app")
    
    if not system_dir.exists():
        print(f"❌ System directory not found: {system_dir}")
        return False
    
    main_file = system_dir / "main.py"
    if not main_file.exists():
        print(f"❌ main.py not found in {system_dir}")
        return False
    
    print(f"✅ Found system: {system_dir}")
    print(f"📦 Installing dependencies...")
    
    # Install dependencies
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      cwd=system_dir, check=True, capture_output=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Test system startup
    print("🔧 Testing system startup...")
    try:
        result = subprocess.run([sys.executable, "main.py"], 
                               cwd=system_dir, 
                               capture_output=True, 
                               text=True, 
                               timeout=10)
        
        if result.returncode == 0:
            print("✅ System started successfully")
            
            # Test health endpoint
            print("🔍 Testing health endpoint...")
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Health endpoint responded correctly")
                    return True
                else:
                    print(f"❌ Health endpoint returned {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Failed to test health endpoint: {e}")
                return False
        else:
            print(f"❌ System failed to start: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ System startup timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing system: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing Specific Working System")
    print("=" * 50)
    
    success = test_specific_system()
    
    if success:
        print("\n🎉 System test passed!")
    else:
        print("\n❌ System test failed!")
        sys.exit(1)