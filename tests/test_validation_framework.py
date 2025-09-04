#!/usr/bin/env python3
"""
Test suite for validation framework with ConfigRequirement
"""

import pytest
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType
# SemanticHealer and PipelineContext will be implemented later
# from autocoder_cc.validation.semantic_healer import SemanticHealer
# from autocoder_cc.validation.pipeline_context import PipelineContext


class TestConfigRequirement:
    """Test ConfigRequirement dataclass"""
    
    def test_basic_requirement(self):
        """Test basic config requirement creation"""
        req = ConfigRequirement(
            name="database_url",
            type="str",
            description="Database connection string",
            required=True,
            semantic_type=ConfigType.DATABASE_URL
        )
        
        assert req.name == "database_url"
        assert req.required is True
        assert req.semantic_type == ConfigType.DATABASE_URL
    
    def test_optional_with_default(self):
        """Test optional requirement with default value"""
        req = ConfigRequirement(
            name="port",
            type="int",
            description="Server port",
            required=False,
            default=8080,
            semantic_type=ConfigType.NETWORK_PORT
        )
        
        assert req.required is False
        assert req.default == 8080
    
    def test_with_validator(self):
        """Test requirement with custom validator"""
        req = ConfigRequirement(
            name="batch_size",
            type="int",
            description="Batch size for processing",
            validator=lambda x: 0 < x <= 1000
        )
        
        # Test validator
        assert req.validator(100) is True
        assert req.validator(0) is False
        assert req.validator(1001) is False
    
    def test_with_options(self):
        """Test requirement with valid options"""
        req = ConfigRequirement(
            name="log_level",
            type="str",
            description="Logging level",
            options=["DEBUG", "INFO", "WARNING", "ERROR"]
        )
        
        assert "DEBUG" in req.options
        assert len(req.options) == 4
    
    def test_conditional_dependency(self):
        """Test conditional requirement with depends_on"""
        req = ConfigRequirement(
            name="ssl_cert",
            type="str",
            description="SSL certificate path",
            depends_on={"use_ssl": True}
        )
        
        assert req.depends_on == {"use_ssl": True}
    
    def test_conflicts_with(self):
        """Test requirement with conflicts"""
        req = ConfigRequirement(
            name="sqlite_path",
            type="str",
            description="SQLite database path",
            conflicts_with=["postgres_url", "mysql_url"]
        )
        
        assert "postgres_url" in req.conflicts_with
        assert len(req.conflicts_with) == 2


class TestComponentConfigRequirements:
    """Test that all components have ConfigRequirement definitions"""
    
    def test_all_components_have_requirements(self):
        """Test that all registered components have get_config_requirements"""
        from autocoder_cc.components.component_registry import component_registry
        
        # Get all registered component types
        component_types = component_registry.get_all_component_types()
        
        missing_requirements = []
        for comp_type in component_types:
            comp_class = component_registry.get_component_class(comp_type)
            if comp_class and not hasattr(comp_class, 'get_config_requirements'):
                missing_requirements.append(comp_type)
        
        # All components should have requirements
        assert len(missing_requirements) == 0, \
            f"Components missing get_config_requirements: {missing_requirements}"
    
    def test_source_requirements(self):
        """Test Source component requirements"""
        from autocoder_cc.components.source import Source
        
        if hasattr(Source, 'get_config_requirements'):
            reqs = Source.get_config_requirements()
            
            # Should have data_source requirement
            req_names = [r.name for r in reqs]
            assert "data_source" in req_names
            
            # Find data_source requirement
            data_source_req = next(r for r in reqs if r.name == "data_source")
            assert data_source_req.required is True
            assert data_source_req.semantic_type == ConfigType.CONNECTION_URL


# PipelineContext tests will be enabled once the module is implemented
# class TestPipelineContext:
#     """Test PipelineContext for validation"""
#     
#     def test_context_creation(self):
#         """Test creating pipeline context"""
#         context = PipelineContext(
#             system_name="test_system",
#             system_description="A test data pipeline",
#             component_name="data_processor",
#             component_type="Transformer",
#             upstream_components=["data_source"],
#             downstream_components=["data_sink"],
#             system_capabilities=["data_transformation", "filtering"],
#             data_flow_description="CSV data flows from source through transformer to sink"
#         )
#         
#         assert context.system_name == "test_system"
#         assert context.component_type == "Transformer"
#         assert "data_source" in context.upstream_components
#     
#     def test_context_to_dict(self):
#         """Test converting context to dictionary"""
#         context = PipelineContext(
#             system_name="test_system",
#             system_description="Test system",
#             component_name="processor",
#             component_type="Transformer"
#         )
#         
#         context_dict = context.to_dict()
#         assert context_dict["system_name"] == "test_system"
#         assert context_dict["component_name"] == "processor"
#         assert "upstream_components" in context_dict


class TestValidationIntegration:
    """Test validation framework integration"""
    
    def test_validate_component_config(self):
        """Test validating component configuration"""
        from autocoder_cc.components.store import Store
        
        if hasattr(Store, 'get_config_requirements'):
            reqs = Store.get_config_requirements()
            
            # Valid config
            valid_config = {
                "database_url": "postgresql://localhost/testdb",
                "table_name": "events"
            }
            
            # Check all required fields present
            required_fields = [r.name for r in reqs if r.required]
            for field in required_fields:
                assert field in valid_config, f"Missing required field: {field}"
    
    def test_semantic_type_validation(self):
        """Test semantic type understanding"""
        req = ConfigRequirement(
            name="kafka_broker",
            type="str",
            description="Kafka broker address",
            semantic_type=ConfigType.KAFKA_BROKER,
            example="localhost:9092"
        )
        
        # Semantic type should guide configuration
        assert req.semantic_type == ConfigType.KAFKA_BROKER
        assert "9092" in req.example  # Standard Kafka port


class TestValidationPipeline:
    """Test complete validation pipeline"""
    
    def test_requirement_with_all_features(self):
        """Test a complex requirement with all features"""
        req = ConfigRequirement(
            name="cache_config",
            type="dict",
            description="Cache configuration",
            required=False,
            default={"type": "memory", "size": 100},
            validator=lambda x: isinstance(x, dict) and "type" in x,
            example='{"type": "redis", "host": "localhost"}',
            semantic_type=ConfigType.DICT,
            depends_on={"use_cache": True},
            conflicts_with=["no_cache"],
            requires=["cache_ttl"],
            options=None
        )
        
        # Test all fields are set correctly
        assert req.name == "cache_config"
        assert req.required is False
        assert req.default["type"] == "memory"
        assert req.validator({"type": "redis"}) is True
        assert req.validator({}) is False
        assert req.depends_on == {"use_cache": True}
        assert "no_cache" in req.conflicts_with
        assert "cache_ttl" in req.requires


if __name__ == "__main__":
    pytest.main([__file__, "-v"])