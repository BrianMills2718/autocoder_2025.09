#!/usr/bin/env python3
"""
TDD Tests for Component Generation Module Extraction

Tests for extracting component generation logic from the monolithic system_generator.py
into clean, modular components with proper dependency injection.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from autocoder_cc.generation.component_generator import ComponentGenerator
from autocoder_cc.generation.template_engine import TemplateEngine
from autocoder_cc.blueprint_language.system_blueprint_parser import (
    ParsedSystemBlueprint, ParsedComponent, ParsedSystem
)


class TestComponentGenerator:
    """Test ComponentGenerator extraction from monolith"""
    
    def test_component_generator_initialization(self):
        """RED: Test that ComponentGenerator can be initialized"""
        # This should fail initially because ComponentGenerator doesn't exist
        prompt_manager = Mock()
        llm_provider = Mock()
        template_engine = Mock()
        
        generator = ComponentGenerator(
            prompt_manager=prompt_manager,
            llm_provider=llm_provider,
            template_engine=template_engine
        )
        
        assert generator is not None
        assert generator.prompt_manager == prompt_manager
        assert generator.llm_provider == llm_provider
        assert generator.template_engine == template_engine
    
    def test_generate_component_basic(self):
        """RED: Test basic component generation"""
        mock_template_engine = Mock()
        mock_template_engine.render.return_value = """
import asyncio
from typing import Dict, Any
from datetime import datetime
from autocoder_cc.components.processor import Processor

