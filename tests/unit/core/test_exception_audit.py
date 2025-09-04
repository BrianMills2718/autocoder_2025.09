"""
Unit tests for the Exception Audit Tool

Tests comprehensive AST-based exception analysis including:
- Semantic analysis accuracy
- Fix generation and application
- Edge cases and malformed code handling
"""

import pytest
import ast
import tempfile
from pathlib import Path
from typing import List

import sys
sys.path.append('/home/brian/autocoder4_cc')

from autocoder_cc.tools.exception_audit_tool import (
    ProductionExceptionAuditor,
    SemanticExceptionAnalyzer,
    ExceptionViolation,
    AuditResult
)


class TestSemanticExceptionAnalyzer:
    """Test semantic AST-based exception analysis"""
    
    def test_bare_except_detection(self):
        """Test detection of bare except statements"""
        code = """
try:
    risky_operation()
except:
    pass
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Should detect multiple violations for bare except (bare_except, missing_context, swallowed)
        assert len(analyzer.violations) >= 1
        
        # Find the bare_except violation specifically
        bare_except_violations = [v for v in analyzer.violations if v.violation_type == "bare_except"]
        assert len(bare_except_violations) == 1
        
        violation = bare_except_violations[0]
        assert violation.severity == "error"
        assert violation.confidence == 1.0
    
    def test_generic_exception_detection(self):
        """Test detection of generic Exception catches"""
        code = """
try:
    risky_operation()
except Exception as e:
    print(f"Error: {e}")
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Find the generic_exception violation specifically
        generic_violations = [v for v in analyzer.violations if v.violation_type == "generic_exception"]
        assert len(generic_violations) == 1
        
        violation = generic_violations[0]
        assert violation.severity == "warning"
        assert violation.confidence == 0.9
    
    def test_generic_exception_in_main_function(self):
        """Test that generic Exception in main functions are treated more leniently"""
        code = """
def main():
    try:
        risky_operation()
    except Exception as e:
        print(f"Error: {e}")
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Find the generic_exception violation specifically
        generic_violations = [v for v in analyzer.violations if v.violation_type == "generic_exception"]
        assert len(generic_violations) == 1
        
        violation = generic_violations[0]
        assert violation.severity == "info"  # More lenient for main functions
        assert violation.confidence == 0.6
    
    def test_overly_broad_exception_catching(self):
        """Test detection of overly broad exception catching"""
        code = """
try:
    risky_operation()
except (ValueError, TypeError, KeyError, IndexError, AttributeError, FileNotFoundError) as e:
    handle_error(e)
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        assert len(analyzer.violations) == 1
        violation = analyzer.violations[0]
        assert violation.violation_type == "overly_broad_except"
        assert violation.severity == "info"
        assert violation.confidence == 0.8
        assert violation.context["exception_count"] == 6
    
    def test_missing_error_context_detection(self):
        """Test detection of missing error context"""
        code = """
try:
    risky_operation()
except ValueError as e:
    return None
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Should detect missing error context but not be severe since there's a return
        violations = [v for v in analyzer.violations if v.violation_type == "missing_error_context"]
        assert len(violations) == 0  # Return statement is acceptable context
    
    def test_swallowed_exception_detection(self):
        """Test detection of swallowed exceptions"""
        code = """
try:
    risky_operation()
except ValueError as e:
    pass
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Should detect both swallowed exception and missing context
        swallowed_violations = [v for v in analyzer.violations if v.violation_type == "swallowed_exception"]
        assert len(swallowed_violations) == 1
        assert swallowed_violations[0].severity == "warning"
        assert swallowed_violations[0].confidence == 0.9
    
    def test_proper_error_handling_with_logging(self):
        """Test that proper error handling with logging is not flagged"""
        code = """
import logging

try:
    risky_operation()
except ValueError as e:
    logging.error(f"Operation failed: {e}")
    raise
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Should not flag this as missing context since it has logging and re-raises
        context_violations = [v for v in analyzer.violations if v.violation_type == "missing_error_context"]
        swallowed_violations = [v for v in analyzer.violations if v.violation_type == "swallowed_exception"]
        assert len(context_violations) == 0
        assert len(swallowed_violations) == 0
    
    def test_function_and_class_context_tracking(self):
        """Test that function and class context is properly tracked"""
        code = """
class TestClass:
    def test_method(self):
        try:
            risky_operation()
        except:
            pass
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        assert len(analyzer.violations) >= 1
        violation = analyzer.violations[0]
        assert violation.function_name == "test_method"
        assert violation.class_name == "TestClass"
    
    def test_import_tracking(self):
        """Test that imports are properly tracked for context-aware suggestions"""
        code = """
import logging
from typing import Any

try:
    risky_operation()
except ValueError as e:
    pass
"""
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        assert "logging" in analyzer.logger_imports
        # Check that suggestions use the tracked logger
        violations = [v for v in analyzer.violations if v.violation_type == "missing_error_context"]
        if violations:
            assert "logging.error" in violations[0].suggested_fix


