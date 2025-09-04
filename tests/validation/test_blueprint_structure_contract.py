#!/usr/bin/env python3
"""
Blueprint Structure Contract Tests
Ensures validation components correctly handle both the expected nested structure
and any potential flat structures for backward compatibility.

This test suite validates the CONTRACT between:
1. Blueprint generators (what they produce)
2. Validation systems (what they consume)
3. System generators (what they expect)
"""

import pytest
from typing import Dict, Any
from pathlib import Path

from autocoder_cc.validation.context_builder import PipelineContextBuilder
from autocoder_cc.validation.pipeline_context import PipelineContext
from autocoder_cc.validation.exceptions import ContextBuildException
from autocoder_cc.blueprint_language.intermediate_to_blueprint_translator import IntermediateToBlueprintTranslator
from autocoder_cc.blueprint_language.intermediate_format import (
    IntermediateSystem,
    IntermediateComponent,
    IntermediateBinding,
    IntermediatePort
)


class TestBlueprintStructureContract:
    """Test that validation handles the actual blueprint structure produced by generators"""
    
    @pytest.fixture
    def real_blueprint_structure(self) -> Dict[str, Any]:
        """
        Create a blueprint with the ACTUAL nested structure produced by IntermediateToBlueprintTranslator.
        This is the CONTRACT we must support.
        """
        return {
            "system": {
                "name": "test_pipeline",
                "description": "Test data pipeline",
                "version": "1.0.0",
                "components": [
                    {
                        "name": "csv_file_source",
                        "type": "Source",
                        "description": "CSV file reader",
                        "configuration": {
                            "file_path": "/data/input.csv"
                        }
                    },
                    {
                        "name": "data_filter",
                        "type": "Transformer",
                        "description": "Filter active records",
                        "configuration": {
                            "filter_field": "status",
                            "filter_value": "active"
                        }
                    },
                    {
                        "name": "s3_sink",
                        "type": "Sink",
                        "description": "Write to S3",
                        "configuration": {
                            "bucket": "output-bucket",
                            "prefix": "processed/"
                        }
                    }
                ],
                "connections": [
                    {"from": "csv_file_source.output", "to": "data_filter.input"},
                    {"from": "data_filter.output", "to": "s3_sink.input"}
                ]
            },
            "schemas": {},
            "metadata": {
                "version": "1.0.0",
                "author": "Intermediate Format Translator",
                "autocoder_version": "4.3.0"
            },
            "policy": {
                "security": {
                    "encryption_at_rest": True,
                    "encryption_in_transit": True
                }
            }
        }
    
    @pytest.fixture
    def flat_blueprint_structure(self) -> Dict[str, Any]:
        """
        Legacy flat structure that our OLD tests used.
        We should handle this for backward compatibility.
        """
        return {
            "name": "test_pipeline",
            "components": [
                {
                    "name": "csv_file_source",
                    "type": "Source",
                    "configuration": {}
                },
                {
                    "name": "data_filter",
                    "type": "Transformer",
                    "configuration": {}
                }
            ],
            "connections": [
                {"from": "csv_file_source.output", "to": "data_filter.input"}
            ]
        }
    
    @pytest.fixture
    def context_builder(self) -> PipelineContextBuilder:
        """Create a context builder instance"""
        return PipelineContextBuilder()
    
    def test_context_builder_handles_nested_structure(self, context_builder, real_blueprint_structure):
        """Test that context builder correctly handles the nested blueprint structure"""
        # This should work with the nested structure
        context = context_builder.build_from_blueprint(
            real_blueprint_structure,
            "csv_file_source"
        )
        
        assert context.component_name == "csv_file_source"
        assert context.component_type == "Source"
        assert context.system_name == "test_pipeline"
        assert len(context.downstream_components) == 1
        assert context.downstream_components[0]["name"] == "data_filter"
    
    def test_context_builder_handles_flat_structure(self, context_builder, flat_blueprint_structure):
        """Test that context builder still handles flat structure for backward compatibility"""
        context = context_builder.build_from_blueprint(
            flat_blueprint_structure,
            "csv_file_source"
        )
        
        assert context.component_name == "csv_file_source"
        assert context.component_type == "Source"
        assert context.system_name == "test_pipeline"
        assert len(context.downstream_components) == 1
        assert context.downstream_components[0]["name"] == "data_filter"
    
    def test_component_not_found_in_nested(self, context_builder, real_blueprint_structure):
        """Test proper error when component not found in nested structure"""
        with pytest.raises(ContextBuildException) as exc:
            context_builder.build_from_blueprint(
                real_blueprint_structure,
                "nonexistent_component"
            )
        assert "nonexistent_component not found in blueprint" in str(exc.value)
    
    def test_component_not_found_in_flat(self, context_builder, flat_blueprint_structure):
        """Test proper error when component not found in flat structure"""
        with pytest.raises(ContextBuildException) as exc:
            context_builder.build_from_blueprint(
                flat_blueprint_structure,
                "nonexistent_component"
            )
        assert "nonexistent_component not found in blueprint" in str(exc.value)
    
    def test_extract_relationships_nested(self, context_builder, real_blueprint_structure):
        """Test relationship extraction with nested structure"""
        upstream, downstream = context_builder.extract_relationships(
            real_blueprint_structure,
            "data_filter"
        )
        
        assert len(upstream) == 1
        assert upstream[0]["name"] == "csv_file_source"
        assert upstream[0]["type"] == "Source"
        
        assert len(downstream) == 1
        assert downstream[0]["name"] == "s3_sink"
        assert downstream[0]["type"] == "Sink"
    
    def test_data_flow_pattern_detection(self, context_builder, real_blueprint_structure):
        """Test that data flow pattern detection works with nested structure"""
        pattern = context_builder.analyze_data_flow(real_blueprint_structure)
        
        # Should detect STREAM pattern (Source -> Sink)
        from autocoder_cc.validation.pipeline_context import DataFlowPattern
        assert pattern == DataFlowPattern.STREAM


