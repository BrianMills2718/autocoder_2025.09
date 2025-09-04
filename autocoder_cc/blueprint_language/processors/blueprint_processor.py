"""
Blueprint Processor - Extracted from SystemGenerator monolith

Handles blueprint parsing and validation logic extracted from the 2000+ line monolith.
Provides clean interfaces for natural language processing, schema validation, and 
component requirement analysis.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path

from typing import TYPE_CHECKING

from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint
from autocoder_cc.observability import get_logger
from autocoder_cc.core.module_interfaces import IBlueprintValidator

if TYPE_CHECKING:
    from .blueprint_validator import BlueprintValidator


class BlueprintProcessor:
    """
    Blueprint processing module extracted from SystemGenerator monolith.
    
    Responsibilities:
    - Natural language blueprint processing (~250 lines from monolith)
    - Schema validation and compatibility checking (~200 lines from monolith)
    - Component requirement analysis (~150 lines from monolith) 
    - Healing integration coupling (~150 lines from monolith)
    
    Total extraction: ~750 lines from monolith
    """
    
    def __init__(self, validator: IBlueprintValidator):
        """Initialize blueprint processor with strict dependency injection"""
        self.logger = get_logger("blueprint_processor", component="BlueprintProcessor")
        
        # Require validator to be injected - no fallbacks
        if validator is None:
            raise ValueError("BlueprintValidator must be provided via dependency injection")
        
        self._validator = validator
        
        self.logger.info(
            "BlueprintProcessor initialized with dependency injection",
            operation="init"
        )
    
    def _get_validator(self) -> IBlueprintValidator:
        """Get validator instance (strictly injected)"""
        return self._validator
    
    def validate_blueprint(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Validate blueprint using comprehensive multi-stage validation.
        
        Extracted from SystemGenerator._validate_pre_generation method.
        
        Args:
            blueprint: Parsed system blueprint to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        self.logger.info(
            "Starting blueprint validation",
            operation="validate_blueprint",
            tags={"system_name": blueprint.system.name}
        )
        
        try:
            validator = self._get_validator()
            validation_errors = validator.validate_pre_generation(blueprint)
            
            self.logger.info(
                "Blueprint validation completed",
                operation="validate_blueprint_complete",
                tags={
                    "system_name": blueprint.system.name,
                    "errors_found": len(validation_errors)
                }
            )
            
            return validation_errors
            
        except Exception as e:
            self.logger.error(
                "Blueprint validation failed",
                error=e,
                operation="validate_blueprint_error",
                tags={"system_name": blueprint.system.name}
            )
            return [f"Blueprint validation error: {e}"]
    
    def process_blueprint(self, blueprint: ParsedSystemBlueprint, enable_healing: bool = True) -> ParsedSystemBlueprint:
        """
        Process blueprint with optional healing integration.
        
        Args:
            blueprint: Blueprint to process
            enable_healing: Whether to enable self-healing for issues
            
        Returns:
            Processed (and potentially healed) blueprint
        """
        self.logger.info(
            "Processing blueprint",
            operation="process_blueprint",
            tags={
                "system_name": blueprint.system.name,
                "healing_enabled": enable_healing
            }
        )
        
        if enable_healing:
            try:
                healed_blueprint = self._apply_basic_healing(blueprint)
                
                self.logger.info(
                    "Blueprint healing completed",
                    operation="process_blueprint_healing",
                    tags={"system_name": blueprint.system.name}
                )
                
                return healed_blueprint
                
            except Exception as e:
                self.logger.error(
                    "Blueprint healing failed",
                    error=e,
                    operation="process_blueprint_healing_error",
                    tags={"system_name": blueprint.system.name}
                )
                return blueprint
        
        return blueprint
    
    def process_natural_language_blueprint(self, natural_language_input: str) -> ParsedSystemBlueprint:
        """
        Process natural language blueprint description.
        
        Extracted from SystemGenerator natural language processing logic.
        
        Args:
            natural_language_input: Natural language description of system
            
        Returns:
            Parsed blueprint from natural language input
        """
        self.logger.info(
            "Processing natural language blueprint",
            operation="process_natural_language",
            tags={"input_length": len(natural_language_input)}
        )
        
        try:
            parsed_blueprint = self._parse_natural_language(natural_language_input)
            
            self.logger.info(
                "Natural language processing completed",
                operation="process_natural_language_complete",
                tags={"system_name": parsed_blueprint.system.name}
            )
            
            return parsed_blueprint
            
        except Exception as e:
            self.logger.error(
                "Natural language processing failed",
                error=e,
                operation="process_natural_language_error"
            )
            raise RuntimeError(f"Natural language processing failed: {e}") from e
    
    def _parse_natural_language(self, input_text: str) -> ParsedSystemBlueprint:
        """
        Parse natural language input into structured blueprint.
        
        Uses pattern matching and template-based approach to convert natural language
        descriptions into valid system blueprints.
        """
        import re
        from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
        
        # Extract system information from natural language
        system_name = self._extract_system_name(input_text)
        components = self._extract_components_from_text(input_text)
        bindings = self._extract_bindings_from_text(input_text, components)
        
        # Generate YAML blueprint
        blueprint_yaml = self._generate_blueprint_yaml(system_name, components, bindings)
        
        # Parse the generated YAML into a structured blueprint
        parser = SystemBlueprintParser()
        return parser.parse_string(blueprint_yaml)
    
    def _extract_system_name(self, text: str) -> str:
        """Extract system name from natural language description"""
        import re
        
        # Look for common patterns
        patterns = [
            r"create(?:\s+a)?\s+system(?:\s+called)?\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"build(?:\s+a)?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+system",
            r"system(?:\s+named)?\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).replace(' ', '_')
        
        # Default system name
        return "natural_language_system"
    
    def _extract_components_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract component definitions from natural language"""
        import re
        
        components = []
        
        # Common component patterns
        component_patterns = {
            r"api(?:\s+endpoint)?(?:\s+on)?\s+port\s+(\d+)": ("APIEndpoint", lambda m: {"port": int(m.group(1))}),
            r"database|data(?:\s+store)|storage": ("Store", lambda m: {"storage_type": "database"}),
            r"file(?:\s+store)|file(?:\s+storage)": ("Store", lambda m: {"storage_type": "file"}),
            r"data(?:\s+source)|source": ("Source", lambda m: {"count": 10}),
            r"transformer|processor": ("Transformer", lambda m: {"multiplier": 1}),
            r"model|ml(?:\s+model)|machine(?:\s+learning)": ("Model", lambda m: {"model_type": "classifier"}),
        }
        
        component_id = 1
        for pattern, (component_type, config_func) in component_patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                component_name = f"{component_type.lower()}_{component_id}"
                config = config_func(match)
                
                components.append({
                    "name": component_name,
                    "type": component_type, 
                    "description": f"Generated from: {match.group(0)}",
                    "configuration": config
                })
                component_id += 1
        
        # Ensure at least one component exists
        if not components:
            # CRITICAL FIX: Use placeholder that will be replaced by ResourceOrchestrator during generation
            # Use a special placeholder value that will be replaced by actual port allocation
            # in system_generator.py during Phase 0.5 port allocation
            default_port = None  # Will be replaced by ResourceOrchestrator during system generation
                
            components.append({
                "name": "default_api",
                "type": "APIEndpoint",
                "description": "Default API endpoint",
                "configuration": {"port": default_port} if default_port else {}
            })
        
        return components
    
    def _extract_bindings_from_text(self, text: str, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract component bindings from natural language"""
        bindings = []
        
        # Simple sequential binding for adjacent components
        for i in range(len(components) - 1):
            from_comp = components[i]
            to_comp = components[i + 1]
            
            bindings.append({
                "from": f"{from_comp['name']}.output",
                "to": f"{to_comp['name']}.input"
            })
        
        return bindings
    
    def _generate_blueprint_yaml(self, system_name: str, components: List[Dict[str, Any]], bindings: List[Dict[str, Any]]) -> str:
        """Generate YAML blueprint from extracted components"""
        import yaml
        
        blueprint = {
            "schema_version": "1.0.0",
            "system": {
                "name": system_name,
                "description": "Generated from natural language input",
                "version": "1.0.0",
                "components": components,
                "bindings": bindings
            }
        }
        
        return yaml.dump(blueprint, default_flow_style=False)
    
    def _apply_basic_healing(self, blueprint: ParsedSystemBlueprint) -> ParsedSystemBlueprint:
        """
        Apply basic blueprint healing to fix common issues.
        
        This provides self-healing functionality for common blueprint problems.
        """
        # Make a copy to avoid modifying the original
        import copy
        healed_blueprint = copy.deepcopy(blueprint)
        
        # Healing Rule 1: Add missing ports to APIEndpoint components
        for component in healed_blueprint.system.components:
            if component.type == 'APIEndpoint':
                if not component.config:
                    component.config = {}
                if 'port' not in component.config:
                    # CRITICAL FIX: Don't assign hardcoded port - let ResourceOrchestrator handle it
                    # The actual port will be allocated by ResourceOrchestrator during system generation
                    # Leave port unset so ResourceOrchestrator can allocate it properly
                    self.logger.info(
                        f"Healed: APIEndpoint '{component.name}' port will be allocated by ResourceOrchestrator during generation",
                        operation="healing_defer_port_allocation"
                    )
        
        # Healing Rule 2: Add missing storage_type to Store components  
        for component in healed_blueprint.system.components:
            if component.type == 'Store':
                if not component.config:
                    component.config = {}
                if 'storage_type' not in component.config:
                    component.config['storage_type'] = 'file'
                    self.logger.info(
                        f"Healed: Added default storage_type 'file' to Store '{component.name}'",
                        operation="healing_add_storage_type"
                    )
        
        # Healing Rule 3: Add missing model_type to Model components
        for component in healed_blueprint.system.components:
            if component.type == 'Model':
                if not component.config:
                    component.config = {}
                if 'model_type' not in component.config:
                    component.config['model_type'] = 'classifier'
                    self.logger.info(
                        f"Healed: Added default model_type 'classifier' to Model '{component.name}'",
                        operation="healing_add_model_type"
                    )
        
        return healed_blueprint
    
    def validate_blueprint_schemas(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Validate blueprint schemas and compatibility.
        
        Args:
            blueprint: Blueprint to validate schemas for
            
        Returns:
            List of schema validation errors
        """
        self.logger.info(
            "Validating blueprint schemas",
            operation="validate_schemas",
            tags={"system_name": blueprint.system.name}
        )
        
        try:
            schema_errors = self._validate_schemas(blueprint)
            
            self.logger.info(
                "Schema validation completed",
                operation="validate_schemas_complete",
                tags={
                    "system_name": blueprint.system.name,
                    "schema_errors": len(schema_errors)
                }
            )
            
            return schema_errors
            
        except Exception as e:
            self.logger.error(
                "Schema validation failed",
                error=e,
                operation="validate_schemas_error",
                tags={"system_name": blueprint.system.name}
            )
            return [f"Schema validation error: {e}"]
    
    def _validate_schemas(self, blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Internal schema validation logic.
        
        Extracted from SystemGenerator schema compatibility checking.
        """
        schema_errors = []
        
        if not hasattr(blueprint, 'schemas') or not blueprint.schemas:
            return schema_errors  # No schemas to validate
        
        # Validate schema compatibility in bindings
        for binding in blueprint.system.bindings:
            # Find source component output schema
            from_comp = next((c for c in blueprint.system.components if c.name == binding.from_component), None)
            if from_comp and hasattr(from_comp, 'outputs') and from_comp.outputs:
                from_output = next((o for o in from_comp.outputs if o.name == binding.from_port), None)
                if from_output:
                    from_schema = from_output.schema
                    
                    # Check each target component input schema
                    for i, to_component in enumerate(binding.to_components):
                        to_comp = next((c for c in blueprint.system.components if c.name == to_component), None)
                        if to_comp and hasattr(to_comp, 'inputs') and to_comp.inputs and i < len(binding.to_ports):
                            to_input = next((inp for inp in to_comp.inputs if inp.name == binding.to_ports[i]), None)
                            if to_input and not self._are_schemas_compatible(from_schema, to_input.schema):
                                schema_errors.append(
                                    f"Schema mismatch in binding: {binding.from_component}.{binding.from_port} "
                                    f"({from_schema}) -> {to_component}.{binding.to_ports[i]} ({to_input.schema})"
                                )
        
        return schema_errors
    
    def _are_schemas_compatible(self, from_schema: str, to_schema: str) -> bool:
        """
        Check if two schemas are compatible for binding connections.
        
        Uses shared schema utility to prevent code duplication.
        """
        from .schema_utils import are_schemas_compatible
        return are_schemas_compatible(from_schema, to_schema)
    
    def analyze_component_requirements(self, blueprint: ParsedSystemBlueprint) -> Dict[str, Any]:
        """
        Analyze component dependencies and configuration requirements.
        
        Args:
            blueprint: Blueprint to analyze
            
        Returns:
            Dictionary containing component requirements analysis
        """
        self.logger.info(
            "Analyzing component requirements",
            operation="analyze_requirements",
            tags={"system_name": blueprint.system.name}
        )
        
        requirements = {
            'components': {},
            'dependencies': {},
            'configurations': {}
        }
        
        try:
            for component in blueprint.system.components:
                component_name = component.name
                component_type = component.type
                
                # Analyze component-specific requirements
                requirements['components'][component_name] = {
                    'type': component_type,
                    'inputs': len(component.inputs) if hasattr(component, 'inputs') and component.inputs else 0,
                    'outputs': len(component.outputs) if hasattr(component, 'outputs') and component.outputs else 0,
                    'config_keys': list(component.config.keys()) if component.config else []
                }
                
                # Analyze dependencies (connections to other components)
                incoming_connections = []
                outgoing_connections = []
                
                for binding in blueprint.system.bindings:
                    if component_name in binding.to_components:
                        incoming_connections.append(binding.from_component)
                    if binding.from_component == component_name:
                        outgoing_connections.extend(binding.to_components)
                
                requirements['dependencies'][component_name] = {
                    'incoming': incoming_connections,
                    'outgoing': outgoing_connections
                }
                
                # Analyze configuration requirements
                config_requirements = self._get_component_config_requirements(component_type)
                requirements['configurations'][component_name] = config_requirements
            
            self.logger.info(
                "Component requirements analysis completed",
                operation="analyze_requirements_complete",
                tags={
                    "system_name": blueprint.system.name,
                    "components_analyzed": len(requirements['components'])
                }
            )
            
            return requirements
            
        except Exception as e:
            self.logger.error(
                "Component requirements analysis failed",
                error=e,
                operation="analyze_requirements_error",
                tags={"system_name": blueprint.system.name}
            )
            return requirements
    
    def _get_component_config_requirements(self, component_type: str) -> Dict[str, Any]:
        """
        Get configuration requirements for a specific component type.
        
        Extracted from SystemGenerator configuration validation logic.
        """
        requirements = {
            'required_configs': [],
            'optional_configs': [],
            'validation_rules': []
        }
        
        # Component-specific configuration requirements
        if component_type == 'Store':
            requirements['required_configs'] = ['storage_type']
            requirements['optional_configs'] = ['storage_path', 'connection_string']
            requirements['validation_rules'] = ['storage_type must be one of: file, memory, database']
        
        elif component_type == 'APIEndpoint':
            requirements['required_configs'] = ['port']
            requirements['optional_configs'] = ['host', 'routes', 'middleware']
            requirements['validation_rules'] = ['port must be integer between 1024-65535']
        
        elif component_type == 'Model':
            requirements['required_configs'] = ['model_type']
            requirements['optional_configs'] = ['model_path', 'inference_type', 'threshold']
            requirements['validation_rules'] = ['model_type must be specified']
        
        return requirements