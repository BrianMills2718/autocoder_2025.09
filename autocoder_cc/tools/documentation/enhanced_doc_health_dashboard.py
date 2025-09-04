#!/usr/bin/env python3
"""
Enhanced Documentation Health Dashboard

This tool provides comprehensive documentation health analysis including:
- Status tag validation against codebase
- Cross-reference checking
- Code example validation
- Coverage reporting
"""

import os
import re
import ast
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import argparse
import fnmatch  # new import

@dataclass
class DocHealthIssue:
    """Represents a documentation health issue"""
    file: str
    line: int
    issue_type: str
    severity: str
    description: str
    suggestion: str

@dataclass
class DocHealthReport:
    """Complete documentation health report"""
    timestamp: str
    total_files: int
    total_issues: int
    health_score: float
    issues: List[DocHealthIssue]
    statistics: Dict[str, Any]

class EnhancedDocHealthDashboard:
    """Enhanced documentation health analysis"""
    
    def __init__(self, repo_root: str = ".", config: Dict[str, Any] = None):
        self.repo_root = Path(repo_root)
        self.issues: List[DocHealthIssue] = []
        self.code_files: Set[str] = set()
        self.doc_files: Set[str] = set()
        self.config = config or {}
        # Precompile exclusion patterns
        self.exclude_patterns = self.config.get("exclude_paths", [])
        
    def scan_codebase(self) -> None:
        """Scan for all code files"""
        for root, dirs, files in os.walk(self.repo_root):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_root)
                    if self._is_excluded(rel_path):
                        continue
                    self.code_files.add(rel_path)
    
    def scan_documentation(self) -> None:
        """Scan for all documentation files"""
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith(('.md', '.rst', '.txt', '.yaml', '.yml')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_root)
                    if self._is_excluded(rel_path):
                        continue
                    self.doc_files.add(rel_path)
    
    def check_status_tags(self, file_path: str) -> None:
        """Check status tags against codebase"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Look for status tags
            status_patterns = self.config.get("status_tag_patterns", [
                r'✔️\s*(.*?)(?:\n|$)',
                r'✅\s*(.*?)(?:\n|$)',
                r'🚧\s*(.*?)(?:\n|$)',
                r'📋\s*(.*?)(?:\n|$)',
                r'❌\s*(.*?)(?:\n|$)',
                r'\[COMPLETE\]',
                r'\[ACTIVE\]',
                r'\[DEPRECATED\]'
            ])
            
            for line_num, line in enumerate(lines, 1):
                for pattern in status_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Check if the feature exists in codebase
                        if not self._feature_exists_in_codebase(match):
                            self.issues.append(DocHealthIssue(
                                file=file_path,
                                line=line_num,
                                issue_type="false_status_tag",
                                severity="HIGH",
                                description=f"Feature marked as complete but not found: {match}",
                                suggestion="Update status tag or implement the feature"
                            ))
        
        except Exception as e:
            self.issues.append(DocHealthIssue(
                file=file_path,
                line=0,
                issue_type="file_read_error",
                severity="MEDIUM",
                description=f"Could not read file: {str(e)}",
                suggestion="Check file permissions and encoding"
            ))
    
    def _feature_exists_in_codebase(self, feature_name: str) -> bool:
        """Check if a feature exists in the codebase"""
        # Simple heuristic: look for feature name in code files
        feature_lower = feature_name.lower()
        
        for code_file in self.code_files:
            if code_file.endswith('.py'):
                try:
                    with open(self.repo_root / code_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        if feature_lower in content:
                            return True
                except:
                    continue
        
        return False
    
    def check_code_examples(self, file_path: str) -> None:
        """Check code examples for syntax errors"""
        try:
            if self.config.get("ignore_md_syntax_errors", False):
                return  # skip check per config
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find code blocks
            code_block_pattern = r'```(?:python|bash|yaml|json)\n(.*?)```'
            matches = re.findall(code_block_pattern, content, re.DOTALL)
            
            for i, code_block in enumerate(matches):
                try:
                    # Try to parse as Python
                    ast.parse(code_block)
                except SyntaxError as e:
                    self.issues.append(DocHealthIssue(
                        file=file_path,
                        line=0,  # Would need more complex parsing to get exact line
                        issue_type="syntax_error",
                        severity="MEDIUM",
                        description=f"Syntax error in code example {i+1}: {str(e)}",
                        suggestion="Fix syntax error in code example"
                    ))
                except:
                    # Not Python code, skip
                    pass
        
        except Exception as e:
            self.issues.append(DocHealthIssue(
                file=file_path,
                line=0,
                issue_type="example_check_error",
                severity="LOW",
                description=f"Could not check code examples: {str(e)}",
                suggestion="Check file format and encoding"
            ))
    
    def check_cross_references(self, file_path: str) -> None:
        """Check cross-references between documents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown links
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, content)
            
            for link_text, link_target in matches:
                if link_target.startswith('http'):
                    continue  # External links
                
                # Remove anchor or query
                clean_target = link_target.split('#')[0].split('?')[0]
                if not clean_target:
                    continue
                # Resolve path relative to current file
                if clean_target.startswith('/'):
                    target_path = self.repo_root / clean_target.lstrip('/')
                else:
                    target_path = Path(file_path).parent / clean_target
                target_path = target_path.resolve()
                if self._is_excluded(str(target_path.relative_to(self.repo_root))):
                    continue
                if not target_path.exists():
                    self.issues.append(DocHealthIssue(
                        file=file_path,
                        line=0,
                        issue_type="broken_link",
                        severity="MEDIUM",
                        description=f"Broken link: {link_target}",
                        suggestion=f"Fix link or create missing file: {link_target}"
                    ))
        
        except Exception as e:
            self.issues.append(DocHealthIssue(
                file=file_path,
                line=0,
                issue_type="reference_check_error",
                severity="LOW",
                description=f"Could not check references: {str(e)}",
                suggestion="Check file format and encoding"
            ))
    
    def check_coverage(self) -> None:
        """Check documentation coverage"""
        # Check for missing README files in directories
        for code_file in self.code_files:
            code_dir = Path(code_file).parent
            readme_files = ['README.md', 'README.rst', 'README.txt']
            
            has_readme = any((self.repo_root / code_dir / readme).exists() for readme in readme_files)
            
            if not has_readme and code_dir != Path('.'):
                if self._is_excluded(str(code_dir)):
                    continue
                max_depth = self.config.get("require_readme_only_at_depth")
                if max_depth is not None:
                    depth = len(code_dir.parts)
                    if depth > max_depth:
                        continue  # ignore deep dirs
                self.issues.append(DocHealthIssue(
                    file=str(code_dir),
                    line=0,
                    issue_type="missing_readme",
                    severity="LOW",
                    description=f"Missing README file in {code_dir}",
                    suggestion=f"Add README.md to {code_dir}"
                ))
    
    def analyze_all(self) -> DocHealthReport:
        """Run complete documentation health analysis"""
        print("🔍 Scanning codebase...")
        self.scan_codebase()
        
        print("📚 Scanning documentation...")
        self.scan_documentation()
        
        print("🏷️ Checking status tags...")
        for doc_file in self.doc_files:
            if doc_file.endswith('.md'):
                self.check_status_tags(self.repo_root / doc_file)
        
        print("💻 Checking code examples...")
        for doc_file in self.doc_files:
            if doc_file.endswith('.md'):
                self.check_code_examples(self.repo_root / doc_file)
        
        print("🔗 Checking cross-references...")
        for doc_file in self.doc_files:
            if doc_file.endswith('.md'):
                self.check_cross_references(self.repo_root / doc_file)
        
        print("📊 Checking coverage...")
        self.check_coverage()
        
        # Calculate health score
        total_issues = len(self.issues)
        high_issues = len([i for i in self.issues if i.severity == "HIGH"])
        medium_issues = len([i for i in self.issues if i.severity == "MEDIUM"])
        low_issues = len([i for i in self.issues if i.severity == "LOW"])
        
        # Score calculation: 100 - (high*3 + medium*2 + low*1)
        health_score = max(0, 100 - (high_issues * 3 + medium_issues * 2 + low_issues))
        
        # Group issues by type
        issue_types = {}
        for issue in self.issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
        
        statistics = {
            "total_files": len(self.doc_files),
            "code_files": len(self.code_files),
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "low_issues": low_issues,
            "issue_types": issue_types
        }
        
        return DocHealthReport(
            timestamp=datetime.now().isoformat(),
            total_files=len(self.doc_files),
            total_issues=total_issues,
            health_score=health_score,
            issues=self.issues,
            statistics=statistics
        )
    
    def generate_report(self, report: DocHealthReport, output_file: str = None) -> str:
        """Generate formatted report"""
        report_text = f"""# Enhanced Documentation Health Dashboard
Generated: {report.timestamp}

## 📊 Summary
- Documentation Files: {report.total_files}
- Code Files: {report.statistics['code_files']}
- Total Issues: {report.total_issues}
- Health Score: {report.health_score:.1f}/100

## 🔴 High Priority Issues ({report.statistics['high_issues']})
"""
        
        high_issues = [i for i in report.issues if i.severity == "HIGH"]
        for issue in high_issues:
            report_text += f"- **{issue.file}:{issue.line}** - {issue.description}\n"
        
        report_text += f"""
## ⚠️ Medium Priority Issues ({report.statistics['medium_issues']})
"""
        
        medium_issues = [i for i in report.issues if i.severity == "MEDIUM"]
        for issue in medium_issues:
            report_text += f"- **{issue.file}:{issue.line}** - {issue.description}\n"
        
        report_text += f"""
## ℹ️ Low Priority Issues ({report.statistics['low_issues']})
"""
        
        low_issues = [i for i in report.issues if i.severity == "LOW"]
        for issue in low_issues:
            report_text += f"- **{issue.file}:{issue.line}** - {issue.description}\n"
        
        report_text += f"""
## 📈 Issue Breakdown
"""
        
        for issue_type, count in report.statistics['issue_types'].items():
            report_text += f"- {issue_type}: {count}\n"
        
        report_text += f"""
## 🎯 Recommendations
"""
        
        if report.statistics['high_issues'] > 0:
            report_text += "- **CRITICAL**: Fix all high priority issues immediately\n"
        if report.statistics['medium_issues'] > 0:
            report_text += "- **HIGH**: Address medium priority issues\n"
        if report.statistics['low_issues'] > 0:
            report_text += "- **MEDIUM**: Consider low priority issues\n"
        
        report_text += f"""
## 📝 Next Steps
1. Review and fix high priority issues
2. Update status tags to match actual implementation
3. Fix broken links and references
4. Add missing documentation
5. Validate all code examples

---
*Report generated by Enhanced Documentation Health Dashboard*
"""
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text

    def _is_excluded(self, rel_path: str) -> bool:
        """Check if a path matches any exclude pattern"""
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        return False

def main():
    parser = argparse.ArgumentParser(description="Enhanced Documentation Health Dashboard")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--json", help="Output JSON data to file")
    parser.add_argument("--config", help="Path to doc guard YAML config")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit with non-zero status if high priority issues found")
    
    args = parser.parse_args()
    
    # Load optional config
    config_data = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}

    dashboard = EnhancedDocHealthDashboard(args.repo_root, config_data)
    report = dashboard.analyze_all()
    
    # Generate text report
    report_text = dashboard.generate_report(report, args.output)
    
    if not args.output:
        print(report_text)
    
    # Generate JSON report
    if args.json:
        json_data = {
            "timestamp": report.timestamp,
            "total_files": report.total_files,
            "total_issues": report.total_issues,
            "health_score": report.health_score,
            "issues": [
                {
                    "file": str(issue.file),
                    "line": issue.line,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion
                }
                for issue in report.issues
            ],
            "statistics": report.statistics
        }
        
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
    
    print(f"✅ Analysis complete. Health score: {report.health_score:.1f}/100")

    if args.fail_on_critical and report.statistics['high_issues'] > 0:
        print("❌ High priority documentation issues detected. Failing pipeline.")
        exit(1)

if __name__ == "__main__":
    main() 