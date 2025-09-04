#!/usr/bin/env python3
"""
Test Type Safety Implementation - P0.8-E1 Type Safety Validation

Tests for strict typing and interface validation in component composition.
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from autocoder_cc.components.type_safety import (
    TypeSafetyValidator, TypeSafeComponentWrapper, InterfaceSpec,
    TypeValidationLevel, TypeValidationError, interface_registry
)
from autocoder_cc.components.type_safe_composition import (
    TypeSafeCompositionFactory, TypeSafeCompositionConfig
)
from autocoder_cc.components.enhanced_composition import (
    BehaviorComposer, DependencyInjector, PipelineComposer,
    CompositionPattern, CompositionStrategy, ComponentDependency
)


# Test component classes
class MockComponent:
    """Mock component for testing"""
    def __init__(self, name: str):
        self.name = name
        self.config = {}
    
    async def process(self):
        """Process method for testing"""
        pass
    
    def process_item(self, item: Any) -> Any:
        """Process item method for testing"""
        return item


class MockSource:
    """Mock source component for testing"""
    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.output_count = 0
    
    def generate_data(self) -> Dict[str, Any]:
        """Generate data method for testing"""
        self.output_count += 1
        return {"id": self.output_count, "data": f"item_{self.output_count}"}


class MockTransformer:
    """Mock transformer component for testing"""
    def __init__(self, name: str):
        self.name = name
        self.config = {}
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data method for testing"""
        return {"transformed": True, **data}


class MockSink:
    """Mock sink component for testing"""
    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.stored_items = []
    
    def store_data(self, data: Dict[str, Any]) -> None:
        """Store data method for testing"""
        self.stored_items.append(data)


class BadComponent:
    """Component that doesn't follow interface correctly"""
    def __init__(self, name: str):
        self.name = name
        # Missing config property
    
    # Missing process method
    
    def process_item(self, item: str) -> int:  # Wrong types
        """Process item with wrong signature"""
        return len(item)


@pytest.fixture
def validator():
    """Create type safety validator for testing"""
    return TypeSafetyValidator(TypeValidationLevel.STRICT)


@pytest.fixture
def composition_factory():
    """Create type-safe composition factory for testing"""
    config = TypeSafeCompositionConfig(
        validation_level=TypeValidationLevel.STRICT,
        fail_on_interface_mismatch=True,
        enable_runtime_validation=True
    )
    return TypeSafeCompositionFactory(config)


class TestTypeSafetyValidator:
    """Test type safety validator functionality"""
    
    def test_validate_component_interface_success(self, validator):
        """Test successful component interface validation"""
        component = MockComponent("test_component")
        interface_spec = interface_registry.get_interface("Component")
        
        errors = validator.validate_component_interface(component, interface_spec)
        assert len(errors) == 0, f"Expected no errors, got: {[e.error_message for e in errors]}"
    
    def test_validate_component_interface_failure(self, validator):
        """Test component interface validation with errors"""
        component = BadComponent("bad_component")
        interface_spec = interface_registry.get_interface("Component")
        
        errors = validator.validate_component_interface(component, interface_spec)
        assert len(errors) > 0, "Expected validation errors for bad component"
        
        # Check for specific errors
        error_messages = [e.error_message for e in errors]
        assert any("config" in msg for msg in error_messages), "Should detect missing config property"
        assert any("process" in msg for msg in error_messages), "Should detect missing process method"
    
    def test_validate_source_interface(self, validator):
        """Test source component interface validation"""
        component = MockSource("test_source")
        interface_spec = interface_registry.get_interface("Source")
        
        errors = validator.validate_component_interface(component, interface_spec)
        assert len(errors) == 0, f"Expected no errors for valid source, got: {[e.error_message for e in errors]}"
    
    def test_validate_transformer_interface(self, validator):
        """Test transformer component interface validation"""
        component = MockTransformer("test_transformer")
        interface_spec = interface_registry.get_interface("Transformer")
        
        errors = validator.validate_component_interface(component, interface_spec)
        assert len(errors) == 0, f"Expected no errors for valid transformer, got: {[e.error_message for e in errors]}"
    
    def test_validate_sink_interface(self, validator):
        """Test sink component interface validation"""
        component = MockSink("test_sink")
        interface_spec = interface_registry.get_interface("Sink")
        
        errors = validator.validate_component_interface(component, interface_spec)
        assert len(errors) == 0, f"Expected no errors for valid sink, got: {[e.error_message for e in errors]}"
    
    def test_runtime_type_validation(self, validator):
        """Test runtime type validation"""
        component = MockTransformer("test_transformer")
        
        # Valid call - should pass
        errors = validator.validate_runtime_types(
            component, "transform", ({"test": "data"},), {}, {"transformed": True, "test": "data"}
        )
        assert len(errors) == 0, "Valid method call should not generate errors"
        
        # Invalid call - should generate errors if strict validation is implemented
        # Note: This test depends on having proper type hints in the mock methods


