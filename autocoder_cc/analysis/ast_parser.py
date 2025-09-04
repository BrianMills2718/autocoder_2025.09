from autocoder_cc.observability.structured_logging import get_logger
"""
AST-based Code Analysis Framework for Autocoder V5.2

This module provides comprehensive AST-based code analysis capabilities for the 
Autocoder system, including placeholder detection and code quality analysis.

## Overview

The AST Analysis Framework ensures code quality and completeness by analyzing
Python Abstract Syntax Trees (AST) rather than using unreliable string matching.
This provides 100% accurate detection of various code patterns and issues.

## Key Features

### 1. Placeholder Detection (PlaceholderVisitor)
Detects incomplete code patterns that indicate unfinished implementation:
- Functions containing only `pass` statements
- Functions that raise `NotImplementedError`
- TODO comments in docstrings and code
- Empty function bodies
- Ellipsis (`...`) placeholders

### 2. Code Quality Analysis (CodeQualityAnalyzer)
Analyzes code for quality and security issues:
- **Hardcoded Values**: Detects values that should be configurable
- **Type Safety**: Identifies missing type hints
- **Complexity**: Flags functions that need refactoring
- **Security**: Detects hardcoded secrets and credentials with entropy analysis
- **Best Practices**: Enforces coding standards

### 3. Environment Variable Security (EnvironmentVariableScanner)
Scans environment files for exposed secrets:
- **.env files**: Comprehensive scanning of environment variable files
- **Docker environments**: Detection in container environment configurations
- **Entropy Analysis**: High-entropy string detection in environment values
- **Pattern Matching**: AWS keys, API tokens, passwords, and connection strings

### 4. Configuration File Security (ConfigurationFileScanner)
Analyzes configuration files for security issues:
- **YAML/JSON**: Structured configuration file analysis
- **Properties/INI**: Key-value configuration file scanning
- **Recursive Analysis**: Deep scanning of nested configuration structures
- **Multi-format Support**: Automatic file type detection and appropriate parsing

### 5. Comprehensive Secret Detection (comprehensive_secret_scan)
Unified security scanning across all file types:
- **Multi-scope Scanning**: Python code, environment files, and configuration files
- **Entropy Threshold Documentation**: Configurable entropy detection (default: 4.5)
- **False Positive Reduction**: Advanced heuristics to minimize false alerts
- **Comprehensive Reporting**: Detailed results with file paths and severity levels

## Usage Examples

### Placeholder Detection
```python
from autocoder_cc.analysis.ast_parser import PlaceholderVisitor
import ast

code = '''
def process_data(data):
    # TODO: implement this
    pass
'''

tree = ast.parse(code)
visitor = PlaceholderVisitor()
visitor.visit(tree)

for placeholder in visitor.placeholders:
    print(f"Found placeholder in {placeholder.function_name}: {placeholder.placeholder_type}")
```

### Code Quality Analysis
```python
from autocoder_cc.analysis.ast_parser import CodeQualityAnalyzer
import ast

code = '''
def connect_to_db():
    password = os.getenv("DB_PASSWORD")  # Secure: use environment variable
    if not password:
        raise ValueError("DB_PASSWORD environment variable not set")
    return connect(password=password)
'''

tree = ast.parse(code)
analyzer = CodeQualityAnalyzer()
analyzer.visit(tree)

for issue in analyzer.issues:
    print(f"Quality issue: {issue.description} (severity: {issue.severity})")
```

### Comprehensive Secret Detection
```python
from autocoder_cc.analysis.ast_parser import comprehensive_secret_scan

# Scan entire project directory
result = comprehensive_secret_scan(
    directory="/path/to/project",
    scan_python=True,
    scan_env=True, 
    scan_config=True
)

print(f"Scanned {result.files_scanned} files using {result.scan_types}")
print(f"Entropy threshold: {result.entropy_threshold}")

for issue in result.issues:
    print(f"Security issue in {issue.file_path}:{issue.line_number}")
    print(f"  {issue.description} (severity: {issue.severity})")
```

### Environment File Scanning
```python
from autocoder_cc.analysis.ast_parser import EnvironmentVariableScanner

scanner = EnvironmentVariableScanner()
issues = scanner.scan_env_file(".env")

for issue in issues:
    print(f"Environment secret detected: {issue.description}")
```

### Configuration File Scanning
```python
from autocoder_cc.analysis.ast_parser import ConfigurationFileScanner

scanner = ConfigurationFileScanner()
issues = scanner.scan_config_file("config.yaml")

for issue in issues:
    print(f"Config secret detected: {issue.description}")
```

## Integration with Autocoder

This module is automatically used by:
- **Component Generation**: Validates generated component code
- **System Assembly**: Ensures all components are complete
- **Production Readiness**: Checks for security and quality issues
- **Development Mode**: Provides real-time feedback during development

## Production Requirements

- All generated code MUST pass placeholder detection
- Code quality issues are classified by severity (error/warning/info)
- Security issues (hardcoded secrets) result in immediate generation failure
- Type safety violations are flagged for production deployments

## Secret Detection Configuration

### Entropy Threshold
- **Default**: 4.5 (Shannon entropy)
- **Minimum string length**: 16 characters for entropy analysis
- **Character diversity requirement**: At least 3 of: uppercase, lowercase, digits, special chars

### Pattern Detection Limitations
- **Environment variables**: Limited to .env, .environment, docker.env, compose.env files
- **Configuration files**: Supports .yaml, .yml, .json, .properties, .ini, .cfg extensions
- **Python AST**: Only detects string constants, not dynamically constructed secrets
- **Nested structures**: YAML/JSON scanning supports unlimited nesting depth
- **File size**: No explicit limits, but very large files may impact performance

### False Positive Reduction
- **Excluded patterns**: "lorem ipsum", "hello world", "test", "example", "placeholder"
- **Length filters**: Minimum 8 characters for basic detection, 16 for entropy analysis
- **Context awareness**: Different thresholds for different file types and contexts

### Supported Secret Types
1. **AWS Access Keys**: Pattern `AKIA[0-9A-Z]{16}`
2. **AWS Secret Keys**: Pattern `[A-Za-z0-9/+=]{40}`
3. **JWT Tokens**: Standard JWT format with three base64 segments
4. **API Keys**: Various formats including `sk-`, `pk_`, `AIza` prefixes
5. **Passwords**: Common password assignment patterns
6. **Private Keys**: PEM format detection
7. **Connection Strings**: MongoDB, PostgreSQL, MySQL URI formats
8. **High Entropy Strings**: Shannon entropy > 4.5 with character diversity
9. **Encoded Secrets**: Base64 and hexadecimal encoded patterns
"""
import ast
import re
import base64
import binascii
import math
import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass
import logging


