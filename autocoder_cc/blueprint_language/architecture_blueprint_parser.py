#!/usr/bin/env python3
"""
Architecture Blueprint Parser
Parses pure architectural design specifications without runtime or deployment concerns
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re

from .blueprint_parser import ParsedBlueprint, ParsedComponent, ParsedPort, ParsedConstraint, ParsedResource, ValidationError

@dataclass
class ArchitecturalComponent:
    """Parsed architectural component (no runtime specifics)"""
    name: str
    type: str
    description: Optional[str] = None
    processing_mode: str = "batch"
    inputs: List[ParsedPort] = field(default_factory=list)
    outputs: List[ParsedPort] = field(default_factory=list)
    properties: List[ParsedConstraint] = field(default_factory=list)
    contracts: List[ParsedConstraint] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    architectural_config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    implementation: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    quality_attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ArchitecturalBinding:
    """Parsed architectural binding (explicit connections only)"""
    from_component: str
    from_port: str
    to_component: str  # Single component (no dot notation)
    to_port: str
    transformation: Optional[str] = None
    condition: Optional[str] = None
    qos_requirements: Dict[str, Any] = field(default_factory=dict)
    fan_out_targets: List[Dict[str, str]] = field(default_factory=list)  # For fan-out scenarios

@dataclass
class ArchitecturalPatterns:
    """Parsed architectural patterns and constraints"""
    style: str = "microservices"
    patterns: List[str] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    capability_tiers: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ArchitecturalSystem:
    """Complete architectural system definition"""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    components: List[ArchitecturalComponent] = field(default_factory=list)
    bindings: List[ArchitecturalBinding] = field(default_factory=list)
    patterns: ArchitecturalPatterns = field(default_factory=ArchitecturalPatterns)

@dataclass
class ArchitecturalBlueprint:
    """Complete parsed architectural blueprint"""
    system: ArchitecturalSystem
    metadata: Dict[str, Any] = field(default_factory=dict)
    schemas: Dict[str, Any] = field(default_factory=dict)
    policy: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    raw_blueprint: Dict[str, Any] = field(default_factory=dict)

class ArchitectureBlueprintParser:
    """
    Parses architectural blueprints containing only pure design specifications
    No runtime configuration, deployment settings, or environment-specific values
    """
    
    def __init__(self, schema_file: Optional[Path] = None):
        """Initialize parser with architecture schema"""
        self.schema_file = schema_file or Path(__file__).parent.parent.parent / "schemas" / "architecture_blueprint.schema.yaml"
        self.validation_errors: List[ValidationError] = []
        
    def parse_file(self, architecture_file: Path) -> ArchitecturalBlueprint:
        """Parse an architectural blueprint file"""
        self.validation_errors.clear()
        
        try:
            with open(architecture_file, 'r') as f:
                raw_blueprint = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML from {architecture_file}: {e}")
        
        # Validate basic structure
        self._validate_architecture_structure(raw_blueprint)
        
        # Parse into structured objects
        blueprint = self._parse_architecture_blueprint(raw_blueprint)
        blueprint.source_file = str(architecture_file)
        blueprint.raw_blueprint = raw_blueprint
        
        # Perform architectural validation
        self._validate_architecture_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Architecture blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def parse_string(self, architecture_yaml: str) -> ArchitecturalBlueprint:
        """Parse architectural blueprint from YAML string"""
        self.validation_errors.clear()
        
        try:
            raw_blueprint = yaml.safe_load(architecture_yaml)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML string: {e}")
        
        # Validate and parse
        self._validate_architecture_structure(raw_blueprint)
        blueprint = self._parse_architecture_blueprint(raw_blueprint)
        blueprint.raw_blueprint = raw_blueprint
        
        self._validate_architecture_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Architecture blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def _validate_architecture_structure(self, blueprint: Dict[str, Any]) -> None:
        """Validate architectural blueprint basic structure"""
        
        # Validate schema version
        if 'schema_version' not in blueprint:
            self.validation_errors.append(
                ValidationError("root", "Missing required 'schema_version' field")
            )
        
        if 'system' not in blueprint:
            self.validation_errors.append(
                ValidationError("root", "Missing required 'system' section")
            )
            return
        
        system = blueprint['system']
        
        # Required system fields
        required_fields = ['name', 'components', 'bindings']
        for field in required_fields:
            if field not in system:
                self.validation_errors.append(
                    ValidationError(f"system.{field}", f"Missing required field '{field}'")
                )
        
        # System name validation
        name = system.get('name', '')
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            self.validation_errors.append(
                ValidationError(
                    "system.name",
                    f"System name '{name}' must be snake_case (lowercase letters, numbers, underscores)"
                )
            )
        
        # Components validation
        components = system.get('components', [])
        if not isinstance(components, list) or len(components) == 0:
            self.validation_errors.append(
                ValidationError("system.components", "System must have at least one component")
            )
        
        # Bindings validation
        bindings = system.get('bindings', [])
        if not isinstance(bindings, list):
            self.validation_errors.append(
                ValidationError("system.bindings", "Bindings must be an array")
            )
        
        # Validate no deployment/runtime configuration present
        self._validate_no_deployment_config(blueprint)
    
    def _validate_no_deployment_config(self, blueprint: Dict[str, Any]) -> None:
        """Ensure no deployment or runtime configuration is present"""
        
        # Check for deployment configuration in root
        forbidden_root_fields = ['deployment', 'runtime', 'environment', 'component_overrides']
        for field in forbidden_root_fields:
            if field in blueprint:
                self.validation_errors.append(
                    ValidationError(
                        f"root.{field}",
                        f"Deployment/runtime field '{field}' not allowed in architectural blueprint"
                    )
                )
        
        # Check for runtime configuration in system
        system = blueprint.get('system', {})
        forbidden_system_fields = ['configuration', 'deployment', 'validation']
        for field in forbidden_system_fields:
            if field in system:
                self.validation_errors.append(
                    ValidationError(
                        f"system.{field}",
                        f"Runtime field '{field}' not allowed in architectural blueprint"
                    )
                )
        
        # Check for runtime configuration in components
        components = system.get('components', [])
        for i, component in enumerate(components):
            if isinstance(component, dict):
                forbidden_component_fields = ['configuration', 'resources', 'observability']
                for field in forbidden_component_fields:
                    if field in component:
                        self.validation_errors.append(
                            ValidationError(
                                f"system.components[{i}].{field}",
                                f"Runtime field '{field}' not allowed in architectural component"
                            )
                        )
    
    def _parse_architecture_blueprint(self, raw: Dict[str, Any]) -> ArchitecturalBlueprint:
        """Parse raw YAML into structured architectural blueprint"""
        
        system_data = raw.get('system', {})
        
        # Parse architectural patterns
        patterns_data = system_data.get('patterns', {})
        patterns = ArchitecturalPatterns(
            style=patterns_data.get('style', 'microservices'),
            patterns=patterns_data.get('patterns', []),
            constraints=patterns_data.get('constraints', []),
            capability_tiers=patterns_data.get('capability_tiers', [])
        )
        
        # Parse components
        components = []
        for comp_data in system_data.get('components', []):
            component = self._parse_architectural_component(comp_data)
            components.append(component)
        
        # Parse bindings (explicit format only)
        bindings = []
        for binding_data in system_data.get('bindings', []):
            binding = self._parse_architectural_binding(binding_data)
            bindings.append(binding)
        
        # Create architectural system
        system = ArchitecturalSystem(
            name=system_data.get('name', ''),
            description=system_data.get('description'),
            version=system_data.get('version', '1.0.0'),
            components=components,
            bindings=bindings,
            patterns=patterns
        )
        
        # Create architectural blueprint
        blueprint = ArchitecturalBlueprint(
            system=system,
            metadata=raw.get('metadata', {}),
            schemas=raw.get('schemas', {}),
            policy=raw.get('policy', {})
        )
        
        return blueprint
    
    def _parse_architectural_component(self, comp_data: Dict[str, Any]) -> ArchitecturalComponent:
        """Parse an architectural component"""
        
        component = ArchitecturalComponent(
            name=comp_data.get('name', ''),
            type=comp_data.get('type', ''),
            description=comp_data.get('description'),
            processing_mode=comp_data.get('processing_mode', 'batch'),
            resource_requirements=comp_data.get('resource_requirements', {}),
            architectural_config=comp_data.get('architectural_config', {}),
            dependencies=comp_data.get('dependencies', []),
            implementation=comp_data.get('implementation', {}),
            security=comp_data.get('security', {}),
            quality_attributes=comp_data.get('quality_attributes', {})
        )
        
        # Parse input ports
        for input_data in comp_data.get('inputs', []):
            port = ParsedPort(
                name=input_data.get('name', ''),
                schema=input_data.get('schema', ''),
                required=input_data.get('required', True),
                description=input_data.get('description')
            )
            component.inputs.append(port)
        
        # Parse output ports
        for output_data in comp_data.get('outputs', []):
            port = ParsedPort(
                name=output_data.get('name', ''),
                schema=output_data.get('schema', ''),
                required=output_data.get('required', True),
                description=output_data.get('description')
            )
            component.outputs.append(port)
        
        # Parse property constraints
        for prop_data in comp_data.get('properties', []):
            constraint = ParsedConstraint(
                expression=prop_data.get('constraint', ''),
                description=prop_data.get('description', ''),
                severity=prop_data.get('severity', 'error')
            )
            component.properties.append(constraint)
        
        # Parse contract constraints
        for contract_data in comp_data.get('contracts', []):
            constraint = ParsedConstraint(
                expression=contract_data.get('expression', ''),
                description=contract_data.get('description', ''),
                severity='error'
            )
            component.contracts.append(constraint)
        
        return component
    
    def _parse_architectural_binding(self, binding_data: Dict[str, Any]) -> ArchitecturalBinding:
        """Parse an architectural binding (explicit format only)"""
        
        # Validate explicit format (no dot notation)
        from_component = binding_data.get('from_component', '')
        from_port = binding_data.get('from_port', '')
        to_component = binding_data.get('to_component', '')
        to_port = binding_data.get('to_port', '')
        
        # Validate required fields
        if not from_component:
            self.validation_errors.append(
                ValidationError("binding.from_component", "Missing required 'from_component' field")
            )
        
        if not from_port:
            self.validation_errors.append(
                ValidationError("binding.from_port", "Missing required 'from_port' field")
            )
        
        # Handle single target or fan-out
        fan_out_targets = []
        if isinstance(to_component, list) and isinstance(to_port, list):
            # Fan-out scenario
            if len(to_component) != len(to_port):
                self.validation_errors.append(
                    ValidationError("binding.to", "to_component and to_port arrays must have same length")
                )
            else:
                for i, (comp, port) in enumerate(zip(to_component, to_port)):
                    if i == 0:
                        # Primary target
                        to_component = comp
                        to_port = port
                    else:
                        # Additional fan-out targets
                        fan_out_targets.append({'component': comp, 'port': port})
        elif isinstance(to_component, str) and isinstance(to_port, str):
            # Single target
            pass
        else:
            self.validation_errors.append(
                ValidationError("binding.to", "to_component and to_port must both be strings or both be arrays")
            )
        
        # Validate component and port names
        if not re.match(r'^[a-z][a-z0-9_]*$', from_component):
            self.validation_errors.append(
                ValidationError("binding.from_component", f"Invalid component name: '{from_component}'")
            )
        
        if not re.match(r'^[a-z][a-z0-9_]*$', from_port):
            self.validation_errors.append(
                ValidationError("binding.from_port", f"Invalid port name: '{from_port}'")
            )
        
        if isinstance(to_component, str) and not re.match(r'^[a-z][a-z0-9_]*$', to_component):
            self.validation_errors.append(
                ValidationError("binding.to_component", f"Invalid component name: '{to_component}'")
            )
        
        if isinstance(to_port, str) and not re.match(r'^[a-z][a-z0-9_]*$', to_port):
            self.validation_errors.append(
                ValidationError("binding.to_port", f"Invalid port name: '{to_port}'")
            )
        
        return ArchitecturalBinding(
            from_component=from_component,
            from_port=from_port,
            to_component=to_component if isinstance(to_component, str) else '',
            to_port=to_port if isinstance(to_port, str) else '',
            transformation=binding_data.get('transformation'),
            condition=binding_data.get('condition'),
            qos_requirements=binding_data.get('qos_requirements', {}),
            fan_out_targets=fan_out_targets
        )
    
    def _validate_architecture_semantics(self, blueprint: ArchitecturalBlueprint) -> None:
        """Perform comprehensive architectural validation"""
        
        system = blueprint.system
        
        # 1. Validate component names are unique
        self._validate_unique_component_names(system.components)
        
        # 2. Validate binding references exist
        self._validate_binding_references(system.components, system.bindings)
        
        # 3. Validate schema compatibility
        self._validate_schema_compatibility(system.components, system.bindings, blueprint.schemas)
        
        # 4. Validate architectural patterns
        self._validate_architectural_patterns(system.patterns)
        
        # 5. Validate security requirements
        self._validate_security_requirements(system.components)
        
        # 6. Validate quality attributes
        self._validate_quality_attributes(system.components)
    
    def _validate_unique_component_names(self, components: List[ArchitecturalComponent]) -> None:
        """Validate all component names are unique"""
        
        component_names = [comp.name for comp in components]
        duplicates = set()
        seen = set()
        
        for name in component_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        
        for duplicate in duplicates:
            self.validation_errors.append(
                ValidationError(
                    "system.components",
                    f"Duplicate component name: '{duplicate}'"
                )
            )
    
    def _validate_binding_references(self, components: List[ArchitecturalComponent], 
                                   bindings: List[ArchitecturalBinding]) -> None:
        """Validate all binding references point to existing components and ports"""
        
        # Build component and port lookup
        component_map = {comp.name: comp for comp in components}
        
        for binding in bindings:
            # Validate from component
            if binding.from_component not in component_map:
                self.validation_errors.append(
                    ValidationError(
                        "binding.from_component",
                        f"Unknown component: '{binding.from_component}'"
                    )
                )
            else:
                # Validate from port
                from_comp = component_map[binding.from_component]
                output_port_names = [port.name for port in from_comp.outputs]
                if binding.from_port not in output_port_names:
                    self.validation_errors.append(
                        ValidationError(
                            "binding.from_port",
                            f"Component '{binding.from_component}' has no output port '{binding.from_port}'. Available: {output_port_names}"
                        )
                    )
            
            # Validate to component
            if binding.to_component not in component_map:
                self.validation_errors.append(
                    ValidationError(
                        "binding.to_component",
                        f"Unknown component: '{binding.to_component}'"
                    )
                )
            else:
                # Validate to port
                to_comp = component_map[binding.to_component]
                input_port_names = [port.name for port in to_comp.inputs]
                if binding.to_port not in input_port_names:
                    self.validation_errors.append(
                        ValidationError(
                            "binding.to_port",
                            f"Component '{binding.to_component}' has no input port '{binding.to_port}'. Available: {input_port_names}"
                        )
                    )
            
            # Validate fan-out targets
            for target in binding.fan_out_targets:
                target_comp = target.get('component', '')
                target_port = target.get('port', '')
                
                if target_comp not in component_map:
                    self.validation_errors.append(
                        ValidationError(
                            "binding.fan_out_targets",
                            f"Unknown fan-out target component: '{target_comp}'"
                        )
                    )
                else:
                    target_comp_obj = component_map[target_comp]
                    target_input_ports = [port.name for port in target_comp_obj.inputs]
                    if target_port not in target_input_ports:
                        self.validation_errors.append(
                            ValidationError(
                                "binding.fan_out_targets",
                                f"Component '{target_comp}' has no input port '{target_port}'. Available: {target_input_ports}"
                            )
                        )
    
    def _validate_schema_compatibility(self, components: List[ArchitecturalComponent], 
                                     bindings: List[ArchitecturalBinding], 
                                     schemas: Dict[str, Any]) -> None:
        """Validate schema compatibility between connected components"""
        
        component_map = {comp.name: comp for comp in components}
        
        for binding in bindings:
            # Skip if components don't exist (caught by reference validation)
            if binding.from_component not in component_map or binding.to_component not in component_map:
                continue
            
            from_comp = component_map[binding.from_component]
            to_comp = component_map[binding.to_component]
            
            # Find output port schema
            from_port_schema = None
            for port in from_comp.outputs:
                if port.name == binding.from_port:
                    from_port_schema = port.schema
                    break
            
            # Find input port schema
            to_port_schema = None
            for port in to_comp.inputs:
                if port.name == binding.to_port:
                    to_port_schema = port.schema
                    break
            
            if from_port_schema and to_port_schema:
                # Check schema compatibility
                if from_port_schema != to_port_schema:
                    # If there's a transformation, schema mismatch is allowed
                    if not binding.transformation:
                        # Check if this is an auto-convertible schema mismatch
                        if not self._can_auto_convert_schemas(from_port_schema, to_port_schema):
                            self.validation_errors.append(
                                ValidationError(
                                    "binding.schema_compatibility",
                                    f"Schema mismatch without transformation: {binding.from_component}.{binding.from_port} ({from_port_schema}) → {binding.to_component}.{binding.to_port} ({to_port_schema})"
                                )
                            )
    
    def _can_auto_convert_schemas(self, from_schema: str, to_schema: str) -> bool:
        """Check if schema types can be automatically converted"""
        
        # Compatible conversions that don't require explicit transformation
        compatible_pairs = [
            ('common_array_schema', 'common_object_schema'),
            ('common_object_schema', 'common_array_schema'),
            ('common_string_schema', 'common_object_schema'),
            ('common_number_schema', 'common_object_schema'),
            ('common_integer_schema', 'common_number_schema'),
            ('common_boolean_schema', 'common_object_schema'),
            ('object', 'common_object_schema'),
            ('array', 'common_array_schema'),
            ('string', 'common_string_schema'),
            ('number', 'common_number_schema'),
            ('integer', 'common_integer_schema'),
            ('boolean', 'common_boolean_schema'),
        ]
        
        return (from_schema, to_schema) in compatible_pairs
    
    def _validate_architectural_patterns(self, patterns: ArchitecturalPatterns) -> None:
        """Validate architectural patterns and constraints"""
        
        # Validate architectural style
        valid_styles = ['layered', 'microservices', 'event_driven', 'pipeline', 'client_server', 'peer_to_peer']
        if patterns.style not in valid_styles:
            self.validation_errors.append(
                ValidationError(
                    "system.patterns.style",
                    f"Invalid architectural style: '{patterns.style}'. Valid options: {valid_styles}"
                )
            )
        
        # Validate design patterns
        valid_patterns = ['cqrs', 'event_sourcing', 'saga', 'circuit_breaker', 'bulkhead', 'throttling']
        for pattern in patterns.patterns:
            if pattern not in valid_patterns:
                self.validation_errors.append(
                    ValidationError(
                        "system.patterns.patterns",
                        f"Invalid design pattern: '{pattern}'. Valid options: {valid_patterns}"
                    )
                )
        
        # Validate constraints
        for constraint in patterns.constraints:
            if not isinstance(constraint, dict):
                self.validation_errors.append(
                    ValidationError(
                        "system.patterns.constraints",
                        "Constraint must be an object"
                    )
                )
            elif 'type' not in constraint or 'description' not in constraint:
                self.validation_errors.append(
                    ValidationError(
                        "system.patterns.constraints",
                        "Constraint must have 'type' and 'description' fields"
                    )
                )
    
    def _validate_security_requirements(self, components: List[ArchitecturalComponent]) -> None:
        """Validate security requirements for components"""
        
        for component in components:
            security = component.security
            
            # Validate authentication requirements
            if 'authentication' in security:
                auth = security['authentication']
                if 'routes' in auth:
                    for route in auth['routes']:
                        if not isinstance(route, dict):
                            self.validation_errors.append(
                                ValidationError(
                                    f"component.{component.name}.security.authentication.routes",
                                    "Route must be an object"
                                )
                            )
                        elif 'path' not in route or 'method' not in route or 'auth_required' not in route:
                            self.validation_errors.append(
                                ValidationError(
                                    f"component.{component.name}.security.authentication.routes",
                                    "Route must have 'path', 'method', and 'auth_required' fields"
                                )
                            )
    
    def _validate_quality_attributes(self, components: List[ArchitecturalComponent]) -> None:
        """Validate quality attributes for components"""
        
        for component in components:
            quality_attrs = component.quality_attributes
            
            # Validate performance requirements
            if 'performance' in quality_attrs:
                performance = quality_attrs['performance']
                
                valid_throughput_classes = ['low', 'medium', 'high', 'very_high']
                if 'throughput_class' in performance:
                    if performance['throughput_class'] not in valid_throughput_classes:
                        self.validation_errors.append(
                            ValidationError(
                                f"component.{component.name}.quality_attributes.performance.throughput_class",
                                f"Invalid throughput class. Valid options: {valid_throughput_classes}"
                            )
                        )
                
                valid_latency_classes = ['relaxed', 'standard', 'strict', 'real_time']
                if 'latency_class' in performance:
                    if performance['latency_class'] not in valid_latency_classes:
                        self.validation_errors.append(
                            ValidationError(
                                f"component.{component.name}.quality_attributes.performance.latency_class",
                                f"Invalid latency class. Valid options: {valid_latency_classes}"
                            )
                        )
    
    def get_component_dependencies(self, blueprint: ArchitecturalBlueprint) -> Dict[str, List[str]]:
        """Get dependency graph for components based on bindings"""
        
        dependencies = {comp.name: [] for comp in blueprint.system.components}
        
        for binding in blueprint.system.bindings:
            if binding.from_component not in dependencies[binding.to_component]:
                dependencies[binding.to_component].append(binding.from_component)
            
            # Add fan-out dependencies
            for target in binding.fan_out_targets:
                target_comp = target.get('component', '')
                if target_comp in dependencies and binding.from_component not in dependencies[target_comp]:
                    dependencies[target_comp].append(binding.from_component)
        
        return dependencies
    
    def get_processing_order(self, blueprint: ArchitecturalBlueprint) -> List[str]:
        """Get optimal component processing order based on dependencies"""
        
        dependencies = self.get_component_dependencies(blueprint)
        
        # Topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component: str):
            if component in temp_visited:
                raise ValueError(f"Circular dependency detected involving component: {component}")
            
            if component not in visited:
                temp_visited.add(component)
                
                for dep in dependencies[component]:
                    visit(dep)
                
                temp_visited.remove(component)
                visited.add(component)
                order.append(component)
        
        for comp in blueprint.system.components:
            if comp.name not in visited:
                visit(comp.name)
        
        return order

def main():
    """Test the architecture blueprint parser"""
    parser = ArchitectureBlueprintParser()
    
    # Test with a simple architecture blueprint
    test_blueprint = {
        'schema_version': '1.0.0',
        'system': {
            'name': 'test_system',
            'description': 'Test architectural system',
            'components': [
                {
                    'name': 'data_source',
                    'type': 'Source',
                    'processing_mode': 'stream',
                    'outputs': [
                        {'name': 'data', 'schema': 'common_object_schema'}
                    ]
                },
                {
                    'name': 'processor',
                    'type': 'Transformer',
                    'processing_mode': 'stream',
                    'inputs': [
                        {'name': 'input', 'schema': 'common_object_schema'}
                    ],
                    'outputs': [
                        {'name': 'output', 'schema': 'common_object_schema'}
                    ]
                }
            ],
            'bindings': [
                {
                    'from_component': 'data_source',
                    'from_port': 'data',
                    'to_component': 'processor',
                    'to_port': 'input'
                }
            ]
        }
    }
    
    try:
        blueprint = parser.parse_string(yaml.dump(test_blueprint))
        print(f"✅ Successfully parsed architecture blueprint: {blueprint.system.name}")
        print(f"   Components: {len(blueprint.system.components)}")
        print(f"   Bindings: {len(blueprint.system.bindings)}")
        
        # Show processing order
        order = parser.get_processing_order(blueprint)
        print(f"   Processing order: {' → '.join(order)}")
        
    except Exception as e:
        print(f"❌ Failed to parse architecture blueprint: {e}")

if __name__ == "__main__":
    main()