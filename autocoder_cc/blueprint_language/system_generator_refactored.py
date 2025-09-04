#!/usr/bin/env python3
"""
System Generator - Refactored Two-Phase Generation Orchestrator
Coordinates scaffold generation and component logic generation to create complete systems

Refactored from 1941-line monolith into modular, maintainable architecture.
"""
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Phase 2B: Import centralized timeout management
from autocoder_cc.core.timeout_manager import get_timeout_manager, TimeoutType, TimeoutError

from .system_blueprint_parser import SystemBlueprintParser, ParsedSystemBlueprint
from .system_scaffold_generator import SystemScaffoldGenerator, GeneratedScaffold
from .component_logic_generator import ComponentLogicGenerator, GeneratedComponent
from .production_deployment_generator import ProductionDeploymentGenerator, GeneratedDeployment
from .verbose_logger import VerboseLogger, GenerationStepContext

# Import extracted classes
from .system_validator import SystemValidator, GeneratedSystem
from .system_communication_generator import SystemCommunicationGenerator
from .system_file_manager import SystemFileManager

from autocoder_cc.components.component_registry import component_registry
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.resource_orchestrator import ResourceOrchestrator

# Phase 1 integration imports
from autocoder_cc.core.schema_versioning import generate_schema_artifacts


class SystemGeneratorRefactored:
    """
    Refactored two-phase system generator with modular architecture.
    
    Reduced from 1941 lines to <500 lines by extracting:
    - SystemValidator: Blueprint and system validation
    - SystemCommunicationGenerator: Messaging and service communication
    - SystemFileManager: File operations and system assembly
    
    Phase 1: System Scaffold Generation
    - Generates main.py with SystemExecutionHarness setup
    - Creates configuration files and infrastructure
    - Handles component registration and connections
    
    Phase 2: Component Logic Generation  
    - Generates harness-compatible component implementations
    - Uses shared observability module to eliminate boilerplate
    - Ensures all components follow lifecycle methods
    """
    
    def __init__(self, output_dir: Path, verbose_logging: bool = True, timeout: Optional[int] = 300):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize observability stack
        self.logger = get_logger("system_generator", component="SystemGeneratorRefactored")
        self.metrics = get_metrics_collector("system_generator")
        self.tracer = get_tracer("system_generator")
        
        # Initialize extracted modules
        self.validator = SystemValidator()
        self.communication_generator = SystemCommunicationGenerator()
        self.file_manager = SystemFileManager(output_dir)
        
        # Initialize existing generators
        self.scaffold_generator = SystemScaffoldGenerator(self.output_dir / "scaffolds")
        self.component_generator = ComponentLogicGenerator(self.output_dir / "scaffolds")
        self.deployment_generator = ProductionDeploymentGenerator(self.output_dir / "deployments")
        
        # Initialize resource orchestrator
        self.resource_orchestrator = ResourceOrchestrator()
        
        # Initialize verbose logging
        self.verbose_logging = verbose_logging
        if verbose_logging:
            self.verbose_logger = VerboseLogger(self.output_dir)
        
        # Initialize timeout management
        self.timeout = timeout
        self.timeout_manager = get_timeout_manager()
        
        self.logger.info(
            "SystemGeneratorRefactored initialized with modular architecture",
            operation="init",
            tags={
                "output_dir": str(output_dir),
                "verbose_logging": verbose_logging,
                "timeout": timeout
            }
        )
    
    async def generate_system_with_timeout(self, *args, **kwargs):
        """Generate system with timeout management"""
        if self.timeout:
            try:
                return await asyncio.wait_for(
                    self.generate_system(*args, **kwargs),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"System generation exceeded {self.timeout}s timeout")
        else:
            return await self.generate_system(*args, **kwargs)
    
    async def generate_system(self, blueprint_file: Path) -> GeneratedSystem:
        """
        Generate complete system from blueprint file
        
        Args:
            blueprint_file: Path to YAML blueprint file
            
        Returns:
            GeneratedSystem with all artifacts
        """
        # Parse blueprint
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_file(blueprint_file)
        
        return await self._generate_system_from_blueprint(system_blueprint)
    
    async def generate_system_from_yaml(self, blueprint_yaml: str) -> GeneratedSystem:
        """
        Generate complete system from YAML string
        
        Args:
            blueprint_yaml: YAML blueprint as string
            
        Returns:
            GeneratedSystem with all artifacts
        """
        # Parse blueprint
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_string(blueprint_yaml)
        
        return await self._generate_system_from_blueprint(system_blueprint)
    
    async def _generate_system_from_blueprint(self, system_blueprint: ParsedSystemBlueprint) -> GeneratedSystem:
        """Main system generation orchestration"""
        if self.verbose_logging:
            return await self._generate_system_with_logging(system_blueprint)
        else:
            return await self._generate_system_core(system_blueprint)
    
    async def _generate_system_with_logging(self, system_blueprint: ParsedSystemBlueprint) -> GeneratedSystem:
        """Generate system with verbose logging"""
        system_name = system_blueprint.system.name
        
        with GenerationStepContext(self.logger, "generate_system", f"Generate System: {system_name}"):
            self.logger.info(f"🚀 Generating system: {system_name}")
            self.logger.info("📋 Blueprint details:")
            self.logger.info(f"   - Components: {len(system_blueprint.system.components)}")
            self.logger.info(f"   - Bindings: {len(system_blueprint.system.bindings)}")
            self.logger.info(f"   - Version: {system_blueprint.schema_version}")
            
            return await self._generate_system_core(system_blueprint)
    
    async def _generate_system_core(self, system_blueprint: ParsedSystemBlueprint) -> GeneratedSystem:
        """Core system generation logic"""
        system_name = system_blueprint.system.name
        
        # Phase 1: Pre-generation Validation
        with GenerationStepContext(self.logger, "pre_generation_validation", "Pre-Generation Validation"):
            validation_errors = self.validator.validate_pre_generation(system_blueprint)
            if validation_errors:
                error_summary = f"System blueprint validation failed with {len(validation_errors)} errors\n"
                error_summary += "\n".join(f"  {error}" for error in validation_errors)
                raise ValueError(error_summary)
            
            self.logger.info("✅ pre_generation: PASSED")
        
        # Phase 2: Allocate System Ports
        with GenerationStepContext(self.logger, "port_allocation", "Allocate System Ports"):
            port_allocations = self.resource_orchestrator.allocate_ports(system_blueprint)
            self.logger.info(f"🔌 Allocated port {port_allocations.get('api_service', 'N/A')} for api_service")
            self.logger.info(f"✅ Allocated {len(port_allocations)} ports successfully")
        
        # Phase 3: Generate System Scaffold
        with GenerationStepContext(self.logger, "scaffold_generation", "Generate System Scaffold"):
            scaffold = await self.scaffold_generator.generate_scaffold(system_blueprint)
            self._log_generated_files(scaffold)
        
        # Phase 4: Generate Database Schema Artifacts
        with GenerationStepContext(self.logger, "schema_generation", "Generate Database Schema Artifacts"):
            schema_artifacts = generate_schema_artifacts(
                system_blueprint, 
                scaffold.output_dir / "database"
            )
            self.logger.info(f"✅ Generated {len(schema_artifacts)} schema artifacts")
            self._log_schema_artifacts(schema_artifacts, scaffold.output_dir)
        
        # Phase 5: Generate Service Communication Configuration
        with GenerationStepContext(self.logger, "communication_config", "Generate Service Communication Configuration"):
            messaging_config = self.communication_generator.generate_service_communication_config(system_blueprint)
            messaging_config_file = scaffold.output_dir / "config" / "messaging_config.yaml"
            messaging_config_file.parent.mkdir(exist_ok=True)
            messaging_config_file.write_text(messaging_config)
            self.logger.info("✅ Generated service communication configuration")
            self._log_file_generated(messaging_config_file, messaging_config)
        
        # Phase 6: Generate Shared Observability Module (Phase 2A Implementation)
        with GenerationStepContext(self.logger, "observability_generation", "Generate Shared Observability Module"):
            from autocoder_cc.generators.scaffold.observability_generator import generate_shared_observability
            
            # Generate shared observability module in components directory
            components_dir = scaffold.output_dir / "components"
            observability_file = generate_shared_observability(
                system_name=system_name,
                output_dir=components_dir,
                include_prometheus=True
            )
            
            observability_content = observability_file.read_text()
            self.logger.info(f"✅ Generated shared observability module: {observability_file}")
            self.logger.info(f"📏 Observability module: {len(observability_content)} chars, {len(observability_content.splitlines())} lines")
        
        # Phase 7: Generate Communication Framework (Phase 2B Implementation)
        with GenerationStepContext(self.logger, "communication_framework", "Generate Communication Framework"):
            from autocoder_cc.generators.scaffold.communication_generator import generate_communication_framework
            
            communication_file = generate_communication_framework(
                system_blueprint=system_blueprint,
                output_dir=components_dir
            )
            
            communication_content = communication_file.read_text()
            self.logger.info(f"✅ Generated communication framework: {communication_file}")
            self.logger.info(f"📏 Communication module: {len(communication_content)} chars, {len(communication_content.splitlines())} lines")
            self.logger.info(f"🔗 Configured {len(system_blueprint.system.bindings)} component bindings for runtime routing")
        
        # Phase 8: Generate Component Implementations
        with GenerationStepContext(self.logger, "component_generation", "Generate Component Implementations"):
            components = await self.component_generator.generate_components(system_blueprint, scaffold.output_dir)
            for component in components:
                self.logger.info(f"🤖 Generated component: {component.name} ({component.type})")
        
        # Phase 9: Generate Production Deployment
        with GenerationStepContext(self.logger, "deployment_generation", "Generate Production Deployment"):
            deployment = await self.deployment_generator.generate_deployment(
                system_blueprint, 
                scaffold.output_dir
            )
            self.logger.info(f"🚀 Generated deployment: {deployment.output_dir}")
        
        # Phase 10: Combine into Final System
        with GenerationStepContext(self.logger, "final_assembly", "Combine into Final System"):
            final_system_dir = self.file_manager.combine_into_final_system(
                scaffold_dir=scaffold.output_dir,
                components=components,
                system_blueprint=system_blueprint,
                deployment_dir=deployment.output_dir
            )
            
            # Save blueprint with system
            self.file_manager.save_blueprint_with_system(system_blueprint, final_system_dir)
            
            # Set up additional system structure
            self.file_manager.copy_documentation_generator(final_system_dir)
            self.file_manager.create_init_files(final_system_dir, components, system_blueprint)
            self.file_manager.setup_autocoder_dependency(final_system_dir)
        
        # Phase 11: Final Validation
        with GenerationStepContext(self.logger, "final_validation", "Final System Validation"):
            generated_system = GeneratedSystem(
                name=system_name,
                scaffold_dir=scaffold.output_dir,
                deployment_dir=deployment.output_dir,
                components=components,
                blueprint=system_blueprint,
                metadata={"generated_at": time.time()}
            )
            
            final_validation_errors = self.validator.validate_generated_system(generated_system)
            if final_validation_errors:
                self.logger.warning(f"Final validation found {len(final_validation_errors)} issues:")
                for error in final_validation_errors:
                    self.logger.warning(f"  - {error}")
            else:
                self.logger.info("✅ Final validation passed")
            
            # Enforce AST validation
            self.validator.enforce_system_ast_validation(final_system_dir)
        
        self.logger.info(f"🎉 System generation completed: {final_system_dir}")
        
        # Create final GeneratedSystem object
        final_generated_system = GeneratedSystem(
            name=system_name,
            scaffold_dir=scaffold.output_dir,
            deployment_dir=deployment.output_dir,
            components=components,
            blueprint=system_blueprint,
            metadata={
                "generated_at": time.time(),
                "final_system_dir": str(final_system_dir),
                "component_count": len(components),
                "validation_errors": len(final_validation_errors)
            }
        )
        
        return final_generated_system
    
    def _log_generated_files(self, scaffold: GeneratedScaffold):
        """Log generated scaffold files"""
        if hasattr(scaffold, 'main_py_content'):
            self.logger.info(f"📄 Generated: main.py")
            self.logger.info(f"   📏 Size: {len(scaffold.main_py_content)} chars, {len(scaffold.main_py_content.splitlines())} lines")
        
        # Log other scaffold files
        if scaffold.output_dir.exists():
            for file_path in scaffold.output_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.py', '.yaml', '.txt', '.dockerfile']:
                    relative_path = file_path.relative_to(scaffold.output_dir)
                    content = file_path.read_text()
                    self.logger.info(f"📄 Generated: {relative_path}")
                    self.logger.info(f"   📏 Size: {len(content)} chars, {len(content.splitlines())} lines")
    
    def _log_schema_artifacts(self, schema_artifacts: List[Path], base_dir: Path):
        """Log generated schema artifacts"""
        for artifact_path in schema_artifacts:
            relative_path = artifact_path.relative_to(base_dir)
            content = artifact_path.read_text()
            self.logger.info(f"📄 Generated: {relative_path}")
            self.logger.info(f"   📏 Size: {len(content)} chars, {len(content.splitlines())} lines")
    
    def _log_file_generated(self, file_path: Path, content: str):
        """Log a generated file"""
        # Extract relative path from output directory
        try:
            relative_path = file_path.relative_to(self.output_dir)
        except ValueError:
            relative_path = file_path.name
        
        self.logger.info(f"📄 Generated: {relative_path}")
        self.logger.info(f"   📏 Size: {len(content)} chars, {len(content.splitlines())} lines")