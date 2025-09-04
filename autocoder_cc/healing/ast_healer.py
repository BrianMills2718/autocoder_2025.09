from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
AST-based Component Healer for Autocoder v5.0

Provides precise, semantic-aware code modifications using AST manipulation.
Handles syntax errors, null safety, bounds checking, and contract compliance.
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import textwrap
from dataclasses import dataclass


@dataclass
class HealingResult:
    """Result of a healing operation"""
    success: bool
    original_code: str
    healed_code: str
    changes_made: List[str]
    error_message: Optional[str] = None


class ASTHealer:
    """
    Heals component code issues using AST manipulation.
    
    Focuses on:
    - Syntax error recovery
    - Null/None safety injection
    - Bounds checking for arrays/indices
    - Contract compliance (input/output validation)
    - Error handling patterns
    """
    
    def __init__(self):
        self.logger = get_logger("ASTHealer")
    
    def heal_syntax_errors(self, code: str) -> HealingResult:
        """
        Attempt to heal syntax errors in Python code.
        
        Args:
            code: Python code with potential syntax errors
            
        Returns:
            HealingResult with healed code or error details
        """
        changes = []
        original_code = code
        
        try:
            # First, try to parse the code
            tree = ast.parse(code)
            
            # Check for undefined variables even if syntax is valid
            undefined_vars = self._find_undefined_variables(tree)
            if undefined_vars:
                healed_tree = self._heal_undefined_variables(tree, undefined_vars, changes)
                healed_code = ast.unparse(healed_tree)
                return HealingResult(
                    success=True,
                    original_code=original_code,
                    healed_code=healed_code,
                    changes_made=changes
                )
            
            return HealingResult(
                success=True,
                original_code=original_code,
                healed_code=code,
                changes_made=["No syntax errors found"]
            )
        except SyntaxError as e:
            self.logger.info(f"Syntax error detected: {e}")
            
            # Common syntax error patterns and fixes
            healed_code = code
            
            # Fix missing colons
            if "expected ':'" in str(e):
                lines = healed_code.split('\n')
                if e.lineno and e.lineno <= len(lines):
                    line = lines[e.lineno - 1]
                    if line.strip().startswith(('if ', 'elif ', 'else', 'for ', 'while ', 'def ', 'class ', 'try', 'except', 'finally', 'with ')):
                        if not line.rstrip().endswith(':'):
                            lines[e.lineno - 1] = line.rstrip() + ':'
                            healed_code = '\n'.join(lines)
                            changes.append(f"Added missing colon at line {e.lineno}")
            
            # Fix indentation errors
            elif "IndentationError" in str(type(e)):
                lines = healed_code.split('\n')
                if e.lineno and e.lineno <= len(lines):
                    # Try to fix by matching previous indentation
                    if e.lineno > 1:
                        prev_indent = len(lines[e.lineno - 2]) - len(lines[e.lineno - 2].lstrip())
                        current_line = lines[e.lineno - 1]
                        stripped_line = current_line.lstrip()
                        
                        # Determine expected indentation
                        if any(lines[e.lineno - 2].strip().startswith(kw) for kw in ['if ', 'elif ', 'else:', 'for ', 'while ', 'def ', 'class ', 'try:', 'except', 'with ']):
                            expected_indent = prev_indent + 4
                        else:
                            expected_indent = prev_indent
                        
                        lines[e.lineno - 1] = ' ' * expected_indent + stripped_line
                        healed_code = '\n'.join(lines)
                        changes.append(f"Fixed indentation at line {e.lineno}")
            
            # Try parsing again
            try:
                ast.parse(healed_code)
                return HealingResult(
                    success=True,
                    original_code=original_code,
                    healed_code=healed_code,
                    changes_made=changes
                )
            except:
                return HealingResult(
                    success=False,
                    original_code=original_code,
                    healed_code=healed_code,
                    changes_made=changes,
                    error_message=f"Could not heal syntax error: {e}"
                )
    
    def inject_null_safety(self, code: str) -> HealingResult:
        """
        Inject null/None safety checks into code.
        
        Args:
            code: Python code to enhance with null safety
            
        Returns:
            HealingResult with null-safe code
        """
        changes = []
        original_code = code
        
        try:
            tree = ast.parse(code)
            transformer = NullSafetyTransformer(changes)
            new_tree = transformer.visit(tree)
            healed_code = ast.unparse(new_tree)
            
            return HealingResult(
                success=True,
                original_code=original_code,
                healed_code=healed_code,
                changes_made=changes if changes else ["No null safety issues found"]
            )
        except Exception as e:
            return HealingResult(
                success=False,
                original_code=original_code,
                healed_code=code,
                changes_made=changes,
                error_message=f"Failed to inject null safety: {e}"
            )
    
    def inject_bounds_checking(self, code: str) -> HealingResult:
        """
        Add bounds checking for array/list access.
        
        Args:
            code: Python code to enhance with bounds checking
            
        Returns:
            HealingResult with bounds-checked code
        """
        changes = []
        original_code = code
        
        try:
            tree = ast.parse(code)
            transformer = BoundsCheckTransformer(changes)
            new_tree = transformer.visit(tree)
            healed_code = ast.unparse(new_tree)
            
            return HealingResult(
                success=True,
                original_code=original_code,
                healed_code=healed_code,
                changes_made=changes if changes else ["No bounds checking needed"]
            )
        except Exception as e:
            return HealingResult(
                success=False,
                original_code=original_code,
                healed_code=code,
                changes_made=changes,
                error_message=f"Failed to inject bounds checking: {e}"
            )
    
    def inject_error_handling(self, code: str) -> HealingResult:
        """
        Add proper error handling patterns.
        
        Args:
            code: Python code to enhance with error handling
            
        Returns:
            HealingResult with error handling added
        """
        changes = []
        original_code = code
        
        try:
            tree = ast.parse(code)
            transformer = ErrorHandlingTransformer(changes)
            new_tree = transformer.visit(tree)
            healed_code = ast.unparse(new_tree)
            
            return HealingResult(
                success=True,
                original_code=original_code,
                healed_code=healed_code,
                changes_made=changes if changes else ["Error handling already adequate"]
            )
        except Exception as e:
            return HealingResult(
                success=False,
                original_code=original_code,
                healed_code=code,
                changes_made=changes,
                error_message=f"Failed to inject error handling: {e}"
            )
    
    def heal_component_code(self, code: str, issues: List[str]) -> HealingResult:
        """
        Apply all relevant healing based on detected issues.
        
        Args:
            code: Component code to heal
            issues: List of detected issues
            
        Returns:
            HealingResult with all applicable healing applied
        """
        current_code = code
        all_changes = []
        
        # Apply healing based on issues
        if any("syntax" in issue.lower() for issue in issues):
            result = self.heal_syntax_errors(current_code)
            if result.success:
                current_code = result.healed_code
                all_changes.extend(result.changes_made)
        
        if any("null" in issue.lower() or "none" in issue.lower() for issue in issues):
            result = self.inject_null_safety(current_code)
            if result.success:
                current_code = result.healed_code
                all_changes.extend(result.changes_made)
        
        if any("bound" in issue.lower() or "index" in issue.lower() for issue in issues):
            result = self.inject_bounds_checking(current_code)
            if result.success:
                current_code = result.healed_code
                all_changes.extend(result.changes_made)
        
        if any("error" in issue.lower() or "exception" in issue.lower() for issue in issues):
            result = self.inject_error_handling(current_code)
            if result.success:
                current_code = result.healed_code
                all_changes.extend(result.changes_made)
        
        return HealingResult(
            success=current_code != code,
            original_code=code,
            healed_code=current_code,
            changes_made=all_changes if all_changes else ["No healing needed"]
        )
    
    def _find_undefined_variables(self, tree: ast.AST) -> List[str]:
        """Find all undefined variables in the AST"""
        visitor = UndefinedVariableFinder()
        visitor.visit(tree)
        return visitor.undefined_vars
    
    def _heal_undefined_variables(self, tree: ast.AST, undefined_vars: List[str], changes: List[str]) -> ast.AST:
        """Replace undefined variables with safe defaults and provide review information"""
        transformer = UndefinedVariableTransformer(undefined_vars, changes)
        new_tree = transformer.visit(tree)
        
        # Get replacement summary for review
        summary = transformer.get_replacement_summary()
        
        # Log critical replacements that need review
        if summary["critical_replacements"]:
            self.logger.warning("🚨 CRITICAL VARIABLE REPLACEMENTS DETECTED:")
            self.logger.warning("   These replacements may affect business logic and should be reviewed:")
            for replacement in summary["critical_replacements"]:
                self.logger.warning(
                    f"   - Variable '{replacement['variable']}' at line {replacement['line']} "
                    f"replaced with {replacement['replacement']} ({replacement['reason']})"
                )
            self.logger.warning("   🔍 Manual code review recommended before deployment")
        
        # Add summary to changes for reporting
        if summary["total_replacements"] > 0:
            changes.append(f"VARIABLE REPLACEMENT SUMMARY: {summary['total_replacements']} total, "
                          f"{len(summary['critical_replacements'])} critical")
        
        return new_tree


