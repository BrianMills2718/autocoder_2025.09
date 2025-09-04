import pytest
import asyncio
from autocoder_cc.validation.pipeline_integration import StrictValidationPipeline
from autocoder_cc.validation.exceptions import ValidationException
from tests.contracts.blueprint_structure_contract import BlueprintContract, BlueprintTestFixture

@pytest.mark.asyncio
async def test_already_valid_config_passes():
    """Valid configs pass through unchanged"""
    pipeline = StrictValidationPipeline()
    
    blueprint = {
        "system": {
            "name": "test_system",
            "components": [
                {"name": "store1", "type": "Store", "config": {"database_url": "postgresql://localhost/db"}}
            ]
        }
    }
    
    result = await pipeline.validate_and_heal_or_fail(
        "store1", "Store", 
        {"database_url": "postgresql://localhost/db"},
        blueprint
    )
    
    assert result["database_url"] == "postgresql://localhost/db"

@pytest.mark.asyncio
async def test_healable_config_gets_healed():
    """Configs with defaults/examples get healed"""
    pipeline = StrictValidationPipeline()
    
    blueprint = {
        "system": {
            "name": "test_system",
            "components": [
                {"name": "api1", "type": "APIEndpoint", "config": {}}
            ]
        }
    }
    
    # Assuming APIEndpoint has port with default 8080
    result = await pipeline.validate_and_heal_or_fail(
        "api1", "APIEndpoint", {}, blueprint
    )
    
    assert "port" in result  # Should be healed

@pytest.mark.asyncio
async def test_unhealable_config_fails_clearly():
    """Unhealable configs fail with clear errors"""
    pipeline = StrictValidationPipeline()
    
    # Disable all healing strategies to force failure
    # This simulates a field that has no default, no example, and no LLM
    pipeline.healer.strategies = []  # Remove all strategies
    pipeline.healer.model = None  # Also disable LLM
    
    blueprint = {
        "system": {
            "name": "test_system",
            "components": [
                {"name": "source1", "type": "Source", "config": {}}
            ]
        }
    }
    
    with pytest.raises(ValidationException) as exc_info:
        await pipeline.validate_and_heal_or_fail(
            "source1", "Source", {}, blueprint
        )
    
    error_msg = str(exc_info.value)
    assert "Cannot heal configuration" in error_msg
    assert "Action Required" in error_msg  # Should provide guidance

@pytest.mark.asyncio
async def test_partial_healing_not_allowed():
    """Partial healing should fail - all or nothing"""
    pipeline = StrictValidationPipeline()
    
    # This test ensures that if healing can't fix ALL issues,
    # it fails rather than returning partial fixes
    # Implementation depends on component requirements
    pass  # TODO: Implement based on actual components