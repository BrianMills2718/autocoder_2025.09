#!/usr/bin/env python3
"""
Comprehensive Validation Scanner for Enterprise Production Readiness
====================================================================

Implements evidence-based validation with automated hardcoded value scanning
using regex patterns and AST analysis as required by Cycle 21 validation.

This tool provides concrete evidence for production readiness claims by:
1. Automated scanning for hardcoded values (ports, URLs, paths, secrets)
2. AST-based validation instead of string matching
3. Comprehensive validation reports with file-by-file analysis
4. Integration-ready CI/CD pipeline validation
"""

import ast
import os
import re
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ValidationIssue:
    """Represents a validation issue found during scanning"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    pattern_matched: str
    suggested_fix: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report with metrics and issues"""
    scan_timestamp: str
    total_files_scanned: int
    total_issues_found: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    validation_score: float  # 0-100
    issues: List[ValidationIssue]
    whitelist_applied: bool
    scan_duration_seconds: float


class HardcodedValueDetector:
    """AST-based detector for hardcoded values in code"""
    
    def __init__(self, whitelist_config: Optional[Dict] = None):
        self.whitelist = whitelist_config or self._default_whitelist()
        self.issues = []
        
    def _default_whitelist(self) -> Dict:
        """Default whitelist for acceptable hardcoded values"""
        return {
            'allowed_ports': [22, 80, 443, 8080],  # Common standard ports
            'allowed_paths': ['/tmp', '/var/log', '__pycache__'],
            'allowed_strings': ['localhost', 'utf-8', 'application/json'],
            'version_patterns': [r'^\d+\.\d+\.\d+$', r'^v\d+\.\d+$'],
            'test_patterns': [r'test_.*', r'.*_test\.py$', r'conftest\.py$']
        }
    
    def scan_file(self, file_path: str) -> List[ValidationIssue]:
        """Scan a single file for hardcoded values using AST analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            visitor = HardcodedValueVisitor(file_path, self.whitelist)
            visitor.visit(tree)
            return visitor.issues
            
        except Exception as e:
            return [ValidationIssue(
                file_path=file_path,
                line_number=1,
                issue_type='scan_error',
                severity='medium',
                description=f"Failed to scan file: {str(e)}",
                pattern_matched="N/A"
            )]


class HardcodedValueVisitor(ast.NodeVisitor):
    """AST visitor for detecting hardcoded values"""
    
    def __init__(self, file_path: str, whitelist: Dict):
        self.file_path = file_path
        self.whitelist = whitelist
        self.issues = []
        
        # Regex patterns for different types of hardcoded values
        self.patterns = {
            'port': r'\b(?:port|PORT).*?(\d{2,5})\b',
            'url': r'https?://[^\s"\'\)]+',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'file_path': r'["\'](?:/[^"\']*|[A-Za-z]:\\[^"\']*)["\']',
            'database_connection': r'(?:postgresql|mysql|sqlite|mongodb)://[^\s"\']+',
            'api_key_pattern': r'(?:api[_-]?key|token|secret)["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
            'password_pattern': r'(?:password|pwd)["\']?\s*[:=]\s*["\'][^"\']+["\']',
            'hardcoded_credentials': r'(?:username|user)["\']?\s*[:=]\s*["\'][^"\']+["\']'
        }
    
    def visit_Constant(self, node):
        """Check constant values for hardcoded patterns"""
        if isinstance(node.value, (str, int)):
            self._check_constant_value(node, str(node.value))
        self.generic_visit(node)
    
    def visit_Str(self, node):
        """Check string literals (Python < 3.8 compatibility)"""
        self._check_constant_value(node, node.s)
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Check numeric literals (Python < 3.8 compatibility)"""
        self._check_constant_value(node, str(node.n))
        self.generic_visit(node)
    
    def _check_constant_value(self, node, value: str):
        """Check if a constant value matches hardcoded patterns"""
        # Skip if in test file
        if self._is_test_file():
            return
            
        # Check each pattern type
        for pattern_type, regex in self.patterns.items():
            matches = re.findall(regex, value, re.IGNORECASE)
            if matches:
                if not self._is_whitelisted(pattern_type, value, matches):
                    severity = self._get_severity(pattern_type)
                    self.issues.append(ValidationIssue(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        issue_type=f'hardcoded_{pattern_type}',
                        severity=severity,
                        description=f"Hardcoded {pattern_type} detected: {value}",
                        pattern_matched=regex,
                        suggested_fix=self._get_suggested_fix(pattern_type)
                    ))
    
    def _is_test_file(self) -> bool:
        """Check if current file is a test file"""
        test_indicators = ['test_', '_test.py', 'conftest.py', '/tests/', '/test/']
        return any(indicator in self.file_path.lower() for indicator in test_indicators)
    
    def _is_whitelisted(self, pattern_type: str, value: str, matches: List[str]) -> bool:
        """Check if value is in whitelist"""
        if pattern_type == 'port':
            try:
                port_nums = [int(match) for match in matches if match.isdigit()]
                return any(port in self.whitelist.get('allowed_ports', []) for port in port_nums)
            except (ValueError, TypeError):
                return False
        
        elif pattern_type in ['file_path', 'url']:
            allowed_paths = self.whitelist.get('allowed_paths', [])
            return any(allowed in value for allowed in allowed_paths)
        
        elif pattern_type in ['api_key_pattern', 'password_pattern']:
            # These should generally not be whitelisted
            return False
        
        # Check version patterns
        version_patterns = self.whitelist.get('version_patterns', [])
        for pattern in version_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _get_severity(self, pattern_type: str) -> str:
        """Get severity level for pattern type"""
        severity_map = {
            'api_key_pattern': 'critical',
            'password_pattern': 'critical', 
            'hardcoded_credentials': 'critical',
            'database_connection': 'high',
            'ip_address': 'high',
            'port': 'medium',
            'url': 'medium',
            'file_path': 'low'
        }
        return severity_map.get(pattern_type, 'medium')
    
    def _get_suggested_fix(self, pattern_type: str) -> str:
        """Get suggested fix for pattern type"""
        fixes = {
            'port': 'Move to environment variable or configuration file',
            'url': 'Use configuration management or environment variables',
            'ip_address': 'Use service discovery or configuration',
            'file_path': 'Use configurable paths or relative paths',
            'database_connection': 'Use environment variables for connection strings',
            'api_key_pattern': 'Move to secure environment variables',
            'password_pattern': 'Use secure credential management',
            'hardcoded_credentials': 'Implement proper authentication system'
        }
        return fixes.get(pattern_type, 'Move to configuration management')