class TestIntermediateToBlueprintContract:
    """Test the actual blueprint generation to understand the structure contract"""
    
    def test_generated_blueprint_structure(self):
        """Verify the exact structure produced by IntermediateToBlueprintTranslator"""
        # Create an intermediate system
        intermediate = IntermediateSystem(
            name="test_system",
            description="Test system",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="source",
                    type="Source",
                    description="Data source",
                    inputs=[],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={"path": "/data"}
                ),
                IntermediateComponent(
                    name="sink",
                    type="Sink",
                    description="Data sink",
                    inputs=[IntermediatePort(name="input", schema_type="object")],
                    outputs=[],
                    config={"target": "/output"}
                )
            ],
            bindings=[
                IntermediateBinding(
                    from_component="source",
                    from_port="output",
                    to_component="sink",
                    to_port="input"
                )
            ]
        )
        
        # Translate to blueprint
        translator = IntermediateToBlueprintTranslator()
        blueprint_dict = translator._build_blueprint_dict(intermediate)
        
        # Verify structure matches what we expect
        assert "system" in blueprint_dict
        assert "components" in blueprint_dict["system"]
        assert "bindings" in blueprint_dict["system"]
        assert "name" in blueprint_dict["system"]
        
        # Components should be nested under system
        assert len(blueprint_dict["system"]["components"]) == 2
        assert blueprint_dict["system"]["components"][0]["name"] == "source"
        
        # This is the CONTRACT: components are under blueprint["system"]["components"]
        # NOT under blueprint["components"]
        assert "components" not in blueprint_dict  # Components are NOT at top level
        
        # Verify other expected keys
        assert "schemas" in blueprint_dict
        assert "metadata" in blueprint_dict
        assert "policy" in blueprint_dict


class TestValidationComponentContract:
    """Test all validation components handle the structure contract correctly"""
    
    @pytest.fixture
    def nested_blueprint(self) -> Dict[str, Any]:
        """Standard nested blueprint structure"""
        return {
            "system": {
                "name": "validation_test",
                "components": [
                    {
                        "name": "comp1",
                        "type": "Source",
                        "config": {"key": "value"}
                    }
                ],
                "connections": []
            }
        }
    
    def test_pipeline_context_builder_contract(self, nested_blueprint):
        """Ensure PipelineContextBuilder follows the contract"""
        builder = PipelineContextBuilder()
        
        # Should handle nested structure without errors
        context = builder.build_from_blueprint(nested_blueprint, "comp1")
        assert context.component_name == "comp1"
        assert context.component_type == "Source"
        assert context.existing_config == {"key": "value"}
    
    @pytest.mark.parametrize("component_name,expected_type", [
        ("csv_file_source", "Source"),
        ("data_filter", "Transformer"),
        ("s3_sink", "Sink")
    ])
    def test_all_components_found_in_nested(self, component_name, expected_type):
        """Test that all components can be found in nested structure"""
        # Create the real blueprint structure inline
        real_blueprint = {
            "system": {
                "name": "test_pipeline",
                "components": [
                    {"name": "csv_file_source", "type": "Source", "config": {}},
                    {"name": "data_filter", "type": "Transformer", "config": {}},
                    {"name": "s3_sink", "type": "Sink", "config": {}}
                ],
                "connections": []
            }
        }
        
        context_builder = PipelineContextBuilder()
        context = context_builder.build_from_blueprint(
            real_blueprint,
            component_name
        )
        assert context.component_name == component_name
        assert context.component_type == expected_type


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])