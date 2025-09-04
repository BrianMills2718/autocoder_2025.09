#!/usr/bin/env python3
"""
Service Registry for AutoCoder4_CC Dependency Injection
Registers all core services to resolve circular imports.
"""

from autocoder_cc.core.dependency_injection import get_container
from autocoder_cc.interfaces.generators import (
    ComponentGeneratorProtocol,
    SystemGeneratorProtocol, 
    LLMComponentGeneratorProtocol,
    ValidationOrchestratorProtocol,
    HealingIntegrationProtocol
)
from autocoder_cc.interfaces.components import (
    ComponentRegistryProtocol,
    ComponentValidatorProtocol
)
from autocoder_cc.interfaces.config import ConfigProtocol
from autocoder_cc.observability.structured_logging import get_logger

logger = get_logger(__name__)

def register_core_services():
    """
    Register all core services for dependency injection.
    This eliminates circular imports by using lazy factory registration.
    """
    container = get_container()
    
    # Register Component Registry (singleton)
    def component_registry_factory():
        from autocoder_cc.components.component_registry import ComponentRegistry
        return ComponentRegistry()
    
    container.register_factory(
        ComponentRegistryProtocol, 
        component_registry_factory, 
        singleton=True
    )
    
    # Register LLM Component Generator (singleton - expensive to initialize)
    def llm_component_generator_factory():
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        return LLMComponentGenerator()
    
    container.register_factory(
        LLMComponentGeneratorProtocol,
        llm_component_generator_factory,
        singleton=True
    )
    
    # Register System Generator (singleton)
    def system_generator_factory():
        from autocoder_cc.blueprint_language import SystemGenerator
        from pathlib import Path
        return SystemGenerator(output_dir=Path("./generated_systems"))
    
    container.register_factory(
        SystemGeneratorProtocol,
        system_generator_factory,
        singleton=True
    )
    
    # Register Validation Orchestrator (singleton)
    def validation_orchestrator_factory():
        from autocoder_cc.blueprint_language.validation_driven_orchestrator import ValidationDrivenOrchestrator
        return ValidationDrivenOrchestrator()
    
    container.register_factory(
        ValidationOrchestratorProtocol,
        validation_orchestrator_factory,
        singleton=True
    )
    
    # Register Healing Integration (singleton)
    def healing_integration_factory():
        from autocoder_cc.blueprint_language.healing_integration import HealingIntegration
        return HealingIntegration()
    
    container.register_factory(
        HealingIntegrationProtocol,
        healing_integration_factory,
        singleton=True
    )
    
    # Register Configuration Service (singleton)
    def config_service_factory():
        from autocoder_cc.core.config import settings
        return settings
    
    container.register_factory(
        ConfigProtocol,
        config_service_factory,
        singleton=True
    )
    
    logger.info("✅ Core services registered for dependency injection")

def get_component_registry() -> ComponentRegistryProtocol:
    """Get the component registry service"""
    return get_container().get(ComponentRegistryProtocol)

def get_llm_component_generator() -> LLMComponentGeneratorProtocol:
    """Get the LLM component generator service"""
    return get_container().get(LLMComponentGeneratorProtocol)

def get_system_generator() -> SystemGeneratorProtocol:
    """Get the system generator service"""
    return get_container().get(SystemGeneratorProtocol)

def get_validation_orchestrator() -> ValidationOrchestratorProtocol:
    """Get the validation orchestrator service"""
    return get_container().get(ValidationOrchestratorProtocol)

def get_healing_integration() -> HealingIntegrationProtocol:
    """Get the healing integration service"""
    return get_container().get(HealingIntegrationProtocol)

def get_config_service() -> ConfigProtocol:
    """Get the configuration service"""
    return get_container().get(ConfigProtocol)

# Auto-register core services when this module is imported
register_core_services()