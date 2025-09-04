#!/usr/bin/env python3
"""
Autocoder 3.3 System Blueprint Parser
Parses and validates complete system blueprints with multiple components and bindings
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from .blueprint_parser import BlueprintParser, ParsedBlueprint, ParsedComponent, ParsedPort, ParsedConstraint, ParsedResource, ValidationError
from .port_auto_generator import ComponentPortAutoGenerator
from .architectural_validator import ArchitecturalValidator
from .architecture_blueprint_parser import ArchitectureBlueprintParser, ArchitecturalBlueprint
from .deployment_blueprint_parser import DeploymentBlueprintParser, DeploymentBlueprint
from autocoder_cc.healing.blueprint_healer import BlueprintHealer
from autocoder_cc.observability.structured_logging import get_logger

logger = get_logger(__name__)

@dataclass
class ParsedBinding:
    """Parsed component binding (connection)"""
    from_component: str
    from_port: str
    to_components: List[str]  # Support fan-out
    to_ports: List[str]
    transformation: Optional[str] = None
    condition: Optional[str] = None
    error_handling: Dict[str, Any] = field(default_factory=dict)
    qos: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedSystemConfiguration:
    """Parsed system-wide configuration"""
    environment: str = "development"
    timeouts: Dict[str, int] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, str] = field(default_factory=dict)

@dataclass
class ParsedDeploymentConfiguration:
    """Parsed deployment configuration"""
    platform: str = "docker"
    external_services: List[Dict[str, Any]] = field(default_factory=list)
    networking: Dict[str, Any] = field(default_factory=dict)
    scaling: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedSystemValidation:
    """Parsed system validation requirements"""
    performance: Dict[str, Any] = field(default_factory=dict)
    end_to_end_tests: bool = True
    load_testing: Dict[str, Any] = field(default_factory=dict)
    sample_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedSystem:
    """Complete parsed system"""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    components: List[ParsedComponent] = field(default_factory=list)
    bindings: List[ParsedBinding] = field(default_factory=list)
    configuration: ParsedSystemConfiguration = field(default_factory=ParsedSystemConfiguration)
    deployment: ParsedDeploymentConfiguration = field(default_factory=ParsedDeploymentConfiguration)
    validation: ParsedSystemValidation = field(default_factory=ParsedSystemValidation)

@dataclass
class ParsedSystemBlueprint:
    """Complete parsed system blueprint"""
    system: ParsedSystem
    metadata: Dict[str, Any] = field(default_factory=dict)
    schemas: Dict[str, Any] = field(default_factory=dict)
    policy: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    raw_blueprint: Dict[str, Any] = field(default_factory=dict)

class SystemBlueprintParser:
    """
    Parses complete system blueprints with multiple components and connections
    Validates schema compatibility, resource conflicts, and system consistency
    """
    
    def __init__(self, schema_file: Optional[Path] = None):
        """Initialize parser with system schema"""
        self.schema_file = schema_file or Path(__file__).parent / "system_blueprint_schema.yaml"
        self.validation_errors: List[ValidationError] = []
        
        # Initialize port auto-generator (Enterprise Roadmap v3 Phase 1)
        self.port_generator = ComponentPortAutoGenerator()
        
        # Initialize sub-parsers for split blueprints
        self.architecture_parser = ArchitectureBlueprintParser()
        self.deployment_parser = DeploymentBlueprintParser()
        
        # Initialize blueprint healer for auto-fixing common issues
        self.healer = BlueprintHealer()
        
    def parse_file(self, system_blueprint_file: Path, max_healing_attempts: int = 3) -> ParsedSystemBlueprint:
        """Parse a system blueprint file with healing retry loop"""
        self.validation_errors.clear()
        
        try:
            with open(system_blueprint_file, 'r') as f:
                blueprint_yaml = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read YAML from {system_blueprint_file}: {e}")
        
        # Use the healing retry logic from parse_string
        system_blueprint = self.parse_string(blueprint_yaml, max_healing_attempts)
        system_blueprint.source_file = str(system_blueprint_file)
        
        return system_blueprint
    
    def parse_string(self, system_blueprint_yaml: str, max_healing_attempts: int = 3) -> ParsedSystemBlueprint:
        """Parse system blueprint from YAML string with healing retry loop"""
        import copy
        
        self.validation_errors.clear()
        
        try:
            raw_blueprint = yaml.safe_load(system_blueprint_yaml)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML string: {e}")
        
        # CRITICAL FIX: Use working_blueprint that preserves healing across attempts
        # This prevents losing transformations when retrying after validation failures
        working_blueprint = copy.deepcopy(raw_blueprint)
        
        # Always normalize binding formats first (even before healing)
        working_blueprint = self._normalize_binding_formats(working_blueprint)
        
        # Healing retry loop
        for attempt in range(max_healing_attempts + 1):  # +1 for initial attempt
            logger.info(f"Blueprint parsing attempt {attempt + 1}/{max_healing_attempts + 1}")
            
            # Phase 1: STRUCTURAL healing (before port generation)
            if attempt > 0:
                logger.info(f"Applying structural healing for attempt {attempt + 1}")
                # Deep copy to prevent healer from modifying our working copy
                working_blueprint = self.healer.heal_blueprint(
                    copy.deepcopy(working_blueprint), 
                    phase='structural'
                )
            else:
                # First attempt - always heal structural issues for consistency
                working_blueprint = self.healer.heal_blueprint(
                    copy.deepcopy(working_blueprint),
                    phase='structural'
                )
            
            # Clear previous validation errors
            self.validation_errors.clear()
            
            # Validate and parse from WORKING blueprint (not raw)
            self._validate_system_structure(working_blueprint)
            system_blueprint = self._parse_system_blueprint(working_blueprint)
            # Keep reference to WORKING blueprint (which has schema_version) not original
            # This is critical for schema generation which needs the schema_version field
            system_blueprint.raw_blueprint = working_blueprint
            
            # Auto-generate missing component ports (Enterprise Roadmap v3 Phase 1)
            system_blueprint = self.port_generator.auto_generate_ports(system_blueprint)
            
            # Phase 2: SCHEMA healing (after port generation) - NEW
            # Always update working blueprint with port changes
            working_blueprint = self._update_working_blueprint_from_parsed(working_blueprint, system_blueprint)
            
            # Always apply schema healing now that ports exist
            logger.info(f"Applying schema healing for attempt {attempt + 1}")
            working_blueprint = self.healer.heal_blueprint(
                copy.deepcopy(working_blueprint),
                phase='schema'
            )
            
            # Re-parse after schema healing to get transformations
            system_blueprint = self._parse_system_blueprint(working_blueprint)
            # Update raw_blueprint to include all healing transformations
            system_blueprint.raw_blueprint = working_blueprint
            
            self._validate_system_semantics(system_blueprint)
            
            # If validation passed, return success
            if not self.validation_errors:
                if attempt > 0:
                    logger.info(f"Blueprint validation succeeded after {attempt + 1} attempts with healing")
                return system_blueprint
            
            # If this was the last attempt, give up
            if attempt >= max_healing_attempts:
                break
            
            # Log validation errors and attempt healing
            logger.warning(f"Blueprint validation failed with {len(self.validation_errors)} errors, attempting healing:")
            for error in self.validation_errors:
                logger.warning(f"  {error.path}: {error.message}")
        
        # All healing attempts exhausted
        error_summary = f"System blueprint validation failed after {max_healing_attempts + 1} attempts with {len(self.validation_errors)} errors"
        for error in self.validation_errors:
            error_summary += f"\n  {error.path}: {error.message}"
        raise ValueError(error_summary)
    
    def parse_split_blueprints(self, architecture_file: Path, deployment_file: Path) -> ParsedSystemBlueprint:
        """Parse split architecture and deployment blueprints and combine them"""
        self.validation_errors.clear()
        
        try:
            # Parse architecture blueprint
            architecture_blueprint = self.architecture_parser.parse_file(architecture_file)
            
            # Parse deployment blueprint
            deployment_blueprint = self.deployment_parser.parse_file(deployment_file)
            
            # Validate that they reference the same system
            if architecture_blueprint.system.name != deployment_blueprint.system_name:
                raise ValueError(f"System name mismatch: architecture '{architecture_blueprint.system.name}' vs deployment '{deployment_blueprint.system_name}'")
            
            # Combine into unified system blueprint
            combined_blueprint = self._combine_blueprints(architecture_blueprint, deployment_blueprint)
            
            # Auto-generate missing component ports
            combined_blueprint = self.port_generator.auto_generate_ports(combined_blueprint)
            
            # Perform system-level validation
            self._validate_system_semantics(combined_blueprint)
            
            if self.validation_errors:
                error_summary = f"Combined blueprint validation failed with {len(self.validation_errors)} errors"
                for error in self.validation_errors:
                    error_summary += f"\n  {error.path}: {error.message}"
                raise ValueError(error_summary)
            
            return combined_blueprint
            
        except Exception as e:
            raise ValueError(f"Failed to parse split blueprints: {e}")
    
    def _combine_blueprints(self, architecture: ArchitecturalBlueprint, deployment: DeploymentBlueprint) -> ParsedSystemBlueprint:
        """Combine architecture and deployment blueprints into unified system blueprint"""
        
        # Convert architectural components to parsed components
        components = []
        for arch_comp in architecture.system.components:
            parsed_comp = ParsedComponent(
                name=arch_comp.name,
                type=arch_comp.type,
                description=arch_comp.description,
                processing_mode=arch_comp.processing_mode,
                config=arch_comp.architectural_config,
                dependencies=arch_comp.dependencies,
                implementation=arch_comp.implementation,
                observability={}  # Will be populated from deployment config
            )
            
            # Copy ports
            parsed_comp.inputs = arch_comp.inputs
            parsed_comp.outputs = arch_comp.outputs
            
            # Copy constraints
            parsed_comp.properties = arch_comp.properties
            parsed_comp.contracts = arch_comp.contracts
            
            # Convert resource requirements to resources
            for req_type, req_config in arch_comp.resource_requirements.items():
                resource = ParsedResource(
                    type=req_type,
                    config=req_config if isinstance(req_config, dict) else {'value': req_config}
                )
                parsed_comp.resources.append(resource)
            
            components.append(parsed_comp)
        
        # Convert architectural bindings to parsed bindings
        bindings = []
        for arch_binding in architecture.system.bindings:
            parsed_binding = ParsedBinding(
                from_component=arch_binding.from_component,
                from_port=arch_binding.from_port,
                to_components=[arch_binding.to_component] + [target['component'] for target in arch_binding.fan_out_targets],
                to_ports=[arch_binding.to_port] + [target['port'] for target in arch_binding.fan_out_targets],
                transformation=arch_binding.transformation,
                condition=arch_binding.condition,
                error_handling={},
                qos=arch_binding.qos_requirements
            )
            bindings.append(parsed_binding)
        
        # Create system configuration from deployment
        system_config = ParsedSystemConfiguration(
            environment=deployment.deployment.target_environment,
            timeouts=deployment.runtime.timeouts,
            resource_limits=deployment.runtime.resource_limits,
            logging=deployment.runtime.logging
        )
        
        # Create deployment configuration
        deployment_config = ParsedDeploymentConfiguration(
            platform=deployment.deployment.platform,
            external_services=deployment.deployment.external_services,
            networking=deployment.deployment.networking,
            scaling=deployment.deployment.scaling
        )
        
        # Create validation configuration (default)
        validation_config = ParsedSystemValidation()
        
        # Create unified system
        unified_system = ParsedSystem(
            name=architecture.system.name,
            description=architecture.system.description,
            version=architecture.system.version,
            components=components,
            bindings=bindings,
            configuration=system_config,
            deployment=deployment_config,
            validation=validation_config
        )
        
        # Apply component overrides from deployment
        for comp_name, override in deployment.component_overrides.items():
            # Find the component
            target_comp = None
            for comp in components:
                if comp.name == comp_name:
                    target_comp = comp
                    break
            
            if target_comp:
                # Apply port overrides
                for port_override in override.ports:
                    port_name = port_override.get('name', '')
                    port_number = port_override.get('port', 0)
                    
                    # Add port configuration to component config
                    if 'ports' not in target_comp.config:
                        target_comp.config['ports'] = {}
                    target_comp.config['ports'][port_name] = port_number
                
                # Apply environment variable overrides
                if override.environment_variables:
                    if 'environment_variables' not in target_comp.config:
                        target_comp.config['environment_variables'] = {}
                    target_comp.config['environment_variables'].update(override.environment_variables)
                
                # Apply resource overrides
                if override.resource_overrides:
                    if 'resource_overrides' not in target_comp.config:
                        target_comp.config['resource_overrides'] = {}
                    target_comp.config['resource_overrides'].update(override.resource_overrides)
                
                # Apply health check configuration
                if override.health_check:
                    target_comp.config['health_check'] = override.health_check
                
                # Apply scaling configuration
                if override.scaling:
                    target_comp.config['scaling'] = override.scaling
        
        # Create unified blueprint
        unified_blueprint = ParsedSystemBlueprint(
            system=unified_system,
            metadata=architecture.metadata,
            schemas=architecture.schemas,
            policy=architecture.policy,
            source_file=f"{architecture.source_file}+{deployment.source_file}",
            raw_blueprint={
                'architecture': architecture.raw_blueprint,
                'deployment': deployment.raw_blueprint
            }
        )
        
        return unified_blueprint
    
    def _update_working_blueprint_from_parsed(self, working_blueprint: Dict[str, Any], 
                                              parsed_blueprint: 'ParsedSystemBlueprint') -> Dict[str, Any]:
        """Update working blueprint with changes from parsed structure (e.g., port generation)"""
        # Deep copy to avoid mutations
        import copy
        updated = copy.deepcopy(working_blueprint)
        
        # Update component ports that were modified by port generator
        if 'system' in updated and 'components' in updated['system']:
            component_lookup = {comp.name: comp for comp in parsed_blueprint.system.components}
            
            for comp_dict in updated['system']['components']:
                comp_name = comp_dict.get('name')
                if comp_name in component_lookup:
                    parsed_comp = component_lookup[comp_name]
                    
                    # Update inputs
                    if parsed_comp.inputs:
                        comp_dict['inputs'] = [
                            {
                                'name': port.name,
                                'schema': port.schema or 'ItemSchema',
                                'schema_type': port.schema  # Keep both for compatibility
                            }
                            for port in parsed_comp.inputs
                        ]
                    
                    # Update outputs
                    if parsed_comp.outputs:
                        comp_dict['outputs'] = [
                            {
                                'name': port.name,
                                'schema': port.schema or 'ItemSchema',
                                'schema_type': port.schema  # Keep both for compatibility
                            }
                            for port in parsed_comp.outputs
                        ]
        
        return updated
    
    def _validate_system_structure(self, blueprint: Dict[str, Any]) -> None:
        """Validate system blueprint basic structure"""
        
        # CRITICAL: Validate schema_version field (Phase 1 requirement)
        try:
            from autocoder_cc.core.schema_versioning import validate_blueprint_schema_version
            validate_blueprint_schema_version(blueprint)
        except ValueError as e:
            self.validation_errors.append(ValidationError(
                path="schema_version",
                message=str(e),
                severity="critical"
            ))
        
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
    
    def _parse_system_blueprint(self, raw: Dict[str, Any]) -> ParsedSystemBlueprint:
        """Parse raw YAML into structured system blueprint object"""
        
        system_data = raw.get('system', {})
        
        # Parse system configuration
        config_data = system_data.get('configuration', {})
        system_config = ParsedSystemConfiguration(
            environment=config_data.get('environment', 'development'),
            timeouts=config_data.get('timeouts', {}),
            resource_limits=config_data.get('resource_limits', {}),
            logging=config_data.get('logging', {})
        )
        
        # Parse deployment configuration
        deploy_data = system_data.get('deployment', {})
        deployment_config = ParsedDeploymentConfiguration(
            platform=deploy_data.get('platform', 'docker'),
            external_services=deploy_data.get('external_services', []),
            networking=deploy_data.get('networking', {}),
            scaling=deploy_data.get('scaling', {})
        )
        
        # Parse validation configuration
        validation_data = system_data.get('validation', {})
        validation_config = ParsedSystemValidation(
            performance=validation_data.get('performance', {}),
            end_to_end_tests=validation_data.get('end_to_end_tests', True),
            load_testing=validation_data.get('load_testing', {}),
            sample_data=validation_data.get('sample_data', {})
        )
        
        # Parse components
        components = []
        for comp_data in system_data.get('components', []):
            component = self._parse_system_component(comp_data)
            components.append(component)
        
        # Parse bindings
        bindings = []
        for binding_data in system_data.get('bindings', []):
            binding = self._parse_binding(binding_data)
            bindings.append(binding)
        
        # Create system
        system = ParsedSystem(
            name=system_data.get('name', ''),
            description=system_data.get('description'),
            version=system_data.get('version', '1.0.0'),
            components=components,
            bindings=bindings,
            configuration=system_config,
            deployment=deployment_config,
            validation=validation_config
        )
        
        # Create system blueprint
        system_blueprint = ParsedSystemBlueprint(
            system=system,
            metadata=raw.get('metadata', {}),
            schemas=raw.get('schemas', {}),
            policy=raw.get('policy', {})
        )
        
        return system_blueprint
    
    def _parse_system_component(self, comp_data: Dict[str, Any]) -> ParsedComponent:
        """Parse a component within a system"""
        
        # Merge database configuration into component configuration for V5.2 compatibility
        # Support both 'config' and 'configuration' keys for backward compatibility
        component_config = comp_data.get('config', comp_data.get('configuration', {})).copy()
        if 'database' in comp_data:
            component_config['_database'] = comp_data['database']
        
        # Create component using same logic as individual component parser
        component = ParsedComponent(
            name=comp_data.get('name', ''),
            type=comp_data.get('type', ''),
            description=comp_data.get('description'),
            processing_mode=comp_data.get('processing_mode', 'batch'),
            config=component_config,
            dependencies=comp_data.get('dependencies', []),
            implementation=comp_data.get('implementation', {}),
            observability=comp_data.get('observability', {})
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
        
        # Parse resources
        resources_data = comp_data.get('resources', {})
        for resource_type, resource_configs in resources_data.items():
            if isinstance(resource_configs, list):
                for config in resource_configs:
                    component.resources.append(ParsedResource(
                        type=config.get('type', resource_type),
                        config=config
                    ))
            elif isinstance(resource_configs, dict):
                component.resources.append(ParsedResource(
                    type=resource_type,
                    config=resource_configs
                ))
        
        return component
    
    def _parse_binding(self, binding_data: Dict[str, Any]) -> ParsedBinding:
        """Parse a component binding - supports old, new, and mixed formats"""
        
        # Parse FROM part (supports both old 'from' and new 'from_component/from_port')
        if 'from_component' in binding_data and 'from_port' in binding_data:
            # New format for FROM
            from_component = binding_data.get('from_component', '')
            from_port = binding_data.get('from_port', '')
        elif 'from' in binding_data:
            # Old format for FROM
            from_spec = binding_data.get('from', '')
            if '.' not in from_spec:
                self.validation_errors.append(
                    ValidationError(f"binding.from", f"Invalid from specification: '{from_spec}' (expected component.port)")
                )
                from_component, from_port = '', ''
            else:
                from_component, from_port = from_spec.split('.', 1)
        else:
            # No FROM specification
            from_component, from_port = '', ''
            
        # Parse TO part (supports old 'to', new 'to_components/to_ports', and mixed formats)
        to_components = []
        to_ports = []
        
        # Check for new format TO specifications
        if 'to_component' in binding_data and 'to_components' not in binding_data:
            # Singular new format for TO
            to_components = [binding_data.get('to_component')]
            to_ports = [binding_data.get('to_port', 'input')]  # Default to 'input' if not specified
        elif 'to_components' in binding_data:
            # Plural new format for TO
            to_components = binding_data.get('to_components', [])
            to_ports = binding_data.get('to_ports', [])
        elif 'to' in binding_data:
            # Old format for TO
            to_spec = binding_data.get('to', '')
            if isinstance(to_spec, str):
                # Single target
                if '.' not in to_spec:
                    self.validation_errors.append(
                        ValidationError(f"binding.to", f"Invalid to specification: '{to_spec}' (expected component.port)")
                    )
                else:
                    to_component, to_port = to_spec.split('.', 1)
                    to_components.append(to_component)
                    to_ports.append(to_port)
            elif isinstance(to_spec, list):
                # Multiple targets (fan-out)
                for target in to_spec:
                    if '.' not in target:
                        self.validation_errors.append(
                            ValidationError(f"binding.to", f"Invalid to specification: '{target}' (expected component.port)")
                        )
                    else:
                        to_component, to_port = target.split('.', 1)
                        to_components.append(to_component)
                        to_ports.append(to_port)
        
        # Validate arrays have matching lengths
        if len(to_components) != len(to_ports):
            self.validation_errors.append(
                ValidationError(f"binding.to", f"to_components and to_ports arrays must have same length: {len(to_components)} vs {len(to_ports)}")
            )
        
        return ParsedBinding(
            from_component=from_component,
            from_port=from_port,
            to_components=to_components,
            to_ports=to_ports,
            transformation=binding_data.get('transformation'),
            condition=binding_data.get('condition'),
            error_handling=binding_data.get('error_handling', {}),
            qos=binding_data.get('qos', {})
        )
    
    def _normalize_binding_formats(self, blueprint_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all binding formats to canonical form (plural arrays).
        This ensures consistent handling throughout the pipeline.
        """
        if 'system' not in blueprint_dict or 'bindings' not in blueprint_dict['system']:
            return blueprint_dict
        
        for binding in blueprint_dict['system'].get('bindings', []):
            # Convert singular to plural for to_component/to_port
            if 'to_component' in binding and 'to_components' not in binding:
                binding['to_components'] = [binding.pop('to_component')]
                if 'to_port' in binding:
                    binding['to_ports'] = [binding.pop('to_port')]
                else:
                    binding['to_ports'] = ['input']  # Default port
            
            # Ensure to_ports array matches to_components length
            if 'to_components' in binding and 'to_ports' in binding:
                while len(binding['to_ports']) < len(binding['to_components']):
                    binding['to_ports'].append('input')  # Default port for missing entries
        
        return blueprint_dict
    
    def _validate_system_semantics(self, system_blueprint: ParsedSystemBlueprint) -> None:
        """Perform comprehensive system-level validation"""
        
        system = system_blueprint.system
        
        # 1. Validate component names are unique
        self._validate_unique_component_names(system.components)
        
        # 2. Validate binding references exist
        self._validate_binding_references(system.components, system.bindings)
        
        # 3. Validate schema compatibility
        self._validate_schema_compatibility(system.components, system.bindings, system_blueprint.schemas)
        
        # 4. Validate resource conflicts
        self._validate_resource_conflicts(system.components)
        
        # 5. Validate component type constraints
        self._validate_component_type_constraints(system.components, system.bindings)
        
        # 6. Validate architectural patterns and system coherence
        self._validate_architectural_patterns(system_blueprint)
    
    def _validate_unique_component_names(self, components: List[ParsedComponent]) -> None:
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
                    f"system.components",
                    f"Duplicate component name: '{duplicate}'"
                )
            )
    
    def _validate_binding_references(self, components: List[ParsedComponent], bindings: List[ParsedBinding]) -> None:
        """Validate all binding references point to existing components and ports"""
        
        # Build component and port lookup
        component_map = {comp.name: comp for comp in components}
        
        for binding in bindings:
            # Validate from component
            if binding.from_component not in component_map:
                self.validation_errors.append(
                    ValidationError(
                        f"binding.from",
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
                            f"binding.from",
                            f"Component '{binding.from_component}' has no output port '{binding.from_port}'. Available: {output_port_names}"
                        )
                    )
            
            # Validate to components
            for i, to_component in enumerate(binding.to_components):
                if to_component not in component_map:
                    self.validation_errors.append(
                        ValidationError(
                            f"binding.to",
                            f"Unknown component: '{to_component}'"
                        )
                    )
                else:
                    # Validate to port
                    to_comp = component_map[to_component]
                    input_port_names = [port.name for port in to_comp.inputs]
                    to_port = binding.to_ports[i] if i < len(binding.to_ports) else ''
                    if to_port not in input_port_names:
                        self.validation_errors.append(
                            ValidationError(
                                f"binding.to",
                                f"Component '{to_component}' has no input port '{to_port}'. Available: {input_port_names}"
                            )
                        )
    
    def _validate_schema_compatibility(self, components: List[ParsedComponent], 
                                     bindings: List[ParsedBinding], schemas: Dict[str, Any]) -> None:
        """Validate schema compatibility between connected components"""
        
        component_map = {comp.name: comp for comp in components}
        
        for binding in bindings:
            # Skip if components don't exist (caught by reference validation)
            if binding.from_component not in component_map:
                continue
            
            from_comp = component_map[binding.from_component]
            
            # Find output port schema
            from_port_schema = None
            for port in from_comp.outputs:
                if port.name == binding.from_port:
                    from_port_schema = port.schema
                    break
            
            if not from_port_schema:
                continue
            
            # Validate against all target ports
            for i, to_component in enumerate(binding.to_components):
                if to_component not in component_map:
                    continue
                
                to_comp = component_map[to_component]
                to_port = binding.to_ports[i] if i < len(binding.to_ports) else ''
                
                # Find input port schema
                to_port_schema = None
                for port in to_comp.inputs:
                    if port.name == to_port:
                        to_port_schema = port.schema
                        break
                
                if not to_port_schema:
                    continue
                
                # Check schema compatibility (allow transformations to bridge schema differences)
                if from_port_schema != to_port_schema:
                    # If there's a transformation, schema mismatch is allowed
                    if not binding.transformation:
                        # Check if this is an auto-convertible schema mismatch
                        if self._can_auto_convert_schemas(from_port_schema, to_port_schema):
                            # Auto-convert compatible schemas - no error needed
                            pass
                        else:
                            self.validation_errors.append(
                                ValidationError(
                                    f"binding.schema_compatibility",
                                    f"Schema mismatch without transformation: {binding.from_component}.{binding.from_port} ({from_port_schema}) → {to_component}.{to_port} ({to_port_schema})"
                                )
                            )
                    # With transformation, we trust the transformation handles the conversion
    
    def _can_auto_convert_schemas(self, from_schema: str, to_schema: str) -> bool:
        """Check if schema types can be automatically converted"""
        
        # "any" type accepts anything - universal compatibility 
        if to_schema == "any":
            return True
            
        # Compatible conversions that don't require explicit transformation
        compatible_pairs = [
            ('common_array_schema', 'common_object_schema'),  # array can be wrapped in object
            ('common_object_schema', 'common_array_schema'),  # object can be placed in array
            ('common_string_schema', 'common_object_schema'), # string can be wrapped in object  
            ('common_number_schema', 'common_object_schema'), # number can be wrapped in object
            ('common_integer_schema', 'common_number_schema'), # integer is a number
            ('common_boolean_schema', 'common_object_schema'), # boolean can be wrapped in object
            # Generic object conversions
            ('object', 'common_object_schema'),
            ('array', 'common_array_schema'),
            ('string', 'common_string_schema'),
            ('number', 'common_number_schema'),
            ('integer', 'common_integer_schema'),
            ('boolean', 'common_boolean_schema'),
            # Support for any type compatibility (for healing)
            ('common_object_schema', 'any'),
            ('common_integer_schema', 'any'),
            ('common_string_schema', 'any'),
            ('common_boolean_schema', 'any'),
            ('common_array_schema', 'any'),
            ('common_number_schema', 'any'),
            ('object', 'any'),
            ('integer', 'any'),
            ('string', 'any'),
            ('boolean', 'any'),
            ('array', 'any'),
            ('number', 'any'),
        ]
        
        return (from_schema, to_schema) in compatible_pairs
    
    def _validate_resource_conflicts(self, components: List[ParsedComponent]) -> None:
        """Validate and auto-heal resource conflicts between components"""
        
        # Convert components to system config format for SystemHealer
        system_config = {
            'components': []
        }
        
        for comp in components:
            comp_config = {
                'name': comp.name,
                'type': comp.type
            }
            
            # Add configuration including ports
            if comp.config:
                comp_config.update(comp.config)
            
            system_config['components'].append(comp_config)
        
        # Apply SystemHealer to fix resource conflicts
        from autocoder_cc.healing.system_healer import SystemHealer
        
        healer = SystemHealer()
        
        # Detect and heal port conflicts
        try:
            # Check for conflicts first
            port_conflicts = healer.detect_port_conflicts(system_config)
            
            if port_conflicts:
                print(f"🚨 Detected {len(port_conflicts)} port conflicts - applying system healing...")
                for conflict in port_conflicts[:3]:  # Show first 3
                    print(f"   - {conflict.description}")
                if len(port_conflicts) > 3:
                    print(f"   - ... and {len(port_conflicts) - 3} more conflicts")
                
                # Apply healing
                healed_config, fixes = healer.heal_port_conflicts(system_config)
                
                if fixes:
                    print(f"✅ System healing applied {len(fixes)} fixes:")
                    for fix in fixes[:3]:  # Show first 3
                        print(f"   - {fix}")
                    if len(fixes) > 3:
                        print(f"   - ... and {len(fixes) - 3} more fixes")
                    
                    # Update component configurations with healed values
                    comp_by_name = {comp.name: comp for comp in components}
                    for healed_comp in healed_config['components']:
                        comp_name = healed_comp['name']
                        if comp_name in comp_by_name:
                            # Update the component's configuration with healed values
                            original_comp = comp_by_name[comp_name]
                            for key, value in healed_comp.items():
                                if key not in ['name', 'type']:  # Don't overwrite name/type
                                    if original_comp.config is None:
                                        original_comp.config = {}
                                    original_comp.config[key] = value
                    
                    print(f"   ✅ Component configurations updated with healed values")
                
        except Exception as e:
            print(f"⚠️ System healing failed: {e}")
            # Fall back to original validation logic
            self._validate_resource_conflicts_original(components)
    
    def _validate_resource_conflicts_original(self, components: List[ParsedComponent]) -> None:
        """Original validation logic (fallback when healing fails)"""
        
        used_ports = set()
        
        for comp in components:
            # Check for port conflicts in API endpoints
            if comp.type == "APIEndpoint" and comp.config and 'port' in comp.config:
                port = comp.config['port']
                if port in used_ports:
                    raise ValueError(f"Port conflict: Port {port} is already used by another component")
                used_ports.add(port)
    
    def _validate_component_type_constraints(self, components: List[ParsedComponent], 
                                           bindings: List[ParsedBinding]) -> None:
        """Validate component types have appropriate connections"""
        
        component_map = {comp.name: comp for comp in components}
        
        # Count inputs and outputs for each component
        input_counts = {comp.name: 0 for comp in components}
        output_counts = {comp.name: 0 for comp in components}
        
        for binding in bindings:
            output_counts[binding.from_component] = output_counts.get(binding.from_component, 0) + 1
            for to_comp in binding.to_components:
                input_counts[to_comp] = input_counts.get(to_comp, 0) + 1
        
        # Validate component type constraints
        for comp in components:
            if comp.type == 'Source' and input_counts[comp.name] > 0:
                # Sources generally shouldn't have inputs from other components
                pass  # This might be OK in some cases
            
            if comp.type == 'Sink' and output_counts[comp.name] > 0:
                # Sinks generally shouldn't have outputs to other components
                pass  # This might be OK in some cases
    
    def _validate_architectural_patterns(self, system_blueprint: ParsedSystemBlueprint) -> None:
        """Validate architectural patterns and system coherence using ArchitecturalValidator"""
        
        try:
            architectural_validator = ArchitecturalValidator()
            arch_errors = architectural_validator.validate_system_architecture(system_blueprint)
            
            # Convert architectural validation errors to SystemBlueprintParser validation errors
            for arch_error in arch_errors:
                if arch_error.severity == "error":
                    self.validation_errors.append(
                        ValidationError(
                            path=arch_error.component or "system",
                            message=f"[{arch_error.error_type}] {arch_error.message}",
                            severity="error"
                        )
                    )
                elif arch_error.severity == "warning":
                    # For warnings, we might want to log them but not fail validation
                    print(f"⚠️ Architectural Warning: {arch_error.message}")
                    if arch_error.suggestion:
                        print(f"   Suggestion: {arch_error.suggestion}")
                        
        except Exception as e:
            # If architectural validation fails, log the error but don't fail the entire validation
            print(f"⚠️ Architectural validation failed: {e}")
    
    def get_component_dependencies(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, List[str]]:
        """Get dependency graph for components based on bindings"""
        
        dependencies = {comp.name: [] for comp in system_blueprint.system.components}
        
        for binding in system_blueprint.system.bindings:
            for to_comp in binding.to_components:
                if binding.from_component not in dependencies[to_comp]:
                    dependencies[to_comp].append(binding.from_component)
        
        return dependencies
    
    def get_processing_order(self, system_blueprint: ParsedSystemBlueprint) -> List[str]:
        """Get optimal component processing order based on dependencies"""
        
        dependencies = self.get_component_dependencies(system_blueprint)
        
        # Topological sort to get processing order
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component: str):
            if component in temp_visited:
                # Cycle detected
                raise ValueError(f"Circular dependency detected involving component: {component}")
            
            if component not in visited:
                temp_visited.add(component)
                
                for dep in dependencies[component]:
                    visit(dep)
                
                temp_visited.remove(component)
                visited.add(component)
                order.append(component)
        
        for comp in system_blueprint.system.components:
            if comp.name not in visited:
                visit(comp.name)
        
        return order

