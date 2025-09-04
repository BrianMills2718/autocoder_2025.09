from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Autocoder 3.3 Validation Framework
Provides constraint validation, contract validation, and error handling
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import ast
import operator


class ValidationSeverity(Enum):
    """Severity levels for validation errors"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    errors: List['ValidationError'] = field(default_factory=list)
    warnings: List['ValidationError'] = field(default_factory=list)
    info: List['ValidationError'] = field(default_factory=list)
    
    def add_error(self, error: 'ValidationError'):
        """Add a validation error"""
        if error.severity == ValidationSeverity.ERROR:
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == ValidationSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)
    
    def get_all_issues(self) -> List['ValidationError']:
        """Get all validation issues"""
        return self.errors + self.warnings + self.info
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors"""
        return len(self.errors) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        return {
            'is_valid': self.is_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'info_count': len(self.info),
            'total_issues': len(self.get_all_issues())
        }


class ValidationError(Exception):
    """
    Validation error with context and severity
    """
    
    def __init__(self, message: str, field_path: str = "", 
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 constraint: str = "", value: Any = None,
                 expected: Any = None, component: str = ""):
        super().__init__(message)
        self.message = message
        self.field_path = field_path
        self.severity = severity
        self.constraint = constraint
        self.value = value
        self.expected = expected
        self.component = component
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'message': self.message,
            'field_path': self.field_path,
            'severity': self.severity.value,
            'constraint': self.constraint,
            'value': str(self.value) if self.value is not None else None,
            'expected': str(self.expected) if self.expected is not None else None,
            'component': self.component,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        path_str = f" at {self.field_path}" if self.field_path else ""
        comp_str = f" in {self.component}" if self.component else ""
        return f"[{self.severity.value.upper()}]{comp_str}{path_str}: {self.message}"


