"""
AST-Based Code Analysis and Quality Assessment
=============================================

The analysis package provides robust code analysis capabilities using Abstract Syntax Tree (AST)
parsing to replace fragile string matching with reliable, semantic-aware code understanding.

## Core Components

- **AST Parser**: Placeholder detection, quality analysis, structure understanding
- **Import Analyzer**: Missing import detection, dependency mapping, circular import prevention
- **Function Analyzer**: Signature extraction, parameter analysis, complexity metrics

## Quick Start

```python
from autocoder_cc.analysis import analyze_code_quality, find_placeholders

# Analyze code quality
with open("component.py", "r") as f:
    code = f.read()

quality_report = analyze_code_quality(code)
print(f"Quality score: {quality_report.score}")

# Find placeholders for self-healing
placeholders = find_placeholders(code)
for placeholder in placeholders:
    print(f"Found placeholder: {placeholder.type} at line {placeholder.line}")
```

## Key Features

- **Semantic Parsing**: Understands code structure, not just text patterns
- **Placeholder Detection**: Identifies TODO, FIXME, and incomplete code sections
- **Quality Assessment**: Code complexity, security, and best practice analysis
- **Import Validation**: Missing dependencies, circular imports, unused imports
- **Function Analysis**: Signature extraction, parameter analysis, docstring parsing
- **Performance Optimized**: Incremental analysis, caching, parallel processing
- **Error Resilient**: Graceful handling of syntax errors and malformed code
"""

from .ast_parser import PlaceholderVisitor, find_placeholders, analyze_code_quality
from .import_analyzer import ImportAnalyzer, find_missing_imports
from .function_analyzer import FunctionAnalyzer, extract_function_signatures

__all__ = [
    'PlaceholderVisitor',
    'find_placeholders',
    'analyze_code_quality',
    'ImportAnalyzer',
    'find_missing_imports',
    'FunctionAnalyzer',
    'extract_function_signatures'
]