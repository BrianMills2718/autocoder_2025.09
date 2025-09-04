#!/usr/bin/env python3
"""Test direct component generation to validate fixes."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
import json

def test_direct_component_generation():
    """Test direct component generation to validate fixes."""
    
    print("🔧 Testing direct component generation...")
    
    try:
        # Initialize the generator
        generator = LLMComponentGenerator()
        
        # Test component configurations
        test_cases = [
            {
                "component_type": "Source",
                "component_name": "todo_generator",
                "component_description": "Generate todo items",
                "component_config": {"output_type": "json", "interval": 1},
                "class_name": "GeneratedSource_todo_generator"
            },
            {
                "component_type": "Store",
                "component_name": "todo_store",
                "component_description": "Store todo items to database",
                "component_config": {"storage_type": "postgresql"},
                "class_name": "GeneratedStore_todo_store"
            },
            {
                "component_type": "APIEndpoint",
                "component_name": "todo_api",
                "component_description": "Todo API endpoints",
                "component_config": {"port": 8000},
                "class_name": "GeneratedAPIEndpoint_todo_api"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test {i+1}: {test_case['component_type']} - {test_case['component_name']}")
            
            try:
                # Generate the component
                generated_code = generator.generate_component_implementation(
                    test_case["component_type"],
                    test_case["component_name"],
                    test_case["component_description"],
                    test_case["component_config"],
                    test_case["class_name"]
                )
                
                print(f"✅ Generated {test_case['component_type']} successfully")
                print(f"   Code length: {len(generated_code)} characters")
                
                # Validate the generated code
                if validate_generated_code(generated_code, test_case["component_name"]):
                    print(f"✅ Validation passed for {test_case['component_name']}")
                else:
                    print(f"❌ Validation failed for {test_case['component_name']}")
                    return False
                
            except Exception as e:
                print(f"❌ Failed to generate {test_case['component_type']}: {e}")
                return False
        
        print("\n🎉 All direct component generation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Generator initialization failed: {e}")
        return False

def validate_generated_code(code: str, component_name: str) -> bool:
    """Validate generated code meets basic requirements."""
    
    # Check for required imports
    required_imports = [
        "from autocoder_cc.components.composed_base import ComposedComponent",
        "from typing import Dict, Any, Optional",
        "import asyncio",
        "import logging"
    ]
    
    missing_imports = []
    for import_stmt in required_imports:
        if import_stmt not in code:
            missing_imports.append(import_stmt)
    
    if missing_imports:
        print(f"❌ Missing imports: {', '.join(missing_imports)}")
        return False
    
    # Check for blocking async calls
    if "anyio.run(" in code or "asyncio.run(" in code:
        if "def __init__" in code:
            print(f"❌ Blocking async call found in __init__")
            return False
    
    # Check for forbidden patterns
    forbidden_patterns = [
        'raise NotImplementedError',
        'return {"value": 42}',
        'return {"test": True}',
        '# TODO',
        'pass  # TODO',
        'dummy_value',
        'placeholder'
    ]
    
    code_lower = code.lower()
    for pattern in forbidden_patterns:
        if pattern.lower() in code_lower:
            print(f"❌ Contains forbidden pattern: {pattern}")
            return False
    
    # AST validation
    try:
        import ast
        tree = ast.parse(code)
        
        # Check for class definition
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if not classes:
            print(f"❌ No class definition found")
            return False
        
        # Check for required methods (including async methods)
        class_node = classes[0]
        methods = [node.name for node in class_node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        required_methods = ["__init__", "process_item"]
        
        missing_methods = []
        for method in required_methods:
            if method not in methods:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {', '.join(missing_methods)}")
            return False
        
        print(f"✅ AST validation passed")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Direct Component Generation Test")
    print("=" * 50)
    
    success = test_direct_component_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All direct component generation tests passed!")
        sys.exit(0)
    else:
        print("❌ Direct component generation tests failed.")
        sys.exit(1)