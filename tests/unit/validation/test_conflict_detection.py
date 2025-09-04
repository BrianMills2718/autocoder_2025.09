"""Test conflict detection in healing strategies"""
import pytest
from autocoder_cc.validation.healing_strategies import DefaultValueStrategy, ExampleBasedStrategy
from autocoder_cc.validation.config_requirement import ConfigRequirement
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError


def test_default_value_strategy_port_conflict():
    """Test that DefaultValueStrategy detects port conflicts"""
    strategy = DefaultValueStrategy()
    
    # Create context with used port
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "ports": {8080, 3000, 5000}  # Ports already in use
        }
    )
    
    # Create error for port field
    error = ValidationError(
        component="api_gateway",
        field="port",
        error_type="missing",
        message="Field missing"
    )
    
    # Requirement with default port that conflicts
    requirement = ConfigRequirement(
        name="port",
        type="int",
        required=True,
        default=8080,  # This conflicts with used resources
        description="API port"
    )
    
    # Should be able to heal
    assert strategy.can_heal(error, requirement) == True
    
    # But should return None due to conflict
    result = strategy.heal(error, requirement, context)
    assert result is None  # Conflict detected, trigger next strategy


def test_default_value_strategy_no_conflict():
    """Test that DefaultValueStrategy works when no conflict"""
    strategy = DefaultValueStrategy()
    
    # Create context with used ports
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "ports": {8080, 3000}
        }
    )
    
    # Requirement with non-conflicting default
    requirement = ConfigRequirement(
        name="port",
        type="int",
        required=True,
        default=5000,  # This doesn't conflict
        description="API port"
    )
    
    error = ValidationError(
        component="api_gateway",
        field="port",
        error_type="missing",
        message="Field missing"
    )
    
    # Should return the default value
    result = strategy.heal(error, requirement, context)
    assert result == 5000


def test_example_based_strategy_database_conflict():
    """Test that ExampleBasedStrategy detects database URL conflicts"""
    strategy = ExampleBasedStrategy()
    
    # Create context with used database URLs
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "database_urls": {"postgresql://localhost/main", "mysql://localhost/users"}
        }
    )
    
    # Requirement with example that conflicts
    requirement = ConfigRequirement(
        name="database_url",
        type="str",
        required=True,
        example="postgresql://localhost/main",  # Conflicts
        description="Database connection URL"
    )
    
    error = ValidationError(
        component="store",
        field="database_url",
        error_type="missing",
        message="Field missing"
    )
    
    # Should be able to heal
    assert strategy.can_heal(error, requirement) == True
    
    # But should return None due to conflict
    result = strategy.heal(error, requirement, context)
    assert result is None


def test_file_path_conflict_detection():
    """Test file path conflict detection"""
    strategy = DefaultValueStrategy()
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "file_paths": {"/data/input.csv", "/logs/app.log"}
        }
    )
    
    # Test conflicting file path
    requirement = ConfigRequirement(
        name="log_path",
        type="str",
        required=True,
        default="/logs/app.log",  # Conflicts
        description="Log file path"
    )
    
    error = ValidationError(
        component="logger",
        field="log_path",
        error_type="missing",
        message="Field missing"
    )
    
    result = strategy.heal(error, requirement, context)
    assert result is None  # Conflict detected


def test_api_path_conflict_detection():
    """Test API path conflict detection"""
    strategy = ExampleBasedStrategy()
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "api_paths": {"/api/v1", "/api/v2", "/health"}
        }
    )
    
    # Test conflicting API path
    requirement = ConfigRequirement(
        name="base_path",
        type="str",
        required=True,
        example='"/api/v1"',  # JSON-encoded string that conflicts
        description="API base path"
    )
    
    error = ValidationError(
        component="api_gateway",
        field="base_path",
        error_type="missing",
        message="Field missing"
    )
    
    result = strategy.heal(error, requirement, context)
    assert result is None  # Conflict detected


def test_queue_name_conflict_detection():
    """Test queue/topic name conflict detection"""
    strategy = DefaultValueStrategy()
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "queue_names": {"events", "commands"},
            "topic_names": {"notifications", "updates"}
        }
    )
    
    # Test conflicting queue name
    requirement_queue = ConfigRequirement(
        name="queue_name",
        type="str",
        required=True,
        default="events",  # Conflicts with queue
        description="Message queue name"
    )
    
    error_queue = ValidationError(
        component="processor",
        field="queue_name",
        error_type="missing",
        message="Field missing"
    )
    
    result = strategy.heal(error_queue, requirement_queue, context)
    assert result is None  # Conflict detected
    
    # Test conflicting topic name
    requirement_topic = ConfigRequirement(
        name="topic",
        type="str",
        required=True,
        default="notifications",  # Conflicts with topic
        description="Topic name"
    )
    
    error_topic = ValidationError(
        component="publisher",
        field="topic",
        error_type="missing",
        message="Field missing"
    )
    
    result = strategy.heal(error_topic, requirement_topic, context)
    assert result is None  # Conflict detected


def test_multiple_field_variants():
    """Test that all field name variants are checked"""
    strategy = DefaultValueStrategy()
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={
            "ports": {8080}
        }
    )
    
    # Test different port field names
    port_fields = ["port", "server_port", "listen_port", "bind_port"]
    
    for field_name in port_fields:
        requirement = ConfigRequirement(
            name=field_name,
            type="int",
            required=True,
            default=8080,  # Conflicts
            description="Port"
        )
        
        error = ValidationError(
            component="component",
            field=field_name,
            error_type="missing",
            message="Field missing"
        )
        
        result = strategy.heal(error, requirement, context)
        assert result is None, f"Conflict not detected for field '{field_name}'"


def test_empty_used_resources():
    """Test that strategies work when used_resources is empty"""
    strategy = DefaultValueStrategy()
    
    # Context with no used resources
    context = PipelineContext(
        system_name="test",
        system_description="Test system",
        used_resources={}  # Empty
    )
    
    requirement = ConfigRequirement(
        name="port",
        type="int",
        required=True,
        default=8080,
        description="Port"
    )
    
    error = ValidationError(
        component="api",
        field="port",
        error_type="missing",
        message="Field missing"
    )
    
    # Should work normally
    result = strategy.heal(error, requirement, context)
    assert result == 8080


def test_context_without_used_resources():
    """Test backwards compatibility when context doesn't have used_resources"""
    strategy = DefaultValueStrategy()
    
    # Old-style context without used_resources
    context = PipelineContext(
        system_name="test",
        system_description="Test system"
    )
    # Remove used_resources to simulate old context
    delattr(context, 'used_resources')
    
    requirement = ConfigRequirement(
        name="port",
        type="int",
        required=True,
        default=8080,
        description="Port"
    )
    
    error = ValidationError(
        component="api",
        field="port",
        error_type="missing",
        message="Field missing"
    )
    
    # Should work normally (no conflict checking)
    result = strategy.heal(error, requirement, context)
    assert result == 8080