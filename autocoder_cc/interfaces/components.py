#!/usr/bin/env python3
"""
Protocol interfaces for component services to resolve circular dependencies.
"""

from typing import Protocol, Dict, Any, List, Optional, Type
from abc import abstractmethod

class ComponentRegistryProtocol(Protocol):
    """Protocol for component registry services"""
    
    @abstractmethod
    def register_component(self, 
                          name: str, 
                          component_class: Type) -> None:
        """Register a component class"""
        ...
    
    @abstractmethod
    def get_component(self, name: str) -> Optional[Type]:
        """Get a component class by name"""
        ...
    
    @abstractmethod
    def list_components(self) -> Dict[str, Type]:
        """List all registered components"""
        ...

class ComponentValidatorProtocol(Protocol):
    """Protocol for component validation services"""
    
    @abstractmethod
    def validate_component(self, 
                          component_code: str, 
                          component_type: str) -> tuple[bool, List[str]]:
        """Validate component code"""
        ...
    
    @abstractmethod
    def get_validation_rules(self, component_type: str) -> List[str]:
        """Get validation rules for component type"""
        ...

class BaseComponentProtocol(Protocol):
    """Protocol for base component interface"""
    
    @abstractmethod
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """Setup the component"""
        ...
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup the component"""
        ...
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        ...