class DataProcessor(Processor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.batch_size = config.get('batch_size', 100)
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Business logic to process data
        processed = {
            'timestamp': datetime.now().isoformat(),
            'original_size': len(str(data)),
            'processed': True
        }
        return processed
    
    async def initialize(self):
        await super().initialize()
        self.logger.info("DataProcessor initialized")
    
    async def cleanup(self):
        await super().cleanup()
        self.logger.info("DataProcessor cleaned up")
"""
        
        generator = ComponentGenerator(Mock(), Mock(), mock_template_engine)
        
        component_spec = ParsedComponent(
            name="DataProcessor",
            type="Processor",
            description="Processes incoming data",
            config={"batch_size": 100}
        )
        
        blueprint_context = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="TestSystem",
                description="Test system for validation",
                version="1.0.0",
                components=[component_spec],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        # Generate component
        generated = generator.generate_component(component_spec, blueprint_context)
        
        # Verify structure
        assert generated.name == "DataProcessor"
        assert generated.type == "Processor"
        assert generated.implementation is not None
        assert len(generated.implementation) > 0
        assert "class DataProcessor" in generated.implementation
    
    def test_llm_integration_for_business_logic(self):
        """RED: Test that LLM is used for business logic generation"""
        mock_llm = Mock()
        mock_llm.generate.return_value = """
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Business logic to process data
        processed = {
            'timestamp': datetime.now().isoformat(),
            'original_size': len(str(data)),
            'processed': True
        }
        return processed
"""
        
        generator = ComponentGenerator(Mock(), mock_llm, Mock())
        
        component_spec = ParsedComponent(
            name="DataProcessor",
            type="Processor",
            description="Processes data by adding metadata",
            config={}
        )
        
        # Generate business logic only
        business_logic = generator.generate_business_logic(component_spec)
        
        assert "async def process" in business_logic
        assert "processed" in business_logic
        assert mock_llm.generate.called
    
    def test_template_assembly_with_business_logic(self):
        """RED: Test assembling template with LLM-generated business logic"""
        # Set up mock to replace the placeholder when called
        def mock_render(context):
            template = """
import asyncio
from typing import Dict, Any
from datetime import datetime
from autocoder_cc.components.processor import Processor

class DataProcessor(Processor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.batch_size = config.get('batch_size', 100)
    
    {business_logic}
    
    async def initialize(self):
        await super().initialize()
        self.logger.info("DataProcessor initialized")
    
    async def cleanup(self):
        await super().cleanup()
        self.logger.info("DataProcessor cleaned up")
"""
            # Replace placeholder with actual business logic
            return template.replace("{business_logic}", context.get("business_logic", ""))
            
        mock_template_engine = Mock()
        mock_template_engine.render.side_effect = mock_render
        
        generator = ComponentGenerator(Mock(), Mock(), mock_template_engine)
        
        business_logic = """
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        processed = {'result': data.get('value', 0) * 2}
        return processed
"""
        
        component_spec = ParsedComponent(
            name="DataProcessor",
            type="Processor",
            config={"batch_size": 50}
        )
        
        # Assemble full component
        full_component = generator.assemble_component(
            component_spec,
            business_logic
        )
        
        assert "class DataProcessor(Processor):" in full_component
        assert "async def process" in full_component
        assert "processed = {'result':" in full_component
        assert "batch_size = config.get('batch_size', 100)" in full_component
    
    def test_multiple_component_types(self):
        """RED: Test generation of different component types"""
        # Mock template engine to return proper implementations
        mock_template_engine = Mock()
        
        def generate_component_code(context):
            comp_type = context.get("component_type")
            comp_name = context.get("component_name")
            
            base_templates = {
                "Store": f"""class {comp_name}(Store):
    async def store(self, key: str, value: Any): pass
    async def retrieve(self, key: str): pass""",
                "Source": f"""class {comp_name}(Source):
    async def generate(self): pass""",
                "Sink": f"""class {comp_name}(Sink):
    async def consume(self, data): pass""",
                "APIEndpoint": f"""class {comp_name}(APIEndpoint):
    async def handle_request(self, request): pass""",
                "Router": f"""class {comp_name}(Router):
    async def route(self, message): pass"""
            }
            return base_templates.get(comp_type, f"class {comp_name}(Component): pass")
        
        mock_template_engine.render.side_effect = generate_component_code
        
        generator = ComponentGenerator(Mock(), Mock(), mock_template_engine)
        
        component_types = [
            ("Store", "CustomerStore", "async def store", "async def retrieve"),
            ("Source", "DataSource", "async def generate", None),
            ("Sink", "DataSink", "async def consume", None),
            ("APIEndpoint", "UserAPI", "async def handle_request", None),
            ("Router", "MessageRouter", "async def route", None)
        ]
        
        for comp_type, comp_name, required_method, optional_method in component_types:
            component_spec = ParsedComponent(
                name=comp_name,
                type=comp_type,
                config={}
            )
            
            generated = generator.generate_component(component_spec, Mock())
            
            assert f"class {comp_name}" in generated.implementation
            assert required_method in generated.implementation
            if optional_method:
                assert optional_method in generated.implementation
    
    def test_error_handling_and_logging(self):
        """RED: Test that generated components include error handling"""
        mock_template_engine = Mock()
        mock_template_engine.render.return_value = """
import logging

class ResilientProcessor(Processor):
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.retry_count = config.get('retry_count', 3)
        
    async def process(self, data):
        try:
            # Process data
            result = await self._do_process(data)
            return result
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            raise
"""
        
        generator = ComponentGenerator(Mock(), Mock(), mock_template_engine)
        
        component_spec = ParsedComponent(
            name="ResilientProcessor",
            type="Processor",
            description="Processor with error handling",
            config={"retry_count": 3}
        )
        
        generated = generator.generate_component(component_spec, Mock())
        
        # Check for error handling patterns
        assert "try:" in generated.implementation
        assert "except" in generated.implementation
        assert "logger" in generated.implementation or "self.logger" in generated.implementation
        assert "retry" in generated.implementation.lower() or "error" in generated.implementation.lower()
    
    def test_dependency_injection_support(self):
        """RED: Test that generator supports dependency injection"""
        # Mock dependencies
        mock_validator = Mock()
        mock_healer = Mock()
        
        generator = ComponentGenerator(
            prompt_manager=Mock(),
            llm_provider=Mock(),
            template_engine=Mock(),
            validator=mock_validator,
            healer=mock_healer
        )
        
        assert generator.validator == mock_validator
        assert generator.healer == mock_healer
        
        # Test validation during generation
        component_spec = ParsedComponent(name="TestComp", type="Processor")
        mock_validator.validate.return_value = {"valid": True, "errors": []}
        
        generated = generator.generate_component(component_spec, Mock())
        
        assert mock_validator.validate.called
    
    def test_component_with_complex_configuration(self):
        """RED: Test generation with complex configuration"""
        mock_template_engine = Mock()
        
        def render_with_config(context):
            config = context.get("config_fields", {})
            config_lines = []
            
            # Handle nested configuration
            if "database" in config:
                config_lines.append("        self.database = config.get('database', {})")
                config_lines.append("        self.db_host = self.database.get('host', 'localhost')")
            if "cache" in config:
                config_lines.append("        self.cache = config.get('cache', {})")
                config_lines.append("        self.cache_ttl = self.cache.get('ttl', 300)")
            if "retry_policy" in config:
                config_lines.append("        self.retry_policy = config.get('retry_policy', {})")
                
            config_init = '\n'.join(config_lines)
            
            return f"""
class ComplexStore(Store):
    def __init__(self, config):
        super().__init__(config)
{config_init}
"""
        
        mock_template_engine.render.side_effect = render_with_config
        
        generator = ComponentGenerator(Mock(), Mock(), mock_template_engine)
        
        component_spec = ParsedComponent(
            name="ComplexStore",
            type="Store",
            config={
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "test_db"
                },
                "cache": {
                    "enabled": True,
                    "ttl": 300
                },
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff": "exponential"
                }
            }
        )
        
        generated = generator.generate_component(component_spec, Mock())
        
        # Verify configuration is properly handled
        assert "database" in generated.implementation
        assert "cache" in generated.implementation
        assert "retry_policy" in generated.implementation
        assert "host" in generated.implementation
        assert "ttl" in generated.implementation


class TestTemplateEngine:
    """Test TemplateEngine for component assembly"""
    
    def test_template_engine_initialization(self):
        """RED: Test TemplateEngine initialization"""
        template_dir = Path("/templates")
        engine = TemplateEngine(template_dir)
        
        assert engine is not None
        assert engine.template_dir == template_dir
    
    def test_render_component_template(self):
        """RED: Test rendering component templates"""
        engine = TemplateEngine(Path("/templates"))
        
        context = {
            "component_name": "DataProcessor",
            "component_type": "Processor",
            "base_class": "Processor",
            "imports": [
                "import asyncio",
                "from typing import Dict, Any",
                "from datetime import datetime"
            ],
            "config_fields": {
                "batch_size": 100,
                "timeout": 30
            },
            "business_logic": "async def process(self, data): return data"
        }
        
        rendered = engine.render_component(context)
        
        assert "class DataProcessor(Processor):" in rendered
        assert "import asyncio" in rendered
        assert "batch_size" in rendered
        assert "async def process(self, data): return data" in rendered
    
    def test_template_caching(self):
        """RED: Test that templates are cached for performance"""
        engine = TemplateEngine(Path("/templates"))
        
        # Test the caching mechanism by checking if the same template name
        # results in using the cache
        
        # Mock a template in the cache
        from unittest.mock import MagicMock
        mock_template = MagicMock()
        mock_template.render.return_value = "Cached template output"
        
        # Add to cache
        engine._template_cache["test_template.jinja2"] = mock_template
        
        # Verify it's cached
        assert engine.is_cached("test_template")
        
        # Test that cached template is used
        cached_template = engine._get_template("test_template.jinja2")
        assert cached_template == mock_template
    
    def test_custom_template_functions(self):
        """RED: Test custom template functions for code generation"""
        engine = TemplateEngine(Path("/templates"))
        
        # Register custom functions
        engine.register_function("to_snake_case", lambda s: s.lower().replace(" ", "_"))
        engine.register_function("to_class_name", lambda s: "".join(w.capitalize() for w in s.split()))
        
        context = {
            "raw_name": "user data processor",
            "component_type": "Processor"
        }
        
        rendered = engine.render_with_functions("component_base", context)
        
        # Custom functions should be applied
        assert "user_data_processor" in rendered  # snake_case
        assert "UserDataProcessor" in rendered    # ClassName