"""Test that import fix generates correct patterns"""
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest

def test_generated_imports_are_valid():
    """Components should generate with working imports"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate system
        result = subprocess.run([
            sys.executable, "-m", "autocoder_cc.cli.main", "generate",
            "Test API", "--output", tmpdir
        ], capture_output=True, text=True)  # No timeout
        
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        
        # Find generated component  
        gen_dir = Path(tmpdir) / "scaffolds"
        system_dir = list(gen_dir.glob("*"))[0]
        
        # Check if there are any component files
        component_files = list(system_dir.glob("components/*.py"))
        assert len(component_files) > 0, "No component files generated"
        
        # Check one of the components
        component_file = [f for f in component_files if 'api' in f.name.lower() or 'controller' in f.name.lower() or 'store' in f.name.lower()][0]
        
        # Check import pattern
        content = component_file.read_text()
        
        # After fix, components should have path setup
        assert ("sys.path.insert" in content or 
                "from .observability import" in content or
                content.startswith("# Shared module imports")), \
            "Should have path setup or use working import pattern"

def test_imports_actually_work():
    """Generated components should be importable"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate and test actual import
        result = subprocess.run([
            sys.executable, "-m", "autocoder_cc.cli.main", "generate",
            "Test API", "--output", tmpdir
        ], capture_output=True)  # No timeout
        
        assert result.returncode == 0, "Generation failed"
        
        gen_dir = Path(tmpdir) / "scaffolds"
        system_dir = list(gen_dir.glob("*"))[0]
        
        # Find an actual component that was generated
        component_files = [f.stem for f in system_dir.glob("components/*.py") 
                          if f.stem not in ["observability", "communication", "__init__"]]
        
        if component_files:
            component_name = component_files[0]
            
            # This should work after fix - try importing the actual component
            result = subprocess.run([
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, 'components'); from {component_name} import *"
            ], cwd=system_dir, capture_output=True)
            
            assert result.returncode == 0, f"Import still broken: {result.stderr.decode()}"