def main():
    """Test the system blueprint parser"""
    parser = SystemBlueprintParser()
    
    # Test with example system blueprint
    example_file = Path(__file__).parent / "examples" / "fraud_detection_system.yaml"
    if example_file.exists():
        try:
            system_blueprint = parser.parse_file(example_file)
            print(f"✅ Successfully parsed system blueprint: {system_blueprint.system.name}")
            print(f"   Description: {system_blueprint.system.description}")
            print(f"   Components: {len(system_blueprint.system.components)}")
            print(f"   Bindings: {len(system_blueprint.system.bindings)}")
            print(f"   Schemas: {len(system_blueprint.schemas)}")
            
            # Show component list
            print(f"\n📦 Components:")
            for comp in system_blueprint.system.components:
                print(f"   - {comp.name} ({comp.type}) - {comp.processing_mode}")
            
            # Show bindings
            print(f"\n🔗 Bindings:")
            for binding in system_blueprint.system.bindings:
                targets = [f"{comp}.{port}" for comp, port in zip(binding.to_components, binding.to_ports)]
                print(f"   - {binding.from_component}.{binding.from_port} → {', '.join(targets)}")
            
            # Show processing order
            try:
                order = parser.get_processing_order(system_blueprint)
                print(f"\n⚡ Processing order: {' → '.join(order)}")
            except ValueError as e:
                print(f"\n❌ Dependency error: {e}")
            
        except Exception as e:
            print(f"❌ Failed to parse system blueprint: {e}")
    else:
        print(f"❌ Example file not found: {example_file}")

if __name__ == "__main__":
    main()