class NullSafetyTransformer(ast.NodeTransformer):
    """AST transformer for null safety injection"""
    
    def __init__(self, changes: List[str]):
        self.changes = changes
    
    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        """Wrap attribute access with null checks"""
        self.generic_visit(node)
        
        # Create null-safe version: value.attr if value is not None else None
        safe_access = ast.IfExp(
            test=ast.Compare(
                left=node.value,
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None)]
            ),
            body=node,
            orelse=ast.Constant(value=None)
        )
        
        self.changes.append(f"Added null safety for attribute access: {ast.unparse(node)}")
        return safe_access
    
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Wrap subscript access with null checks"""
        self.generic_visit(node)
        
        # Don't wrap if already in a safe context
        if isinstance(node.ctx, ast.Store):
            return node
        
        # Create null-safe version
        safe_access = ast.IfExp(
            test=ast.Compare(
                left=node.value,
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None)]
            ),
            body=node,
            orelse=ast.Constant(value=None)
        )
        
        self.changes.append(f"Added null safety for subscript access")
        return safe_access


class BoundsCheckTransformer(ast.NodeTransformer):
    """AST transformer for bounds checking injection"""
    
    def __init__(self, changes: List[str]):
        self.changes = changes
    
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Add bounds checking for subscript access"""
        self.generic_visit(node)
        
        # Only for integer indices in Load context
        if isinstance(node.ctx, ast.Store) or not isinstance(node.slice, ast.Constant):
            return node
        
        if not isinstance(node.slice.value, int):
            return node
        
        # Create bounds-checked version
        # value[index] if 0 <= index < len(value) else None
        bounds_check = ast.IfExp(
            test=ast.BoolOp(
                op=ast.And(),
                values=[
                    ast.Compare(
                        left=ast.Constant(value=0),
                        ops=[ast.LtE()],
                        comparators=[node.slice]
                    ),
                    ast.Compare(
                        left=node.slice,
                        ops=[ast.Lt()],
                        comparators=[ast.Call(
                            func=ast.Name(id='len', ctx=ast.Load()),
                            args=[node.value],
                            keywords=[]
                        )]
                    )
                ]
            ),
            body=node,
            orelse=ast.Constant(value=None)
        )
        
        self.changes.append(f"Added bounds checking for index access")
        return bounds_check


