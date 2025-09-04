from autocoder_cc.observability.structured_logging import get_logger
"""
Component Logic Generator Factory - implements factory pattern.
Delegates component generation to specialized generators.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .api_endpoint_generator import APIEndpointGenerator
from .auth_endpoint_generator import AuthEndpointGenerator
from .data_transformer_generator import DataTransformerGenerator
# Removed dead CQRS generator imports
from .store_generator import StoreGenerator

# Note: Some generators referenced in GENERATOR_MAP may not exist yet
# This is part of the integration process to wire CQRS into main pipeline


class ComponentGeneratorFactory:
    """
    Factory for component generators following Enterprise Roadmap v2.
    
    Key principles:
    - Each component type has its own generator
    - No monolithic generation logic
    - Easy to extend with new component types
    - All generators use composition, not inheritance
    """
    
    # Map component types to their generators
    GENERATOR_MAP = {
        "APIEndpoint": APIEndpointGenerator,
        "AuthEndpoint": AuthEndpointGenerator,
        "Transformer": DataTransformerGenerator,
        "Store": StoreGenerator,
        
        # Note: These generators need to be created or properly imported
        # "Source": SourceGenerator,
        # "Sink": SinkGenerator,
        # "Controller": ControllerGenerator,
        # "StreamProcessor": StreamProcessorGenerator,
        # "Accumulator": AccumulatorGenerator,
    }
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._generators = {}
        
        # Initialize all generators
        for comp_type, generator_class in self.GENERATOR_MAP.items():
            self._generators[comp_type] = generator_class()
    
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """
        Generate component implementation based on type.
        
        Args:
            component_spec: Component specification with type, name, config
            
        Returns:
            Generated Python code for the component
            
        Raises:
            ValueError: If component type is unknown
        """
        comp_type = component_spec.get('type')
        comp_name = component_spec.get('name', 'unnamed')
        
        if not comp_type:
            raise ValueError(f"Component {comp_name} missing 'type' field")
        
        generator = self._generators.get(comp_type)
        
        if not generator:
            raise ValueError(
                f"Unknown component type: {comp_type}. "
                f"Available types: {list(self.GENERATOR_MAP.keys())}"
            )
        
        self.logger.info(f"Generating {comp_type} component: {comp_name}")
        
        try:
            return generator.generate(component_spec)
        except Exception as e:
            self.logger.error(f"Failed to generate {comp_type} {comp_name}: {e}")
            raise
    
    def register_generator(self, comp_type: str, generator_class: type):
        """
        Register a new component generator.
        
        Allows extending the factory with custom generators.
        
        Args:
            comp_type: Component type name
            generator_class: Generator class (must have generate method)
        """
        self.GENERATOR_MAP[comp_type] = generator_class
        self._generators[comp_type] = generator_class()
        self.logger.info(f"Registered new generator for type: {comp_type}")
    
    def list_supported_types(self) -> list:
        """Get list of supported component types."""
        return list(self.GENERATOR_MAP.keys())
    
    def has_generator(self, comp_type: str) -> bool:
        """Check if a generator exists for the given type."""
        return comp_type in self.GENERATOR_MAP