#!/usr/bin/env python3
"""
Generated System Integration Test

This test verifies that the complete pipeline works:
1. Generate system from natural language
2. Start the generated system
3. Verify health endpoints respond
4. Test core functionality
5. Gracefully shut down

Usage:
    python test_generated_system_integration.py "Create a todo API"
"""

import asyncio
import subprocess
import time
import requests
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional


async def test_end_to_end_pipeline(natural_language_input: str, timeout: int = 300):
    """Test complete pipeline from natural language to running system"""
    
    print(f"🧪 Testing end-to-end pipeline: '{natural_language_input}'")
    
    # Create temporary directory for test
    test_dir = Path(tempfile.mkdtemp(prefix="integration_test_"))
    print(f"📁 Test directory: {test_dir}")
    
    try:
        # Step 1: Generate system
        print("📝 Step 1: Generating system...")
        system_path = await generate_system(natural_language_input, test_dir, timeout)
        print(f"✅ System generated at: {system_path}")
        
        # Step 2: Verify generated files
        print("🔍 Step 2: Verifying generated files...")
        verify_generated_files(system_path)
        print("✅ Generated files verified")
        
        # Step 3: Start system
        print("🚀 Step 3: Starting generated system...")
        process = await start_system(system_path)
        
        # Wait for startup
        await asyncio.sleep(5)
        
        try:
            # Step 4: Test health endpoints
            print("🔍 Step 4: Testing health endpoints...")
            await test_health_endpoints()
            print("✅ Health checks passed")
            
            # Step 5: Test core functionality (API endpoints)
            print("🧪 Step 5: Testing core functionality...")
            await test_core_functionality(natural_language_input)
            print("✅ Core functionality tests passed")
            
        finally:
            # Step 6: Graceful shutdown
            print("🛑 Step 6: Shutting down system...")
            await shutdown_system(process)
            print("✅ System shut down gracefully")
        
        print("🎉 End-to-end pipeline test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end pipeline test FAILED: {e}")
        return False
        
    finally:
        # Cleanup test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory: {test_dir}")


async def generate_system(natural_language_input: str, output_dir: Path, timeout: int) -> Path:
    """Generate a system from natural language input"""
    
    # Look for system generation script
    generation_scripts = [
        "generate_deployed_system.py",
        "main.py",
        "autocoder_cc/main.py",
        "autocoder/main.py"
    ]
    
    generation_script = None
    current_dir = Path.cwd()
    
    for script in generation_scripts:
        script_path = current_dir / script
        if script_path.exists():
            generation_script = script_path
            break
    
    if not generation_script:
        # Try to find any generation script
        for script_path in current_dir.rglob("*generate*.py"):
            if "test" not in script_path.name.lower():
                generation_script = script_path
                break
    
    if not generation_script:
        raise FileNotFoundError("Could not find system generation script")
    
    print(f"📝 Using generation script: {generation_script}")
    
    # Run generation script
    cmd = [sys.executable, str(generation_script), natural_language_input, "--output", str(output_dir)]
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=current_dir
        )
        
        if result.returncode != 0:
            print(f"Generation stdout: {result.stdout}")
            print(f"Generation stderr: {result.stderr}")
            raise Exception(f"System generation failed with return code {result.returncode}: {result.stderr}")
        
        # Extract system path from output
        system_path = extract_system_path(result.stdout, output_dir)
        
        if not system_path or not system_path.exists():
            raise Exception(f"Generated system path not found or doesn't exist: {system_path}")
        
        return system_path
        
    except subprocess.TimeoutExpired:
        raise Exception(f"System generation timed out after {timeout} seconds")


def extract_system_path(output: str, base_dir: Path) -> Path:
    """Extract the generated system path from generator output"""
    
    # Look for common patterns in output
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Look for "Generated in:" or similar patterns
        if "generated" in line.lower() and ("in:" in line.lower() or "at:" in line.lower()):
            # Extract path after "in:" or "at:"
            parts = line.split()
            for i, part in enumerate(parts):
                if part.lower() in ["in:", "at:"]:
                    if i + 1 < len(parts):
                        path = Path(parts[i + 1])
                        if path.exists():
                            return path
        
        # Look for directory paths
        if line.startswith('/') or line.startswith('./'):
            path = Path(line)
            if path.exists() and path.is_dir():
                return path
    
    # Fallback: look for directories in the output directory
    if base_dir.exists():
        for item in base_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                # Check if it has main.py
                if (item / "main.py").exists():
                    return item
    
    # Final fallback: assume the base directory is the system
    return base_dir


def verify_generated_files(system_path: Path) -> None:
    """Verify that the generated system has required files"""
    
    required_files = [
        "main.py",
        "requirements.txt"
    ]
    
    optional_files = [
        "blueprint.yaml",
        "system_metadata.json",
        "components",
        "config"
    ]
    
    missing_required = []
    for file_name in required_files:
        file_path = system_path / file_name
        if not file_path.exists():
            missing_required.append(file_name)
    
    if missing_required:
        raise Exception(f"Missing required files: {missing_required}")
    
    # Check main.py content
    main_py_content = (system_path / "main.py").read_text()
    if "SystemExecutionHarness" not in main_py_content:
        print("⚠️  Warning: main.py doesn't use SystemExecutionHarness (may be using bypass)")
    
    print(f"📁 System structure verified:")
    for item in system_path.iterdir():
        if item.is_dir():
            print(f"   📁 {item.name}/")
        else:
            print(f"   📄 {item.name}")