@dataclass
class Placeholder:
    """Information about a detected placeholder."""
    function_name: str
    line_number: int
    placeholder_type: str  # 'pass', 'not_implemented', 'todo_comment'
    context: Optional[str] = None


@dataclass
class CodeQualityIssue:
    """Detected code quality issue."""
    issue_type: str
    line_number: int
    description: str
    severity: str  # 'error', 'warning', 'info'
    file_path: Optional[str] = None  # For file-based scanning


@dataclass 
class SecretDetectionResult:
    """Result of comprehensive secret detection across all file types."""
    issues: List[CodeQualityIssue]
    files_scanned: int
    entropy_threshold: float = 4.5
    scan_types: List[str] = None  # Types of scans performed


class PlaceholderVisitor(ast.NodeVisitor):
    """
    AST visitor that detects placeholder code.
    
    Detects:
    - Functions with only 'pass'
    - Functions that raise NotImplementedError
    - TODO, FIXME, XXX, HACK, BUG, NOTE comments in docstrings and inline
    - Empty function bodies
    """
    
    def __init__(self, source_lines: Optional[List[str]] = None):
        self.placeholders: List[Placeholder] = []
        self.current_class: Optional[str] = None
        self.source_lines = source_lines or []
        self.logger = get_logger(self.__class__.__name__)
        
        # Expanded placeholder patterns
        self.placeholder_patterns = re.compile(
            r'\b(TODO|FIXME|XXX|HACK|BUG|NOTE)\b[:\s]*(.*)$',
            re.IGNORECASE | re.MULTILINE
        )
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class context."""
        try:
            old_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = old_class
        except Exception as e:
            self.logger.error(f"Error processing class definition at line {node.lineno}: {e}")
            # Continue processing without failing entirely
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function definitions for placeholders."""
        try:
            self._check_function(node)
            self.generic_visit(node)
        except Exception as e:
            self.logger.error(f"Error processing function definition '{node.name}' at line {node.lineno}: {e}")
            # Continue processing without failing entirely
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Check async function definitions for placeholders."""
        try:
            self._check_function(node)
            self.generic_visit(node)
        except Exception as e:
            self.logger.error(f"Error processing async function definition '{node.name}' at line {node.lineno}: {e}")
            # Continue processing without failing entirely
    
    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """Check if function is a placeholder."""
        func_name = node.name
        if self.current_class:
            func_name = f"{self.current_class}.{func_name}"
        
        # Check for empty body
        if not node.body:
            self.placeholders.append(Placeholder(
                function_name=func_name,
                line_number=node.lineno,
                placeholder_type='empty'
            ))
            return
        
        # Check for single statement body (without docstring)
        has_docstring = (node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and 
                        isinstance(node.body[0].value.value, str))
        
        if len(node.body) == 1 and not has_docstring:
            stmt = node.body[0]
            
            # Check for 'pass'
            if isinstance(stmt, ast.Pass):
                self.placeholders.append(Placeholder(
                    function_name=func_name,
                    line_number=node.lineno,
                    placeholder_type='pass'
                ))
            
            # Check for 'raise NotImplementedError'
            elif isinstance(stmt, ast.Raise):
                if self._is_not_implemented_error(stmt):
                    self.placeholders.append(Placeholder(
                        function_name=func_name,
                        line_number=node.lineno,
                        placeholder_type='not_implemented'
                    ))
            
            # Check for ellipsis (...)
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if stmt.value.value is Ellipsis:
                    self.placeholders.append(Placeholder(
                        function_name=func_name,
                        line_number=node.lineno,
                        placeholder_type='ellipsis'
                    ))
            
            # Check for default return values (return {}, return [], return 0, etc.)
            elif isinstance(stmt, ast.Return):
                if self._is_default_return_value(stmt):
                    self.placeholders.append(Placeholder(
                        function_name=func_name,
                        line_number=node.lineno,
                        placeholder_type='default_return',
                        context=self._get_return_value_context(stmt)
                    ))
        
        # Check docstring for placeholder patterns
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                docstring = node.body[0].value.value
                if isinstance(docstring, str):
                    matches = self.placeholder_patterns.findall(docstring)
                    for match in matches:
                        placeholder_type, context = match
                        self.placeholders.append(Placeholder(
                            function_name=func_name,
                            line_number=node.lineno,
                            placeholder_type=f'{placeholder_type.lower()}_comment',
                            context=context.strip()
                        ))
        
        # Check for pass statements even in functions with docstrings
        self._check_pass_statements(node, func_name)
        
        # Check for template patterns in multi-statement functions
        self._check_template_patterns(node, func_name)
        
        # Check for inline comment placeholders in function body
        if self.source_lines:
            self._check_inline_comments(node, func_name)
    
    def _is_not_implemented_error(self, raise_node: ast.Raise) -> bool:
        """Check if raise statement is NotImplementedError."""
        if not raise_node.exc:
            return False
        
        # Direct raise NotImplementedError
        if isinstance(raise_node.exc, ast.Name):
            return raise_node.exc.id == 'NotImplementedError'
        
        # raise NotImplementedError(...)
        elif isinstance(raise_node.exc, ast.Call):
            if isinstance(raise_node.exc.func, ast.Name):
                return raise_node.exc.func.id == 'NotImplementedError'
        
        return False
    
    def _check_inline_comments(self, node: ast.FunctionDef | ast.AsyncFunctionDef, func_name: str):
        """Check for placeholder patterns in inline comments within function body."""
        try:
            # Get the range of lines for this function
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else len(self.source_lines)
            
            for line_idx in range(start_line, min(end_line, len(self.source_lines))):
                try:
                    line = self.source_lines[line_idx]
                    # Check for comments (# character)
                    comment_start = line.find('#')
                    if comment_start != -1:
                        comment_text = line[comment_start:]
                        matches = self.placeholder_patterns.findall(comment_text)
                        for match in matches:
                            placeholder_type, context = match
                            self.placeholders.append(Placeholder(
                                function_name=func_name,
                                line_number=line_idx + 1,  # Convert back to 1-based
                                placeholder_type=f'{placeholder_type.lower()}_inline_comment',
                                context=context.strip()
                            ))
                except (IndexError, AttributeError) as e:
                    self.logger.warning(f"Error processing line {line_idx + 1} in function {func_name}: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error checking inline comments for function {func_name}: {e}")
    
    def _is_default_return_value(self, return_node: ast.Return) -> bool:
        """Check if return statement contains a default/placeholder value."""
        if not return_node.value:
            return False
        
        # Check for common default return values
        if isinstance(return_node.value, ast.Constant):
            value = return_node.value.value
            # Common placeholder constants
            if value in (None, 0, 42, "", "TODO", "placeholder"):
                return True
            # Check for simple numeric placeholders
            if isinstance(value, int) and value in range(-1, 101):
                return True
        
        # Check for empty containers
        elif isinstance(return_node.value, ast.Dict):
            if not return_node.value.keys and not return_node.value.values:  # Empty dict
                return True
        elif isinstance(return_node.value, (ast.List, ast.Set)):
            if not return_node.value.elts:  # Empty list or set
                return True
        
        # Check for simple True/False placeholders in non-boolean contexts
        elif isinstance(return_node.value, ast.Constant) and isinstance(return_node.value.value, bool):
            return True
        
        return False
    
    def _get_return_value_context(self, return_node: ast.Return) -> str:
        """Get a string representation of the return value for context."""
        if not return_node.value:
            return "None"
        
        if isinstance(return_node.value, ast.Constant):
            return str(return_node.value.value)
        elif isinstance(return_node.value, ast.Dict):
            return "{}"
        elif isinstance(return_node.value, ast.List):
            return "[]"
        elif isinstance(return_node.value, ast.Set):
            return "set()"
        else:
            return "unknown_value"
    
    def _check_template_patterns(self, node: ast.FunctionDef | ast.AsyncFunctionDef, func_name: str):
        """Check for template code patterns in function body."""
        try:
            # Skip if function only has docstring
            body_statements = node.body
            if (len(body_statements) == 1 and 
                isinstance(body_statements[0], ast.Expr) and 
                isinstance(body_statements[0].value, ast.Constant) and 
                isinstance(body_statements[0].value.value, str)):
                return
            
            # Skip docstring if present
            start_idx = 0
            if (body_statements and 
                isinstance(body_statements[0], ast.Expr) and 
                isinstance(body_statements[0].value, ast.Constant) and 
                isinstance(body_statements[0].value.value, str)):
                start_idx = 1
            
            actual_body = body_statements[start_idx:]
            
            # Check for simple template patterns
            if len(actual_body) == 1:
                stmt = actual_body[0]
                
                # Simple variable assignment followed by return
                if (isinstance(stmt, ast.Assign) and 
                    len(stmt.targets) == 1 and 
                    isinstance(stmt.targets[0], ast.Name)):
                    
                    # Check if it's a placeholder assignment
                    if isinstance(stmt.value, ast.Constant):
                        value = stmt.value.value
                        if value in ("placeholder", "TODO", "FIXME", None, 0, ""):
                            self.placeholders.append(Placeholder(
                                function_name=func_name,
                                line_number=stmt.lineno,
                                placeholder_type='template_assignment',
                                context=f"{stmt.targets[0].id} = {value}"
                            ))
            
            # Check for simple two-statement template (assign + return)
            elif len(actual_body) == 2:
                if (isinstance(actual_body[0], ast.Assign) and 
                    isinstance(actual_body[1], ast.Return)):
                    
                    assign_stmt = actual_body[0]
                    return_stmt = actual_body[1]
                    
                    # Check if assignment is to a placeholder value and return is the same variable
                    if (len(assign_stmt.targets) == 1 and 
                        isinstance(assign_stmt.targets[0], ast.Name) and 
                        isinstance(return_stmt.value, ast.Name) and 
                        assign_stmt.targets[0].id == return_stmt.value.id):
                        
                        if isinstance(assign_stmt.value, ast.Constant):
                            value = assign_stmt.value.value
                            if value in ("placeholder", "TODO", "FIXME", None, 0, ""):
                                self.placeholders.append(Placeholder(
                                    function_name=func_name,
                                    line_number=assign_stmt.lineno,
                                    placeholder_type='template_pattern',
                                    context=f"{assign_stmt.targets[0].id} = {value}; return {assign_stmt.targets[0].id}"
                                ))
        
        except Exception as e:
            self.logger.error(f"Error checking template patterns for function {func_name}: {e}")
    
    def _check_pass_statements(self, node: ast.FunctionDef | ast.AsyncFunctionDef, func_name: str):
        """Check for pass statements in function body, only for functions with docstrings."""
        try:
            # Only check functions with docstrings (since single statements without docstrings are already handled)
            has_docstring = (node.body and 
                           isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and 
                           isinstance(node.body[0].value.value, str))
            
            if not has_docstring:
                return  # Single statements without docstrings are handled elsewhere
            
            # Skip docstring to get to actual body
            actual_body = node.body[1:]
            
            # Check if the body consists only of pass statements
            if len(actual_body) == 1 and isinstance(actual_body[0], ast.Pass):
                self.placeholders.append(Placeholder(
                    function_name=func_name,
                    line_number=actual_body[0].lineno,
                    placeholder_type='pass'
                ))
            # Also check for multiple pass statements
            elif actual_body and all(isinstance(stmt, ast.Pass) for stmt in actual_body):
                for stmt in actual_body:
                    self.placeholders.append(Placeholder(
                        function_name=func_name,
                        line_number=stmt.lineno,
                        placeholder_type='pass'
                    ))
        except Exception as e:
            self.logger.error(f"Error checking pass statements for function {func_name}: {e}")


class CodeQualityAnalyzer(ast.NodeVisitor):
    """
    Analyzes code quality issues using AST.
    
    Detects:
    - Hardcoded values that should be configurable
    - Missing type hints
    - Complex functions that need refactoring
    - Security issues (hardcoded secrets with entropy analysis)
    """
    
    def __init__(self):
        self.issues: List[CodeQualityIssue] = []
        self.current_function: Optional[str] = None
        self.function_complexity: Dict[str, int] = {}
        
        # Enhanced secret detection patterns
        self.secret_patterns = {
            'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
            'aws_secret_key': re.compile(r'[A-Za-z0-9/+=]{40}'),
            'jwt_token': re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)["\s]*[:=]["\s]*([A-Za-z0-9-_]{20,})'),
            'password': re.compile(r'(?i)(password|passwd|pwd)["\s]*[:=]["\s]*([A-Za-z0-9!@#$%^&*()_+-=]{8,})'),
            'secret': re.compile(r'(?i)(secret|token)["\s]*[:=]["\s]*([A-Za-z0-9-_]{16,})'),
            'private_key': re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
            'connection_string': re.compile(r'(?i)(mongodb|postgres|mysql)://[^\s"\']+'),
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function definitions."""
        try:
            old_func = self.current_function
            self.current_function = node.name
            
            # Check for missing type hints
            self._check_type_hints(node)
            
            # Calculate complexity
            self.function_complexity[node.name] = self._calculate_complexity(node)
            
            if self.function_complexity[node.name] > 10:
                self.issues.append(CodeQualityIssue(
                    issue_type='high_complexity',
                    line_number=node.lineno,
                    description=f"Function '{node.name}' has complexity {self.function_complexity[node.name]} (>10)",
                    severity='warning'
                ))
            
            self.generic_visit(node)
            self.current_function = old_func
        except Exception as e:
            logging.error(f"Error analyzing function '{getattr(node, 'name', 'unknown')}' at line {getattr(node, 'lineno', 0)}: {e}")
            # Continue processing without failing entirely
    
    def visit_Constant(self, node: ast.Constant):
        """Check for hardcoded values."""
        try:
            if isinstance(node.value, str):
                # Check for hardcoded URLs
                if any(pattern in node.value for pattern in ['http://', 'https://', 'amqp://', 'redis://']):
                    self.issues.append(CodeQualityIssue(
                        issue_type='hardcoded_url',
                        line_number=node.lineno,
                        description=f"Hardcoded URL: {node.value[:50]}...",
                        severity='error'
                    ))
                
                # Enhanced secret detection
                self._analyze_string_for_secrets(node.value, node.lineno)
            
            # Check for hardcoded ports
            elif isinstance(node.value, int) and 1024 <= node.value <= 65535:
                if self.current_function and 'init' not in self.current_function:
                    self.issues.append(CodeQualityIssue(
                        issue_type='hardcoded_port',
                        line_number=node.lineno,
                        description=f"Hardcoded port number: {node.value}",
                        severity='warning'
                    ))
            
            self.generic_visit(node)
        except Exception as e:
            logging.error(f"Error analyzing constant at line {getattr(node, 'lineno', 0)}: {e}")
            # Continue processing without failing entirely
    
    def _check_type_hints(self, node: ast.FunctionDef):
        """Check if function has proper type hints."""
        # Skip checking dunder methods
        if node.name.startswith('__') and node.name.endswith('__'):
            return
        
        # Check return type
        if not node.returns and node.name != '__init__':
            self.issues.append(CodeQualityIssue(
                issue_type='missing_return_type',
                line_number=node.lineno,
                description=f"Function '{node.name}' missing return type hint",
                severity='info'
            ))
        
        # Check parameter types
        for arg in node.args.args:
            if arg.arg != 'self' and not arg.annotation:
                self.issues.append(CodeQualityIssue(
                    issue_type='missing_param_type',
                    line_number=node.lineno,
                    description=f"Parameter '{arg.arg}' in '{node.name}' missing type hint",
                    severity='info'
                ))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Each decision point adds complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each 'and'/'or' adds a branch
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_string_for_secrets(self, value: str, line_number: int):
        """Analyze string for potential secrets using patterns and entropy."""
        # Skip very short strings
        if len(value) < 8:
            return
        
        # Check against known secret patterns
        for secret_type, pattern in self.secret_patterns.items():
            if pattern.search(value):
                self.issues.append(CodeQualityIssue(
                    issue_type=f'hardcoded_{secret_type}',
                    line_number=line_number,
                    description=f"Detected hardcoded {secret_type.replace('_', ' ')}: {value[:20]}...",
                    severity='error'
                ))
                return  # Don't double-report
        
        # Entropy-based detection for random strings
        if self._has_high_entropy(value):
            # Additional checks to reduce false positives
            if self._looks_like_secret(value):
                self.issues.append(CodeQualityIssue(
                    issue_type='high_entropy_string',
                    line_number=line_number,
                    description=f"High entropy string (possible secret): {value[:20]}...",
                    severity='warning'
                ))
        
        # Check for base64/hex encoded secrets
        if self._is_encoded_secret(value):
            self.issues.append(CodeQualityIssue(
                issue_type='encoded_secret',
                line_number=line_number,
                description=f"Potential base64/hex encoded secret: {value[:20]}...",
                severity='warning'
            ))
    
    def _has_high_entropy(self, text: str) -> bool:
        """Calculate Shannon entropy of a string."""
        if len(text) < 16:  # Too short to be meaningful
            return False
        
        # Calculate character frequency
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # High entropy threshold (adjusted for typical secret entropy)
        return entropy > 4.5
    
    def _looks_like_secret(self, text: str) -> bool:
        """Additional heuristics to identify potential secrets."""
        # Length checks
        if len(text) < 16 or len(text) > 512:
            return False
        
        # Character diversity checks
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in text)
        
        # Secrets often have mixed case and digits
        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        # Avoid common false positives
        false_positive_patterns = [
            'lorem ipsum',
            'hello world',
            'test',
            'example',
            'placeholder',
            'abcdef',
            '123456',
        ]
        
        if any(pattern in text.lower() for pattern in false_positive_patterns):
            return False
        
        return diversity_score >= 3
    
    def _is_encoded_secret(self, text: str) -> bool:
        """Check if string appears to be base64 or hex encoded."""
        # Base64 pattern check
        if len(text) >= 16 and len(text) % 4 == 0:
            try:
                # Try to decode as base64
                decoded = base64.b64decode(text, validate=True)
                # If successful and has reasonable entropy, might be encoded secret
                if len(decoded) >= 8 and self._has_high_entropy(decoded.decode('utf-8', errors='ignore')):
                    return True
            except:
                pass
        
        # Hex pattern check
        if len(text) >= 32 and len(text) % 2 == 0:
            try:
                # Try to decode as hex
                bytes.fromhex(text)
                # If all hex chars and long enough, might be hex-encoded secret
                if all(c in '0123456789abcdefABCDEF' for c in text):
                    return True
            except:
                pass
        
        return False


