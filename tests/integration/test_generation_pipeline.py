#!/usr/bin/env python3
"""
Integration test for the complete generation pipeline.
Tests the full flow from natural language to generated system.
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
from autocoder_cc.validation.context_builder import PipelineContextBuilder
from autocoder_cc.validation.pipeline_integration import StrictValidationPipeline
from autocoder_cc.blueprint_language.intermediate_to_blueprint_translator import IntermediateToBlueprintTranslator
from autocoder_cc.blueprint_language.intermediate_format import (
    IntermediateSystem,
    IntermediateComponent,
    IntermediateBinding,
    IntermediatePort
)


class TestGenerationPipeline:
    """Test the complete generation pipeline from NL to system"""
    
    @pytest.fixture
    def sample_nl_request(self) -> str:
        """Sample natural language request"""
        return "Build a data pipeline that reads CSV files from a directory, filters rows where status equals 'active', and writes the results to S3"
    
    @pytest.fixture
    def expected_components(self) -> list:
        """Expected components that should be generated"""
        return ["Source", "Transformer", "Sink"]
    
    def test_intermediate_to_blueprint_structure(self):
        """Test that intermediate format produces correct blueprint structure"""
        # Create intermediate system
        intermediate = IntermediateSystem(
            name="test_pipeline",
            description="Test pipeline",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="csv_source",
                    type="Source",
                    description="Read CSV files",
                    inputs=[],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={"file_path": "/data/input.csv"}
                ),
                IntermediateComponent(
                    name="filter",
                    type="Transformer",
                    description="Filter active records",
                    inputs=[IntermediatePort(name="input", schema_type="object")],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={"filter_field": "status", "filter_value": "active"}
                ),
                IntermediateComponent(
                    name="s3_sink",
                    type="Sink",
                    description="Write to S3",
                    inputs=[IntermediatePort(name="input", schema_type="object")],
                    outputs=[],
                    config={"bucket": "output-bucket"}
                )
            ],
            bindings=[
                IntermediateBinding(
                    from_component="csv_source",
                    from_port="output",
                    to_component="filter",
                    to_port="input"
                ),
                IntermediateBinding(
                    from_component="filter",
                    from_port="output",
                    to_component="s3_sink",
                    to_port="input"
                )
            ]
        )
        
        # Translate to blueprint
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # Verify structure
        assert "system" in blueprint
        assert "components" in blueprint["system"]
        assert len(blueprint["system"]["components"]) == 3
        
        # Verify connections are preserved (called bindings in blueprint)
        assert "bindings" in blueprint["system"]
        assert len(blueprint["system"]["bindings"]) == 2
        
        # Verify component details
        source = blueprint["system"]["components"][0]
        assert source["name"] == "csv_source"
        assert source["type"] == "Source"
        assert source["configuration"]["file_path"] == "/data/input.csv"
    
    def test_context_builder_with_generated_blueprint(self):
        """Test that context builder works with blueprints from the generator"""
        # Generate a blueprint using the translator
        intermediate = IntermediateSystem(
            name="validation_test",
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
                )
            ],
            bindings=[]
        )
        
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # Build context from the generated blueprint
        context_builder = PipelineContextBuilder()
        context = context_builder.build_from_blueprint(blueprint, "source")
        
        # Verify context extraction
        assert context.component_name == "source"
        assert context.component_type == "Source"
        assert context.system_name == "validation_test"
        assert context.existing_config["path"] == "/data"
    
    @pytest.mark.asyncio
    async def test_validation_pipeline_with_generated_blueprint(self):
        """Test that validation pipeline works with generated blueprints"""
        # Generate a blueprint with incomplete config
        intermediate = IntermediateSystem(
            name="healing_test",
            description="Test healing",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="csv_source",
                    type="Source",
                    description="CSV reader",
                    inputs=[],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={}  # Missing required fields
                )
            ],
            bindings=[]
        )
        
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # Create validation pipeline
        pipeline = StrictValidationPipeline()
        
        # Component config is missing required fields
        component_config = {}
        
        # Validate and heal
        result = await pipeline.validate_and_heal_or_fail(
            component_name="csv_source",
            component_type="Source",
            config=component_config,
            blueprint=blueprint
        )
        
        # Should either heal completely or fail clearly
        assert result is not None
        if isinstance(result, dict):
            # Config was healed
            assert "data_source" in result  # Source requires this
        else:
            # Config couldn't be healed - should have clear error
            assert "error" in str(result).lower()
    
    def test_blueprint_structure_consistency(self):
        """Ensure blueprint structure is consistent across different generation paths"""
        # Path 1: Direct intermediate to blueprint
        intermediate = IntermediateSystem(
            name="consistency_test",
            description="Test",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="comp1",
                    type="Source",
                    description="Component 1",
                    inputs=[],
                    outputs=[IntermediatePort(name="out", schema_type="object")],
                    config={"key": "value"}
                )
            ],
            bindings=[]
        )
        
        translator = IntermediateToBlueprintTranslator()
        blueprint1 = translator._build_blueprint_dict(intermediate)
        
        # Path 2: Using translate method (which adds YAML conversion)
        yaml_str = translator.translate(intermediate)
        # Parse YAML back to dict
        import yaml
        blueprint2 = yaml.safe_load(yaml_str)
        
        # Both should have same structure
        assert "system" in blueprint1
        assert "system" in blueprint2
        assert "components" in blueprint1["system"]
        assert "components" in blueprint2["system"]
        
        # Component details should match
        assert blueprint1["system"]["components"][0]["name"] == blueprint2["system"]["components"][0]["name"]
        assert blueprint1["system"]["components"][0]["type"] == blueprint2["system"]["components"][0]["type"]
    
    def test_connections_become_bindings(self):
        """Test that connections in generated systems become bindings in blueprints"""
        # When we generate from NL, we often use "connections"
        # But IntermediateToBlueprintTranslator uses "bindings"
        
        intermediate = IntermediateSystem(
            name="connection_test",
            description="Test connections",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="a",
                    type="Source",
                    description="Component A",
                    inputs=[],
                    outputs=[IntermediatePort(name="out", schema_type="object")],
                    config={}
                ),
                IntermediateComponent(
                    name="b",
                    type="Sink",
                    description="Component B",
                    inputs=[IntermediatePort(name="in", schema_type="object")],
                    outputs=[],
                    config={}
                )
            ],
            bindings=[
                IntermediateBinding(
                    from_component="a",
                    from_port="out",
                    to_component="b",
                    to_port="in"
                )
            ]
        )
        
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # Should have bindings in the blueprint
        assert "bindings" in blueprint["system"]
        assert len(blueprint["system"]["bindings"]) == 1
        
        binding = blueprint["system"]["bindings"][0]
        assert binding["from"]["component"] == "a"
        assert binding["from"]["port"] == "out"
        assert binding["to"]["component"] == "b"
        assert binding["to"]["port"] == "in"


class TestEndToEndGeneration:
    """Test complete end-to-end generation scenarios"""
    
    def test_csv_to_s3_pipeline(self):
        """Test generating a CSV to S3 pipeline"""
        # This mimics what happens when user runs:
        # autocoder generate "Build a data pipeline that reads CSV files..."
        
        # Step 1: Create intermediate representation
        intermediate = IntermediateSystem(
            name="csv_to_s3_pipeline",
            description="Pipeline to process CSV files and upload to S3",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="csv_file_source",
                    type="Source",
                    description="Read CSV files from directory",
                    inputs=[],
                    outputs=[IntermediatePort(name="output", schema_type="object", description="CSV records")],
                    config={
                        "directory": "/data/input",
                        "pattern": "*.csv"
                    }
                ),
                IntermediateComponent(
                    name="status_filter",
                    type="Transformer", 
                    description="Filter records by status",
                    inputs=[IntermediatePort(name="input", schema_type="object")],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={
                        "filter_field": "status",
                        "filter_value": "active"
                    }
                ),
                IntermediateComponent(
                    name="s3_writer",
                    type="Sink",
                    description="Write filtered data to S3",
                    inputs=[IntermediatePort(name="input", schema_type="object")],
                    outputs=[],
                    config={
                        "bucket": "processed-data",
                        "prefix": "filtered/",
                        "format": "parquet"
                    }
                )
            ],
            bindings=[
                IntermediateBinding(
                    from_component="csv_file_source",
                    from_port="output",
                    to_component="status_filter",
                    to_port="input"
                ),
                IntermediateBinding(
                    from_component="status_filter",
                    from_port="output",
                    to_component="s3_writer",
                    to_port="input"
                )
            ]
        )
        
        # Step 2: Convert to blueprint
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # Step 3: Validate blueprint structure
        assert blueprint["system"]["name"] == "csv_to_s3_pipeline"
        assert len(blueprint["system"]["components"]) == 3
        assert len(blueprint["system"]["bindings"]) == 2
        
        # Step 4: Validate each component can be found
        context_builder = PipelineContextBuilder()
        
        # Should be able to build context for each component
        for component in blueprint["system"]["components"]:
            context = context_builder.build_from_blueprint(blueprint, component["name"])
            assert context.component_name == component["name"]
            assert context.component_type == component["type"]
        
        # Step 5: Validate relationships are correct
        csv_context = context_builder.build_from_blueprint(blueprint, "csv_file_source")
        assert len(csv_context.downstream_components) == 1
        assert csv_context.downstream_components[0]["name"] == "status_filter"
        
        filter_context = context_builder.build_from_blueprint(blueprint, "status_filter")
        assert len(filter_context.upstream_components) == 1
        assert filter_context.upstream_components[0]["name"] == "csv_file_source"
        assert len(filter_context.downstream_components) == 1
        assert filter_context.downstream_components[0]["name"] == "s3_writer"
        
        s3_context = context_builder.build_from_blueprint(blueprint, "s3_writer")
        assert len(s3_context.upstream_components) == 1
        assert s3_context.upstream_components[0]["name"] == "status_filter"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])