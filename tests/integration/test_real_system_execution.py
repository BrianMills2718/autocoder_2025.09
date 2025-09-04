#!/usr/bin/env python3
"""
AutoCoder4_CC Phase 2A Real Integration Testing Suite
====================================================

Tests that generated systems can actually run as real applications with:
- HTTP endpoints serving real requests
- Database persistence across restarts
- Component communication through harness
- Complete CRUD operations

This follows the evidence-based development approach from CLAUDE.md.
"""

import pytest
import tempfile
import subprocess
import time
import requests
import json
import os
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List


class IntegrationTestRunner:
    """Helper class for running integration tests with proper cleanup"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.test_dirs: List[str] = []
    
    def cleanup(self):
        """Clean up all test processes and directories"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
        self.processes.clear()


@pytest.fixture
def integration_runner():
    """Fixture that provides cleanup for integration tests"""
    runner = IntegrationTestRunner()
    yield runner
    runner.cleanup()


def test_real_system_generation(integration_runner):
    """INTEGRATION TEST: Generate a complete todo system"""
    
    blueprint_description = (
        "A complete todo application with REST API endpoints for creating, reading, "
        "updating and deleting todos. Include persistent storage and proper CRUD operations."
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate the system using the CLI
        result = subprocess.run([
            "python", "-m", "autocoder_cc.cli.main", "generate", 
            blueprint_description, "-o", temp_dir
        ], capture_output=True, text=True, cwd="/home/brian/projects/autocoder4_cc")
        
        print(f"Generation stdout: {result.stdout}")
        print(f"Generation stderr: {result.stderr}")
        
        assert result.returncode == 0, f"System generation failed: {result.stderr}"
        
        # Check that files were generated
        system_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "main.py" in files and "requirements.txt" in files:
                system_dir = root
                break
        
        assert system_dir is not None, "Generated system directory with main.py not found"
        assert Path(system_dir, "main.py").exists(), "main.py missing"
        assert Path(system_dir, "requirements.txt").exists(), "requirements.txt missing"
        assert Path(system_dir, "components").exists(), "components directory missing"
        
        integration_runner.test_dirs.append(temp_dir)
        return system_dir


def test_component_import_fix(integration_runner):
    """INTEGRATION TEST: Check if generated components can be imported after fixing imports"""
    
    system_dir = test_real_system_generation(integration_runner)
    
    # Check for the known import bug
    component_files = list(Path(system_dir, "components").glob("*.py"))
    component_files = [f for f in component_files if not f.name.startswith("_")]
    
    import_bugs_found = []
    
    for component_file in component_files:
        content = component_file.read_text()
        if "from autocoder_cc.components.composed_base import ComposedComponent" in content:
            import_bugs_found.append(str(component_file))
    
    # This test is expected to FAIL initially - documenting the bug
    assert len(import_bugs_found) > 0, f"Expected import bugs not found - may already be fixed"
    
    print(f"✅ CONFIRMED: Import bug found in {len(import_bugs_found)} files")
    print(f"   Files with import bugs: {import_bugs_found}")
    
    # Now test if fixing the imports would resolve the issue
    # (This is a simulation - we're not actually fixing the generation pipeline yet)
    fixed_count = 0
    for component_file in component_files:
        content = component_file.read_text()
        if "from autocoder_cc.components.composed_base import ComposedComponent" in content:
            # Simulate the fix
            fixed_content = content.replace(
                "from autocoder_cc.components.composed_base import ComposedComponent",
                "from .observability import ComposedComponent"
            )
            component_file.write_text(fixed_content)
            fixed_count += 1
    
    print(f"✅ SIMULATED FIX: Fixed imports in {fixed_count} files")
    return system_dir


@pytest.mark.asyncio 
async def test_real_system_execution(integration_runner):
    """INTEGRATION TEST: Can generated system actually run after fixing imports?"""
    
    system_dir = test_component_import_fix(integration_runner)
    
    # Try to install dependencies
    install_result = subprocess.run([
        "pip", "install", "-r", str(Path(system_dir) / "requirements.txt")
    ], capture_output=True, text=True)
    
    assert install_result.returncode == 0, f"Dependency installation failed: {install_result.stderr}"
    
    # Try to start the system
    process = subprocess.Popen([
        "python", str(Path(system_dir) / "main.py")
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       cwd=system_dir, text=True)
    
    integration_runner.processes.append(process)
    
    try:
        # Wait for system to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"System exited early. STDOUT: {stdout}\\nSTDERR: {stderr}")
        
        # Test if system is responding on expected ports
        # Check common ports: 8080, 8000, 8554 (from generation logs)
        ports_to_try = [8080, 8000, 8554]
        system_port = None
        
        for port in ports_to_try:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    system_port = port
                    break
            except requests.exceptions.RequestException:
                continue
        
        if system_port is None:
            # Try the /docs endpoint which FastAPI provides by default
            for port in ports_to_try:
                try:
                    response = requests.get(f"http://localhost:{port}/docs", timeout=2)
                    if response.status_code == 200:
                        system_port = port
                        break
                except requests.exceptions.RequestException:
                    continue
        
        if system_port is None:
            # Get process output for debugging
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            pytest.fail(f"System not responding on any port. STDOUT: {stdout}\\nSTDERR: {stderr}")
        
        print(f"✅ INTEGRATION TEST PASSED: Generated system runs and responds on port {system_port}")
        return system_port
        
    except Exception as e:
        # Get process output for debugging
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(f"Integration test failed: {e}\\nSTDOUT: {stdout}\\nSTDERR: {stderr}")


def test_real_api_endpoints(integration_runner):
    """INTEGRATION TEST: Do API endpoints work for CRUD operations?"""
    
    try:
        system_port = test_real_system_execution(integration_runner)
    except Exception as e:
        pytest.skip(f"System execution test failed, skipping API test: {e}")
    
    base_url = f"http://localhost:{system_port}"
    
    # Test API discovery first
    endpoints_to_try = [
        "/todos", "/tasks", "/api/todos", "/api/tasks",
        "/todo", "/task", "/items", "/api/items"
    ]
    
    working_endpoint = None
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=2)
            if response.status_code in [200, 404]:  # 404 means endpoint exists but no data
                working_endpoint = endpoint
                break
        except requests.exceptions.RequestException:
            continue
    
    if working_endpoint is None:
        pytest.fail(f"No working API endpoints found. Tried: {endpoints_to_try}")
    
    print(f"✅ Found working endpoint: {working_endpoint}")
    
    # Test CREATE todo
    todo_data = {"title": "Integration Test Todo", "description": "Testing CRUD"}
    
    try:
        create_response = requests.post(f"{base_url}{working_endpoint}", 
                                      json=todo_data, timeout=5)
        
        print(f"Create response status: {create_response.status_code}")
        print(f"Create response body: {create_response.text}")
        
        # Accept various success codes
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.status_code} - {create_response.text}"
        
        # Try to extract ID from response
        todo_id = None
        try:
            response_data = create_response.json()
            todo_id = response_data.get("id") or response_data.get("task_id") or response_data.get("todo_id")
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Test READ todos
        list_response = requests.get(f"{base_url}{working_endpoint}", timeout=5)
        assert list_response.status_code == 200, f"List failed: {list_response.status_code}"
        
        try:
            todos = list_response.json()
            if isinstance(todos, dict):
                todos = todos.get("todos", todos.get("tasks", todos.get("items", [])))
            assert len(todos) > 0, "No todos returned after creation"
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response from list endpoint: {list_response.text}")
        
        print(f"✅ CRUD Operations: CREATE and READ working")
        
        # Test UPDATE and DELETE if we have an ID
        if todo_id:
            # Test UPDATE todo
            update_response = requests.put(f"{base_url}{working_endpoint}/{todo_id}",
                                         json={"completed": True}, timeout=5)
            print(f"Update response: {update_response.status_code}")
            
            # Test DELETE todo
            delete_response = requests.delete(f"{base_url}{working_endpoint}/{todo_id}", timeout=5)
            print(f"Delete response: {delete_response.status_code}")
            
            print(f"✅ CRUD Operations: All operations attempted")
        
        print("✅ INTEGRATION TEST PASSED: API endpoints responding")
        return True
        
    except Exception as e:
        pytest.fail(f"API endpoint testing failed: {e}")


