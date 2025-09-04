#!/usr/bin/env python3
"""
Test LLM generation verification for reference implementation patterns.

This test suite ensures that LLM generation produces reference-compliant components
that use ComposedComponent and follow the correct patterns.
"""

import pytest
import asyncio
import ast
import re
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
from autocoder_cc.components.composed_base import ComposedComponent


class TestLLMGenerationVerification:
    """Test that LLM generation produces reference-compliant components."""
    
    def setup_method(self):
        """Setup test instances."""
        self.generator = LLMComponentGenerator()
        
    @pytest.mark.asyncio
    async def test_generates_composed_component_base_class(self):
        """Test LLM generates ComposedComponent (not StandaloneComponentBase)."""
        
        # Mock LLM response that should use ComposedComponent
        mock_llm_response = '''
class GeneratedStore_TestStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
    
    async def process_item(self, item: Any) -> Any:
        """Store or retrieve items."""
        action = item.get("action", "store")
        if action == "store":
            key = item["key"]
            value = item["value"]
            self._items[key] = value
            return {"status": "success", "action": "store", "key": key}
        elif action == "retrieve":
            key = item["key"]
            value = self._items.get(key)
            if value is not None:
                return {"status": "success", "action": "retrieve", "key": key, "value": value}
            else:
                return {"status": "not_found", "key": key}
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="Store",
                component_name="TestStore", 
                component_description="Test store component",
                component_config={},
                class_name="GeneratedStore_TestStore"
            )
            
            generated_code = result.get('implementation', result)
            
            # Should use ComposedComponent
            assert "ComposedComponent" in generated_code
            assert "class GeneratedStore_TestStore(ComposedComponent)" in generated_code
            
            # Should NOT use deprecated base classes
            assert "StandaloneComponentBase" not in generated_code
            assert "ComponentBase" not in generated_code
            
    @pytest.mark.asyncio
    async def test_generated_method_signatures_match_reference(self):
        """Test generated methods match reference implementation."""
        
        mock_llm_response = '''