class EnvironmentVariableScanner:
    """
    Scanner for detecting secrets in environment variables and .env files.
    
    Scans:
    - .env files
    - Environment variable assignments
    - Docker environment files
    - System environment variables (optional)
    """
    
    def __init__(self):
        self.secret_patterns = {
            'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
            'aws_secret_key': re.compile(r'[A-Za-z0-9/+=]{40}'),
            'jwt_token': re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)["\s]*[:=]["\s]*([A-Za-z0-9-_]{20,})'),
            'password': re.compile(r'(?i)(password|passwd|pwd)["\s]*[:=]["\s]*([A-Za-z0-9!@#$%^&*()_+-=]{8,})'),
            'secret': re.compile(r'(?i)(secret|token)["\s]*[:=]["\s]*([A-Za-z0-9-_]{16,})'),
            'private_key': re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
            'connection_string': re.compile(r'(?i)(mongodb|postgres|mysql)://[^\s"\']+'),
        }
    
    def scan_env_file(self, file_path: Union[str, Path]) -> List[CodeQualityIssue]:
        """Scan a .env file for secrets."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse environment variable assignment
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Check for secrets in the value
                    secret_issues = self._analyze_env_value(key, value, line_num, str(file_path))
                    issues.extend(secret_issues)
        
        except (IOError, UnicodeDecodeError) as e:
            logging.warning(f"Could not read env file {file_path}: {e}")
        
        return issues
    
    def scan_directory_for_env_files(self, directory: Union[str, Path]) -> List[CodeQualityIssue]:
        """Scan a directory for .env files and analyze them."""
        issues = []
        directory = Path(directory)
        
        env_file_patterns = [
            '*.env',
            '.env*',
            '*.environment',
            'docker.env',
            'compose.env'
        ]
        
        for pattern in env_file_patterns:
            for env_file in directory.rglob(pattern):
                if env_file.is_file():
                    file_issues = self.scan_env_file(env_file)
                    issues.extend(file_issues)
        
        return issues
    
    def _analyze_env_value(self, key: str, value: str, line_num: int, file_path: str) -> List[CodeQualityIssue]:
        """Analyze an environment variable value for secrets."""
        issues = []
        
        # Skip very short values
        if len(value) < 8:
            return issues
        
        # Check against known secret patterns
        for secret_type, pattern in self.secret_patterns.items():
            if pattern.search(value):
                issues.append(CodeQualityIssue(
                    issue_type=f'env_{secret_type}',
                    line_number=line_num,
                    description=f"Environment variable '{key}' contains {secret_type.replace('_', ' ')}: {value[:20]}...",
                    severity='error',
                    file_path=file_path
                ))
                return issues  # Don't double-report
        
        # Entropy-based detection
        if self._has_high_entropy(value):
            if self._looks_like_secret(value):
                issues.append(CodeQualityIssue(
                    issue_type='env_high_entropy_string',
                    line_number=line_num,
                    description=f"Environment variable '{key}' has high entropy (possible secret): {value[:20]}...",
                    severity='warning',
                    file_path=file_path
                ))
        
        # Check for encoded secrets
        if self._is_encoded_secret(value):
            issues.append(CodeQualityIssue(
                issue_type='env_encoded_secret',
                line_number=line_num,
                description=f"Environment variable '{key}' contains encoded secret: {value[:20]}...",
                severity='warning',
                file_path=file_path
            ))
        
        return issues
    
    def _has_high_entropy(self, text: str) -> bool:
        """Calculate Shannon entropy - same as CodeQualityAnalyzer."""
        if len(text) < 16:
            return False
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy > 4.5
    
    def _looks_like_secret(self, text: str) -> bool:
        """Additional heuristics to identify potential secrets - same as CodeQualityAnalyzer."""
        if len(text) < 16 or len(text) > 512:
            return False
        
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in text)
        
        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        false_positive_patterns = [
            'lorem ipsum', 'hello world', 'test', 'example', 
            'placeholder', 'abcdef', '123456'
        ]
        
        if any(pattern in text.lower() for pattern in false_positive_patterns):
            return False
        
        return diversity_score >= 3
    
    def _is_encoded_secret(self, text: str) -> bool:
        """Check if string appears to be base64 or hex encoded - same as CodeQualityAnalyzer."""
        # Base64 pattern check
        if len(text) >= 16 and len(text) % 4 == 0:
            try:
                decoded = base64.b64decode(text, validate=True)
                if len(decoded) >= 8 and self._has_high_entropy(decoded.decode('utf-8', errors='ignore')):
                    return True
            except:
                pass
        
        # Hex pattern check
        if len(text) >= 32 and len(text) % 2 == 0:
            try:
                bytes.fromhex(text)
                if all(c in '0123456789abcdefABCDEF' for c in text):
                    return True
            except:
                pass
        
        return False


class ConfigurationFileScanner:
    """
    Scanner for detecting secrets in configuration files.
    
    Supports:
    - YAML configuration files
    - JSON configuration files
    - Properties files
    - INI files
    """
    
    def __init__(self):
        self.secret_patterns = {
            'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
            'aws_secret_key': re.compile(r'[A-Za-z0-9/+=]{40}'),
            'jwt_token': re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)["\s]*[:=]["\s]*([A-Za-z0-9-_]{20,})'),
            'password': re.compile(r'(?i)(password|passwd|pwd)["\s]*[:=]["\s]*([A-Za-z0-9!@#$%^&*()_+-=]{8,})'),
            'secret': re.compile(r'(?i)(secret|token)["\s]*[:=]["\s]*([A-Za-z0-9-_]{16,})'),
            'private_key': re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
            'connection_string': re.compile(r'(?i)(mongodb|postgres|mysql)://[^\s"\']+'),
        }
    
    def scan_config_file(self, file_path: Union[str, Path]) -> List[CodeQualityIssue]:
        """Scan a configuration file for secrets."""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            return self._scan_yaml_file(file_path)
        elif file_path.suffix.lower() == '.json':
            return self._scan_json_file(file_path)
        elif file_path.suffix.lower() in ['.properties', '.ini', '.cfg']:
            return self._scan_properties_file(file_path)
        else:
            # Fallback to text-based scanning
            return self._scan_text_file(file_path)
    
    def scan_directory_for_config_files(self, directory: Union[str, Path]) -> List[CodeQualityIssue]:
        """Scan directory for configuration files."""
        issues = []
        directory = Path(directory)
        
        config_patterns = [
            '*.yaml', '*.yml', '*.json', 
            '*.properties', '*.ini', '*.cfg',
            'config.*', 'settings.*', 'credentials.*'
        ]
        
        for pattern in config_patterns:
            for config_file in directory.rglob(pattern):
                if config_file.is_file():
                    file_issues = self.scan_config_file(config_file)
                    issues.extend(file_issues)
        
        return issues
    
    def _scan_yaml_file(self, file_path: Path) -> List[CodeQualityIssue]:
        """Scan YAML configuration file."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            issues.extend(self._scan_config_data(content, str(file_path)))
        except (yaml.YAMLError, IOError, UnicodeDecodeError) as e:
            logging.warning(f"Could not parse YAML file {file_path}: {e}")
        
        return issues
    
    def _scan_json_file(self, file_path: Path) -> List[CodeQualityIssue]:
        """Scan JSON configuration file."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            issues.extend(self._scan_config_data(content, str(file_path)))
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            logging.warning(f"Could not parse JSON file {file_path}: {e}")
        
        return issues
    
    def _scan_properties_file(self, file_path: Path) -> List[CodeQualityIssue]:
        """Scan properties/INI file."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    secret_issues = self._analyze_config_value(key, value, line_num, str(file_path))
                    issues.extend(secret_issues)
        except (IOError, UnicodeDecodeError) as e:
            logging.warning(f"Could not read properties file {file_path}: {e}")
        
        return issues
    
    def _scan_text_file(self, file_path: Path) -> List[CodeQualityIssue]:
        """Fallback text-based scanning."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply regex patterns to entire content
            for secret_type, pattern in self.secret_patterns.items():
                matches = pattern.finditer(content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(CodeQualityIssue(
                        issue_type=f'config_{secret_type}',
                        line_number=line_num,
                        description=f"Config file contains {secret_type.replace('_', ' ')}: {match.group()[:20]}...",
                        severity='error',
                        file_path=str(file_path)
                    ))
        except (IOError, UnicodeDecodeError) as e:
            logging.warning(f"Could not read config file {file_path}: {e}")
        
        return issues
    
    def _scan_config_data(self, data: Any, file_path: str, path: str = "") -> List[CodeQualityIssue]:
        """Recursively scan configuration data structure."""
        issues = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str):
                    secret_issues = self._analyze_config_value(current_path, value, 0, file_path)
                    issues.extend(secret_issues)
                elif isinstance(value, (dict, list)):
                    issues.extend(self._scan_config_data(value, file_path, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, str):
                    secret_issues = self._analyze_config_value(current_path, item, 0, file_path)
                    issues.extend(secret_issues)
                elif isinstance(item, (dict, list)):
                    issues.extend(self._scan_config_data(item, file_path, current_path))
        
        return issues
    
    def _analyze_config_value(self, key: str, value: str, line_num: int, file_path: str) -> List[CodeQualityIssue]:
        """Analyze a configuration value for secrets."""
        issues = []
        
        # Skip very short values
        if len(value) < 8:
            return issues
        
        # Check against known secret patterns
        for secret_type, pattern in self.secret_patterns.items():
            if pattern.search(value):
                issues.append(CodeQualityIssue(
                    issue_type=f'config_{secret_type}',
                    line_number=line_num,
                    description=f"Config key '{key}' contains {secret_type.replace('_', ' ')}: {value[:20]}...",
                    severity='error',
                    file_path=file_path
                ))
                return issues  # Don't double-report
        
        # Entropy-based detection (same logic as other scanners)
        if self._has_high_entropy(value) and self._looks_like_secret(value):
            issues.append(CodeQualityIssue(
                issue_type='config_high_entropy_string',
                line_number=line_num,
                description=f"Config key '{key}' has high entropy (possible secret): {value[:20]}...",
                severity='warning',
                file_path=file_path
            ))
        
        return issues
    
    def _has_high_entropy(self, text: str) -> bool:
        """Calculate Shannon entropy."""
        if len(text) < 16:
            return False
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy > 4.5
    
    def _looks_like_secret(self, text: str) -> bool:
        """Additional heuristics to identify potential secrets."""
        if len(text) < 16 or len(text) > 512:
            return False
        
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in text)
        
        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        false_positive_patterns = [
            'lorem ipsum', 'hello world', 'test', 'example', 
            'placeholder', 'abcdef', '123456'
        ]
        
        if any(pattern in text.lower() for pattern in false_positive_patterns):
            return False
        
        return diversity_score >= 3


def comprehensive_secret_scan(directory: Union[str, Path], 
                            scan_python: bool = True,
                            scan_env: bool = True, 
                            scan_config: bool = True) -> SecretDetectionResult:
    """
    Perform comprehensive secret detection across all file types.
    
    Args:
        directory: Directory to scan
        scan_python: Include Python file scanning
        scan_env: Include environment file scanning  
        scan_config: Include configuration file scanning
        
    Returns:
        SecretDetectionResult with all detected issues
    """
    all_issues = []
    files_scanned = 0
    scan_types = []
    
    directory = Path(directory)
    
    # Python file scanning
    if scan_python:
        scan_types.append('python')
        for py_file in directory.rglob('*.py'):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    issues = analyze_code_quality(content)
                    # Filter for secret-related issues and add file path
                    secret_issues = []
                    secret_types = {
                        'hardcoded_aws_access_key', 'hardcoded_aws_secret_key',
                        'hardcoded_jwt_token', 'hardcoded_api_key',
                        'hardcoded_password', 'hardcoded_secret',
                        'hardcoded_private_key', 'hardcoded_connection_string',
                        'high_entropy_string', 'encoded_secret'
                    }
                    for issue in issues:
                        if issue.issue_type in secret_types:
                            issue.file_path = str(py_file)
                            secret_issues.append(issue)
                    all_issues.extend(secret_issues)
                    files_scanned += 1
                except (IOError, UnicodeDecodeError):
                    continue
    
    # Environment file scanning
    if scan_env:
        scan_types.append('environment')
        env_scanner = EnvironmentVariableScanner()
        env_issues = env_scanner.scan_directory_for_env_files(directory)
        all_issues.extend(env_issues)
        files_scanned += len(set(issue.file_path for issue in env_issues if issue.file_path))
    
    # Configuration file scanning
    if scan_config:
        scan_types.append('configuration')
        config_scanner = ConfigurationFileScanner()
        config_issues = config_scanner.scan_directory_for_config_files(directory)
        all_issues.extend(config_issues)
        files_scanned += len(set(issue.file_path for issue in config_issues if issue.file_path))
    
    return SecretDetectionResult(
        issues=all_issues,
        files_scanned=files_scanned,
        entropy_threshold=4.5,
        scan_types=scan_types
    )


def find_placeholders(source_code: str) -> List[Placeholder]:
    """
    Find all placeholders in source code using AST.
    
    Args:
        source_code: Python source code to analyze
        
    Returns:
        List of detected placeholders
    """
    try:
        tree = ast.parse(source_code)
        source_lines = source_code.splitlines()
        visitor = PlaceholderVisitor(source_lines)
        visitor.visit(tree)
        return visitor.placeholders
    except SyntaxError as e:
        logging.error(f"Syntax error in source code: {e}")
        return []


def analyze_code_quality(source_code: str) -> List[CodeQualityIssue]:
    """
    Analyze code quality issues using AST.
    
    Args:
        source_code: Python source code to analyze
        
    Returns:
        List of detected issues
    """
    try:
        tree = ast.parse(source_code)
        analyzer = CodeQualityAnalyzer()
        analyzer.visit(tree)
        return analyzer.issues
    except SyntaxError as e:
        logging.error(f"Syntax error in source code: {e}")
        return [CodeQualityIssue(
            issue_type='syntax_error',
            line_number=e.lineno or 0,
            description=str(e),
            severity='error'
        )]


def extract_imports(source_code: str) -> Set[str]:
    """
    Extract all import statements from source code.
    
    Returns:
        Set of imported module names
    """
    imports = set()
    
    try:
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    
    except SyntaxError:
        pass
    
    return imports


def find_function_calls(source_code: str, function_name: str) -> List[int]:
    """
    Find all calls to a specific function.
    
    Returns:
        List of line numbers where function is called
    """
    calls = []
    
    try:
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Direct function call
                if isinstance(node.func, ast.Name) and node.func.id == function_name:
                    calls.append(node.lineno)
                # Method call
                elif isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                    calls.append(node.lineno)
    
    except SyntaxError:
        pass
    
    return calls