#!/usr/bin/env python3
"""Automatically fix import path issues in generated components"""
import ast
import re
from pathlib import Path
from typing import Optional, List, Tuple

class ImportAutoFixer:
    """Fixes common import path issues in generated components"""
    
    def fix_component_imports(self, component_file: Path) -> bool:
        """
        Fix imports in a component file.
        Returns True if fixes were applied, False otherwise.
        """
        try:
            original_code = component_file.read_text()
            fixed_code = original_code
            
            # Fix observability imports
            fixed_code = self._fix_observability_import(fixed_code, component_file)
            
            # Fix autocoder vs autocoder_cc
            fixed_code = self._fix_package_name(fixed_code)
            
            # Fix relative vs absolute imports
            fixed_code = self._fix_relative_imports(fixed_code, component_file)
            
            if fixed_code != original_code:
                # Backup original
                backup_path = component_file.with_suffix('.py.backup')
                backup_path.write_text(original_code)
                
                # Write fixed version
                component_file.write_text(fixed_code)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error fixing {component_file}: {e}")
            return False
    
    def _fix_observability_import(self, code: str, component_file: Path) -> str:
        """Fix observability module import based on actual file location"""
        obs_patterns = [
            r'from observability import (.+)',
            r'import observability'
        ]
        
        # Check where observability.py actually exists
        obs_in_same_dir = (component_file.parent / 'observability.py').exists()
        obs_in_parent = (component_file.parent.parent / 'observability.py').exists()
        obs_in_autocoder = Path('autocoder_cc/observability.py').exists()
        
        for pattern in obs_patterns:
            matches = re.findall(pattern, code)
            if matches:
                if obs_in_same_dir:
                    # Already correct
                    pass
                elif obs_in_parent:
                    # Need to go up one level
                    if isinstance(matches[0], str):
                        code = re.sub(pattern, r'from ..observability import \1', code)
                    else:
                        code = re.sub(pattern, r'from .. import observability', code)
                elif obs_in_autocoder:
                    # Use absolute import
                    if isinstance(matches[0], str):
                        code = re.sub(pattern, r'from autocoder_cc.observability import \1', code)
                    else:
                        code = re.sub(pattern, r'from autocoder_cc import observability', code)
        
        return code
    
    def _fix_package_name(self, code: str) -> str:
        """Fix autocoder vs autocoder_cc naming"""
        # Simple replacement - be careful not to break autocoder_cc
        code = re.sub(r'\bfrom autocoder\.', 'from autocoder_cc.', code)
        code = re.sub(r'\bimport autocoder\.', 'import autocoder_cc.', code)
        return code
    
    def _fix_relative_imports(self, code: str, component_file: Path) -> str:
        """Fix relative import issues"""
        # This is more complex and depends on project structure
        # For now, just ensure consistency
        return code
    
    def fix_all_components(self, systems_dir: Path = Path('generated_systems')) -> Tuple[int, int]:
        """
        Fix all components in generated systems.
        Returns (total_files, fixed_files)
        """
        total = 0
        fixed = 0
        
        for system_dir in systems_dir.iterdir():
            if system_dir.is_dir() and system_dir.name.startswith('system_'):
                components_dirs = list(system_dir.glob('**/components'))
                if components_dirs:
                    components_dir = components_dirs[0]
                    for component_file in components_dir.glob('*.py'):
                        if component_file.name not in ['__init__.py', 'observability.py', 'communication.py']:
                            total += 1
                            if self.fix_component_imports(component_file):
                                fixed += 1
                                print(f"✅ Fixed imports in {component_file}")
        
        return total, fixed

if __name__ == '__main__':
    fixer = ImportAutoFixer()
    total, fixed = fixer.fix_all_components()
    print(f"\n📊 Fixed {fixed}/{total} component files ({fixed/max(total,1)*100:.1f}%)")