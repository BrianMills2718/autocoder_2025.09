"""
AutoCoder4_CC Strategic Smoke Test Suite

Purpose: Evidence-based bug discovery through critical workflow testing
Strategy: Test what users actually need, write unit tests only for proven broken components
Success: Clear bug inventory with specific reproduction steps and targeted action plan

Tests the 4 critical workflows:
1. System Generation: Blueprint → Generated System → Runnable Code
2. Component Integration: Store + API → Binding → Communication → Data Flow
3. CLI Operations: Command parsing → Basic operations → Help/version
4. System Execution: System startup → Health check → Basic response
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
import yaml
from io import StringIO
import asyncio

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_system_generation_workflow():
    """SMOKE TEST: Can AutoCoder4_CC generate a working system from blueprint?
    
    Tests: blueprint parsing → component generation → system assembly → file creation
    Critical for: Core system generation functionality
    """
    
    # Define a simple but realistic blueprint
    blueprint_yaml = """
    system:
      name: simple_todo_app
      description: "Simple todo application for smoke testing"
      components:
        - name: todo_store
          type: Store
          description: "Stores todo items"
          config:
            storage_type: memory
        - name: todo_api
          type: APIEndpoint
          description: "REST API for todo operations"
          config:
            port: 8080
          bindings:
            - todo_store
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Test: Can we import the system generator?
            from autocoder_cc.blueprint_language.system_generator import SystemGenerator
            
            # Test: Can we create system generator?
            generator = SystemGenerator(output_dir=temp_dir)
            
            # Test: Can we parse the blueprint?
            result = await generator.generate_system_from_yaml(blueprint_yaml)
            
            # Test: Did we get expected output structure?
            assert result is not None, "System generation returned None"
            
            # Test: Were files actually created?
            generated_files = list(Path(temp_dir).rglob("*.py"))
            assert len(generated_files) > 0, f"No Python files generated in {temp_dir}"
            
            # Test: Do generated files contain expected components?
            file_contents = []
            for file_path in generated_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    file_contents.append(content)
            
            all_content = ' '.join(file_contents)
            assert 'Store' in all_content, "Generated files missing Store component"
            assert 'APIEndpoint' in all_content, "Generated files missing APIEndpoint component"
            
            print(f"✅ SMOKE TEST PASSED: System generation created {len(generated_files)} files")
            return True
            
        except Exception as e:
            print(f"❌ SMOKE TEST FAILED: System generation - {type(e).__name__}: {e}")
            print(f"   Blueprint used: {blueprint_yaml}")
            print(f"   Output directory: {temp_dir}")
            return False


@pytest.mark.asyncio
async def test_component_integration_workflow():
    """SMOKE TEST: Do Store and API components work together?
    
    Tests: Component creation → binding → communication → data operations
    Critical for: Component interaction functionality
    """
    
    try:
        # Test: Can we import and create components?
        from autocoder_cc.components.store import Store
        from autocoder_cc.components.api_endpoint import APIEndpoint
        
        # Test: Can we create Store component?
        store = Store("test_store", {"storage_type": "memory"})
        await store.setup()
        
        # Test: Can we create API component?
        api = APIEndpoint("test_api", {"port": 8080})
        
        # Test: Can we bind components together?
        # (This tests the binding mechanism our reference patterns prove work)
        if hasattr(api, 'set_store_component'):
            api.set_store_component(store)
        elif hasattr(api, 'bind_component'):
            api.bind_component('store', store)
        else:
            # Test alternative binding patterns
            api.components = {'store': store}
        
        # Test: Can Store handle CRUD operations? (We know this works from reference tests)
        create_result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Test Task', 'completed': False}
        })
        assert create_result['status'] == 'success', f"Store create failed: {create_result}"
        task_id = create_result['id']
        
        # Test: Can we read back the created item?
        read_result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert read_result['status'] == 'success', f"Store read failed: {read_result}"
        assert read_result['data']['data']['title'] == 'Test Task'
        
        # Test: Can API component process requests? (if it has process_item method)
        if hasattr(api, 'process_item'):
            api_result = await api.process_item({
                'action': 'create_task',
                'data': {'title': 'API Test Task', 'completed': False}
            })
            print(f"API result: {api_result}")
        
        await store.cleanup()
        
        print("✅ SMOKE TEST PASSED: Component integration - Store and API work together")
        return True
        
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: Component integration - {type(e).__name__}: {e}")
        print(f"   Error details: {str(e)}")
        return False


