#!/usr/bin/env python3
"""
Mutation Testing Framework for TDD Workflow
Implements mutation testing to evaluate test suite quality by introducing deliberate bugs
"""

import ast
import copy
import tempfile
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..observability.structured_logging import get_logger


class MutationType(Enum):
    """Types of mutations that can be applied to code"""
    ARITHMETIC_OPERATOR = "arithmetic_operator"
    COMPARISON_OPERATOR = "comparison_operator" 
    BOOLEAN_OPERATOR = "boolean_operator"
    CONSTANT_REPLACEMENT = "constant_replacement"
    CONDITIONAL_BOUNDARY = "conditional_boundary"
    STATEMENT_DELETION = "statement_deletion"


@dataclass
class MutationResult:
    """Result of applying a single mutation"""
    mutation_type: MutationType
    location: str  # file:line:col
    original_code: str
    mutated_code: str
    survived: bool  # True if mutation was not caught by tests
    test_output: str
    execution_time: float


@dataclass
class MutationReport:
    """Complete mutation testing report"""
    total_mutations: int
    killed_mutations: int
    survived_mutations: int
    mutation_score: float  # killed_mutations / total_mutations
    results: List[MutationResult]
    execution_time: float


class CodeMutator(ast.NodeTransformer):
    """AST transformer that applies mutations to Python code"""
    
    def __init__(self, mutation_type: MutationType, target_location: Optional[Tuple[int, int]] = None):
        self.mutation_type = mutation_type
        self.target_location = target_location  # (line, col) to target specific location
        self.mutations_applied = 0
        self.logger = get_logger(__name__)
        
        # Mutation mappings
        self.arithmetic_mutations = {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.Div,
            ast.Div: ast.Mult,
            ast.Mod: ast.Add,
            ast.Pow: ast.Mult
        }
        
        self.comparison_mutations = {
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
            ast.Lt: ast.Gt,
            ast.Gt: ast.Lt,
            ast.LtE: ast.GtE,
            ast.GtE: ast.LtE,
            ast.Is: ast.IsNot,
            ast.IsNot: ast.Is,
            ast.In: ast.NotIn,
            ast.NotIn: ast.In
        }
        
        self.boolean_mutations = {
            ast.And: ast.Or,
            ast.Or: ast.And
        }
    
    def visit_BinOp(self, node: ast.BinOp) -> ast.BinOp:
        """Mutate arithmetic and boolean operators"""
        if self._should_mutate(node) and self.mutation_type == MutationType.ARITHMETIC_OPERATOR:
            if type(node.op) in self.arithmetic_mutations:
                new_op = self.arithmetic_mutations[type(node.op)]()
                node.op = new_op
                self.mutations_applied += 1
                self.logger.debug(f"Applied arithmetic mutation at line {node.lineno}")
        
        elif self._should_mutate(node) and self.mutation_type == MutationType.BOOLEAN_OPERATOR:
            if type(node.op) in self.boolean_mutations:
                new_op = self.boolean_mutations[type(node.op)]()
                node.op = new_op
                self.mutations_applied += 1
                self.logger.debug(f"Applied boolean mutation at line {node.lineno}")
        
        return self.generic_visit(node)
    
    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        """Mutate comparison operators"""
        if self._should_mutate(node) and self.mutation_type == MutationType.COMPARISON_OPERATOR:
            for i, op in enumerate(node.ops):
                if type(op) in self.comparison_mutations:
                    new_op = self.comparison_mutations[type(op)]()
                    node.ops[i] = new_op
                    self.mutations_applied += 1
                    self.logger.debug(f"Applied comparison mutation at line {node.lineno}")
                    break  # Only mutate first operator
        
        return self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Mutate constant values"""
        if self._should_mutate(node) and self.mutation_type == MutationType.CONSTANT_REPLACEMENT:
            if isinstance(node.value, (int, float)):
                if node.value == 0:
                    node.value = 1
                elif node.value == 1:
                    node.value = 0
                elif node.value > 0:
                    node.value = -node.value
                else:
                    node.value = abs(node.value)
                self.mutations_applied += 1
                self.logger.debug(f"Applied constant mutation at line {node.lineno}")
            
            elif isinstance(node.value, bool):
                node.value = not node.value
                self.mutations_applied += 1
                self.logger.debug(f"Applied boolean constant mutation at line {node.lineno}")
            
            elif isinstance(node.value, str) and node.value:
                node.value = ""
                self.mutations_applied += 1
                self.logger.debug(f"Applied string constant mutation at line {node.lineno}")
        
        return self.generic_visit(node)
    
    def visit_If(self, node: ast.If) -> ast.If:
        """Mutate conditional boundaries"""
        if self._should_mutate(node) and self.mutation_type == MutationType.CONDITIONAL_BOUNDARY:
            # Replace if condition with True or False
            if hasattr(node.test, 'lineno'):
                node.test = ast.Constant(value=False)
                self.mutations_applied += 1
                self.logger.debug(f"Applied conditional boundary mutation at line {node.lineno}")
        
        return self.generic_visit(node)
    
    def _should_mutate(self, node: ast.AST) -> bool:
        """Determine if this node should be mutated based on target location"""
        if self.target_location is None:
            return self.mutations_applied == 0  # Apply only first mutation found
        
        if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            target_line, target_col = self.target_location
            return node.lineno == target_line and node.col_offset >= target_col
        
        return False


class MutationTester:
    """Main mutation testing controller"""
    
    def __init__(self, source_files: List[str], test_command: str = "python -m pytest"):
        self.source_files = [Path(f) for f in source_files]
        self.test_command = test_command
        self.logger = get_logger(__name__)
        
        # Validate source files exist
        for file_path in self.source_files:
            if not file_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
    
    def run_mutation_testing(self, mutation_types: List[MutationType] = None) -> MutationReport:
        """Run complete mutation testing suite"""
        if mutation_types is None:
            mutation_types = list(MutationType)
        
        all_results = []
        start_time = self._get_time()
        
        self.logger.info(f"Starting mutation testing on {len(self.source_files)} files")
        
        # First, verify tests pass on original code
        if not self._run_tests():
            raise RuntimeError("Original tests are failing - cannot proceed with mutation testing")
        
        for source_file in self.source_files:
            self.logger.info(f"Mutating file: {source_file}")
            file_results = self._mutate_file(source_file, mutation_types)
            all_results.extend(file_results)
        
        end_time = self._get_time()
        execution_time = end_time - start_time
        
        # Generate report
        total_mutations = len(all_results)
        killed_mutations = sum(1 for r in all_results if not r.survived)
        survived_mutations = total_mutations - killed_mutations
        mutation_score = killed_mutations / total_mutations if total_mutations > 0 else 0.0
        
        report = MutationReport(
            total_mutations=total_mutations,
            killed_mutations=killed_mutations,
            survived_mutations=survived_mutations,
            mutation_score=mutation_score,
            results=all_results,
            execution_time=execution_time
        )
        
        self.logger.info(f"Mutation testing complete. Score: {mutation_score:.2%} ({killed_mutations}/{total_mutations})")
        
        return report
    
    def _mutate_file(self, source_file: Path, mutation_types: List[MutationType]) -> List[MutationResult]:
        """Apply mutations to a single file and test each one"""
        results = []
        
        # Read original source
        with open(source_file, 'r') as f:
            original_source = f.read()
        
        try:
            original_tree = ast.parse(original_source)
        except SyntaxError as e:
            self.logger.warning(f"Cannot parse {source_file}: {e}")
            return results
        
        # Find potential mutation points
        mutation_points = self._find_mutation_points(original_tree, mutation_types)
        
        self.logger.info(f"Found {len(mutation_points)} potential mutations in {source_file.name}")
        
        # Apply each mutation
        for mutation_type, line, col in mutation_points:
            result = self._test_single_mutation(
                source_file, original_source, original_tree, 
                mutation_type, (line, col)
            )
            if result:
                results.append(result)
        
        return results
    
    def _find_mutation_points(self, tree: ast.AST, mutation_types: List[MutationType]) -> List[Tuple[MutationType, int, int]]:
        """Find all locations where mutations can be applied"""
        points = []
        
        class PointFinder(ast.NodeVisitor):
            def visit_BinOp(self, node):
                if MutationType.ARITHMETIC_OPERATOR in mutation_types:
                    if hasattr(node, 'lineno'):
                        points.append((MutationType.ARITHMETIC_OPERATOR, node.lineno, node.col_offset))
                if MutationType.BOOLEAN_OPERATOR in mutation_types:
                    if hasattr(node, 'lineno'):
                        points.append((MutationType.BOOLEAN_OPERATOR, node.lineno, node.col_offset))
                self.generic_visit(node)
            
            def visit_Compare(self, node):
                if MutationType.COMPARISON_OPERATOR in mutation_types:
                    if hasattr(node, 'lineno'):
                        points.append((MutationType.COMPARISON_OPERATOR, node.lineno, node.col_offset))
                self.generic_visit(node)
            
            def visit_Constant(self, node):
                if MutationType.CONSTANT_REPLACEMENT in mutation_types:
                    if hasattr(node, 'lineno'):
                        points.append((MutationType.CONSTANT_REPLACEMENT, node.lineno, node.col_offset))
                self.generic_visit(node)
            
            def visit_If(self, node):
                if MutationType.CONDITIONAL_BOUNDARY in mutation_types:
                    if hasattr(node, 'lineno'):
                        points.append((MutationType.CONDITIONAL_BOUNDARY, node.lineno, node.col_offset))
                self.generic_visit(node)
        
        finder = PointFinder()
        finder.visit(tree)
        
        return points
    
    def _test_single_mutation(
        self, 
        source_file: Path, 
        original_source: str, 
        original_tree: ast.AST,
        mutation_type: MutationType, 
        location: Tuple[int, int]
    ) -> Optional[MutationResult]:
        """Test a single mutation"""
        line, col = location
        
        try:
            # Apply mutation
            mutated_tree = copy.deepcopy(original_tree)
            mutator = CodeMutator(mutation_type, location)
            mutated_tree = mutator.visit(mutated_tree)
            
            if mutator.mutations_applied == 0:
                return None  # No mutation was actually applied
            
            # Generate mutated source code
            try:
                mutated_source = ast.unparse(mutated_tree)
            except Exception as e:
                self.logger.warning(f"Cannot unparse mutated AST: {e}")
                return None
            
            # Create temporary file with mutation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(mutated_source)
                temp_file_path = temp_file.name
            
            try:
                # Backup original file and replace with mutated version
                backup_path = str(source_file) + '.backup'
                os.rename(source_file, backup_path)
                os.rename(temp_file_path, source_file)
                
                # Run tests
                start_time = self._get_time()
                test_passed = self._run_tests()
                execution_time = self._get_time() - start_time
                
                # Mutation survived if tests still pass
                survived = test_passed
                
                return MutationResult(
                    mutation_type=mutation_type,
                    location=f"{source_file.name}:{line}:{col}",
                    original_code=self._extract_line(original_source, line),
                    mutated_code=self._extract_line(mutated_source, line),
                    survived=survived,
                    test_output="Tests passed" if test_passed else "Tests failed",
                    execution_time=execution_time
                )
            
            finally:
                # Restore original file
                if os.path.exists(backup_path):
                    if os.path.exists(source_file):
                        os.remove(source_file)
                    os.rename(backup_path, source_file)
                
                # Clean up temp file if it still exists
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        except Exception as e:
            self.logger.error(f"Error testing mutation at {source_file}:{line}:{col}: {e}")
            return None
    
    def _run_tests(self) -> bool:
        """Run test suite and return True if all tests pass"""
        try:
            result = subprocess.run(
                self.test_command.split(), 
                capture_output=True, 
                text=True, 
                timeout=60  # 1 minute timeout
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.logger.warning("Test execution timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running tests: {e}")
            return False
    
    def _extract_line(self, source: str, line_number: int) -> str:
        """Extract a specific line from source code"""
        lines = source.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
    
    def _get_time(self) -> float:
        """Get current time for timing measurements"""
        import time
        return time.time()


def generate_mutation_report(report: MutationReport, output_file: str = "mutation_report.html") -> None:
    """Generate HTML report for mutation testing results"""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mutation Testing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .score {{ font-size: 24px; font-weight: bold; color: {'green' if report.mutation_score >= 0.8 else 'orange' if report.mutation_score >= 0.6 else 'red'}; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .survived {{ background-color: #ffcccc; }}
        .killed {{ background-color: #ccffcc; }}
    </style>
</head>
<body>
    <h1>Mutation Testing Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="score">Mutation Score: {report.mutation_score:.2%}</div>
        <p>Total Mutations: {report.total_mutations}</p>
        <p>Killed Mutations: {report.killed_mutations}</p>
        <p>Survived Mutations: {report.survived_mutations}</p>
        <p>Execution Time: {report.execution_time:.2f} seconds</p>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Location</th>
            <th>Mutation Type</th>
            <th>Original Code</th>
            <th>Mutated Code</th>
            <th>Status</th>
            <th>Execution Time</th>
        </tr>
    """
    
    for result in report.results:
        status_class = "survived" if result.survived else "killed"
        status_text = "SURVIVED" if result.survived else "KILLED"
        
        html_content += f"""
        <tr class="{status_class}">
            <td>{result.location}</td>
            <td>{result.mutation_type.value}</td>
            <td><code>{result.original_code}</code></td>
            <td><code>{result.mutated_code}</code></td>
            <td>{status_text}</td>
            <td>{result.execution_time:.3f}s</td>
        </tr>
        """
    
    html_content += """
    </table>
    
    <div style="margin-top: 20px;">
        <h3>Interpretation</h3>
        <p><strong>Killed mutations</strong> indicate that the test suite successfully detected the introduced bug.</p>
        <p><strong>Survived mutations</strong> indicate potential weaknesses in the test suite.</p>
        <p>A mutation score above 80% is generally considered good test coverage.</p>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Run mutation testing")
    parser.add_argument("source_files", nargs="+", help="Source files to mutate")
    parser.add_argument("--test-command", default="python -m pytest", help="Command to run tests")
    parser.add_argument("--output", default="mutation_report.html", help="Output report file")
    
    args = parser.parse_args()
    
    tester = MutationTester(args.source_files, args.test_command)
    report = tester.run_mutation_testing()
    generate_mutation_report(report, args.output)
    
    print(f"Mutation testing complete. Score: {report.mutation_score:.2%}")
    print(f"Report saved to: {args.output}")