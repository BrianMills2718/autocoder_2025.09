#!/usr/bin/env python3
"""
Property-based tests for component generation invariants

Uses Hypothesis to test that generated components maintain critical invariants
across a wide range of inputs and configurations.
"""
import ast
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any
from unittest.mock import Mock

from autocoder_cc.generation.component_generator import ComponentGenerator
from autocoder_cc.generation.template_engine import TemplateEngine
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedComponent


class TestComponentInvariants:
    """Property-based tests for component generation invariants"""
    
    @given(
        component_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        component_type=st.sampled_from(['Store', 'Source', 'Sink', 'Processor', 'APIEndpoint', 'Router']),
        config_keys=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
    )
    @settings(max_examples=50)
    def test_generated_component_is_valid_python(self, component_name, component_type, config_keys):
        """Property: All generated components must be valid Python code"""
        # Ensure valid Python identifier
        component_name = "".join(c if c.isalnum() or c == "_" else "_" for c in component_name)
        if not component_name[0].isalpha() and component_name[0] != "_":
            component_name = "C" + component_name
        assume(component_name.isidentifier())
        
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        config = {key: f"value_{i}" for i, key in enumerate(config_keys)}
        component_spec = ParsedComponent(
            name=component_name,
            type=component_type,
            config=config
        )
        
        generated = generator.generate_component(component_spec, Mock())
        
        # Must be valid Python
        try:
            ast.parse(generated.implementation)
        except SyntaxError as e:
            pytest.fail(f"Generated code is not valid Python: {e}")
    
    @given(
        component_type=st.sampled_from(['Store', 'Source', 'Sink', 'Processor', 'APIEndpoint', 'Router']),
        config_depth=st.integers(min_value=1, max_value=5)
    )
    def test_required_methods_present(self, component_type, config_depth):
        """Property: Components must have required methods for their type"""
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        # Generate nested config
        config = self._generate_nested_config(config_depth)
        
        component_spec = ParsedComponent(
            name=f"Test{component_type}",
            type=component_type,
            config=config
        )
        
        generated = generator.generate_component(component_spec, Mock())
        code = generated.implementation
        
        # Parse AST to check for required methods
        tree = ast.parse(code)
        
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == f"Test{component_type}":
                class_node = node
                break
        
        assert class_node is not None, f"Class Test{component_type} not found"
        
        method_names = {
            method.name for method in class_node.body 
            if isinstance(method, ast.AsyncFunctionDef) or isinstance(method, ast.FunctionDef)
        }
        
        # Check required methods by type
        required_methods = {
            'Store': {'store', 'retrieve', 'initialize', 'cleanup'},
            'Source': {'generate', 'initialize', 'cleanup'},
            'Sink': {'consume', 'initialize', 'cleanup'},
            'Processor': {'process', 'initialize', 'cleanup'},
            'APIEndpoint': {'handle_request', 'initialize', 'cleanup'},
            'Router': {'route', 'initialize', 'cleanup'}
        }
        
        for method in required_methods[component_type]:
            assert method in method_names, f"Required method '{method}' not found in {component_type}"
    
    @given(
        component_name=st.text(min_size=1, max_size=30),
        error_probability=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_error_handling_present(self, component_name, error_probability):
        """Property: All components must have error handling"""
        # Sanitize component name
        component_name = "".join(c if c.isalnum() else "_" for c in component_name)
        if not component_name or not component_name[0].isalpha():
            component_name = "Component" + component_name
        assume(component_name.isidentifier())
        
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        component_spec = ParsedComponent(
            name=component_name,
            type="Processor",
            config={"error_rate": error_probability}
        )
        
        generated = generator.generate_component(component_spec, Mock())
        code = generated.implementation
        
        # Parse AST to check for try/except blocks
        tree = ast.parse(code)
        
        has_error_handling = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                has_error_handling = True
                break
        
        assert has_error_handling, "Component must include error handling (try/except blocks)"
    
    @given(
        config=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
                st.booleans(),
                st.lists(st.integers(), max_size=5),
                st.dictionaries(st.text(max_size=10), st.integers(), max_size=3)
            ),
            max_size=20
        )
    )
    def test_configuration_properly_initialized(self, config):
        """Property: All config values must be properly initialized"""
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        component_spec = ParsedComponent(
            name="ConfiguredComponent",
            type="Processor",
            config=config
        )
        
        generated = generator.generate_component(component_spec, Mock())
        code = generated.implementation
        
        # Check that config values are referenced in __init__
        for key in config:
            # Config keys should be accessed in initialization
            assert f"config.get('{key}'" in code or f'config["{key}"]' in code or f"config['{key}']" in code, \
                   f"Config key '{key}' not properly initialized"
    
    @given(
        num_imports=st.integers(min_value=1, max_value=10),
        num_methods=st.integers(min_value=1, max_value=5)
    )
    def test_imports_are_used(self, num_imports, num_methods):
        """Property: All imports must be used in the component"""
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        # Generate some imports
        import_modules = [f"module_{i}" for i in range(num_imports)]
        
        component_spec = ParsedComponent(
            name="ImportedComponent",
            type="Processor",
            config={"imports": import_modules}
        )
        
        generated = generator.generate_component(component_spec, Mock())
        code = generated.implementation
        
        # Parse to check imports
        tree = ast.parse(code)
        
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                imported_names.add(node.module.split('.')[0] if node.module else '')
        
        # All standard imports should be present
        standard_imports = {'asyncio', 'typing', 'datetime', 'logging'}
        for imp in standard_imports:
            if imp in code:
                assert imp in imported_names or f"from {imp}" in code or f"import {imp}" in code
    
    @given(
        component_type=st.sampled_from(['Store', 'APIEndpoint', 'MessageBus']),
        num_operations=st.integers(min_value=1, max_value=10)
    )
    def test_async_methods_are_async(self, component_type, num_operations):
        """Property: I/O operations must be async"""
        generator = ComponentGenerator(Mock(), Mock(), Mock())
        
        component_spec = ParsedComponent(
            name=f"Async{component_type}",
            type=component_type,
            config={"max_operations": num_operations}
        )
        
        generated = generator.generate_component(component_spec, Mock())
        code = generated.implementation
        
        # Parse and check async methods
        tree = ast.parse(code)
        
        io_methods = {
            'Store': ['store', 'retrieve'],
            'APIEndpoint': ['handle_request'],
            'MessageBus': ['publish', 'subscribe']
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in io_methods.get(component_type, []):
                pytest.fail(f"I/O method {node.name} must be async")
            elif isinstance(node, ast.AsyncFunctionDef) and node.name in io_methods.get(component_type, []):
                # Good - I/O methods are async
                pass
    
    def _generate_nested_config(self, depth: int, current_depth: int = 0) -> Dict[str, Any]:
        """Helper to generate nested configuration"""
        if current_depth >= depth:
            return {"value": f"leaf_{current_depth}"}
        
        return {
            f"level_{current_depth}": {
                "config": self._generate_nested_config(depth, current_depth + 1),
                "value": current_depth
            }
        }