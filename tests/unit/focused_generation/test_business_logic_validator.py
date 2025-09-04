#!/usr/bin/env python3
"""
TDD Tests for Business Logic Validator

Tests validation of generated business logic against requirements (not boilerplate)
(RED phase - these should fail initially).
"""

import pytest
from typing import Dict, Any

class TestBusinessLogicValidator:
    """Test validation of business logic accomplishes specified requirements"""
    
    def test_validate_business_logic_accomplishes_transformation(self):
        """Test that validator checks if business logic accomplishes specified transformation"""
        # This test will fail until we implement BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        # Business spec for number doubling
        business_spec = BusinessLogicSpec(
            component_name="number_doubler",
            component_type="Transformer",
            business_purpose="Double all numeric values in input data",
            input_schema={"numbers": "array of integers"},
            output_schema={"doubled_numbers": "array of integers"},
            transformation_description="For each number in input.numbers, multiply by 2"
        )
        
        # Generated method that correctly implements the transformation
        correct_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    numbers = item.get('numbers', [])
    doubled_numbers = [num * 2 for num in numbers if isinstance(num, (int, float))]
    return {'doubled_numbers': doubled_numbers}'''
        
        validator = BusinessLogicValidator()
        validation_result = validator.validate_business_logic(correct_method, business_spec)
        
        # Should pass validation
        assert validation_result.is_valid == True
        assert validation_result.accomplishes_transformation == True
        assert "multiplication by 2" in validation_result.transformation_analysis.lower()
        
        # Test method that doesn't implement the transformation
        incorrect_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    numbers = item.get('numbers', [])
    # This adds 1 instead of multiplying by 2!
    added_numbers = [num + 1 for num in numbers if isinstance(num, (int, float))]
    return {'doubled_numbers': added_numbers}'''
        
        validation_result = validator.validate_business_logic(incorrect_method, business_spec)
        
        # Should fail validation
        assert validation_result.is_valid == False
        assert validation_result.accomplishes_transformation == False
        assert "addition" in validation_result.transformation_analysis.lower()
        assert "does not multiply by 2" in validation_result.errors[0].lower()
    
    def test_validate_input_output_schema_compliance(self):
        """Test that validator checks input/output schema compliance"""
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="user_filter",
            component_type="Transformer",
            business_purpose="Filter active users",
            input_schema={"users": "array of objects", "filter_criteria": "object"},
            output_schema={"active_users": "array of objects", "filtered_count": "integer"},
            transformation_description="Return only users with status='active'"
        )
        
        # Method with correct schema compliance
        correct_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    users = item.get('users', [])
    filter_criteria = item.get('filter_criteria', {})
    
    active_users = [user for user in users if user.get('status') == 'active']
    
    return {
        'active_users': active_users,
        'filtered_count': len(active_users)
    }'''
        
        validator = BusinessLogicValidator()
        validation_result = validator.validate_business_logic(correct_method, business_spec)
        
        assert validation_result.input_schema_compliance == True
        assert validation_result.output_schema_compliance == True
        assert "users" in validation_result.input_fields_found
        assert "filter_criteria" in validation_result.input_fields_found
        assert "active_users" in validation_result.output_fields_found
        assert "filtered_count" in validation_result.output_fields_found
        
        # Method with incorrect schema compliance
        incorrect_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    # Missing filter_criteria input, wrong output field names
    users = item.get('users', [])
    
    active_users = [user for user in users if user.get('status') == 'active']
    
    return {
        'results': active_users,  # Wrong field name
        'total': len(active_users)  # Wrong field name
    }'''
        
        validation_result = validator.validate_business_logic(incorrect_method, business_spec)
        
        assert validation_result.input_schema_compliance == False  # Missing filter_criteria
        assert validation_result.output_schema_compliance == False  # Wrong field names
        assert "filter_criteria" not in validation_result.input_fields_found
        assert "active_users" not in validation_result.output_fields_found
        assert "filtered_count" not in validation_result.output_fields_found
    
    def test_validate_edge_case_handling(self):
        """Test that validator checks if edge cases are properly handled"""
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="division_calculator",
            component_type="Transformer",
            business_purpose="Calculate division with error handling",
            input_schema={"numerator": "number", "denominator": "number"},
            output_schema={"result": "number", "error": "string"},
            transformation_description="Divide numerator by denominator",
            edge_cases=["Handle division by zero", "Handle negative numbers", "Handle non-numeric inputs"]
        )
        
        # Method that handles edge cases properly
        good_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    numerator = item.get('numerator')
    denominator = item.get('denominator')
    
    # Handle non-numeric inputs
    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        return {'result': 0, 'error': 'Non-numeric input provided'}
    
    # Handle division by zero
    if denominator == 0:
        return {'result': 0, 'error': 'Division by zero'}
    
    # Handle negative numbers (validate them)
    result = numerator / denominator
    
    return {'result': result, 'error': ''}'''
        
        validator = BusinessLogicValidator()
        validation_result = validator.validate_business_logic(good_method, business_spec)
        
        assert validation_result.edge_cases_handled == True
        assert "division by zero" in validation_result.edge_case_analysis.lower()
        assert "non-numeric" in validation_result.edge_case_analysis.lower()
        
        # Method that doesn't handle edge cases
        bad_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    numerator = item.get('numerator')
    denominator = item.get('denominator')
    
    # No edge case handling - will crash on division by zero!
    result = numerator / denominator
    
    return {'result': result, 'error': ''}'''
        
        validation_result = validator.validate_business_logic(bad_method, business_spec)
        
        assert validation_result.edge_cases_handled == False
        assert "division by zero not handled" in validation_result.errors[0].lower()
    
    def test_validate_quality_requirements(self):
        """Test that validator considers quality requirements in assessment"""
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="high_performance_sorter",
            component_type="Transformer",
            business_purpose="Sort large arrays efficiently",
            input_schema={"data": "array"},
            output_schema={"sorted_data": "array"},
            transformation_description="Sort array in ascending order",
            quality_requirements={
                "max_latency_ms": 100,
                "memory_limit_mb": 50,
                "algorithm_complexity": "O(n log n)"
            }
        )
        
        # Efficient implementation
        efficient_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    data = item.get('data', [])
    
    # Use efficient built-in sort (O(n log n))
    sorted_data = sorted(data)
    
    return {'sorted_data': sorted_data}'''
        
        validator = BusinessLogicValidator()
        validation_result = validator.validate_business_logic(efficient_method, business_spec)
        
        assert validation_result.quality_requirements_met == True
        assert "efficient" in validation_result.quality_analysis.lower()
        
        # Inefficient implementation
        inefficient_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    data = item.get('data', [])
    
    # Bubble sort - O(n^2) complexity!
    for i in range(len(data)):
        for j in range(len(data) - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    
    return {'sorted_data': data}'''
        
        validation_result = validator.validate_business_logic(inefficient_method, business_spec)
        
        assert validation_result.quality_requirements_met == False
        assert "o(n^2)" in validation_result.quality_analysis.lower()
        assert "exceeds complexity requirement" in validation_result.warnings[0].lower()
    
    def test_validator_focuses_on_business_logic_not_boilerplate(self):
        """Test that validator ignores boilerplate and focuses only on business logic"""
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="simple_adder",
            component_type="Transformer",
            business_purpose="Add two numbers",
            input_schema={"a": "number", "b": "number"},
            output_schema={"sum": "number"},
            transformation_description="Return a + b"
        )
        
        # Business logic method only (what we expect from new system)
        method_only = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    a = item.get('a', 0)
    b = item.get('b', 0)
    return {'sum': a + b}'''
        
        # Complete component with boilerplate (current system output)
        complete_component = '''import logging