class ComposedComponentValidator:
    """Validates exclusive use of ComposedComponent architecture"""
    
    def __init__(self):
        self.deprecated_patterns = [
            'UnifiedComponent',
            'from.*unified_base.*import',
            'class.*\\(UnifiedComponent\\)',
            'inherit.*UnifiedComponent'
        ]
    
    def scan_file(self, file_path: str) -> List[ValidationIssue]:
        """Scan file for deprecated component patterns"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.deprecated_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(ValidationIssue(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type='deprecated_component_pattern',
                            severity='high',
                            description=f"Deprecated component pattern found: {pattern}",
                            pattern_matched=pattern,
                            suggested_fix="Replace with ComposedComponent architecture"
                        ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=1,
                issue_type='component_scan_error',
                severity='medium',
                description=f"Failed to scan for component patterns: {str(e)}",
                pattern_matched="N/A"
            ))
        
        return issues


class ValidationScanner:
    """Main validation scanner orchestrator"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.hardcoded_detector = HardcodedValueDetector(self.config.get('whitelist'))
        self.component_validator = ComposedComponentValidator()
        self.logger = self._setup_logging()
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'include_patterns': ['*.py'],
            'exclude_patterns': ['*/__pycache__/*', '*/venv/*', '*/node_modules/*'],
            'whitelist': {}
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for validation scanner"""
        logger = get_logger('validation_scanner')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def scan_directory(self, root_path: str) -> ValidationReport:
        """Scan entire directory tree for validation issues"""
        start_time = datetime.now()
        self.logger.info(f"Starting validation scan of {root_path}")
        
        all_issues = []
        files_scanned = 0
        
        # Find all Python files to scan
        python_files = self._find_python_files(root_path)
        
        for file_path in python_files:
            try:
                # Scan for hardcoded values
                hardcoded_issues = self.hardcoded_detector.scan_file(file_path)
                all_issues.extend(hardcoded_issues)
                
                # Scan for component architecture compliance
                component_issues = self.component_validator.scan_file(file_path)
                all_issues.extend(component_issues)
                
                files_scanned += 1
                
                if files_scanned % 50 == 0:
                    self.logger.info(f"Scanned {files_scanned} files...")
                    
            except Exception as e:
                self.logger.error(f"Error scanning {file_path}: {str(e)}")
        
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        
        # Generate report
        report = self._generate_report(all_issues, files_scanned, scan_duration, start_time)
        self.logger.info(f"Scan complete. Found {len(all_issues)} issues in {files_scanned} files")
        
        return report
    
    def _find_python_files(self, root_path: str) -> List[str]:
        """Find all Python files to scan"""
        python_files = []
        root = Path(root_path)
        
        for file_path in root.rglob('*.py'):
            # Apply exclude patterns
            if self._should_exclude(str(file_path)):
                continue
            python_files.append(str(file_path))
        
        return python_files
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded from scanning"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.search(pattern.replace('*', '.*'), file_path):
                return True
        return False
    
    def _generate_report(self, issues: List[ValidationIssue], files_scanned: int, 
                        scan_duration: float, start_time: datetime) -> ValidationReport:
        """Generate comprehensive validation report"""
        
        # Calculate metrics
        issues_by_severity = {}
        issues_by_type = {}
        
        for issue in issues:
            severity = issue.severity
            issue_type = issue.issue_type
            
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        # Calculate validation score (0-100)
        critical_issues = issues_by_severity.get('critical', 0)
        high_issues = issues_by_severity.get('high', 0) 
        medium_issues = issues_by_severity.get('medium', 0)
        low_issues = issues_by_severity.get('low', 0)
        
        total_weighted_issues = (critical_issues * 10 + high_issues * 5 + 
                               medium_issues * 2 + low_issues * 1)
        max_possible_score = files_scanned * 10  # Assume max 1 critical issue per file
        
        if max_possible_score > 0:
            validation_score = max(0, 100 - (total_weighted_issues / max_possible_score * 100))
        else:
            validation_score = 100
        
        return ValidationReport(
            scan_timestamp=start_time.isoformat(),
            total_files_scanned=files_scanned,
            total_issues_found=len(issues),
            issues_by_severity=issues_by_severity,
            issues_by_type=issues_by_type,
            validation_score=round(validation_score, 2),
            issues=issues,
            whitelist_applied=bool(self.config.get('whitelist')),
            scan_duration_seconds=round(scan_duration, 2)
        )
    
    def export_report(self, report: ValidationReport, output_path: str, format_type: str = 'json'):
        """Export validation report in specified format"""
        if format_type == 'json':
            with open(output_path, 'w') as f:
                # Convert dataclasses to dict for JSON serialization
                report_dict = asdict(report)
                json.dump(report_dict, f, indent=2)
        
        elif format_type == 'html':
            self._export_html_report(report, output_path)
        
        elif format_type == 'csv':
            self._export_csv_report(report, output_path)
        
        self.logger.info(f"Report exported to {output_path}")
    
    def _export_html_report(self, report: ValidationReport, output_path: str):
        """Export HTML validation report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Validation Report - {report.scan_timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .critical {{ border-color: #d32f2f; background: #ffebee; }}
        .high {{ border-color: #f57c00; background: #fff3e0; }}
        .medium {{ border-color: #fbc02d; background: #fffde7; }}
        .low {{ border-color: #388e3c; background: #e8f5e8; }}
    </style>
</head>
<body>
    <h1>Validation Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Scan Time:</strong> {report.scan_timestamp}</p>
        <p><strong>Files Scanned:</strong> {report.total_files_scanned}</p>
        <p><strong>Total Issues:</strong> {report.total_issues_found}</p>
        <p><strong>Validation Score:</strong> {report.validation_score}/100</p>
        <p><strong>Scan Duration:</strong> {report.scan_duration_seconds}s</p>
    </div>
    
    <h2>Issues by Severity</h2>
    <ul>
"""
        for severity, count in report.issues_by_severity.items():
            html_content += f"        <li><strong>{severity.title()}:</strong> {count}</li>\n"
        
        html_content += "    </ul>\n\n    <h2>Detailed Issues</h2>\n"
        
        for issue in report.issues:
            css_class = issue.severity
            html_content += f"""
    <div class="issue {css_class}">
        <h3>{issue.issue_type} - {issue.severity.title()}</h3>
        <p><strong>File:</strong> {issue.file_path}:{issue.line_number}</p>
        <p><strong>Description:</strong> {issue.description}</p>
        <p><strong>Suggested Fix:</strong> {issue.suggested_fix or 'N/A'}</p>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _export_csv_report(self, report: ValidationReport, output_path: str):
        """Export CSV validation report"""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['File Path', 'Line Number', 'Issue Type', 'Severity', 
                           'Description', 'Pattern Matched', 'Suggested Fix'])
            
            for issue in report.issues:
                writer.writerow([
                    issue.file_path, issue.line_number, issue.issue_type,
                    issue.severity, issue.description, issue.pattern_matched,
                    issue.suggested_fix or ''
                ])


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Enterprise Validation Scanner')
    parser.add_argument('path', help='Path to scan for validation issues')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', default='validation_report.json', 
                       help='Output file path')
    parser.add_argument('--format', choices=['json', 'html', 'csv'], 
                       default='json', help='Output format')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        get_logger().setLevel(logging.DEBUG)
    
    # Initialize scanner
    scanner = ValidationScanner(args.config)
    
    # Perform scan
    report = scanner.scan_directory(args.path)
    
    # Export report
    scanner.export_report(report, args.output, args.format)
    
    # Print summary
    print(f"\nValidation Scan Complete")
    print(f"Files Scanned: {report.total_files_scanned}")
    print(f"Total Issues: {report.total_issues_found}")
    print(f"Validation Score: {report.validation_score}/100")
    print(f"Report exported to: {args.output}")
    
    # Return exit code based on critical issues
    critical_issues = report.issues_by_severity.get('critical', 0)
    if critical_issues > 0:
        print(f"ERROR: {critical_issues} critical issues found!")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())