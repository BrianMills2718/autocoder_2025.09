#!/usr/bin/env python3
"""
Test full pipeline with Store/Sink components to verify fixes
"""
import subprocess
import sys
import os
import json
from pathlib import Path

def test_pipeline_with_store():
    """Test the pipeline with a system that has a Store component"""
    
    test_request = """
    Create a simple todo API system with the following components:
    1. A REST API endpoint that accepts todo items
    2. A Store component that saves todos to a database (PostgreSQL)
    3. The API should support creating and retrieving todos
    """
    
    print("Testing pipeline with Store component...")
    print("Request:", test_request)
    print("-" * 50)
    
    # Run the pipeline
    env = os.environ.copy()
    
    # Use Gemini if configured, otherwise use OpenAI
    if 'GEMINI_API_KEY' in env:
        env['LLM_PROVIDER'] = 'gemini'
        env['LLM_MODEL'] = 'gemini-2.0-flash-exp'
        print("Using Gemini API")
    else:
        print("Using OpenAI API")
    
    result = subprocess.run([
        sys.executable,
        "autocoder_cc/generate_deployed_system.py",
        test_request
    ], capture_output=True, text=True, env=env)
    
    print("Exit code:", result.returncode)
    
    # Parse output to find generated system directory
    output_lines = result.stdout.split('\n')
    system_dir = None
    
    for line in output_lines:
        if "System Generated:" in line:
            # Extract system name
            parts = line.split("System Generated:")
            if len(parts) > 1:
                system_name = parts[1].strip()
                # Find the output directory
                for line2 in output_lines:
                    if "Output Directory:" in line2 and system_name in line2:
                        dir_path = line2.split("Output Directory:")[-1].strip()
                        system_dir = Path(dir_path)
                        break
    
    if not system_dir or not system_dir.exists():
        print("Could not find generated system directory")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print(f"Found generated system at: {system_dir}")
    
    # Check for Store component
    components_dir = system_dir / "components"
    if not components_dir.exists():
        print("Components directory not found")
        return False
    
    # Look for store component
    store_found = False
    sink_instead_of_store = False
    
    for py_file in components_dir.glob("*.py"):
        content = py_file.read_text()
        if "GeneratedStore_" in content:
            print(f"✅ Found Store component in {py_file.name}")
            store_found = True
        elif "store" in py_file.name.lower() and "GeneratedSink_" in content:
            print(f"❌ ERROR: Found Sink class in store component file {py_file.name}")
            sink_instead_of_store = True
            # Print the class definition line
            for line in content.split('\n'):
                if "class Generated" in line:
                    print(f"   Class definition: {line.strip()}")
    
    return store_found and not sink_instead_of_store

if __name__ == "__main__":
    success = test_pipeline_with_store()
    
    if success:
        print("\n✅ Pipeline test PASSED - Store components generated correctly")
        sys.exit(0)
    else:
        print("\n❌ Pipeline test FAILED - Store/Sink confusion detected")
        sys.exit(1)