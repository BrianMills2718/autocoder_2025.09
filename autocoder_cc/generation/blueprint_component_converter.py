#!/usr/bin/env python3
"""
Blueprint to Generated Component Converter
Bridges the gap between blueprint ParsedComponent and test generation GeneratedComponent
"""

import re
from typing import Dict, Any, List, Type, Optional
from dataclasses import dataclass
from pydantic import BaseModel

from autocoder_cc.generation.nl_parser import ComponentType
from autocoder_cc.generation.schema_generator import GeneratedComponent
from autocoder_cc.blueprint_language.blueprint_parser import ParsedComponent
from autocoder_cc.observability.structured_logging import get_logger


class BlueprintConversionError(Exception):
    """Raised when blueprint component conversion fails - no fallbacks"""
    pass


class BlueprintToGeneratedComponentConverter:
    """
    Converts blueprint components to GeneratedComponent format for test generation
    
    Key Responsibilities:
    - Transform ParsedComponent → GeneratedComponent
    - Convert snake_case names to PascalCase class names
    - Map string component types to ComponentType enums
    - Generate placeholder schema classes (to be filled by LLM)
    - Extract dependencies and configuration
    """
    
    def __init__(self):
        self.logger = get_logger("BlueprintComponentConverter")
        
        # Component type mapping from blueprint strings to enums
        # Note: ComponentType enum only has SOURCE, TRANSFORMER, SINK
        # We'll map all types to these three categories
        self.type_mapping = {
            'APIEndpoint': ComponentType.SINK,        # API endpoints receive and respond (like sinks)
            'Source': ComponentType.SOURCE,           # Direct mapping
            'Transformer': ComponentType.TRANSFORMER, # Direct mapping
            'Store': ComponentType.TRANSFORMER,       # Stores transform data for persistence
            'Sink': ComponentType.SINK,              # Direct mapping
            'Controller': ComponentType.TRANSFORMER,  # Controllers transform control flow
            'StreamProcessor': ComponentType.TRANSFORMER, # Processors transform streams
            'Accumulator': ComponentType.TRANSFORMER, # Accumulators transform by aggregation
            'Model': ComponentType.TRANSFORMER        # Models transform input to predictions
        }
        
    def convert(self, blueprint_component: ParsedComponent) -> GeneratedComponent:
        """
        Convert a blueprint component to GeneratedComponent format
        
        Args:
            blueprint_component: ParsedComponent from blueprint parser
            
        Returns:
            GeneratedComponent ready for test generation
            
        Raises:
            BlueprintConversionError: If conversion fails with no fallback
        """
        try:
            # Convert component name to class name
            class_name = self._to_pascal_case(blueprint_component.name)
            
            # Map component type
            component_type = self._map_component_type(blueprint_component.type)
            
            # Extract description
            description = blueprint_component.description or f"{class_name} component"
            
            # Generate placeholder schemas (will be filled by LLM)
            schema_classes = self._create_placeholder_schemas(blueprint_component)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(blueprint_component)
            
            # Extract imports (empty for now, will be filled during generation)
            imports = []
            
            # Create GeneratedComponent using schema_generator's structure
            generated = GeneratedComponent(
                class_name=class_name,
                component_type=component_type,
                source_code="",  # Not needed for test generation
                schema_classes=schema_classes,
                config_template={},  # Will be filled from configuration
                validation_results={}  # Will be filled during validation
            )
            
            self.logger.info(f"✅ Converted {blueprint_component.name} → {class_name}")
            return generated
            
        except Exception as e:
            raise BlueprintConversionError(
                f"Failed to convert component {blueprint_component.name}: {str(e)}\n"
                f"Component type: {blueprint_component.type}\n"
                f"NO FALLBACKS - this indicates an architectural gap"
            )
    
    def _to_pascal_case(self, snake_case_name: str) -> str:
        """Convert snake_case to PascalCase"""
        # Handle special cases
        if not snake_case_name:
            raise ValueError("Component name cannot be empty")
            
        # Split by underscore and capitalize each part
        parts = snake_case_name.split('_')
        
        # Handle acronyms properly (API stays API, not Api)
        pascal_parts = []
        for part in parts:
            if part.upper() == part and len(part) > 1:
                # Already uppercase, likely an acronym
                pascal_parts.append(part)
            else:
                # Normal word, capitalize first letter
                pascal_parts.append(part.capitalize())
                
        return ''.join(pascal_parts)
    
    def _map_component_type(self, type_string: str) -> ComponentType:
        """Map blueprint component type string to ComponentType enum"""
        if type_string not in self.type_mapping:
            raise ValueError(
                f"Unknown component type: {type_string}\n"
                f"Available types: {list(self.type_mapping.keys())}"
            )
        
        return self.type_mapping[type_string]
    
    def _create_placeholder_schemas(self, component: ParsedComponent) -> Dict[str, Type[BaseModel]]:
        """
        Create placeholder schema classes for the component
        These will be filled with actual fields by the LLM schema generator
        """
        schemas = {}
        component_pascal = self._to_pascal_case(component.name)
        
        # All components need a config schema
        config_schema_name = f"{component_pascal}ConfigSchema"
        schemas[config_schema_name] = type(
            config_schema_name,
            (BaseModel,),
            {
                "__doc__": f"Configuration schema for {component_pascal}",
                "__module__": f"components.{component.name}"
            }
        )
        
        # Type-specific schemas
        if component.type == "APIEndpoint":
            # API endpoints need request and response schemas
            request_schema_name = f"{component_pascal}RequestSchema"
            schemas[request_schema_name] = type(
                request_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Request schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
            response_schema_name = f"{component_pascal}ResponseSchema"
            schemas[response_schema_name] = type(
                response_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Response schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
        elif component.type in ["Source", "Sink"]:
            # Sources output data, sinks input data
            data_schema_name = f"{component_pascal}DataSchema"
            schemas[data_schema_name] = type(
                data_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Data schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
        elif component.type == "Transformer":
            # Transformers have input and output schemas
            input_schema_name = f"{component_pascal}InputSchema"
            schemas[input_schema_name] = type(
                input_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Input schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
            output_schema_name = f"{component_pascal}OutputSchema"
            schemas[output_schema_name] = type(
                output_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Output schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
        elif component.type == "Store":
            # Stores have entity and query schemas
            entity_schema_name = f"{component_pascal}EntitySchema"
            schemas[entity_schema_name] = type(
                entity_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Entity schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
            
            query_schema_name = f"{component_pascal}QuerySchema"
            schemas[query_schema_name] = type(
                query_schema_name,
                (BaseModel,),
                {
                    "__doc__": f"Query schema for {component_pascal}",
                    "__module__": f"components.{component.name}"
                }
            )
        
        return schemas
    
    def _extract_dependencies(self, component: ParsedComponent) -> Dict[str, Any]:
        """Extract dependencies from blueprint component"""
        dependencies = {}
        
        # Check for explicit dependencies in the blueprint
        if hasattr(component, 'dependencies') and component.dependencies:
            dependencies.update(component.dependencies)
        
        # Extract dependencies from configuration
        if hasattr(component, 'config') and component.config:
            config = component.config
            
            # Database dependencies
            if 'database' in config:
                dependencies['database'] = config['database']
                
            # Redis dependencies
            if 'redis' in config or 'redis_url' in config:
                dependencies['redis'] = config.get('redis', config.get('redis_url'))
                
            # Message queue dependencies
            if 'kafka' in config or 'rabbitmq' in config:
                dependencies['message_queue'] = config
        
        # Extract from inputs/outputs (component connections)
        if hasattr(component, 'inputs') and component.inputs:
            dependencies['inputs'] = component.inputs
            
        if hasattr(component, 'outputs') and component.outputs:
            dependencies['outputs'] = component.outputs
        
        return dependencies