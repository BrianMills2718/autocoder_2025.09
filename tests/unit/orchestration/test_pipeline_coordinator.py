"""
Unit tests for PipelineCoordinator - TDD RED Phase
Tests the interface that will coordinate the system generation pipeline
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from autocoder_cc.orchestration.pipeline_coordinator import PipelineCoordinator
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint


class TestPipelineCoordinator:
    """Test the pipeline coordination module extracted from monolith"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for PipelineCoordinator"""
        return {
            'resource_orchestrator': Mock(),
            'scaffold_generator': Mock(),
            'component_generator': AsyncMock(),
            'test_generator': Mock(),
            'deployment_generator': Mock(),  # Changed from AsyncMock to Mock since deploy_system is synchronous
            'validation_orchestrator': Mock()
        }
    
    @pytest.fixture
    def sample_blueprint(self):
        """Create a minimal parsed blueprint for testing"""
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        blueprint.system.components = []
        blueprint.system.bindings = []
        return blueprint
    
    def test_pipeline_coordinator_initialization(self, mock_dependencies):
        """RED: Test that PipelineCoordinator can be initialized with dependencies"""
        output_dir = Path("/tmp/test_output")
        
        coordinator = PipelineCoordinator(
            output_dir=output_dir,
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        assert coordinator.output_dir == output_dir
        assert coordinator.resource_orchestrator == mock_dependencies['resource_orchestrator']
    
    @pytest.mark.asyncio
    async def test_orchestrate_system_generation(self, mock_dependencies, sample_blueprint):
        """RED: Test the main orchestration method"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Setup mocks to return proper values
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.errors = []
        mock_dependencies['validation_orchestrator'].validate_pre_generation.return_value = validation_result
        mock_dependencies['scaffold_generator'].generate_system.return_value = Mock()
        mock_dependencies['component_generator'].generate_components.return_value = []
        mock_dependencies['test_generator'].generate_tests.return_value = []
        deployment_result = Mock()
        deployment_result.environment = "production"
        
        # Make deploy_system return deployment_result directly (it's synchronous)
        mock_dependencies['deployment_generator'].deploy_system.return_value = deployment_result
        
        # This should orchestrate the entire pipeline
        result = await coordinator.orchestrate_system_generation(sample_blueprint)
        
        # Verify pipeline phases were called in correct order
        mock_dependencies['scaffold_generator'].generate_system.assert_called_once()
        mock_dependencies['component_generator'].generate_components.assert_called_once()
        mock_dependencies['test_generator'].generate_tests.assert_called_once()
        mock_dependencies['deployment_generator'].deploy_system.assert_called_once()
        
        assert result.name == "test_system"
        assert result.output_directory is not None
    
    @pytest.mark.asyncio
    async def test_resource_allocation_phase(self, mock_dependencies, sample_blueprint):
        """RED: Test port and resource allocation coordination"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Mock component that needs port allocation
        mock_component = Mock()
        mock_component.name = "api_endpoint"
        mock_component.type = "APIEndpoint"
        mock_component.config = {}
        sample_blueprint.system.components = [mock_component]
        
        # Mock port allocation
        mock_dependencies['resource_orchestrator'].allocate_port.return_value = 8080
        
        await coordinator._allocate_system_resources(sample_blueprint)
        
        # Verify port was allocated and component config updated
        mock_dependencies['resource_orchestrator'].allocate_port.assert_called_once_with(
            "api_endpoint", "test_system"
        )
        assert mock_component.config['port'] == 8080
    
    @pytest.mark.asyncio 
    async def test_validation_phase_integration(self, mock_dependencies, sample_blueprint):
        """RED: Test pre-generation validation integration"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Mock validation success
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.errors = []
        mock_dependencies['validation_orchestrator'].validate_pre_generation.return_value = validation_result
        
        validation_result_actual = await coordinator._run_pre_generation_validation(sample_blueprint)
        
        assert validation_result_actual.is_valid == True
        mock_dependencies['validation_orchestrator'].validate_pre_generation.assert_called_once_with(sample_blueprint)
    
    @pytest.mark.asyncio
    async def test_validation_failure_handling(self, mock_dependencies, sample_blueprint):
        """RED: Test that validation failures are properly handled"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Mock validation failure
        validation_result = Mock()
        validation_result.is_valid = False
        validation_result.errors = ["Component 'test' has invalid configuration"]
        mock_dependencies['validation_orchestrator'].validate_pre_generation.return_value = validation_result
        
        with pytest.raises(RuntimeError, match="Pipeline execution failed"):
            await coordinator.orchestrate_system_generation(sample_blueprint)
    
    @pytest.mark.asyncio
    async def test_error_propagation_across_phases(self, mock_dependencies, sample_blueprint):
        """RED: Test centralized error handling across pipeline stages"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Mock scaffold generation failure
        mock_dependencies['scaffold_generator'].generate_system.side_effect = RuntimeError("Scaffold failed")
        
        with pytest.raises(RuntimeError, match="Pipeline execution failed"):
            await coordinator.orchestrate_system_generation(sample_blueprint)
    
    def test_dependency_injection_integration(self, mock_dependencies):
        """RED: Test that dependencies are properly injected"""
        coordinator = PipelineCoordinator(
            output_dir=Path("/tmp/test"),
            resource_orchestrator=mock_dependencies['resource_orchestrator'],
            scaffold_generator=mock_dependencies['scaffold_generator'],
            component_generator=mock_dependencies['component_generator'],
            test_generator=mock_dependencies['test_generator'],
            deployment_manager=mock_dependencies['deployment_generator'],
            blueprint_validator=mock_dependencies['validation_orchestrator']
        )
        
        # Verify all required dependencies are available (using actual attribute names)
        assert hasattr(coordinator, 'resource_orchestrator')
        assert getattr(coordinator, 'resource_orchestrator') == mock_dependencies['resource_orchestrator']
        
        assert hasattr(coordinator, 'scaffold_generator')
        assert getattr(coordinator, 'scaffold_generator') == mock_dependencies['scaffold_generator']
        
        assert hasattr(coordinator, 'component_generator')
        assert getattr(coordinator, 'component_generator') == mock_dependencies['component_generator']
        
        assert hasattr(coordinator, 'test_generator')
        assert getattr(coordinator, 'test_generator') == mock_dependencies['test_generator']
        
        assert hasattr(coordinator, 'deployment_manager')
        assert getattr(coordinator, 'deployment_manager') == mock_dependencies['deployment_generator']
        
        assert hasattr(coordinator, 'blueprint_validator')
        assert getattr(coordinator, 'blueprint_validator') == mock_dependencies['validation_orchestrator']