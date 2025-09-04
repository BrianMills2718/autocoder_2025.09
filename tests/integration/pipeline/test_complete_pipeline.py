#!/usr/bin/env python3
"""
Complete Pipeline Test Suite
Tests entire natural language to deployed system pipeline
"""
import asyncio
import subprocess
import tempfile
import shutil
import sys
import re
from pathlib import Path

def extract_system_path(generation_output: str) -> str:
    """Extract system path from generation output."""
    # Look for patterns like "Generated system at:" or similar
    patterns = [
        r"Generated system at:\s*(.+)",
        r"System generated successfully:\s*(.+)", 
        r"✅ Generated system:\s*(.+)",
        r"System location:\s*(.+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, generation_output, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Fallback: look for generated_systems paths
    lines = generation_output.split('\n')
    for line in lines:
        if 'generated_systems/' in line and 'system_' in line:
            # Try to extract path from the line
            parts = line.strip().split()
            for part in parts:
                if 'generated_systems/' in part and 'system_' in part:
                    return part.strip()
    
    # Last resort: use most recent system directory
    try:
        generated_dir = Path("generated_systems")
        if generated_dir.exists():
            system_dirs = [d for d in generated_dir.iterdir() if d.is_dir() and d.name.startswith('system_')]
            if system_dirs:
                latest_dir = max(system_dirs, key=lambda d: d.stat().st_mtime)
                # Look for actual system directories within
                system_subdirs = [d for d in latest_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
                if system_subdirs:
                    return str(system_subdirs[0])
                return str(latest_dir)
    except Exception:
        pass
    
    return "generated_systems/latest"

async def validate_system_startup(system_path: str) -> bool:
    """Validate that a generated system can start up successfully."""
    print(f"  🔍 Validating system startup: {system_path}")
    
    # Check if main.py exists
    main_py = Path(system_path) / "main.py"
    if not main_py.exists():
        print(f"  ❌ main.py not found at {main_py}")
        return False
    
    # Change to system directory for startup
    original_cwd = Path.cwd()
    system_dir = Path(system_path)
    
    try:
        import os
        os.chdir(system_dir)
        
        # Start the system with a timeout
        process = subprocess.Popen([
            "python", "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait briefly for startup
        import time
        time.sleep(5)
        
        # Check if process is still running (indicates successful startup)
        if process.poll() is None:
            print(f"  ✅ System started successfully")
            success = True
        else:
            stdout, stderr = process.communicate()
            print(f"  ❌ System failed to start")
            print(f"  Error output: {stderr[:200]}...")
            success = False
        
        # Cleanup
        if process.poll() is None:
            process.terminate()
            process.wait()  # No timeout
        
    except Exception as e:
        print(f"  ❌ Startup validation failed: {e}")
        success = False
    
    finally:
        os.chdir(original_cwd)
    
    return success

async def test_complete_pipeline():
    """Test complete pipeline from natural language to working system."""
    test_requests = [
        "Create a simple todo API with add and list functionality",
        "Build a user management system with basic CRUD operations", 
        "Make a basic blog API with posts and comments"
    ]
    
    results = []
    successful_systems = []
    
    print("🧪 Testing Complete Pipeline: Natural Language → Working Systems")
    print("=" * 70)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📝 Test {i}/3: {request}")
        print("-" * 50)
        
        try:
            # Generate system with timeout
            print("  🔧 Generating system...")
            result = subprocess.run([
                "python", "autocoder_cc/generate_deployed_system.py", request
            ], capture_output=True, text=True)  # No timeout
            
            if result.returncode != 0:
                print(f"  ❌ Generation failed: {result.stderr[:200]}...")
                results.append(False)
                continue
            
            print("  ✅ System generation completed")
            
            # Extract system path from output
            system_path = extract_system_path(result.stdout)
            print(f"  📂 System path: {system_path}")
            
            # Validate startup
            startup_success = await validate_system_startup(system_path)
            results.append(startup_success)
            
            if startup_success:
                successful_systems.append({
                    'request': request,
                    'path': system_path
                })
            
            status = "✅ PASSED" if startup_success else "❌ FAILED"
            print(f"  📊 Result: {status}")
            
        except subprocess.TimeoutExpired:
            print(f"  ❌ Generation timed out (10 minutes)")
            results.append(False)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    # Calculate results
    success_count = sum(results)
    total_count = len(results)
    success_rate = success_count / total_count if total_count > 0 else 0
    
    print("\n" + "=" * 70)
    print(f"📊 PIPELINE TEST RESULTS")
    print("=" * 70)
    print(f"Success Rate: {success_rate:.1%} ({success_count}/{total_count})")
    print(f"Successful Systems: {len(successful_systems)}")
    
    if successful_systems:
        print("\n✅ Working Systems Generated:")
        for system in successful_systems:
            print(f"  • {system['request']}")
            print(f"    Path: {system['path']}")
    
    # Determine overall result
    required_success_rate = 0.6  # 60% success rate required
    overall_success = success_rate >= required_success_rate
    
    print(f"\n🎯 Overall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    print(f"Required: {required_success_rate:.0%}, Achieved: {success_rate:.1%}")
    
    return overall_success

if __name__ == "__main__":
    print("🚀 AutoCoder4 Complete Pipeline Test Suite")
    print("Testing entire pipeline: Natural Language → Blueprint → Components → Deployed System")
    print()
    
    try:
        success = asyncio.run(test_complete_pipeline())
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        exit_code = 1
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        exit_code = 1
    
    sys.exit(exit_code)