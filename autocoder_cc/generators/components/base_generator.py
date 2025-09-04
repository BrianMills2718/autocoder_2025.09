#!/usr/bin/env python3
"""
Base Component Generator
Provides common functionality for all component generators.
Uses standalone imports - no autocoder framework dependencies.
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from autocoder_cc.generation.standalone_import_resolver import StandaloneImportResolver
from autocoder_cc.components.component_registry import component_registry
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors


class BaseComponentGenerator(ABC):
    """
    Base class for component generators.
    Ensures generated components are standalone and portable.
    """
    
    def __init__(self, use_standalone: bool = True):
        """
        Args:
            use_standalone: If True, generate fully standalone components
        """
        self.use_standalone = use_standalone
        self.import_resolver = StandaloneImportResolver(use_local_base=use_standalone)
        self.error_handler = ConsistentErrorHandler("BaseComponentGenerator")
    
    @abstractmethod
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """Generate component implementation."""
        pass
    
    def _generate_imports(self, 
                         component_type: str,
                         capabilities: Optional[List[str]] = None,
                         additional_imports: Optional[List[str]] = None) -> str:
        """Generate import statements for a component."""
        # Get resolved imports
        imports = self.import_resolver.resolve_imports(
            component_type=component_type,
            capabilities=capabilities,
            inline_base=not self.use_standalone
        )
        
        # Add any additional imports
        if additional_imports:
            imports.extend(additional_imports)
        
        # If not using standalone, add inline base class
        if not self.use_standalone:
            imports.append("")
            imports.append("# Inline base class for standalone operation")
        
        return "\n".join(imports)
    
    def _generate_base_class(self) -> str:
        """Generate base class definition if needed."""
        if not self.use_standalone:
            return self.import_resolver.generate_inline_base_class()
        return ""
    
    def _generate_stream_helpers(self) -> str:
        """Generate stream helper functions if needed."""
        if not self.use_standalone:
            return self.import_resolver.generate_stream_helpers()
        return ""
    
    def _format_config(self, config: Dict[str, Any]) -> str:
        """Format configuration dictionary as Python code."""
        if not config:
            return "{}"
        
        items = []
        for key, value in config.items():
            if isinstance(value, str):
                items.append(f'"{key}": "{value}"')
            elif isinstance(value, (list, dict)):
                items.append(f'"{key}": {repr(value)}')
            else:
                items.append(f'"{key}": {value}')
        
        return "{\n        " + ",\n        ".join(items) + "\n    }"
    
    def _generate_component_class(self,
                                 name: str,
                                 component_type: str,
                                 config: Dict[str, Any],
                                 process_implementation: str,
                                 additional_methods: Optional[str] = None) -> str:
        """Generate the component class definition."""
        config_str = self._format_config(config)
        
        class_def = f'''class Generated{component_type}_{name}(Component):
    """
    Generated {component_type} component: {name}
    Standalone implementation - no external dependencies.
    """
    
    def __init__(self, name: str = "{name}", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {config_str})
        
        # Component-specific initialization
        self._setup_component()
    
    def _setup_component(self):
        """Initialize component-specific resources."""
        # Register component with ComponentRegistry for validation
        try:
            # Extract component type from class name more reliably
            class_name = self.__class__.__name__
            if 'Source' in class_name:
                component_type = 'Source'
            elif 'Transformer' in class_name:
                component_type = 'Transformer'
            elif 'Sink' in class_name:
                component_type = 'Sink'
            elif 'Store' in class_name:
                component_type = 'Store'
            elif 'APIEndpoint' in class_name:
                component_type = 'APIEndpoint'
            else:
                # Fallback - try to extract from class name
                component_type = class_name.split('_')[0].replace('Generated', '')
            
            # Attempt registry validation
            registry_component = component_registry.create_component(
                component_type=component_type,
                name=self.name,
                config=self.config
            )
            
            # If successful, store registry reference for validation
            self._registry_component = registry_component
            self.logger.info(f"✅ ComponentRegistry validation passed for {{self.name}}")
            
        except Exception as e:
            # FAIL-HARD: All components must pass registry validation regardless of mode
            self.logger.error(f"❌ ComponentRegistry validation FAILED for {{self.name}}: {{e}}")
            self.logger.error("🚫 FAIL-HARD: Component validation is mandatory for all components")
            self.logger.error("   No development mode exceptions - registry validation is required")
            raise RuntimeError(f"Component {{self.name}} failed registry validation: {{e}}") from e

{process_implementation}'''
        
        if additional_methods:
            class_def += f"\n{additional_methods}"
        
        return class_def
    
    def _generate_main_block(self, name: str, component_type: str) -> str:
        """Generate main block for testing the component standalone."""
        return f'''

if __name__ == "__main__":
    # Test the component standalone
    async def test_component():
        component = Generated{component_type}_{name}()
        await component.setup()
        
        # Run for a short time
        try:
            await asyncio.wait_for(component.process(), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        
        await component.cleanup()
        
        # Print health status
        health = await component.health_check()
        print(f"Component health: {{health}}")
    
    # Run the test
    asyncio.run(test_component())
'''