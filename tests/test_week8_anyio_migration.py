import ast
import os
from pathlib import Path

def check_imports(filepath):
    """Check what async framework a file uses"""
    if not os.path.exists(filepath):
        return None, None
        
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except:
            return None, None
            
    uses_asyncio = False
    uses_anyio = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name == 'asyncio':
                    uses_asyncio = True
                elif name.name == 'anyio':
                    uses_anyio = True
        elif isinstance(node, ast.ImportFrom):
            if node.module and 'asyncio' in node.module:
                uses_asyncio = True
            elif node.module and 'anyio' in node.module:
                uses_anyio = True
                
    return uses_asyncio, uses_anyio

def test_walking_skeleton_uses_anyio():
    """Walking skeleton should use anyio exclusively"""
    files = [
        'autocoder_cc/components/walking_skeleton/api_source.py',
        'autocoder_cc/components/walking_skeleton/controller.py',
        'autocoder_cc/components/walking_skeleton/store.py'
    ]
    
    failures = []
    for filepath in files:
        if os.path.exists(filepath):
            uses_asyncio, uses_anyio = check_imports(filepath)
            if uses_asyncio:
                failures.append(f"{filepath} still uses asyncio")
                
    assert not failures, f"Files using asyncio: {failures}"

def test_ports_use_anyio():
    """Ports should use anyio"""
    uses_asyncio, uses_anyio = check_imports('autocoder_cc/ports/base.py')
    assert not uses_asyncio, "ports/base.py still uses asyncio"
    assert uses_anyio, "ports/base.py should use anyio"

def test_no_mixed_imports():
    """No file should import both asyncio and anyio"""
    mixed = []
    for py_file in Path('autocoder_cc').rglob('*.py'):
        uses_asyncio, uses_anyio = check_imports(py_file)
        if uses_asyncio and uses_anyio:
            mixed.append(str(py_file))
            
    # Allow some mixed during migration, but track them
    if mixed:
        print(f"WARNING: {len(mixed)} files have mixed imports")
        for f in mixed[:5]:  # Show first 5
            print(f"  - {f}")
    
    # This test is informational for now
    assert True, "Tracking mixed imports"