class ConstraintValidator:
    """
    Validates data against constraint expressions
    Supports Python expressions for property validation
    """
    
    def __init__(self):
        self.logger = get_logger("ConstraintValidator")
        
        # Safe operators for constraint evaluation
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.LShift: operator.lshift,
            ast.RShift: operator.rshift,
            ast.BitOr: operator.or_,
            ast.BitXor: operator.xor,
            ast.BitAnd: operator.and_,
            ast.FloorDiv: operator.floordiv,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.Is: operator.is_,
            ast.IsNot: operator.is_not,
            ast.In: lambda x, y: x in y,
            ast.NotIn: lambda x, y: x not in y,
            ast.And: lambda x, y: x and y,
            ast.Or: lambda x, y: x or y,
            ast.Not: operator.not_,
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }
        
        # Safe built-in functions for constraints
        self.safe_builtins = {
            'len': len,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sum': sum,
            'any': any,
            'all': all,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'sorted': sorted,
            'reversed': reversed,
        }
    
    def validate_constraint(self, data: Dict[str, Any], constraint: str, 
                          field_path: str = "", component: str = "") -> ValidationResult:
        """
        Validate data against a constraint expression
        
        Args:
            data: Data to validate
            constraint: Python expression to evaluate
            field_path: Path to the field being validated
            component: Component name for context
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Parse the constraint expression
            tree = ast.parse(constraint, mode='eval')
            
            # Evaluate the constraint
            constraint_result = self._eval_ast_node(tree.body, data)
            
            if not constraint_result:
                error = ValidationError(
                    message=f"Constraint failed: {constraint}",
                    field_path=field_path,
                    constraint=constraint,
                    value=data,
                    component=component
                )
                result.add_error(error)
        
        except Exception as e:
            error = ValidationError(
                message=f"Constraint evaluation error: {e}",
                field_path=field_path,
                constraint=constraint,
                value=data,
                component=component
            )
            result.add_error(error)
        
        return result
    
    def validate_multiple_constraints(self, data: Dict[str, Any], 
                                    constraints: List[Dict[str, Any]],
                                    component: str = "") -> ValidationResult:
        """
        Validate data against multiple constraints
        
        Args:
            data: Data to validate
            constraints: List of constraint dictionaries with 'expression', 'description', 'severity'
            component: Component name for context
        """
        result = ValidationResult(is_valid=True)
        
        for constraint_info in constraints:
            expression = constraint_info.get('expression', '')
            description = constraint_info.get('description', '')
            severity_str = constraint_info.get('severity', 'error')
            
            try:
                severity = ValidationSeverity(severity_str)
            except ValueError:
                severity = ValidationSeverity.ERROR
            
            constraint_result = self.validate_constraint(
                data=data,
                constraint=expression,
                field_path=description,
                component=component
            )
            
            # Adjust severity of constraint errors
            for error in constraint_result.get_all_issues():
                error.severity = severity
                result.add_error(error)
        
        return result
    
    def _eval_ast_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate an AST node with the given context
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            elif node.id in self.safe_builtins:
                return self.safe_builtins[node.id]
            else:
                raise NameError(f"Name '{node.id}' is not defined")
        elif isinstance(node, ast.Attribute):
            obj = self._eval_ast_node(node.value, context)
            return getattr(obj, node.attr)
        elif isinstance(node, ast.Subscript):
            obj = self._eval_ast_node(node.value, context)
            key = self._eval_ast_node(node.slice, context)
            return obj[key]
        elif isinstance(node, ast.Index):  # Python < 3.9
            return self._eval_ast_node(node.value, context)
        elif isinstance(node, ast.BinOp):
            left = self._eval_ast_node(node.left, context)
            right = self._eval_ast_node(node.right, context)
            op_func = self.safe_operators.get(type(node.op))
            if op_func:
                return op_func(left, right)
            else:
                raise ValueError(f"Unsupported binary operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_ast_node(node.operand, context)
            op_func = self.safe_operators.get(type(node.op))
            if op_func:
                return op_func(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.Compare):
            left = self._eval_ast_node(node.left, context)
            result = True
            for op, comp in zip(node.ops, node.comparators):
                right = self._eval_ast_node(comp, context)
                op_func = self.safe_operators.get(type(op))
                if op_func:
                    result = result and op_func(left, right)
                    left = right  # Chain comparisons
                else:
                    raise ValueError(f"Unsupported comparison operator: {type(op)}")
            return result
        elif isinstance(node, ast.BoolOp):
            op_func = self.safe_operators.get(type(node.op))
            if not op_func:
                raise ValueError(f"Unsupported boolean operator: {type(node.op)}")
            
            values = [self._eval_ast_node(val, context) for val in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
        elif isinstance(node, ast.Call):
            func = self._eval_ast_node(node.func, context)
            args = [self._eval_ast_node(arg, context) for arg in node.args]
            kwargs = {kw.arg: self._eval_ast_node(kw.value, context) for kw in node.keywords}
            return func(*args, **kwargs)
        elif isinstance(node, ast.List):
            return [self._eval_ast_node(item, context) for item in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_ast_node(item, context) for item in node.elts)
        elif isinstance(node, ast.Dict):
            keys = [self._eval_ast_node(k, context) for k in node.keys]
            values = [self._eval_ast_node(v, context) for v in node.values]
            return dict(zip(keys, values))
        else:
            raise ValueError(f"Unsupported AST node type: {type(node)}")


class SchemaValidator:
    """
    Validates data against JSON-like schemas
    """
    
    def __init__(self):
        self.logger = get_logger("SchemaValidator")
    
    def validate_schema(self, data: Any, schema: Dict[str, Any], 
                       field_path: str = "", component: str = "") -> ValidationResult:
        """
        Validate data against a schema
        
        Args:
            data: Data to validate
            schema: Schema definition
            field_path: Current field path for error reporting
            component: Component name for context
        """
        result = ValidationResult(is_valid=True)
        
        # Type validation
        expected_type = schema.get('type')
        if expected_type:
            if not self._validate_type(data, expected_type):
                error = ValidationError(
                    message=f"Expected type {expected_type}, got {type(data).__name__}",
                    field_path=field_path,
                    value=data,
                    expected=expected_type,
                    component=component
                )
                result.add_error(error)
                return result
        
        # Required fields validation (for objects)
        if isinstance(data, dict) and 'required' in schema:
            for required_field in schema['required']:
                if required_field not in data:
                    error = ValidationError(
                        message=f"Required field '{required_field}' is missing",
                        field_path=f"{field_path}.{required_field}" if field_path else required_field,
                        component=component
                    )
                    result.add_error(error)
        
        # Properties validation (for objects)
        if isinstance(data, dict) and 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in data:
                    prop_path = f"{field_path}.{prop_name}" if field_path else prop_name
                    prop_result = self.validate_schema(
                        data[prop_name], prop_schema, prop_path, component
                    )
                    for error in prop_result.get_all_issues():
                        result.add_error(error)
        
        # Array items validation
        if isinstance(data, list) and 'items' in schema:
            items_schema = schema['items']
            for i, item in enumerate(data):
                item_path = f"{field_path}[{i}]" if field_path else f"[{i}]"
                item_result = self.validate_schema(item, items_schema, item_path, component)
                for error in item_result.get_all_issues():
                    result.add_error(error)
        
        # Range validation (for numbers)
        if isinstance(data, (int, float)):
            if 'minimum' in schema and data < schema['minimum']:
                error = ValidationError(
                    message=f"Value {data} is below minimum {schema['minimum']}",
                    field_path=field_path,
                    value=data,
                    expected=f">= {schema['minimum']}",
                    component=component
                )
                result.add_error(error)
            
            if 'maximum' in schema and data > schema['maximum']:
                error = ValidationError(
                    message=f"Value {data} is above maximum {schema['maximum']}",
                    field_path=field_path,
                    value=data,
                    expected=f"<= {schema['maximum']}",
                    component=component
                )
                result.add_error(error)
        
        # String validation
        if isinstance(data, str):
            if 'minLength' in schema and len(data) < schema['minLength']:
                error = ValidationError(
                    message=f"String length {len(data)} is below minimum {schema['minLength']}",
                    field_path=field_path,
                    value=data,
                    component=component
                )
                result.add_error(error)
            
            if 'maxLength' in schema and len(data) > schema['maxLength']:
                error = ValidationError(
                    message=f"String length {len(data)} is above maximum {schema['maxLength']}",
                    field_path=field_path,
                    value=data,
                    component=component
                )
                result.add_error(error)
            
            if 'pattern' in schema:
                pattern = schema['pattern']
                if not re.match(pattern, data):
                    error = ValidationError(
                        message=f"String does not match pattern: {pattern}",
                        field_path=field_path,
                        value=data,
                        expected=pattern,
                        component=component
                    )
                    result.add_error(error)
        
        return result
    
    def _validate_type(self, data: Any, expected_type: str) -> bool:
        """Validate data type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, assume valid
        
        return isinstance(data, expected_python_type)


