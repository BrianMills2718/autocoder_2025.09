"""
Function analysis using AST.
"""
import ast
from typing import List, Dict, Any


class FunctionAnalyzer(ast.NodeVisitor):
    """Analyzes functions in Python code using AST."""
    
    def __init__(self):
        self.functions: List[Dict[str, Any]] = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        func_info = {
            'name': node.name,
            'args': [arg.arg for arg in node.args.args],
            'is_async': False,
            'line': node.lineno,
            'has_return': any(isinstance(stmt, ast.Return) for stmt in ast.walk(node))
        }
        self.functions.append(func_info)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        func_info = {
            'name': node.name,
            'args': [arg.arg for arg in node.args.args],
            'is_async': True,
            'line': node.lineno,
            'has_return': any(isinstance(stmt, ast.Return) for stmt in ast.walk(node))
        }
        self.functions.append(func_info)
        self.generic_visit(node)


def extract_function_signatures(source_code: str) -> List[Dict[str, Any]]:
    """Extract function signatures from code."""
    try:
        tree = ast.parse(source_code)
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)
        return analyzer.functions
    except:
        return []