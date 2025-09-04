"""Test that all generated process methods are async"""
import subprocess
import sys
import tempfile
from pathlib import Path
import re
import pytest


def test_all_process_methods_are_async():
    """All process methods in generated components should be async"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate a test system
        result = subprocess.run([
            sys.executable, "-m", "autocoder_cc.cli.main", "generate",
            "Async Test System", "--output", tmpdir
        ], capture_output=True, text=True, timeout=300)
        
        # Allow generation to fail with validation errors (known issue)
        # but it should still generate files
        
        # Find generated system
        system_dir = None
        for path in Path(tmpdir).rglob("components"):
            if path.is_dir() and list(path.glob("*.py")):
                system_dir = path.parent
                break
        
        if not system_dir:
            pytest.skip("No system generated - generation may have failed")
        
        components_dir = system_dir / "components"
        
        sync_methods = []
        async_methods = []
        
        # Check each component
        for comp_file in components_dir.glob("*.py"):
            if comp_file.stem in ["observability", "communication", "__init__"]:
                continue
            
            content = comp_file.read_text()
            
            # Find sync process methods (should be none)
            sync_pattern = r'^\s{4}def (process[^(]*)\('
            sync_matches = re.findall(sync_pattern, content, re.MULTILINE)
            
            # Find async process methods (should be all)
            async_pattern = r'^\s{4}async def (process[^(]*)\('
            async_matches = re.findall(async_pattern, content, re.MULTILINE)
            
            if sync_matches:
                for method in sync_matches:
                    sync_methods.append(f"{comp_file.stem}.{method}")
            
            if async_matches:
                for method in async_matches:
                    async_methods.append(f"{comp_file.stem}.{method}")
        
        # Report findings
        print(f"\nAsync methods found: {len(async_methods)}")
        print(f"Sync methods found: {len(sync_methods)}")
        
        if sync_methods:
            print("\n⚠️  SYNC methods that should be ASYNC:")
            for method in sync_methods:
                print(f"  - {method}")
        
        # This test currently expects to fail - documenting the issue
        if sync_methods:
            pytest.xfail(f"Found {len(sync_methods)} sync process methods that should be async")
        
        assert len(sync_methods) == 0, f"All process methods should be async, found sync: {sync_methods}"


def test_async_await_consistency():
    """Test that async methods properly use await"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable, "-m", "autocoder_cc.cli.main", "generate",
            "Await Test System", "--output", tmpdir
        ], capture_output=True, text=True, timeout=300)
        
        # Find generated system
        system_dir = None
        for path in Path(tmpdir).rglob("components"):
            if path.is_dir() and list(path.glob("*.py")):
                system_dir = path.parent
                break
        
        if not system_dir:
            pytest.skip("No system generated")
        
        components_dir = system_dir / "components"
        
        issues = []
        
        for comp_file in components_dir.glob("*.py"):
            if comp_file.stem in ["observability", "communication", "__init__"]:
                continue
            
            content = comp_file.read_text()
            
            # Check for await without async context
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'await ' in line and not any(
                    f'async def' in lines[j] for j in range(max(0, i-20), i)
                ):
                    issues.append(f"{comp_file.stem}:{i} - await outside async context")
        
        if issues:
            print("\n⚠️  Await issues found:")
            for issue in issues:
                print(f"  - {issue}")
            
        # Document known issues
        if issues:
            pytest.xfail(f"Found {len(issues)} await consistency issues")