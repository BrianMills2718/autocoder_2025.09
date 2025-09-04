"""
Import analysis using AST.
"""
import ast
from typing import List, Set


class ImportAnalyzer(ast.NodeVisitor):
    """Analyzes imports in Python code using AST."""
    
    def __init__(self):
        self.imports: Set[str] = set()
        self.missing_imports: List[str] = []
        
    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from ... import statements."""
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def find_missing_imports(source_code: str) -> List[str]:
    """Find potentially missing imports in code."""
    try:
        tree = ast.parse(source_code)
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        return analyzer.missing_imports
    except:
        return []