class ErrorHandlingTransformer(ast.NodeTransformer):
    """AST transformer for error handling injection"""
    
    def __init__(self, changes: List[str]):
        self.changes = changes
        self.in_try_block = False
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Wrap function bodies in try-except if not already wrapped"""
        self.generic_visit(node)
        
        # Check if already has try-except
        has_try = any(isinstance(stmt, ast.Try) for stmt in node.body)
        
        if not has_try and len(node.body) > 0:
            # Wrap entire function body in try-except
            try_node = ast.Try(
                body=node.body,
                handlers=[
                    ast.ExceptHandler(
                        type=ast.Name(id='Exception', ctx=ast.Load()),
                        name='e',
                        body=[
                            ast.Expr(value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='self', ctx=ast.Load()),
                                    attr='logger',
                                    ctx=ast.Load()
                                ),
                                args=[
                                    ast.JoinedStr(values=[
                                        ast.Constant(value=f"Error in {node.name}: "),
                                        ast.FormattedValue(
                                            value=ast.Name(id='e', ctx=ast.Load()),
                                            conversion=-1
                                        )
                                    ])
                                ],
                                keywords=[]
                            )),
                            ast.Raise()
                        ]
                    )
                ],
                orelse=[],
                finalbody=[]
            )
            
            node.body = [try_node]
            self.changes.append(f"Added error handling to function: {node.name}")
        
        return node


class UndefinedVariableFinder(ast.NodeVisitor):
    """Find undefined variables in AST"""
    
    def __init__(self):
        self.defined_vars = set()
        self.used_vars = set()
        self.undefined_vars = []
        # Add Python builtins
        self.defined_vars.update(['print', 'len', 'range', 'str', 'int', 'float', 
                                 'list', 'dict', 'set', 'tuple', 'bool', 'None', 
                                 'True', 'False', 'Exception', 'self'])
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Add function parameters to defined vars
        for arg in node.args.args:
            self.defined_vars.add(arg.arg)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.defined_vars.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            if node.id not in self.defined_vars and node.id not in self.undefined_vars:
                self.undefined_vars.append(node.id)
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        # Add loop variable to defined vars
        if isinstance(node.target, ast.Name):
            self.defined_vars.add(node.target.id)
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Add exception variable to defined vars
        if node.name:
            self.defined_vars.add(node.name)
        self.generic_visit(node)


class UndefinedVariableTransformer(ast.NodeTransformer):
    """Replace undefined variables with safe defaults using context-aware analysis"""
    
    def __init__(self, undefined_vars: List[str], changes: List[str]):
        self.undefined_vars = set(undefined_vars)
        self.changes = changes
        self.replacement_log = []  # Detailed log of all replacements
        self.context_stack = []  # Track context for better replacement decisions
        self.logger = get_logger("UndefinedVariableTransformer")
    
    def visit_BinOp(self, node: ast.BinOp):
        """Track arithmetic operations context"""
        self.context_stack.append("arithmetic")
        result = self.generic_visit(node)
        self.context_stack.pop()
        return result
    
    def visit_Compare(self, node: ast.Compare):
        """Track comparison operations context"""
        self.context_stack.append("comparison")
        result = self.generic_visit(node)
        self.context_stack.pop()
        return result
    
    def visit_Call(self, node: ast.Call):
        """Track function call context"""
        self.context_stack.append("function_call")
        result = self.generic_visit(node)
        self.context_stack.pop()
        return result
    
    def visit_Subscript(self, node: ast.Subscript):
        """Track subscript context"""
        self.context_stack.append("subscript")
        result = self.generic_visit(node)
        self.context_stack.pop()
        return result
    
    def visit_For(self, node: ast.For):
        """Track iteration context"""
        self.context_stack.append("iteration")
        result = self.generic_visit(node)
        self.context_stack.pop()
        return result
    
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id in self.undefined_vars:
            # Determine appropriate replacement based on context
            replacement_value, reason = self._get_context_aware_replacement(node.id)
            
            # Log the replacement with detailed context information
            replacement_info = {
                "variable": node.id,
                "line": getattr(node, 'lineno', 'unknown'),
                "context": self.context_stack.copy(),
                "replacement": replacement_value,
                "reason": reason,
                "requires_review": self._requires_manual_review(node.id)
            }
            self.replacement_log.append(replacement_info)
            
            # Create warning message for potentially problematic replacements
            warning_level = "CRITICAL" if replacement_info["requires_review"] else "INFO"
            self.logger.warning(
                f"[{warning_level}] Replaced undefined variable '{node.id}' with {replacement_value} "
                f"at line {replacement_info['line']} ({reason})"
            )
            
            # Add to changes list with context information
            context_str = " -> ".join(self.context_stack) if self.context_stack else "general"
            self.changes.append(
                f"Replaced undefined variable '{node.id}' with {replacement_value} "
                f"(context: {context_str}, reason: {reason})"
            )
            
            return ast.Constant(value=replacement_value)
        return node
    
    def _get_context_aware_replacement(self, var_name: str) -> Tuple[Any, str]:
        """Get appropriate replacement value based on current context"""
        current_context = self.context_stack[-1] if self.context_stack else "general"
        
        # Context-specific replacement logic
        if current_context == "arithmetic":
            return 0, "arithmetic context - using 0 to prevent TypeError"
        elif current_context == "comparison":
            return None, "comparison context - using None for safe comparison"
        elif current_context == "iteration":
            return [], "iteration context - using empty list for safe iteration"
        elif current_context == "subscript":
            return {}, "subscript context - using empty dict for safe key access"
        elif current_context == "function_call":
            # Try to infer from variable name
            if any(word in var_name.lower() for word in ["count", "size", "length", "num"]):
                return 0, "function call with numeric variable name"
            elif any(word in var_name.lower() for word in ["list", "items", "data"]):
                return [], "function call with list-like variable name"
            elif any(word in var_name.lower() for word in ["dict", "config", "params"]):
                return {}, "function call with dict-like variable name"
            else:
                return None, "function call context - using None as safe default"
        else:
            # Analyze variable name for hints
            if any(word in var_name.lower() for word in ["count", "index", "size", "length", "num"]):
                return 0, "variable name suggests numeric value"
            elif any(word in var_name.lower() for word in ["list", "items", "data", "results"]):
                return [], "variable name suggests list/array"
            elif any(word in var_name.lower() for word in ["dict", "config", "params", "options"]):
                return {}, "variable name suggests dictionary"
            elif any(word in var_name.lower() for word in ["text", "string", "message", "name"]):
                return "", "variable name suggests string"
            else:
                return None, "general context - using None as safe default"
    
    def _requires_manual_review(self, var_name: str) -> bool:
        """Determine if this replacement requires manual review"""
        # Variables that are likely to be critical for business logic
        critical_patterns = [
            "price", "amount", "cost", "value", "payment", "balance",
            "user", "customer", "account", "id", "key", "token",
            "score", "rate", "percentage", "probability",
            "threshold", "limit", "max", "min",
            "weight", "factor", "multiplier"
        ]
        
        return any(pattern in var_name.lower() for pattern in critical_patterns)
    
    def get_replacement_summary(self) -> Dict[str, Any]:
        """Get a summary of all variable replacements for review"""
        return {
            "total_replacements": len(self.replacement_log),
            "critical_replacements": [r for r in self.replacement_log if r["requires_review"]],
            "replacements_by_context": self._group_by_context(),
            "all_replacements": self.replacement_log
        }
    
    def _group_by_context(self) -> Dict[str, List[Dict]]:
        """Group replacements by their context"""
        grouped = {}
        for replacement in self.replacement_log:
            context = replacement["context"][-1] if replacement["context"] else "general"
            if context not in grouped:
                grouped[context] = []
            grouped[context].append(replacement)
        return grouped


def heal_component(file_path: str, issues: Optional[List[str]] = None) -> bool:
    """
    Convenience function to heal a component file.
    
    Args:
        file_path: Path to the component file
        issues: Optional list of detected issues
        
    Returns:
        bool: True if healing was successful
    """
    healer = ASTHealer()
    
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Auto-detect issues if not provided
        if issues is None:
            issues = []
            try:
                ast.parse(code)
            except SyntaxError:
                issues.append("syntax error")
        
        result = healer.heal_component_code(code, issues)
        
        if result.success and result.healed_code != code:
            # Backup original
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w') as f:
                f.write(code)
            
            # Write healed code
            with open(file_path, 'w') as f:
                f.write(result.healed_code)
            
            logging.info(f"Component healed successfully: {file_path}")
            logging.info(f"Changes made: {result.changes_made}")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Failed to heal component: {e}")
        return False


if __name__ == "__main__":
    # Test the AST healer
    test_code = '''
def process_data(self, data):
    result = data["value"]
    items = data["items"]
    return items[0]
'''
    
    healer = ASTHealer()
    
    print("Original code:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    
    # Test null safety injection
    result = healer.inject_null_safety(test_code)
    print("After null safety injection:")
    print(result.healed_code)
    print(f"Changes: {result.changes_made}")
    
    print("\n" + "="*50 + "\n")
    
    # Test bounds checking
    result = healer.inject_bounds_checking(test_code)
    print("After bounds checking:")
    print(result.healed_code)
    print(f"Changes: {result.changes_made}")