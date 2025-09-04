#!/usr/bin/env python3
"""
Module Interfaces for Autocoder CC

Defines strict interfaces for all major system modules to enforce
clean dependency injection and prevent circular dependencies.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import types from existing modules
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autocoder_cc.blueprint_language.system_blueprint_parser import (
        SystemBlueprint,
        ParsedSystemBlueprint,
        ParsedComponent as Component
    )
else:
    # Runtime imports to avoid circular dependencies
    SystemBlueprint = Any
    ParsedSystemBlueprint = Any
    Component = Any

# Local type definitions
ValidationResult = Any  # Will be replaced with proper type


# Data Transfer Objects (DTOs)

@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    status: str
    environment: str
    deployment_path: Path
    manifests: Dict[str, str]
    resource_allocations: Dict[str, Any]
    validation_results: Optional[ValidationResult] = None
    error: Optional[str] = None
    replicas: int = 1
    resource_limits: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Result of component generation"""
    component_name: str
    component_type: str
    generated_code: str
    imports: List[str]
    dependencies: List[str]
    validation_passed: bool
    metrics: Dict[str, Any]


@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class HealingResult:
    """Result of a healing operation"""
    original_value: Any
    healed_value: Any
    healing_applied: bool
    healing_reason: str


# Core Module Interfaces

class IPipelineCoordinator(ABC):
    """Interface for pipeline orchestration"""
    
    @abstractmethod
    def orchestrate_system_generation(
        self,
        blueprint: SystemBlueprint,
        output_dir: Path,
        environment: str = "development"
    ) -> Dict[str, Any]:
        """Orchestrate the complete system generation pipeline"""
        pass
    
    @abstractmethod
    def validate_pipeline_state(self) -> ValidationResult:
        """Validate current pipeline state"""
        pass
    
    @abstractmethod
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        pass


class IBlueprintProcessor(ABC):
    """Interface for blueprint processing"""
    
    @abstractmethod
    def process_blueprint(
        self,
        blueprint: SystemBlueprint
    ) -> ParsedSystemBlueprint:
        """Process and parse a system blueprint"""
        pass
    
    @abstractmethod
    def process_natural_language_blueprint(
        self,
        description: str
    ) -> SystemBlueprint:
        """Process natural language into blueprint"""
        pass
    
    @abstractmethod
    def validate_blueprint(
        self,
        blueprint: SystemBlueprint
    ) -> ValidationResult:
        """Validate blueprint structure and content"""
        pass
    
    @abstractmethod
    def apply_healing(
        self,
        blueprint: SystemBlueprint,
        validation_errors: List[ValidationError]
    ) -> Tuple[SystemBlueprint, List[HealingResult]]:
        """Apply healing to fix validation errors"""
        pass


class IBlueprintValidator(ABC):
    """Interface for blueprint validation"""
    
    @abstractmethod
    def validate_pre_generation(
        self,
        blueprint: ParsedSystemBlueprint
    ) -> ValidationResult:
        """Validate blueprint before generation"""
        pass
    
    @abstractmethod
    def validate_component(
        self,
        component: Component
    ) -> ValidationResult:
        """Validate individual component"""
        pass
    
    @abstractmethod
    def validate_bindings(
        self,
        blueprint: ParsedSystemBlueprint
    ) -> ValidationResult:
        """Validate component bindings"""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules"""
        pass


class IComponentGenerator(ABC):
    """Interface for component generation"""
    
    @abstractmethod
    def generate_component(
        self,
        component: Component,
        blueprint: ParsedSystemBlueprint
    ) -> GenerationResult:
        """Generate code for a component"""
        pass
    
    @abstractmethod
    def generate_business_logic(
        self,
        component: Component,
        prompt: str
    ) -> str:
        """Generate business logic using LLM"""
        pass
    
    @abstractmethod
    def assemble_component(
        self,
        component: Component,
        business_logic: str,
        imports: List[str]
    ) -> str:
        """Assemble complete component code"""
        pass
    
    @abstractmethod
    def get_generation_metrics(self) -> Dict[str, Any]:
        """Get generation performance metrics"""
        pass


class ITemplateEngine(ABC):
    """Interface for template rendering"""
    
    @abstractmethod
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a template with context"""
        pass
    
    @abstractmethod
    def register_template(
        self,
        name: str,
        template_content: str
    ) -> None:
        """Register a new template"""
        pass
    
    @abstractmethod
    def has_template(self, name: str) -> bool:
        """Check if template exists"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear template cache"""
        pass


