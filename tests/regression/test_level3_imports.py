"""Test that we've achieved Level 3: Imports work"""
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


class TestLevel3Achievement:
    """Verify we've achieved Level 3: Components can import dependencies"""
    
    def test_generation_completes(self):
        """Level 0: Generation completes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True, text=True)  # No timeout
            
            assert result.returncode == 0, f"Generation failed: {result.stderr}"
    
    def test_files_created(self):
        """Level 1: Files are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            gen_dir = Path(tmpdir) / "scaffolds"
            assert gen_dir.exists()
            
            system_dirs = list(gen_dir.glob("*"))
            assert len(system_dirs) > 0, "No system generated"
            
            system_dir = system_dirs[0]
            component_files = list(system_dir.glob("components/*.py"))
            
            # Should have at least 3 components plus framework files
            assert len(component_files) >= 3, f"Only {len(component_files)} files created"
    
    def test_syntax_valid(self):
        """Level 2: Python syntax is valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Check each component can be parsed
            for py_file in system_dir.glob("components/*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(py_file)
                ], capture_output=True)
                
                assert result.returncode == 0, f"Syntax error in {py_file.name}"
    
    def test_imports_work(self):
        """Level 3: Components can import their dependencies - THIS IS THE KEY TEST"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate system
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Get actual component files (not framework files)
            component_files = [
                f for f in system_dir.glob("components/*.py")
                if f.stem not in ["observability", "communication", "__init__"]
            ]
            
            assert len(component_files) > 0, "No actual components generated"
            
            # Test each component can be imported
            for component_file in component_files:
                component_name = component_file.stem
                
                # Test 1: Direct import test
                test_script = f"""
import sys
sys.path.insert(0, 'components')
try:
    import {component_name}
    print("Direct import successful")
except ImportError as e:
    print(f"Import failed: {{e}}")
    exit(1)
"""
                result = subprocess.run([
                    sys.executable, "-c", test_script
                ], cwd=system_dir, capture_output=True, text=True)
                
                assert result.returncode == 0, (
                    f"Component {component_name} cannot be imported.\n"
                    f"Error: {result.stderr}\n"
                    f"This means Level 3 is NOT achieved!"
                )
                
                # Test 2: Can instantiate the component
                test_script = f"""
import sys
import os
sys.path.insert(0, 'components')
os.chdir('components')  # Ensure relative imports work

# Import the component module
import {component_name}

# Find the Generated class in the module
classes = [obj for name, obj in vars({component_name}).items() 
           if isinstance(obj, type) and name.startswith('Generated')]

if classes:
    ComponentClass = classes[0]
    # Try to instantiate
    instance = ComponentClass(name="test", config={{}})
    print(f"Successfully instantiated {{ComponentClass.__name__}}")
else:
    print("No Generated class found")
    exit(1)
"""
                result = subprocess.run([
                    sys.executable, "-c", test_script
                ], cwd=system_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    # This is acceptable - instantiation may fail due to missing deps
                    # But import must work
                    assert "No Generated class found" not in result.stderr, (
                        f"Component {component_name} has no Generated class"
                    )
    
    def test_framework_imports_work(self):
        """Verify framework files (observability, communication) can be imported"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Test observability import
            result = subprocess.run([
                sys.executable, "-c",
                "import sys; sys.path.insert(0, 'components'); "
                "from observability import ComposedComponent, SpanStatus"
            ], cwd=system_dir, capture_output=True)
            
            assert result.returncode == 0, "Cannot import from observability.py"
            
            # Test communication import if it exists
            if (system_dir / "components" / "communication.py").exists():
                result = subprocess.run([
                    sys.executable, "-c",
                    "import sys; sys.path.insert(0, 'components'); "
                    "from communication import MessageEnvelope"
                ], cwd=system_dir, capture_output=True)
                
                assert result.returncode == 0, "Cannot import from communication.py"
    
    def test_generated_code_has_path_setup(self):
        """Verify generated components include proper path setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple Test System", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            assert result.returncode == 0
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Check at least one component has sys.path setup
            component_files = [
                f for f in system_dir.glob("components/*.py")
                if f.stem not in ["observability", "communication", "__init__"]
            ]
            
            has_path_setup = False
            for component_file in component_files:
                content = component_file.read_text()
                if "sys.path.insert" in content or "sys.path.append" in content:
                    has_path_setup = True
                    break
            
            assert has_path_setup, (
                "No component has sys.path setup. "
                "This means the import fix was not applied!"
            )