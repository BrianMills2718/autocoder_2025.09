"""Tests documenting current issues - these SHOULD FAIL initially"""
import subprocess
import sys
from pathlib import Path
import pytest
import tempfile

class TestCurrentLevel1State:
    """What currently works - these should PASS"""
    
    def test_generation_completes(self):
        """Level 0: Generation process completes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple API", "--output", tmpdir
            ], capture_output=True, text=True)  # No timeout
            
            assert result.returncode == 0, "Generation should complete"
            assert "error" not in result.stderr.lower() or "broken pipe" in result.stderr.lower()
    
    def test_files_created(self):
        """Level 1: Files are created with content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple API", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            # Find generated system
            gen_dir = Path(tmpdir) / "scaffolds"
            assert gen_dir.exists(), "Scaffolds directory should exist"
            
            system_dirs = list(gen_dir.glob("*"))
            assert len(system_dirs) > 0, "Should have generated system"
            
            # Check components exist
            components = list(system_dirs[0].glob("components/*.py"))
            assert len(components) >= 3, f"Should have 3+ components, got {len(components)}"

class TestCurrentFailures:
    """What's currently broken - these should FAIL"""
    
    @pytest.mark.xfail(reason="Import paths broken - Level 3 failure")
    def test_imports_work(self):
        """Level 3: Components can import dependencies"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple API", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Try to import - THIS WILL FAIL
            result = subprocess.run([
                sys.executable, "-c", 
                "from components.api_endpoint import *"
            ], cwd=system_dir, capture_output=True)
            
            assert result.returncode == 0, f"Import failed: {result.stderr}"
    
    @pytest.mark.xfail(reason="Execution blocked by imports - Level 4 failure")
    def test_system_runs(self):
        """Level 4: System can execute"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Simple API", "--output", tmpdir
            ], capture_output=True)  # No timeout
            
            gen_dir = Path(tmpdir) / "scaffolds"
            system_dir = list(gen_dir.glob("*"))[0]
            
            # Try to run - THIS WILL FAIL
            result = subprocess.run([
                sys.executable, "main.py"
            ], cwd=system_dir, capture_output=True)  # No timeout
            
            assert result.returncode == 0, f"Execution failed: {result.stderr}"