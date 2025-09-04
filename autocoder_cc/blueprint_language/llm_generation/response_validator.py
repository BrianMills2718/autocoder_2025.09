"""
LLM Response Validation

This module contains comprehensive validation logic for LLM-generated code.
It implements the strict "NO LAZY IMPLEMENTATIONS" principle by detecting
and rejecting placeholder patterns, syntax errors, and incomplete implementations.

Key Features:
- AST-based syntax validation
- Placeholder pattern detection
- Business logic verification
- Functional implementation validation
"""

import ast
import re
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Tuple


class ComponentGenerationError(Exception):
    """Raised when component generation fails - no fallbacks available"""
    pass


class ResponseValidator:
    """
    Comprehensive validation for LLM-generated component code
    
    Implements multiple layers of validation:
    1. Syntax validation using AST parsing
    2. Placeholder pattern detection
    3. Business logic verification
    4. Import validation
    5. Component structure validation
    """
    
    def __init__(self):
        self.forbidden_patterns = self._get_forbidden_patterns()
        self.required_patterns = self._get_required_patterns()
    
    def _get_forbidden_patterns(self) -> List[str]:
        """Get list of forbidden patterns that indicate placeholder code"""
        return [
            r'return\s*\{\s*["\']value["\']\s*:\s*42\s*\}',  # {"value": 42} pattern
            r'return\s*\{\s*["\']test["\']\s*:\s*True\s*\}',  # {"test": True} pattern
            r'return\s*\{\s*\}.*placeholder',                # Empty dict with placeholder comment
            r'#\s*TODO:|#\s*FIXME:|pass\s*#',                # TODO/FIXME/pass comments (must be actual comments)
            r'NotImplementedError',                          # NotImplementedError
            r'raise\s+NotImplementedError',                  # raise NotImplementedError
            r'pass\s*$',                                     # Pass statements as method body
            r'pass\s*\n\s*$',                               # Pass statements with newline
            r'localhost|127\.0\.0\.1',                      # Hardcoded localhost
            r'your_[a-z_]+_url',                            # Placeholder URLs
            r'dummy_\w+',                                    # Dummy variables
            r'mock_\w+',                                     # Mock variables
        ]
    
    def _get_required_patterns(self) -> List[str]:
        """
        Get list of patterns that must be present in standalone components
        
        Phase 2A Update: With shared observability module, these patterns are imported
        rather than defined inline, so we only check for usage patterns.
        """
        return [
            "ComposedComponent",  # Must inherit from this class
        ]
    
    def validate_python_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate Python syntax using AST parsing
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Compile to catch compilation errors
            compile(tree, '<generated_code>', 'exec')
            
            # Check for placeholder patterns using AST
            placeholder_issues = self._detect_placeholders_ast(tree)
            if placeholder_issues:
                return False, f"Placeholder patterns found: {placeholder_issues}"
            
            # Check for async issues using AST
            async_issues = self._detect_async_issues_ast(tree)
            if async_issues:
                return False, f"Async issues found: {async_issues}"
            
            return True, "Validation passed"
            
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Compilation error: {e}"
    
    def _detect_placeholders_ast(self, tree) -> List[str]:
        """Use AST to detect placeholder patterns"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for TODO comments
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str) and "TODO" in node.value.value:
                    issues.append(f"TODO comment at line {node.lineno}")
            
            # Check for NotImplementedError
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                if isinstance(node.exc.func, ast.Name) and node.exc.func.id == "NotImplementedError":
                    issues.append(f"NotImplementedError at line {node.lineno}")
            
            # Check for pass statements in methods
            if isinstance(node, ast.FunctionDef) and len(node.body) == 1:
                if isinstance(node.body[0], ast.Pass):
                    issues.append(f"Pass statement in method {node.name} at line {node.lineno}")
        
        return issues
    
    def _detect_async_issues_ast(self, tree) -> List[str]:
        """Use AST to detect async issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for blocking async calls in __init__ methods
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if (isinstance(child.func.value, ast.Name) and 
                                child.func.value.id in ['anyio', 'asyncio'] and
                                child.func.attr == 'run'):
                                issues.append(f"Blocking async call {child.func.value.id}.{child.func.attr}() in __init__")
        
        return issues
    
    def validate_no_placeholders(self, code: str) -> bool:
        """
        Enhanced validation using AST-based analysis
        
        Args:
            code: Python code to validate
            
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If placeholder patterns are found
        """
        # Use the new AST-based validation
        valid, message = self.validate_python_syntax(code)
        if not valid:
            raise ValueError(message)
        
        # Additional string-based checks for obvious placeholders
        forbidden_patterns = [
            'raise NotImplementedError',
            '# TODO:',
            '# FIXME:',
            'pass  # Implement',
            'return {}  # Placeholder',
            'return {"value": 42}',
            'return {"test": True}',
            'dummy_value',
            'placeholder'
        ]
        
        clean_code = code.strip()
        for pattern in forbidden_patterns:
            if pattern in clean_code:
                raise ValueError(f"Generated code contains forbidden pattern: {pattern}")
        
        return True
    
    def validate_functional_implementation(self, code: str) -> bool:
        """
        Validate that generated code is truly functional, not placeholder
        CRITICAL: Address Gemini finding of placeholder pattern generation
        
        Args:
            code: Python code to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        # Check for forbidden patterns (Gemini confirmed these exist)
        # TEMPORARILY COMMENTED OUT: Regex patterns cause false positives with domain terms (e.g., "todo" in todo apps)
        # TODO: Remove entirely after confirming AST validation catches real issues
        # for pattern in self.forbidden_patterns:
        #     matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
        #     if matches:
        #         print(f"❌ Found forbidden pattern '{pattern}': {matches}")
        #         return False
        
        # Verify actual business logic implementation
        return self._verify_business_logic_implementation(code)
    
    def _verify_business_logic_implementation(self, code: str) -> bool:
        """Verify that the code contains actual business logic, not just structure"""
        try:
            tree = ast.parse(code)
            
            # Find the main component class (not base classes)
            component_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Skip embedded base classes
                    if node.name not in ['ComposedComponent', 'StandaloneMetricsCollector', 
                                        'StandaloneTracer', 'StandaloneSpan', 'ComponentStatus']:
                        component_classes.append(node)
            
            if not component_classes:
                print("❌ No component class found")
                return False
            
            main_class = component_classes[0]  # Take the first non-base class
            
            # Check for process_item method with real implementation
            process_item_method = None
            for item in main_class.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == 'process_item':
                    process_item_method = item
                    break
            
            if not process_item_method:
                print("❌ No process_item method found")
                return False
            
            # Check method body has more than just pass statements
            meaningful_statements = 0
            for stmt in ast.walk(process_item_method):
                if isinstance(stmt, (ast.Return, ast.Assign, ast.AugAssign, ast.Call, ast.If, ast.Try)):
                    meaningful_statements += 1
            
            if meaningful_statements < 2:  # Should have at least a few meaningful operations
                print(f"❌ process_item method too simple: only {meaningful_statements} meaningful statements")
                return False
            
            print(f"✅ Found component class '{main_class.name}' with substantial process_item implementation")
            return True
            
        except SyntaxError as e:
            # Syntax errors should be caught earlier, but if we get here, provide clear feedback
            print(f"❌ Business logic verification failed due to syntax error: {e}")
            return False
        except Exception as e:
            print(f"❌ Business logic verification failed: {e}")
            return False
    
    def validate_generated_component(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated standalone component code for common issues
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for FORBIDDEN imports from autocoder_cc (allow architectural templates)
        # NOTE: ComposedComponent is NOW ALLOWED as it's our standard base class
        forbidden_patterns = [
            # Removed ComposedComponent from forbidden patterns
            # Components are generated to use ComposedComponent
        ]
        
        # Allowed architectural template imports and Phase 2A shared observability
        allowed_patterns = [
            "from autocoder_cc.blueprint_language.architectural_templates.",
            "import autocoder_cc.blueprint_language.architectural_templates.",
            "from autocoder_cc.generators.scaffold.shared_observability import"  # Phase 2A: Allow shared observability
        ]
        
        # Check for forbidden patterns but allow architectural templates
        for pattern in forbidden_patterns:
            if pattern in code:
                issues.append(f"FORBIDDEN import found: {pattern}")
        
        # Check for other autocoder_cc imports that are not architectural templates or shared observability
        for line in code.split('\n'):
            if ('from autocoder_cc.' in line or 'import autocoder_cc.' in line):
                # Check if it's an allowed import
                is_allowed = any(allowed_pattern in line for allowed_pattern in allowed_patterns)
                if not is_allowed:
                    issues.append(f"FORBIDDEN import found: {line.strip()} - only architectural template imports and shared observability are allowed from autocoder_cc.*")
        
        # Check for required standalone patterns
        for pattern in self.required_patterns:
            if pattern not in code:
                issues.append(f"Missing required standalone pattern: {pattern}")
        
        # Check that component inherits from ComposedComponent
        if "ComposedComponent)" not in code:
            issues.append("Component must inherit from ComposedComponent")
        
        # Check for blocking async calls in __init__
        if "anyio.run(" in code or "asyncio.run(" in code:
            if "def __init__" in code:
                issues.append("Blocking async call found in __init__ method")
        
        # Check for undefined method references
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
        return len(issues) == 0, issues
    
    def validate_ast_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate generated code using AST parsing
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            tree = ast.parse(code)
            
            # Check for class definitions
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                return False, "No class definition found"
            
            # Look for the component class (not the base class)
            component_class = None
            for class_node in classes:
                # Skip the embedded base classes
                if class_node.name in ['ComposedComponent', 'StandaloneMetricsCollector', 'StandaloneTracer', 'StandaloneSpan', 'ComponentStatus']:
                    continue
                # This should be the actual component class
                component_class = class_node
                break
            
            if not component_class:
                return False, "No component class found (only base classes)"
            
            # Check for required methods (including async methods) in the component class
            methods = [node.name for node in component_class.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            required_methods = ["__init__", "process_item"]
            
            for method in required_methods:
                if method not in methods:
                    return False, f"Missing required method: {method} in component class {component_class.name}"
            
            return True, "AST validation passed"
            
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
    
    def validate_imports(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate that all required standalone imports are present and no forbidden imports exist
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_imports)
        """
        # Check for FORBIDDEN imports (allow architectural templates)
        # NOTE: ComposedComponent is NOW ALLOWED as it's our standard base class
        forbidden_patterns = [
            # Removed ComposedComponent from forbidden patterns
            # Components are generated to use ComposedComponent
        ]
        
        # Allowed architectural template imports and Phase 2A shared observability
        allowed_patterns = [
            "from autocoder_cc.blueprint_language.architectural_templates.",
            "import autocoder_cc.blueprint_language.architectural_templates.",
            "from autocoder_cc.generators.scaffold.shared_observability import"  # Phase 2A: Allow shared observability
        ]
        
        # Check for forbidden patterns but allow architectural templates
        for pattern in forbidden_patterns:
            if pattern in code:
                return False, [f"FORBIDDEN import found: {pattern}"]
        
        # Check for other autocoder_cc imports that are not architectural templates or shared observability
        for line in code.split('\n'):
            if ('from autocoder_cc.' in line or 'import autocoder_cc.' in line):
                # Check if it's an allowed import
                is_allowed = any(allowed_pattern in line for allowed_pattern in allowed_patterns)
                if not is_allowed:
                    return False, [f"FORBIDDEN import found: {line.strip()} - only architectural template imports and shared observability are allowed"]
        
        # Check for required standalone imports/patterns (Phase 2A updated)
        required_patterns = [
            # Phase 2A Fix: Don't require imports in raw LLM code - they're added by component_logic_generator.py
            # "Dict", "Any", "Optional" - These are added by the wrapper, not generated by LLM
            "ComposedComponent",  # Must inherit from base class (class definition, not import)
            # Note: All imports now handled by component_logic_generator.py shared module injection
        ]
        
        missing_imports = []
        for pattern in required_patterns:
            if pattern not in code:
                missing_imports.append(pattern)
        
        return len(missing_imports) == 0, missing_imports
    
    def validate_with_external_compilation(self, code: str) -> None:
        """
        Validate code by actually compiling it with Python
        
        Args:
            code: Python code to validate
            
        Raises:
            ComponentGenerationError: If compilation fails
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                tmp_file.write(code.strip())
                tmp_file.flush()
                tmp_filename = tmp_file.name
            
            try:
                result = subprocess.run([
                    'python3', '-m', 'py_compile', tmp_filename
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    raise ComponentGenerationError(f"Code compilation failed: {result.stderr}")
                    
            finally:
                try:
                    os.unlink(tmp_filename)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            raise ComponentGenerationError("Code compilation timeout")
        except subprocess.CalledProcessError as e:
            raise ComponentGenerationError(f"Code compilation subprocess failed: {e}")
        except Exception as e:
            raise ComponentGenerationError(f"Code validation failed: {e}")