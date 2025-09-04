import pytest
from autocoder_cc.validation.config_validator import ConfigurationValidator
from autocoder_cc.validation.config_requirement import ConfigRequirement
from autocoder_cc.validation.pipeline_context import PipelineContext

def test_validation_behavior_with_defaults():
    """Diagnose how validator handles fields with defaults"""
    validator = ConfigurationValidator()
    context = PipelineContext(
        system_name="test",
        system_description="test",
        component_name="test_component"
    )
    
    # Test 1: Field with default, required=False (like APIEndpoint.port)
    req1 = ConfigRequirement(
        name="port",
        type="int",
        required=False,
        default=8080,
        description="Port number"
    )
    
    errors = validator.check_required_fields([req1], {}, context)
    assert len(errors) == 1, "Should report missing field with default"
    assert "port" in errors[0].field
    assert "8080" in str(errors[0].suggestion)
    
    # Test 2: Field required=True, no default (like Store.database_url)
    req2 = ConfigRequirement(
        name="database_url",
        type="str",
        required=True,
        default=None,
        description="Database URL"
    )
    
    errors = validator.check_required_fields([req2], {}, context)
    assert len(errors) == 1, "Should report missing required field"
    assert "database_url" in errors[0].field
    
    # Test 3: Field with example but no default, required=False
    req3 = ConfigRequirement(
        name="timeout",
        type="int",
        required=False,
        default=None,
        example="30",
        description="Timeout in seconds"
    )
    
    errors = validator.check_required_fields([req3], {}, context)
    assert len(errors) == 1, "Should report missing field with example"
    assert "timeout" in errors[0].field
    assert "30" in str(errors[0].suggestion)
    
    # Test 4: Field with neither default nor example, required=False
    req4 = ConfigRequirement(
        name="optional_field",
        type="str",
        required=False,
        default=None,
        example=None,
        description="Truly optional field"
    )
    
    errors = validator.check_required_fields([req4], {}, context)
    assert len(errors) == 0, "Should NOT report truly optional field"
    
    print("✅ All diagnostic tests passed!")