"""
Pipeline Coordinator - Extracted from SystemGenerator monolith

Coordinates the system generation pipeline with clean separation of concerns.
Manages the orchestration of scaffold generation, component generation, testing, and deployment.
"""
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.core.module_interfaces import (
    IResourceOrchestrator,
    IComponentGenerator,
    IDeploymentManager,
    IBlueprintValidator
)


@dataclass
class GeneratedSystem:
    """Complete generated system result"""
    name: str
    scaffold: Any  # GeneratedScaffold 
    components: List[Any]  # List[GeneratedComponent]
    tests: List[Any]  # List[PropertyTestSuite]
    deployment: Any  # GeneratedDeployment
    output_directory: Path


class PipelineCoordinator:
    """
    Pipeline coordination extracted from SystemGenerator monolith.
    
    Responsibilities:
    - Overall pipeline orchestration (~200 lines from monolith)
    - Module integration with clean interfaces
    - Resource management integration with ResourceOrchestrator
    - Centralized error handling across pipeline stages
    """
    
    def __init__(
        self,
        output_dir: Path,
        resource_orchestrator: IResourceOrchestrator,
        scaffold_generator: Any,  # IScaffoldGenerator when defined
        component_generator: IComponentGenerator,
        test_generator: Any,  # ITestGenerator when defined
        deployment_manager: IDeploymentManager,
        blueprint_validator: IBlueprintValidator
    ):
        """Initialize pipeline coordinator with injected dependencies"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store injected dependencies
        self.resource_orchestrator = resource_orchestrator
        self.scaffold_generator = scaffold_generator
        self.component_generator = component_generator
        self.test_generator = test_generator
        self.deployment_manager = deployment_manager
        self.blueprint_validator = blueprint_validator
        
        # Initialize observability
        self.logger = get_logger("pipeline_coordinator", component="PipelineCoordinator")
        self.metrics_collector = get_metrics_collector("pipeline_coordinator")
        self.tracer = get_tracer("pipeline_coordinator")
        
        self.logger.info(
            "PipelineCoordinator initialized with dependency injection",
            operation="init",
            tags={"output_dir": str(output_dir)}
        )
    
    async def orchestrate_system_generation(self, system_blueprint: ParsedSystemBlueprint) -> GeneratedSystem:
        """
        Main pipeline orchestration method.
        
        Coordinates all phases of system generation with proper error handling
        and resource management.
        """
        system_name = system_blueprint.system.name
        
        with self.tracer.span("pipeline_orchestration", tags={"system_name": system_name}) as span_id:
            start_time = time.time()
            
            self.logger.info(
                "Starting system generation pipeline orchestration",
                operation="orchestrate_system_generation", 
                tags={"system_name": system_name}
            )
            
            try:
                # Phase 0: Pre-generation validation
                validation_result = await self._run_pre_generation_validation(system_blueprint)
                if not validation_result.is_valid:
                    raise ValueError(f"Blueprint validation failed: {validation_result.errors}")
                
                # Phase 0.5: Resource allocation
                allocated_ports = await self._allocate_system_resources(system_blueprint)
                
                # Phase 1: Scaffold generation
                scaffold = await self._generate_system_scaffold(system_blueprint)
                
                # Phase 2: Component generation
                components = await self._generate_system_components(system_blueprint)
                
                # Phase 3: Test generation
                tests = await self._generate_system_tests(system_blueprint)
                
                # Phase 4: Deployment generation
                deployment = await self._generate_system_deployment(system_blueprint, allocated_ports)
                
                # Phase 5: System assembly
                final_system_dir = await self._assemble_final_system(
                    system_name, scaffold, components, tests, deployment, system_blueprint
                )
                
                # Record metrics
                generation_time = (time.time() - start_time) * 1000
                self.metrics_collector.record_system_generated()
                self.metrics_collector.record_generation_time(generation_time)
                
                result = GeneratedSystem(
                    name=system_name,
                    scaffold=scaffold,
                    components=components,
                    tests=tests,
                    deployment=deployment,
                    output_directory=final_system_dir
                )
                
                self.logger.info(
                    "System generation pipeline completed successfully",
                    operation="orchestrate_system_generation_complete",
                    metrics={"generation_time_ms": generation_time},
                    tags={"system_name": system_name}
                )
                
                return result
                
            except Exception as e:
                # Centralized error handling
                self.metrics_collector.record_error(e.__class__.__name__)
                self.logger.error(
                    "Pipeline execution failed",
                    error=e,
                    operation="orchestrate_system_generation_error",
                    tags={"system_name": system_name}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Pipeline error: {e}", "error")
                
                raise RuntimeError(f"Pipeline execution failed: {e}") from e
    
    async def _run_pre_generation_validation(self, system_blueprint: ParsedSystemBlueprint):
        """Run pre-generation validation phase"""
        self.logger.info("Running pre-generation validation", operation="pre_validation")
        
        validation_result = self.blueprint_validator.validate_pre_generation(system_blueprint)
        
        self.logger.info(
            "Pre-generation validation completed",
            operation="pre_validation_complete",
            tags={"is_valid": validation_result.is_valid}
        )
        
        return validation_result
    
    async def _allocate_system_resources(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, int]:
        """Allocate ports and resources for system components"""
        self.logger.info("Allocating system resources", operation="resource_allocation")
        
        allocated_ports = {}
        
        for component in system_blueprint.system.components:
            if component.type in ['APIEndpoint', 'MetricsEndpoint']:
                allocated_port = self.resource_orchestrator.allocate_port(
                    component.name,
                    system_blueprint.system.name
                )
                allocated_ports[component.name] = allocated_port
                
                # Update component config with allocated port
                if not component.config:
                    component.config = {}
                component.config['port'] = allocated_port
                
                self.logger.info(
                    f"Allocated port {allocated_port} for {component.name}",
                    operation="port_allocation",
                    tags={"component": component.name, "port": allocated_port}
                )
        
        self.logger.info(
            f"Resource allocation completed - {len(allocated_ports)} ports allocated",
            operation="resource_allocation_complete",
            tags={"ports_allocated": len(allocated_ports)}
        )
        
        return allocated_ports
    
    async def _generate_system_scaffold(self, system_blueprint: ParsedSystemBlueprint):
        """Generate system scaffold phase"""
        self.logger.info("Generating system scaffold", operation="scaffold_generation")
        
        try:
            scaffold = self.scaffold_generator.generate_system(system_blueprint)
            
            self.logger.info(
                "System scaffold generated successfully",
                operation="scaffold_generation_complete"
            )
            
            return scaffold
            
        except Exception as e:
            self.logger.error(
                "Scaffold generation failed",
                error=e,
                operation="scaffold_generation_error"
            )
            raise RuntimeError(f"Scaffold generation failed: {e}") from e
    
    async def _generate_system_components(self, system_blueprint: ParsedSystemBlueprint):
        """Generate system components phase"""
        self.logger.info("Generating system components", operation="component_generation")
        
        try:
            components = await self.component_generator.generate_components(system_blueprint)
            
            self.logger.info(
                f"Generated {len(components)} components successfully",
                operation="component_generation_complete",
                tags={"components_count": len(components)}
            )
            
            return components
            
        except Exception as e:
            self.logger.error(
                "Component generation failed", 
                error=e,
                operation="component_generation_error"
            )
            raise RuntimeError(f"Component generation failed: {e}") from e
    
    async def _generate_system_tests(self, system_blueprint: ParsedSystemBlueprint):
        """Generate system tests phase"""
        self.logger.info("Generating system tests", operation="test_generation")
        
        try:
            tests = self.test_generator.generate_tests(system_blueprint)
            
            self.logger.info(
                f"Generated {len(tests)} test files successfully",
                operation="test_generation_complete",
                tags={"tests_count": len(tests)}
            )
            
            return tests
            
        except Exception as e:
            self.logger.error(
                "Test generation failed",
                error=e, 
                operation="test_generation_error"
            )
            raise RuntimeError(f"Test generation failed: {e}") from e
    
    async def _generate_system_deployment(self, system_blueprint: ParsedSystemBlueprint, allocated_ports: Dict[str, int]):
        """Generate system deployment phase"""
        self.logger.info("Generating system deployment", operation="deployment_generation")
        
        try:
            # Use deployment manager interface
            deployment_result = self.deployment_manager.deploy_system(
                blueprint=system_blueprint,
                output_dir=self.output_dir / system_blueprint.system.name / "deployment",
                environment="production"
            )
            
            self.logger.info(
                "System deployment generated successfully",
                operation="deployment_generation_complete",
                tags={"environment": deployment_result.environment}
            )
            
            return deployment_result
            
        except Exception as e:
            self.logger.error(
                "Deployment generation failed",
                error=e,
                operation="deployment_generation_error"
            )
            raise RuntimeError(f"Deployment generation failed: {e}") from e
    
    async def _assemble_final_system(self, system_name: str, scaffold, components, tests, deployment, system_blueprint):
        """Assemble final system from all generated components"""
        self.logger.info("Assembling final system", operation="system_assembly")
        
        try:
            # Create final system directory
            final_dir = self.output_dir / system_name
            final_dir.mkdir(exist_ok=True)
            
            self.logger.info(
                f"Final system assembled at {final_dir}",
                operation="system_assembly_complete",
                tags={"output_directory": str(final_dir)}
            )
            
            return final_dir
            
        except Exception as e:
            self.logger.error(
                "System assembly failed",
                error=e,
                operation="system_assembly_error" 
            )
            raise RuntimeError(f"System assembly failed: {e}") from e