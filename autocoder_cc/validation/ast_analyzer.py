#!/usr/bin/env python3
"""
AST-based Code Analysis for Placeholder Detection and Port Binding Validation
=============================================================================

Provides reliable code analysis using AST visitors instead of string matching.
Used by Step 5 of Enterprise Roadmap v2 to ensure no NotImplementedError in generated code.

Phase 2C Enhancement: Added port binding validation and component interface validation
"""
import ast
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# Phase 2C: Import port registry for validation
from autocoder_cc.core.port_registry import get_port_registry

@dataclass
class ValidationIssue:
    """Represents a validation issue found during AST analysis"""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: int
    column_number: int = 0
    file_path: Optional[str] = None
    component_name: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PortBindingInfo:
    """Information about port usage in component code"""
    port_variable: str
    assigned_value: Any
    line_number: int
    assignment_type: str  # 'hardcoded', 'config_lookup', 'fallback'
    
class PortBindingVisitor(ast.NodeVisitor):
    """
    AST visitor to validate port binding patterns in generated components
    
    Phase 2C Enhancement: Ensures components properly use allocated ports
    """
    
    def __init__(self, component_name: str = None):
        self.component_name = component_name
        self.issues: List[ValidationIssue] = []
        self.port_bindings: List[PortBindingInfo] = []
        self.hardcoded_ports: Set[int] = set()
        
    def visit_Assign(self, node):
        """Check assignment statements for port-related assignments"""
        # Look for port assignments like self.port = ...
        if (len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Attribute) and
            isinstance(node.targets[0].value, ast.Name) and
            node.targets[0].value.id == 'self' and
            'port' in node.targets[0].attr.lower()):
            
            port_info = self._analyze_port_assignment(node)
            if port_info:
                self.port_bindings.append(port_info)
                
                # Check for hardcoded port values
                if port_info.assignment_type == 'hardcoded':
                    try:
                        port_value = int(port_info.assigned_value)
                        self.hardcoded_ports.add(port_value)
                        
                        # Flag common problematic hardcoded ports
                        if port_value in {80, 443, 8080, 3000, 5000}:
                            self.issues.append(ValidationIssue(
                                issue_type='hardcoded_common_port',
                                severity='error',
                                message=f'Hardcoded common port {port_value} detected. Use config-based allocation.',
                                line_number=node.lineno,
                                component_name=self.component_name,
                                additional_info={'port': port_value}
                            ))
                        elif port_value < 1024:
                            self.issues.append(ValidationIssue(
                                issue_type='hardcoded_privileged_port',
                                severity='error',  
                                message=f'Hardcoded privileged port {port_value} detected. Use port registry allocation.',
                                line_number=node.lineno,
                                component_name=self.component_name,
                                additional_info={'port': port_value}
                            ))
                        else:
                            self.issues.append(ValidationIssue(
                                issue_type='hardcoded_port',
                                severity='warning',
                                message=f'Hardcoded port {port_value} detected. Consider using config-based allocation.',
                                line_number=node.lineno,
                                component_name=self.component_name,
                                additional_info={'port': port_value}
                            ))
                    except (ValueError, TypeError):
                        pass
                        
        self.generic_visit(node)
    
    def _analyze_port_assignment(self, node) -> Optional[PortBindingInfo]:
        """Analyze a port assignment to determine its type and value"""
        attr = node.targets[0].attr
        value = node.value
        
        # Check for config.get('port') pattern (good)
        if (isinstance(value, ast.Call) and
            isinstance(value.func, ast.Attribute) and
            value.func.attr == 'get' and
            len(value.args) > 0 and
            isinstance(value.args[0], ast.Constant) and
            'port' in str(value.args[0].value).lower()):
            
            fallback_value = None
            if len(value.args) > 1:
                if isinstance(value.args[1], ast.Constant):
                    fallback_value = value.args[1].value
            
            return PortBindingInfo(
                port_variable=attr,
                assigned_value=f"config.get('port', {fallback_value})",
                line_number=node.lineno,
                assignment_type='config_lookup'
            )
        
        # Check for hardcoded integer port
        elif isinstance(value, ast.Constant) and isinstance(value.value, int):
            return PortBindingInfo(
                port_variable=attr,
                assigned_value=value.value,
                line_number=node.lineno,
                assignment_type='hardcoded'
            )
        
        # Other assignment types
        else:
            return PortBindingInfo(
                port_variable=attr,
                assigned_value='unknown',
                line_number=node.lineno,
                assignment_type='other'
            )

