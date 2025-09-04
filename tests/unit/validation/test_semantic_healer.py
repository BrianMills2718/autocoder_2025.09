import pytest
import asyncio
from autocoder_cc.validation.semantic_healer import SemanticHealer
from autocoder_cc.validation.healing_strategies import DefaultValueStrategy, ExampleBasedStrategy
from autocoder_cc.validation.config_requirement import ConfigRequirement
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError
from autocoder_cc.validation.exceptions import HealingFailure

def test_default_value_strategy():
    """Test that DefaultValueStrategy uses default values correctly"""
    strategy = DefaultValueStrategy()
    
    error = ValidationError(
        component="test",
        field="pool_size",
        error_type="missing",
        message="Field missing"
    )
    
    requirement = ConfigRequirement(
        name="pool_size",
        type="int",
        required=False,
        default=10,
        description="Pool size"
    )
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system"
    )
    
    assert strategy.can_heal(error, requirement) == True
    assert strategy.heal(error, requirement, context) == 10

def test_example_based_strategy():
    """Test that ExampleBasedStrategy uses examples correctly"""
    strategy = ExampleBasedStrategy()
    
    error = ValidationError(
        component="test",
        field="database_url",
        error_type="missing",
        message="Field missing"
    )
    
    requirement = ConfigRequirement(
        name="database_url",
        type="str",
        required=True,
        example="postgresql://localhost/db",
        description="Database URL"
    )
    
    context = PipelineContext(
        system_name="test",
        system_description="Test system"
    )
    
    assert strategy.can_heal(error, requirement) == True
    assert strategy.heal(error, requirement, context) == "postgresql://localhost/db"

@pytest.mark.asyncio
async def test_semantic_healer_non_llm_strategies():
    """Test that SemanticHealer tries non-LLM strategies first"""
    healer = SemanticHealer()  # No validator, no LLM
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="store1",
        component_type="Store",
        existing_config={}
    )
    
    requirements = [
        ConfigRequirement(
            name="pool_size",
            type="int",
            required=False,
            default=20,
            description="Connection pool size"
        ),
        ConfigRequirement(
            name="timeout",
            type="int",
            required=False,
            example="30",
            description="Timeout in seconds"
        )
    ]
    
    errors = [
        ValidationError(
            component="store1",
            field="pool_size",
            error_type="missing",
            message="Field missing"
        ),
        ValidationError(
            component="store1",
            field="timeout",
            error_type="missing",
            message="Field missing"
        )
    ]
    
    healed = await healer.heal_configuration(context, requirements, errors)
    
    assert healed["pool_size"] == 20  # From default
    assert healed["timeout"] == 30  # From example (parsed as JSON)

@pytest.mark.asyncio
async def test_healing_cache():
    """Test that healing results are cached"""
    healer = SemanticHealer()
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="api1",
        component_type="APIEndpoint",
        existing_config={"host": "localhost"}
    )
    
    requirements = [
        ConfigRequirement(
            name="port",
            type="int",
            required=True,
            default=8080,
            description="Port number"
        )
    ]
    
    errors = [
        ValidationError(
            component="api1",
            field="port",
            error_type="missing",
            message="Field missing"
        )
    ]
    
    # First call - should heal
    result1 = await healer.heal_configuration(context, requirements, errors)
    assert result1["port"] == 8080
    
    # Generate cache key
    cache_key = healer._generate_cache_key(context, errors)
    assert cache_key in healer.healing_cache
    
    # Second call - should use cache
    result2 = await healer.heal_configuration(context, requirements, errors)
    assert result2 == result1

@pytest.mark.asyncio
async def test_healing_failure_no_strategy():
    """Test that HealingFailure is raised when no strategy can heal"""
    healer = SemanticHealer()
    healer.healing_cache.clear()  # Ensure cache is empty
    # Force no LLM to test non-LLM behavior
    healer.model = None
    
    context = PipelineContext(
        system_name="test_system",
        system_description="Test",
        component_name="store1",
        component_type="Store",
        existing_config={}
    )
    
    # Requirement with no default, no example, and no semantic_type that can be inferred
    requirements = [
        ConfigRequirement(
            name="database_url",
            type="str",
            required=True,
            description="Database URL",
            default=None,  # Explicitly no default
            example=None,  # Explicitly no example
            semantic_type=None  # Explicitly no semantic type
        )
    ]
    
    errors = [
        ValidationError(
            component="store1",
            field="database_url",
            error_type="missing",
            message="Required field missing"
        )
    ]
    
    # The healer should fail since no strategy can heal this
    with pytest.raises(HealingFailure) as exc_info:
        await healer.heal_configuration(context, requirements, errors)
    
    assert "Could not heal 1 errors" in str(exc_info.value)

def test_strategy_ordering():
    """Test that strategies are tried in the correct order"""
    healer = SemanticHealer()
    
    # Check strategy order
    assert isinstance(healer.strategies[0], DefaultValueStrategy)
    assert isinstance(healer.strategies[1], ExampleBasedStrategy)
    # ContextBasedStrategy is third
    assert len(healer.strategies) == 3