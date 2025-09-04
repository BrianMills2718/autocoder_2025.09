#!/usr/bin/env python3
"""
Fix async/await issues in all generated components
"""
import ast
import astor
from pathlib import Path

def fix_async_issues(component_file: Path) -> bool:
    """Fix async issues in a component file"""
    try:
        with open(component_file, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        modified = False
        
        class AsyncFixer(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                # Make process_item async if it isn't
                if node.name == 'process_item' and not isinstance(node, ast.AsyncFunctionDef):
                    # Convert to async function
                    async_node = ast.AsyncFunctionDef(
                        name=node.name,
                        args=node.args,
                        body=node.body,
                        decorator_list=node.decorator_list,
                        returns=node.returns,
                        lineno=node.lineno,
                        col_offset=node.col_offset
                    )
                    nonlocal modified
                    modified = True
                    return async_node
                return node
        
        transformer = AsyncFixer()
        new_tree = transformer.visit(tree)
        
        if modified:
            new_code = astor.to_source(new_tree)
            with open(component_file, 'w') as f:
                f.write(new_code)
            print(f"✅ Fixed async issues in {component_file}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Failed to fix {component_file}: {e}")
        return False

def fix_all_components():
    """Fix all components in generated systems"""
    systems_dir = Path('generated_systems')
    fixed_count = 0
    
    for component_file in systems_dir.glob('**/components/*.py'):
        if component_file.name not in ['__init__.py', 'observability.py', 'communication.py']:
            if fix_async_issues(component_file):
                fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} component files")

if __name__ == '__main__':
    fix_all_components()