class ComponentInterfaceVisitor(ast.NodeVisitor):
    """
    AST visitor to validate component interface compliance
    
    Phase 2C Enhancement: Ensures components follow interface contracts
    """
    
    def __init__(self, component_name: str = None, expected_interface: Dict[str, Any] = None):
        self.component_name = component_name
        self.expected_interface = expected_interface or {}
        self.issues: List[ValidationIssue] = []
        self.found_methods: Set[str] = set()
        self.found_init_params: List[str] = []
        self.class_name: Optional[str] = None
        
    def visit_ClassDef(self, node):
        """Validate class definition and interface compliance"""
        self.class_name = node.name
        
        # Check for proper base class inheritance
        expected_bases = self.expected_interface.get('base_classes', [])
        if expected_bases:
            actual_bases = [self._get_base_name(base) for base in node.bases]
            missing_bases = set(expected_bases) - set(actual_bases)
            
            for missing_base in missing_bases:
                self.issues.append(ValidationIssue(
                    issue_type='missing_base_class',
                    severity='error',
                    message=f'Component class missing required base class: {missing_base}',
                    line_number=node.lineno,
                    component_name=self.component_name,
                    additional_info={'expected_bases': expected_bases, 'actual_bases': actual_bases}
                ))
        
        self.generic_visit(node)
        
        # After visiting all methods, check for missing required methods
        required_methods = set(self.expected_interface.get('required_methods', []))
        missing_methods = required_methods - self.found_methods
        
        for missing_method in missing_methods:
            self.issues.append(ValidationIssue(
                issue_type='missing_required_method',
                severity='error',
                message=f'Component missing required method: {missing_method}',
                line_number=node.lineno,
                component_name=self.component_name,
                additional_info={'method_name': missing_method}
            ))
    
    def visit_FunctionDef(self, node):
        """Validate method definitions"""
        self.found_methods.add(node.name)
        
        # Validate __init__ method signature
        if node.name == '__init__':
            self._validate_init_signature(node)
        
        # Validate async methods that should be async
        expected_async_methods = self.expected_interface.get('async_methods', [])
        if node.name in expected_async_methods and not isinstance(node, ast.AsyncFunctionDef):
            self.issues.append(ValidationIssue(
                issue_type='method_should_be_async',
                severity='error',
                message=f'Method {node.name} should be async',
                line_number=node.lineno,
                component_name=self.component_name,
                additional_info={'method_name': node.name}
            ))
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Validate async method definitions"""
        self.found_methods.add(node.name)
        self.generic_visit(node)
        
    def _validate_init_signature(self, node):
        """Validate __init__ method signature matches expected interface"""
        expected_params = self.expected_interface.get('init_params', ['self', 'name', 'config'])
        
        actual_params = [arg.arg for arg in node.args.args]
        self.found_init_params = actual_params
        
        # Check for missing required parameters
        missing_params = set(expected_params) - set(actual_params)
        for missing_param in missing_params:
            self.issues.append(ValidationIssue(
                issue_type='missing_init_parameter',
                severity='error',
                message=f'__init__ method missing required parameter: {missing_param}',
                line_number=node.lineno,
                component_name=self.component_name,
                additional_info={'parameter': missing_param}
            ))
    
    def _get_base_name(self, base_node) -> str:
        """Extract base class name from AST node"""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            return base_node.attr
        else:
            return 'unknown'

class PlaceholderVisitor(ast.NodeVisitor):
    """AST visitor to detect placeholder patterns in generated code"""
    
    def __init__(self):
        self.placeholders = []
    
    def visit_FunctionDef(self, node):
        """Check function definitions for placeholder patterns"""
        # Check for functions with only pass statements
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                self.placeholders.append(f"Function '{node.name}' at line {node.lineno} contains only 'pass'")
            elif isinstance(stmt, ast.Raise) and self._is_not_implemented(stmt):
                self.placeholders.append(f"Function '{node.name}' at line {node.lineno} raises NotImplementedError")
        
        # Check for TODO/FIXME in docstrings
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docstring = node.body[0].value.value
            if isinstance(docstring, str):
                if any(word in docstring.upper() for word in ['TODO', 'FIXME', 'PLACEHOLDER']):
                    self.placeholders.append(f"Function '{node.name}' at line {node.lineno} has placeholder in docstring")
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Check class definitions for placeholder patterns"""
        # Check for empty classes
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.placeholders.append(f"Class '{node.name}' at line {node.lineno} contains only 'pass'")
        
        self.generic_visit(node)
    
    def visit_Raise(self, node):
        """Check for NotImplementedError raises"""
        if self._is_not_implemented(node):
            self.placeholders.append(f"NotImplementedError raised at line {node.lineno}")
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Check for placeholder return values"""
        if node.value:
            # Check for specific placeholder patterns
            if isinstance(node.value, ast.Dict):
                # Check for empty dict or placeholder dicts
                if len(node.value.keys) == 0:
                    self.placeholders.append(f"Empty dict return at line {node.lineno}")
                elif self._is_placeholder_dict(node.value):
                    self.placeholders.append(f"Placeholder dict return at line {node.lineno}")
            
            elif isinstance(node.value, ast.Constant):
                # Check for placeholder constants
                if node.value.value in [42, "placeholder", "TODO", None]:
                    self.placeholders.append(f"Placeholder constant return at line {node.lineno}")
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Check for placeholder variable assignments"""
        if isinstance(node.value, ast.Constant):
            if node.value.value in ["placeholder", "TODO", "FIXME"]:
                self.placeholders.append(f"Placeholder assignment at line {node.lineno}")
        
        self.generic_visit(node)
    
    def _is_not_implemented(self, node):
        """Check if a raise statement raises NotImplementedError"""
        if isinstance(node.exc, ast.Call):
            if isinstance(node.exc.func, ast.Name) and node.exc.func.id == 'NotImplementedError':
                return True
        elif isinstance(node.exc, ast.Name) and node.exc.id == 'NotImplementedError':
            return True
        return False
    
    def _is_placeholder_dict(self, dict_node):
        """Check if a dict contains placeholder patterns"""
        for key, value in zip(dict_node.keys, dict_node.values):
            if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
                key_val = key.value
                val_val = value.value
                
                # Common placeholder patterns
                placeholder_patterns = [
                    ("value", 42),
                    ("test", True),
                    ("placeholder", True),
                    ("dummy", "data")
                ]
                
                if (key_val, val_val) in placeholder_patterns:
                    return True
        
        return False