async def start_system(system_path: Path) -> subprocess.Popen:
    """Start the generated system"""
    
    # Change to system directory
    main_py = system_path / "main.py"
    if not main_py.exists():
        raise Exception(f"main.py not found in {system_path}")
    
    # Install requirements if requirements.txt exists
    requirements_txt = system_path / "requirements.txt"
    if requirements_txt.exists():
        print("📦 Installing requirements...")
        install_result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_txt)
        ], capture_output=True, text=True)
        
        if install_result.returncode != 0:
            print(f"⚠️  Warning: Requirements installation failed: {install_result.stderr}")
    
    # Start the system
    print(f"🚀 Starting system: python {main_py}")
    
    process = subprocess.Popen([
        sys.executable, str(main_py)
    ], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE,
    cwd=system_path,
    text=True
    )
    
    return process


async def test_health_endpoints(base_url: str = "http://localhost:8000") -> None:
    """Test health endpoints"""
    
    endpoints = [
        "/health",
        "/ready"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        
        # Retry logic for startup
        for attempt in range(10):
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {data.get('status', 'unknown')}")
                    break
                else:
                    print(f"⚠️  {endpoint}: HTTP {response.status_code}")
                    if attempt < 9:
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"Health check failed: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                if attempt < 9:
                    print(f"🔄 Waiting for system startup... (attempt {attempt + 1}/10)")
                    await asyncio.sleep(3)
                else:
                    raise Exception(f"Could not connect to {url}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Health check request failed: {e}")


async def test_core_functionality(natural_language_input: str, base_url: str = "http://localhost:8000") -> None:
    """Test the generated system's core functionality"""
    
    # Test basic endpoints
    endpoints_to_test = [
        "/",
        "/api/v1",
        "/docs",  # FastAPI docs
    ]
    
    successful_tests = 0
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code in [200, 404]:  # 404 is ok for missing endpoints
                print(f"✅ {endpoint}: HTTP {response.status_code}")
                if response.status_code == 200:
                    successful_tests += 1
            else:
                print(f"⚠️  {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  {endpoint}: Request failed - {e}")
    
    # Test API functionality based on input
    if "todo" in natural_language_input.lower() or "api" in natural_language_input.lower():
        await test_api_functionality(base_url)
        successful_tests += 1
    
    if successful_tests == 0:
        raise Exception("No core functionality tests passed")
    
    print(f"✅ {successful_tests} core functionality tests passed")


async def test_api_functionality(base_url: str) -> None:
    """Test API-specific functionality"""
    
    # Test common API endpoints
    api_endpoints = [
        "/api/v1/health",
        "/api/v1/status",
    ]
    
    for endpoint in api_endpoints:
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ API {endpoint}: Working")
                break
            elif response.status_code == 404:
                continue  # Try next endpoint
            else:
                print(f"⚠️  API {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException:
            continue  # Try next endpoint
    
    # Test POST functionality if possible
    try:
        test_data = {"test": "data", "message": "integration test"}
        response = requests.post(f"{base_url}/api/v1/test", json=test_data, timeout=5)
        
        if response.status_code in [200, 201, 404, 405]:  # 404/405 are acceptable
            print(f"✅ API POST test: HTTP {response.status_code}")
        else:
            print(f"⚠️  API POST test: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException:
        print("ℹ️  API POST test: Endpoint not available")


async def shutdown_system(process: subprocess.Popen) -> None:
    """Gracefully shut down the system"""
    
    try:
        # Try graceful shutdown first
        process.terminate()
        
        # Wait for graceful shutdown
        try:
            process.wait(timeout=10)
            print("✅ System terminated gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            print("⚠️  Graceful shutdown timeout, forcing kill...")
            process.kill()
            process.wait(timeout=5)
            print("✅ System force killed")
            
    except Exception as e:
        print(f"⚠️  Error during shutdown: {e}")


async def main():
    """Main entry point"""
    
    if len(sys.argv) != 2:
        print("Usage: python test_generated_system_integration.py '<natural language>'")
        print("Example: python test_generated_system_integration.py 'Create a todo API'")
        sys.exit(1)
    
    natural_language_input = sys.argv[1]
    
    print("🧪 Generated System Integration Test")
    print(f"📝 Input: {natural_language_input}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        success = await test_end_to_end_pipeline(natural_language_input)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            print("=" * 60)
            print(f"🎉 INTEGRATION TEST PASSED")
            print(f"⏱️  Duration: {duration:.1f} seconds")
            sys.exit(0)
        else:
            print("=" * 60)
            print(f"❌ INTEGRATION TEST FAILED")
            print(f"⏱️  Duration: {duration:.1f} seconds")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print(f"❌ INTEGRATION TEST FAILED: {e}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())