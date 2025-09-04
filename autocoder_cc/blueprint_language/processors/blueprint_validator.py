"""
Blueprint Validator - Extracted from SystemGenerator monolith

Provides comprehensive blueprint validation logic extracted from the monolithic SystemGenerator.
Includes component registry validation, connection validation, and configuration validation.
"""
from typing import List, Dict, Any, Set
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint
from autocoder_cc.components.component_registry import component_registry
from autocoder_cc.observability import get_logger


class BlueprintValidator:
    """
    Blueprint validation module extracted from SystemGenerator monolith.
    
    Responsibilities extracted from SystemGenerator._validate_pre_generation (~500 lines):
    - ComponentRegistry validation with multi-stage lifecycle
    - Dangling component detection and connection validation
    - Configuration completeness validation
    - Schema compatibility validation
    - Resource conflict detection
    """
    
    def __init__(self):
        """Initialize blueprint validator with logger"""
        self.logger = get_logger("blueprint_validator", component="BlueprintValidator")
        
        self.logger.info(
            "BlueprintValidator initialized with comprehensive validation rules",
            operation="init"
        )
    
    def validate_pre_generation(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Comprehensive pre-generation blueprint validation.
        
        Extracted from SystemGenerator._validate_pre_generation method.
        This is the main validation entry point that runs all validation phases.
        
        Args:
            blueprint: Parsed system blueprint to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        self.logger.info(
            "Starting comprehensive pre-generation validation",
            operation="validate_pre_generation",
            tags={"system_name": blueprint.system.name}
        )
        
        validation_errors = []
        
        try:
            # Phase 0: ComponentRegistry validation - fail hard on registry issues
            registry_errors = self._validate_component_registry(blueprint)
            validation_errors.extend(registry_errors)
            
            # Phase 1: Connection and topology validation
            connection_errors = self._validate_component_connections(blueprint)
            validation_errors.extend(connection_errors)
            
            # Phase 2: Configuration completeness validation
            config_errors = self._validate_configuration_completeness(blueprint)
            validation_errors.extend(config_errors)
            
            # Phase 3: Component type compatibility validation
            compatibility_errors = self._validate_component_compatibility(blueprint)
            validation_errors.extend(compatibility_errors)
            
            # Phase 4: Resource conflict detection
            resource_errors = self._validate_resource_conflicts(blueprint)
            validation_errors.extend(resource_errors)
            
            # Phase 5: Schema compatibility validation (if schemas exist)
            if hasattr(blueprint, 'schemas') and blueprint.schemas:
                schema_errors = self._validate_schema_compatibility(blueprint)
                validation_errors.extend(schema_errors)
            
            self.logger.info(
                "Pre-generation validation completed",
                operation="validate_pre_generation_complete",
                tags={
                    "system_name": blueprint.system.name,
                    "total_errors": len(validation_errors),
                    "registry_errors": len(registry_errors),
                    "connection_errors": len(connection_errors),
                    "config_errors": len(config_errors),
                    "compatibility_errors": len(compatibility_errors),
                    "resource_errors": len(resource_errors)
                }
            )
            
            return validation_errors
            
        except Exception as e:
            error_msg = f"Pre-generation validation failed with exception: {e}"
            self.logger.error(
                "Pre-generation validation exception",
                error=e,
                operation="validate_pre_generation_error",
                tags={"system_name": blueprint.system.name}
            )
            return [error_msg]
    
    def _validate_component_registry(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 0: ComponentRegistry validation with multi-stage lifecycle.
        
        Extracted from SystemGenerator ComponentRegistry validation section.
        """
        validation_errors = []
        system = blueprint.system
        
        try:
            # Convert ParsedSystemBlueprint to dict for registry validation
            blueprint_dict = {
                'system': {
                    'name': system.name,
                    'components': [
                        {
                            'name': comp.name,
                            'type': comp.type,
                            'config': comp.config or {}
                        }
                        for comp in system.components
                    ],
                    'bindings': [
                        {
                            'from_component': binding.from_component,
                            'from_port': binding.from_port,
                            'to_components': binding.to_components,
                            'to_ports': binding.to_ports
                        }
                        for binding in system.bindings
                    ]
                },
                'policy': getattr(blueprint, 'policy', {})
            }
            
            # Validate all components can be created via registry
            for component_config in blueprint_dict['system']['components']:
                try:
                    # Validate component type is registered
                    component_type = component_config['type']
                    if not component_registry._component_classes.get(component_type):
                        validation_errors.append(
                            f"Component type '{component_type}' not registered in ComponentRegistry. "
                            f"Available types: {list(component_registry._component_classes.keys())}"
                        )
                        continue
                    
                    # Stage 1: Implementation Validation
                    # Stage 2: Configuration Validation  
                    component_registry._validate_component_config(component_type, component_config['config'])
                    
                    # Stage 3: Dependency Validation (lightweight check)
                    component_registry._validate_external_dependencies(
                        component_config['name'], 
                        component_config['config']
                    )
                    
                except Exception as e:
                    validation_errors.append(f"ComponentRegistry validation failed for '{component_config['name']}': {e}")
            
            # System-level policy validation
            if hasattr(component_registry, 'validate_system_against_blueprint_policy'):
                try:
                    component_registry.validate_system_against_blueprint_policy(blueprint_dict)
                except Exception as e:
                    validation_errors.append(f"System policy validation failed: {e}")
                    
        except Exception as e:
            validation_errors.append(f"ComponentRegistry pre-generation validation failed: {e}")
        
        return validation_errors
    
    def validate_component_connections(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Public interface for component connection validation.
        """
        return self._validate_component_connections(blueprint)
    
    def _validate_component_connections(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 1: Component connection and topology validation.
        
        Extracted from SystemGenerator dangling component detection logic.
        """
        validation_errors = []
        system = blueprint.system
        
        # Find all connected components
        connected_components = set()
        
        # Find components referenced in bindings
        for binding in system.bindings:
            connected_components.add(binding.from_component)
            connected_components.update(binding.to_components)
        
        # Check for components that have inputs/outputs but aren't connected
        for comp in system.components:
            # Sources and Sinks are allowed to be "dangling" - they're endpoints
            # Store components are terminal components like Sinks - they receive data but don't output it
            if comp.type in ['Source', 'Sink', 'EventSource', 'Store']:
                continue
            
            # APIEndpoints are also allowed to be unconnected (external interface)
            if comp.type == 'APIEndpoint':
                continue
            
            # Controllers can be unconnected if they provide services (like auth/authorization)
            if comp.type == 'Controller':
                continue
                
            # Other components should be connected if they have inputs/outputs
            if comp.name not in connected_components:
                if (hasattr(comp, 'inputs') and comp.inputs) or (hasattr(comp, 'outputs') and comp.outputs):
                    validation_errors.append(
                        f"Component '{comp.name}' has inputs/outputs but is not connected to any other components"
                    )
        
        # Validate circular dependencies (informational - allowed in V5.2)
        circular_info = self._check_circular_dependencies(system.bindings)
        if circular_info:
            # Note: Not adding as error since circular dependencies are allowed in stream architecture
            self.logger.info(
                "Circular dependencies detected (allowed in stream architecture)",
                operation="circular_dependency_info",
                tags={"circular_paths": circular_info}
            )
        
        return validation_errors
    
    def _check_circular_dependencies(self, bindings) -> List[str]:
        """
        Check for circular dependencies in bindings.
        Returns information about cycles but doesn't treat them as errors.
        """
        # Build adjacency list
        graph = {}
        for binding in bindings:
            if binding.from_component not in graph:
                graph[binding.from_component] = []
            graph[binding.from_component].extend(binding.to_components)
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found cycle - extract cycle path
                cycle_start = path.index(node)
                cycle_path = path[cycle_start:] + [node]
                cycles.append(" -> ".join(cycle_path))
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def validate_configuration_completeness(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Public interface for configuration validation.
        """
        return self._validate_configuration_completeness(blueprint)
    
    def _validate_configuration_completeness(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 2: Configuration completeness validation.
        
        Extracted from SystemGenerator missing configuration validation logic.
        """
        validation_errors = []
        system = blueprint.system
        
        for comp in system.components:
            component_config = comp.config or {}
            
            # Store components should have database type specified (Phase 2C: Updated validation)
            if comp.type == 'Store':
                # Check for any valid database configuration format
                has_db_config = (
                    component_config.get('storage_type') or  # Legacy format
                    component_config.get('database_type') or  # Current format
                    (isinstance(component_config.get('_database'), dict) and 
                     component_config.get('_database', {}).get('type'))  # V5.0+ format
                )
                if not has_db_config:
                    validation_errors.append(
                        f"Store component '{comp.name}' missing database configuration. "
                        f"Provide one of: 'database_type', 'storage_type', or '_database.type'"
                    )
            
            # APIEndpoint components should have port specified
            elif comp.type == 'APIEndpoint':
                if not component_config.get('port'):
                    validation_errors.append(
                        f"APIEndpoint component '{comp.name}' missing required 'port' configuration"
                    )
            
            # Model components should have model-related configuration
            elif comp.type == 'Model':
                model_configs = ['model_path', 'model_type', 'inference_type']
                if not any(component_config.get(config) for config in model_configs):
                    validation_errors.append(
                        f"Model component '{comp.name}' missing model configuration (model_path, model_type, or inference_type)"
                    )
        
        return validation_errors
    
    def _validate_component_compatibility(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 3: Component type compatibility validation.
        
        Extracted from SystemGenerator component compatibility logic.
        """
        validation_errors = []
        system = blueprint.system
        
        component_types = [comp.type for comp in system.components]
        
        # Systems with Models should have at least one Source or APIEndpoint for input
        if 'Model' in component_types:
            input_types = ['Source', 'APIEndpoint', 'EventSource']
            if not any(comp_type in component_types for comp_type in input_types):
                validation_errors.append(
                    "System contains Model components but no input components (Source, APIEndpoint, EventSource)"
                )
        
        return validation_errors
    
    def _validate_resource_conflicts(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 4: Resource conflict detection.
        
        Extracted from SystemGenerator resource conflict validation logic.
        """
        validation_errors = []
        system = blueprint.system
        
        # Check for port conflicts
        api_ports = []
        for comp in system.components:
            if comp.type == 'APIEndpoint':
                port = comp.config.get('port') if comp.config else None
                if port:
                    if port in api_ports:
                        validation_errors.append(
                            f"Port conflict: Multiple APIEndpoint components using port {port}"
                        )
                    api_ports.append(port)
        
        return validation_errors
    
    def _validate_schema_compatibility(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Phase 5: Schema compatibility validation.
        
        Extracted from SystemGenerator schema validation logic.
        """
        validation_errors = []
        system = blueprint.system
        
        if not hasattr(blueprint, 'schemas') or not blueprint.schemas:
            return validation_errors
        
        for binding in system.bindings:
            # Find source component output schema
            from_comp = next((c for c in system.components if c.name == binding.from_component), None)
            if from_comp and hasattr(from_comp, 'outputs') and from_comp.outputs:
                from_output = next((o for o in from_comp.outputs if o.name == binding.from_port), None)
                if from_output:
                    from_schema = from_output.schema
                    
                    # Check each target component input schema
                    for i, to_component in enumerate(binding.to_components):
                        to_comp = next((c for c in system.components if c.name == to_component), None)
                        if to_comp and hasattr(to_comp, 'inputs') and to_comp.inputs and i < len(binding.to_ports):
                            to_input = next((inp for inp in to_comp.inputs if inp.name == binding.to_ports[i]), None)
                            if to_input and not self._are_schemas_compatible(from_schema, to_input.schema):
                                validation_errors.append(
                                    f"Schema mismatch in binding: {binding.from_component}.{binding.from_port} "
                                    f"({from_schema}) -> {to_component}.{binding.to_ports[i]} ({to_input.schema})"
                                )
        
        return validation_errors
    
    def _are_schemas_compatible(self, from_schema: str, to_schema: str) -> bool:
        """
        Check if two schemas are compatible for binding connections.
        
        Uses shared schema utility to prevent code duplication.
        """
        from .schema_utils import are_schemas_compatible
        return are_schemas_compatible(from_schema, to_schema)