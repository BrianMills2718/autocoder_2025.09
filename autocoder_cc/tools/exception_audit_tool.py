"""
Production-Grade Exception Audit Tool with Advanced AST Analysis

Performs comprehensive semantic analysis of exception handling patterns
across the entire codebase, identifying violations and generating fixes.
"""

import ast
import logging
import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import sys


@dataclass
class ExceptionViolation:
    """Specific exception handling violation"""
    file_path: Path
    line_number: int
    violation_type: str  # generic_except, bare_except, missing_context, etc.
    current_code: str
    suggested_fix: str
    severity: str  # error, warning, info
    confidence: float  # 0.0 to 1.0
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class AuditResult:
    """Complete audit results for the codebase"""
    total_files: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    files_with_violations: List[Dict[str, Any]]
    suggested_fixes: List[Dict[str, Any]]
    audit_timestamp: str
    total_violations: int
    confidence_score: float
    patterns_detected: Dict[str, int]


class SemanticExceptionAnalyzer(ast.NodeVisitor):
    """Advanced AST-based exception analysis with semantic understanding"""
    
    def __init__(self, file_path: Path, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.violations: List[ExceptionViolation] = []
        self.current_function = None
        self.current_class = None
        self.import_names = set()
        self.logger_imports = set()
        self.function_stack = []
        self.class_stack = []
        
        # Exception handling patterns to detect
        self.logging_patterns = {
            'logger.error', 'logger.warning', 'logger.exception', 'logger.critical',
            'logging.error', 'logging.warning', 'logging.exception', 'logging.critical',
            'log.error', 'log.warning', 'log.exception', 'log.critical',
            'print'  # Basic logging
        }
        
        # Common exception types that should be specific
        self.specific_exceptions = {
            'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'FileNotFoundError', 'IOError', 'OSError', 'ConnectionError',
            'TimeoutError', 'RuntimeError', 'ImportError', 'ModuleNotFoundError'
        }
    
    def visit_Import(self, node: ast.Import):
        """Track imports for context-aware analysis"""
        for alias in node.names:
            self.import_names.add(alias.name)
            if alias.name in ['logging', 'logger']:
                self.logger_imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from imports"""
        if node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                self.import_names.add(full_name)
                if 'logging' in node.module.lower():
                    self.logger_imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class for context"""
        self.class_stack.append(self.current_class)
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = self.class_stack.pop()
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track current function for context"""
        self.function_stack.append(self.current_function)
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = self.function_stack.pop()
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Track async functions for context"""
        self.function_stack.append(self.current_function)
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = self.function_stack.pop()
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Analyze exception handlers for violations"""
        
        # Check for bare except
        if node.type is None:
            self._add_violation(
                node.lineno,
                "bare_except",
                self._get_source_line(node.lineno),
                "Replace bare 'except:' with specific exception types like 'except (ValueError, TypeError) as e:'",
                "error",
                1.0,
                context={"handler_body_length": len(node.body)}
            )
        
        # Check for generic Exception catch
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            # Determine severity based on context
            severity = "warning"
            confidence = 0.9
            
            # If in a very high-level function, Exception might be acceptable
            if self.current_function and self.current_function in ['main', '__main__', 'run', 'execute']:
                severity = "info"
                confidence = 0.6
            
            self._add_violation(
                node.lineno,
                "generic_exception",
                self._get_source_line(node.lineno),
                f"Replace 'except Exception:' with specific exceptions. Consider: {', '.join(list(self.specific_exceptions)[:3])}",
                severity,
                confidence,
                context={"alternatives": list(self.specific_exceptions)[:5]}
            )
        
        # Check for overly broad exception catching
        elif isinstance(node.type, ast.Tuple):
            exception_names = []
            for elt in node.type.elts:
                if isinstance(elt, ast.Name):
                    exception_names.append(elt.id)
            
            if len(exception_names) > 5:
                self._add_violation(
                    node.lineno,
                    "overly_broad_except",
                    self._get_source_line(node.lineno),
                    f"Catching too many exception types ({len(exception_names)}). Consider separate handlers or more specific exceptions",
                    "info",
                    0.8,
                    context={"exception_count": len(exception_names), "exceptions": exception_names}
                )
        
        # Check for missing exception context
        if not self._has_proper_error_handling(node):
            severity = "warning"
            confidence = 0.8
            
            # More lenient for pass statements in certain contexts
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                severity = "info"
                confidence = 0.6
            
            suggestion = self._generate_context_suggestion(node)
            
            self._add_violation(
                node.lineno,
                "missing_error_context",
                self._get_source_line(node.lineno),
                suggestion,
                severity,
                confidence,
                context={"has_variable": node.name is not None, "body_statements": len(node.body)}
            )
        
        # Check for swallowed exceptions
        if self._is_exception_swallowed(node):
            self._add_violation(
                node.lineno,
                "swallowed_exception",
                self._get_source_line(node.lineno),
                "Exception is caught but not logged or re-raised. Add logging or re-raise with context",
                "warning",
                0.9,
                context={"body_type": "pass_only"}
            )
        
        self.generic_visit(node)
    
    def _has_proper_error_handling(self, except_node: ast.ExceptHandler) -> bool:
        """Check if exception handler has proper error handling"""
        
        for stmt in except_node.body:
            # Check for logging calls
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if self._is_logging_call(stmt.value):
                    return True
            
            # Check for re-raising
            elif isinstance(stmt, ast.Raise):
                return True
            
            # Check for return statements (acceptable in some contexts)
            elif isinstance(stmt, ast.Return):
                return True
            
            # Check for assignments that might store error info
            elif isinstance(stmt, ast.Assign):
                return True
        
        return False
    
    def _is_logging_call(self, call_node: ast.Call) -> bool:
        """Check if a call is a logging operation"""
        
        if isinstance(call_node.func, ast.Attribute):
            # logger.error(), logging.error(), etc.
            attr_name = call_node.func.attr
            if attr_name in ['error', 'warning', 'exception', 'critical', 'info', 'debug']:
                if isinstance(call_node.func.value, ast.Name):
                    obj_name = call_node.func.value.id
                    return obj_name in self.logger_imports or obj_name in ['logger', 'logging', 'log']
        
        elif isinstance(call_node.func, ast.Name):
            # print() calls
            return call_node.func.id == 'print'
        
        return False
    
    def _is_exception_swallowed(self, except_node: ast.ExceptHandler) -> bool:
        """Check if exception is completely swallowed"""
        
        # Empty body or only pass statement
        if not except_node.body:
            return True
        
        if len(except_node.body) == 1 and isinstance(except_node.body[0], ast.Pass):
            return True
        
        # Check if all statements are just comments (docstrings)
        non_comment_statements = []
        for stmt in except_node.body:
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)):
                non_comment_statements.append(stmt)
        
        return len(non_comment_statements) == 0
    
    def _generate_context_suggestion(self, except_node: ast.ExceptHandler) -> str:
        """Generate context-appropriate suggestion for exception handling"""
        
        variable_name = except_node.name or "e"
        function_context = f" in {self.current_function}" if self.current_function else ""
        
        if self.logger_imports:
            logger_name = next(iter(self.logger_imports))
            return f"Add logging: {logger_name}.error(f'Error{function_context}: {{{variable_name}}}')"
        else:
            return f"Add error context: print(f'Error{function_context}: {{{variable_name}}}') or re-raise with 'raise'"
    
    def _add_violation(self, line_number: int, violation_type: str, 
                      current_code: str, suggested_fix: str, 
                      severity: str, confidence: float,
                      context: Optional[Dict[str, Any]] = None):
        """Add a violation to the list"""
        self.violations.append(ExceptionViolation(
            file_path=self.file_path,
            line_number=line_number,
            violation_type=violation_type,
            current_code=current_code.strip(),
            suggested_fix=suggested_fix,
            severity=severity,
            confidence=confidence,
            function_name=self.current_function,
            class_name=self.current_class,
            context=context or {}
        ))
    
    def _get_source_line(self, line_number: int) -> str:
        """Get source code line by number"""
        if 1 <= line_number <= len(self.lines):
            return self.lines[line_number - 1]
        return ""


class ProductionExceptionAuditor:
    """Production-grade exception auditing with comprehensive fixes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging for the auditor"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def audit_codebase(self, base_dir: Path) -> AuditResult:
        """Perform comprehensive exception audit of entire codebase"""
        
        start_time = datetime.utcnow()
        self.logger.info(f"Starting exception audit of {base_dir}")
        
        results = {
            "total_files": 0,
            "violations_by_type": {},
            "violations_by_severity": {},
            "files_with_violations": [],
            "suggested_fixes": [],
            "audit_timestamp": start_time.isoformat(),
            "total_violations": 0,
            "confidence_score": 0.0,
            "patterns_detected": {}
        }
        
        python_files = list(base_dir.rglob("*.py"))
        results["total_files"] = len(python_files)
        
        all_violations = []
        total_confidence = 0.0
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                file_violations = self._analyze_file_semantically(file_path)
                if file_violations:
                    all_violations.extend(file_violations)
                    results["files_with_violations"].append({
                        "file": str(file_path.relative_to(base_dir)),
                        "violations": len(file_violations),
                        "severity_breakdown": self._get_severity_breakdown(file_violations)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
        
        # Aggregate statistics
        for violation in all_violations:
            # By type
            if violation.violation_type not in results["violations_by_type"]:
                results["violations_by_type"][violation.violation_type] = 0
            results["violations_by_type"][violation.violation_type] += 1
            
            # By severity
            if violation.severity not in results["violations_by_severity"]:
                results["violations_by_severity"][violation.severity] = 0
            results["violations_by_severity"][violation.severity] += 1
            
            total_confidence += violation.confidence
        
        # Calculate overall metrics
        results["total_violations"] = len(all_violations)
        results["confidence_score"] = (total_confidence / len(all_violations)) if all_violations else 1.0
        
        # Detect patterns
        results["patterns_detected"] = self._detect_patterns(all_violations)
        
        # Generate comprehensive fixes
        results["suggested_fixes"] = self._generate_comprehensive_fixes(all_violations)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Audit completed in {duration:.2f}s. Found {len(all_violations)} violations in {len(results['files_with_violations'])} files")
        
        return AuditResult(**results)
    
    def _analyze_file_semantically(self, file_path: Path) -> List[ExceptionViolation]:
        """Perform semantic analysis of a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Skip empty files
            if not source_code.strip():
                return []
            
            tree = ast.parse(source_code, filename=str(file_path))
            
            # Analyze exception handling semantically
            analyzer = SemanticExceptionAnalyzer(file_path, source_code)
            analyzer.visit(tree)
            
            return analyzer.violations
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Analysis failed for {file_path}: {e}")
            return []
    
    def _get_severity_breakdown(self, violations: List[ExceptionViolation]) -> Dict[str, int]:
        """Get breakdown of violations by severity"""
        breakdown = {"error": 0, "warning": 0, "info": 0}
        for violation in violations:
            if violation.severity in breakdown:
                breakdown[violation.severity] += 1
        return breakdown
    
    def _detect_patterns(self, violations: List[ExceptionViolation]) -> Dict[str, int]:
        """Detect common patterns in violations"""
        patterns = {}
        
        # Group by function
        functions_with_violations = set()
        for violation in violations:
            if violation.function_name:
                functions_with_violations.add(violation.function_name)
        patterns["functions_with_violations"] = len(functions_with_violations)
        
        # Group by file
        files_with_multiple_violations = 0
        violations_by_file = {}
        for violation in violations:
            file_key = str(violation.file_path)
            if file_key not in violations_by_file:
                violations_by_file[file_key] = 0
            violations_by_file[file_key] += 1
        
        for count in violations_by_file.values():
            if count > 5:
                files_with_multiple_violations += 1
        patterns["files_with_multiple_violations"] = files_with_multiple_violations
        
        # High confidence violations
        high_confidence = sum(1 for v in violations if v.confidence > 0.9)
        patterns["high_confidence_violations"] = high_confidence
        
        return patterns
    
    def _generate_comprehensive_fixes(self, violations: List[ExceptionViolation]) -> List[Dict[str, Any]]:
        """Generate comprehensive fixes for all violations"""
        fixes = []
        
        # Group violations by file for batch fixing
        violations_by_file = {}
        for violation in violations:
            file_path = str(violation.file_path)
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        for file_path, file_violations in violations_by_file.items():
            # Sort by confidence and severity for prioritization
            file_violations.sort(key=lambda v: (v.severity == "error", v.confidence), reverse=True)
            
            fixes.append({
                "file": file_path,
                "violations_count": len(file_violations),
                "priority_score": self._calculate_priority_score(file_violations),
                "fixes": [
                    {
                        "line": v.line_number,
                        "type": v.violation_type,
                        "current": v.current_code,
                        "suggested": v.suggested_fix,
                        "severity": v.severity,
                        "confidence": v.confidence,
                        "function": v.function_name,
                        "class": v.class_name,
                        "context": v.context
                    }
                    for v in file_violations
                ]
            })
        
        # Sort files by priority
        fixes.sort(key=lambda f: f["priority_score"], reverse=True)
        
        return fixes
    
    def _calculate_priority_score(self, violations: List[ExceptionViolation]) -> float:
        """Calculate priority score for a file based on its violations"""
        score = 0.0
        
        for violation in violations:
            base_score = 1.0
            
            # Weight by severity
            if violation.severity == "error":
                base_score *= 3.0
            elif violation.severity == "warning":
                base_score *= 2.0
            
            # Weight by confidence
            base_score *= violation.confidence
            
            score += base_score
        
        return score
    
    def apply_fixes(self, violations: List[ExceptionViolation], 
                   dry_run: bool = True) -> Dict[str, Any]:
        """Apply fixes to actual files (with dry_run option)"""
        
        results = {
            "files_modified": 0,
            "fixes_applied": 0,
            "errors": [],
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Group by file
        violations_by_file = {}
        for violation in violations:
            file_path = str(violation.file_path)
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        for file_path, file_violations in violations_by_file.items():
            try:
                if not dry_run:
                    self._apply_file_fixes(Path(file_path), file_violations)
                    results["files_modified"] += 1
                
                results["fixes_applied"] += len(file_violations)
                
            except Exception as e:
                results["errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return results
    
    def _apply_file_fixes(self, file_path: Path, violations: List[ExceptionViolation]):
        """Apply fixes to a single file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort violations by line number in reverse to avoid line number shifting
        violations.sort(key=lambda v: v.line_number, reverse=True)
        
        for violation in violations:
            if violation.violation_type == "bare_except":
                # Replace bare except with Exception
                line_idx = violation.line_number - 1
                if line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].replace("except:", "except Exception as e:")
            
            elif violation.violation_type == "generic_exception":
                # Add logging to generic exception handlers
                line_idx = violation.line_number - 1
                if line_idx < len(lines):
                    indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                    log_line = " " * (indent + 4) + "logging.error(f'Error in {self.current_function}: {e}')\n"
                    lines.insert(line_idx + 1, log_line)
            
            elif violation.violation_type == "missing_error_context":
                # Add error logging
                line_idx = violation.line_number - 1
                if line_idx < len(lines):
                    # Find the except handler and add logging
                    indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                    log_line = " " * (indent + 4) + "logging.error(f'Exception occurred: {e}')\n"
                    
                    # Insert after the except line
                    insert_idx = line_idx + 1
                    while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                        insert_idx += 1
                    lines.insert(insert_idx, log_line)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "__pycache__",
            ".git",
            "venv",
            "env",
            ".pytest_cache",
            "build",
            "dist",
            ".tox",
            "node_modules"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def generate_audit_report(self, audit_result: AuditResult, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive audit report"""
        
        report = f"""
# Exception Handling Audit Report

**Generated**: {audit_result.audit_timestamp}
**Total Files Analyzed**: {audit_result.total_files}
**Total Violations**: {audit_result.total_violations}
**Overall Confidence**: {audit_result.confidence_score:.2f}

## Summary

"""
        
        if audit_result.total_violations == 0:
            report += "✅ **Excellent!** No exception handling violations found.\n\n"
        else:
            report += f"⚠️ Found {audit_result.total_violations} exception handling violations across {len(audit_result.files_with_violations)} files.\n\n"
        
        # Violations by severity
        report += "### Violations by Severity\n\n"
        for severity, count in audit_result.violations_by_severity.items():
            emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
            report += f"- {emoji} **{severity.title()}**: {count}\n"
        
        # Violations by type
        report += "\n### Violations by Type\n\n"
        for violation_type, count in audit_result.violations_by_type.items():
            report += f"- **{violation_type.replace('_', ' ').title()}**: {count}\n"
        
        # Patterns detected
        if audit_result.patterns_detected:
            report += "\n### Patterns Detected\n\n"
            for pattern, count in audit_result.patterns_detected.items():
                report += f"- **{pattern.replace('_', ' ').title()}**: {count}\n"
        
        # Top files with violations
        if audit_result.files_with_violations:
            report += "\n### Files Requiring Attention\n\n"
            sorted_files = sorted(audit_result.files_with_violations, key=lambda f: f["violations"], reverse=True)
            for file_info in sorted_files[:10]:  # Top 10
                report += f"- `{file_info['file']}`: {file_info['violations']} violations\n"
                breakdown = file_info.get('severity_breakdown', {})
                if breakdown:
                    parts = []
                    if breakdown.get('error', 0) > 0:
                        parts.append(f"{breakdown['error']} errors")
                    if breakdown.get('warning', 0) > 0:
                        parts.append(f"{breakdown['warning']} warnings")
                    if breakdown.get('info', 0) > 0:
                        parts.append(f"{breakdown['info']} info")
                    if parts:
                        report += f"  - {', '.join(parts)}\n"
        
        # Recommendations
        report += "\n### Recommendations\n\n"
        if audit_result.total_violations > 0:
            high_priority = sum(1 for f in audit_result.suggested_fixes for fix in f["fixes"] if fix["severity"] == "error")
            if high_priority > 0:
                report += f"1. **Priority**: Fix {high_priority} error-level violations first\n"
            
            report += "2. **Best Practices**: Replace generic exception handling with specific exception types\n"
            report += "3. **Logging**: Add proper error logging to all exception handlers\n"
            report += "4. **Documentation**: Document expected exceptions in function docstrings\n"
        else:
            report += "✅ Excellent exception handling practices detected!\n"
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def main():
    """Command-line interface for exception auditing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Exception Audit Tool")
    parser.add_argument("directory", type=Path, help="Directory to audit")
    parser.add_argument("--output", type=Path, help="Output file for results")
    parser.add_argument("--apply-fixes", action="store_true", help="Apply fixes (not dry-run)")
    parser.add_argument("--report", type=Path, help="Generate markdown report")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    auditor = ProductionExceptionAuditor()
    
    # Perform audit
    result = auditor.audit_codebase(args.directory)
    
    # Output results
    if args.json:
        output = json.dumps(asdict(result), indent=2, default=str)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
    else:
        # Generate and display report
        report = auditor.generate_audit_report(result, args.report)
        if not args.report:
            print(report)
    
    # Apply fixes if requested
    if args.apply_fixes and result.total_violations > 0:
        print("\nApplying fixes...")
        # Would need to reconstruct violations list from result
        # This is a placeholder for the implementation
        print("Fix application not implemented in CLI mode. Use Python API.")
    
    return 0 if result.total_violations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())