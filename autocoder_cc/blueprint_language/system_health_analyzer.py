#!/usr/bin/env python3
"""Analyze health of all generated systems to identify common issues"""
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class SystemHealthAnalyzer:
    """Analyzes generated systems to identify validation issues"""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = {
            'total_systems': 0,
            'total_components': 0,
            'import_failures': 0,
            'ast_failures': 0,
            'missing_cleanup': 0,
            'validation_passed': 0
        }
    
    def analyze_all_systems(self, systems_dir: Path = Path('generated_systems')) -> Dict:
        """Analyze all systems and return comprehensive report"""
        for system_dir in sorted(systems_dir.iterdir()):
            if system_dir.is_dir() and system_dir.name.startswith('system_'):
                self.stats['total_systems'] += 1
                self._analyze_system(system_dir)
        
        return {
            'statistics': self.stats,
            'issues_by_type': dict(self.issues),
            'success_rate': self._calculate_success_rate()
        }
    
    def _analyze_system(self, system_dir: Path):
        """Analyze a single system"""
        components_dirs = list(system_dir.glob('**/components'))
        if not components_dirs:
            return
        
        components_dir = components_dirs[0]
        
        for component_file in components_dir.glob('*.py'):
            if component_file.name in ['__init__.py', 'observability.py', 'communication.py']:
                continue
                
            self.stats['total_components'] += 1
            self._analyze_component(component_file)
    
    def _analyze_component(self, component_file: Path):
        """Analyze a single component for issues"""
        # Check import issues
        if not self._check_imports(component_file):
            self.stats['import_failures'] += 1
            self.issues['import_path'].append(str(component_file))
        
        # Check AST parsing
        if not self._check_ast_parsing(component_file):
            self.stats['ast_failures'] += 1
            self.issues['ast_syntax'].append(str(component_file))
        
        # Check lifecycle methods
        if not self._check_lifecycle_methods(component_file):
            self.stats['missing_cleanup'] += 1
            self.issues['missing_cleanup'].append(str(component_file))
    
    def _check_imports(self, component_file: Path) -> bool:
        """Check if imports can be resolved"""
        try:
            code = component_file.read_text()
            # Check if observability module exists
            obs_path = component_file.parent / 'observability.py'
            if 'from observability import' in code and not obs_path.exists():
                return False
            
            # Check for autocoder vs autocoder_cc
            if 'from autocoder.' in code:
                return False
                
            return True
        except Exception:
            return False
    
    def _check_ast_parsing(self, component_file: Path) -> bool:
        """Check if AST can parse the file"""
        try:
            code = component_file.read_text()
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    def _check_lifecycle_methods(self, component_file: Path) -> bool:
        """Check if component has required lifecycle methods"""
        try:
            code = component_file.read_text()
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
                    # Check for cleanup method
                    if 'cleanup' not in methods and 'ComposedComponent' in code:
                        return False
            return True
        except Exception:
            return True  # Don't fail if we can't parse
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.stats['total_components'] == 0:
            return 0.0
        
        failed = (self.stats['import_failures'] + 
                 self.stats['ast_failures'] + 
                 self.stats['missing_cleanup'])
        
        success = self.stats['total_components'] - failed
        return (success / self.stats['total_components']) * 100

    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "="*60)
        print("SYSTEM HEALTH ANALYSIS REPORT")
        print("="*60)
        
        stats = report['statistics']
        print(f"\nSystems analyzed: {stats['total_systems']}")
        print(f"Components analyzed: {stats['total_components']}")
        print(f"\nIssue Breakdown:")
        print(f"  Import failures: {stats['import_failures']} ({stats['import_failures']/max(stats['total_components'],1)*100:.1f}%)")
        print(f"  AST parse failures: {stats['ast_failures']} ({stats['ast_failures']/max(stats['total_components'],1)*100:.1f}%)")
        print(f"  Missing cleanup(): {stats['missing_cleanup']} ({stats['missing_cleanup']/max(stats['total_components'],1)*100:.1f}%)")
        print(f"\nEstimated success rate: {report['success_rate']:.1f}%")
        
        if report['issues_by_type']:
            print("\nTop Issues by Type:")
            for issue_type, files in report['issues_by_type'].items():
                print(f"\n{issue_type} ({len(files)} files):")
                for f in files[:3]:  # Show first 3
                    print(f"  - {f}")
                if len(files) > 3:
                    print(f"  ... and {len(files)-3} more")

if __name__ == '__main__':
    analyzer = SystemHealthAnalyzer()
    report = analyzer.analyze_all_systems()
    analyzer.print_report(report)
    
    # Save detailed report
    with open('system_health_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("\n✅ Detailed report saved to system_health_report.json")