class TestProductionExceptionAuditor:
    """Test production exception auditor functionality"""
    
    @pytest.fixture
    def auditor(self):
        return ProductionExceptionAuditor()
    
    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file with exception handling issues"""
        content = """
def test_function():
    try:
        risky_operation()
    except:
        pass
    
    try:
        another_operation()
    except Exception as e:
        print("Error occurred")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            f.flush()
            yield Path(f.name)
        Path(f.name).unlink()
    
    def test_audit_single_file(self, auditor, temp_python_file):
        """Test auditing a single file with violations"""
        violations = auditor._analyze_file_semantically(temp_python_file)
        
        assert len(violations) >= 2  # Should find both bare except and missing context
        
        # Check violation types
        violation_types = {v.violation_type for v in violations}
        assert "bare_except" in violation_types
    
    def test_audit_codebase(self, auditor):
        """Test auditing entire codebase"""
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file with violations
            test_file = temp_path / "test_violations.py"
            test_file.write_text("""
try:
    operation()
except:
    pass

try:
    other_operation()
except Exception as e:
    continue
""")
            
            # Create valid file
            valid_file = temp_path / "valid_code.py"
            valid_file.write_text("""
try:
    operation()
except ValueError as e:
    logging.error(f"Value error: {e}")
    raise
""")
            
            result = auditor.audit_codebase(temp_path)
            
            assert isinstance(result, AuditResult)
            assert result.total_files == 2
            assert result.total_violations > 0
            assert len(result.files_with_violations) == 1  # Only test_violations.py should have issues
    
    def test_severity_breakdown(self, auditor):
        """Test severity breakdown calculation"""
        violations = [
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=1,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Fix it",
                severity="error",
                confidence=1.0
            ),
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=2,
                violation_type="generic_exception",
                current_code="except Exception:",
                suggested_fix="Fix it",
                severity="warning",
                confidence=0.9
            ),
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=3,
                violation_type="missing_context",
                current_code="pass",
                suggested_fix="Fix it",
                severity="info",
                confidence=0.8
            )
        ]
        
        breakdown = auditor._get_severity_breakdown(violations)
        
        assert breakdown["error"] == 1
        assert breakdown["warning"] == 1
        assert breakdown["info"] == 1
    
    def test_pattern_detection(self, auditor):
        """Test pattern detection functionality"""
        violations = [
            ExceptionViolation(
                file_path=Path("file1.py"),
                line_number=1,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Fix it",
                severity="error",
                confidence=1.0,
                function_name="func1"
            ),
            ExceptionViolation(
                file_path=Path("file1.py"),
                line_number=5,
                violation_type="generic_exception",
                current_code="except Exception:",
                suggested_fix="Fix it",
                severity="warning",
                confidence=0.9,
                function_name="func1"
            ),
            ExceptionViolation(
                file_path=Path("file2.py"),
                line_number=10,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Fix it",
                severity="error",
                confidence=1.0,
                function_name="func2"
            )
        ]
        
        patterns = auditor._detect_patterns(violations)
        
        assert patterns["functions_with_violations"] == 2  # func1 and func2
        assert patterns["high_confidence_violations"] == 2  # Two with confidence 1.0
    
    def test_comprehensive_fixes_generation(self, auditor):
        """Test comprehensive fixes generation"""
        violations = [
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=1,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Use specific exceptions",
                severity="error",
                confidence=1.0
            ),
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=5,
                violation_type="generic_exception",
                current_code="except Exception:",
                suggested_fix="Use specific exceptions",
                severity="warning",
                confidence=0.9
            )
        ]
        
        fixes = auditor._generate_comprehensive_fixes(violations)
        
        assert len(fixes) == 1  # One file
        assert fixes[0]["file"] == str(Path("test.py"))
        assert fixes[0]["violations_count"] == 2
        assert len(fixes[0]["fixes"]) == 2
        
        # Check that fixes are sorted by severity and confidence
        fix_severities = [fix["severity"] for fix in fixes[0]["fixes"]]
        assert fix_severities[0] == "error"  # Error should come first
    
    def test_priority_score_calculation(self, auditor):
        """Test priority score calculation for files"""
        violations = [
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=1,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Fix it",
                severity="error",
                confidence=1.0
            ),
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=5,
                violation_type="generic_exception",
                current_code="except Exception:",
                suggested_fix="Fix it",
                severity="warning",
                confidence=0.9
            )
        ]
        
        score = auditor._calculate_priority_score(violations)
        
        # Error (3.0 * 1.0) + Warning (2.0 * 0.9) = 4.8
        expected_score = 3.0 * 1.0 + 2.0 * 0.9
        assert score == expected_score
    
    def test_skip_file_logic(self, auditor):
        """Test file skipping logic"""
        skip_files = [
            Path("__pycache__/test.py"),
            Path("venv/lib/python3.9/site-packages/test.py"),
            Path("build/lib/test.py"),
            Path(".git/hooks/test.py")
        ]
        
        for file_path in skip_files:
            assert auditor._should_skip_file(file_path)
        
        # Should not skip regular files
        regular_files = [
            Path("src/main.py"),
            Path("tests/test_main.py"),
            Path("scripts/deploy.py")
        ]
        
        for file_path in regular_files:
            assert not auditor._should_skip_file(file_path)
    
    def test_apply_fixes_dry_run(self, auditor):
        """Test applying fixes in dry run mode"""
        violations = [
            ExceptionViolation(
                file_path=Path("test.py"),
                line_number=1,
                violation_type="bare_except",
                current_code="except:",
                suggested_fix="Use specific exceptions",
                severity="error",
                confidence=1.0
            )
        ]
        
        result = auditor.apply_fixes(violations, dry_run=True)
        
        assert result["dry_run"] is True
        assert result["files_modified"] == 0  # No files actually modified in dry run
        assert result["fixes_applied"] == 1  # But fixes would be applied
        assert len(result["errors"]) == 0
    
    def test_audit_report_generation(self, auditor):
        """Test audit report generation"""
        audit_result = AuditResult(
            total_files=10,
            violations_by_type={"bare_except": 2, "generic_exception": 3},
            violations_by_severity={"error": 2, "warning": 3},
            files_with_violations=[
                {"file": "test1.py", "violations": 2, "severity_breakdown": {"error": 1, "warning": 1}},
                {"file": "test2.py", "violations": 3, "severity_breakdown": {"error": 1, "warning": 2}}
            ],
            suggested_fixes=[],
            audit_timestamp="2025-01-01T00:00:00",
            total_violations=5,
            confidence_score=0.95,
            patterns_detected={"functions_with_violations": 3}
        )
        
        report = auditor.generate_audit_report(audit_result)
        
        assert "Exception Handling Audit Report" in report
        assert "Total Files Analyzed: 10" in report
        assert "Total Violations: 5" in report
        assert "Overall Confidence: 0.95" in report
        assert "🔴 **Error**: 2" in report
        assert "🟡 **Warning**: 3" in report


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_file_handling(self):
        """Test handling of empty Python files"""
        auditor = ProductionExceptionAuditor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            try:
                violations = auditor._analyze_file_semantically(Path(f.name))
                assert len(violations) == 0  # Should handle empty files gracefully
            finally:
                Path(f.name).unlink()
    
    def test_syntax_error_handling(self):
        """Test handling of files with syntax errors"""
        auditor = ProductionExceptionAuditor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def invalid_syntax(\n")  # Syntax error
            f.flush()
            
            try:
                violations = auditor._analyze_file_semantically(Path(f.name))
                assert len(violations) == 0  # Should handle syntax errors gracefully
            finally:
                Path(f.name).unlink()
    
    def test_unicode_handling(self):
        """Test handling of files with unicode content"""
        auditor = ProductionExceptionAuditor()
        
        content = """
# -*- coding: utf-8 -*-
def test_function():
    try:
        operation_with_unicode_comment()  # 这是一个测试
    except:
        pass
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            
            try:
                violations = auditor._analyze_file_semantically(Path(f.name))
                assert len(violations) >= 1  # Should detect bare except despite unicode
            finally:
                Path(f.name).unlink()
    
    def test_nested_exception_handlers(self):
        """Test handling of nested exception handlers"""
        code = """
def nested_function():
    try:
        outer_operation()
        try:
            inner_operation()
        except ValueError as e:
            logging.error(f"Inner error: {e}")
        except:  # This should be flagged
            pass
    except Exception as e:  # This should also be flagged
        print(f"Outer error: {e}")
"""
        
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        # Should detect both the bare except and the generic Exception
        bare_except_violations = [v for v in analyzer.violations if v.violation_type == "bare_except"]
        generic_violations = [v for v in analyzer.violations if v.violation_type == "generic_exception"]
        
        assert len(bare_except_violations) == 1
        assert len(generic_violations) == 1
    
    def test_async_function_context(self):
        """Test handling of async functions"""
        code = """
async def async_function():
    try:
        await async_operation()
    except:
        pass
"""
        
        analyzer = SemanticExceptionAnalyzer(Path("test.py"), code)
        tree = ast.parse(code)
        analyzer.visit(tree)
        
        assert len(analyzer.violations) >= 1
        violation = analyzer.violations[0]
        assert violation.function_name == "async_function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])