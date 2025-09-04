"""Component type registry and detection system."""
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from autocoder_cc.observability import get_logger

@dataclass
class ComponentTypeSpec:
    """Specification for a component type."""
    name: str
    requires_inputs: bool
    requires_outputs: bool
    base_class: str
    validation_rules: Dict[str, Any]

# Component type registry with specifications
COMPONENT_TYPE_REGISTRY = {
    'Source': ComponentTypeSpec(
        name='Source',
        requires_inputs=False,
        requires_outputs=True,
        base_class='autocoder_cc.components.primitives.base.Source',
        validation_rules={'must_have_generate': True}
    ),
    'Sink': ComponentTypeSpec(
        name='Sink',
        requires_inputs=True,
        requires_outputs=False,
        base_class='autocoder_cc.components.primitives.base.Sink',
        validation_rules={'must_have_consume': True}
    ),
    'Transformer': ComponentTypeSpec(
        name='Transformer',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.primitives.base.Transformer',
        validation_rules={'must_have_transform': True}
    ),
    'Store': ComponentTypeSpec(
        name='Store',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.primitives.base.Store',
        validation_rules={'must_have_store_retrieve': True}
    ),
    'Controller': ComponentTypeSpec(
        name='Controller',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.primitives.base.Controller',
        validation_rules={'must_have_process': True}
    ),
    'APIEndpoint': ComponentTypeSpec(
        name='APIEndpoint',
        requires_inputs=False,
        requires_outputs=True,
        base_class='autocoder_cc.components.api_endpoint.APIEndpoint',
        validation_rules={'must_have_routes': True}
    ),
    'WebSocket': ComponentTypeSpec(
        name='WebSocket',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.websocket.WebSocket',
        validation_rules={'must_have_handlers': True}
    ),
    'StreamProcessor': ComponentTypeSpec(
        name='StreamProcessor',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.stream_processor.StreamProcessor',
        validation_rules={'must_have_process_stream': True}
    ),
    'Model': ComponentTypeSpec(
        name='Model',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.model.Model',
        validation_rules={'must_have_predict': True}
    ),
    'Router': ComponentTypeSpec(
        name='Router',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.router.Router',
        validation_rules={'must_have_route': True}
    ),
    'Aggregator': ComponentTypeSpec(
        name='Aggregator',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.aggregator.Aggregator',
        validation_rules={'must_have_aggregate': True}
    ),
    'Filter': ComponentTypeSpec(
        name='Filter',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.filter.Filter',
        validation_rules={'must_have_filter': True}
    ),
    'Accumulator': ComponentTypeSpec(
        name='Accumulator',
        requires_inputs=True,
        requires_outputs=True,
        base_class='autocoder_cc.components.accumulator.Accumulator',
        validation_rules={'must_have_accumulate': True}
    )
}

class ComponentTypeDetector:
    """Detect and validate component types."""
    
    def __init__(self):
        self.logger = get_logger("ComponentTypeDetector")
        self.registry = COMPONENT_TYPE_REGISTRY
    
    def detect_type(self, component_spec: Dict[str, Any]) -> Optional[str]:
        """Detect component type from specification.
        
        Args:
            component_spec: Component specification dictionary
            
        Returns:
            Component type name or None if cannot detect
        """
        # Method 1: Explicit type field
        if 'type' in component_spec:
            comp_type = component_spec['type']
            if comp_type in self.registry:
                self.logger.info(f"Detected type '{comp_type}' from explicit field")
                return comp_type
            else:
                self.logger.warning(f"Unknown type '{comp_type}' in specification")
        
        # Method 2: Infer from port configuration
        has_inputs = bool(component_spec.get('inputs'))
        has_outputs = bool(component_spec.get('outputs'))
        
        if not has_inputs and has_outputs:
            self.logger.info("Inferred type 'Source' from port configuration")
            return 'Source'
        elif has_inputs and not has_outputs:
            self.logger.info("Inferred type 'Sink' from port configuration")
            return 'Sink'
        elif has_inputs and has_outputs:
            # Need more context to determine specific transformer type
            return self._infer_transformer_type(component_spec)
        
        self.logger.error("Could not detect component type")
        return None
    
    def _infer_transformer_type(self, spec: Dict[str, Any]) -> str:
        """Infer specific transformer type from specification."""
        name = spec.get('name', '').lower()
        description = spec.get('description', '').lower()
        
        # Pattern matching on name/description
        if 'filter' in name or 'filter' in description:
            return 'Filter'
        elif 'route' in name or 'routing' in description:
            return 'Router'
        elif 'aggregate' in name or 'aggregat' in description:
            return 'Aggregator'
        elif 'accumulate' in name or 'accumul' in description:
            return 'Accumulator'
        elif 'model' in name or 'predict' in description:
            return 'Model'
        elif 'control' in name or 'orchestrat' in description:
            return 'Controller'
        elif 'store' in name or 'storage' in description:
            return 'Store'
        elif 'stream' in name or 'streaming' in description:
            return 'StreamProcessor'
        else:
            # Default transformer
            return 'Transformer'
    
    def validate_type(self, component_type: str, component_code: str) -> bool:
        """Validate component code matches its type requirements.
        
        Args:
            component_type: The component type to validate against
            component_code: The component source code
            
        Returns:
            True if validation passes
        """
        if component_type not in self.registry:
            self.logger.error(f"Unknown component type: {component_type}")
            return False
        
        spec = self.registry[component_type]
        
        # Check inheritance
        if spec.base_class not in component_code:
            self.logger.error(f"Component does not inherit from {spec.base_class}")
            return False
        
        # Check required methods based on validation rules
        for rule, value in spec.validation_rules.items():
            if rule == 'must_have_generate' and value:
                if 'def generate' not in component_code and 'async def generate' not in component_code:
                    self.logger.error("Source component missing generate method")
                    return False
            elif rule == 'must_have_consume' and value:
                if 'def consume' not in component_code and 'async def consume' not in component_code:
                    self.logger.error("Sink component missing consume method")
                    return False
            elif rule == 'must_have_transform' and value:
                if 'def transform' not in component_code and 'async def transform' not in component_code:
                    self.logger.error("Transformer component missing transform method")
                    return False
        
        self.logger.info(f"Component type '{component_type}' validation passed")
        return True

    def get_valid_types(self) -> Set[str]:
        """Get set of all valid component types."""
        return set(self.registry.keys())