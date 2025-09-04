#!/usr/bin/env python3
"""
Dependency Injection Configuration for Autocoder CC

Configures and registers all system modules with the enhanced
dependency injection container using interface-based registration.
"""
from typing import Dict, Any, Optional, Type
import logging
from pathlib import Path

from autocoder_cc.observability import get_logger
from autocoder_cc.core.dependency_container import EnhancedDependencyContainer
from autocoder_cc.core.module_interfaces import (
    IPipelineCoordinator,
    IBlueprintProcessor,
    IBlueprintValidator,
    IComponentGenerator,
    ITemplateEngine,
    IDeploymentManager,
    IEnvironmentProvisioner,
    IResourceOrchestrator,
    IPromptManager,
    ILLMProvider,
    IConfigManager,
    ISecretManager,
    ModuleRegistry
)


class SystemDependencyConfiguration:
    """
    Configures system-wide dependency injection using the enhanced container.
    
    Registers all modules with their proper interfaces and lifecycles.
    """
    
    def __init__(self):
        """Initialize dependency configuration"""
        self.logger = get_logger("dependency_configuration", component="SystemDependencyConfiguration")
        self.container = EnhancedDependencyContainer()
        
        self.logger.info(
            "SystemDependencyConfiguration initialized",
            operation="init"
        )
    
    def configure_standard_modules(self, output_dir: Path) -> None:
        """
        Configure and register all standard system modules.
        
        Args:
            output_dir: Output directory for generated systems
        """
        self.logger.info("Configuring standard system modules")
        
        # Register mock/external dependencies first
        self._register_external_dependencies()
        
        # Register core modules using ModuleRegistry
        ModuleRegistry.register_all_modules(self.container)
        
        # Configure additional modules
        self._configure_pipeline_dependencies(output_dir)
        
        # Validate all registrations
        errors = self.container.validate_registrations()
        if errors:
            self.logger.error(
                "Dependency validation failed",
                errors=errors
            )
            raise RuntimeError(f"Dependency validation failed: {errors}")
        
        self.logger.info(
            "Standard modules configured successfully",
            stats=self.container.get_statistics()
        )
    
    def _register_external_dependencies(self) -> None:
        """Register external/mock dependencies"""
        # These would normally come from external systems
        # For now, register mocks or stubs
        
        # Resource Orchestrator (if not already available)
        if not self.container.has_registration(IResourceOrchestrator):
            from autocoder_cc.resource_orchestrator import ResourceOrchestrator
            self.container.register_singleton(
                IResourceOrchestrator,
                ResourceOrchestrator,
                description="Resource allocation and management"
            )
        
        # Prompt Manager
        if not self.container.has_registration(IPromptManager):
            from autocoder_cc.blueprint_language.prompt_manager import PromptManager
            self.container.register_singleton(
                IPromptManager,
                PromptManager,
                description="LLM prompt management"
            )
        
        # LLM Provider
        if not self.container.has_registration(ILLMProvider):
            from autocoder_cc.blueprint_language.llm_provider import LLMProvider
            self.container.register_singleton(
                ILLMProvider,
                LLMProvider,
                description="LLM integration provider"
            )
        
        # Config Manager
        if not self.container.has_registration(IConfigManager):
            from autocoder_cc.core.config_manager import ConfigManager
            self.container.register_singleton(
                IConfigManager,
                ConfigManager,
                description="Configuration management"
            )
        
        # Secret Manager  
        if not self.container.has_registration(ISecretManager):
            from autocoder_cc.production.secrets_manager import SecretsManager
            self.container.register_singleton(
                ISecretManager,
                SecretsManager,
                description="Secret management"
            )
    
    def _configure_pipeline_dependencies(self, output_dir: Path) -> None:
        """Configure pipeline-specific dependencies"""
        # Register pipeline coordinator factory with output directory
        def create_pipeline_coordinator() -> IPipelineCoordinator:
            from autocoder_cc.orchestration.pipeline_coordinator import PipelineCoordinator
            
            # Resolve deployment manager in proper scope
            with self.container.scope("deployment"):
                deployment_manager = self.container.resolve(IDeploymentManager)
            
            return PipelineCoordinator(
                output_dir=output_dir,
                resource_orchestrator=self.container.resolve(IResourceOrchestrator),
                scaffold_generator=None,  # TODO: Add IScaffoldGenerator interface
                component_generator=self.container.resolve(IComponentGenerator),
                test_generator=None,  # TODO: Add ITestGenerator interface
                deployment_manager=deployment_manager,
                blueprint_validator=self.container.resolve(IBlueprintValidator)
            )
        
        self.container.register_factory(
            IPipelineCoordinator,
            create_pipeline_coordinator,
            description="Pipeline orchestration with output directory"
        )
    
    def register_legacy_modules(self, output_dir: Path) -> None:
        """
        Register legacy modules that haven't been fully extracted yet.
        
        This is temporary until all modules are properly extracted.
        """
        # Scaffold Generator (placeholder until extracted)
        class ScaffoldGeneratorStub:
            def generate_system(self, blueprint):
                return {"scaffold": "generated", "status": "success"}
        
        self.container.register_instance(
            ScaffoldGeneratorStub,
            ScaffoldGeneratorStub(),
            alias="scaffold_generator"
        )
        
        # Test Generator (placeholder until extracted)
        class TestGeneratorStub:
            def generate_tests(self, blueprint):
                return [{"test": "generated", "type": "unit"}]
        
        self.container.register_instance(
            TestGeneratorStub,
            TestGeneratorStub(),
            alias="test_generator"
        )
    
    def get_container(self) -> EnhancedDependencyContainer:
        """
        Get the configured dependency container.
        
        Returns:
            Configured EnhancedDependencyContainer
        """
        return self.container
    
    def resolve(self, interface: Type) -> Any:
        """
        Resolve a dependency by interface.
        
        Args:
            interface: Interface type to resolve
            
        Returns:
            Implementation instance
        """
        return self.container.resolve(interface)
    
    def get_dependency_report(self) -> str:
        """
        Get a human-readable dependency report.
        
        Returns:
            Formatted dependency report
        """
        return self.container.export_registration_summary()
    
    def validate_system_ready(self) -> bool:
        """
        Validate that the system has all required dependencies.
        
        Returns:
            True if system is ready, False otherwise
        """
        required_interfaces = [
            IPipelineCoordinator,
            IBlueprintProcessor,
            IBlueprintValidator,
            IComponentGenerator,
            ITemplateEngine,
            IDeploymentManager,
            IEnvironmentProvisioner,
            IResourceOrchestrator
        ]
        
        missing = []
        for interface in required_interfaces:
            if not self.container.has_registration(interface):
                missing.append(interface.__name__)
        
        if missing:
            self.logger.warning(
                "System not ready - missing dependencies",
                missing=missing
            )
            return False
        
        return True