class ContractValidator:
    """
    Validates contracts between components (input/output compatibility)
    """
    
    def __init__(self):
        self.logger = get_logger("ContractValidator")
        self.schema_validator = SchemaValidator()
        self.constraint_validator = ConstraintValidator()
    
    def validate_contract(self, input_data: Dict[str, Any], input_schema: Dict[str, Any],
                         output_data: Dict[str, Any], output_schema: Dict[str, Any],
                         contracts: List[Dict[str, Any]], component: str = "") -> ValidationResult:
        """
        Validate a contract between input and output data
        
        Args:
            input_data: Input data to component
            input_schema: Schema for input data
            output_data: Output data from component
            output_schema: Schema for output data
            contracts: List of contract expressions
            component: Component name for context
        """
        result = ValidationResult(is_valid=True)
        
        # Validate input against input schema
        input_result = self.schema_validator.validate_schema(
            input_data, input_schema, "input", component
        )
        for error in input_result.get_all_issues():
            result.add_error(error)
        
        # Validate output against output schema
        output_result = self.schema_validator.validate_schema(
            output_data, output_schema, "output", component
        )
        for error in output_result.get_all_issues():
            result.add_error(error)
        
        # Validate contracts (relationships between input and output)
        for contract in contracts:
            expression = contract.get('expression', '')
            description = contract.get('description', '')
            
            # Create context with both input and output data
            context = {
                'input': input_data,
                'output': output_data,
                **input_data,  # Allow direct access to input fields
                **output_data  # Allow direct access to output fields
            }
            
            contract_result = self.constraint_validator.validate_constraint(
                context, expression, f"contract: {description}", component
            )
            for error in contract_result.get_all_issues():
                result.add_error(error)
        
        return result
    
    def validate_field_preservation(self, input_data: Dict[str, Any], 
                                   output_data: Dict[str, Any],
                                   preserved_fields: List[str], 
                                   component: str = "") -> ValidationResult:
        """
        Validate that specified fields are preserved from input to output
        """
        result = ValidationResult(is_valid=True)
        
        for field in preserved_fields:
            if field in input_data:
                if field not in output_data:
                    error = ValidationError(
                        message=f"Required field '{field}' not preserved in output",
                        field_path=field,
                        value=input_data.get(field),
                        component=component
                    )
                    result.add_error(error)
                elif input_data[field] != output_data[field]:
                    error = ValidationError(
                        message=f"Field '{field}' value changed from input to output",
                        field_path=field,
                        value=output_data[field],
                        expected=input_data[field],
                        component=component
                    )
                    result.add_error(error)
        
        return result


def validate_data(data: Any, schema: Dict[str, Any], constraints: List[Dict[str, Any]] = None,
                 component: str = "") -> ValidationResult:
    """
    Convenience function for validating data with schema and constraints
    """
    result = ValidationResult(is_valid=True)
    
    # Schema validation
    schema_validator = SchemaValidator()
    schema_result = schema_validator.validate_schema(data, schema, "", component)
    for error in schema_result.get_all_issues():
        result.add_error(error)
    
    # Constraint validation
    if constraints:
        constraint_validator = ConstraintValidator()
        constraint_result = constraint_validator.validate_multiple_constraints(
            data, constraints, component
        )
        for error in constraint_result.get_all_issues():
            result.add_error(error)
    
    return result