#!/usr/bin/env python3
"""
Integration Tests for Module Integration with DI Container

Tests the integration of all extracted modules using the
enhanced dependency injection container.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
from typing import Dict, Any

from autocoder_cc.core.dependency_container import EnhancedDependencyContainer, Lifecycle
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
from autocoder_cc.core.dependency_graph import DependencyGraphVisualizer


class TestModuleIntegration:
    """Integration tests for module DI integration"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing"""
        # Mock external dependencies
        mock_resource_orchestrator = Mock(spec=IResourceOrchestrator)
        mock_resource_orchestrator.allocate_port.return_value = 8080
        mock_resource_orchestrator.allocate_database.return_value = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db"
        }
        
        mock_prompt_manager = Mock(spec=IPromptManager)
        mock_prompt_manager.get_prompt.return_value = "Test prompt"
        
        mock_llm_provider = Mock(spec=ILLMProvider)
        mock_llm_provider.generate.return_value = "Generated code"
        
        mock_config_manager = Mock(spec=IConfigManager)
        mock_config_manager.get_config.return_value = "test_value"
        
        mock_secret_manager = Mock(spec=ISecretManager)
        mock_secret_manager.create_secret.return_value = "vault://secret"
        
        return {
            "resource_orchestrator": mock_resource_orchestrator,
            "prompt_manager": mock_prompt_manager,
            "llm_provider": mock_llm_provider,
            "config_manager": mock_config_manager,
            "secret_manager": mock_secret_manager
        }
    
    @pytest.fixture
    def container(self, mock_dependencies):
        """Create container with mocked observability"""
        with patch('autocoder_cc.core.dependency_container.get_logger') as mock_logger, \
             patch('autocoder_cc.core.dependency_container.get_metrics_collector') as mock_metrics, \
             patch('autocoder_cc.core.dependency_container.get_tracer') as mock_tracer:
            
            mock_logger.return_value = Mock()
            mock_metrics.return_value = Mock()
            mock_tracer.return_value = Mock()
            
            container = EnhancedDependencyContainer()
            
            # Register mock dependencies
            for interface, instance in [
                (IResourceOrchestrator, mock_dependencies["resource_orchestrator"]),
                (IPromptManager, mock_dependencies["prompt_manager"]),
                (ILLMProvider, mock_dependencies["llm_provider"]),
                (IConfigManager, mock_dependencies["config_manager"]),
                (ISecretManager, mock_dependencies["secret_manager"])
            ]:
                container.register_instance(interface, instance)
            
            return container
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_module_registration_with_di_container(self, container):
        """Test registering all modules with DI container"""
        # Patch module imports and observability
        with patch('autocoder_cc.orchestration.pipeline_coordinator.get_logger'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_metrics_collector'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_tracer'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_processor.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_metrics_collector'), \
             patch('autocoder_cc.generation.component_generator.get_tracer'), \
             patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'):
            
            # Use ModuleRegistry to register all modules
            ModuleRegistry.register_all_modules(container)
            
            # Verify all modules are registered
            assert container.has_registration(IPipelineCoordinator)
            assert container.has_registration(IBlueprintProcessor)
            assert container.has_registration(IBlueprintValidator)
            assert container.has_registration(IComponentGenerator)
            assert container.has_registration(ITemplateEngine)
            assert container.has_registration(IDeploymentManager)
            assert container.has_registration(IEnvironmentProvisioner)
            
            # Check lifecycles
            pipeline_reg = container.get_registration(IPipelineCoordinator)
            assert pipeline_reg.lifecycle == Lifecycle.SINGLETON
            
            component_gen_reg = container.get_registration(IComponentGenerator)
            assert component_gen_reg.lifecycle == Lifecycle.TRANSIENT
            
            deployment_reg = container.get_registration(IDeploymentManager)
            assert deployment_reg.lifecycle == Lifecycle.SCOPED
    
    def test_dependency_graph_visualization(self, container, temp_dir):
        """Test dependency graph generation and visualization"""
        # Register modules
        with patch('autocoder_cc.orchestration.pipeline_coordinator.get_logger'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_metrics_collector'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_tracer'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_processor.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_metrics_collector'), \
             patch('autocoder_cc.generation.component_generator.get_tracer'), \
             patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'):
            
            ModuleRegistry.register_all_modules(container)
            
            # Create visualizer
            visualizer = DependencyGraphVisualizer(container)
            
            # Generate analysis (skip PNG to avoid matplotlib in tests)
            results = visualizer.analyze_and_visualize(
                output_dir=temp_dir,
                formats=["dot", "report"]
            )
            
            # Verify results
            assert "stats" in results
            assert results["stats"]["total_nodes"] >= 7  # All registered modules
            assert "cycles" in results
            assert len(results["cycles"]) == 0  # No circular dependencies
            
            # Check generated files
            assert (temp_dir / "dependency_graph.dot").exists()
            assert (temp_dir / "dependency_analysis.txt").exists()
            assert (temp_dir / "dependency_analysis.json").exists()
            
            # Verify report content
            report_content = (temp_dir / "dependency_analysis.txt").read_text()
            assert "Dependency Graph Analysis Report" in report_content
            assert "No circular dependencies detected" in report_content
    
    def test_container_validation_passes(self, container):
        """Test container validation with all modules"""
        with patch('autocoder_cc.orchestration.pipeline_coordinator.get_logger'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_metrics_collector'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_tracer'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_processor.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_metrics_collector'), \
             patch('autocoder_cc.generation.component_generator.get_tracer'), \
             patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'):
            
            ModuleRegistry.register_all_modules(container)
            
            # Validate registrations
            errors = container.validate_registrations()
            
            # Should have no errors (all dependencies are mocked)
            assert len(errors) == 0
    
    def test_module_resolution_chain(self, container):
        """Test resolving modules with dependency chains"""
        with patch('autocoder_cc.orchestration.pipeline_coordinator.get_logger'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_metrics_collector'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_tracer'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_processor.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_metrics_collector'), \
             patch('autocoder_cc.generation.component_generator.get_tracer'), \
             patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'):
            
            # Patch component_registry
            with patch('autocoder_cc.blueprint_language.processors.blueprint_validator.component_registry'):
                ModuleRegistry.register_all_modules(container)
                
                # Resolve template engine (no dependencies)
                template_engine = container.resolve(ITemplateEngine)
                assert template_engine is not None
                
                # Resolve blueprint validator (no injected dependencies)
                validator = container.resolve(IBlueprintValidator)
                assert validator is not None
                
                # Resolve blueprint processor (depends on validator)
                processor = container.resolve(IBlueprintProcessor)
                assert processor is not None
                # Validator should be injected
                assert hasattr(processor, 'validator')
                
                # Resolve component generator (multiple dependencies)
                generator = container.resolve(IComponentGenerator)
                assert generator is not None
                assert hasattr(generator, 'prompt_manager')
                assert hasattr(generator, 'llm_provider')
                assert hasattr(generator, 'template_engine')
    
    def test_scoped_deployment_resolution(self, container):
        """Test scoped lifecycle for deployment modules"""
        with patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'), \
             patch('autocoder_cc.generation.template_engine.get_logger'):
            
            # Register deployment modules
            from autocoder_cc.deployment.deployment_manager import DeploymentManager
            from autocoder_cc.deployment.environment_provisioner import EnvironmentProvisioner
            from autocoder_cc.generation.template_engine import TemplateEngine
            
            container.register_singleton(ITemplateEngine, TemplateEngine)
            container.register_scoped(IEnvironmentProvisioner, EnvironmentProvisioner)
            container.register_scoped(IDeploymentManager, DeploymentManager)
            
            # Test scoped resolution
            with container.scope("deployment1"):
                dm1 = container.resolve(IDeploymentManager)
                dm1_again = container.resolve(IDeploymentManager)
                assert dm1 is dm1_again  # Same instance in scope
            
            with container.scope("deployment2"):
                dm2 = container.resolve(IDeploymentManager)
                assert dm2 is not dm1  # Different instance in different scope
    
    def test_performance_metrics_collection(self, container):
        """Test performance metrics are collected during resolution"""
        with patch('autocoder_cc.generation.template_engine.get_logger'):
            from autocoder_cc.generation.template_engine import TemplateEngine
            
            container.register_singleton(ITemplateEngine, TemplateEngine)
            
            # Resolve multiple times
            for _ in range(10):
                container.resolve(ITemplateEngine)
            
            # Get statistics
            stats = container.get_statistics()
            
            assert stats["performance"]["total_resolutions"] >= 10
            assert stats["performance"]["average_resolution_time_ms"] > 0
            
            # Check top resolved
            top_resolved = stats["top_resolved"]
            assert len(top_resolved) > 0
            assert any(item["interface"] == "ITemplateEngine" for item in top_resolved)
    
    def test_container_summary_export(self, container):
        """Test exporting container summary with all modules"""
        with patch('autocoder_cc.orchestration.pipeline_coordinator.get_logger'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_metrics_collector'), \
             patch('autocoder_cc.orchestration.pipeline_coordinator.get_tracer'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_processor.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_logger'), \
             patch('autocoder_cc.generation.component_generator.get_metrics_collector'), \
             patch('autocoder_cc.generation.component_generator.get_tracer'), \
             patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_logger'), \
             patch('autocoder_cc.deployment.deployment_manager.get_metrics_collector'), \
             patch('autocoder_cc.deployment.deployment_manager.get_tracer'), \
             patch('autocoder_cc.deployment.environment_provisioner.get_logger'):
            
            with patch('autocoder_cc.blueprint_language.processors.blueprint_validator.component_registry'):
                ModuleRegistry.register_all_modules(container)
                
                # Resolve some modules to generate metrics
                container.resolve(ITemplateEngine)
                container.resolve(IBlueprintValidator)
                
                # Export summary
                summary = container.export_registration_summary()
                
                # Verify content
                assert "Dependency Container Registration Summary" in summary
                assert "SINGLETON Dependencies:" in summary
                assert "TRANSIENT Dependencies:" in summary
                assert "SCOPED Dependencies:" in summary
                
                # Check specific modules
                assert "IPipelineCoordinator -> PipelineCoordinator" in summary
                assert "IBlueprintProcessor -> BlueprintProcessor" in summary
                assert "IComponentGenerator -> ComponentGenerator" in summary
                assert "IDeploymentManager -> DeploymentManager" in summary
                
                # Check descriptions
                assert "Main pipeline orchestration" in summary
                assert "Blueprint parsing and processing" in summary
                assert "Component code generation" in summary
                assert "Deployment orchestration" in summary
    
    def test_error_handling_missing_dependency(self, container):
        """Test error handling when dependency is missing"""
        # Create a mock class that requires a missing dependency
        class ServiceRequiringMissing:
            def __init__(self, missing_service: 'IMissingService'):
                self.missing = missing_service
        
        container.register_transient(ServiceRequiringMissing, ServiceRequiringMissing)
        
        with pytest.raises(ValueError, match="Cannot resolve required dependency"):
            container.resolve(ServiceRequiringMissing)
    
    def test_tag_based_module_grouping(self, container):
        """Test grouping modules by tags"""
        with patch('autocoder_cc.generation.template_engine.get_logger'), \
             patch('autocoder_cc.blueprint_language.processors.blueprint_validator.get_logger'):
            
            from autocoder_cc.generation.template_engine import TemplateEngine
            from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator
            
            # Register with tags
            container.register_singleton(
                ITemplateEngine,
                TemplateEngine,
                tags=["generation", "core"]
            )
            
            container.register_singleton(
                IBlueprintValidator,
                BlueprintValidator,
                tags=["validation", "core"]
            )
            
            # Query by tags
            core_modules = container.get_registrations_by_tag("core")
            assert len(core_modules) == 2
            assert ITemplateEngine in core_modules
            assert IBlueprintValidator in core_modules
            
            generation_modules = container.get_registrations_by_tag("generation")
            assert len(generation_modules) == 1
            assert ITemplateEngine in generation_modules