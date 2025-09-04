#!/usr/bin/env python3
"""
Documentation Health Dashboard - Focused Edition

Scans the codebase for practical documentation issues:
- Link integrity (broken cross-references)
- Documentation coverage (missing docs for key features)
- Code example validation (do examples still work?)
- Architecture doc currency (are docs up to date with code?)
"""

import os
import re
import json
import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime

class DocumentationHealthDashboard:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.results = {
            "scan_timestamp": datetime.now().isoformat(),
            "summary": {},
            "link_issues": [],
            "coverage_gaps": [],
            "code_example_issues": [],
            "currency_issues": [],
            "recommendations": []
        }
        
        # Track what we find
        self.all_doc_files = set()
        self.all_code_files = set()
        self.all_directories = set()
        
    def scan_documentation(self, max_issues_per_category: int = 10) -> Dict[str, Any]:
        """Scan the codebase for documentation health issues.
        
        Args:
            max_issues_per_category: Maximum number of issues to report per category
        """
        
        print("Scanning documentation health...")
        
        # 1. Find all documentation files
        self._find_documentation_files()
        
        # 2. Find all code files and directories
        self._find_code_structure()
        
        # 3. Check link integrity
        self._check_link_integrity()
        
        # 4. Check documentation coverage
        self._check_documentation_coverage()
        
        # 5. Validate code examples
        self._validate_code_examples()
        
        # 6. Check architecture currency
        self._check_architecture_currency()
        
        # 7. Generate summary and recommendations
        self._generate_summary(max_issues_per_category)
        
        return self.results
    
    def _find_documentation_files(self):
        """Find all documentation files in the project."""
        doc_patterns = ["*.md", "*.rst", "*.txt", "README*", "CHANGELOG*"]
        
        for pattern in doc_patterns:
            for file_path in self.root_dir.rglob(pattern):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    # Skip archive directory
                    if 'archive' not in file_path.parts:
                        self.all_doc_files.add(file_path)
    
    def _find_code_structure(self):
        """Find all code files and directories."""
        # Find Python files
        for file_path in self.root_dir.rglob("*.py"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Skip archive directory
                if 'archive' not in file_path.parts:
                    self.all_code_files.add(file_path)
        
        # Find directories (for coverage checking)
        for item in self.root_dir.rglob("*"):
            if item.is_dir() and not item.name.startswith('.'):
                # Skip archive directory
                if 'archive' not in item.parts:
                    self.all_directories.add(item)
    
    def _check_link_integrity(self):
        """Check for broken markdown links."""
        print("Checking link integrity...")
        
        # Patterns for markdown links and images
        link_patterns = [
            r'\[([^\]]+)\]\(([^)]+)\)',  # [text](url)
            r'!\[([^\]]*)\]\(([^)]+)\)',  # ![alt](url)
        ]
        
        for doc_file in self.all_doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                for pattern in link_patterns:
                    for match in re.finditer(pattern, content):
                        link_text = match.group(1)
                        link_url = match.group(2)
                        
                        # Skip external links
                        if link_url.startswith(('http://', 'https://', 'mailto:')):
                            continue
                        
                        # Handle relative paths
                        if link_url.startswith('#'):
                            # Anchor link - check if it exists in the same file
                            anchor = link_url[1:]
                            anchor_found = False
                            
                            # Check for standard markdown headers
                            if re.search(rf'^#+\s+{re.escape(anchor)}', content, re.MULTILINE):
                                anchor_found = True
                            
                            # Check for explicit markdown anchor syntax {#anchor}
                            if f'{{#{anchor}}}' in content:
                                anchor_found = True
                            
                            # Check for HTML anchor tags
                            if f'<a name="{anchor}">' in content or f'<a name=\'{anchor}\'>' in content:
                                anchor_found = True
                            
                            if not anchor_found:
                                self.results["link_issues"].append({
                                    "file": str(doc_file.relative_to(self.root_dir)),
                                    "issue": f"Broken anchor link: {link_url}",
                                    "severity": "MEDIUM"
                                })
                        else:
                            # File link
                            target_path = doc_file.parent / link_url
                            if not target_path.exists():
                                self.results["link_issues"].append({
                                    "file": str(doc_file.relative_to(self.root_dir)),
                                    "issue": f"Broken link: {link_url}",
                                    "severity": "HIGH"
                                })
                                
            except Exception as e:
                self.results["link_issues"].append({
                    "file": str(doc_file.relative_to(self.root_dir)),
                    "issue": f"Error reading file: {str(e)}",
                    "severity": "HIGH"
                })
    
    def _check_documentation_coverage(self):
        """Check for missing documentation for key features."""
        print("Checking documentation coverage...")
        
        # Key directories that should have documentation
        key_dirs = [
            "autocoder_cc/autocoder",
            "autocoder_cc/blueprint_language", 
            "autocoder_cc/tools",
            "examples"
        ]
        
        for key_dir in key_dirs:
            dir_path = self.root_dir / key_dir
            if not dir_path.exists():
                continue
                
            # Check for README in key directories
            readme_files = list(dir_path.glob("README*"))
            if not readme_files:
                self.results["coverage_gaps"].append({
                    "directory": key_dir,
                    "issue": "Missing README file",
                    "severity": "MEDIUM"
                })
            
            # Check for corresponding docs for major modules
            if key_dir == "autocoder_cc/autocoder":
                # Check for docs about major autocoder modules
                major_modules = ["security", "components", "validation", "observability"]
                for module in major_modules:
                    module_path = dir_path / module
                    if module_path.exists():
                        # Check if module has its own README
                        module_readme = list(module_path.glob("README*"))
                        if not module_readme:
                            self.results["coverage_gaps"].append({
                                "directory": key_dir,
                                "issue": f"Missing README file for {module} module",
                                "severity": "LOW"
                            })
    
    def _validate_code_examples(self):
        """Validate code examples in documentation."""
        print("Validating code examples...")
        
        for doc_file in self.all_doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                # Find Python code blocks - only content between ```python and ```
                code_blocks = re.findall(r'```python\s*\n(.*?)\n```', content, re.DOTALL)
                
                for i, code_block in enumerate(code_blocks):
                    # Skip empty code blocks
                    if not code_block.strip():
                        continue
                    
                    # Skip blocks that contain non-ASCII characters (likely markdown content)
                    if any(ord(char) > 127 for char in code_block):
                        continue
                        
                    try:
                        # Basic syntax check
                        ast.parse(code_block)
                        
                        # Check for obvious import issues
                        import_lines = re.findall(r'^import\s+(\S+)', code_block, re.MULTILINE)
                        import_lines.extend(re.findall(r'^from\s+(\S+)\s+import', code_block, re.MULTILINE))
                        
                        for import_line in import_lines:
                            # Check if the import path makes sense
                            if import_line.startswith('autocoder'):
                                # Check if this module exists
                                module_path = self.root_dir / "autocoder_cc" / import_line.replace('.', '/')
                                if not any(module_path.glob("*.py")):
                                    self.results["code_example_issues"].append({
                                        "file": str(doc_file.relative_to(self.root_dir)),
                                        "issue": f"Example imports non-existent module: {import_line}",
                                        "severity": "MEDIUM"
                                    })
                                    
                    except SyntaxError as e:
                        self.results["code_example_issues"].append({
                            "file": str(doc_file.relative_to(self.root_dir)),
                            "issue": f"Syntax error in code example: {str(e)}",
                            "severity": "HIGH"
                        })
                        
            except Exception as e:
                self.results["code_example_issues"].append({
                    "file": str(doc_file.relative_to(self.root_dir)),
                    "issue": f"Error reading file: {str(e)}",
                    "severity": "HIGH"
                })
    
    def _check_architecture_currency(self):
        """Check if architecture docs are up to date with code."""
        print("Checking architecture currency...")
        
        # Check version consistency
        try:
            setup_py = self.root_dir / "autocoder_cc/setup.py"
            if setup_py.exists():
                setup_content = setup_py.read_text()
                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
                if version_match:
                    setup_version = version_match.group(1)
                    
                    # Check if docs mention the same version
                    for doc_file in self.all_doc_files:
                        try:
                            content = doc_file.read_text(encoding='utf-8')
                            if setup_version in content:
                                # Version mentioned in docs
                                pass  # This is good
                        except:
                            pass
        except:
            pass
        
        # Check if documented classes/functions exist in code
        for doc_file in self.all_doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                # Look for class/function mentions in code blocks only
                code_blocks = re.findall(r'```python\s*\n(.*?)\n```', content, re.DOTALL)
                
                for code_block in code_blocks:
                    # Look for actual class definitions in code blocks
                    class_mentions = re.findall(r'^class\s+(\w+)', code_block, re.MULTILINE)
                    function_mentions = re.findall(r'^def\s+(\w+)', code_block, re.MULTILINE)
                    
                    for class_name in class_mentions:
                        # Skip common Python built-ins and obvious non-classes
                        if class_name in ['DocumentationHealthDashboard', 'str', 'int', 'list', 'dict', 'bool', 'float']:
                            continue
                        
                        # Check if this class is marked as an example
                        # Look for example markers in the code block or in the surrounding context
                        example_markers = [
                            '# NOTE: This is an example class for documentation purposes only',
                            '# Example class for documentation',
                            '# This is an example',
                            '# Example:',
                            '# NOTE: Example',
                            '# NOTE: These are example classes for documentation purposes only'
                        ]
                        
                        # Check both the current code block and the surrounding content
                        is_example = any(marker in code_block for marker in example_markers)
                        
                        # Also check if there's a comment right before the class definition
                        class_pattern = rf'^class\s+{re.escape(class_name)}'
                        class_match = re.search(class_pattern, code_block, re.MULTILINE)
                        if class_match:
                            # Get the lines before this class definition
                            lines_before = code_block[:class_match.start()].split('\n')
                            # Check if any of the last few lines contain example markers
                            for line in lines_before[-5:]:  # Check last 5 lines
                                if any(marker in line for marker in example_markers):
                                    is_example = True
                                    break
                        
                        if is_example:
                            continue  # Skip example classes
                            
                        # Check if this class exists in the codebase
                        found = False
                        for code_file in self.all_code_files:
                            try:
                                code_content = code_file.read_text(encoding='utf-8')
                                if f"class {class_name}" in code_content:
                                    found = True
                                    break
                            except:
                                continue
                        
                        if not found:
                            self.results["currency_issues"].append({
                                "file": str(doc_file.relative_to(self.root_dir)),
                                "issue": f"Documented class '{class_name}' not found in codebase",
                                "severity": "MEDIUM"
                            })
                        
            except Exception as e:
                self.results["currency_issues"].append({
                    "file": str(doc_file.relative_to(self.root_dir)),
                    "issue": f"Error reading file: {str(e)}",
                    "severity": "HIGH"
                })
    
    def _generate_summary(self, max_issues_per_category: int = 10):
        """Generate summary statistics and recommendations.
        
        Args:
            max_issues_per_category: Maximum number of issues to report per category
        """
        # Limit issues per category for readability
        for issue_type in ["link_issues", "coverage_gaps", "code_example_issues", "currency_issues"]:
            if len(self.results[issue_type]) > max_issues_per_category:
                self.results[issue_type] = self.results[issue_type][:max_issues_per_category]
        
        total_issues = (
            len(self.results["link_issues"]) +
            len(self.results["coverage_gaps"]) +
            len(self.results["code_example_issues"]) +
            len(self.results["currency_issues"])
        )
        
        self.results["summary"] = {
            "total_doc_files": len(self.all_doc_files),
            "total_code_files": len(self.all_code_files),
            "link_issues": len(self.results["link_issues"]),
            "coverage_gaps": len(self.results["coverage_gaps"]),
            "code_example_issues": len(self.results["code_example_issues"]),
            "currency_issues": len(self.results["currency_issues"]),
            "total_issues": total_issues
        }
        
        # Calculate health score after summary is set
        self.results["summary"]["health_score"] = self._calculate_health_score()
        
        # Generate recommendations
        if self.results["link_issues"]:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "action": f"Fix {len(self.results['link_issues'])} broken links",
                "description": "Broken links create poor user experience"
            })
            
        if self.results["code_example_issues"]:
            self.results["recommendations"].append({
                "priority": "HIGH", 
                "action": f"Fix {len(self.results['code_example_issues'])} code example issues",
                "description": "Broken examples mislead users"
            })
            
        if self.results["coverage_gaps"]:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "action": f"Add documentation for {len(self.results['coverage_gaps'])} gaps",
                "description": "Missing docs make the system harder to understand"
            })
            
        if self.results["currency_issues"]:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "action": f"Update {len(self.results['currency_issues'])} outdated references",
                "description": "Outdated docs can mislead developers"
            })
        
        # Add general recommendations for documentation quality
        if self.results["summary"]["health_score"] >= 90:
            self.results["recommendations"].append({
                "priority": "LOW",
                "action": "Consider adding more detailed docstrings to complex functions",
                "description": "High-quality docstrings improve code maintainability"
            })
        elif self.results["summary"]["health_score"] < 70:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "action": "Review and improve overall documentation quality",
                "description": "Low documentation health indicates significant gaps"
            })
    
    def _calculate_health_score(self) -> int:
        """Calculate overall documentation health score (0-100)."""
        summary = self.results["summary"]
        
        if summary["total_doc_files"] == 0:
            return 0
            
        # Start with perfect score
        score = 100
        
        # Penalties for issues
        score -= len(self.results["link_issues"]) * 5  # Broken links are bad
        score -= len(self.results["code_example_issues"]) * 8  # Broken examples are worse
        score -= len(self.results["coverage_gaps"]) * 3  # Missing docs
        score -= len(self.results["currency_issues"]) * 2  # Outdated docs
        
        return max(0, min(100, score))
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a formatted report."""
        if not self.results["summary"]:
            self.scan_documentation()
        
        report_lines = [
            "# Documentation Health Dashboard - Focused Edition",
            f"Generated: {self.results['scan_timestamp']}",
            "",
            "> **Note**: This is an auto-generated report from the DocumentationHealthDashboard tool. ",
            "> For comprehensive documentation about this tool and other documentation utilities, ",
            "> see the tooling documentation in `autocoder_cc/tools/documentation/`.",
            "",
            "## Summary",
            f"- Documentation Files: {self.results['summary']['total_doc_files']}",
            f"- Code Files: {self.results['summary']['total_code_files']}",
            f"- Link Issues: {self.results['summary']['link_issues']}",
            f"- Coverage Gaps: {self.results['summary']['coverage_gaps']}",
            f"- Code Example Issues: {self.results['summary']['code_example_issues']}",
            f"- Currency Issues: {self.results['summary']['currency_issues']}",
            f"- Total Issues: {self.results['summary']['total_issues']}",
            f"- Health Score: {self.results['summary']['health_score']}/100",
            "",
        ]
        
        # Link Issues
        if self.results["link_issues"]:
            report_lines.extend([
                "## 🔗 Link Issues",
                "| File | Issue | Severity |",
                "|------|-------|----------|",
            ])
            for issue in self.results["link_issues"][:10]:  # Limit to top 10
                report_lines.append(f"| {issue['file']} | {issue['issue']} | {issue['severity']} |")
        else:
            report_lines.append("## 🔗 Link Issues\n- No broken links found ✓")
        
        # Coverage Gaps
        if self.results["coverage_gaps"]:
            report_lines.extend([
                "",
                "## 📚 Coverage Gaps",
                "| Directory | Issue | Severity |",
                "|-----------|-------|----------|",
            ])
            for gap in self.results["coverage_gaps"]:
                report_lines.append(f"| {gap['directory']} | {gap['issue']} | {gap['severity']} |")
        else:
            report_lines.append("\n## 📚 Coverage Gaps\n- No coverage gaps found ✓")
        
        # Code Example Issues
        if self.results["code_example_issues"]:
            report_lines.extend([
                "",
                "## 💻 Code Example Issues",
                "| File | Issue | Severity |",
                "|------|-------|----------|",
            ])
            for issue in self.results["code_example_issues"][:10]:  # Limit to top 10
                report_lines.append(f"| {issue['file']} | {issue['issue']} | {issue['severity']} |")
        else:
            report_lines.append("\n## 💻 Code Example Issues\n- No code example issues found ✓")
        
        # Currency Issues
        if self.results["currency_issues"]:
            report_lines.extend([
                "",
                "## 🔄 Currency Issues",
                "| File | Issue | Severity |",
                "|------|-------|----------|",
            ])
            for issue in self.results["currency_issues"][:10]:  # Limit to top 10
                report_lines.append(f"| {issue['file']} | {issue['issue']} | {issue['severity']} |")
        else:
            report_lines.append("\n## 🔄 Currency Issues\n- No currency issues found ✓")
        
        # Recommendations
        if self.results["recommendations"]:
            report_lines.extend([
                "",
                "## 📋 Recommendations",
            ])
            for rec in self.results["recommendations"]:
                report_lines.append(f"- **{rec['priority']}**: {rec['action']}")
                report_lines.append(f"  - {rec['description']}")
        else:
            report_lines.append("\n## 📋 Recommendations\n- No recommendations - documentation looks healthy! ✓")
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
                
        return report

def main():
    """Main entry point for the documentation health dashboard.
    
    This tool scans a codebase for documentation health issues including:
    - Broken links in markdown files
    - Missing documentation for key modules
    - Code example validation
    - Architecture currency checks
    
    The tool generates a comprehensive report with health scoring and recommendations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Health Dashboard - Scans codebase for documentation issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python doc_health_dashboard.py                    # Scan current directory
  python doc_health_dashboard.py --root-dir /path   # Scan specific directory
  python doc_health_dashboard.py --output report.md # Save report to file
  python doc_health_dashboard.py --json data.json   # Save JSON data
        """
    )
    parser.add_argument("--root-dir", default=".", help="Root directory to scan (default: current directory)")
    parser.add_argument("--output", help="Output file for the markdown report")
    parser.add_argument("--json", help="Output JSON data to file")
    parser.add_argument("--max-issues", type=int, default=10, help="Maximum issues per category (default: 10)")
    
    args = parser.parse_args()
    
    dashboard = DocumentationHealthDashboard(args.root_dir)
    results = dashboard.scan_documentation(max_issues_per_category=args.max_issues)
    
    # Generate report
    report = dashboard.generate_report()
    print(report)
    
    # Save report to file if specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        # Default behavior - save to standard files
        dashboard.generate_report("docs_health_report.md")
        with open("docs_health_data.json", 'w') as f:
            json.dump(results, f, indent=2)
        print("Reports saved to docs_health_report.md and docs_health_data.json")
    
    # Save JSON data if specified
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"JSON data saved to: {args.json}")
    
    # Exit with error code if there are issues
    if results["summary"]["total_issues"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main() 