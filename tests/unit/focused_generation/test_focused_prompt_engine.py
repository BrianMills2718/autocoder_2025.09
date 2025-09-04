#!/usr/bin/env python3
"""
TDD Tests for Focused Prompt Engine

Tests the generation of business-logic-only prompts without boilerplate
(RED phase - these should fail initially).
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock

class TestFocusedPromptEngine:
    """Test focused prompt generation for business logic only (no boilerplate)"""
    
    @pytest.mark.asyncio
    async def test_generate_focused_prompt_no_boilerplate(self):
        """Test that focused prompts contain NO boilerplate code or infrastructure"""
        # This test will fail until we implement FocusedPromptEngine
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="number_doubler",
            component_type="Transformer",
            business_purpose="Double all numeric values in input data",
            input_schema={"numbers": "array of integers"},
            output_schema={"doubled_numbers": "array of integers"},
            transformation_description="For each number in input.numbers, multiply by 2"
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Verify NO boilerplate in prompt
        boilerplate_patterns = [
            "class StandaloneComponentBase",
            "def get_logger",
            "import logging",
            "class StandaloneMetricsCollector",
            "class StandaloneTracer",
            "def __init__",
            "super().__init__",
            "from typing import Dict, Any",
            "from abc import ABC, abstractmethod"
        ]
        
        for pattern in boilerplate_patterns:
            assert pattern not in prompt, f"Prompt should not contain boilerplate pattern: {pattern}"
        
        # Verify ONLY business logic focus
        business_patterns = [
            "Double all numeric values",
            "multiply by 2",
            "numbers",
            "doubled_numbers",
            "process_item"
        ]
        
        for pattern in business_patterns:
            assert pattern in prompt, f"Prompt should contain business pattern: {pattern}"
    
    def test_focused_prompt_is_concise(self):
        """Test that focused prompts are significantly more concise than current system"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="data_filter",
            component_type="Transformer", 
            business_purpose="Filter records based on status field",
            input_schema={"records": "array of objects"},
            output_schema={"filtered_records": "array of objects"},
            transformation_description="Keep only records where status == 'active'"
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Focused prompts should be <500 characters (vs current 2000+)
        assert len(prompt) < 500, f"Prompt too long: {len(prompt)} chars. Should be <500 for focused generation"
        
        # Should be substantially shorter than current system
        # (Current system embeds 150+ lines of boilerplate = ~6000 chars)
        assert len(prompt) < 1000, "Focused prompt should be dramatically shorter than current system"
        
        # But still contain all necessary business context
        assert "Filter records" in prompt
        assert "status == 'active'" in prompt
        assert "process_item" in prompt
    
    def test_focused_prompt_method_only_generation(self):
        """Test that prompts request ONLY method implementation, not complete files"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="calculator",
            component_type="Transformer",
            business_purpose="Calculate statistical metrics",
            input_schema={"values": "array of numbers"},
            output_schema={"mean": "number", "median": "number", "std_dev": "number"},
            transformation_description="Calculate mean, median, and standard deviation"
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Should request only method implementation
        method_request_patterns = [
            "async def process_item",
            "return only",
            "method implementation",
            "business logic"
        ]
        
        # At least one pattern should be present
        assert any(pattern in prompt for pattern in method_request_patterns), \
            "Prompt should explicitly request method-only implementation"
        
        # Should NOT request complete files
        complete_file_patterns = [
            "complete component",
            "full class",
            "imports at top",
            "complete file",
            "entire implementation"
        ]
        
        for pattern in complete_file_patterns:
            assert pattern not in prompt, f"Prompt should not request complete files: {pattern}"
    
    def test_focused_prompt_includes_specific_requirements(self):
        """Test that prompts include specific transformation requirements, not vague guidance"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="email_validator",
            component_type="Transformer",
            business_purpose="Validate email addresses according to RFC standards",
            input_schema={"email": "string"},
            output_schema={"is_valid": "boolean", "error_message": "string"},
            transformation_description="Check email format, domain validity, and character restrictions",
            edge_cases=["Handle empty strings", "Handle malformed domains", "Handle special characters"],
            quality_requirements={"max_latency_ms": 10},
            validation_rules=["Must follow RFC 5322 standard", "Must validate domain existence"]
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Should include specific requirements
        specific_requirements = [
            "RFC standards",
            "email format",
            "domain validity",
            "empty strings",
            "malformed domains",
            "max_latency_ms: 10",
            "RFC 5322"
        ]
        
        for requirement in specific_requirements:
            assert requirement in prompt, f"Prompt should include specific requirement: {requirement}"
        
        # Should NOT include vague guidance
        vague_patterns = [
            "system-wide architecture",
            "quality patterns",
            "best practices",
            "proper error handling",
            "robust implementation",
            "scalable design"
        ]
        
        for pattern in vague_patterns:
            assert pattern not in prompt, f"Prompt should not include vague guidance: {pattern}"
    
    def test_focused_prompt_component_type_specific(self):
        """Test that prompts are tailored to specific component types"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        engine = FocusedPromptEngine()
        
        # Test Source component
        source_spec = BusinessLogicSpec(
            component_name="data_generator",
            component_type="Source",
            business_purpose="Generate synthetic customer data",
            input_schema={},
            output_schema={"customer_record": "object"},
            transformation_description="Create realistic customer records with random but valid data"
        )
        
        source_prompt = engine.generate_business_logic_prompt(source_spec)
        assert "generate" in source_prompt.lower()
        assert "customer_record" in source_prompt
        
        # Test Sink component
        sink_spec = BusinessLogicSpec(
            component_name="database_writer",
            component_type="Sink",
            business_purpose="Store processed data to PostgreSQL database",
            input_schema={"processed_data": "object"},
            output_schema={"write_result": "object"},
            transformation_description="Insert data into customers table with proper error handling"
        )
        
        sink_prompt = engine.generate_business_logic_prompt(sink_spec)
        assert "store" in sink_prompt.lower() or "insert" in sink_prompt.lower()
        assert "PostgreSQL" in sink_prompt
        assert "customers table" in sink_prompt
        
        # Test APIEndpoint component
        api_spec = BusinessLogicSpec(
            component_name="user_endpoint",
            component_type="APIEndpoint",
            business_purpose="Handle user CRUD operations via REST API",
            input_schema={"http_request": "object"},
            output_schema={"http_response": "object"},
            transformation_description="Route to appropriate handler based on HTTP method and path"
        )
        
        api_prompt = engine.generate_business_logic_prompt(api_spec)
        assert "rest api" in api_prompt.lower() or "http" in api_prompt.lower()
        assert "crud" in api_prompt.lower()
    
    def test_focused_prompt_edge_case_handling(self):
        """Test that prompts include specific edge case handling requirements"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="payment_processor",
            component_type="Transformer",
            business_purpose="Process payment transactions with fraud detection", 
            input_schema={"transaction": "object"},
            output_schema={"result": "object", "fraud_score": "number"},
            transformation_description="Validate payment details and calculate fraud risk score",
            edge_cases=[
                "Handle negative amounts",
                "Handle expired cards", 
                "Handle invalid currencies",
                "Handle network timeouts",
                "Handle duplicate transactions"
            ]
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Should include all edge cases
        edge_cases = business_spec.edge_cases
        for edge_case in edge_cases:
            assert edge_case in prompt, f"Prompt should include edge case: {edge_case}"
        
        # Should frame them as requirements, not examples
        assert "must handle" in prompt.lower() or "requirements" in prompt.lower()
    
    def test_focused_prompt_without_examples(self):
        """Test that prompts avoid pattern-matching examples that encourage copying"""
        from autocoder_cc.focused_generation.focused_prompt_engine import FocusedPromptEngine
        from autocoder_cc.focused_generation.business_logic_spec import BusinessLogicSpec
        
        business_spec = BusinessLogicSpec(
            component_name="text_analyzer",
            component_type="Transformer",
            business_purpose="Analyze text sentiment and extract keywords",
            input_schema={"text": "string"},
            output_schema={"sentiment": "string", "keywords": "array"},
            transformation_description="Use NLP techniques to determine sentiment and extract key terms"
        )
        
        engine = FocusedPromptEngine()
        prompt = engine.generate_business_logic_prompt(business_spec)
        
        # Should NOT include pattern-matching examples
        example_patterns = [
            "for example:",
            "like this:",
            "such as:",
            "example implementation:",
            "sample code:",
            "here's how:",
            "you might do:"
        ]
        
        for pattern in example_patterns:
            assert pattern not in prompt.lower(), f"Prompt should not include examples: {pattern}"
        
        # Should focus on requirements instead
        requirement_patterns = [
            "must",
            "should",
            "implement",
            "accomplish",
            "achieve"
        ]
        
        assert any(pattern in prompt.lower() for pattern in requirement_patterns), \
            "Prompt should focus on requirements, not examples"