class EnhancedValidationFramework:
    """
    Enhanced validation framework coordinating all validation types
    
    Phase 2C Implementation: Comprehensive validation with all four levels
    """
    
    def __init__(self):
        self.validation_results: Dict[str, List[ValidationIssue]] = {}
        self.port_registry = get_port_registry()
        
    def validate_component_file(self, 
                               file_path: str, 
                               component_name: str = None,
                               component_type: str = None,
                               system_id: str = None) -> Dict[str, Any]:
        """
        Comprehensive validation of a component file
        
        Args:
            file_path: Path to the component file
            component_name: Name of the component being validated
            component_type: Type of component (APIEndpoint, Store, etc.)
            system_id: ID of the system this component belongs to
            
        Returns:
            Dictionary with validation results
        """
        try:
            with open(file_path, 'r') as f:
                source_code = f.read()
                
            tree = ast.parse(source_code)
            
            # Level 1: Placeholder validation
            placeholder_visitor = PlaceholderVisitor()
            placeholder_visitor.visit(tree)
            
            # Level 2: Port binding validation 
            port_visitor = PortBindingVisitor(component_name)
            port_visitor.visit(tree)
            
            # Level 3: Component interface validation
            expected_interface = self._get_expected_interface(component_type)
            interface_visitor = ComponentInterfaceVisitor(component_name, expected_interface)
            interface_visitor.visit(tree)
            
            # Level 4: Port registry consistency validation
            registry_issues = self._validate_port_registry_consistency(
                component_name, port_visitor.hardcoded_ports, system_id
            )
            
            # Compile results
            all_issues = (
                [self._convert_placeholder_to_issue(p, file_path, component_name) 
                 for p in placeholder_visitor.placeholders] +
                port_visitor.issues +
                interface_visitor.issues +
                registry_issues
            )
            
            validation_result = {
                'file_path': file_path,
                'component_name': component_name,
                'component_type': component_type,
                'system_id': system_id,
                'total_issues': len(all_issues),
                'issues_by_severity': self._group_issues_by_severity(all_issues),
                'port_bindings': port_visitor.port_bindings,
                'hardcoded_ports': list(port_visitor.hardcoded_ports),
                'found_methods': list(interface_visitor.found_methods) if hasattr(interface_visitor, 'found_methods') else [],
                'all_issues': all_issues,
                'validation_passed': len([i for i in all_issues if i.severity == 'error']) == 0
            }
            
            return validation_result
            
        except Exception as e:
            return {
                'file_path': file_path,
                'component_name': component_name,
                'validation_error': str(e),
                'validation_passed': False,
                'all_issues': [ValidationIssue(
                    issue_type='validation_failure',
                    severity='error',
                    message=f'Failed to validate file: {e}',
                    line_number=0,
                    file_path=file_path,
                    component_name=component_name
                )]
            }
    
    def validate_system(self, 
                       component_files: List[Tuple[str, str, str]], 
                       system_id: str) -> Dict[str, Any]:
        """
        Validate an entire system's components
        
        Args:
            component_files: List of (file_path, component_name, component_type) tuples
            system_id: ID of the system being validated
            
        Returns:
            System-wide validation results
        """
        component_results = []
        all_issues = []
        total_components = len(component_files)
        passed_components = 0
        
        for file_path, component_name, component_type in component_files:
            result = self.validate_component_file(
                file_path=file_path,
                component_name=component_name,
                component_type=component_type,
                system_id=system_id
            )
            
            component_results.append(result)
            all_issues.extend(result.get('all_issues', []))
            
            if result.get('validation_passed', False):
                passed_components += 1
        
        # System-level validations
        system_issues = self._validate_system_consistency(component_results, system_id)
        all_issues.extend(system_issues)
        
        return {
            'system_id': system_id,
            'total_components': total_components,
            'passed_components': passed_components,
            'failed_components': total_components - passed_components,
            'system_validation_passed': len([i for i in all_issues if i.severity == 'error']) == 0,
            'total_issues': len(all_issues),
            'issues_by_severity': self._group_issues_by_severity(all_issues),
            'component_results': component_results,
            'system_issues': system_issues,
            'all_issues': all_issues
        }
    
    def _get_expected_interface(self, component_type: str) -> Dict[str, Any]:
        """Get expected interface definition for component type"""
        interfaces = {
            'APIEndpoint': {
                'base_classes': ['ComposedComponent'],
                'required_methods': ['__init__', 'process_item'],
                'async_methods': ['process_item'],
                'init_params': ['self', 'name', 'config']
            },
            'Store': {
                'base_classes': ['ComposedComponent'],
                'required_methods': ['__init__', 'process_item'],
                'async_methods': ['process_item'],
                'init_params': ['self', 'name', 'config']
            },
            'Controller': {
                'base_classes': ['ComposedComponent'],
                'required_methods': ['__init__', 'process_item'],
                'async_methods': ['process_item'],
                'init_params': ['self', 'name', 'config']
            },
            'WebSocket': {
                'base_classes': ['ComposedComponent'],
                'required_methods': ['__init__', 'process_item'],
                'async_methods': ['process_item'],
                'init_params': ['self', 'name', 'config']
            }
        }
        
        return interfaces.get(component_type, {
            'base_classes': ['ComposedComponent'],
            'required_methods': ['__init__'],
            'async_methods': [],
            'init_params': ['self', 'name', 'config']
        })
    
    def _validate_port_registry_consistency(self, 
                                          component_name: str,
                                          hardcoded_ports: Set[int],
                                          system_id: str) -> List[ValidationIssue]:
        """Validate consistency with port registry"""
        issues = []
        
        if not component_name:
            return issues
            
        # Check if component has allocated port in registry
        allocated_port = self.port_registry.get_component_port(component_name)
        
        if allocated_port:
            # Component has allocated port - check for conflicts with hardcoded ports
            if hardcoded_ports and allocated_port not in hardcoded_ports:
                issues.append(ValidationIssue(
                    issue_type='port_allocation_mismatch',
                    severity='error',
                    message=f'Component uses hardcoded ports {hardcoded_ports} but has allocated port {allocated_port}',
                    line_number=0,
                    component_name=component_name,
                    additional_info={
                        'allocated_port': allocated_port,
                        'hardcoded_ports': list(hardcoded_ports)
                    }
                ))
        else:
            # Component doesn't have allocated port but uses hardcoded ports
            if hardcoded_ports:
                issues.append(ValidationIssue(
                    issue_type='missing_port_allocation',
                    severity='warning',
                    message=f'Component uses hardcoded ports {hardcoded_ports} but has no port allocated in registry',
                    line_number=0,
                    component_name=component_name,
                    additional_info={'hardcoded_ports': list(hardcoded_ports)}
                ))
        
        return issues
    
    def _validate_system_consistency(self, 
                                   component_results: List[Dict[str, Any]], 
                                   system_id: str) -> List[ValidationIssue]:
        """Validate system-level consistency"""
        issues = []
        
        # Check for port conflicts across components
        all_hardcoded_ports = {}
        for result in component_results:
            component_name = result.get('component_name')
            hardcoded_ports = result.get('hardcoded_ports', [])
            
            for port in hardcoded_ports:
                if port in all_hardcoded_ports:
                    issues.append(ValidationIssue(
                        issue_type='port_conflict',
                        severity='error',
                        message=f'Port {port} used by multiple components: {component_name} and {all_hardcoded_ports[port]}',
                        line_number=0,
                        component_name=component_name,
                        additional_info={
                            'conflicting_port': port,
                            'other_component': all_hardcoded_ports[port]
                        }
                    ))
                else:
                    all_hardcoded_ports[port] = component_name
        
        return issues
    
    def _convert_placeholder_to_issue(self, 
                                    placeholder_msg: str, 
                                    file_path: str, 
                                    component_name: str) -> ValidationIssue:
        """Convert placeholder detection message to ValidationIssue"""
        # Extract line number from message if present
        line_match = re.search(r'line (\d+)', placeholder_msg)
        line_number = int(line_match.group(1)) if line_match else 0
        
        return ValidationIssue(
            issue_type='placeholder_detected',
            severity='error',
            message=placeholder_msg,
            line_number=line_number,
            file_path=file_path,
            component_name=component_name
        )
    
    def _group_issues_by_severity(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """Group issues by severity level"""
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            
        return severity_counts
    
    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate human-readable validation report"""
        if 'system_id' in validation_result:
            # System validation report
            return self._generate_system_report(validation_result)
        else:
            # Component validation report
            return self._generate_component_report(validation_result)
    
    def _generate_system_report(self, result: Dict[str, Any]) -> str:
        """Generate system validation report"""
        lines = []
        lines.append(f"=== System Validation Report: {result['system_id']} ===")
        lines.append(f"Components: {result['passed_components']}/{result['total_components']} passed")
        lines.append(f"Overall Status: {'PASSED' if result['system_validation_passed'] else 'FAILED'}")
        lines.append("")
        
        severity_counts = result['issues_by_severity']
        lines.append(f"Issues Summary:")
        lines.append(f"  Errors: {severity_counts.get('error', 0)}")
        lines.append(f"  Warnings: {severity_counts.get('warning', 0)}")
        lines.append(f"  Info: {severity_counts.get('info', 0)}")
        lines.append("")
        
        # Component-by-component breakdown
        for comp_result in result['component_results']:
            comp_name = comp_result.get('component_name', 'unknown')
            comp_passed = comp_result.get('validation_passed', False)
            comp_issues = len(comp_result.get('all_issues', []))
            
            status = "✅ PASSED" if comp_passed else "❌ FAILED"
            lines.append(f"  {comp_name}: {status} ({comp_issues} issues)")
        
        return "\n".join(lines)
    
    def _generate_component_report(self, result: Dict[str, Any]) -> str:
        """Generate component validation report"""
        lines = []
        comp_name = result.get('component_name', 'unknown')
        status = "✅ PASSED" if result.get('validation_passed', False) else "❌ FAILED"
        
        lines.append(f"=== Component Validation Report: {comp_name} ===")
        lines.append(f"Status: {status}")
        lines.append(f"File: {result.get('file_path', 'unknown')}")
        lines.append("")
        
        severity_counts = result.get('issues_by_severity', {})
        lines.append(f"Issues Summary:")
        lines.append(f"  Errors: {severity_counts.get('error', 0)}")
        lines.append(f"  Warnings: {severity_counts.get('warning', 0)}")
        lines.append(f"  Info: {severity_counts.get('info', 0)}")
        lines.append("")
        
        # Detailed issues
        all_issues = result.get('all_issues', [])
        if all_issues:
            lines.append("Detailed Issues:")
            for issue in all_issues:
                lines.append(f"  [{issue.severity.upper()}] Line {issue.line_number}: {issue.message}")
        
        return "\n".join(lines)


class ComponentPatternValidator(ast.NodeVisitor):
    """Validates component architecture patterns using AST analysis"""
    
    def __init__(self):
        self.violations = []
        self.component_classes = []
        self.deprecated_patterns = {
            'UnifiedComponent': 'Use ComposedComponent instead',
            'BaseComponent': 'Use ComposedComponent instead', 
            'LegacyComponent': 'Use ComposedComponent instead'
        }
        self.required_methods = {'setup', 'process', 'cleanup', 'health_check'}
        self.composed_component_found = False
    
    def visit_ClassDef(self, node):
        """Validate class definitions for component patterns"""
        # Check for deprecated component inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.deprecated_patterns:
                    self.violations.append({
                        'type': 'deprecated_inheritance',
                        'line': node.lineno,
                        'class_name': node.name,
                        'deprecated_base': base_name,
                        'suggestion': self.deprecated_patterns[base_name],
                        'severity': 'high'
                    })
            elif isinstance(base, ast.Attribute):
                # Handle module.Class patterns
                if isinstance(base.value, ast.Name):
                    full_name = f"{base.value.id}.{base.attr}"
                    if 'UnifiedComponent' in full_name or 'BaseComponent' in full_name:
                        self.violations.append({
                            'type': 'deprecated_inheritance',
                            'line': node.lineno,
                            'class_name': node.name,
                            'deprecated_base': full_name,
                            'suggestion': 'Use ComposedComponent instead',
                            'severity': 'high'
                        })
        
        # Check if this is a ComposedComponent
        if any(isinstance(base, ast.Name) and base.id == 'ComposedComponent' for base in node.bases):
            self.composed_component_found = True
            self._validate_component_class(node)
        
        # Check if class looks like a component but doesn't inherit from ComposedComponent
        if self._looks_like_component(node) and not any(
            isinstance(base, ast.Name) and base.id in ['ComposedComponent', 'Component'] 
            for base in node.bases
        ):
            self.violations.append({
                'type': 'missing_proper_inheritance',
                'line': node.lineno,
                'class_name': node.name,
                'suggestion': 'Component classes should inherit from ComposedComponent',
                'severity': 'medium'
            })
        
        self.generic_visit(node)
    
    def _looks_like_component(self, node):
        """Check if class looks like a component based on method names"""
        method_names = set()
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_names.add(item.name)
        
        # If it has component-like methods, it's probably a component
        component_indicators = {'process', 'setup', 'cleanup', 'receive_streams', 'send_streams'}
        return len(method_names.intersection(component_indicators)) >= 2
    
    def _validate_component_class(self, node):
        """Validate a ComposedComponent class"""
        self.component_classes.append(node.name)
        
        # Check for required methods
        method_names = set()
        async_methods = set()
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_names.add(item.name)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_names.add(item.name)
                async_methods.add(item.name)
        
        # Check for missing required methods
        missing_methods = self.required_methods - method_names
        if missing_methods:
            self.violations.append({
                'type': 'missing_required_methods',
                'line': node.lineno,
                'class_name': node.name,
                'missing_methods': list(missing_methods),
                'suggestion': f'Implement missing methods: {", ".join(missing_methods)}',
                'severity': 'high'
            })
        
        # Check that process method is async
        if 'process' in method_names and 'process' not in async_methods:
            self.violations.append({
                'type': 'sync_process_method',
                'line': node.lineno,
                'class_name': node.name,
                'suggestion': 'process() method should be async',
                'severity': 'medium'
            })
    
    def visit_Import(self, node):
        """Check for deprecated imports"""
        for alias in node.names:
            if 'unified_base' in alias.name or 'UnifiedComponent' in alias.name:
                self.violations.append({
                    'type': 'deprecated_import',
                    'line': node.lineno,
                    'import_name': alias.name,
                    'suggestion': 'Import ComposedComponent instead',
                    'severity': 'high'
                })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check for deprecated from imports"""
        if node.module and ('unified_base' in node.module or 'base_component' in node.module):
            for alias in node.names:
                if alias.name in self.deprecated_patterns:
                    self.violations.append({
                        'type': 'deprecated_from_import',
                        'line': node.lineno,
                        'module': node.module,
                        'import_name': alias.name,
                        'suggestion': self.deprecated_patterns[alias.name],
                        'severity': 'high'
                    })
        self.generic_visit(node)


class HardcodedValueAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for hardcoded values replacing string matching"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.current_function = None
        self.in_test_file = self._is_test_file(file_path)
        self.in_all_assignment = False  # Track if we're in __all__ assignment
        self.is_shared_module = self._is_shared_framework_module(file_path)
        
        # Patterns that indicate hardcoded values
        self.hardcoded_patterns = {
            'port_numbers': r'^\d{4,5}$',  # 4-5 digit port numbers
            'ip_addresses': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
            'urls': r'^https?://',
            'file_paths': r'^(/[^/\s]+)+/?$',  # Unix paths
            'connection_strings': r'(postgresql|mysql|sqlite|mongodb)://',
            'api_keys': r'^[A-Za-z0-9]{20,}$',  # Long alphanumeric strings
        }
        
        # Acceptable hardcoded values
        self.whitelist = {
            'common_ports': {80, 443, 22, 8080, 8000, 3000, 5000},
            'localhost_patterns': {'localhost', '127.0.0.1', '0.0.0.0'},
            'common_paths': {'/tmp', '/var/log', '/etc', '/usr', '/opt'},
            'test_values': {'test', 'example', 'demo', 'sample'},
            'version_patterns': r'^\d+\.\d+(\.\d+)?$',
            'framework_classes': {
                'StandaloneMetricsCollector', 'ComponentCommunicator', 'ComposedComponent',
                'StandaloneTracer', 'StandaloneSpan', 'ComponentStatus', 'MessageEnvelope',
                'ComponentRegistry', 'CommunicationConfig', 'EnhancedValidationFramework',
                'PortBindingVisitor', 'ComponentInterfaceVisitor', 'HardcodedValueAnalyzer'
            }
        }
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file"""
        test_indicators = ['test_', '_test.py', 'conftest.py', '/tests/', '/test/']
        return any(indicator in file_path.lower() for indicator in test_indicators)
    
    def _is_shared_framework_module(self, file_path: str) -> bool:
        """Check if file is a shared framework module (observability.py, communication.py)"""
        framework_modules = ['observability.py', 'communication.py', '/scaffold/', '/scaffolds/']
        return any(indicator in file_path.lower() for indicator in framework_modules)
    
    def visit_FunctionDef(self, node):
        """Track current function context"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Track current async function context"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Assign(self, node):
        """Track assignments, especially __all__"""
        # Check if this is an __all__ assignment
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                self.in_all_assignment = True
                self.generic_visit(node)
                self.in_all_assignment = False
                return
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Analyze constant values for hardcoded patterns"""
        if isinstance(node.value, (str, int)) and not self.in_all_assignment:
            self._check_hardcoded_value(node, str(node.value))
        self.generic_visit(node)
    
    def visit_Str(self, node):
        """Check string literals (Python < 3.8 compatibility)"""
        if not self.in_all_assignment:
            self._check_hardcoded_value(node, node.s)
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Check numeric literals (Python < 3.8 compatibility)"""
        if not self.in_all_assignment:
            self._check_hardcoded_value(node, str(node.n))
        self.generic_visit(node)
    
    def _check_hardcoded_value(self, node, value: str):
        """Check if value appears to be hardcoded"""
        # Skip check in test files for most patterns
        if self.in_test_file and not self._is_critical_hardcoded_value(value):
            return
        
        # Skip check in shared framework modules for framework patterns
        if self.is_shared_module and self._is_likely_identifier(value):
            return
        
        # Check for various hardcoded patterns
        violations = []
        
        # Port numbers
        if value.isdigit() and 1000 <= int(value) <= 65535:
            if int(value) not in self.whitelist['common_ports']:
                violations.append({
                    'type': 'hardcoded_port',
                    'value': value,
                    'suggestion': 'Use environment variable or configuration file'
                })
        
        # IP addresses
        if self._matches_pattern(value, self.hardcoded_patterns['ip_addresses']):
            if value not in self.whitelist['localhost_patterns']:
                violations.append({
                    'type': 'hardcoded_ip',
                    'value': value,
                    'suggestion': 'Use configuration or service discovery'
                })
        
        # URLs
        if self._matches_pattern(value, self.hardcoded_patterns['urls']):
            violations.append({
                'type': 'hardcoded_url',
                'value': value,
                'suggestion': 'Use configuration management'
            })
        
        # Connection strings
        if self._matches_pattern(value, self.hardcoded_patterns['connection_strings']):
            violations.append({
                'type': 'hardcoded_connection_string',
                'value': value,
                'suggestion': 'Use environment variables for connection strings'
            })
        
        # Potential API keys (long alphanumeric strings)
        # Skip if it looks like a class/function name (contains uppercase and lowercase)
        if (len(value) > 20 and 
            self._matches_pattern(value, self.hardcoded_patterns['api_keys']) and
            value not in self.whitelist['test_values'] and
            not self._is_likely_identifier(value)):
            violations.append({
                'type': 'potential_api_key',
                'value': value[:10] + '...',  # Truncate for security
                'suggestion': 'Move sensitive values to environment variables'
            })
        
        # Add violations
        for violation in violations:
            self.violations.append({
                **violation,
                'line': node.lineno,
                'function': self.current_function,
                'severity': self._get_violation_severity(violation['type']),
                'file': self.file_path
            })
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches regex pattern"""
        import re
        try:
            return bool(re.match(pattern, value))
        except:
            return False
    
    def _is_likely_identifier(self, value: str) -> bool:
        """Check if string is likely a Python identifier (class/function name)"""
        # Check if it's in the framework classes whitelist
        if value in self.whitelist['framework_classes']:
            return True
            
        # Check for mixed case (typical of class names)
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        
        # Check for common identifier patterns
        identifier_patterns = [
            'Base', 'Component', 'Class', 'Handler', 'Manager', 
            'Controller', 'Service', 'Provider', 'Factory', 'Builder',
            'Collector', 'Tracer', 'Logger', 'Client', 'Server',
            'Generator', 'Validator', 'Processor', 'Registry',
            'Standalone', 'Communicator', 'Envelope', 'Config',
            'Framework', 'Visitor', 'Analyzer', 'Status'
        ]
        
        # If it has mixed case and contains common identifier words, it's likely a class name
        if has_upper and has_lower:
            for pattern in identifier_patterns:
                if pattern in value:
                    return True
        
        # Check if it's all uppercase (constant) or follows snake_case/camelCase
        if value.isupper() or '_' in value or (has_upper and has_lower):
            return True
        
        # Special case for framework modules: be more lenient with long alphanumeric strings
        # that contain common framework patterns
        if self.is_shared_module and len(value) > 15 and has_upper and has_lower:
            framework_indicators = any(pattern in value for pattern in identifier_patterns)
            if framework_indicators:
                return True
            
        return False
    
    def _is_critical_hardcoded_value(self, value: str) -> bool:
        """Check if value is critical (should be flagged even in tests)"""
        critical_patterns = [
            self.hardcoded_patterns['connection_strings'],
            self.hardcoded_patterns['api_keys']
        ]
        return any(self._matches_pattern(value, pattern) for pattern in critical_patterns)
    
    def _get_violation_severity(self, violation_type: str) -> str:
        """Get severity level for violation type"""
        severity_map = {
            'potential_api_key': 'critical',
            'hardcoded_connection_string': 'high',
            'hardcoded_url': 'medium',
            'hardcoded_ip': 'medium',
            'hardcoded_port': 'low'
        }
        return severity_map.get(violation_type, 'medium')


class CodeQualityAnalyzer(ast.NodeVisitor):
    """Analyzes code quality metrics beyond placeholders"""
    
    def __init__(self):
        self.metrics = {
            'function_count': 0,
            'class_count': 0,
            'complexity_score': 0,
            'has_error_handling': False,
            'has_logging': False,
            'docstring_coverage': 0
        }
        self.functions_with_docstrings = 0
    
    def visit_FunctionDef(self, node):
        """Count functions and check for docstrings"""
        self.metrics['function_count'] += 1
        
        # Check for docstring
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            self.functions_with_docstrings += 1
        
        # Update complexity (simple metric based on nested structures)
        self.metrics['complexity_score'] += self._calculate_complexity(node)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Count classes"""
        self.metrics['class_count'] += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Check for error handling"""
        self.metrics['has_error_handling'] = True
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Check for logging calls"""
        if (isinstance(node.func, ast.Attribute) and 
            isinstance(node.func.value, ast.Name) and
            node.func.value.id in ['logger', 'logging'] and
            node.func.attr in ['info', 'debug', 'warning', 'error', 'critical']):
            self.metrics['has_logging'] = True
        
        self.generic_visit(node)
    
    def finalize_metrics(self):
        """Calculate final metrics"""
        if self.metrics['function_count'] > 0:
            self.metrics['docstring_coverage'] = self.functions_with_docstrings / self.metrics['function_count']
    
    def _calculate_complexity(self, node):
        """Simple complexity calculation"""
        complexity = 1  # Base complexity
        
        # Count control flow statements
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity += 1
        
        return complexity


class ASTValidationRuleEngine:
    """
    Comprehensive AST validation rule engine for component pattern validation.
    
    Replaces string-based validation with comprehensive AST analysis as required 
    by Cycle 21 validation requirements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.results = {
            'placeholder_issues': [],
            'component_violations': [],
            'hardcoded_violations': [],
            'code_quality_metrics': {},
            'files_analyzed': 0,
            'total_violations': 0
        }
        
        # Rule configuration
        self.rules_enabled = self.config.get('rules_enabled', {
            'placeholder_detection': True,
            'component_pattern_validation': True,
            'hardcoded_value_detection': True,
            'code_quality_analysis': True
        })
        
        self.severity_thresholds = self.config.get('severity_thresholds', {
            'critical': 0,  # Fail on any critical issues
            'high': 5,      # Allow up to 5 high severity issues
            'medium': 20,   # Allow up to 20 medium severity issues
            'low': 50       # Allow up to 50 low severity issues
        })
    
    def analyze_file(self, file_path: str, file_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single Python file using comprehensive AST analysis.
        
        Args:
            file_path: Path to the Python file
            file_content: Optional file content (if not provided, reads from file)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Read file content if not provided
            if file_content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            
            # Parse AST
            tree = ast.parse(file_content, filename=file_path)
            
            file_results = {
                'file_path': file_path,
                'analysis_timestamp': datetime.now().isoformat(),
                'placeholders': [],
                'component_violations': [],
                'hardcoded_violations': [],
                'quality_metrics': {},
                'success': True,
                'error': None
            }
            
            # Run enabled analyzers
            if self.rules_enabled.get('placeholder_detection', True):
                placeholder_visitor = PlaceholderVisitor()
                placeholder_visitor.visit(tree)
                file_results['placeholders'] = placeholder_visitor.placeholders
            
            if self.rules_enabled.get('component_pattern_validation', True):
                component_visitor = ComponentPatternValidator()
                component_visitor.visit(tree)
                file_results['component_violations'] = component_visitor.violations
                file_results['component_classes'] = component_visitor.component_classes
                file_results['composed_component_found'] = component_visitor.composed_component_found
            
            if self.rules_enabled.get('hardcoded_value_detection', True):
                hardcoded_visitor = HardcodedValueAnalyzer(file_path)
                hardcoded_visitor.visit(tree)
                file_results['hardcoded_violations'] = hardcoded_visitor.violations
            
            if self.rules_enabled.get('code_quality_analysis', True):
                quality_visitor = CodeQualityAnalyzer()
                quality_visitor.visit(tree)
                quality_visitor.finalize_metrics()
                file_results['quality_metrics'] = quality_visitor.metrics
            
            # Update overall results
            self.results['files_analyzed'] += 1
            self.results['placeholder_issues'].extend(file_results['placeholders'])
            self.results['component_violations'].extend(file_results['component_violations'])
            self.results['hardcoded_violations'].extend(file_results['hardcoded_violations'])
            
            return file_results
            
        except Exception as e:
            error_result = {
                'file_path': file_path,
                'analysis_timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'placeholders': [],
                'component_violations': [],
                'hardcoded_violations': [],
                'quality_metrics': {}
            }
            return error_result
    
    def analyze_directory(self, directory_path: str, 
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory tree.
        
        Args:
            directory_path: Root directory to analyze
            include_patterns: File patterns to include (default: ['*.py'])
            exclude_patterns: File patterns to exclude
            
        Returns:
            Comprehensive analysis results
        """
        from pathlib import Path
        import re
        
        if include_patterns is None:
            include_patterns = ['*.py']
        
        if exclude_patterns is None:
            exclude_patterns = [
                '*/__pycache__/*',
                '*/venv/*',
                '*/node_modules/*',
                '*.pyc',
                '*/.git/*'
            ]
        
        directory = Path(directory_path)
        file_results = []
        
        # Find all Python files
        for pattern in include_patterns:
            for file_path in directory.rglob(pattern):
                # Check exclude patterns
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if re.search(exclude_pattern.replace('*', '.*'), str(file_path)):
                        should_exclude = True
                        break
                
                if not should_exclude:
                    result = self.analyze_file(str(file_path))
                    file_results.append(result)
        
        # Calculate summary statistics
        self._calculate_summary_statistics(file_results)
        
        return {
            'summary': self.results,
            'file_results': file_results,
            'analysis_complete': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_summary_statistics(self, file_results: List[Dict[str, Any]]):
        """Calculate summary statistics from file results"""
        
        # Count violations by severity
        violation_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for file_result in file_results:
            for violation in file_result.get('component_violations', []):
                severity = violation.get('severity', 'medium')
                violation_counts[severity] = violation_counts.get(severity, 0) + 1
            
            for violation in file_result.get('hardcoded_violations', []):
                severity = violation.get('severity', 'medium')
                violation_counts[severity] = violation_counts.get(severity, 0) + 1
        
        self.results['violation_counts'] = violation_counts
        self.results['total_violations'] = sum(violation_counts.values())
        
        # Calculate quality metrics averages
        quality_metrics = []
        for file_result in file_results:
            metrics = file_result.get('quality_metrics', {})
            if metrics:
                quality_metrics.append(metrics)
        
        if quality_metrics:
            avg_metrics = {}
            for key in quality_metrics[0].keys():
                if isinstance(quality_metrics[0][key], (int, float)):
                    avg_metrics[f'avg_{key}'] = sum(m.get(key, 0) for m in quality_metrics) / len(quality_metrics)
            
            self.results['code_quality_metrics'] = avg_metrics
        
        # Check if analysis passes thresholds
        self.results['passes_quality_gates'] = self._check_quality_gates(violation_counts)
    
    def _check_quality_gates(self, violation_counts: Dict[str, int]) -> bool:
        """Check if analysis results pass configured quality gates"""
        for severity, count in violation_counts.items():
            threshold = self.severity_thresholds.get(severity, float('inf'))
            if count > threshold:
                return False
        return True
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        return {
            'summary': self.results,
            'recommendations': self._generate_recommendations(),
            'quality_gate_status': 'PASS' if self.results.get('passes_quality_gates', False) else 'FAIL',
            'next_steps': self._generate_next_steps()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        violation_counts = self.results.get('violation_counts', {})
        
        if violation_counts.get('critical', 0) > 0:
            recommendations.append(
                "CRITICAL: Address critical security/architecture violations immediately"
            )
        
        if violation_counts.get('high', 0) > 5:
            recommendations.append(
                "HIGH: Consider refactoring to reduce high-severity architecture violations"
            )
        
        component_violations = self.results.get('component_violations', [])
        deprecated_patterns = [v for v in component_violations if v.get('type') == 'deprecated_inheritance']
        if deprecated_patterns:
            recommendations.append(
                f"ARCHITECTURE: Migrate {len(deprecated_patterns)} classes from deprecated component patterns to ComposedComponent"
            )
        
        hardcoded_violations = self.results.get('hardcoded_violations', [])
        if hardcoded_violations:
            recommendations.append(
                f"CONFIGURATION: Move {len(hardcoded_violations)} hardcoded values to configuration management"
            )
        
        placeholder_issues = self.results.get('placeholder_issues', [])
        if placeholder_issues:
            recommendations.append(
                f"COMPLETENESS: Implement {len(placeholder_issues)} placeholder/TODO items"
            )
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate concrete next steps for remediation"""
        next_steps = []
        
        # Critical issues first
        critical_violations = [
            v for v in self.results.get('component_violations', []) + self.results.get('hardcoded_violations', [])
            if v.get('severity') == 'critical'
        ]
        
        if critical_violations:
            next_steps.append("1. Fix critical violations immediately")
            for violation in critical_violations[:3]:  # Show first 3
                next_steps.append(f"   - {violation.get('suggestion', 'Address violation')}")
        
        # Component architecture issues
        deprecated_components = [
            v for v in self.results.get('component_violations', [])
            if v.get('type') == 'deprecated_inheritance'
        ]
        
        if deprecated_components:
            next_steps.append("2. Migrate deprecated component patterns")
            next_steps.append("   - Update imports to use ComposedComponent")
            next_steps.append("   - Verify all component classes inherit from ComposedComponent")
        
        # Configuration management
        hardcoded_issues = self.results.get('hardcoded_violations', [])
        if hardcoded_issues:
            next_steps.append("3. Implement configuration management")
            next_steps.append("   - Move hardcoded values to environment variables")
            next_steps.append("   - Create configuration schema validation")
        
        # Code completeness
        placeholder_count = len(self.results.get('placeholder_issues', []))
        if placeholder_count > 0:
            next_steps.append("4. Complete implementation")
            next_steps.append(f"   - Implement {placeholder_count} placeholder/TODO items")
        
        return next_steps


# Convenience functions for easy integration
def analyze_python_file(file_path: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Analyze a single Python file with comprehensive AST validation"""
    engine = ASTValidationRuleEngine(config)
    return engine.analyze_file(file_path)


def analyze_python_project(project_path: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Analyze an entire Python project with comprehensive AST validation"""
    engine = ASTValidationRuleEngine(config)
    return engine.analyze_directory(project_path)


def validate_component_compliance(file_path: str) -> Dict[str, Any]:
    """Quick validation of component architecture compliance"""
    config = {
        'rules_enabled': {
            'placeholder_detection': False,
            'component_pattern_validation': True,
            'hardcoded_value_detection': False,
            'code_quality_analysis': False
        }
    }
    
    result = analyze_python_file(file_path, config)
    
    return {
        'file_path': file_path,
        'is_compliant': len(result.get('component_violations', [])) == 0,
        'violations': result.get('component_violations', []),
        'composed_component_found': result.get('composed_component_found', False),
        'component_classes': result.get('component_classes', [])
    }