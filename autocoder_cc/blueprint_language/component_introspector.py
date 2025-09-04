"""Component introspection for intelligent test data generation"""
import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import re

class ComponentIntrospector:
    """Analyzes component code to understand expected inputs and behavior"""
    
    def analyze_component(self, component_file: Path) -> Dict[str, Any]:
        """
        Analyze a component file to extract input expectations.
        
        Returns:
            Dict containing:
            - expected_fields: Set of field names referenced in code
            - required_fields: Fields that trigger validation errors if missing
            - action_handlers: Dict of action names to handler info
            - data_validations: List of validation checks found
        """
        with open(component_file, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        analysis = {
            'expected_fields': set(),
            'required_fields': set(),
            'action_handlers': {},
            'data_validations': [],
            'component_type': self._detect_component_type(tree)
        }
        
        # Run various analyzers
        self._extract_field_accesses(tree, analysis)
        self._extract_validation_checks(tree, analysis)
        self._extract_action_handlers(tree, analysis)
        
        return analysis
    
    def _detect_component_type(self, tree: ast.AST) -> str:
        """Detect the component type from inheritance and patterns"""
        
        # First, check for any class definition
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 1. Check direct inheritance (existing logic)
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(base.attr)
                
                # Direct type detection
                component_types = ["Source", "Sink", "Transformer", "Model", "Store", 
                                 "APIEndpoint", "Controller", "StreamProcessor", "WebSocket"]
                for base in base_classes:
                    if base in component_types:
                        return base
                
                # 2. NEW: Check class name patterns
                class_name = node.name.lower()
                if 'controller' in class_name:
                    return 'Controller'
                elif 'store' in class_name:
                    return 'Store'
                elif 'apiendpoint' in class_name or 'api_endpoint' in class_name:
                    return 'APIEndpoint'
                elif 'source' in class_name:
                    return 'Source'
                elif 'sink' in class_name:
                    return 'Sink'
                
                # 3. NEW: Check for pattern-based detection
                # Look for controller patterns (action handling)
                has_action_handling = False
                has_payload_handling = False
                
                for inner_node in ast.walk(node):
                    # Check for action field access
                    if (isinstance(inner_node, ast.Call) and 
                        isinstance(inner_node.func, ast.Attribute) and
                        inner_node.func.attr == 'get' and
                        len(inner_node.args) > 0 and
                        isinstance(inner_node.args[0], ast.Constant) and
                        inner_node.args[0].value == 'action'):
                        has_action_handling = True
                    
                    # Check for payload field access
                    if (isinstance(inner_node, ast.Name) and 
                        inner_node.id == 'payload'):
                        has_payload_handling = True
                
                # If has both action and payload handling, it's likely a Controller
                if has_action_handling and has_payload_handling:
                    return 'Controller'
                
                # 4. Check for ComposedComponent with specific patterns
                if 'ComposedComponent' in base_classes:
                    # Additional heuristics for ComposedComponent-based components
                    if has_action_handling:
                        return 'Controller'
                    # Add more patterns as needed
        
        return 'Component'  # Default fallback
    
    def _extract_field_accesses(self, tree: ast.AST, analysis: Dict):
        """Extract all field accesses from data/payload objects"""
        # Track payload-specific fields
        payload_fields = set()
        
        for node in ast.walk(tree):
            # Pattern: data.get('field_name') or item.get('field_name')
            if (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Attribute) and
                node.func.attr == 'get' and
                len(node.args) > 0 and
                isinstance(node.args[0], ast.Constant)):
                
                field_name = node.args[0].value
                
                # Check if accessing from payload
                if (isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'payload'):
                    payload_fields.add(field_name)
                else:
                    analysis['expected_fields'].add(field_name)
                
                # Check if it's a required field (no default value)
                if len(node.args) == 1:  # No default value provided
                    if field_name not in ['payload']:  # Don't mark payload itself as required
                        analysis['required_fields'].add(field_name)
            
            # Pattern: data['field_name']
            elif (isinstance(node, ast.Subscript) and
                  isinstance(node.slice, ast.Constant) and
                  isinstance(node.slice.value, str)):
                
                field_name = node.slice.value
                analysis['expected_fields'].add(field_name)
                analysis['required_fields'].add(field_name)  # Direct access implies required
        
        # Store payload fields separately for better test generation
        analysis['payload_fields'] = payload_fields
    
    def _extract_validation_checks(self, tree: ast.AST, analysis: Dict):
        """Extract validation patterns to understand requirements"""
        for node in ast.walk(tree):
            # Pattern: if 'field' not in data:
            if (isinstance(node, ast.Compare) and
                len(node.ops) == 1 and
                isinstance(node.ops[0], (ast.In, ast.NotIn))):
                
                # Extract field being checked
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    field_name = node.left.value
                    analysis['required_fields'].add(field_name)
                    analysis['data_validations'].append({
                        'type': 'presence_check',
                        'field': field_name
                    })
    
    def _extract_action_handlers(self, tree: ast.AST, analysis: Dict):
        """Extract action-based routing patterns (common in Controllers)"""
        for node in ast.walk(tree):
            # Pattern: if action == 'some_action':
            if (isinstance(node, ast.If) and
                isinstance(node.test, ast.Compare) and
                len(node.test.ops) == 1 and
                isinstance(node.test.ops[0], ast.Eq)):
                
                # Check if comparing against a string constant
                if (isinstance(node.test.left, ast.Name) and 
                    node.test.left.id == 'action' and
                    isinstance(node.test.comparators[0], ast.Constant)):
                    
                    action_name = node.test.comparators[0].value
                    analysis['action_handlers'][action_name] = {
                        'fields': self._extract_fields_from_block(node.body)
                    }
    
    def _extract_fields_from_block(self, body: List[ast.stmt]) -> Set[str]:
        """Extract field references from a code block"""
        fields = set()
        for stmt in body:
            for node in ast.walk(stmt):
                if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'get' and
                    len(node.args) > 0 and
                    isinstance(node.args[0], ast.Constant)):
                    fields.add(node.args[0].value)
        return fields