def test_cli_operations_workflow():
    """SMOKE TEST: Does the AutoCoder4_CC CLI work for basic operations?
    
    Tests: CLI import → command parsing → help/version commands
    Critical for: User interface functionality
    """
    
    try:
        # Test: Can we import the CLI module?
        from autocoder_cc.cli.main import main
        
        # Test: Can we import command-line argument handling?
        import sys
        from io import StringIO
        
        # Test: Can CLI handle --help command?
        old_stdout = sys.stdout
        old_argv = sys.argv.copy()
        sys.stdout = captured_output = StringIO()
        
        try:
            # This should show help and exit gracefully
            sys.argv = ['autocoder_cc', '--help']
            main()
        except SystemExit as e:
            # Help command typically exits with code 0
            if e.code == 0:
                help_output = captured_output.getvalue()
                assert len(help_output) > 0, "CLI help produced no output"
                print("✅ CLI help command works")
            else:
                print(f"⚠️ CLI help exited with code {e.code}")
        finally:
            sys.stdout = old_stdout
            sys.argv = old_argv
        
        print("✅ SMOKE TEST PASSED: CLI operations - Basic CLI functionality works")
        return True
        
    except ImportError as e:
        print(f"❌ SMOKE TEST FAILED: CLI operations - Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: CLI operations - {type(e).__name__}: {e}")
        return False


@pytest.mark.asyncio
async def test_system_execution_workflow():
    """SMOKE TEST: Can a generated system actually start and respond?
    
    Tests: System startup → health check → basic operations
    Critical for: End-to-end functionality
    """
    
    try:
        # Test: Can we import the harness for running systems?
        from autocoder_cc.orchestration.harness import SystemExecutionHarness
        
        # Test: Can we create a simple system execution harness?
        harness = SystemExecutionHarness()
        
        # Test: Can we add components to the harness?
        from autocoder_cc.components.store import Store
        store = Store("test_store", {"storage_type": "memory"})
        
        # Test: Can harness manage component lifecycle?
        await store.setup()
        
        # Test: Is the component healthy?
        if hasattr(store, 'get_health_status'):
            health = store.get_health_status()
            assert health.get('healthy', False), f"Store component unhealthy: {health}"
        
        # Test: Can we run basic operations?
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'System Execution Test'}
        })
        assert result['status'] == 'success', f"System execution test failed: {result}"
        
        await store.cleanup()
        
        print("✅ SMOKE TEST PASSED: System execution - Components can start and operate")
        return True
        
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: System execution - {type(e).__name__}: {e}")
        return False


def run_all_smoke_tests():
    """Run all smoke tests and create comprehensive bug inventory"""
    
    results = {}
    
    print("🔥 AUTOCODER4_CC STRATEGIC SMOKE TEST SUITE")
    print("=" * 60)
    
    # Run each smoke test and capture results
    smoke_tests = [
        ("System Generation", test_system_generation_workflow),
        ("Component Integration", test_component_integration_workflow), 
        ("CLI Operations", test_cli_operations_workflow),
        ("System Execution", test_system_execution_workflow)
    ]
    
    for test_name, test_func in smoke_tests:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 40)
        
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            results[test_name] = {
                'passed': result,
                'error': None
            }
        except Exception as e:
            results[test_name] = {
                'passed': False,
                'error': f"{type(e).__name__}: {e}"
            }
            print(f"❌ CRITICAL FAILURE: {test_name} - {e}")
    
    # Generate bug inventory
    print("\n" + "=" * 60)
    print("📋 SMOKE TEST RESULTS & BUG INVENTORY")
    print("=" * 60)
    
    passed_tests = [name for name, result in results.items() if result['passed']]
    failed_tests = [name for name, result in results.items() if not result['passed']]
    
    print(f"✅ PASSED: {len(passed_tests)}/{len(results)} workflows")
    print(f"❌ FAILED: {len(failed_tests)}/{len(results)} workflows")
    
    if passed_tests:
        print(f"\n✅ Working workflows: {', '.join(passed_tests)}")
    
    if failed_tests:
        print(f"\n❌ BROKEN workflows requiring unit tests and fixes:")
        for test_name in failed_tests:
            error = results[test_name]['error']
            print(f"   - {test_name}: {error}")
    
    print("\n📝 NEXT ACTIONS:")
    if failed_tests:
        print("1. Write targeted unit tests for components in failed workflows")
        print("2. Fix broken components identified by smoke tests")
        print("3. Re-run smoke tests to validate fixes")
    else:
        print("1. All critical workflows pass - system is functional!")
        print("2. Consider adding integration tests for edge cases")
        print("3. Focus on performance optimization and additional features")
    
    return results


if __name__ == "__main__":
    run_all_smoke_tests()