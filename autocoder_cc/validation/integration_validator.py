"""
Integration Validation for Reference Implementation Patterns
Validates pipeline, bindings, health checks, and lifecycle
"""

import ast
import inspect
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from autocoder_cc.observability.structured_logging import get_logger

logger = get_logger(__name__)


class IntegrationValidator:
    """Validates integration aspects of generated components."""
    
    def __init__(self):
        self.validation_results = []
        self.errors = []
        
    def validate_pipeline(self, component_code: str) -> Tuple[bool, List[str]]:
        """Validate pipeline patterns match reference implementation."""
        errors = []
        
        try:
            tree = ast.parse(component_code)
            
            # Check for ComposedComponent base class
            has_composed_base = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'ComposedComponent':
                            has_composed_base = True
                            break
                            
            if not has_composed_base:
                errors.append("Component must inherit from ComposedComponent")
                
            # Check for required async process_item method
            has_process_item = False
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef) and node.name == 'process_item':
                    has_process_item = True
                    # Check signature
                    if len(node.args.args) < 2:  # self, item
                        errors.append("process_item must accept 'self' and 'item' parameters")
                        
            if not has_process_item:
                errors.append("Component must have async process_item method")
                
        except SyntaxError as e:
            errors.append(f"Syntax error in component code: {e}")
            
        return len(errors) == 0, errors
        
    def validate_binding(self, api_code: str, store_code: str) -> Tuple[bool, List[str]]:
        """Validate binding patterns between API and Store components."""
        errors = []
        
        try:
            # Check API has set_store_component method
            api_tree = ast.parse(api_code)
            has_set_store = False
            
            for node in ast.walk(api_tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'set_store_component':
                    has_set_store = True
                    # Check it accepts store parameter
                    if len(node.args.args) < 2:  # self, store
                        errors.append("set_store_component must accept 'store' parameter")
                        
            if not has_set_store:
                errors.append("API component must have set_store_component method")
                
            # Check Store has proper CRUD methods
            store_tree = ast.parse(store_code)
            required_patterns = ['create', 'get', 'update', 'delete', 'list']
            found_patterns = []
            
            for node in ast.walk(store_tree):
                if isinstance(node, ast.AsyncFunctionDef) and node.name == 'process_item':
                    # Look for action handling patterns
                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, ast.Compare):
                            for comparator in sub_node.comparators:
                                if isinstance(comparator, ast.Constant):
                                    value = comparator.value
                                    for pattern in required_patterns:
                                        if pattern in str(value):
                                            found_patterns.append(pattern)
                                            
        except SyntaxError as e:
            errors.append(f"Syntax error in component code: {e}")
            
        return len(errors) == 0, errors
        
    def validate_health_check(self, component_code: str) -> Tuple[bool, List[str]]:
        """Validate health check implementation."""
        errors = []
        
        try:
            tree = ast.parse(component_code)
            
            # Check for get_health_status method
            has_health_check = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'get_health_status':
                    has_health_check = True
                    
                    # Check it returns dict with required fields
                    has_return = False
                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, ast.Return):
                            has_return = True
                            # Check for dict literal with status key
                            if isinstance(sub_node.value, ast.Dict):
                                keys = [k.value if isinstance(k, ast.Constant) else None 
                                       for k in sub_node.value.keys]
                                if 'status' not in keys:
                                    errors.append("get_health_status must return dict with 'status' key")
                                    
                    if not has_return:
                        errors.append("get_health_status must return a value")
                        
            if not has_health_check:
                errors.append("Component must have get_health_status method")
                
        except SyntaxError as e:
            errors.append(f"Syntax error in component code: {e}")
            
        return len(errors) == 0, errors
        
    def validate_lifecycle(self, component_code: str) -> Tuple[bool, List[str]]:
        """Validate lifecycle methods match reference pattern."""
        errors = []
        
        try:
            tree = ast.parse(component_code)
            
            # Required lifecycle methods
            required_methods = ['setup', 'cleanup']
            found_methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in required_methods:
                        found_methods.append(node.name)
                        
            # Check for missing methods
            missing = set(required_methods) - set(found_methods)
            for method in missing:
                errors.append(f"Component missing required lifecycle method: {method}")
                
            # Check for incorrect methods
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == 'teardown':
                        errors.append("Component uses 'teardown' instead of 'cleanup' method")
                    if node.name == 'process' and not node.name == 'process_item':
                        errors.append("Component uses 'process' instead of 'process_item' method")
                        
        except SyntaxError as e:
            errors.append(f"Syntax error in component code: {e}")
            
        return len(errors) == 0, errors
        
    def validate_component_integration(self, component_code: str, component_type: str) -> Dict[str, Any]:
        """Comprehensive integration validation for a component."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        # Run pipeline validation
        pipeline_valid, pipeline_errors = self.validate_pipeline(component_code)
        results['checks']['pipeline'] = pipeline_valid
        if not pipeline_valid:
            results['errors'].extend(pipeline_errors)
            results['valid'] = False
            
        # Run health check validation
        health_valid, health_errors = self.validate_health_check(component_code)
        results['checks']['health'] = health_valid
        if not health_valid:
            results['errors'].extend(health_errors)
            results['valid'] = False
            
        # Run lifecycle validation
        lifecycle_valid, lifecycle_errors = self.validate_lifecycle(component_code)
        results['checks']['lifecycle'] = lifecycle_valid
        if not lifecycle_valid:
            results['errors'].extend(lifecycle_errors)
            results['valid'] = False
            
        # Type-specific validation
        if component_type == 'API':
            # Check for set_store_component method
            try:
                tree = ast.parse(component_code)
                has_binding_method = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == 'set_store_component':
                        has_binding_method = True
                        
                if not has_binding_method:
                    results['warnings'].append("API component should have set_store_component method for bindings")
            except:
                pass
                
        elif component_type == 'Store':
            # Check for storage initialization
            try:
                tree = ast.parse(component_code)
                has_storage = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                        for sub_node in ast.walk(node):
                            if isinstance(sub_node, ast.Assign):
                                for target in sub_node.targets:
                                    if isinstance(target, ast.Attribute):
                                        if hasattr(target, 'attr') and '_' in target.attr:
                                            has_storage = True
                                            
                if not has_storage:
                    results['warnings'].append("Store component should initialize internal storage with underscore prefix")
            except:
                pass
                
        return results
        
    def validate_system_integration(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate integration of complete system."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'component_results': {},
            'system_checks': {}
        }
        
        # Validate each component
        for component in components:
            name = component.get('name', 'unknown')
            code = component.get('code', '')
            comp_type = component.get('type', 'unknown')
            
            comp_results = self.validate_component_integration(code, comp_type)
            results['component_results'][name] = comp_results
            
            if not comp_results['valid']:
                results['valid'] = False
                results['errors'].append(f"Component {name} failed validation")
                
        # Check system-level integration
        api_components = [c for c in components if c.get('type') == 'API']
        store_components = [c for c in components if c.get('type') == 'Store']
        
        # Verify API-Store bindings possible
        if api_components and store_components:
            for api in api_components:
                api_code = api.get('code', '')
                for store in store_components:
                    store_code = store.get('code', '')
                    binding_valid, binding_errors = self.validate_binding(api_code, store_code)
                    
                    if not binding_valid:
                        results['warnings'].extend(binding_errors)
                        
        results['system_checks']['has_api'] = len(api_components) > 0
        results['system_checks']['has_store'] = len(store_components) > 0
        results['system_checks']['bindable'] = len(api_components) > 0 and len(store_components) > 0
        
        return results


def validate_integration(component_code: str, component_type: str = 'unknown') -> Dict[str, Any]:
    """Convenience function for integration validation."""
    validator = IntegrationValidator()
    return validator.validate_component_integration(component_code, component_type)


def validate_system(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for system integration validation."""
    validator = IntegrationValidator()
    return validator.validate_system_integration(components)