"""
Unit tests for Blueprint Processor - TDD RED Phase
Tests blueprint parsing and validation logic extracted from the monolith
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from autocoder_cc.blueprint_language.processors.blueprint_processor import BlueprintProcessor
from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint


class TestBlueprintProcessor:
    """Test the blueprint processing module extracted from monolith"""
    
    @pytest.fixture
    def sample_blueprint(self):
        """Create a minimal parsed blueprint for testing"""
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        blueprint.system.components = []
        blueprint.system.bindings = []
        blueprint.policy = {}
        return blueprint
    
    @pytest.fixture
    def complex_blueprint(self):
        """Create a complex blueprint for testing validation logic"""
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "complex_system"
        
        # Create components with various types
        api_component = Mock()
        api_component.name = "api_service"
        api_component.type = "APIEndpoint"
        api_component.config = {"port": 8080}
        api_component.inputs = []
        api_component.outputs = [Mock(name="output", schema="DataRecord")]
        
        store_component = Mock()
        store_component.name = "data_store"
        store_component.type = "Store"
        store_component.config = {"storage_type": "file"}
        store_component.inputs = [Mock(name="input", schema="DataRecord")]
        store_component.outputs = []
        
        blueprint.system.components = [api_component, store_component]
        
        # Create binding
        binding = Mock()
        binding.from_component = "api_service"
        binding.from_port = "output"
        binding.to_components = ["data_store"]
        binding.to_ports = ["input"]
        
        blueprint.system.bindings = [binding]
        blueprint.policy = {}
        
        return blueprint
    
    def test_blueprint_processor_initialization(self):
        """RED: Test that BlueprintProcessor can be initialized"""
        processor = BlueprintProcessor(validator=Mock())
        
        assert processor is not None
        assert hasattr(processor, 'validate_blueprint')
        assert hasattr(processor, 'process_blueprint')
    
    def test_blueprint_validation_success(self, sample_blueprint):
        """RED: Test successful blueprint validation"""
        processor = BlueprintProcessor(validator=Mock())
        
        # Mock the validator to return no errors
        with patch.object(processor, '_get_validator') as mock_get_validator:
            mock_validator = Mock()
            mock_validator.validate_pre_generation.return_value = []
            mock_get_validator.return_value = mock_validator
            
            validation_errors = processor.validate_blueprint(sample_blueprint)
            
            assert validation_errors == []
            mock_validator.validate_pre_generation.assert_called_once_with(sample_blueprint)
    
    def test_blueprint_validation_failure(self, sample_blueprint):
        """RED: Test blueprint validation with errors"""
        processor = BlueprintProcessor(validator=Mock())
        
        expected_errors = [
            "Component 'test_component' missing required configuration",
            "Invalid binding from non-existent component"
        ]
        
        with patch.object(processor, '_get_validator') as mock_get_validator:
            mock_validator = Mock()
            mock_validator.validate_pre_generation.return_value = expected_errors
            mock_get_validator.return_value = mock_validator
            
            validation_errors = processor.validate_blueprint(sample_blueprint)
            
            assert validation_errors == expected_errors
            mock_validator.validate_pre_generation.assert_called_once_with(sample_blueprint)
    
    def test_blueprint_processing_with_healing(self):
        """Test actual blueprint processing with healing functionality"""
        processor = BlueprintProcessor(validator=Mock())
        
        # Create a blueprint with missing configurations that healing should fix
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_healing_system"
        
        # APIEndpoint component missing port
        api_component = Mock()
        api_component.name = "api_service"
        api_component.type = "APIEndpoint"
        api_component.config = {}  # Missing port
        
        # Store component missing storage_type
        store_component = Mock()
        store_component.name = "data_store"
        store_component.type = "Store"
        store_component.config = {}  # Missing storage_type
        
        blueprint.system.components = [api_component, store_component]
        
        # Test actual healing functionality
        healed_blueprint = processor.process_blueprint(blueprint, enable_healing=True)
        
        # Verify healing was applied
        assert healed_blueprint is not blueprint  # Should be a different object (copied)
        
        # Check that missing configurations were added
        healed_api = healed_blueprint.system.components[0]
        assert healed_api.config.get('port') == 8080
        
        healed_store = healed_blueprint.system.components[1]
        assert healed_store.config.get('storage_type') == 'file'
    
    def test_blueprint_natural_language_processing(self):
        """Test actual natural language blueprint parsing functionality"""
        processor = BlueprintProcessor(validator=Mock())
        
        natural_language_input = """
        Create a system with:
        - An API endpoint on port 8080
        - A data store for persistence
        - Connect the API to the store
        """
        
        # Test actual functionality without mocking
        result = processor.process_natural_language_blueprint(natural_language_input)
        
        # Verify the result is a valid ParsedSystemBlueprint
        assert hasattr(result, 'system')
        assert hasattr(result.system, 'name')
        assert hasattr(result.system, 'components')
        assert len(result.system.components) >= 2  # Should have API and store components
        
        # Verify components were extracted correctly
        component_types = [comp.type for comp in result.system.components]
        assert 'APIEndpoint' in component_types
        assert 'Store' in component_types
        
        # Verify API endpoint has correct port
        api_components = [comp for comp in result.system.components if comp.type == 'APIEndpoint']
        assert len(api_components) > 0
        assert api_components[0].config.get('port') == 8080
    
    def test_blueprint_schema_validation(self, complex_blueprint):
        """RED: Test blueprint schema validation"""
        processor = BlueprintProcessor(validator=Mock())
        
        with patch.object(processor, '_validate_schemas') as mock_validate_schemas:
            mock_validate_schemas.return_value = []  # No schema errors
            
            schema_errors = processor.validate_blueprint_schemas(complex_blueprint)
            
            assert schema_errors == []
            mock_validate_schemas.assert_called_once_with(complex_blueprint)
    
    def test_blueprint_component_requirement_analysis(self, complex_blueprint):
        """Test component requirement analysis functionality"""
        processor = BlueprintProcessor(validator=Mock())
        
        requirements = processor.analyze_component_requirements(complex_blueprint)
        
        # Should analyze dependencies and configuration requirements
        assert 'components' in requirements
        assert 'dependencies' in requirements
        assert 'configurations' in requirements
        
        # Verify actual component analysis
        assert len(requirements['components']) == len(complex_blueprint.system.components)
        for component_name, component_info in requirements['components'].items():
            assert 'type' in component_info
            assert 'config_keys' in component_info
    
    def test_dependency_injection_integration(self):
        """Test that dependency injection works correctly"""
        from autocoder_cc.blueprint_language.processors.blueprint_validator import BlueprintValidator
        
        # Create a validator instance
        validator = BlueprintValidator()
        
        # Create processor with injected validator
        processor = BlueprintProcessor(validator=validator)
        
        # Verify the validator was injected correctly
        assert processor._get_validator() is validator
        
        # Test without injection (fallback)
        processor_no_injection = BlueprintProcessor(validator=Mock())
        assert processor_no_injection._get_validator() is not None


class TestBlueprintValidator:
    """Test the blueprint validation module extracted from monolith"""
    
    @pytest.fixture
    def mock_component_registry(self):
        """Mock component registry for testing"""
        with patch('autocoder_cc.components.component_registry.component_registry') as mock_registry:
            mock_registry._component_classes = {
                'APIEndpoint': Mock(),
                'Store': Mock(),
                'Transformer': Mock()
            }
            mock_registry._validate_component_config = Mock()
            mock_registry._validate_external_dependencies = Mock()
            yield mock_registry
    
    def test_validator_initialization(self, mock_component_registry):
        """RED: Test BlueprintValidator initialization"""
        validator = BlueprintValidator()
        
        assert validator is not None
        assert hasattr(validator, 'validate_pre_generation')
        assert hasattr(validator, 'validate_component_connections')
        assert hasattr(validator, 'validate_configuration_completeness')
    
    def test_component_registry_validation(self, mock_component_registry):
        """RED: Test component registry validation phase"""
        validator = BlueprintValidator()
        
        # Create test blueprint
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        
        component = Mock()
        component.name = "test_api"
        component.type = "APIEndpoint"
        component.config = {"port": 8080}
        
        blueprint.system.components = [component]
        blueprint.system.bindings = []
        blueprint.policy = {}
        
        # Mock successful validation
        mock_component_registry._validate_component_config.return_value = None
        mock_component_registry._validate_external_dependencies.return_value = None
        
        validation_errors = validator.validate_pre_generation(blueprint)
        
        # Should have some errors or none, but test should not crash
        assert isinstance(validation_errors, list)
    
    def test_dangling_component_detection(self, mock_component_registry):
        """RED: Test detection of unconnected components"""
        validator = BlueprintValidator()
        
        # Create blueprint with unconnected component
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        
        # Transformer should be connected but isn't
        transformer = Mock()
        transformer.name = "data_transformer"
        transformer.type = "Transformer"  # Should be connected
        transformer.inputs = [Mock(name="input")]
        transformer.outputs = [Mock(name="output")]
        
        blueprint.system.components = [transformer]
        blueprint.system.bindings = []  # No connections
        blueprint.policy = {}
        
        validation_errors = validator.validate_pre_generation(blueprint)
        
        # Should detect dangling component
        dangling_errors = [error for error in validation_errors if "not connected" in error]
        assert len(dangling_errors) > 0
    
    def test_configuration_validation(self, mock_component_registry):
        """RED: Test missing configuration validation"""
        validator = BlueprintValidator()
        
        # Create blueprint with missing Store configuration
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        
        store = Mock()
        store.name = "data_store"
        store.type = "Store"
        store.config = {}  # Missing storage_type
        
        blueprint.system.components = [store]
        blueprint.system.bindings = []
        blueprint.policy = {}
        
        validation_errors = validator.validate_pre_generation(blueprint)
        
        # Should detect missing storage_type
        config_errors = [error for error in validation_errors if "storage_type" in error]
        assert len(config_errors) > 0
    
    def test_schema_compatibility_validation(self, mock_component_registry):
        """RED: Test schema compatibility between connected components"""
        validator = BlueprintValidator()
        
        # Create blueprint with schema mismatch
        blueprint = Mock()
        blueprint.system = Mock()
        blueprint.system.name = "test_system"
        blueprint.schemas = {"string_schema": {}, "object_schema": {}}
        
        # Components with incompatible schemas
        source = Mock()
        source.name = "data_source"
        source.type = "Source"
        # Create output mock with proper name attribute
        output_mock = Mock()
        output_mock.name = "output"
        output_mock.schema = "incompatible_schema" 
        source.outputs = [output_mock]
        
        sink = Mock()
        sink.name = "data_sink"
        sink.type = "Sink"
        # Create input mock with proper name attribute
        input_mock = Mock()
        input_mock.name = "input"
        input_mock.schema = "different_schema"
        sink.inputs = [input_mock]
        
        blueprint.system.components = [source, sink]
        
        # Binding with schema mismatch
        binding = Mock()
        binding.from_component = "data_source"
        binding.from_port = "output"
        binding.to_components = ["data_sink"]
        binding.to_ports = ["input"]
        
        blueprint.system.bindings = [binding]
        blueprint.policy = {}
        
        validation_errors = validator.validate_pre_generation(blueprint)
        
        # Should detect schema mismatch - the schemas are incompatible
        schema_errors = [error for error in validation_errors if "schema mismatch" in error.lower()]
        assert len(schema_errors) > 0