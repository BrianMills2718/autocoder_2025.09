#!/usr/bin/env python3
"""
Protocol interfaces for generator services to resolve circular dependencies.
"""

from typing import Protocol, Dict, Any, List, Optional, Tuple
from abc import abstractmethod

class ComponentGeneratorProtocol(Protocol):
    """Protocol for component generation services"""
    
    @abstractmethod
    def generate_component(self, 
                          component_type: str, 
                          config: Dict[str, Any], 
                          system_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate component code"""
        ...
    
    @abstractmethod
    def validate_component(self, component_code: str) -> Tuple[bool, List[str]]:
        """Validate generated component code"""
        ...

class SystemGeneratorProtocol(Protocol):
    """Protocol for system generation services"""
    
    @abstractmethod
    def generate_system(self, 
                       blueprint: Dict[str, Any], 
                       output_path: str) -> Dict[str, Any]:
        """Generate complete system from blueprint"""
        ...
    
    @abstractmethod
    def validate_system(self, system_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate generated system configuration"""
        ...

class LLMComponentGeneratorProtocol(Protocol):
    """Protocol for LLM-based component generation"""
    
    @abstractmethod
    def generate_component_implementation(self,
                                        component_type: str,
                                        system_requirements: Dict[str, Any],
                                        context: Optional[Dict[str, Any]] = None) -> str:
        """Generate component implementation using LLM"""
        ...
    
    @abstractmethod
    def improve_with_feedback(self,
                            component_code: str,
                            feedback: List[str]) -> str:
        """Improve component code based on validation feedback"""
        ...

class ValidationOrchestratorProtocol(Protocol):
    """Protocol for validation orchestration services"""
    
    @abstractmethod
    def validate_component(self, 
                          component_code: str, 
                          component_type: str) -> Tuple[bool, List[str]]:
        """Orchestrate component validation"""
        ...
    
    @abstractmethod
    def validate_system(self, 
                       system_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Orchestrate system validation"""
        ...

class HealingIntegrationProtocol(Protocol):
    """Protocol for validation + self-healing integration"""
    
    @abstractmethod
    def validate_and_heal(self, 
                         component_code: str, 
                         component_type: str) -> Tuple[str, bool, List[str]]:
        """Validate component and attempt self-healing if needed"""
        ...
    
    @abstractmethod
    def heal_validation_failures(self, 
                                code: str, 
                                failures: List[str]) -> str:
        """Attempt to heal validation failures"""
        ...