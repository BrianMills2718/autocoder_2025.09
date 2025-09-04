#!/usr/bin/env python3
"""
Component Generation Module - Extracted from system_generator.py monolith

Responsible for generating component code using LLM integration and template assembly.
This module handles ~650 lines of component generation logic previously embedded
in the monolithic system_generator.py file.
"""
import ast
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.blueprint_language.system_blueprint_parser import (
    ParsedSystemBlueprint, ParsedComponent
)
from autocoder_cc.core.module_interfaces import (
    IPromptManager,
    ILLMProvider,
    ITemplateEngine,
    IValidationHealer,
    GenerationResult
)


@dataclass
class GeneratedComponent:
    """Generated component implementation with metadata"""
    name: str
    type: str
    implementation: str
    imports: List[str]
    dependencies: List[str]
    file_path: Optional[str] = None


class ComponentGenerator:
    """
    Generates component implementations using LLM for business logic
    and templates for boilerplate structure.
    
    Key Responsibilities:
    - LLM integration for business logic generation
    - Template-based code assembly
    - Component validation and healing
    - Configuration integration
    """
    
    def __init__(
        self,
        prompt_manager: IPromptManager,
        llm_provider: ILLMProvider,
        template_engine: ITemplateEngine,
        validator: Optional[Any] = None,
        healer: Optional[IValidationHealer] = None
    ):
        """
        Initialize ComponentGenerator with strict dependency injection.
        
        Args:
            prompt_manager: Manages prompts for LLM generation
            llm_provider: LLM service for business logic generation
            template_engine: Template system for code assembly
            validator: Optional component validator
            healer: Optional component healer
        """
        # Require core dependencies
        if prompt_manager is None:
            raise ValueError("PromptManager must be provided via dependency injection")
        if llm_provider is None:
            raise ValueError("LLMProvider must be provided via dependency injection")
        if template_engine is None:
            raise ValueError("TemplateEngine must be provided via dependency injection")
            
        self.prompt_manager = prompt_manager
        self.llm_provider = llm_provider
        self.template_engine = template_engine
        self.validator = validator
        self.healer = healer
        
        # Initialize observability
        self.logger = get_logger("component_generator", component="ComponentGenerator")
        self.metrics = get_metrics_collector("component_generator")
        self.tracer = get_tracer("component_generator")
        
        self.logger.info("ComponentGenerator initialized with dependencies")
    
    def generate_component(
        self,
        component_spec: ParsedComponent,
        blueprint_context: ParsedSystemBlueprint
    ) -> GeneratedComponent:
        """
        Generate a complete component implementation.
        
        Args:
            component_spec: Component specification from blueprint
            blueprint_context: Full system blueprint for context
            
        Returns:
            GeneratedComponent with full implementation
        """
        with self.tracer.span("generate_component", tags={"component": component_spec.name, "type": component_spec.type}):
            self.logger.info(f"Generating component: {component_spec.name} ({component_spec.type})")
            
            # Generate business logic using LLM
            business_logic = self.generate_business_logic(component_spec)
            
            # Assemble full component with template
            implementation = self.assemble_component(component_spec, business_logic)
            
            # Validate if validator is available
            if self.validator:
                validation_result = self.validator.validate(implementation)
                if not validation_result.get("valid", False) and self.healer:
                    # Attempt to heal validation issues
                    implementation = self.healer.heal(implementation, validation_result)
            
            # Extract imports and dependencies
            imports = self._extract_imports(implementation)
            dependencies = self._extract_dependencies(implementation)
            
            generated = GeneratedComponent(
                name=component_spec.name,
                type=component_spec.type,
                implementation=implementation,
                imports=imports,
                dependencies=dependencies
            )
            
            # Record metric - use available method
            try:
                if hasattr(self.metrics, 'record_component_generated'):
                    self.metrics.record_component_generated(component_spec.type)
                elif hasattr(self.metrics, 'record_component_start'):
                    self.metrics.record_component_start()
            except:
                # Metrics are optional - don't fail on metric recording
                pass
            self.logger.info(f"Successfully generated component: {component_spec.name}")
            
            return generated
    
    def generate_business_logic(self, component_spec: ParsedComponent) -> str:
        """
        Generate business logic for component using LLM.
        
        Args:
            component_spec: Component specification
            
        Returns:
            Generated business logic code (methods only, no boilerplate)
        """
        self.logger.debug(f"Generating business logic for {component_spec.name}")
        
        # Get appropriate prompt for component type
        prompt = self._build_business_logic_prompt(component_spec)
        
        # Generate using LLM
        if hasattr(self.llm_provider, 'generate'):
            business_logic = self.llm_provider.generate(prompt)
        else:
            # For testing - generate minimal business logic
            business_logic = self._generate_minimal_business_logic(component_spec)
        
        return business_logic
    
    def assemble_component(
        self,
        component_spec: ParsedComponent,
        business_logic: str
    ) -> str:
        """
        Assemble full component by combining template with business logic.
        
        Args:
            component_spec: Component specification
            business_logic: LLM-generated business logic
            
        Returns:
            Complete component implementation
        """
        self.logger.debug(f"Assembling component {component_spec.name}")
        
        # Prepare template context
        context = {
            "component_name": component_spec.name,
            "component_type": component_spec.type,
            "base_class": self._get_base_class(component_spec.type),
            "imports": self._get_required_imports(component_spec.type),
            "config_fields": component_spec.config or {},
            "business_logic": business_logic,
            "description": component_spec.description or f"Generated {component_spec.type} component"
        }
        
        # Render template
        if hasattr(self.template_engine, 'render'):
            implementation = self.template_engine.render(context)
        else:
            # For testing - use basic template
            implementation = self._basic_component_template(context)
        
        return implementation
    
    def _build_business_logic_prompt(self, component_spec: ParsedComponent) -> str:
        """Build prompt for LLM business logic generation"""
        prompts = {
            "Store": f"""Generate the business logic methods for a Store component named {component_spec.name}.
Include async def store(self, key: str, value: Any) and async def retrieve(self, key: str) methods.
Configuration: {component_spec.config}
Description: {component_spec.description}""",
            
            "Processor": f"""Generate the business logic for a Processor component named {component_spec.name}.
Include async def process(self, data: Dict[str, Any]) -> Dict[str, Any] method.
Configuration: {component_spec.config}
Description: {component_spec.description}""",
            
            "Source": f"""Generate the business logic for a Source component named {component_spec.name}.
Include async def generate(self) -> Dict[str, Any] method.
Configuration: {component_spec.config}
Description: {component_spec.description}""",
            
            "Sink": f"""Generate the business logic for a Sink component named {component_spec.name}.
Include async def consume(self, data: Dict[str, Any]) method.
Configuration: {component_spec.config}
Description: {component_spec.description}""",
            
            "APIEndpoint": f"""Generate the business logic for an APIEndpoint component named {component_spec.name}.
Include async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any] method.
Configuration: {component_spec.config}
Description: {component_spec.description}""",
            
            "Router": f"""Generate the business logic for a Router component named {component_spec.name}.
Include async def route(self, message: Dict[str, Any]) -> str method.
Configuration: {component_spec.config}
Description: {component_spec.description}"""
        }
        
        return prompts.get(component_spec.type, f"Generate business logic for {component_spec.type} component")
    
    def _generate_minimal_business_logic(self, component_spec: ParsedComponent) -> str:
        """Generate minimal business logic for testing"""
        logic_templates = {
            "Store": """
    async def store(self, key: str, value: Any) -> None:
        \"\"\"Store a value with the given key\"\"\"
        try:
            # Business logic to persist data
            self._storage[key] = value
            self.logger.info(f"Stored value for key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to store value: {e}")
            raise
    
    async def retrieve(self, key: str) -> Any:
        \"\"\"Retrieve value for the given key\"\"\"
        try:
            value = self._storage.get(key)
            if value is None:
                raise KeyError(f"Key not found: {key}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to retrieve value: {e}")
            raise""",
            
            "Processor": """
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Process incoming data\"\"\"
        try:
            # Business logic to transform data
            processed = {
                'timestamp': datetime.now().isoformat(),
                'original_size': len(str(data)),
                'processed': True,
                'result': data.get('value', 0) * 2 if 'value' in data else data
            }
            return processed
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise""",
            
            "Source": """
    async def generate(self) -> Dict[str, Any]:
        \"\"\"Generate data\"\"\"
        try:
            # Business logic to produce data
            import random
            data = {
                'timestamp': datetime.now().isoformat(),
                'value': random.randint(1, 100),
                'source': self.name
            }
            return data
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise""",
            
            "Sink": """
    async def consume(self, data: Dict[str, Any]) -> None:
        \"\"\"Consume incoming data\"\"\"
        try:
            # Business logic to handle data
            self.logger.info(f"Consuming data: {data}")
            self._consumed_count += 1
        except Exception as e:
            self.logger.error(f"Consumption failed: {e}")
            raise""",
            
            "APIEndpoint": """
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Handle API request\"\"\"
        try:
            # Business logic for request handling
            method = request.get('method', 'GET')
            path = request.get('path', '/')
            
            response = {
                'status': 200,
                'body': {
                    'message': f'Handled {method} {path}',
                    'timestamp': datetime.now().isoformat()
                }
            }
            return response
        except Exception as e:
            self.logger.error(f"Request handling failed: {e}")
            return {'status': 500, 'body': {'error': str(e)}}""",
            
            "Router": """
    async def route(self, message: Dict[str, Any]) -> str:
        \"\"\"Route message to appropriate destination\"\"\"
        try:
            # Business logic for routing
            msg_type = message.get('type', 'default')
            routing_rules = self.config.get('routing_rules', {})
            
            destination = routing_rules.get(msg_type, 'default_queue')
            self.logger.info(f"Routing message type '{msg_type}' to '{destination}'")
            
            return destination
        except Exception as e:
            self.logger.error(f"Routing failed: {e}")
            raise"""
        }
        
        return logic_templates.get(component_spec.type, "    # TODO: Implement business logic")
    
    def _get_base_class(self, component_type: str) -> str:
        """Get base class for component type"""
        base_classes = {
            "Store": "Store",
            "Processor": "Processor", 
            "Source": "Source",
            "Sink": "Sink",
            "APIEndpoint": "APIEndpoint",
            "Router": "Router",
            "Model": "Model",
            "Accumulator": "Accumulator",
            "Controller": "Controller",
            "StreamProcessor": "StreamProcessor",
            "MessageBus": "MessageBus",
            "WebSocket": "WebSocket",
            "Aggregator": "Aggregator",
            "Filter": "Filter"
        }
        return base_classes.get(component_type, "Component")
    
    def _get_required_imports(self, component_type: str) -> List[str]:
        """Get required imports for component type"""
        base_imports = [
            "import asyncio",
            "import logging",
            "from typing import Dict, Any, Optional, List",
            "from datetime import datetime"
        ]
        
        type_specific = {
            "Store": ["from autocoder_cc.components.store import Store"],
            "Processor": ["from autocoder_cc.components.processor import Processor"],
            "Source": ["from autocoder_cc.components.source import Source"],
            "Sink": ["from autocoder_cc.components.sink import Sink"],
            "APIEndpoint": ["from autocoder_cc.components.api_endpoint import APIEndpoint"],
            "Router": ["from autocoder_cc.components.router import Router"]
        }
        
        return base_imports + type_specific.get(component_type, [])
    
    def _basic_component_template(self, context: Dict[str, Any]) -> str:
        """Basic component template for testing"""
        imports = "\n".join(context.get("imports", []))
        
        config_init = "\n".join([
            f"        self.{key} = config.get('{key}', {repr(value)})"
            for key, value in context.get("config_fields", {}).items()
        ])
        
        if context["component_type"] == "Store":
            config_init += "\n        self._storage = {}"
        elif context["component_type"] == "Sink":
            config_init += "\n        self._consumed_count = 0"
        
        template = f"""
{imports}

class {context['component_name']}({context['base_class']}):
    \"\"\"{context.get('description', 'Generated component')}\"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "{context['component_name']}"
        self.logger = logging.getLogger(self.name)
{config_init}
    
{context['business_logic']}
    
    async def initialize(self):
        \"\"\"Initialize component\"\"\"
        await super().initialize()
        self.logger.info(f"{{self.name}} initialized")
    
    async def cleanup(self):
        \"\"\"Cleanup component resources\"\"\"
        await super().cleanup()
        self.logger.info(f"{{self.name}} cleaned up")
"""
        return template.strip()
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code"""
        imports = []
        
        # Convert to string if needed (for mocking)
        if not isinstance(code, str):
            code = str(code)
            
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
        except:
            # Fallback to regex if AST parsing fails
            import re
            import_pattern = r'^(import\s+\S+|from\s+\S+\s+import\s+\S+)'
            try:
                imports = re.findall(import_pattern, code, re.MULTILINE)
            except:
                # If even regex fails, return empty list
                pass
        
        return imports
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract external dependencies from code"""
        dependencies = set()
        
        # Convert to string if needed (for mocking)
        if not isinstance(code, str):
            code = str(code)
        
        # Common dependencies based on imports
        dependency_map = {
            "asyncio": "asyncio",
            "aiohttp": "aiohttp",
            "fastapi": "fastapi",
            "pydantic": "pydantic",
            "sqlalchemy": "sqlalchemy",
            "redis": "redis",
            "kafka": "kafka-python",
            "psycopg": "psycopg2-binary",
            "pymongo": "pymongo"
        }
        
        for module, package in dependency_map.items():
            if module in code:
                dependencies.add(package)
        
        return list(dependencies)