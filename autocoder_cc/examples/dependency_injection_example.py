#!/usr/bin/env python3
"""
Example showing how to refactor circular import issues using dependency injection.

BEFORE (with circular import workaround):
```python
def some_method(self):
    # Import inside function to avoid circular import
    from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
    from autocoder_cc.components.component_registry import ComponentRegistry
    
    generator = LLMComponentGenerator()
    registry = ComponentRegistry()
    return generator.generate_component(...)
```

AFTER (with dependency injection):
```python
def some_method(self):
    # Clean dependency injection - no imports needed
    generator = inject(LLMComponentGeneratorProtocol)
    registry = inject(ComponentRegistryProtocol)
    return generator.generate_component(...)
```
"""

from typing import Dict, Any
from autocoder_cc.core.dependency_injection import inject
from autocoder_cc.interfaces.generators import LLMComponentGeneratorProtocol
from autocoder_cc.interfaces.components import ComponentRegistryProtocol
from autocoder_cc.observability.structured_logging import get_logger

class ExampleService:
    """
    Example service demonstrating dependency injection usage.
    This eliminates the need for imports inside functions.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def generate_component_example(self, component_type: str, config: Dict[str, Any]) -> str:
        """
        Example method showing clean dependency injection usage.
        No imports inside functions - dependencies resolved at runtime.
        """
        # Clean dependency injection - services resolved lazily
        llm_generator = inject(LLMComponentGeneratorProtocol)
        component_registry = inject(ComponentRegistryProtocol)
        
        self.logger.info(f"Generating {component_type} component using dependency injection")
        
        # Use the injected services
        try:
            # Check if component type is registered
            registered_components = component_registry.list_components()
            if component_type not in registered_components:
                self.logger.warning(f"Component type {component_type} not registered")
            
            # Generate component using LLM generator
            component_code = llm_generator.generate_component_implementation(
                component_type=component_type,
                system_requirements=config
            )
            
            self.logger.info(f"Successfully generated {component_type} component")
            return component_code
            
        except Exception as e:
            self.logger.error(f"Failed to generate component: {e}")
            raise
    
    def validate_and_heal_example(self, component_code: str, component_type: str) -> str:
        """
        Example method showing validation + healing integration.
        Demonstrates how services can depend on each other without circular imports.
        """
        from autocoder_cc.interfaces.generators import HealingIntegrationProtocol
        
        # Inject the healing integration service
        healing_service = inject(HealingIntegrationProtocol)
        
        self.logger.info(f"Validating and healing {component_type} component")
        
        # Use the healing integration service
        healed_code, success, issues = healing_service.validate_and_heal(
            component_code, component_type
        )
        
        if success:
            self.logger.info("Component validation passed")
        else:
            self.logger.warning(f"Component validation issues: {issues}")
        
        return healed_code

# Example of decorator-based service registration
from autocoder_cc.core.dependency_injection import injectable

@injectable(interface=type, singleton=True)
class ExampleSingletonService:
    """Example of automatically registered singleton service"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("ExampleSingletonService initialized as singleton")
    
    def do_something(self):
        return "Singleton service response"

def demonstrate_dependency_injection():
    """
    Demonstrate the dependency injection system in action.
    """
    logger = get_logger(__name__)
    
    logger.info("🚀 Demonstrating Dependency Injection System")
    
    # Initialize the service registry (registers all core services)
    from autocoder_cc.core.service_registry import register_core_services
    register_core_services()
    
    # Create example service
    example_service = ExampleService()
    
    # Test component generation with dependency injection
    try:
        config = {
            "name": "test_component",
            "type": "api_endpoint"
        }
        
        component_code = example_service.generate_component_example("api_endpoint", config)
        logger.info("✅ Dependency injection working - component generated")
        
    except Exception as e:
        logger.error(f"❌ Dependency injection failed: {e}")
    
    logger.info("✅ Dependency injection demonstration complete")

if __name__ == "__main__":
    demonstrate_dependency_injection()