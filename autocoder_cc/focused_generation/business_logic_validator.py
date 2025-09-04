#!/usr/bin/env python3
"""
BusinessLogicValidator - Validate business logic accomplishes requirements

This module validates that generated business logic methods accomplish the specified
business requirements, focusing on transformation logic rather than code structure.
"""

import ast
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .business_logic_spec import BusinessLogicSpec


@dataclass
class ValidationResult:
    """Results of business logic validation"""
    is_valid: bool
    accomplishes_transformation: bool
    input_schema_compliance: bool = False
    output_schema_compliance: bool = False
    edge_cases_handled: bool = False
    quality_requirements_met: bool = False
    
    # Detailed analysis
    transformation_analysis: str = ""
    input_fields_found: List[str] = field(default_factory=list)
    output_fields_found: List[str] = field(default_factory=list)
    edge_case_analysis: str = ""
    quality_analysis: str = ""
    validation_summary: str = ""
    
    # Issues and suggestions
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


class BusinessLogicValidator:
    """
    Validates business logic accomplishes specified requirements.
    
    Focuses on validating business transformation logic and requirement
    accomplishment rather than code structure or boilerplate presence.
    """
    
    def validate_business_logic(self, business_code: str, business_spec: BusinessLogicSpec) -> ValidationResult:
        """
        Validate that business code accomplishes specified requirements.
        
        Args:
            business_code: Generated business logic code (method or complete component)
            business_spec: Business requirements specification
            
        Returns:
            Detailed validation results with analysis and suggestions
        """
        result = ValidationResult(is_valid=False, accomplishes_transformation=False)
        
        # Extract method code if this is a complete component
        method_code = self._extract_business_method(business_code)
        
        # Validate transformation logic
        self._validate_transformation_logic(method_code, business_spec, result)
        
        # Validate input/output schema compliance
        self._validate_schema_compliance(method_code, business_spec, result)
        
        # Validate edge case handling
        self._validate_edge_cases(method_code, business_spec, result)
        
        # Validate quality requirements
        self._validate_quality_requirements(method_code, business_spec, result)
        
        # Generate overall assessment
        self._generate_overall_assessment(result, business_spec)
        
        return result
    
    def _extract_business_method(self, business_code: str) -> str:
        """Extract business method from complete component or return as-is if already a method"""
        # If it's already just a method, return as-is
        if business_code.strip().startswith('async def process_item'):
            return business_code
            
        # Extract process_item method from complete component
        try:
            tree = ast.parse(business_code)
            for node in ast.walk(tree):
                if (isinstance(node, ast.AsyncFunctionDef) and 
                    node.name == 'process_item'):
                    # Reconstruct the method source
                    lines = business_code.split('\n')
                    method_lines = []
                    in_method = False
                    method_indent = None
                    
                    for line in lines:
                        if 'async def process_item' in line:
                            in_method = True
                            method_indent = len(line) - len(line.lstrip())
                            method_lines.append(line[method_indent:])  # Remove class indentation
                        elif in_method:
                            if line.strip() and len(line) - len(line.lstrip()) <= method_indent:
                                # Next method or class element
                                break
                            elif line.strip():
                                method_lines.append(line[method_indent:])  # Remove class indentation
                            else:
                                method_lines.append("")  # Empty line
                    
                    return '\n'.join(method_lines)
        except:
            pass
            
        # If extraction fails, return original code
        return business_code
    
    def _validate_transformation_logic(self, method_code: str, business_spec: BusinessLogicSpec, result: ValidationResult):
        """Validate that the method implements the required transformation"""
        transformation_desc = business_spec.transformation_description.lower()
        method_lower = method_code.lower()
        
        # Check for specific transformation patterns
        transformation_indicators = []
        
        # Detect actual operations in code first
        actual_operations = []
        if '+' in method_code and any(pattern in method_code for pattern in [' + ', '+ 1', '+ 2', 'num + ']):
            actual_operations.append("addition operation found")
        if '-' in method_code and any(pattern in method_code for pattern in [' - ', '- 1', 'num - ']):
            actual_operations.append("subtraction operation found")
        if '/' in method_code and any(pattern in method_code for pattern in [' / ', '/ 2', 'num / ']):
            actual_operations.append("division operation found")

        # Mathematical operations
        if any(op in transformation_desc for op in ['multiply', 'double', 'triple']):
            if '*' in method_code:
                if ('double' in transformation_desc or 'multiply by 2' in transformation_desc) and '* 2' in method_code:
                    transformation_indicators.append("multiplication by 2 (doubling)")
                elif '* 3' in method_code:
                    transformation_indicators.append("multiplication by 3 (tripling)")
                else:
                    transformation_indicators.append("multiplication operation found")
            else:
                # Check if we found a different operation when multiplication was expected
                if any('addition' in op for op in actual_operations):
                    result.errors.append("Expected multiplication but found addition instead - does not multiply by 2")
                else:
                    result.errors.append("Expected multiplication operation not found")
        
        # Filtering operations
        if any(op in transformation_desc for op in ['filter', 'where', 'condition']):
            if any(pattern in method_lower for pattern in ['if ', 'for ', 'filter(', 'where']):
                transformation_indicators.append("filtering/conditional logic found")
            else:
                result.errors.append("Expected filtering operation not found")
        
        # Aggregation operations
        if any(op in transformation_desc for op in ['sum', 'count', 'average', 'aggregate']):
            if any(pattern in method_lower for pattern in ['sum(', 'len(', 'count', 'average']):
                transformation_indicators.append("aggregation operation found")
            else:
                result.errors.append("Expected aggregation operation not found")
        
        # Conversion operations
        if any(op in transformation_desc for op in ['convert', 'transform', 'format']):
            if any(pattern in method_lower for pattern in ['str(', 'int(', 'float(', 'format']):
                transformation_indicators.append("conversion operation found")
            else:
                result.errors.append("Expected conversion operation not found")
        
        # If we found actual operations but no expected ones, report the actual operations
        if actual_operations and not transformation_indicators:
            transformation_indicators.extend(actual_operations)
        
        result.transformation_analysis = "; ".join(transformation_indicators) if transformation_indicators else "No clear transformation patterns identified"
        result.accomplishes_transformation = len(transformation_indicators) > 0 and len(result.errors) == 0
    
    def _validate_schema_compliance(self, method_code: str, business_spec: BusinessLogicSpec, result: ValidationResult):
        """Validate input/output schema compliance"""
        # Find input fields accessed
        input_fields = []
        for field_name in business_spec.input_schema.keys():
            if f"'{field_name}'" in method_code or f'"{field_name}"' in method_code:
                input_fields.append(field_name)
        
        result.input_fields_found = input_fields
        expected_input_fields = list(business_spec.input_schema.keys())
        result.input_schema_compliance = all(field in input_fields for field in expected_input_fields)
        
        # Find output fields produced
        output_fields = []
        for field_name in business_spec.output_schema.keys():
            if f"'{field_name}'" in method_code or f'"{field_name}"' in method_code:
                output_fields.append(field_name)
        
        result.output_fields_found = output_fields
        expected_output_fields = list(business_spec.output_schema.keys())
        result.output_schema_compliance = all(field in output_fields for field in expected_output_fields)
        
        # Add errors for missing fields
        missing_inputs = [f for f in expected_input_fields if f not in input_fields]
        missing_outputs = [f for f in expected_output_fields if f not in output_fields]
        
        if missing_inputs:
            result.errors.append(f"Missing input fields: {', '.join(missing_inputs)}")
        if missing_outputs:
            result.errors.append(f"Missing output fields: {', '.join(missing_outputs)}")
            for field in missing_outputs:
                result.improvement_suggestions.append(f"Add {field} field to return statement")
    
    def _validate_edge_cases(self, method_code: str, business_spec: BusinessLogicSpec, result: ValidationResult):
        """Validate edge case handling"""
        if not business_spec.edge_cases:
            result.edge_cases_handled = True
            result.edge_case_analysis = "No edge cases specified"
            return
        
        handled_cases = []
        unhandled_cases = []
        
        method_lower = method_code.lower()
        
        for edge_case in business_spec.edge_cases:
            case_lower = edge_case.lower()
            handled = False
            
            # Check for common edge case patterns
            if any(keyword in case_lower for keyword in ['empty', 'none', 'null']):
                if any(pattern in method_lower for pattern in ['if not', 'is none', 'len(', 'empty']):
                    handled = True
                    handled_cases.append(f"empty/null check for: {edge_case}")
            
            if any(keyword in case_lower for keyword in ['invalid', 'error', 'malformed']):
                if any(pattern in method_lower for pattern in ['try:', 'except', 'isinstance', 'validate']):
                    handled = True
                    handled_cases.append(f"error handling for: {edge_case}")
            
            if any(keyword in case_lower for keyword in ['non-numeric', 'numeric', 'type', 'invalid']):
                if any(pattern in method_lower for pattern in ['isinstance', 'type(', 'int(', 'float(']):
                    handled = True
                    handled_cases.append(f"type validation for: {edge_case}")
            
            if any(keyword in case_lower for keyword in ['negative', 'positive']):
                if any(pattern in method_lower for pattern in ['< 0', '> 0', '>= 0', '<= 0', 'abs(', 'negative', 'validate']):
                    handled = True
                    handled_cases.append(f"numeric validation for: {edge_case}")
            
            if any(keyword in case_lower for keyword in ['zero', 'division']):
                if any(pattern in method_lower for pattern in ['!= 0', '== 0', 'zerodivision']):
                    handled = True
                    handled_cases.append(f"zero handling for: {edge_case}")
                elif 'if' in method_lower and ('denominator' in method_lower or 'divisor' in method_lower) and '0' in method_lower:
                    handled = True
                    handled_cases.append(f"zero handling for: {edge_case}")
            
            if not handled:
                unhandled_cases.append(edge_case)
        
        result.edge_cases_handled = len(unhandled_cases) == 0
        result.edge_case_analysis = "; ".join(handled_cases) if handled_cases else "No edge case handling detected"
        
        for unhandled in unhandled_cases:
            result.errors.append(f"Edge case not handled: {unhandled}")
            
            # Generate specific suggestions based on detected issues
            unhandled_lower = unhandled.lower()
            if 'empty' in unhandled_lower or 'none' in unhandled_lower:
                result.improvement_suggestions.append("Check for none values and validate input with isinstance() or 'if not' checks")
            elif 'malformed' in unhandled_lower:
                result.improvement_suggestions.append("Add try/except blocks around parsing operations")
            elif 'zero' in unhandled_lower:
                result.improvement_suggestions.append("Add division by zero check with 'if denominator == 0'")
            else:
                result.improvement_suggestions.append(f"Add handling for {unhandled}")
    
    def _validate_quality_requirements(self, method_code: str, business_spec: BusinessLogicSpec, result: ValidationResult):
        """Validate quality requirements are considered"""
        if not business_spec.quality_requirements:
            result.quality_requirements_met = True
            result.quality_analysis = "No quality requirements specified"
            return
        
        quality_indicators = []
        quality_issues = []
        
        method_lower = method_code.lower()
        
        for req_key, req_value in business_spec.quality_requirements.items():
            req_key_lower = req_key.lower()
            
            # Performance requirements
            if 'latency' in req_key_lower or 'performance' in req_key_lower:
                # Look for efficient algorithms (but skip complexity analysis - handled separately)
                if any(pattern in method_lower for pattern in ['o(n)', 'efficient', 'optimized']):
                    quality_indicators.append("performance considerations found")
            
            # Memory requirements
            if 'memory' in req_key_lower:
                if any(pattern in method_lower for pattern in ['generator', 'yield', 'stream']):
                    quality_indicators.append("memory-efficient patterns found")
            
            # Complexity requirements
            if 'complexity' in req_key_lower:
                complexity_req = str(req_value).lower()
                
                # Check for inefficient patterns FIRST
                if any(pattern in method_lower for pattern in ['bubble', 'selection', 'for i in range', 'nested loop']):
                    # Look for nested loops specifically
                    if 'for i in range' in method_lower and 'for j in range' in method_lower:
                        quality_issues.append("O(n^2) algorithm used, exceeds complexity requirement")
                        quality_indicators.append("inefficient O(n^2) nested loop algorithm detected")
                elif 'o(n log n)' in complexity_req and any(pattern in method_lower for pattern in ['sort', 'sorted']):
                    quality_indicators.append("efficient O(n log n) algorithm used")
        
        result.quality_requirements_met = len(quality_issues) == 0
        result.quality_analysis = "; ".join(quality_indicators) if quality_indicators else "No quality indicators found"
        
        for issue in quality_issues:
            result.warnings.append(issue)
    
    def _generate_overall_assessment(self, result: ValidationResult, business_spec: BusinessLogicSpec):
        """Generate overall validation assessment"""
        # Overall validity
        result.is_valid = (
            result.accomplishes_transformation and
            result.input_schema_compliance and 
            result.output_schema_compliance and
            len(result.errors) == 0
        )
        
        # Generate summary
        summary_parts = []
        
        if result.accomplishes_transformation:
            summary_parts.append("✅ Transformation logic implemented correctly")
        else:
            summary_parts.append("❌ Transformation logic missing or incorrect")
        
        if result.input_schema_compliance and result.output_schema_compliance:
            summary_parts.append("✅ Input/output schema compliance verified")
        else:
            summary_parts.append("❌ Schema compliance issues detected")
        
        if result.edge_cases_handled:
            summary_parts.append("✅ Edge cases properly handled")
        elif business_spec.edge_cases:
            summary_parts.append("⚠️ Some edge cases not handled")
        
        if result.quality_requirements_met:
            summary_parts.append("✅ Quality requirements satisfied")
        elif business_spec.quality_requirements:
            summary_parts.append("⚠️ Quality requirements need attention")
        
        result.validation_summary = "; ".join(summary_parts)