#!/usr/bin/env python3
"""
Config/Configuration Consistency Checker
========================================

Linting tool to prevent config/configuration field name inconsistencies
that could cause runtime errors in the autocoder system.

This tool checks for:
1. Use of 'config' instead of 'configuration' in LLM prompt templates
2. Conditional access patterns that indicate inconsistency workarounds
3. Model field name mismatches between related classes

Usage:
    python config_consistency_check.py [--fix] [--path PATH]
"""

import ast
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set

class ConfigConsistencyChecker:
    """Check for config/configuration field name inconsistencies"""
    
    def __init__(self):
        self.issues: List[Dict] = []
        self.fix_mode = False
    
    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a single Python file for config/configuration issues"""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check for problematic patterns
            issues.extend(self._check_prompt_templates(file_path, lines))
            issues.extend(self._check_conditional_access(file_path, lines))
            issues.extend(self._check_model_definitions(file_path, content))
            
        except Exception as e:
            issues.append({
                'file': str(file_path),
                'line': 0,
                'type': 'error',
                'message': f'Failed to process file: {e}'
            })
        
        return issues
    
    def _check_prompt_templates(self, file_path: Path, lines: List[str]) -> List[Dict]:
        """Check for 'config' field in LLM prompt templates where 'configuration' should be used"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Look for Jinja2 template definitions with config field
            if 'config:' in line and ('Dict[str, Any]' in line or '= {}' in line):
                # Check if this is in a template context (look for class definition)
                context_lines = lines[max(0, i-10):i+5]
                context = '\n'.join(context_lines)
                
                if 'BaseModel' in context or 'class.*Component' in '\n'.join(context_lines):
                    issues.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'inconsistency',
                        'message': 'LLM prompt template uses "config" field instead of "configuration"',
                        'suggestion': 'Replace "config:" with "configuration:" to match actual model definition'
                    })
        
        return issues
    
    def _check_conditional_access(self, file_path: Path, lines: List[str]) -> List[Dict]:
        """Check for conditional access patterns that indicate workarounds"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Look for .get('config', .get('configuration', patterns
            if ".get('config'" in line and ".get('configuration'" in line:
                issues.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'workaround',
                    'message': 'Found conditional access workaround for config/configuration inconsistency',
                    'suggestion': 'Standardize on "configuration" field name and remove workaround'
                })
            
            # Look for hasattr checks for both config and configuration
            if ('hasattr' in line and 'config' in line) or ('getattr' in line and 'config' in line):
                issues.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'potential_workaround',
                    'message': 'Potential config/configuration workaround pattern detected',
                    'suggestion': 'Verify this is not working around field name inconsistency'
                })
        
        return issues
    
    def _check_model_definitions(self, file_path: Path, content: str) -> List[Dict]:
        """Check Pydantic model definitions for config/configuration field consistency"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if this is a Pydantic model
                    is_pydantic = any(
                        isinstance(base, ast.Name) and base.id == 'BaseModel'
                        for base in node.bases
                    )
                    
                    if is_pydantic or 'Component' in node.name:
                        config_fields = []
                        
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                if field_name in ['config', 'configuration']:
                                    config_fields.append((field_name, item.lineno))
                        
                        # Check for inconsistent naming
                        if len(config_fields) > 1:
                            issues.append({
                                'file': str(file_path),
                                'line': config_fields[0][1],
                                'type': 'model_inconsistency',
                                'message': f'Model {node.name} has both config and configuration fields',
                                'suggestion': 'Standardize on "configuration" field name'
                            })
        
        except SyntaxError as e:
            issues.append({
                'file': str(file_path),
                'line': e.lineno or 0,
                'type': 'syntax_error',
                'message': f'Syntax error prevents analysis: {e}'
            })
        
        return issues
    
    def check_directory(self, directory: Path) -> List[Dict]:
        """Recursively check all Python files in a directory"""
        all_issues = []
        
        python_files = list(directory.glob('**/*.py'))
        
        for file_path in python_files:
            # Skip test files and generated systems
            if 'test_' in file_path.name or 'generated_systems' in str(file_path):
                continue
            
            issues = self.check_file(file_path)
            all_issues.extend(issues)
        
        return all_issues
    
    def fix_issues(self, issues: List[Dict]) -> int:
        """Attempt to automatically fix detected issues"""
        fixed_count = 0
        
        # Group issues by file
        by_file = {}
        for issue in issues:
            file_path = issue['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(issue)
        
        for file_path, file_issues in by_file.items():
            try:
                path = Path(file_path)
                content = path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Apply fixes (in reverse line order to preserve line numbers)
                file_issues.sort(key=lambda x: x['line'], reverse=True)
                
                for issue in file_issues:
                    if issue['type'] == 'inconsistency' and issue['line'] > 0:
                        line_idx = issue['line'] - 1
                        if line_idx < len(lines):
                            # Replace 'config:' with 'configuration:'
                            lines[line_idx] = lines[line_idx].replace('config:', 'configuration:')
                            fixed_count += 1
                
                # Write back the fixed content
                path.write_text('\n'.join(lines), encoding='utf-8')
                
            except Exception as e:
                print(f"Failed to fix issues in {file_path}: {e}", file=sys.stderr)
        
        return fixed_count
    
    def print_report(self, issues: List[Dict]):
        """Print a formatted report of issues"""
        if not issues:
            print("✅ No config/configuration consistency issues found!")
            return
        
        print(f"🚨 Found {len(issues)} config/configuration consistency issues:\n")
        
        # Group by type
        by_type = {}
        for issue in issues:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        for issue_type, type_issues in by_type.items():
            print(f"📋 {issue_type.replace('_', ' ').title()} ({len(type_issues)} issues):")
            
            for issue in type_issues:
                file_path = issue['file']
                line = issue['line']
                message = issue['message']
                suggestion = issue.get('suggestion', '')
                
                print(f"  📁 {file_path}:{line}")
                print(f"     ❌ {message}")
                if suggestion:
                    print(f"     💡 {suggestion}")
                print()


def main():
    parser = argparse.ArgumentParser(description='Check for config/configuration field name consistency')
    parser.add_argument('--fix', action='store_true', help='Automatically fix detected issues')
    parser.add_argument('--path', type=Path, default=Path.cwd(), help='Path to check (default: current directory)')
    parser.add_argument('--exit-code', action='store_true', help='Exit with error code if issues found')
    
    args = parser.parse_args()
    
    checker = ConfigConsistencyChecker()
    checker.fix_mode = args.fix
    
    print(f"🔍 Checking for config/configuration consistency in: {args.path}")
    print()
    
    if args.path.is_file():
        issues = checker.check_file(args.path)
    else:
        issues = checker.check_directory(args.path)
    
    if args.fix and issues:
        print("🔧 Attempting to fix issues...")
        fixed_count = checker.fix_issues(issues)
        print(f"✅ Fixed {fixed_count} issues automatically")
        print()
        
        # Re-check after fixes
        if args.path.is_file():
            issues = checker.check_file(args.path)
        else:
            issues = checker.check_directory(args.path)
    
    checker.print_report(issues)
    
    if args.exit_code and issues:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()