class IDeploymentManager(ABC):
    """Interface for deployment management"""
    
    @abstractmethod
    def deploy_system(
        self,
        blueprint: ParsedSystemBlueprint,
        output_dir: Path,
        environment: str = "development"
    ) -> DeploymentResult:
        """Deploy a system to specified environment"""
        pass
    
    @abstractmethod
    def generate_kubernetes_manifests(
        self,
        blueprint: ParsedSystemBlueprint,
        environment: str
    ) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        pass
    
    @abstractmethod
    def generate_docker_compose(
        self,
        blueprint: ParsedSystemBlueprint,
        environment: str
    ) -> str:
        """Generate Docker Compose configuration"""
        pass
    
    @abstractmethod
    def validate_deployment(
        self,
        deployment: DeploymentResult
    ) -> ValidationResult:
        """Validate deployment configuration"""
        pass
    
    @abstractmethod
    def rollback_deployment(
        self,
        deployment: DeploymentResult
    ) -> bool:
        """Rollback a failed deployment"""
        pass


class IEnvironmentProvisioner(ABC):
    """Interface for environment provisioning"""
    
    @abstractmethod
    def provision_environment(
        self,
        environment: str,
        blueprint: ParsedSystemBlueprint
    ) -> Dict[str, Any]:
        """Provision resources for environment"""
        pass
    
    @abstractmethod
    def inject_configuration(
        self,
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject environment-specific configuration"""
        pass
    
    @abstractmethod
    def manage_secrets(
        self,
        environment: str,
        secrets: Dict[str, str]
    ) -> Dict[str, str]:
        """Manage environment secrets"""
        pass
    
    @abstractmethod
    def teardown_environment(
        self,
        environment: str
    ) -> bool:
        """Teardown environment resources"""
        pass


class IResourceOrchestrator(ABC):
    """Interface for resource orchestration"""
    
    @abstractmethod
    def allocate_port(
        self,
        service_name: str,
        preferred_port: Optional[int] = None
    ) -> int:
        """Allocate a port for a service"""
        pass
    
    @abstractmethod
    def allocate_database(
        self,
        service_name: str,
        database_type: str
    ) -> Dict[str, Any]:
        """Allocate database resources"""
        pass
    
    @abstractmethod
    def release_resources(
        self,
        service_name: str
    ) -> bool:
        """Release allocated resources"""
        pass
    
    @abstractmethod
    def get_resource_allocation(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """Get current resource allocation"""
        pass


class IPromptManager(ABC):
    """Interface for prompt management"""
    
    @abstractmethod
    def get_prompt(
        self,
        prompt_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Get formatted prompt for LLM"""
        pass
    
    @abstractmethod
    def register_prompt_template(
        self,
        prompt_type: str,
        template: str
    ) -> None:
        """Register new prompt template"""
        pass
    
    @abstractmethod
    def validate_prompt(
        self,
        prompt: str
    ) -> ValidationResult:
        """Validate prompt structure"""
        pass


class ILLMProvider(ABC):
    """Interface for LLM providers"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def validate_response(
        self,
        response: str
    ) -> bool:
        """Validate LLM response"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        pass


class IConfigManager(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_config(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def set_config(
        self,
        key: str,
        value: Any
    ) -> None:
        """Set configuration value"""
        pass
    
    @abstractmethod
    def load_config_file(
        self,
        file_path: Path
    ) -> Dict[str, Any]:
        """Load configuration from file"""
        pass
    
    @abstractmethod
    def validate_config(self) -> ValidationResult:
        """Validate current configuration"""
        pass


class ISecretManager(ABC):
    """Interface for secret management"""
    
    @abstractmethod
    def create_secret(
        self,
        name: str,
        value: str,
        environment: str
    ) -> str:
        """Create a new secret"""
        pass
    
    @abstractmethod
    def get_secret(
        self,
        name: str,
        environment: str
    ) -> str:
        """Retrieve a secret"""
        pass
    
    @abstractmethod
    def update_secret(
        self,
        name: str,
        value: str,
        environment: str
    ) -> bool:
        """Update existing secret"""
        pass
    
    @abstractmethod
    def delete_secret(
        self,
        name: str,
        environment: str
    ) -> bool:
        """Delete a secret"""
        pass


class IValidationHealer(ABC):
    """Interface for validation healing"""
    
    @abstractmethod
    def heal(
        self,
        component: Component,
        validation_errors: List[ValidationError]
    ) -> Tuple[Component, List[HealingResult]]:
        """Heal component validation errors"""
        pass
    
    @abstractmethod
    def can_heal(
        self,
        error: ValidationError
    ) -> bool:
        """Check if error can be healed"""
        pass
    
    @abstractmethod
    def get_healing_strategies(self) -> Dict[str, Any]:
        """Get available healing strategies"""
        pass


class ISystemGenerator(ABC):
    """Interface for system generation (legacy monolith)"""
    
    @abstractmethod
    def generate_system(
        self,
        blueprint_path: Path,
        output_dir: Path,
        environment: str = "development"
    ) -> Dict[str, Any]:
        """Generate complete system from blueprint"""
        pass
    
    @abstractmethod
    def get_generation_status(self) -> Dict[str, Any]:
        """Get current generation status"""
        pass


# Factory Interfaces

class IModuleFactory(ABC):
    """Interface for creating module instances"""
    
    @abstractmethod
    def create_pipeline_coordinator(self) -> IPipelineCoordinator:
        """Create pipeline coordinator instance"""
        pass
    
    @abstractmethod
    def create_blueprint_processor(self) -> IBlueprintProcessor:
        """Create blueprint processor instance"""
        pass
    
    @abstractmethod
    def create_component_generator(self) -> IComponentGenerator:
        """Create component generator instance"""
        pass
    
    @abstractmethod
    def create_deployment_manager(self) -> IDeploymentManager:
        """Create deployment manager instance"""
        pass


# Module Registration Helper

class ModuleRegistry:
    """Helper class for module registration with DI container"""
    
    @staticmethod
    def register_all_modules(container: Any) -> None:
        """Register all standard modules with container"""
        from autocoder_cc.orchestration.pipeline_coordinator import PipelineCoordinator
        from autocoder_cc.blueprint_language.processors.blueprint_processor import BlueprintProcessor
        from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator
        from autocoder_cc.generation.component_generator import ComponentGenerator
        from autocoder_cc.generation.template_engine import TemplateEngine
        from autocoder_cc.deployment.deployment_manager import DeploymentManager
        from autocoder_cc.deployment.environment_provisioner import EnvironmentProvisioner
        
        # Register core modules
        container.register_singleton(
            IPipelineCoordinator,
            PipelineCoordinator,
            description="Main pipeline orchestration"
        )
        
        container.register_singleton(
            IBlueprintProcessor,
            BlueprintProcessor,
            description="Blueprint parsing and processing"
        )
        
        container.register_singleton(
            IBlueprintValidator,
            BlueprintValidator,
            description="Blueprint validation logic"
        )
        
        container.register_transient(
            IComponentGenerator,
            ComponentGenerator,
            description="Component code generation"
        )
        
        container.register_singleton(
            ITemplateEngine,
            TemplateEngine,
            description="Template rendering engine"
        )
        
        container.register_scoped(
            IDeploymentManager,
            DeploymentManager,
            description="Deployment orchestration"
        )
        
        container.register_scoped(
            IEnvironmentProvisioner,
            EnvironmentProvisioner,
            description="Environment provisioning"
        )