import pytest
from autocoder_cc.validation.config_validator import ConfigurationValidator
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError

def test_check_required_fields():
    """Test that required fields are properly validated"""
    validator = ConfigurationValidator()
    
    requirements = [
        ConfigRequirement(
            name="database_url",
            type="str",
            required=True,
            description="Database connection URL"
        ),
        ConfigRequirement(
            name="port",
            type="int",
            required=False,
            description="Port number"
        )
    ]
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="store1",
        component_type="Store"
    )
    
    # Missing required field
    config = {"port": 5432}
    errors = validator.check_required_fields(requirements, config, context)
    
    assert len(errors) == 1
    assert errors[0].field == "database_url"
    assert errors[0].error_type == "missing"

def test_validate_field_types():
    """Test type validation works correctly"""
    validator = ConfigurationValidator()
    
    requirements = [
        ConfigRequirement(
            name="port",
            type="int",
            required=True,
            description="Port number"
        ),
        ConfigRequirement(
            name="enabled",
            type="bool",
            required=True,
            description="Feature flag"
        )
    ]
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="api1",
        component_type="APIEndpoint"
    )
    
    # Wrong types
    config = {
        "port": "8080",  # Should be int
        "enabled": 1      # Should be bool
    }
    
    errors = validator.validate_field_types(requirements, config, context)
    
    assert len(errors) == 2
    assert any(e.field == "port" for e in errors)
    assert any(e.field == "enabled" for e in errors)

def test_conditional_requirements():
    """Test conditional requirement checking"""
    validator = ConfigurationValidator()
    
    requirements = [
        ConfigRequirement(
            name="use_ssl",
            type="bool",
            required=True,
            description="Use SSL",
            requires=["ssl_cert", "ssl_key"]  # These fields are required when use_ssl is present
        ),
        ConfigRequirement(
            name="ssl_cert",
            type="str",
            required=False,
            description="SSL certificate"
        ),
        ConfigRequirement(
            name="ssl_key",
            type="str",
            required=False,
            description="SSL key"
        )
    ]
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="api1",
        component_type="APIEndpoint"
    )
    
    # use_ssl present but missing required companions
    config = {
        "use_ssl": True
    }
    
    errors = validator.check_conditional_requirements(requirements, config, context)
    
    assert len(errors) == 2
    assert any(e.field == "ssl_cert" for e in errors)
    assert any(e.field == "ssl_key" for e in errors)

def test_custom_validators():
    """Test custom validator functions work"""
    validator = ConfigurationValidator()
    
    def validate_port(value):
        """Custom validator for port range"""
        return isinstance(value, int) and 1 <= value <= 65535
    
    requirements = [
        ConfigRequirement(
            name="port",
            type="int",
            required=True,
            description="Port number",
            validator=validate_port
        )
    ]
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="api1",
        component_type="APIEndpoint"
    )
    
    # Invalid port number
    config = {
        "port": 99999
    }
    
    errors = validator.run_custom_validators(requirements, config, context)
    
    assert len(errors) == 1
    assert errors[0].field == "port"
    assert errors[0].error_type == "invalid"

def test_full_validation():
    """Test complete validation flow"""
    validator = ConfigurationValidator()
    
    requirements = [
        ConfigRequirement(
            name="database_url",
            type="str",
            required=True,
            description="Database URL",
            example="postgresql://localhost/db"
        ),
        ConfigRequirement(
            name="pool_size",
            type="int",
            required=False,
            default=10,
            description="Connection pool size"
        )
    ]
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="store1",
        component_type="Store"
    )
    
    # Valid configuration
    valid_config = {
        "database_url": "postgresql://localhost/testdb",
        "pool_size": 20
    }
    
    errors = validator.validate_component_config(
        "Store", valid_config, context, requirements
    )
    
    assert len(errors) == 0
    
    # Invalid configuration
    invalid_config = {
        "pool_size": "twenty"  # Wrong type, missing required field
    }
    
    errors = validator.validate_component_config(
        "Store", invalid_config, context, requirements
    )
    
    assert len(errors) >= 2  # At least missing field and wrong type