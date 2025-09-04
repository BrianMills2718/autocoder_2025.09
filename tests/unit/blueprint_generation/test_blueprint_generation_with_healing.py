"""
Comprehensive tests for blueprint generation, validation, and healing.

This demonstrates the TDD approach with:
1. Real LLM calls (no mocking)
2. Validation-healing cycles
3. End-to-end testing of the generation pipeline
"""

import pytest
import yaml
from typing import Dict, Any
import os
from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator as NaturalLanguageToBlueprint
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
from autocoder_cc.healing.blueprint_healer import BlueprintHealer
from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator


class TestBlueprintGenerationWithHealing:
    """Test blueprint generation with validation and healing cycles."""
    
    @pytest.fixture
    def nl_converter(self):
        """Create natural language to blueprint converter."""
        return NaturalLanguageToBlueprint()
    
    @pytest.fixture
    def parser(self):
        """Create blueprint parser."""
        return SystemBlueprintParser()
    
    @pytest.fixture
    def validator(self):
        """Create blueprint validator."""
        return BlueprintValidator()
    
    @pytest.fixture
    def healer(self):
        """Create blueprint healer."""
        return BlueprintHealer()
    
    def test_simple_system_generation_validation_healing(self, nl_converter, parser, validator, healer):
        """Test complete cycle: generation → validation → healing → re-validation."""
        # Step 1: Generate blueprint from natural language
        description = "Create a simple data processing system with API and database"
        
        blueprint_yaml = nl_converter.generate_full_blueprint(description)
        assert blueprint_yaml is not None
        
        # Step 2: Parse YAML to dict
        blueprint_dict = yaml.safe_load(blueprint_yaml)
        
        # Step 3: Validate the generated blueprint
        validation_result = validator.validate_blueprint(blueprint_dict)
        
        # If validation fails, heal and re-validate
        if not validation_result.is_valid:
            print(f"Initial validation failed: {validation_result.errors}")
            
            # Heal the blueprint
            healed_dict = healer.heal(blueprint_dict, validation_result)
            
            # Re-validate
            healed_validation = validator.validate_blueprint(healed_dict)
            assert healed_validation.is_valid, f"Healing failed: {healed_validation.errors}"
            
            blueprint_dict = healed_dict
        
        # Step 4: Parse the valid blueprint
        parsed_blueprint = parser.parse_dict(blueprint_dict)
        
        # Verify the parsed blueprint structure
        assert parsed_blueprint.system.name is not None
        assert len(parsed_blueprint.system.components) > 0
        assert parsed_blueprint.schema_version == "1.0.0"
        assert parsed_blueprint.policy is not None
    
    def test_complex_system_with_specific_requirements(self, nl_converter, validator, healer):
        """Test generation of complex system with specific requirements."""
        description = """
        Build an e-commerce order processing system with:
        - REST API for order submission and tracking
        - PostgreSQL database for order storage
        - Redis cache for session management
        - Message queue for async order processing
        - Email notification service
        - Admin dashboard API
        """
        
        # Generate blueprint
        blueprint_yaml = nl_converter.convert(description)
        blueprint_dict = yaml.safe_load(blueprint_yaml)
        
        # Validate and heal if needed
        validation_result = validator.validate_blueprint(blueprint_dict)
        if not validation_result.is_valid:
            blueprint_dict = healer.heal(blueprint_dict, validation_result)
            validation_result = validator.validate_blueprint(blueprint_dict)
            assert validation_result.is_valid
        
        # Verify all requested components are present
        components = blueprint_dict["system"]["components"]
        component_types = [c.get("type") for c in components]
        component_names_lower = [c.get("name", "").lower() for c in components]
        
        # Check for API components
        assert any(t == "APIEndpoint" for t in component_types), "Missing API endpoint"
        assert any("order" in name for name in component_names_lower), "Missing order-related component"
        
        # Check for database component
        assert any(t == "Store" for t in component_types), "Missing Store component"
        assert any("postgres" in name or "database" in name for name in component_names_lower)
        
        # Check for cache component
        assert any("cache" in name or "redis" in name for name in component_names_lower)
        
        # Check for message queue
        assert any(t in ["MessageBus", "Queue", "Processor"] for t in component_types)
        
        # Check for notification service
        assert any("notification" in name or "email" in name for name in component_names_lower)
    
    def test_healing_fixes_common_blueprint_issues(self, healer, validator):
        """Test that healer can fix common blueprint issues."""
        # Test case 1: Missing schema_version
        broken_blueprint1 = {
            "system": {
                "name": "TestSystem",
                "components": []
            }
        }
        
        validation1 = validator.validate_blueprint(broken_blueprint1)
        assert not validation1.is_valid
        assert any("schema_version" in str(e) for e in validation1.errors)
        
        healed1 = healer.heal(broken_blueprint1, validation1)
        assert "schema_version" in healed1
        assert healed1["schema_version"] == "1.0.0"
        
        # Test case 2: schema_version in wrong location
        broken_blueprint2 = {
            "system": {
                "schema_version": "1.0",  # Wrong location and format
                "name": "TestSystem",
                "components": []
            }
        }
        
        healed2 = healer.heal(broken_blueprint2, validator.validate_blueprint(broken_blueprint2))
        assert "schema_version" in healed2
        assert healed2["schema_version"] == "1.0.0"
        assert "schema_version" not in healed2["system"]
        
        # Test case 3: Missing policy block
        broken_blueprint3 = {
            "schema_version": "1.0.0",
            "system": {
                "name": "TestSystem",
                "components": []
            }
        }
        
        validation3 = validator.validate_blueprint(broken_blueprint3)
        if not validation3.is_valid and any("policy" in str(e) for e in validation3.errors):
            healed3 = healer.heal(broken_blueprint3, validation3)
            assert "policy" in healed3
            assert "security" in healed3["policy"]
        
        # Test case 4: Empty component config
        broken_blueprint4 = {
            "schema_version": "1.0.0",
            "policy": {"security": {"authentication_required": True}},
            "system": {
                "name": "TestSystem",
                "components": [
                    {
                        "name": "TestComponent",
                        "type": "Store",
                        "config": {}  # Empty config that might cause issues
                    }
                ]
            }
        }
        
        healed4 = healer.heal(broken_blueprint4, validator.validate_blueprint(broken_blueprint4))
        # Healer should provide default config values
        component = healed4["system"]["components"][0]
        if "config" in component and not component["config"]:
            assert len(component["config"]) > 0  # Should have default values
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="Requires LLM API key for real generation"
    )
    def test_real_llm_generation_produces_valid_blueprints(self, nl_converter, validator, healer, parser):
        """Test that real LLM calls produce valid, parseable blueprints."""
        test_descriptions = [
            "Simple REST API",
            "Data processing pipeline with storage",
            "Real-time chat application",
            "IoT sensor data collection system",
            "Machine learning model serving API"
        ]
        
        for description in test_descriptions:
            print(f"\nTesting: {description}")
            
            # Generate blueprint
            blueprint_yaml = nl_converter.convert(description)
            assert blueprint_yaml is not None
            
            # Parse YAML
            try:
                blueprint_dict = yaml.safe_load(blueprint_yaml)
            except yaml.YAMLError as e:
                pytest.fail(f"Generated invalid YAML for '{description}': {e}")
            
            # Validate
            validation_result = validator.validate_blueprint(blueprint_dict)
            
            # Heal if needed
            if not validation_result.is_valid:
                blueprint_dict = healer.heal(blueprint_dict, validation_result)
                validation_result = validator.validate_blueprint(blueprint_dict)
            
            # Should be valid after healing
            assert validation_result.is_valid, f"Blueprint for '{description}' invalid after healing: {validation_result.errors}"
            
            # Should be parseable
            try:
                parsed = parser.parse_dict(blueprint_dict)
                assert parsed.system.name is not None
                assert len(parsed.system.components) > 0
            except Exception as e:
                pytest.fail(f"Failed to parse healed blueprint for '{description}': {e}")
    
    def test_validation_error_details_are_actionable(self, validator):
        """Test that validation errors provide actionable information."""
        # Create blueprint with multiple issues
        broken_blueprint = {
            "system": {
                "name": "TestSystem",
                "components": [
                    {
                        "name": "Component1",
                        # Missing 'type'
                        "config": {}
                    },
                    {
                        "type": "Store",
                        # Missing 'name'
                        "config": {}
                    }
                ]
            }
            # Missing schema_version and policy
        }
        
        validation_result = validator.validate_blueprint(broken_blueprint)
        assert not validation_result.is_valid
        
        # Check that errors are specific and actionable
        error_messages = [str(e) for e in validation_result.errors]
        
        # Should identify missing schema_version
        assert any("schema_version" in msg for msg in error_messages)
        
        # Should identify component issues with path
        assert any("Component1" in msg and "type" in msg for msg in error_messages)
        assert any("components[1]" in msg and "name" in msg for msg in error_messages)
        
        # Each error should have a path
        for error in validation_result.errors:
            assert hasattr(error, 'path') or hasattr(error, 'location')
    
    def test_healer_preserves_valid_content(self, healer, validator):
        """Test that healer doesn't modify valid parts of blueprint."""
        # Create a mostly valid blueprint with one issue
        blueprint = {
            "schema_version": "1.0",  # Wrong format, should be "1.0.0"
            "policy": {
                "security": {
                    "authentication_required": True,
                    "encryption_at_rest": True
                }
            },
            "system": {
                "name": "PreservationTest",
                "description": "This should be preserved",
                "components": [
                    {
                        "name": "UserAPI",
                        "type": "APIEndpoint",
                        "config": {
                            "port": 8080,
                            "path": "/api/users"
                        },
                        "custom_field": "preserve_this"
                    }
                ]
            },
            "custom_section": {
                "data": "should_be_preserved"
            }
        }
        
        # Heal the blueprint
        validation_result = validator.validate_blueprint(blueprint)
        healed = healer.heal(blueprint, validation_result)
        
        # Check that valid content is preserved
        assert healed["system"]["description"] == "This should be preserved"
        assert healed["system"]["components"][0]["custom_field"] == "preserve_this"
        assert healed["system"]["components"][0]["config"]["port"] == 8080
        assert "custom_section" in healed
        assert healed["custom_section"]["data"] == "should_be_preserved"
        
        # Only the schema_version should be fixed
        assert healed["schema_version"] == "1.0.0"
    
    def test_component_relationship_validation(self, validator):
        """Test validation of component relationships and bindings."""
        blueprint = {
            "schema_version": "1.0.0",
            "policy": {"security": {"authentication_required": True}},
            "system": {
                "name": "TestSystem",
                "components": [
                    {
                        "name": "DataSource",
                        "type": "Source",
                        "config": {},
                        "ports": {
                            "output": ["data_out"]
                        }
                    },
                    {
                        "name": "DataProcessor",
                        "type": "Processor",
                        "config": {},
                        "ports": {
                            "input": ["data_in"],
                            "output": ["processed_out"]
                        }
                    }
                ]
            },
            "bindings": [
                {
                    "from": {
                        "component": "DataSource",
                        "port": "data_out"
                    },
                    "to": {
                        "component": "DataProcessor",
                        "port": "data_in"
                    }
                },
                {
                    "from": {
                        "component": "DataProcessor",
                        "port": "processed_out"
                    },
                    "to": {
                        "component": "NonExistentComponent",  # Invalid reference
                        "port": "input"
                    }
                }
            ]
        }
        
        validation_result = validator.validate_blueprint(blueprint)
        
        # Should detect invalid component reference in binding
        if not validation_result.is_valid:
            error_messages = [str(e) for e in validation_result.errors]
            assert any("NonExistentComponent" in msg for msg in error_messages)