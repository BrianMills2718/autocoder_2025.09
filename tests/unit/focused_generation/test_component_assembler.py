#!/usr/bin/env python3
"""
TDD Tests for Component Assembler

Tests programmatic injection of boilerplate around generated business logic
(RED phase - these should fail initially).
"""

import pytest
from typing import Dict, Any

class TestComponentAssembler:
    """Test programmatic assembly of complete components from business logic methods"""
    
    def test_assemble_complete_component_from_method(self):
        """Test assembling complete component by injecting boilerplate around business method"""
        # This test will fail until we implement ComponentAssembler
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        # Mock generated business logic method (what LLM produces)
        business_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """Double all numbers in the input"""
    numbers = item.get('numbers', [])
    doubled_numbers = [num * 2 for num in numbers if isinstance(num, (int, float))]
    
    return {
        'doubled_numbers': doubled_numbers,
        'original_count': len(numbers),
        'processed_count': len(doubled_numbers)
    }'''
        
        business_spec = BusinessLogicSpec(
            component_name="number_doubler",
            component_type="Transformer",
            business_purpose="Double all numeric values",
            input_schema={"numbers": "array"},
            output_schema={"doubled_numbers": "array"},
            transformation_description="Multiply each number by 2"
        )
        
        assembler = ComponentAssembler()
        complete_component = assembler.assemble_component(business_method, business_spec)
        
        # Verify complete component contains business logic
        assert "num * 2" in complete_component
        assert "doubled_numbers" in complete_component
        
        # Verify complete component contains injected boilerplate
        assert "class StandaloneComponentBase" in complete_component
        assert "def get_logger" in complete_component
        assert "class NumberDoublerComponent" in complete_component
        assert "def __init__" in complete_component
        
        # Verify imports are automatically added
        assert "from typing import Dict, Any" in complete_component
        assert "import logging" in complete_component
    
    def test_smart_import_detection(self):
        """Test automatic detection and injection of required imports based on business logic"""
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        # Business method that uses various libraries
        business_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio
    import json
    import re
    from datetime import datetime, timezone
    import uuid
    
    # Process the data
    data = json.loads(item.get('data', '{}'))
    pattern = re.compile(r'\\d+')
    timestamp = datetime.now(timezone.utc)
    record_id = str(uuid.uuid4())
    
    await asyncio.sleep(0.1)  # Simulate async processing
    
    return {
        'processed_data': data,
        'timestamp': timestamp.isoformat(),
        'record_id': record_id
    }'''
        
        business_spec = BusinessLogicSpec(
            component_name="data_processor",
            component_type="Transformer",
            business_purpose="Process data with metadata",
            input_schema={"data": "string"},
            output_schema={"processed_data": "object"},
            transformation_description="Parse JSON and add metadata"
        )
        
        assembler = ComponentAssembler()
        complete_component = assembler.assemble_component(business_method, business_spec)
        
        # Verify required imports are detected and added to top
        expected_imports = [
            "import asyncio",
            "import json", 
            "import re",
            "from datetime import datetime, timezone",
            "import uuid"
        ]
        
        for import_stmt in expected_imports:
            assert import_stmt in complete_component
        
        # Verify imports are at the top, not inside the method
        lines = complete_component.split('\n')
        import_lines = [i for i, line in enumerate(lines) if 'import' in line and not line.strip().startswith('#')]
        method_lines = [i for i, line in enumerate(lines) if 'async def process_item' in line]
        
        assert len(import_lines) > 0, "Should have import statements"
        assert len(method_lines) > 0, "Should have method definition"
        assert max(import_lines) < min(method_lines), "Imports should come before method"
    
    def test_component_specific_initialization(self):
        """Test that different component types get appropriate initialization logic"""
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        assembler = ComponentAssembler()
        
        business_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": "processed"}'''
        
        # Test Store component initialization
        store_spec = BusinessLogicSpec(
            component_name="user_store",
            component_type="Store",
            business_purpose="Store user data",
            input_schema={"user": "object"},
            output_schema={"result": "object"},
            transformation_description="Persist user to database",
            quality_requirements={"connection_pool_size": 10}
        )
        
        store_component = assembler.assemble_component(business_method, store_spec)
        
        # Should include database-specific initialization
        assert "connection_pool_size" in store_component
        assert "database" in store_component.lower() or "store" in store_component.lower()
        
        # Test APIEndpoint component initialization
        api_spec = BusinessLogicSpec(
            component_name="user_api",
            component_type="APIEndpoint", 
            business_purpose="Handle user API requests",
            input_schema={"request": "object"},
            output_schema={"response": "object"},
            transformation_description="Process HTTP requests",
            quality_requirements={"rate_limit_rps": 100}
        )
        
        api_component = assembler.assemble_component(business_method, api_spec)
        
        # Should include API-specific initialization
        assert "rate_limit_rps" in api_component
        assert "api" in api_component.lower() or "endpoint" in api_component.lower()
    
    def test_preserve_business_logic_exactly(self):
        """Test that business logic is preserved exactly without modification"""
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        # Complex business logic with specific formatting
        original_business_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complex business logic with specific formatting
    """
    # Step 1: Validate input
    if not isinstance(item, dict):
        raise ValueError("Input must be a dictionary")
    
    # Step 2: Extract data
    numbers = item.get('numbers', [])
    multiplier = item.get('multiplier', 2)
    
    # Step 3: Process with error handling
    results = []
    errors = []
    
    for i, num in enumerate(numbers):
        try:
            if isinstance(num, (int, float)):
                result = num * multiplier
                results.append(result)
            else:
                errors.append(f"Invalid number at index {i}: {num}")
        except Exception as e:
            errors.append(f"Error processing index {i}: {str(e)}")
    
    # Step 4: Return structured result
    return {
        'results': results,
        'errors': errors,
        'processed_count': len(results),
        'error_count': len(errors),
        'success_rate': len(results) / len(numbers) if numbers else 1.0
    }'''
        
        business_spec = BusinessLogicSpec(
            component_name="complex_processor",
            component_type="Transformer",
            business_purpose="Complex data processing",
            input_schema={"numbers": "array"},
            output_schema={"results": "array"},
            transformation_description="Process with error handling"
        )
        
        assembler = ComponentAssembler()
        complete_component = assembler.assemble_component(original_business_method, business_spec)
        
        # Verify exact preservation of business logic
        assert "Complex business logic with specific formatting" in complete_component
        assert "Step 1: Validate input" in complete_component
        assert "if not isinstance(item, dict):" in complete_component
        assert "'success_rate': len(results) / len(numbers) if numbers else 1.0" in complete_component
        
        # Verify indentation is preserved properly
        lines = complete_component.split('\n')
        method_start = next(i for i, line in enumerate(lines) if 'async def process_item' in line)
        
        # Business logic should be indented properly within class
        for i in range(method_start + 1, len(lines)):
            if lines[i].strip() and not lines[i].startswith('class'):
                # Should have proper class method indentation
                assert lines[i].startswith('    '), f"Line should be indented: '{lines[i]}'"
    
    def test_assemble_validates_business_method(self):
        """Test that assembler validates business method before assembly"""
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        assembler = ComponentAssembler()
        
        business_spec = BusinessLogicSpec(
            component_name="test_component",
            component_type="Transformer",
            business_purpose="Test validation",
            input_schema={"data": "object"},
            output_schema={"result": "object"},
            transformation_description="Test transformation"
        )
        
        # Test invalid method (missing async)
        invalid_method_1 = '''def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": "test"}'''
        
        with pytest.raises(ValueError, match="Business method must be async"):
            assembler.assemble_component(invalid_method_1, business_spec)
        
        # Test invalid method (wrong signature)
        invalid_method_2 = '''async def wrong_method_name(self, item):
    return {"result": "test"}'''
        
        with pytest.raises(ValueError, match="Method must be named 'process_item'"):
            assembler.assemble_component(invalid_method_2, business_spec)
        
        # Test invalid method (no return type)
        invalid_method_3 = '''async def process_item(self, item):
    return {"result": "test"}'''
        
        with pytest.raises(ValueError, match="Method must have proper type hints"):
            assembler.assemble_component(invalid_method_3, business_spec)
    
    def test_assemble_creates_valid_python_code(self):
        """Test that assembled component is valid, executable Python code"""
        from autocoder_cc.focused_generation.component_assembler import ComponentAssembler
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        import ast
        
        business_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    numbers = item.get('numbers', [])
    doubled = [n * 2 for n in numbers if isinstance(n, (int, float))]
    return {'doubled_numbers': doubled}'''
        
        business_spec = BusinessLogicSpec(
            component_name="doubler",
            component_type="Transformer",
            business_purpose="Double numbers",
            input_schema={"numbers": "array"},
            output_schema={"doubled_numbers": "array"}, 
            transformation_description="Multiply by 2"
        )
        
        assembler = ComponentAssembler()
        complete_component = assembler.assemble_component(business_method, business_spec)
        
        # Verify it's valid Python syntax
        try:
            ast.parse(complete_component)
        except SyntaxError as e:
            pytest.fail(f"Assembled component has invalid Python syntax: {e}")
        
        # Verify it can be compiled
        try:
            compile(complete_component, '<generated_component>', 'exec')
        except Exception as e:
            pytest.fail(f"Assembled component cannot be compiled: {e}")
        
        # Verify it has the expected structure
        tree = ast.parse(complete_component)
        
        # Should have import statements
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        assert len(imports) > 0, "Should have import statements"
        
        # Should have class definitions
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        assert len(classes) >= 2, "Should have base class and component class"
        
        # Should have the business logic method
        component_class = None
        for cls in classes:
            if cls.name.endswith('Component') and cls.name != 'StandaloneComponentBase':
                component_class = cls
                break
        
        assert component_class is not None, "Should have component class"
        
        methods = [node for node in component_class.body if isinstance(node, ast.AsyncFunctionDef)]
        process_methods = [m for m in methods if m.name == "process_item"]
        assert len(process_methods) == 1, "Should have exactly one process_item method"