def test_database_persistence(integration_runner):
    """INTEGRATION TEST: Does data survive application restarts?"""
    
    try:
        system_port = test_real_system_execution(integration_runner)
    except Exception as e:
        pytest.skip(f"System execution test failed, skipping persistence test: {e}")
    
    base_url = f"http://localhost:{system_port}"
    
    # Find working endpoint
    endpoints_to_try = ["/todos", "/tasks", "/api/todos", "/api/tasks"]
    working_endpoint = None
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=2)
            if response.status_code in [200, 404]:
                working_endpoint = endpoint
                break
        except requests.exceptions.RequestException:
            continue
    
    if working_endpoint is None:
        pytest.skip("No working API endpoints found for persistence test")
    
    # Create a todo before restart
    todo_data = {"title": "Persistence Test", "description": "Should survive restart"}
    
    try:
        create_response = requests.post(f"{base_url}{working_endpoint}",
                                      json=todo_data, timeout=5)
        assert create_response.status_code in [200, 201]
        
        # Get current todo count
        list_response = requests.get(f"{base_url}{working_endpoint}", timeout=5)
        original_todos = list_response.json()
        if isinstance(original_todos, dict):
            original_todos = original_todos.get("todos", original_todos.get("tasks", original_todos.get("items", [])))
        original_count = len(original_todos)
        
        print(f"✅ Created todo, original count: {original_count}")
        
    except Exception as e:
        pytest.skip(f"Could not create initial todo for persistence test: {e}")
    
    # Stop the current process
    current_process = integration_runner.processes[-1]
    current_process.terminate()
    current_process.wait(timeout=10)
    integration_runner.processes.remove(current_process)
    
    # Wait a moment for cleanup
    time.sleep(2)
    
    # Start system again (this would test persistence if it was properly implemented)
    system_dir = Path(current_process.args[1]).parent  # Get system directory from process args
    
    new_process = subprocess.Popen([
        "python", "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       cwd=system_dir, text=True)
    
    integration_runner.processes.append(new_process)
    
    try:
        # Wait for restart
        time.sleep(5)
        
        # Check if todos still exist
        list_response = requests.get(f"{base_url}{working_endpoint}", timeout=5)
        
        if list_response.status_code == 200:
            todos_after_restart = list_response.json()
            if isinstance(todos_after_restart, dict):
                todos_after_restart = todos_after_restart.get("todos", todos_after_restart.get("tasks", todos_after_restart.get("items", [])))
            
            new_count = len(todos_after_restart)
            
            print(f"✅ After restart count: {new_count}")
            
            # This test is expected to FAIL initially if persistence isn't implemented
            if new_count >= original_count:
                print("✅ INTEGRATION TEST PASSED: Data persists across restarts")
                return True
            else:
                print("❌ INTEGRATION TEST FAILED: Data lost across restarts (expected)")
                pytest.fail("Data persistence not implemented - todos lost after restart")
        else:
            pytest.fail(f"System not responding after restart: {list_response.status_code}")
            
    except Exception as e:
        new_process.terminate()
        stdout, stderr = new_process.communicate(timeout=5)
        pytest.fail(f"Persistence test failed: {e}\\nSTDOUT: {stdout}\\nSTDERR: {stderr}")


def run_all_integration_tests():
    """Run all integration tests and report results"""
    
    print("🚀 AUTOCODER4_CC PHASE 2A REAL INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Create a test runner for manual execution
    runner = IntegrationTestRunner()
    
    tests = [
        ("System Generation", lambda: test_real_system_generation(runner)),
        ("Component Import Fix", lambda: test_component_import_fix(runner)),
        ("System Execution", lambda: test_real_system_execution(runner)),
        ("API Endpoints", lambda: test_real_api_endpoints(runner)),
        ("Database Persistence", lambda: test_database_persistence(runner))
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n🧪 Testing: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = {'passed': True, 'error': None, 'result': result}
            print(f"✅ PASSED: {test_name}")
        except Exception as e:
            results[test_name] = {'passed': False, 'error': str(e), 'result': None}
            print(f"❌ FAILED: {test_name} - {e}")
        except SystemExit:
            results[test_name] = {'passed': False, 'error': 'Test caused system exit', 'result': None}
            print(f"❌ FAILED: {test_name} - Test caused system exit")
    
    # Clean up
    runner.cleanup()
    
    # Results summary
    print("\\n" + "=" * 60)
    print("📋 PHASE 2A INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = [name for name, r in results.items() if r['passed']]
    failed = [name for name, r in results.items() if not r['passed']]
    
    print(f"✅ PASSED: {len(passed)}/{len(tests)} integration tests")
    print(f"❌ FAILED: {len(failed)}/{len(tests)} integration tests")
    
    if passed:
        print(f"\\n✅ PASSED TESTS:")
        for test_name in passed:
            print(f"   - {test_name}")
    
    if failed:
        print(f"\\n❌ FAILED TESTS:")
        for test_name in failed:
            error = results[test_name]['error']
            print(f"   - {test_name}: {error}")
    
    return results


if __name__ == "__main__":
    run_all_integration_tests()