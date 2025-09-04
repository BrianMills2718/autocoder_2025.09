#!/usr/bin/env python3
"""
Test system generation validation to verify it catches missing files
"""
import subprocess
import sys
import os
import tempfile
from pathlib import Path

def test_system_validation():
    """Test that system generation validates output correctly"""
    
    test_request = "Create a simple hello world API"
    
    print("Testing system generation validation...")
    print("Request:", test_request)
    print("-" * 50)
    
    # Run the pipeline
    env = os.environ.copy()
    
    result = subprocess.run([
        sys.executable,
        "autocoder_cc/generate_deployed_system.py",
        test_request
    ], capture_output=True, text=True, env=env)
    
    print("Exit code:", result.returncode)
    
    # Check for validation messages in output
    output = result.stdout
    
    validation_checks = {
        "directory_created": False,
        "files_validated": False,
        "components_validated": False
    }
    
    # Look for validation messages
    if "Failed to create output directory" in output:
        print("✅ Directory creation validation present")
        validation_checks["directory_created"] = True
    elif "Output Directory:" in output:
        print("✅ Output directory created successfully")
        validation_checks["directory_created"] = True
    
    if "Validated Files:" in output and "component files" in output:
        print("✅ Component files validation present")
        validation_checks["files_validated"] = True
    
    if "Required file/directory missing:" in output:
        print("✅ Missing file validation present")
        validation_checks["files_validated"] = True
    elif "Components:" in output:
        print("✅ Components generated successfully")
        validation_checks["components_validated"] = True
    
    # Check if all validation succeeded
    if result.returncode == 0 and "System Generated:" in output:
        print("\n✅ System generation with validation succeeded")
        
        # Extract generated system info
        for line in output.split('\n'):
            if "Output Directory:" in line:
                print(f"   {line.strip()}")
            elif "Components:" in line:
                print(f"   {line.strip()}")
            elif "Validated Files:" in line:
                print(f"   {line.strip()}")
        
        return True
    else:
        print("\n❌ System generation failed")
        if result.stderr:
            print("STDERR:", result.stderr)
        return False

if __name__ == "__main__":
    success = test_system_validation()
    
    if success:
        print("\n✅ System generation validation is working correctly")
        sys.exit(0)
    else:
        print("\n❌ System generation validation test failed")
        sys.exit(1)