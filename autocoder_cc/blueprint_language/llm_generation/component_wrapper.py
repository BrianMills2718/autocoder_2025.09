"""
Component Wrapper Module

This module provides functionality to wrap generated component classes with
necessary boilerplate code (imports, base classes, etc.) programmatically
instead of having the LLM generate it.
"""

def get_standalone_boilerplate():
    """
    Get the standalone boilerplate code that should wrap every component.
    
    **Phase 2A Improvement**: Now imports from shared observability module instead
    of generating 167 lines of duplicated code. This eliminates code duplication
    while preserving all functionality.
    
    **Before Phase 2A**: 167 lines of observability boilerplate generated inline
    **After Phase 2A**: Single import statement from shared module
    **Reduction**: 166 lines per component (99% reduction in boilerplate)
    
    NOTE: We MUST include the basic imports here since the LLM-generated code
    expects ComposedComponent to be available.
    """
    # CRITICAL FIX: Add the essential imports that ALL components need
    return """
import uuid
from datetime import datetime, timezone

# Essential imports for all components - use sys.path to ensure imports work
import sys
import os
# Add the components directory to sys.path for imports
if __name__ != '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
from observability import ComposedComponent, SpanStatus
# Standard library imports - MUST include all typing types used
from typing import Dict, Any, Optional, List, Tuple, Union, Set
"""


def get_component_imports(component_type: str, component_code: str) -> str:
    """
    Analyze component code and return necessary imports based on what it uses.
    
    Args:
        component_type: Type of component (Store, APIEndpoint, etc.)
        component_code: The generated component class code
        
    Returns:
        Import statements needed for the component
        
    NOTE: Basic imports (typing, observability, communication) are now handled by
    component_logic_generator.py. This function adds additional component-specific imports.
    """
    imports = []
    
    # Basic imports are handled by component_logic_generator.py
    # Add additional component-specific imports here
    
    # CRITICAL FIX: Add communication imports for components that use them
    if "MessageEnvelope" in component_code and "from communication import" not in component_code:
        imports.append("from communication import MessageEnvelope")
    
    if "CommunicationConfig" in component_code and "from communication import" not in component_code:
        if "from communication import MessageEnvelope" not in imports:
            imports.append("from communication import CommunicationConfig")
        else:
            # Extend the existing import
            imports = [imp.replace("from communication import MessageEnvelope", 
                                  "from communication import MessageEnvelope, CommunicationConfig") 
                      if "from communication import MessageEnvelope" in imp else imp 
                      for imp in imports]
    
    if "ComponentCommunicator" in component_code and "from communication import" not in component_code:
        if any("from communication import" in imp for imp in imports):
            # Extend existing communication import
            for i, imp in enumerate(imports):
                if "from communication import" in imp:
                    if "ComponentCommunicator" not in imp:
                        imports[i] = imp.rstrip() + ", ComponentCommunicator"
                    break
        else:
            imports.append("from communication import ComponentCommunicator")
    
    # Check for specific library usage in the code
    if "asyncpg" in component_code:
        imports.append("import asyncpg")
    if "asyncio" in component_code:
        imports.append("import asyncio")
    if "uuid" in component_code:
        imports.append("import uuid")
    if "datetime" in component_code:
        imports.append("from datetime import datetime, timezone")
    if "re." in component_code or "re.compile" in component_code:
        imports.append("import re")
    if "aiohttp" in component_code:
        imports.append("import aiohttp")
    if "json.dumps" in component_code or "json.loads" in component_code:
        imports.append("import json")
    if "httpx" in component_code:
        imports.append("import httpx")
    if "time." in component_code:
        imports.append("import time")
    if "random." in component_code:
        imports.append("import random")
    if "os." in component_code or "os.getenv" in component_code:
        imports.append("import os")
    
    # Component-specific common imports
    if component_type == "Store":
        # Stores often need database libraries
        if "postgres" in component_code.lower():
            imports.append("import asyncpg")
        if "sqlite" in component_code.lower() or "aiosqlite" in component_code:
            imports.append("import aiosqlite")
    elif component_type == "APIEndpoint":
        # API endpoints might need web frameworks
        if "fastapi" in component_code.lower():
            imports.append("from fastapi import FastAPI, HTTPException")
        if "uvicorn" in component_code.lower():
            imports.append("import uvicorn")
    elif component_type == "Controller":
        # Controllers often need MessageEnvelope
        if "MessageEnvelope" in component_code and not any("from communication import" in imp and "MessageEnvelope" in imp for imp in imports):
            imports.append("from communication import MessageEnvelope")
    
    return "\n".join(imports)


