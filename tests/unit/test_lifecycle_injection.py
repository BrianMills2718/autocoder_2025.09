#!/usr/bin/env python3
"""
Test lifecycle method injection for generated components.

This test suite ensures that required lifecycle methods (setup, cleanup, get_health_status)
are properly injected into LLM-generated components that are missing them.
"""

import pytest
import ast
from typing import Dict, Any

# Import the injection function we'll create
from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator


class TestLifecycleInjection:
    """Test that lifecycle methods are properly injected into generated components."""
    
    def setup_method(self):
        """Setup test instance of ComponentLogicGenerator."""
        self.generator = ComponentLogicGenerator(output_dir="/tmp/test_output")
    
    def test_inject_all_missing_lifecycle_methods(self):
        """Test that all missing lifecycle methods are injected."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
    
    async def process_item(self, item: Any) -> Any:
        self._items[item['id']] = item
        return {"status": "success", "id": item['id']}
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify all methods are present
        assert "def setup(self):" in injected_code
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
        
        # Verify docstrings
        assert '"""Initialize component resources."""' in injected_code
        assert '"""Clean up component resources."""' in injected_code
        assert '"""Return component health status."""' in injected_code
        
        # Verify health status implementation
        assert '"healthy": True' in injected_code
        assert '"component": self.name' in injected_code
    
    def test_preserve_existing_lifecycle_methods(self):
        """Test that existing lifecycle methods are not overwritten."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._connection = None
    
    def setup(self):
        """Custom setup logic."""
        self._connection = self._create_connection()
        self.custom_setup = True
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success"}
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify custom setup is preserved
        assert "self.custom_setup = True" in injected_code
        assert "Custom setup logic" in injected_code
        
        # Verify missing methods are added
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
        
        # Verify only one setup method exists
        assert injected_code.count("def setup(self):") == 1
    
    def test_handle_async_lifecycle_methods(self):
        """Test that async lifecycle methods are preserved."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def setup(self):
        """Async setup."""
        await self._async_init()
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success"}
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify async setup is preserved
        assert "async def setup(self):" in injected_code
        assert "await self._async_init()" in injected_code
        
        # Verify other methods are added (non-async by default)
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
    
    def test_inject_with_complex_class_structure(self):
        """Test injection works with complex class structures."""
        generated_code = '''
class GeneratedAPI_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._routes = {}
    
    async def process_item(self, item: Any) -> Any:
        return await self._handle_request(item)
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Private helper method."""
        route = request.get('route', '/')
        handler = self._routes.get(route, self._default_handler)
        return await handler(request)
    
    async def _default_handler(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": 404, "error": "Not found"}
    
    def register_route(self, route: str, handler):
        """Register a route handler."""
        self._routes[route] = handler
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify lifecycle methods are added
        assert "def setup(self):" in injected_code
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
        
        # Verify existing methods are preserved
        assert "def register_route(self, route: str, handler):" in injected_code
        assert "async def _handle_request(self, request: Dict[str, Any])" in injected_code
    
    def test_complex_init_with_conditionals(self):
        """Test that injection works correctly with complex __init__ containing conditionals."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.storage_type = self.config.get("storage_type", "memory")
        
        if self.storage_type in ["file", "database"]:
            self.db_host = self.config.get("db_host")
            self.db_port = self.config.get("db_port")
            if not self.db_host:
                raise ValueError("Database host required")
        else:
            self._memory_store = {}
    
    async def process_item(self, item: Any) -> Any:
        if self.storage_type == "memory":
            self._memory_store[item["id"]] = item
        return {"status": "success"}
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify methods are injected
        assert "def setup(self):" in injected_code
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
        
        # Verify __init__ is complete and not interrupted
        lines = injected_code.split('\n')
        init_start = None
        init_end = None
        for i, line in enumerate(lines):
            if 'def __init__' in line:
                init_start = i
            elif init_start is not None and 'def ' in line and '__init__' not in line:
                # Found next method
                init_end = i
                break
        
        # Check that the __init__ contains all expected code
        init_body = '\n'.join(lines[init_start:init_end]) if init_end else '\n'.join(lines[init_start:])
        assert 'self.storage_type' in init_body
        assert 'self.db_host' in init_body
        assert 'self._memory_store' in init_body
        assert 'raise ValueError' in init_body
        
        # Verify the lifecycle methods come AFTER __init__ and process_item
        setup_line = None
        process_line = None
        for i, line in enumerate(lines):
            if 'def setup(self):' in line:
                setup_line = i
            elif 'async def process_item' in line:
                process_line = i
        
        assert setup_line > process_line, "Lifecycle methods should be after process_item"
        
        # Parse to verify it's valid Python
        try:
            ast.parse(injected_code)
        except SyntaxError:
            pytest.fail(f"Injected code has syntax errors: {injected_code}")
    
    def test_inject_preserves_indentation(self):
        """Test that proper indentation is maintained."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success"}
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Parse to verify it's valid Python
        try:
            ast.parse(injected_code)
        except SyntaxError:
            pytest.fail("Injected code has syntax errors - likely indentation issues")
        
        # Check indentation visually
        lines = injected_code.split('\n')
        for i, line in enumerate(lines):
            if 'def setup(self):' in line:
                assert line.startswith('    def'), f"Line {i} has wrong indentation: {line}"
            if 'pass' in line and i > 0 and 'def' in lines[i-2]:
                assert line.startswith('        '), f"Line {i} has wrong indentation: {line}"
    
    def test_inject_with_multiple_classes(self):
        """Test injection only affects the component class."""
        generated_code = '''
class HelperClass:
    """Should not get lifecycle methods."""
    def __init__(self):
        pass

class GeneratedStore_Test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success"}

class AnotherHelper:
    """Also should not get lifecycle methods."""
    pass
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Verify only the Generated component gets methods
        assert injected_code.count("def setup(self):") == 1
        assert injected_code.count("def cleanup(self):") == 1
        assert injected_code.count("def get_health_status(self)") == 1
        
        # Verify helper classes are unchanged
        assert "class HelperClass:" in injected_code
        assert "class AnotherHelper:" in injected_code
        
        # Parse and check AST
        tree = ast.parse(injected_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "GeneratedStore_Test":
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    assert "setup" in methods
                    assert "cleanup" in methods
                    assert "get_health_status" in methods
                elif node.name in ["HelperClass", "AnotherHelper"]:
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    assert "setup" not in methods
                    assert "cleanup" not in methods
                    assert "get_health_status" not in methods
    
    def test_empty_component_gets_all_methods(self):
        """Test that even minimal components get all required methods."""
        generated_code = '''
class GeneratedStore_Test(ComposedComponent):
    pass
'''
        
        injected_code = self.generator._inject_lifecycle_methods(generated_code)
        
        # Should have all methods even though class was empty
        assert "def __init__(self, name: str, config: Dict[str, Any] = None):" in injected_code
        assert "super().__init__(name, config)" in injected_code
        assert "def setup(self):" in injected_code
        assert "def cleanup(self):" in injected_code
        assert "def get_health_status(self) -> Dict[str, Any]:" in injected_code
        assert "async def process_item(self, item: Any) -> Any:" in injected_code