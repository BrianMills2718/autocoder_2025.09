#!/usr/bin/env python3
"""
TDD Tests for Blueprint Business Logic Extractor

Tests the extraction of focused business requirements from blueprint components
(RED phase - these should fail initially).
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock

class TestBlueprintExtractor:
    """Test extraction of business logic requirements from blueprint components"""
    
    def test_extract_business_requirements_from_component(self):
        """Test extracting business requirements from a blueprint component"""
        # This test will fail until we implement BlueprintExtractor
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        # Mock blueprint component data
        mock_component = Mock()
        mock_component.name = "number_doubler"
        mock_component.type = "Transformer"
        mock_component.description = "Transform numbers by doubling them"
        mock_component.config = {"multiplier": 2, "precision": "integer"}
        input_mock = Mock()
        input_mock.name = "numbers"
        input_mock.schema_type = "array"
        input_mock.description = "Array of numbers to double"
        input_mock.required = True
        
        output_mock = Mock()
        output_mock.name = "doubled_numbers"
        output_mock.schema_type = "array"
        output_mock.description = "Array of doubled numbers"
        
        mock_component.inputs = [input_mock]
        mock_component.outputs = [output_mock]
        
        extractor = BlueprintExtractor()
        business_spec = extractor.extract_business_requirements(mock_component)
        
        # Verify extraction preserves all business context
        assert business_spec.component_name == "number_doubler"
        assert business_spec.component_type == "Transformer"
        assert "doubling" in business_spec.business_purpose.lower()
        assert "numbers" in business_spec.input_schema
        assert "doubled_numbers" in business_spec.output_schema
        assert "double" in business_spec.transformation_description.lower()
    
    def test_extract_transformation_from_description(self):
        """Test extracting specific transformation logic from component description"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        test_cases = [
            {
                "description": "Filter active users from the input list",
                "expected_transformation": "filter active users"
            },
            {
                "description": "Calculate the sum of all numeric values",
                "expected_transformation": "sum numeric values"
            },
            {
                "description": "Convert timestamps to human readable format",
                "expected_transformation": "convert timestamps readable format"
            },
            {
                "description": "Aggregate customer data by region and compute averages",
                "expected_transformation": "aggregate customer data averages"
            }
        ]
        
        extractor = BlueprintExtractor()
        
        for test_case in test_cases:
            mock_component = Mock()
            mock_component.description = test_case["description"]
            mock_component.name = "test_component"
            mock_component.type = "Transformer"
            mock_component.config = {}
            mock_component.inputs = []
            mock_component.outputs = []
            
            business_spec = extractor.extract_business_requirements(mock_component)
            
            # Verify transformation description captures the essence
            transformation = business_spec.transformation_description.lower()
            expected = test_case["expected_transformation"].lower()
            
            # Check for key concepts (flexible matching)
            key_words = expected.split()
            matches = sum(1 for word in key_words if word in transformation)
            assert matches >= len(key_words) // 2, f"Transformation '{transformation}' should contain concepts from '{expected}'"
    
    def test_extract_input_output_schemas_from_ports(self):
        """Test extracting precise input/output schemas from component ports"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        mock_component = Mock()
        mock_component.name = "data_processor"
        mock_component.type = "Transformer"
        mock_component.description = "Process customer data"
        mock_component.config = {}
        
        # Mock input ports
        input1_mock = Mock()
        input1_mock.name = "customer_data"
        input1_mock.schema_type = "object"
        input1_mock.description = "Customer information"
        input1_mock.required = True
        
        input2_mock = Mock()
        input2_mock.name = "preferences"
        input2_mock.schema_type = "object"
        input2_mock.description = "User preferences"
        input2_mock.required = False
        
        mock_component.inputs = [input1_mock, input2_mock]
        
        # Mock output ports
        output1_mock = Mock()
        output1_mock.name = "processed_data"
        output1_mock.schema_type = "object"
        output1_mock.description = "Processed customer data"
        
        output2_mock = Mock()
        output2_mock.name = "metrics"
        output2_mock.schema_type = "object"
        output2_mock.description = "Processing metrics"
        
        mock_component.outputs = [output1_mock, output2_mock]
        
        extractor = BlueprintExtractor()
        business_spec = extractor.extract_business_requirements(mock_component)
        
        # Verify input schema extraction
        assert "customer_data" in business_spec.input_schema
        assert "preferences" in business_spec.input_schema
        assert business_spec.input_schema["customer_data"]["required"] == True
        assert business_spec.input_schema["preferences"]["required"] == False
        
        # Verify output schema extraction
        assert "processed_data" in business_spec.output_schema
        assert "metrics" in business_spec.output_schema
    
    def test_extract_edge_cases_from_config_and_description(self):
        """Test extracting edge cases from component configuration and description"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        mock_component = Mock()
        mock_component.name = "validator"
        mock_component.type = "Transformer"
        mock_component.description = "Validate user input data, handling empty fields and invalid formats"
        mock_component.config = {
            "allow_empty": False,
            "max_length": 100,
            "required_fields": ["email", "name"],
            "validation_rules": ["email_format", "name_length"]
        }
        mock_component.inputs = []
        mock_component.outputs = []
        
        extractor = BlueprintExtractor()
        business_spec = extractor.extract_business_requirements(mock_component)
        
        # Verify edge cases are extracted
        edge_cases = [case.lower() for case in business_spec.edge_cases]
        
        # Should extract from description
        assert any("empty" in case for case in edge_cases)
        assert any("invalid" in case for case in edge_cases)
        
        # Should extract from config
        assert any("length" in case for case in edge_cases)
        assert any("required" in case for case in edge_cases)
    
    def test_extract_quality_requirements_from_config(self):
        """Test extracting quality requirements (performance, reliability) from config"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        mock_component = Mock()
        mock_component.name = "high_performance_processor"
        mock_component.type = "Transformer"
        mock_component.description = "High-performance data processor"
        mock_component.config = {
            "max_latency_ms": 50,
            "throughput_rps": 1000,
            "memory_limit_mb": 256,
            "error_tolerance": 0.01,
            "retry_attempts": 3,
            "timeout_seconds": 30
        }
        mock_component.inputs = []
        mock_component.outputs = []
        
        extractor = BlueprintExtractor()
        business_spec = extractor.extract_business_requirements(mock_component)
        
        # Verify quality requirements extraction
        quality_req = business_spec.quality_requirements
        
        assert quality_req["max_latency_ms"] == 50
        assert quality_req["throughput_rps"] == 1000
        assert quality_req["memory_limit_mb"] == 256
        assert quality_req["error_tolerance"] == 0.01
        assert quality_req["retry_attempts"] == 3
        assert quality_req["timeout_seconds"] == 30
    
    def test_extract_component_specific_patterns(self):
        """Test that extractor handles component-type-specific patterns"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        extractor = BlueprintExtractor()
        
        # Test Source component
        source_component = Mock()
        source_component.name = "data_source"
        source_component.type = "Source"
        source_component.description = "Generate customer records every 5 seconds"
        source_component.config = {"interval_seconds": 5, "batch_size": 100}
        source_component.inputs = []
        source_output_mock = Mock()
        source_output_mock.name = "records"
        source_output_mock.schema_type = "array"
        source_component.outputs = [source_output_mock]
        
        source_spec = extractor.extract_business_requirements(source_component)
        assert "generate" in source_spec.business_purpose.lower()
        assert source_spec.quality_requirements["interval_seconds"] == 5
        
        # Test Sink component
        sink_component = Mock()
        sink_component.name = "data_sink"
        sink_component.type = "Sink"
        sink_component.description = "Store processed data to database"
        sink_component.config = {"connection_pool_size": 10}
        sink_input_mock = Mock()
        sink_input_mock.name = "data"
        sink_input_mock.schema_type = "object"
        sink_component.inputs = [sink_input_mock]
        sink_component.outputs = []
        
        sink_spec = extractor.extract_business_requirements(sink_component)
        assert "store" in sink_spec.business_purpose.lower()
        assert sink_spec.quality_requirements["connection_pool_size"] == 10
        
        # Test APIEndpoint component
        api_component = Mock()
        api_component.name = "user_api"
        api_component.type = "APIEndpoint"
        api_component.description = "REST API for user management operations"
        api_component.config = {"rate_limit_rps": 100, "auth_required": True}
        api_input_mock = Mock()
        api_input_mock.name = "request"
        api_input_mock.schema_type = "object"
        
        api_output_mock = Mock()
        api_output_mock.name = "response"
        api_output_mock.schema_type = "object"
        
        api_component.inputs = [api_input_mock]
        api_component.outputs = [api_output_mock]
        
        api_spec = extractor.extract_business_requirements(api_component)
        assert "api" in api_spec.business_purpose.lower()
        assert api_spec.quality_requirements["rate_limit_rps"] == 100
    
    def test_extractor_preserves_all_blueprint_context(self):
        """Test that extractor preserves all business context from blueprint (no information loss)"""
        from autocoder_cc.focused_generation.blueprint_extractor import BlueprintExtractor
        
        # Create comprehensive mock component with all possible fields
        mock_component = Mock()
        mock_component.name = "comprehensive_transformer"
        mock_component.type = "Transformer"
        mock_component.description = "Advanced data transformation with validation, filtering, and aggregation"
        mock_component.config = {
            "transformation_rules": ["uppercase", "trim_whitespace"],
            "validation_schema": {"required": ["id", "name"]},
            "performance": {"max_latency_ms": 100, "memory_limit_mb": 512},
            "error_handling": {"retry_count": 3, "fallback_enabled": True},
            "output_format": "json"
        }
        input1_mock = Mock()
        input1_mock.name = "raw_data"
        input1_mock.schema_type = "object"
        input1_mock.description = "Raw input data"
        input1_mock.required = True
        
        input2_mock = Mock()
        input2_mock.name = "config_overrides"
        input2_mock.schema_type = "object"
        input2_mock.description = "Optional config"
        input2_mock.required = False
        
        output1_mock = Mock()
        output1_mock.name = "transformed_data"
        output1_mock.schema_type = "object"
        output1_mock.description = "Transformed output"
        
        output2_mock = Mock()
        output2_mock.name = "validation_errors"
        output2_mock.schema_type = "array"
        output2_mock.description = "List of validation errors"
        
        mock_component.inputs = [input1_mock, input2_mock]
        mock_component.outputs = [output1_mock, output2_mock]
        
        extractor = BlueprintExtractor()
        business_spec = extractor.extract_business_requirements(mock_component)
        
        # Verify NO information loss - everything is preserved
        assert business_spec.component_name == "comprehensive_transformer"
        assert business_spec.component_type == "Transformer"
        assert "transformation" in business_spec.business_purpose.lower()
        assert "validation" in business_spec.business_purpose.lower()
        
        # Input/output schemas preserved
        assert "raw_data" in business_spec.input_schema
        assert "transformed_data" in business_spec.output_schema
        
        # Transformation logic extracted
        assert "uppercase" in business_spec.transformation_description
        assert "trim" in business_spec.transformation_description
        
        # Quality requirements preserved
        assert business_spec.quality_requirements["max_latency_ms"] == 100
        assert business_spec.quality_requirements["memory_limit_mb"] == 512
        
        # Edge cases inferred
        assert len(business_spec.edge_cases) > 0
        assert any("validation" in case.lower() for case in business_spec.edge_cases)
        
        # Validation rules extracted
        assert len(business_spec.validation_rules) > 0