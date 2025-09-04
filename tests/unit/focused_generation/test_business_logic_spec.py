#!/usr/bin/env python3
"""
TDD Tests for BusinessLogicSpec - Focused LLM Generation

Tests the dataclass that captures business requirements extracted from blueprints
for focused LLM generation (RED phase - these should fail initially).
"""

import pytest
from typing import Dict, Any, List
from dataclasses import dataclass

class TestBusinessLogicSpec:
    """Test the BusinessLogicSpec dataclass captures all necessary business context"""
    
    def test_business_logic_spec_creation(self):
        """Test that BusinessLogicSpec can be created with all required fields"""
        # This test will fail until we implement BusinessLogicSpec
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        spec = BusinessLogicSpec(
            component_name="number_doubler",
            component_type="Transformer",
            business_purpose="Double all numeric values in input data",
            input_schema={"numbers": "array of integers"},
            output_schema={"doubled_numbers": "array of integers", "count": "integer"},
            transformation_description="For each number in input.numbers, multiply by 2",
            edge_cases=["Handle non-numeric values", "Handle empty arrays"],
            quality_requirements={"max_latency_ms": 100, "accuracy_required": 0.99},
            validation_rules=["All input numbers must be positive", "Output count must match valid inputs"]
        )
        
        assert spec.component_name == "number_doubler"
        assert spec.component_type == "Transformer"
        assert spec.business_purpose == "Double all numeric values in input data"
        assert "numbers" in spec.input_schema
        assert "doubled_numbers" in spec.output_schema
        assert "multiply by 2" in spec.transformation_description
        assert len(spec.edge_cases) == 2
        assert spec.quality_requirements["max_latency_ms"] == 100
        assert len(spec.validation_rules) == 2
    
    def test_business_logic_spec_validation(self):
        """Test that BusinessLogicSpec validates required fields"""
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        # Should raise ValueError for missing required fields
        with pytest.raises(ValueError, match="business_purpose is required"):
            BusinessLogicSpec(
                component_name="test",
                component_type="Transformer",
                business_purpose="",  # Empty purpose should fail
                input_schema={},
                output_schema={},
                transformation_description="test"
            )
        
        with pytest.raises(ValueError, match="transformation_description is required"):
            BusinessLogicSpec(
                component_name="test", 
                component_type="Transformer",
                business_purpose="Test purpose",
                input_schema={},
                output_schema={},
                transformation_description=""  # Empty transformation should fail
            )
    
    def test_business_logic_spec_to_prompt_context(self):
        """Test that BusinessLogicSpec can generate focused prompt context"""
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        spec = BusinessLogicSpec(
            component_name="data_filter",
            component_type="Transformer",
            business_purpose="Filter data based on criteria",
            input_schema={"records": "array of objects"},
            output_schema={"filtered_records": "array of objects"},
            transformation_description="Keep only records where status = 'active'",
            edge_cases=["Handle empty input", "Handle records without status field"],
            quality_requirements={"max_latency_ms": 50},
            validation_rules=["Must preserve record structure"]
        )
        
        prompt_context = spec.to_prompt_context()
        
        # Verify prompt context contains all necessary information
        assert "Filter data based on criteria" in prompt_context
        assert "records" in prompt_context
        assert "filtered_records" in prompt_context
        assert "status = 'active'" in prompt_context
        assert "Handle empty input" in prompt_context
        assert "max_latency_ms" in prompt_context
        assert "preserve record structure" in prompt_context
        
        # Verify prompt context is concise (focused generation requirement)
        assert len(prompt_context) < 1000, "Prompt context should be concise for focused generation"
    
    def test_business_logic_spec_component_types(self):
        """Test BusinessLogicSpec works with different component types"""
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        component_types = ["Source", "Transformer", "Sink", "Store", "APIEndpoint", "Router"]
        
        for component_type in component_types:
            spec = BusinessLogicSpec(
                component_name=f"test_{component_type.lower()}",
                component_type=component_type,
                business_purpose=f"Test {component_type} functionality",
                input_schema={"data": "object"},
                output_schema={"result": "object"},
                transformation_description=f"Process data for {component_type}"
            )
            
            assert spec.component_type == component_type
            assert component_type in spec.to_prompt_context()
    
    def test_business_logic_spec_serialization(self):
        """Test that BusinessLogicSpec can be serialized/deserialized for storage"""
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        import json
        
        original_spec = BusinessLogicSpec(
            component_name="serialization_test",
            component_type="Transformer",
            business_purpose="Test serialization",
            input_schema={"input": "string"},
            output_schema={"output": "string"},
            transformation_description="Convert input to uppercase",
            edge_cases=["Handle empty strings"],
            quality_requirements={"memory_limit_mb": 100},
            validation_rules=["Output must be uppercase"]
        )
        
        # Test serialization
        serialized = original_spec.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["component_name"] == "serialization_test"
        
        # Test JSON serialization
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)
        
        # Test deserialization
        deserialized_dict = json.loads(json_str)
        reconstructed_spec = BusinessLogicSpec.from_dict(deserialized_dict)
        
        assert reconstructed_spec.component_name == original_spec.component_name
        assert reconstructed_spec.business_purpose == original_spec.business_purpose
        assert reconstructed_spec.transformation_description == original_spec.transformation_description