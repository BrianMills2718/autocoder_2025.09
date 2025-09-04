#!/usr/bin/env python3
"""
Autocoder 3.3 Blueprint Parser
Parses and validates blueprint YAML files according to the formal schema
"""
import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import re

@dataclass
class ValidationError:
    """Blueprint validation error"""
    path: str
    message: str
    severity: str = "error"

@dataclass
class ParsedPort:
    """Parsed input/output port with VR1 boundary semantics support"""
    name: str
    schema: str
    required: bool = True
    description: Optional[str] = None
    
    # Schema evolution support
    data_schema: Optional[Dict[str, Any]] = None  # {"id": "UserProfile", "version": 2}
    
    # VR1 boundary semantics
    boundary_ingress: bool = False     # External system entry point
    boundary_egress: bool = False      # External system reply/emission  
    reply_required: bool = False       # Must produce response for ingress
    satisfies_reply: bool = False      # This port satisfies reply contract
    
    # VR1 observability and streaming
    observability_export: bool = False # Port emits to monitoring/logs
    checkpoint: bool = False           # Port writes to checkpoint system
    
    # Security attributes (Phase 4 preparation)
    data_classification: str = "public"          # public, internal, confidential, secret
    egress_policy: Optional[str] = None          # encryption/redaction requirements

@dataclass
class ParsedConstraint:
    """Parsed property or contract constraint"""
    expression: str
    description: str
    severity: str = "error"

@dataclass
class ParsedResource:
    """Parsed resource requirement"""
    type: str
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedComponent:
    """Parsed component definition with VR1 durability support"""
    name: str
    type: str
    description: Optional[str] = None
    processing_mode: str = "batch"
    inputs: List[ParsedPort] = field(default_factory=list)
    outputs: List[ParsedPort] = field(default_factory=list)
    properties: List[ParsedConstraint] = field(default_factory=list)
    contracts: List[ParsedConstraint] = field(default_factory=list)
    resources: List[ParsedResource] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    implementation: Dict[str, Any] = field(default_factory=dict)
    observability: Dict[str, Any] = field(default_factory=dict)
    
    # VR1 extensions
    durable: bool = False              # Durability contract for VR1 validation
    terminal: bool = False             # Legacy terminal hint (VR1: pure hint only)
    statefulness: str = "stateless"    # stateless, stateful
    monitored_bus_ok: bool = False     # Allow observability-only termination
    
    # Durability finalization tracking
    _durability_finalized: bool = field(default=False, init=False)

@dataclass
class ParsedBlueprint:
    """Complete parsed blueprint"""
    component: ParsedComponent
    metadata: Dict[str, Any] = field(default_factory=dict)
    schemas: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None