from typing import Dict, Any

class StandaloneComponentBase:
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}

class SimpleAdderComponent(StandaloneComponentBase):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        a = item.get('a', 0)
        b = item.get('b', 0)
        return {'sum': a + b}'''
        
        validator = BusinessLogicValidator()
        
        # Both should validate the same way (business logic focus)
        result_method_only = validator.validate_business_logic(method_only, business_spec)
        result_complete = validator.validate_business_logic(complete_component, business_spec)
        
        assert result_method_only.is_valid == result_complete.is_valid
        assert result_method_only.accomplishes_transformation == result_complete.accomplishes_transformation
        assert result_method_only.input_schema_compliance == result_complete.input_schema_compliance
        assert result_method_only.output_schema_compliance == result_complete.output_schema_compliance
        
        # Validation should not mention boilerplate at all
        assert "import" not in result_complete.validation_summary.lower()
        assert "class" not in result_complete.validation_summary.lower()
        assert "standalonecomponentbase" not in result_complete.validation_summary.lower()
    
    def test_validation_result_provides_actionable_feedback(self):
        """Test that validation results provide specific, actionable feedback for fixes"""
        from autocoder_cc.focused_generation.business_logic_validator import BusinessLogicValidator
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="email_parser",
            component_type="Transformer",
            business_purpose="Extract domain from email addresses",
            input_schema={"email": "string"},
            output_schema={"domain": "string", "is_valid": "boolean"},
            transformation_description="Extract domain part after @ symbol",
            edge_cases=["Handle malformed emails", "Handle empty input"]
        )
        
        # Flawed implementation
        flawed_method = '''async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    email = item.get('email')
    
    # This will crash on None or malformed emails!
    domain = email.split('@')[1]
    
    return {'domain': domain}  # Missing is_valid field'''
        
        validator = BusinessLogicValidator()
        validation_result = validator.validate_business_logic(flawed_method, business_spec)
        
        assert validation_result.is_valid == False
        
        # Should provide specific, actionable feedback
        errors = [error.lower() for error in validation_result.errors]
        
        # Should identify specific issues
        assert any("handle none" in error or "handle empty" in error for error in errors)
        assert any("malformed" in error for error in errors)
        assert any("missing" in error and "is_valid" in error for error in errors)
        
        # Should provide suggestions
        suggestions = [suggestion.lower() for suggestion in validation_result.improvement_suggestions]
        
        assert any("check for none" in suggestion or "validate input" in suggestion for suggestion in suggestions)
        assert any("add is_valid" in suggestion for suggestion in suggestions)
        assert any("try/except" in suggestion or "error handling" in suggestion for suggestion in suggestions)