# Legacy compatibility layer
class DependencyContainer:
    """
    Legacy dependency container wrapper for backward compatibility.
    
    This wraps the new enhanced container to provide the old API
    while migrating to the new system.
    """
    
    def __init__(self):
        """Initialize with enhanced container"""
        self._config = SystemDependencyConfiguration()
        self._logger = logging.getLogger(__name__)
    
    def register_dependency(self, name: str, dependency: Any, singleton: bool = False) -> None:
        """Legacy registration method"""
        # Use instance registration for backward compatibility
        interface_type = type(dependency)
        self._config.container.register_instance(
            interface_type,
            dependency,
            alias=name
        )
    
    def get_dependency(self, name: str) -> Any:
        """Legacy resolution method"""
        # Try alias first, then direct resolution
        try:
            # Find interface by alias
            for interface, reg in self._config.container.get_all_registrations().items():
                if hasattr(reg, 'alias') and reg.alias == name:
                    return self._config.container.resolve(interface)
            
            # Try direct resolution by name
            return self._config.container.resolve(None, alias=name)
        except ValueError:
            raise KeyError(f"Dependency '{name}' not registered")
    
    def get_all_dependencies(self) -> Dict[str, Any]:
        """Legacy method to get all dependencies"""
        # Return dictionary of alias -> instance
        result = {}
        registrations = self._config.container.get_all_registrations()
        
        for interface, reg in registrations.items():
            # Use interface name as key if no alias
            key = getattr(reg, 'alias', interface.__name__)
            try:
                result[key] = self._config.container.resolve(interface)
            except Exception:
                # Skip if cannot resolve
                pass
        
        return result
    
    def register_standard_system_dependencies(self, output_dir: Path) -> None:
        """Legacy standard registration"""
        self._config.configure_standard_modules(output_dir)
        self._config.register_legacy_modules(output_dir)