#!/usr/bin/env python3
"""
Component Port Auto-Generator - Enterprise Roadmap v3 Phase 1
Auto-generates component port definitions based on component type and bindings
"""

from typing import Dict, Any, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import logging

from .blueprint_parser import ParsedComponent, ParsedPort
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer

# Import types only for type checking to avoid circular imports
if TYPE_CHECKING:
    from .system_blueprint_parser import ParsedBinding, ParsedSystemBlueprint


@dataclass
class ComponentTypeTemplate:
    """Template for component type port definitions"""
    default_inputs: List[ParsedPort]
    default_outputs: List[ParsedPort]
    required_inputs: Set[str]
    required_outputs: Set[str]


class ComponentPortAutoGenerator:
    """
    Auto-generates component port definitions based on type and connections.
    
    Features:
    - Component type-based default ports
    - Binding-driven port inference
    - Missing port detection and generation
    - Schema consistency validation
    """
    
    def __init__(self):
        self.structured_logger = get_logger("port_auto_generator", component="ComponentPortAutoGenerator")
        self.metrics_collector = get_metrics_collector("port_auto_generator")
        self.tracer = get_tracer("port_auto_generator")
        
        # Initialize component type templates
        self.type_templates = self._initialize_component_templates()
        
        self.structured_logger.info(
            "ComponentPortAutoGenerator initialized",
            operation="init",
            tags={"template_count": len(self.type_templates)}
        )
    
    def _initialize_component_templates(self) -> Dict[str, ComponentTypeTemplate]:
        """Initialize default port templates for component types"""
        
        templates = {}
        
        # Source components - only outputs, no inputs
        templates["Source"] = ComponentTypeTemplate(
            default_inputs=[],
            default_outputs=[
                ParsedPort(name="output", schema="common_object_schema", description="Generated data items")
            ],
            required_inputs=set(),
            required_outputs={"output"}
        )
        
        # Transformer components - require both inputs and outputs
        templates["Transformer"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Input data items")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Transformed data items")
            ],
            required_inputs={"input"},
            required_outputs={"output"}
        )
        
        # Sink components - only inputs, no outputs
        templates["Sink"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Data items to process")
            ],
            default_outputs=[],
            required_inputs={"input"},
            required_outputs=set()
        )
        
        # Store components - inputs for storage, terminal component (no outputs)
        templates["Store"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to store")
            ],
            default_outputs=[],  # No default outputs - terminal component
            required_inputs={"input"},
            required_outputs=set()  # No required outputs - terminal component
        )
        
        # APIEndpoint components - HTTP request/response
        templates["APIEndpoint"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="request", schema="APIRequestSchema", description="HTTP requests")
            ],
            default_outputs=[
                ParsedPort(name="response", schema="APIResponseSchema", description="HTTP responses")
            ],
            required_inputs={"request"},
            required_outputs={"response"}
        )
        
        # Accumulator components - multiple inputs to single output
        templates["Accumulator"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to accumulate")
            ],
            default_outputs=[
                ParsedPort(name="aggregate", schema="AggregateSchema", description="Aggregated results")
            ],
            required_inputs={"input"},
            required_outputs={"aggregate"}
        )
        
        # StreamProcessor components - stream processing
        templates["StreamProcessor"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="stream", schema="ItemSchema", description="Stream data items")
            ],
            default_outputs=[
                ParsedPort(name="processed", schema="ItemSchema", description="Processed stream items")
            ],
            required_inputs={"stream"},
            required_outputs={"processed"}
        )
        
        # Controller components - control signals
        templates["Controller"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="control", schema="SignalSchema", description="Control signals")
            ],
            default_outputs=[
                ParsedPort(name="command", schema="SignalSchema", description="Command signals")
            ],
            required_inputs={"control"},
            required_outputs={"command"}
        )
        
        # Router components - routing and dispatching
        templates["Router"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to route")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Routed items")
            ],
            required_inputs={"input"},
            required_outputs={"output"}
        )
        
        # Model components - ML model inference
        templates["Model"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="features", schema="ItemSchema", description="Feature data for inference")
            ],
            default_outputs=[
                ParsedPort(name="predictions", schema="ItemSchema", description="Model predictions")
            ],
            required_inputs={"features"},
            required_outputs={"predictions"}
        )
        
        
        # MessageBus components - message routing
        templates["MessageBus"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="messages", schema="EventSchema", description="Messages to route")
            ],
            default_outputs=[
                ParsedPort(name="routed", schema="EventSchema", description="Routed messages")
            ],
            required_inputs={"messages"},
            required_outputs={"routed"}
        )
        
        # Aggregator components - multiple inputs to single output
        templates["Aggregator"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input1", schema="ItemSchema", description="First input stream"),
                ParsedPort(name="input2", schema="ItemSchema", description="Second input stream")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Aggregated output")
            ],
            required_inputs={"input1", "input2"},
            required_outputs={"output"}
        )
        
        # Filter components - filtering and selection
        templates["Filter"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to filter")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Filtered items")
            ],
            required_inputs={"input"},
            required_outputs={"output"}
        )
        
        # EventSource components - event generation
        templates["EventSource"] = ComponentTypeTemplate(
            default_inputs=[],
            default_outputs=[
                ParsedPort(name="events", schema="EventSchema", description="Generated events")
            ],
            required_inputs=set(),
            required_outputs={"events"}
        )
        
        return templates
    
    def auto_generate_ports(self, system_blueprint: "ParsedSystemBlueprint") -> "ParsedSystemBlueprint":
        """Auto-generate missing component ports based on types and bindings"""
        
        with self.tracer.span("port_auto_generation") as span_id:
            try:
                self.structured_logger.info(
                    "Starting port auto-generation",
                    operation="auto_generate_ports",
                    tags={"component_count": len(system_blueprint.system.components)}
                )
                
                # Analyze bindings to understand required ports
                port_requirements = self._analyze_binding_requirements(system_blueprint.system.bindings)
                
                # Generate ports for each component
                components_modified = 0
                for component in system_blueprint.system.components:
                    if self._generate_component_ports(component, port_requirements):
                        components_modified += 1
                
                # Record metrics (simplified for now)
                # self.metrics_collector.record_ports_generated(components_modified)
                
                self.structured_logger.info(
                    "Port auto-generation completed",
                    operation="ports_generated",
                    tags={"components_modified": components_modified}
                )
                
                return system_blueprint
                
            except Exception as e:
                self.structured_logger.error(
                    "Port auto-generation failed",
                    error=e,
                    operation="generation_error"
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Generation error: {e}", "error")
                
                raise
    
    def _analyze_binding_requirements(self, bindings: List["ParsedBinding"]) -> Dict[str, Dict[str, Set[str]]]:
        """Analyze bindings to determine required input/output ports"""
        
        requirements = {}
        
        for binding in bindings:
            # From component needs an output port
            if binding.from_component not in requirements:
                requirements[binding.from_component] = {"inputs": set(), "outputs": set()}
            requirements[binding.from_component]["outputs"].add(binding.from_port)
            
            # To components need input ports
            for i, to_component in enumerate(binding.to_components):
                if to_component not in requirements:
                    requirements[to_component] = {"inputs": set(), "outputs": set()}
                
                # Get corresponding to_port
                to_port = binding.to_ports[i] if i < len(binding.to_ports) else "input"
                requirements[to_component]["inputs"].add(to_port)
        
        return requirements
    
    def _generate_component_ports(self, component: ParsedComponent, port_requirements: Dict[str, Dict[str, Set[str]]]) -> bool:
        """Generate missing ports for a component. Returns True if modifications were made."""
        
        component_requirements = port_requirements.get(component.name, {"inputs": set(), "outputs": set()})
        template = self.type_templates.get(component.type)
        
        if not template:
            self.structured_logger.warning(
                f"No template for component type: {component.type}",
                operation="missing_template",
                tags={"component_name": component.name, "component_type": component.type}
            )
            return False
        
        modifications_made = False
        
        # Generate missing input ports
        existing_input_names = {port.name for port in component.inputs}
        
        # Add required inputs from template
        for required_input in template.required_inputs:
            if required_input not in existing_input_names:
                # Find the template port
                template_port = next((p for p in template.default_inputs if p.name == required_input), None)
                if template_port:
                    component.inputs.append(ParsedPort(
                        name=template_port.name,
                        schema=template_port.schema,
                        required=True,
                        description=template_port.description
                    ))
                    existing_input_names.add(template_port.name)  # Update the set
                    modifications_made = True
                    self.structured_logger.debug(
                        f"Added required input port: {required_input}",
                        operation="port_added",
                        tags={"component": component.name, "port_type": "input", "port_name": required_input}
                    )
        
        # Add binding-required inputs
        for required_input in component_requirements["inputs"]:
            if required_input not in existing_input_names:
                component.inputs.append(ParsedPort(
                    name=required_input,
                    schema="ItemSchema",  # Default schema
                    required=True,
                    description=f"Auto-generated input port for binding"
                ))
                existing_input_names.add(required_input)  # Update the set
                modifications_made = True
                self.structured_logger.debug(
                    f"Added binding-required input port: {required_input}",
                    operation="port_added",
                    tags={"component": component.name, "port_type": "input", "port_name": required_input}
                )
        
        # Generate missing output ports
        existing_output_names = {port.name for port in component.outputs}
        
        # Add required outputs from template
        for required_output in template.required_outputs:
            if required_output not in existing_output_names:
                # Find the template port
                template_port = next((p for p in template.default_outputs if p.name == required_output), None)
                if template_port:
                    component.outputs.append(ParsedPort(
                        name=template_port.name,
                        schema=template_port.schema,
                        required=True,
                        description=template_port.description
                    ))
                    existing_output_names.add(template_port.name)  # Update the set
                    modifications_made = True
                    self.structured_logger.debug(
                        f"Added required output port: {required_output}",
                        operation="port_added",
                        tags={"component": component.name, "port_type": "output", "port_name": required_output}
                    )
        
        # Add binding-required outputs
        for required_output in component_requirements["outputs"]:
            if required_output not in existing_output_names:
                component.outputs.append(ParsedPort(
                    name=required_output,
                    schema="ItemSchema",  # Default schema
                    required=True,
                    description=f"Auto-generated output port for binding"
                ))
                existing_output_names.add(required_output)  # Update the set
                modifications_made = True
                self.structured_logger.debug(
                    f"Added binding-required output port: {required_output}",
                    operation="port_added",
                    tags={"component": component.name, "port_type": "output", "port_name": required_output}
                )
        
        return modifications_made
    
    def validate_component_ports(self, component: ParsedComponent) -> List[str]:
        """Validate that component has all required ports for its type"""
        
        errors = []
        template = self.type_templates.get(component.type)
        
        if not template:
            return [f"Unknown component type: {component.type}"]
        
        # Check required inputs
        existing_input_names = {port.name for port in component.inputs}
        for required_input in template.required_inputs:
            if required_input not in existing_input_names:
                errors.append(f"Missing required input port: {required_input}")
        
        # Check required outputs
        existing_output_names = {port.name for port in component.outputs}
        for required_output in template.required_outputs:
            if required_output not in existing_output_names:
                errors.append(f"Missing required output port: {required_output}")
        
        return errors
    
    def get_component_type_info(self, component_type: str) -> Optional[ComponentTypeTemplate]:
        """Get port template information for a component type"""
        return self.type_templates.get(component_type)
    
    def list_supported_component_types(self) -> List[str]:
        """Get list of supported component types with templates"""
        return list(self.type_templates.keys())


# Convenience functions
def auto_generate_component_ports(system_blueprint: "ParsedSystemBlueprint") -> "ParsedSystemBlueprint":
    """Auto-generate missing component ports based on types and bindings"""
    generator = ComponentPortAutoGenerator()
    return generator.auto_generate_ports(system_blueprint)


def validate_component_ports(component: ParsedComponent) -> List[str]:
    """Validate that component has all required ports for its type"""
    generator = ComponentPortAutoGenerator()
    return generator.validate_component_ports(component)