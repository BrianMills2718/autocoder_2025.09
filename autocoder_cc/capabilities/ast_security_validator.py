from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
AST-Based Security Validator for Enhanced Code Injection Prevention

This module provides comprehensive AST-based security validation to replace
brittle regex patterns with robust structural code analysis.

Implements Gemini-identified critical improvement:
"Relying solely on regex patterns for security can be brittle. 
Additional AST-based validation needed for code injection prevention."
"""

import ast
import logging
from typing import Set, List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class SecurityViolationType(Enum):
    """Types of security violations detected by AST analysis"""
    DANGEROUS_FUNCTION_CALL = "dangerous_function_call"
    DYNAMIC_CODE_EXECUTION = "dynamic_code_execution"
    UNSAFE_IMPORT = "unsafe_import"
    INTROSPECTION_CALL = "introspection_call"
    SUBPROCESS_CALL = "subprocess_call"
    ATTRIBUTE_MANIPULATION = "attribute_manipulation"
    DISALLOWED_NODE_TYPE = "disallowed_node_type"
    CODE_INJECTION_ATTEMPT = "code_injection_attempt"


@dataclass
class SecurityViolation:
    """Represents a detected security violation"""
    violation_type: SecurityViolationType
    node_type: str
    line_number: int
    column_number: int
    description: str
    severity: str
    context: Dict[str, Any]


class ASTSecurityValidationError(Exception):
    """Raised when AST security validation fails"""
    def __init__(self, message: str, violations: List[SecurityViolation]):
        super().__init__(message)
        self.violations = violations


class ASTSecurityValidator(ast.NodeVisitor):
    """
    Comprehensive AST-based security validator.
    
    Replaces regex-based security checking with robust AST analysis
    to prevent code injection and detect dangerous code patterns.
    """
    
    def __init__(self, strict_mode: bool = True):
        self.logger = get_logger("ASTSecurityValidator")
        self.strict_mode = strict_mode
        self.violations: List[SecurityViolation] = []
        
        # Define allowed AST node types (whitelist approach)
        self.allowed_node_types = {
            # Basic structures
            ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
            ast.Return, ast.Assign, ast.AugAssign, ast.AnnAssign,
            
            # Control flow
            ast.If, ast.For, ast.AsyncFor, ast.While, ast.Break, ast.Continue,
            ast.Try, ast.ExceptHandler, ast.Raise, ast.Assert,
            ast.With, ast.AsyncWith,
            
            # Expressions
            ast.Expr, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
            ast.Call, ast.Attribute, ast.Subscript, ast.Index, ast.Slice,
            ast.Name, ast.Load, ast.Store, ast.Del,
            
            # Comparison operators (essential for normal code)
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Is, ast.IsNot, ast.In, ast.NotIn,
            
            # Logical operators (essential for normal code)
            ast.And, ast.Or, ast.Not,
            
            # Arithmetic operators (essential for normal code)
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
            ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
            ast.FloorDiv, ast.Invert, ast.UAdd, ast.USub,
            
            # Literals
            ast.Constant, ast.Num, ast.Str, ast.Bytes, ast.NameConstant,
            ast.List, ast.Tuple, ast.Set, ast.Dict,
            
            # F-strings (essential for modern Python)
            ast.JoinedStr, ast.FormattedValue,
            
            # Comprehensions
            ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
            ast.comprehension,  # For comprehension clauses (in list/dict/set comprehensions)
            
            # Arguments and keywords
            ast.arguments, ast.arg, ast.keyword,
            
            # Import statements (controlled)
            ast.Import, ast.ImportFrom, ast.alias,
            
            # Lambda (limited)
            ast.Lambda,
            
            # Conditional expressions (safe Python constructs)
            ast.IfExp,
        }
        
        # Dangerous function names that should not be called
        self.dangerous_functions = {
            # Dynamic code execution
            'eval', 'exec', 'compile',
            
            # System access
            'system', 'popen', 'spawn', 'fork',
            
            # Introspection (potentially dangerous)
            'globals', 'locals', 'vars', 'dir',
            
            # Attribute manipulation
            'setattr', 'delattr', 'hasattr',
            
            # Import manipulation
            '__import__', 'importlib',
            
            # Memory/object access
            'id', 'hash', 'memoryview',
            
            # File operations (some are dangerous)
            'open',  # Can be dangerous depending on usage
        }
        
        # Dangerous module patterns
        self.dangerous_modules = {
            'subprocess', 'os', 'sys', 'importlib', 'ctypes',
            'marshal', 'pickle', 'shelve', 'dill',
            '__builtin__', '__builtins__', 'builtins'
        }
        
        # Subprocess-related dangerous calls
        self.subprocess_calls = {
            'run', 'call', 'check_call', 'check_output', 'Popen',
            'getstatusoutput', 'getoutput'
        }
        
        # OS module dangerous calls
        self.os_dangerous_calls = {
            'system', 'popen', 'exec', 'execl', 'execle', 'execlp',
            'execv', 'execve', 'execvp', 'execvpe', 'spawn'
        }
    
    def validate_code(self, code: str) -> List[SecurityViolation]:
        """
        Validate Python code for security violations using AST analysis.
        
        Args:
            code: Python code to validate
            
        Returns:
            List of security violations found
            
        Raises:
            ASTSecurityValidationError: If violations found in strict mode
        """
        self.violations.clear()
        
        try:
            # Parse code into AST
            tree = ast.parse(code)
            
            # Visit all nodes in the AST
            self.visit(tree)
            
            # In strict mode, raise exception if violations found
            if self.strict_mode and self.violations:
                violation_summary = f"Found {len(self.violations)} security violations"
                raise ASTSecurityValidationError(violation_summary, self.violations)
            
            return self.violations
            
        except SyntaxError as e:
            # Syntax errors are also security concerns (malformed code)
            violation = SecurityViolation(
                violation_type=SecurityViolationType.CODE_INJECTION_ATTEMPT,
                node_type="SyntaxError",
                line_number=e.lineno or 0,
                column_number=e.offset or 0,
                description=f"Syntax error in code: {e.msg}",
                severity="critical",
                context={"error": str(e), "text": e.text}
            )
            if self.strict_mode:
                raise ASTSecurityValidationError("Syntax error detected", [violation])
            return [violation]
    
    def visit(self, node):
        """Override visit to check node types against whitelist"""
        # Check if node type is allowed
        if type(node) not in self.allowed_node_types:
            self._record_violation(
                SecurityViolationType.DISALLOWED_NODE_TYPE,
                node,
                f"Disallowed AST node type: {type(node).__name__}",
                "critical",
                {"node_type": type(node).__name__}
            )
        
        # Continue with specific node analysis
        super().visit(node)
    
    def visit_Call(self, node):
        """Analyze function calls for security violations"""
        self._analyze_function_call(node)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Analyze attribute access for dangerous patterns"""
        self._analyze_attribute_access(node)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Analyze import statements for dangerous modules"""
        for alias in node.names:
            if alias.name in self.dangerous_modules:
                self._record_violation(
                    SecurityViolationType.UNSAFE_IMPORT,
                    node,
                    f"Import of dangerous module: {alias.name}",
                    "high",
                    {"module": alias.name, "alias": alias.asname}
                )
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Analyze from...import statements for dangerous modules"""
        if node.module and node.module in self.dangerous_modules:
            imported_names = [alias.name for alias in node.names]
            self._record_violation(
                SecurityViolationType.UNSAFE_IMPORT,
                node,
                f"Import from dangerous module: {node.module} ({imported_names})",
                "high",
                {"module": node.module, "names": imported_names}
            )
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Analyze string constants for potential code injection"""
        if isinstance(node.value, str):
            self._analyze_string_literal(node, node.value)
        self.generic_visit(node)
    
    def visit_Str(self, node):
        """Analyze string literals (Python < 3.8 compatibility)"""
        self._analyze_string_literal(node, node.s)
        self.generic_visit(node)
    
    def _analyze_function_call(self, node):
        """Analyze function calls for dangerous patterns"""
        func_name = self._get_function_name(node)
        
        if func_name in self.dangerous_functions:
            # Categorize the violation type
            if func_name in ['eval', 'exec', 'compile']:
                violation_type = SecurityViolationType.DYNAMIC_CODE_EXECUTION
                severity = "critical"
            elif func_name in ['globals', 'locals', 'vars', 'dir']:
                violation_type = SecurityViolationType.INTROSPECTION_CALL
                severity = "high"
            elif func_name in ['setattr', 'delattr', 'hasattr']:
                violation_type = SecurityViolationType.ATTRIBUTE_MANIPULATION
                severity = "medium"
            else:
                violation_type = SecurityViolationType.DANGEROUS_FUNCTION_CALL
                severity = "high"
            
            self._record_violation(
                violation_type,
                node,
                f"Dangerous function call: {func_name}()",
                severity,
                {"function_name": func_name, "args_count": len(node.args)}
            )
    
    def _analyze_attribute_access(self, node):
        """Analyze attribute access for dangerous patterns"""
        # Check for subprocess module calls
        if isinstance(node.value, ast.Name) and node.value.id == 'subprocess':
            if node.attr in self.subprocess_calls:
                self._record_violation(
                    SecurityViolationType.SUBPROCESS_CALL,
                    node,
                    f"Subprocess call: subprocess.{node.attr}",
                    "critical",
                    {"module": "subprocess", "function": node.attr}
                )
        
        # Check for os module calls
        elif isinstance(node.value, ast.Name) and node.value.id == 'os':
            if node.attr in self.os_dangerous_calls:
                self._record_violation(
                    SecurityViolationType.SUBPROCESS_CALL,
                    node,
                    f"OS system call: os.{node.attr}",
                    "critical",
                    {"module": "os", "function": node.attr}
                )
        
        # Check for builtins access
        elif isinstance(node.value, ast.Name) and node.value.id in ['__builtins__', '__builtin__', 'builtins']:
            self._record_violation(
                SecurityViolationType.INTROSPECTION_CALL,
                node,
                f"Builtins access: {node.value.id}.{node.attr}",
                "critical",
                {"module": node.value.id, "attribute": node.attr}
            )
        
        # Check for dunder method access
        elif node.attr.startswith('__') and node.attr.endswith('__'):
            if node.attr in ['__import__', '__subclasses__', '__class__', '__bases__', '__mro__']:
                self._record_violation(
                    SecurityViolationType.INTROSPECTION_CALL,
                    node,
                    f"Dangerous dunder method access: {node.attr}",
                    "high",
                    {"dunder_method": node.attr}
                )
    
    def _analyze_string_literal(self, node, value: str):
        """Analyze string literals for potential code injection patterns"""
        # Check for embedded code patterns
        dangerous_patterns = [
            'eval(', 'exec(', 'subprocess.',
            'os.system', '__import__', '__builtins__'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in value:
                self._record_violation(
                    SecurityViolationType.CODE_INJECTION_ATTEMPT,
                    node,
                    f"String contains dangerous pattern: '{pattern}'",
                    "medium",
                    {"pattern": pattern, "string_value": value[:100]}  # Truncate long strings
                )
    
    def _get_function_name(self, call_node) -> str:
        """Extract function name from call node"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        else:
            return "unknown_function"
    
    def _record_violation(self, violation_type: SecurityViolationType, node, 
                         description: str, severity: str, context: Dict[str, Any]):
        """Record a security violation"""
        violation = SecurityViolation(
            violation_type=violation_type,
            node_type=type(node).__name__,
            line_number=getattr(node, 'lineno', 0),
            column_number=getattr(node, 'col_offset', 0),
            description=description,
            severity=severity,
            context=context
        )
        
        self.violations.append(violation)
        
        # Log the violation
        if severity == "critical":
            self.logger.critical(f"Security violation: {description} at line {violation.line_number}")
        else:
            self.logger.error(f"Security violation: {description} at line {violation.line_number}")
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of all violations found"""
        summary = {
            "total_violations": len(self.violations),
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "violations": []
        }
        
        for violation in self.violations:
            # Count by type
            type_name = violation.violation_type.value
            summary["by_type"][type_name] = summary["by_type"].get(type_name, 0) + 1
            
            # Count by severity
            summary["by_severity"][violation.severity] = summary["by_severity"].get(violation.severity, 0) + 1
            
            # Count critical violations
            if violation.severity == "critical":
                summary["critical_count"] += 1
            
            # Add violation details
            summary["violations"].append({
                "type": type_name,
                "description": violation.description,
                "line": violation.line_number,
                "severity": violation.severity,
                "context": violation.context
            })
        
        return summary


def validate_code_security(code: str, strict_mode: bool = True) -> List[SecurityViolation]:
    """
    Convenience function to validate code security using AST analysis.
    
    Args:
        code: Python code to validate
        strict_mode: Whether to raise exceptions on violations
        
    Returns:
        List of security violations found
        
    Raises:
        ASTSecurityValidationError: If violations found in strict mode
    """
    validator = ASTSecurityValidator(strict_mode=strict_mode)
    return validator.validate_code(code)


def is_code_secure(code: str) -> bool:
    """
    Quick check if code passes security validation.
    
    Args:
        code: Python code to check
        
    Returns:
        True if code is secure, False otherwise
    """
    try:
        violations = validate_code_security(code, strict_mode=False)
        # Consider code secure if no critical violations
        return not any(v.severity == "critical" for v in violations)
    except Exception:
        return False