class GeneratedAPI_TestAPI(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 8000)
    
    async def process_item(self, item: Any) -> Dict[str, Any]:
        """Process HTTP requests."""
        method = item.get("method", "GET").upper()
        path = item.get("path", "/")
        
        if path == "/health":
            return {
                "status": 200,
                "body": {"healthy": True},
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return {
                "status": 404,
                "body": {"error": "Not Found"},
                "headers": {"Content-Type": "application/json"}
            }
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="API",
                component_name="TestAPI",
                component_description="Test API component", 
                component_config={},
                class_name="GeneratedAPI_TestAPI"
            )
            
            generated_code = result.get('implementation', result)
            
            # Parse AST to check method signatures
            tree = ast.parse(generated_code)
            
            # Find the component class
            component_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "GeneratedAPI_TestAPI":
                    component_class = node
                    break
                    
            assert component_class is not None, "Component class not found"
            
            # Check method signatures
            methods = {n.name for n in component_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            
            # Should have __init__ and process_item
            assert "__init__" in methods
            assert "process_item" in methods
            
            # Find process_item method and check signature
            process_item_method = None
            for node in component_class.body:
                if isinstance(node, ast.AsyncFunctionDef) and node.name == "process_item":
                    process_item_method = node
                    break
                    
            assert process_item_method is not None, "process_item method not found"
            assert len(process_item_method.args.args) >= 2, "process_item should have self and item parameters"
            
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_generated_imports_are_correct(self):
        """Test generated code has correct import statements."""
        
        mock_llm_response = '''
class GeneratedStore_TestStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
    
    async def process_item(self, item: Any) -> Any:
        return {"status": "success"}
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="Store",
                component_name="TestStore",
                component_description="Test store component",
                component_config={},
                class_name="GeneratedStore_TestStore"
            )
            
            # Check if result includes proper imports (either in the code or separately)
            if isinstance(result, dict):
                generated_code = result.get('implementation', '')
                imports = result.get('imports', [])
            else:
                generated_code = result
                imports = []
                
            # Extract imports from generated code if present
            import_lines = []
            for line in generated_code.split('\n'):
                line = line.strip()
                if line.startswith('from ') or line.startswith('import '):
                    import_lines.append(line)
                    
            all_imports = imports + import_lines
            
            # Should have correct ComposedComponent import (either in code or as metadata)
            expected_imports = [
                "ComposedComponent",  # The class should be available
                "Dict",  # Type hints should be available
                "Any"   # Type hints should be available
            ]
            
            # Check that the necessary symbols are available (either imported or referenced)
            full_content = str(result)
            for symbol in expected_imports:
                assert symbol in full_content, f"Required symbol '{symbol}' not found in generation result"
                
    @pytest.mark.asyncio
    async def test_no_deprecated_patterns_in_output(self):
        """Test no StandaloneComponentBase or deprecated patterns."""
        
        mock_llm_response = '''
class GeneratedTransformer_TestTransformer(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.transform_config = config.get("transform", {})
    
    async def process_item(self, item: Any) -> Any:
        """Transform input data."""
        # Simple transformation example
        if isinstance(item, dict):
            transformed = {k: str(v).upper() if isinstance(v, str) else v for k, v in item.items()}
            return {"status": "success", "transformed": transformed}
        else:
            return {"status": "success", "transformed": str(item).upper()}
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="Transformer",
                component_name="TestTransformer",
                component_description="Test transformer component",
                component_config={},
                class_name="GeneratedTransformer_TestTransformer"
            )
            
            generated_code = result.get('implementation', result)
            
            # Check for deprecated patterns
            deprecated_patterns = [
                "StandaloneComponentBase",
                "ComponentBase", 
                "def teardown(",
                "def start(",
                "def stop(",
                "from autocoder_cc.components",  # Wrong package name
                "import autocoder_cc.components"
            ]
            
            for pattern in deprecated_patterns:
                assert pattern not in str(result), f"Deprecated pattern found: {pattern}"
                
            # Should use correct patterns
            correct_patterns = [
                "ComposedComponent",
                "async def process_item(",
                "def __init__("
            ]
            
            for pattern in correct_patterns:
                assert pattern in str(result), f"Expected pattern not found: {pattern}"
                
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_generated_code_is_syntactically_valid(self):
        """Test that generated code is syntactically valid Python."""
        
        mock_llm_response = '''
class GeneratedSink_TestSink(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.output_config = config.get("output", {})
        self.processed_count = 0
    
    async def process_item(self, item: Any) -> Any:
        """Process and output data."""
        self.processed_count += 1
        
        # Simulate output processing
        output_format = self.output_config.get("format", "json")
        
        if output_format == "json":
            import json
            output = json.dumps(item)
        else:
            output = str(item)
            
        return {"status": "success", "output": output, "count": self.processed_count}
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="Sink",
                component_name="TestSink",
                component_description="Test sink component",
                component_config={},
                class_name="GeneratedSink_TestSink"
            )
            
            generated_code = result.get('implementation', result)
            
            # Test that code is syntactically valid
            try:
                ast.parse(generated_code)
            except SyntaxError as e:
                pytest.fail(f"Generated code has syntax error: {e}")
                
            # Test that class definition is correct
            tree = ast.parse(generated_code)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            assert len(classes) >= 1, "No class definitions found"
            
            main_class = classes[0]
            assert main_class.name == "GeneratedSink_TestSink"
            assert len(main_class.bases) >= 1, "Class should inherit from ComposedComponent"
            
    @pytest.mark.asyncio
    async def test_lifecycle_methods_injection_or_presence(self):
        """Test that lifecycle methods are either generated or will be injected."""
        
        # Test with minimal LLM output (just business logic)
        minimal_llm_response = '''
class GeneratedStore_MinimalStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._data = {}
    
    async def process_item(self, item: Any) -> Any:
        """Simple store logic."""
        if "store" in item:
            self._data[item["key"]] = item["value"]
            return {"status": "stored"}
        elif "get" in item:
            return {"status": "success", "value": self._data.get(item["key"])}
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=minimal_llm_response):
            result = await self.generator.generate_component_structured(
                component_type="Store",
                component_name="MinimalStore",
                component_description="Minimal store component",
                component_config={},
                class_name="GeneratedStore_MinimalStore"
            )
            
            generated_code = result.get('implementation', result)
            
            # Parse AST to check methods
            tree = ast.parse(generated_code)
            component_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "MinimalStore" in node.name:
                    component_class = node
                    break
                    
            assert component_class is not None
            
            methods = {n.name for n in component_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            
            # Should have essential methods
            assert "__init__" in methods
            assert "process_item" in methods
            
            # Lifecycle methods might be missing (to be injected later) or present
            lifecycle_methods = ["setup", "cleanup", "get_health_status"]
            
            # Check if injection indicator is present or methods are already there
            has_lifecycle_methods = any(method in methods for method in lifecycle_methods)
            needs_injection = not has_lifecycle_methods
            
            # Both cases are valid:
            # 1. LLM generates complete component with lifecycle methods
            # 2. LLM generates minimal component that needs lifecycle injection
            
            if needs_injection:
                # If injection is needed, verify the generator knows this
                assert hasattr(self.generator, 'inject_lifecycle_methods') or 'inject' in str(result), \
                    "Generator should support lifecycle method injection for minimal components"


class TestGenerationPromptCompliance:
    """Test that generation follows prompt instructions correctly."""
    
    def setup_method(self):
        """Setup test instances.""" 
        self.generator = LLMComponentGenerator()
        
    @pytest.mark.asyncio
    async def test_follows_component_naming_conventions(self):
        """Test that generated components follow naming conventions."""
        
        mock_response = '''
class GeneratedAPI_UserAPI(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
'''
        
        with patch.object(self.generator, '_generate_from_llm', return_value=mock_response):
            result = await self.generator.generate_component_structured(
                component_type="API",
                component_name="UserAPI",
                component_description="User management API",
                component_config={},
                class_name="GeneratedAPI_UserAPI"
            )
            
            generated_code = result.get('implementation', result)
            
            # Should follow naming convention: Generated{Type}_{Name}
            assert "class GeneratedAPI_UserAPI" in generated_code
            assert "ComposedComponent" in generated_code
            
    @pytest.mark.asyncio
    async def test_respects_component_type_patterns(self):
        """Test that different component types follow their expected patterns."""
        
        component_types = {
            "Store": {
                "expected_methods": ["process_item"],
                "expected_patterns": ["_items", "store", "retrieve"]
            },
            "API": {
                "expected_methods": ["process_item"],
                "expected_patterns": ["status", "headers", "method"]
            },
            "Transformer": {
                "expected_methods": ["process_item"],
                "expected_patterns": ["transform", "process"]
            }
        }
        
        for comp_type, expectations in component_types.items():
            mock_response = f'''
class Generated{comp_type}_Test{comp_type}(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def process_item(self, item: Any) -> Any:
        return {{"status": "success", "type": "{comp_type.lower()}"}}
'''
            
            with patch.object(self.generator, '_generate_from_llm', return_value=mock_response):
                result = await self.generator.generate_component_structured(
                    component_type=comp_type,
                    component_name=f"Test{comp_type}",
                    component_description=f"Test {comp_type.lower()} component",
                    component_config={},
                    class_name=f"Generated{comp_type}_Test{comp_type}"
                )
                
                generated_code = result.get('implementation', result)
                
                # Check class name pattern
                assert f"class Generated{comp_type}_Test{comp_type}(ComposedComponent)" in generated_code
                
                # Check required methods
                for method in expectations["expected_methods"]:
                    assert f"def {method}(" in generated_code or f"async def {method}(" in generated_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])