class TestTypeSafeComponentWrapper:
    """Test type-safe component wrapper functionality"""
    
    def test_wrapper_creation(self, composition_factory):
        """Test creating type-safe component wrapper"""
        component = MockComponent("test_component")
        
        wrapped = composition_factory.create_type_safe_component(component, "Component")
        assert isinstance(wrapped, TypeSafeComponentWrapper)
        assert wrapped.get_wrapped_component() is component
    
    def test_wrapper_method_access(self, composition_factory):
        """Test accessing methods through wrapper"""
        component = MockComponent("test_component")
        wrapped = composition_factory.create_type_safe_component(component, "Component")
        
        # Should be able to access component properties
        assert wrapped.name == "test_component"
        assert wrapped.config == {}
        
        # Should be able to call methods
        result = wrapped.process_item("test_data")
        assert result == "test_data"
    
    def test_wrapper_interface_validation_failure(self, composition_factory):
        """Test wrapper creation with invalid component"""
        component = BadComponent("bad_component")
        
        with pytest.raises(TypeError, match="interface validation failed"):
            composition_factory.create_type_safe_component(component, "Component")
    
    def test_wrapper_with_lenient_validation(self):
        """Test wrapper with lenient validation settings"""
        config = TypeSafeCompositionConfig(
            validation_level=TypeValidationLevel.BASIC,
            fail_on_interface_mismatch=False
        )
        factory = TypeSafeCompositionFactory(config)
        
        component = BadComponent("bad_component")
        
        # Should succeed with lenient validation
        wrapped = factory.create_type_safe_component(component, "Component")
        assert isinstance(wrapped, TypeSafeComponentWrapper)


class TestTypeSafeComposition:
    """Test type-safe composition functionality"""
    
    def test_create_type_safe_pipeline(self, composition_factory):
        """Test creating type-safe pipeline"""
        source = MockSource("source")
        transformer = MockTransformer("transformer")
        sink = MockSink("sink")
        
        components = [source, transformer, sink]
        interfaces = ["Source", "Transformer", "Sink"]
        
        pipeline = composition_factory.create_type_safe_pipeline(components, interfaces)
        assert isinstance(pipeline, TypeSafeComponentWrapper)
    
    def test_compose_type_safe_behavior(self, composition_factory):
        """Test composing type-safe behaviors"""
        # Register a simple behavior
        composition_factory._type_safe_behavior_composer.get_wrapped_component().register_behavior(
            "test_behavior",
            lambda data, context: {"processed": True, **data}
        )
        
        behavior_spec = {
            "type": "sequential",
            "behaviors": ["test_behavior"]
        }
        
        composed = composition_factory.compose_type_safe_behavior(behavior_spec)
        assert hasattr(composed, "execute")
    
    def test_create_type_safe_system(self, composition_factory):
        """Test creating type-safe system"""
        # Create components
        source = MockSource("source")
        transformer = MockTransformer("transformer")
        sink = MockSink("sink")
        
        components = {
            "source": source,
            "transformer": transformer,
            "sink": sink
        }
        
        interfaces = {
            "source": "Source",
            "transformer": "Transformer", 
            "sink": "Sink"
        }
        
        # Create composition pattern
        pattern = CompositionPattern(
            name="test_pipeline",
            strategy=CompositionStrategy.SEQUENTIAL,
            components=["source", "transformer", "sink"],
            dependencies=[
                ComponentDependency("source", "transformer", "data_flow"),
                ComponentDependency("transformer", "sink", "data_flow")
            ]
        )
        
        system = composition_factory.create_type_safe_system(pattern, components, interfaces)
        assert len(system) == 3
        assert all(isinstance(comp, (TypeSafeComponentWrapper, MockSource, MockTransformer, MockSink)) 
                  for comp in system.values())
    
    def test_validate_system_types(self, composition_factory):
        """Test system-wide type validation"""
        components = {
            "good_source": MockSource("good_source"),
            "bad_component": BadComponent("bad_component"),
            "good_sink": MockSink("good_sink")
        }
        
        interfaces = {
            "good_source": "Source",
            "bad_component": "Component",
            "good_sink": "Sink"
        }
        
        validation_results = composition_factory.validate_system_types(components, interfaces)
        
        assert len(validation_results) == 3
        assert len(validation_results["good_source"]) == 0, "Good source should have no errors"
        assert len(validation_results["bad_component"]) > 0, "Bad component should have errors"
        assert len(validation_results["good_sink"]) == 0, "Good sink should have no errors"


class TestInterfaceRegistry:
    """Test interface registry functionality"""
    
    def test_register_custom_interface(self):
        """Test registering custom interface"""
        custom_interface = InterfaceSpec(
            name="CustomInterface",
            methods={
                "custom_method": {
                    "parameters": {"param": str},
                    "return_type": bool
                }
            },
            properties={
                "custom_property": int
            }
        )
        
        interface_registry.register_interface(custom_interface)
        
        retrieved = interface_registry.get_interface("CustomInterface")
        assert retrieved is not None
        assert retrieved.name == "CustomInterface"
        assert "custom_method" in retrieved.methods
    
    def test_register_component_interface_association(self):
        """Test associating component with interface"""
        interface_registry.register_component_interface("test_component", "Component")
        
        interface_spec = interface_registry.get_component_interface("test_component")
        assert interface_spec is not None
        assert interface_spec.name == "Component"
    
    def test_list_interfaces(self):
        """Test listing all interfaces"""
        interfaces = interface_registry.list_interfaces()
        
        # Should include built-in interfaces
        assert "Component" in interfaces
        assert "Source" in interfaces
        assert "Transformer" in interfaces
        assert "Sink" in interfaces


@pytest.mark.asyncio
class TestAsyncTypeValidation:
    """Test async method type validation"""
    
    @pytest.mark.asyncio
    async def test_async_method_validation(self, composition_factory):
        """Test type validation for async methods"""
        component = MockComponent("async_test")
        wrapped = composition_factory.create_type_safe_component(component, "Component")
        
        # Should be able to call async methods
        await wrapped.process()
        
        # The wrapper should handle both sync and async methods correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])