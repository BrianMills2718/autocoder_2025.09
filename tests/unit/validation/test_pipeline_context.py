import pytest
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError, DataFlowPattern
from autocoder_cc.validation.context_builder import PipelineContextBuilder
from autocoder_cc.validation.exceptions import ContextBuildException
from tests.contracts.blueprint_structure_contract import BlueprintContract, BlueprintTestFixture

def test_validation_error_to_dict():
    """Test ValidationError serialization"""
    error = ValidationError(
        component="test_comp",
        field="database_url",
        error_type="missing",
        message="Required field missing",
        suggestion="Add database_url"
    )
    
    error_dict = error.to_dict()
    assert error_dict["component"] == "test_comp"
    assert error_dict["field"] == "database_url"

def test_pipeline_context_creation():
    """Test PipelineContext with proper field factories"""
    context = PipelineContext(
        system_name="test_system",
        system_description="Test description",
        component_name="processor",
        component_type="Transformer"
    )
    
    # Test mutable defaults work correctly
    context.upstream_components.append({"name": "source", "type": "Source"})
    
    # Create another context - should have empty list
    context2 = PipelineContext(
        system_name="test_system2",
        system_description="Test description 2"
    )
    assert len(context2.upstream_components) == 0  # Should be empty, not shared

def test_context_builder_from_blueprint():
    """Test building context from blueprint"""
    # Use BlueprintTestFixture to create proper nested structure
    blueprint = {
        "system": {
            "name": "test_system",
            "description": "Test system",
            "components": [
                {
                    "name": "source1",
                    "type": "Source",
                    "config": {"data_source": "file://data.json"},
                    "outputs": [{"name": "data", "schema": {}}]
                },
                {
                    "name": "transformer1",
                    "type": "Transformer",
                    "config": {},
                    "inputs": [{"component": "source1", "output": "data"}]
                }
            ],
            "connections": [
                {"from": "source1.data", "to": "transformer1.input"}
            ]
        }
    }
    
    builder = PipelineContextBuilder()
    context = builder.build_from_blueprint(blueprint, "transformer1")
    
    assert context.component_name == "transformer1"
    assert context.component_type == "Transformer"
    assert len(context.upstream_components) == 1
    assert context.upstream_components[0]["name"] == "source1"

def test_data_flow_pattern_detection():
    """Test data flow pattern identification"""
    builder = PipelineContextBuilder()
    
    # Test STREAM pattern - use nested structure
    blueprint = {
        "system": {
            "components": [
                {"name": "source", "type": "Source"},
                {"name": "transformer", "type": "Transformer"},
                {"name": "sink", "type": "Sink"}
            ]
        }
    }
    assert builder.analyze_data_flow(blueprint) == DataFlowPattern.STREAM
    
    # Test BATCH pattern - use nested structure
    blueprint = {
        "system": {
            "components": [
                {"name": "source", "type": "Source"},
                {"name": "accumulator", "type": "Accumulator"},
                {"name": "store", "type": "Store"}
            ]
        }
    }
    assert builder.analyze_data_flow(blueprint) == DataFlowPattern.BATCH

def test_context_to_prompt():
    """Test conversion to LLM prompt"""
    context = PipelineContext(
        system_name="data_pipeline",
        system_description="Customer data processing",
        component_name="enricher",
        component_type="Transformer",
        environment="production",
        deployment_target="kubernetes"
    )
    
    prompt = context.to_prompt_context()
    assert "System: data_pipeline" in prompt
    assert "Environment: production" in prompt
    assert "Deployment: kubernetes" in prompt