class BlueprintParser:
    """
    Parses blueprint YAML files and validates them against the schema
    Converts YAML to structured Python objects for code generation
    """
    
    # Exact set of components that default to durable=True
    DURABLE_BY_DEFAULT_TYPES = frozenset({
        "Store",     # Persistent data storage
        "Database",  # Database connections (mapped to Store)
    })
    
    def __init__(self, schema_file: Optional[Path] = None, enable_vr1_semantics: bool = None):
        """Initialize parser with schema for validation and VR1 semantic inference"""
        self.schema_file = schema_file or Path(__file__).parent / "blueprint_schema.yaml"
        self.schema = self._load_schema()
        self.validation_errors: List[ValidationError] = []
        
        # Use settings if not explicitly provided
        if enable_vr1_semantics is None:
            from autocoder_cc.core.config import settings
            self.enable_vr1_semantics = settings.ENABLE_VR1_VALIDATION
        else:
            self.enable_vr1_semantics = enable_vr1_semantics
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the blueprint schema for validation"""
        try:
            with open(self.schema_file, 'r') as f:
                schema_content = yaml.safe_load(f)
                
            # Convert YAML schema to JSON Schema format for jsonschema library
            # Note: This is a simplified conversion - in production we'd use a full YAML->JSON Schema converter
            return {
                "type": "object",
                "required": ["component"],
                "properties": {
                    "component": {"type": "object"},
                    "metadata": {"type": "object"},
                    "schemas": {"type": "object"}
                }
            }
        except Exception as e:
            raise ValueError(f"Failed to load schema from {self.schema_file}: {e}")
    
    def parse_file(self, blueprint_file: Path) -> ParsedBlueprint:
        """Parse a blueprint file and return structured representation"""
        self.validation_errors.clear()
        
        try:
            with open(blueprint_file, 'r') as f:
                raw_blueprint = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML from {blueprint_file}: {e}")
        
        # Validate against schema
        self._validate_schema(raw_blueprint)
        
        # Parse into structured objects
        blueprint = self._parse_blueprint(raw_blueprint)
        blueprint.source_file = str(blueprint_file)
        
        # Perform semantic validation
        self._validate_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def parse_dict(self, blueprint_dict: Dict[str, Any]) -> ParsedBlueprint:
        """Parse blueprint from dictionary"""
        self.validation_errors.clear()
        
        # Validate and parse directly from dictionary
        self._validate_schema(blueprint_dict)
        blueprint = self._parse_blueprint(blueprint_dict)
        self._validate_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def parse_string(self, blueprint_yaml: str) -> ParsedBlueprint:
        """Parse blueprint from YAML string"""
        self.validation_errors.clear()
        
        try:
            raw_blueprint = yaml.safe_load(blueprint_yaml)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML string: {e}")
        
        # Validate and parse
        self._validate_schema(raw_blueprint)
        blueprint = self._parse_blueprint(raw_blueprint)
        self._validate_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def _validate_schema(self, blueprint: Dict[str, Any]) -> None:
        """Validate blueprint against JSON schema"""
        try:
            # Basic structure validation
            if 'component' not in blueprint:
                self.validation_errors.append(
                    ValidationError("root", "Missing required 'component' section")
                )
                return
                
            component = blueprint['component']
            
            # Required fields
            required_fields = ['name', 'type', 'processing_mode']
            for field in required_fields:
                if field not in component:
                    self.validation_errors.append(
                        ValidationError(f"component.{field}", f"Missing required field '{field}'")
                    )
            
            # Component type validation
            valid_types = [
                'Source', 'Transformer', 'Accumulator', 'Store', 'Controller',
                'Sink', 'StreamProcessor', 'Model', 'APIEndpoint', 'Router',
                'WebSocket', 'gRPCEndpoint', 'Cache', 'Database'
            ]
            if component.get('type') not in valid_types:
                self.validation_errors.append(
                    ValidationError(
                        "component.type", 
                        f"Invalid component type '{component.get('type')}'. Must be one of: {valid_types}"
                    )
                )
            
            # Processing mode validation
            valid_modes = ['batch', 'stream', 'hybrid']
            if component.get('processing_mode') not in valid_modes:
                self.validation_errors.append(
                    ValidationError(
                        "component.processing_mode",
                        f"Invalid processing mode '{component.get('processing_mode')}'. Must be one of: {valid_modes}"
                    )
                )
            
            # Name validation (snake_case)
            name = component.get('name', '')
            if not re.match(r'^[a-z][a-z0-9_]*$', name):
                self.validation_errors.append(
                    ValidationError(
                        "component.name",
                        f"Component name '{name}' must be snake_case (lowercase letters, numbers, underscores)"
                    )
                )
                
        except Exception as e:
            self.validation_errors.append(
                ValidationError("schema", f"Schema validation error: {e}")
            )
    
    def _get_durability_default(self, component_type: str) -> bool:
        """Get durability default with Cache special case"""
        
        # SPECIAL CASE: Cache is never durable (before normalization)
        if component_type == "Cache":
            return False
        
        # Check defaults for known types
        return component_type in self.DURABLE_BY_DEFAULT_TYPES
    
    def _parse_blueprint(self, raw: Dict[str, Any]) -> ParsedBlueprint:
        """Parse raw YAML with VR1 field support"""
        
        component_data = raw.get('component', {})
        
        # Determine durability default BEFORE normalization
        original_type = component_data.get('type', '')
        durable_default = self._get_durability_default(original_type)
        
        component = ParsedComponent(
            name=component_data.get('name', ''),
            type=component_data.get('type', ''),
            description=component_data.get('description'),
            processing_mode=component_data.get('processing_mode', 'batch'),
            config=component_data.get('configuration', {}),
            dependencies=component_data.get('dependencies', []),
            implementation=component_data.get('implementation', {}),
            observability=component_data.get('observability', {}),
            durable=component_data.get('durable', durable_default),
            terminal=component_data.get('terminal', False),
            statefulness=component_data.get('statefulness', 'stateless'),
            monitored_bus_ok=component_data.get('monitored_bus_ok', False)
        )
        
        # Mark durability as finalized
        component._durability_finalized = True
        
        # Parse ports with boundary semantics
        for input_data in component_data.get('inputs', []):
            port = self._parse_port_with_boundary_semantics(input_data)
            component.inputs.append(port)
        
        for output_data in component_data.get('outputs', []):
            port = self._parse_port_with_boundary_semantics(output_data)
            component.outputs.append(port)
        
        # Apply component type defaults for boundary semantics
        self._apply_component_type_defaults(component)
        
        # Parse property constraints
        for prop_data in component_data.get('properties', []):
            constraint = ParsedConstraint(
                expression=prop_data.get('constraint', ''),
                description=prop_data.get('description', ''),
                severity=prop_data.get('severity', 'error')
            )
            component.properties.append(constraint)
        
        # Parse contract constraints
        for contract_data in component_data.get('contracts', []):
            constraint = ParsedConstraint(
                expression=contract_data.get('expression', ''),
                description=contract_data.get('description', ''),
                severity='error'  # Contracts are always errors
            )
            component.contracts.append(constraint)
        
        # Parse resources
        resources_data = component_data.get('resources', {})
        
        # Parse ports
        for port_data in resources_data.get('ports', []):
            resource = ParsedResource(
                type='port',
                config=port_data
            )
            component.resources.append(resource)
        
        # Parse databases
        for db_data in resources_data.get('databases', []):
            resource = ParsedResource(
                type='database',
                config=db_data
            )
            component.resources.append(resource)
        
        # Parse external services
        for service_data in resources_data.get('external_services', []):
            resource = ParsedResource(
                type='external_service',
                config=service_data
            )
            component.resources.append(resource)
        
        # Create blueprint
        blueprint = ParsedBlueprint(
            component=component,
            metadata=raw.get('metadata', {}),
            schemas=raw.get('schemas', {})
        )
        
        return blueprint

    def _parse_port_with_boundary_semantics(self, port_data: Dict[str, Any]) -> ParsedPort:
        """Parse port with VR1 boundary field support"""
        
        # Handle schema precedence: data_schema.* > schema
        schema_string, data_schema = self._parse_port_schema(port_data)
        
        port = ParsedPort(
            name=port_data.get('name', ''),
            schema=schema_string,
            required=port_data.get('required', True),
            description=port_data.get('description'),
            data_schema=data_schema,
            
            # VR1 boundary semantics
            boundary_ingress=port_data.get('boundary_ingress', False),
            boundary_egress=port_data.get('boundary_egress', False),
            reply_required=port_data.get('reply_required', False),
            satisfies_reply=port_data.get('satisfies_reply', False),
            observability_export=port_data.get('observability_export', False),
            checkpoint=port_data.get('checkpoint', False),
            
            # Security attributes
            data_classification=port_data.get('data_classification', 'public'),
            egress_policy=port_data.get('egress_policy')
        )
        
        # Track which fields were explicitly set to avoid overriding with defaults
        if 'boundary_ingress' in port_data:
            setattr(port, '_boundary_ingress_set', True)
        if 'boundary_egress' in port_data:
            setattr(port, '_boundary_egress_set', True)
        if 'reply_required' in port_data:
            setattr(port, '_reply_required_set', True)
        if 'satisfies_reply' in port_data:
            setattr(port, '_satisfies_reply_set', True)
        
        return port

    def _parse_port_schema(self, port_data: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """Parse port schema with data_schema precedence"""
        data_schema = port_data.get('data_schema')
        if data_schema:
            # Convert structured schema to string for compatibility
            if isinstance(data_schema, dict) and 'id' in data_schema:
                schema_string = f"{data_schema['id']}_v{data_schema.get('version', 1)}"
            else:
                schema_string = str(data_schema)
            return schema_string, data_schema
        else:
            # Use legacy schema field
            return port_data.get('schema', ''), None

    def _apply_component_type_defaults(self, component: ParsedComponent) -> None:
        """Apply VR1 defaults based on component type and port naming patterns"""
        
        if component.type == "APIEndpoint":
            # Auto-set APIEndpoint boundary semantics (only if not explicitly set)
            for port in component.inputs:
                if port.name in ["request", "http_request", "api_request"]:
                    if not hasattr(port, '_boundary_ingress_set'):
                        port.boundary_ingress = True
                    if not hasattr(port, '_reply_required_set'):
                        port.reply_required = True
            
            for port in component.outputs:
                if port.name in ["response", "http_response", "api_response"]:
                    if not hasattr(port, '_boundary_egress_set'):
                        port.boundary_egress = True
                    if not hasattr(port, '_satisfies_reply_set'):
                        port.satisfies_reply = True
        
        elif component.type == "WebSocket":
            # Auto-set WebSocket boundary semantics
            for port in component.inputs:
                if port.name in ["connection_request", "ws_connect", "connect"]:
                    if not hasattr(port, '_boundary_ingress_set'):
                        port.boundary_ingress = True
                    if not hasattr(port, '_reply_required_set'):
                        port.reply_required = True
                elif port.name in ["message_in", "client_message", "message"]:
                    if not hasattr(port, '_boundary_ingress_set'):
                        port.boundary_ingress = True
                    if not hasattr(port, '_reply_required_set'):
                        port.reply_required = False
            
            for port in component.outputs:
                if port.name in ["connection_status", "connect_response", "status"]:
                    if not hasattr(port, '_boundary_egress_set'):
                        port.boundary_egress = True
                    if not hasattr(port, '_satisfies_reply_set'):
                        port.satisfies_reply = True
                elif port.name in ["message_out", "server_message", "broadcast"]:
                    if not hasattr(port, '_boundary_egress_set'):
                        port.boundary_egress = True
                    if not hasattr(port, '_satisfies_reply_set'):
                        port.satisfies_reply = False
        
        elif component.type == "Source":
            # Source components generate data that enters the system
            for port in component.outputs:
                if port.name in ["data", "stream", "events", "output"]:
                    if not hasattr(port, '_boundary_egress_set'):
                        # Source outputs are internal, not boundary egress
                        port.boundary_egress = False
                        
        elif component.type == "Sink":
            # Sink components consume data that exits the system
            for port in component.inputs:
                if port.name in ["data", "input", "events"]:
                    # Sink inputs may be boundary points if they're externally triggered
                    # This depends on the specific use case
                    pass
                    
        elif component.type == "Store":
            # Store components have special durability semantics
            component.durable = True  # Ensure durability flag is set
            
        elif component.type == "Controller":
            # Controller components may have control inputs
            for port in component.inputs:
                if port.name in ["control", "command", "trigger"]:
                    # Control inputs may be boundary ingress
                    if not hasattr(port, '_reply_required_set'):
                        port.reply_required = True
                        
        elif component.type == "StreamProcessor":
            # StreamProcessor components process continuous data streams
            # Generally internal components without boundary semantics
            pass
    
    def _validate_semantics(self, blueprint: ParsedBlueprint) -> None:
        """Perform semantic validation on parsed blueprint"""
        
        # Validate property constraints are valid Python expressions
        for prop in blueprint.component.properties:
            if not self._validate_python_expression(prop.expression):
                self.validation_errors.append(
                    ValidationError(
                        f"component.properties.{prop.expression}",
                        f"Invalid Python expression: '{prop.expression}'"
                    )
                )
        
        # Validate contract constraints are valid Python expressions
        for contract in blueprint.component.contracts:
            if not self._validate_python_expression(contract.expression):
                self.validation_errors.append(
                    ValidationError(
                        f"component.contracts.{contract.expression}",
                        f"Invalid Python expression: '{contract.expression}'"
                    )
                )
        
        # Validate schema references
        for port in blueprint.component.inputs + blueprint.component.outputs:
            if port.schema not in blueprint.schemas:
                self.validation_errors.append(
                    ValidationError(
                        f"component.{port.name}.schema",
                        f"Schema '{port.schema}' not found in schemas section"
                    )
                )
        
        # Validate component type has appropriate ports
        self._validate_component_type_ports(blueprint.component)
    
    def _validate_python_expression(self, expression: str) -> bool:
        """Validate that string is a valid Python expression"""
        try:
            compile(expression, '<blueprint>', 'eval')
            return True
        except SyntaxError:
            return False
    
    def _validate_component_type_ports(self, component: ParsedComponent) -> None:
        """Validate component type has appropriate input/output ports"""
        
        # Source components should have outputs but minimal inputs
        if component.type == 'Source':
            if not component.outputs:
                self.validation_errors.append(
                    ValidationError(
                        "component.outputs",
                        "Source components must have at least one output port"
                    )
                )
        
        # Sink components should have inputs but minimal outputs
        elif component.type == 'Sink':
            if not component.inputs:
                self.validation_errors.append(
                    ValidationError(
                        "component.inputs",
                        "Sink components must have at least one input port"
                    )
                )
        
        # Transformer components should have both inputs and outputs
        elif component.type in ['Transformer', 'Model']:
            if not component.inputs:
                self.validation_errors.append(
                    ValidationError(
                        "component.inputs",
                        f"{component.type} components must have at least one input port"
                    )
                )
            if not component.outputs:
                self.validation_errors.append(
                    ValidationError(
                        "component.outputs",
                        f"{component.type} components must have at least one output port"
                    )
                )
    
    def to_dict(self, blueprint: ParsedBlueprint) -> Dict[str, Any]:
        """Convert parsed blueprint back to dictionary format"""
        
        component_dict = {
            'name': blueprint.component.name,
            'type': blueprint.component.type,
            'processing_mode': blueprint.component.processing_mode,
            'durable': blueprint.component.durable,
            'terminal': blueprint.component.terminal,
            'statefulness': blueprint.component.statefulness,
            'monitored_bus_ok': blueprint.component.monitored_bus_ok
        }
        
        if blueprint.component.description:
            component_dict['description'] = blueprint.component.description
        
        if blueprint.component.inputs:
            component_dict['inputs'] = [
                {
                    'name': port.name,
                    'schema': port.schema,
                    'required': port.required,
                    'description': port.description,
                    'data_schema': port.data_schema,
                    'boundary_ingress': port.boundary_ingress,
                    'boundary_egress': port.boundary_egress,
                    'reply_required': port.reply_required,
                    'satisfies_reply': port.satisfies_reply,
                    'observability_export': port.observability_export,
                    'checkpoint': port.checkpoint,
                    'data_classification': port.data_classification,
                    'egress_policy': port.egress_policy
                } for port in blueprint.component.inputs
            ]
        
        if blueprint.component.outputs:
            component_dict['outputs'] = [
                {
                    'name': port.name,
                    'schema': port.schema,
                    'required': port.required,
                    'description': port.description,
                    'data_schema': port.data_schema,
                    'boundary_ingress': port.boundary_ingress,
                    'boundary_egress': port.boundary_egress,
                    'reply_required': port.reply_required,
                    'satisfies_reply': port.satisfies_reply,
                    'observability_export': port.observability_export,
                    'checkpoint': port.checkpoint,
                    'data_classification': port.data_classification,
                    'egress_policy': port.egress_policy
                } for port in blueprint.component.outputs
            ]
        
        if blueprint.component.properties:
            component_dict['properties'] = [
                {
                    'constraint': prop.expression,
                    'description': prop.description,
                    'severity': prop.severity
                } for prop in blueprint.component.properties
            ]
        
        if blueprint.component.contracts:
            component_dict['contracts'] = [
                {
                    'expression': contract.expression,
                    'description': contract.description
                } for contract in blueprint.component.contracts
            ]
        
        if blueprint.component.config:
            component_dict['configuration'] = blueprint.component.config
        
        if blueprint.component.dependencies:
            component_dict['dependencies'] = blueprint.component.dependencies
        
        if blueprint.component.implementation:
            component_dict['implementation'] = blueprint.component.implementation
        
        if blueprint.component.observability:
            component_dict['observability'] = blueprint.component.observability
        
        result = {'component': component_dict}
        
        if blueprint.metadata:
            result['metadata'] = blueprint.metadata
        
        if blueprint.schemas:
            result['schemas'] = blueprint.schemas
        
        return result

def main():
    """Test the blueprint parser"""
    parser = BlueprintParser()
    
    # Test with example blueprint
    example_file = Path(__file__).parent / "examples" / "fraud_scorer.yaml"
    if example_file.exists():
        try:
            blueprint = parser.parse_file(example_file)
            print(f"✅ Successfully parsed blueprint: {blueprint.component.name}")
            print(f"   Type: {blueprint.component.type}")
            print(f"   Processing mode: {blueprint.component.processing_mode}")
            print(f"   Inputs: {len(blueprint.component.inputs)}")
            print(f"   Outputs: {len(blueprint.component.outputs)}")
            print(f"   Properties: {len(blueprint.component.properties)}")
            print(f"   Contracts: {len(blueprint.component.contracts)}")
            print(f"   Resources: {len(blueprint.component.resources)}")
            
            # Test conversion back to dict
            dict_repr = parser.to_dict(blueprint)
            print(f"✅ Successfully converted back to dictionary format")
            
        except Exception as e:
            print(f"❌ Failed to parse blueprint: {e}")
    else:
        print(f"❌ Example file not found: {example_file}")

if __name__ == "__main__":
    main()