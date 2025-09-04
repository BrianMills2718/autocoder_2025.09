from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Import Path Resolver
Generates correct import paths for components that haven't been written yet
"""

import re
from typing import List, Dict, Any, Optional
import logging


class ImportPathResolver:
    """
    Resolve import paths for components and schemas in generated systems
    
    Key Responsibilities:
    - Generate predictable import paths for components
    - Handle schema imports for test files
    - Create relative imports when needed
    - Maintain consistency with system structure
    """
    
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.logger = get_logger("ImportPathResolver")
        
        # Standard directory structure for generated systems
        self.component_base = "components"
        self.test_base = "tests"
        
    def get_component_import(self, component_name: str, from_test: bool = False) -> str:
        """
        Get import statement for a component class
        
        Args:
            component_name: Snake_case component name (e.g., "inventory_api")
            from_test: Whether the import is from a test file
            
        Returns:
            Import statement string
        """
        module_name = component_name.lower()
        class_name = self._to_pascal_case(component_name)
        
        if from_test:
            # From test file, need to go up one directory
            return f"from ..{self.component_base}.{module_name} import {class_name}"
        else:
            # From component or main file
            return f"from {self.component_base}.{module_name} import {class_name}"
    
    def get_schema_imports(self, 
                          component_name: str, 
                          schema_names: List[str],
                          from_test: bool = False) -> str:
        """
        Get import statement for component schemas
        
        Args:
            component_name: Snake_case component name
            schema_names: List of schema class names to import
            from_test: Whether the import is from a test file
            
        Returns:
            Import statement string
        """
        if not schema_names:
            return ""
            
        module_name = component_name.lower()
        schemas_str = ", ".join(schema_names)
        
        if from_test:
            return f"from ..{self.component_base}.{module_name} import {schemas_str}"
        else:
            return f"from {self.component_base}.{module_name} import {schemas_str}"
    
    def get_test_utilities_imports(self) -> List[str]:
        """Get standard imports needed for test files"""
        return [
            "import pytest",
            "import time",
            "import asyncio",
            "from hypothesis import given, strategies as st",
            "from pydantic import ValidationError",
            "from typing import Dict, Any, List, Optional",
            "from datetime import datetime"
        ]
    
    def get_autocoder_imports(self, from_test: bool = False) -> List[str]:
        """Get imports for Autocoder framework components"""
        imports = []
        
        if from_test:
            # From test files, these would be external imports
            imports.extend([
                "from autocoder_cc.components.enhanced_base import (",
                "    ComponentValidationError,",
                "    DependencyValidationError,",
                "    SchemaValidationError",
                ")"
            ])
        else:
            # From component files
            imports.extend([
                "from autocoder_cc.components.enhanced_base import EnhancedComponent",
                "from autocoder_cc.components.base import ValidationResult",
                "from autocoder_cc.orchestration.component import Component"
            ])
            
        return imports
    
    def get_component_specific_imports(self, component_type: str) -> List[str]:
        """Get imports specific to a component type"""
        imports = []
        
        type_import_map = {
            "APIEndpoint": [
                "from fastapi import FastAPI, HTTPException, Request, Response",
                "from pydantic import BaseModel",
                "import uvicorn"
            ],
            "Store": [
                "from autocoder_cc.components.v5_enhanced_store import V5EnhancedStore",
                "from sqlalchemy import Column, String, Integer, DateTime, Float",
                "from databases import Database"
            ],
            "Source": [
                "from autocoder_cc.components.source import Source",
                "import asyncio",
                "from typing import AsyncGenerator"
            ],
            "Sink": [
                "from autocoder_cc.components.sink import Sink",
                "import asyncio"
            ],
            "Transformer": [
                "from autocoder_cc.components.transformer import Transformer",
                "from typing import Any, Dict"
            ],
            "Controller": [
                "from autocoder_cc.components.controller import Controller",
                "from typing import Any, Dict"
            ],
            "StreamProcessor": [
                "from autocoder_cc.components.stream_processor import StreamProcessor",
                "from typing import AsyncIterator"
            ],
            "Accumulator": [
                "from autocoder_cc.components.accumulator import Accumulator",
                "import redis"
            ]
        }
        
        return type_import_map.get(component_type, [])
    
    def organize_imports(self, imports: List[str]) -> str:
        """
        Organize imports according to PEP 8 standards
        
        Groups:
        1. Standard library imports
        2. Third-party imports
        3. Local imports
        """
        stdlib = []
        third_party = []
        local = []
        
        stdlib_modules = {
            'import asyncio', 'import time', 'import json', 'import logging',
            'import re', 'import os', 'import sys', 'from typing import',
            'from datetime import', 'from pathlib import', 'from dataclasses import'
        }
        
        third_party_modules = {
            'import pytest', 'from hypothesis import', 'from pydantic import',
            'from fastapi import', 'import redis', 'from sqlalchemy import',
            'import uvicorn', 'from databases import'
        }
        
        for imp in imports:
            imp = imp.strip()
            if not imp:
                continue
                
            # Check if it's a standard library import
            if any(imp.startswith(std) for std in stdlib_modules):
                stdlib.append(imp)
            # Check if it's a third-party import
            elif any(imp.startswith(tp) for tp in third_party_modules):
                third_party.append(imp)
            # Everything else is local
            else:
                local.append(imp)
        
        # Combine with proper spacing
        sections = []
        if stdlib:
            sections.append('\n'.join(sorted(set(stdlib))))
        if third_party:
            sections.append('\n'.join(sorted(set(third_party))))
        if local:
            sections.append('\n'.join(sorted(set(local))))
            
        return '\n\n'.join(sections)
    
    def _to_pascal_case(self, snake_case_name: str) -> str:
        """Convert snake_case to PascalCase"""
        parts = snake_case_name.split('_')
        pascal_parts = []
        
        for part in parts:
            if part.upper() == part and len(part) > 1:
                # Already uppercase, likely an acronym
                pascal_parts.append(part)
            else:
                # Normal word, capitalize first letter
                pascal_parts.append(part.capitalize())
                
        return ''.join(pascal_parts)
    
    def get_test_file_imports(self, 
                            component_name: str,
                            component_type: str,
                            schema_names: List[str]) -> str:
        """
        Get all imports needed for a component test file
        
        Args:
            component_name: Component being tested
            component_type: Type of the component
            schema_names: List of schema classes to import
            
        Returns:
            Organized import block as a string
        """
        imports = []
        
        # Standard test utilities
        imports.extend(self.get_test_utilities_imports())
        
        # Component import
        imports.append(self.get_component_import(component_name, from_test=True))
        
        # Schema imports
        if schema_names:
            imports.append(self.get_schema_imports(component_name, schema_names, from_test=True))
        
        # Autocoder framework imports
        imports.extend(self.get_autocoder_imports(from_test=True))
        
        # Organize and return
        return self.organize_imports(imports)