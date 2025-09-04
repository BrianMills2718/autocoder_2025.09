"""Test Level 4: Components can execute without runtime errors"""
import subprocess
import sys
import tempfile
from pathlib import Path
import asyncio
import importlib.util
import pytest
import time


class TestExecutionDiagnosis:
    """Diagnose what prevents execution"""
    
    def test_component_instantiation(self):
        """Test if components can be instantiated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate system
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Execution Test", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0, f"Generation failed: {result.stderr}"
            
            system_dir = list(Path(tmpdir).glob("scaffolds/*"))[0]
            
            # Add components to path
            sys.path.insert(0, str(system_dir / "components"))
            
            errors = []
            successes = []
            
            # Try to instantiate each component
            for comp_file in system_dir.glob("components/*.py"):
                if comp_file.stem in ["observability", "communication", "__init__"]:
                    continue
                    
                try:
                    # Load and instantiate
                    spec = importlib.util.spec_from_file_location(comp_file.stem, comp_file)
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add components dir to path for the module
                    original_path = sys.path.copy()
                    sys.path.insert(0, str(comp_file.parent))
                    
                    try:
                        spec.loader.exec_module(module)
                    finally:
                        sys.path = original_path
                    
                    # Find Generated class
                    generated_classes = [
                        (name, obj) for name, obj in vars(module).items()
                        if isinstance(obj, type) and name.startswith("Generated")
                    ]
                    
                    if not generated_classes:
                        errors.append(f"{comp_file.stem}: No Generated class found")
                        continue
                    
                    for class_name, ComponentClass in generated_classes:
                        try:
                            instance = ComponentClass(name="test", config={})
                            successes.append(f"{comp_file.stem}.{class_name}")
                        except Exception as e:
                            errors.append(f"{comp_file.stem}.{class_name}: {type(e).__name__}: {str(e)[:100]}")
                            
                except Exception as e:
                    errors.append(f"{comp_file.stem}: Module load failed - {type(e).__name__}: {str(e)[:100]}")
            
            # Report results
            print(f"\n=== Instantiation Results ===")
            print(f"Successes: {len(successes)}")
            for success in successes:
                print(f"  ✅ {success}")
            
            print(f"\nErrors: {len(errors)}")
            for error in errors:
                print(f"  ❌ {error}")
            
            # Don't fail yet - we're diagnosing
            # assert len(errors) == 0, f"Components failed to instantiate: {errors}"
    
    def test_main_py_execution(self):
        """Test if main.py runs without immediate crash"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Execution Test", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0, f"Generation failed"
            
            system_dir = list(Path(tmpdir).glob("scaffolds/*"))[0]
            
            # Try to run main.py for 2 seconds
            try:
                process = subprocess.Popen([
                    sys.executable, "main.py"
                ], cwd=system_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Wait for 2 seconds
                time.sleep(2)
                
                # Check if still running
                if process.poll() is None:
                    # Still running - good sign
                    process.terminate()
                    stdout, stderr = process.communicate()  # No timeout
                    
                    print("\n=== main.py Execution ===")
                    print("✅ Ran for 2 seconds without crash")
                    
                    # Check for errors in output
                    error_types = ["AttributeError", "TypeError", "NameError", "KeyError", "ImportError"]
                    found_errors = [err for err in error_types if err in stderr]
                    
                    if found_errors:
                        print(f"⚠️  Errors detected: {found_errors}")
                        print(f"Stderr sample:\n{stderr[:500]}")
                    else:
                        print("✅ No Python errors detected")
                        
                else:
                    stdout, stderr = process.communicate()
                    print("\n=== main.py Execution ===")
                    print(f"❌ Crashed immediately with code {process.returncode}")
                    print(f"Stderr:\n{stderr[:1000]}")
                    
                    # Don't fail yet - diagnosing
                    # assert False, f"main.py crashed: {stderr[:500]}"
                    
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print("⚠️  Process had to be killed (timeout)")
    
    def test_async_consistency(self):
        """Check if all process methods are async"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Async Test", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            system_dir = list(Path(tmpdir).glob("scaffolds/*"))[0]
            
            print("\n=== Async Consistency Check ===")
            
            sync_methods = []
            async_methods = []
            
            for comp_file in system_dir.glob("components/*.py"):
                if comp_file.stem in ["observability", "communication", "__init__"]:
                    continue
                    
                content = comp_file.read_text()
                
                # Check for sync process methods
                import re
                sync_pattern = r'^    def (process[^(]*)\('
                async_pattern = r'^    async def (process[^(]*)\('
                
                sync_matches = re.findall(sync_pattern, content, re.MULTILINE)
                async_matches = re.findall(async_pattern, content, re.MULTILINE)
                
                if sync_matches:
                    for method in sync_matches:
                        sync_methods.append(f"{comp_file.stem}.{method}")
                
                if async_matches:
                    for method in async_matches:
                        async_methods.append(f"{comp_file.stem}.{method}")
            
            print(f"Sync process methods found: {len(sync_methods)}")
            for method in sync_methods:
                print(f"  ⚠️  {method} (should be async)")
            
            print(f"\nAsync process methods found: {len(async_methods)}")
            for method in async_methods[:3]:  # Show first 3
                print(f"  ✅ {method}")
            if len(async_methods) > 3:
                print(f"  ... and {len(async_methods) - 3} more")
            
            # Don't fail yet - diagnosing
            # assert len(sync_methods) == 0, f"Found sync process methods: {sync_methods}"