def wrap_component_with_boilerplate(
    component_type: str,
    component_name: str, 
    component_code: str
) -> str:
    """
    Wrap a generated component class with necessary boilerplate.
    
    Args:
        component_type: Type of component (Store, APIEndpoint, etc.)
        component_name: Name of the component
        component_code: The generated component class code (just the class)
        
    Returns:
        Complete Python file with boilerplate + component + lifecycle methods
    """
    # DIAGNOSTIC: Log entry state
    print(f"\n=== DIAGNOSTIC: wrap_component_with_boilerplate ENTRY ===")
    print(f"Component: {component_name}, Type: {component_type}")
    print(f"Input has class definition: {'class Generated' in component_code}")
    print(f"Input __init__ count: {component_code.count('def __init__')}")
    print(f"First 200 chars: {component_code[:200]}")
    
    try:
        # Get the base boilerplate
        boilerplate = get_standalone_boilerplate()
        
        # Get component-specific imports
        additional_imports = get_component_imports(component_type, component_code)
        
        # SAFETY CHECK: If component already has ALL lifecycle methods, minimize processing
        # Check for all required lifecycle methods, not just __init__ and process_item
        if all(x in component_code for x in ['class Generated', 'def __init__', 'def process_item', 'def setup(', 'def cleanup(', 'def get_health_status(']):
            # Component seems complete with all lifecycle methods, just add imports if needed
            if 'from observability import' not in component_code:
                return f"{boilerplate}\n{additional_imports}\n\n{component_code}"
            else:
                # Already has imports and all methods, return as-is
                return component_code
        
        # Inject lifecycle methods into the component code
        from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator
        generator = ComponentLogicGenerator(output_dir="/tmp")
        component_code_with_lifecycle = generator._inject_lifecycle_methods(component_code)
        
        # DIAGNOSTIC: After lifecycle injection
        print(f"\n=== DIAGNOSTIC: After _inject_lifecycle_methods ===")
        print(f"Has class definition: {'class Generated' in component_code_with_lifecycle}")
        print(f"__init__ count: {component_code_with_lifecycle.count('def __init__')}")
        if 'class Generated' not in component_code_with_lifecycle:
            print(f"ERROR: Class lost! First 300 chars: {component_code_with_lifecycle[:300]}")
        
        # VALIDATION: Ensure we didn't lose the class definition
        if 'class Generated' not in component_code_with_lifecycle:
            if 'class Generated' in component_code:
                print(f"WARNING: Class definition lost during processing, using original code")
                print(f"Original had class, processed doesn't. First 300 chars of processed: {component_code_with_lifecycle[:300]}")
                component_code_with_lifecycle = component_code
            else:
                print(f"WARNING: No class definition in original component code either!")
                print(f"First 300 chars of original: {component_code[:300]}")
        
        # Combine everything
        complete_code = f"{boilerplate}\n{additional_imports}\n\n{component_code_with_lifecycle}"
        
        # DIAGNOSTIC: Before return
        print(f"\n=== DIAGNOSTIC: wrap_component_with_boilerplate EXIT ===")
        print(f"Final has class: {'class Generated' in complete_code}")
        print(f"Final __init__ count: {complete_code.count('def __init__')}")
        
        # FINAL VALIDATION: Ensure valid Python
        import ast
        try:
            ast.parse(complete_code)
        except SyntaxError as e:
            print(f"ERROR: Processing created invalid Python: {e}")
            print(f"Returning original code with just imports")
            return f"{boilerplate}\n{additional_imports}\n\n{component_code}"
        
        return complete_code
        
    except Exception as e:
        print(f"ERROR in wrap_component_with_boilerplate: {e}")
        print(f"Returning original code with minimal processing")
        # Fallback: just add the essential imports
        boilerplate = get_standalone_boilerplate()
        return f"{boilerplate}\n\n{component_code}"