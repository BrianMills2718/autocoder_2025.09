#!/usr/bin/env python3
"""
Blueprint Healer - Heals common blueprint validation errors before parsing
"""
from typing import Dict, Any, List
from autocoder_cc.observability.structured_logging import get_logger
from autocoder_cc.core.config import Settings

logger = get_logger(__name__)
settings = Settings()


class BlueprintHealer:
    """Heal common blueprint validation errors"""

    def __init__(self):
        """Initialize the BlueprintHealer with matrix checking capabilities"""
        from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator
        self.validator = ArchitecturalValidator()
        self.rejected_bindings = set()  # Track what we've already rejected
        self.generated_bindings = set()  # Track what we've already generated
        self.logger = logger
        self.healing_history = []  # Track healing operations across attempts
        self.stagnation_count = 0  # Track when no progress is made
        
    def _is_connection_allowed(self, from_type: str, to_type: str) -> bool:
        """Check if connection is allowed by CONNECTIVITY_MATRIX"""
        matrix = self.validator.CONNECTIVITY_MATRIX
        from_rules = matrix.get(from_type, {})
        to_rules = matrix.get(to_type, {})
        
        # Must be allowed in BOTH directions
        can_connect = to_type in from_rules.get('can_connect_to', [])
        can_receive = from_type in to_rules.get('can_receive_from', [])
        
        return can_connect and can_receive
    
    def _should_create_binding(self, from_comp_name: str, from_comp_type: str, 
                              to_comp_name: str, to_comp_type: str) -> bool:
        """Check if we should create a binding between components"""
        # Check if already rejected
        binding_key = (from_comp_name, to_comp_name)
        if binding_key in self.rejected_bindings:
            return False
        
        # Check if already generated
        if binding_key in self.generated_bindings:
            return False
        
        # CHECK MATRIX RULES!
        if not self._is_connection_allowed(from_comp_type, to_comp_type):
            self.rejected_bindings.add(binding_key)
            self.logger.debug(f"Rejected {from_comp_type}→{to_comp_type}: not allowed by matrix")
            return False
        
        # Mark as generated to prevent duplicates
        self.generated_bindings.add(binding_key)
        return True

    def _is_stagnating(self, operations: List[str]) -> bool:
        """Check if healing is stagnating (making no progress)"""
        if not operations:
            # No operations performed means we made no changes
            self.stagnation_count += 1
        elif self.healing_history and operations == self.healing_history[-1]:
            # Same operations as last time - we're in a loop
            self.stagnation_count += 1
            self.logger.warning(f"Detected healing loop - repeating same operations")
        else:
            # Different operations performed - progress was made
            self.stagnation_count = 0
            
        # Add current operations to history
        self.healing_history.append(operations.copy() if operations else operations)
        
        # Stagnation if we've made no progress for 2 attempts
        if self.stagnation_count >= 2:
            self.logger.warning(f"Healing stagnated after {len(self.healing_history)} attempts")
            return True
            
        return False

    def heal_blueprint(self, blueprint_dict: dict, phase: str = 'all') -> dict:
        """
        Fix common blueprint issues based on phase.
        
        Phases:
        - 'structural': Fix missing components, bindings, format issues (before port gen)
        - 'schema': Fix schema mismatches, add transformations (after port gen)
        - 'all': Run both phases (default for backward compatibility)

        Args:
            blueprint_dict: The raw blueprint dictionary from YAML
            phase: Which healing phase to run ('structural', 'schema', or 'all')

        Returns:
            Healed blueprint dictionary
        """
        logger.info(f"Starting blueprint healing process (phase: {phase})")

        # Track healing operations for debugging
        operations = []

        # Phase: STRUCTURAL (before port generation)
        if phase in ['structural', 'all']:
            # Fix schema_version placement
            healed = self._fix_schema_version_placement(blueprint_dict)
            if healed != blueprint_dict:
                operations.append("Fixed schema_version placement")
                blueprint_dict = healed

            # Add missing schema_version
            if "schema_version" not in blueprint_dict:
                blueprint_dict["schema_version"] = "1.0.0"
                operations.append("Added missing schema_version")

            # Fix version format (1.0 -> 1.0.0)
            if blueprint_dict.get("schema_version") == "1.0":
                blueprint_dict["schema_version"] = "1.0.0"
                operations.append("Fixed schema_version format from 1.0 to 1.0.0")

            # Add missing policy block
            if "policy" not in blueprint_dict:
                blueprint_dict["policy"] = self._get_default_policy()
                operations.append("Added missing policy block")

            # Fix empty bindings and generate missing ones
            if "bindings" in blueprint_dict:
                healed_bindings = self._heal_bindings(blueprint_dict["bindings"])
                if healed_bindings != blueprint_dict["bindings"]:
                    blueprint_dict["bindings"] = healed_bindings
                    operations.append("Healed bindings")
            
            # CRITICAL FIX: Generate missing bindings based on component types
            if "system" in blueprint_dict and "components" in blueprint_dict["system"]:
                # Get existing bindings from system block
                existing_bindings = blueprint_dict["system"].get("bindings", [])
                
                missing_bindings = self._generate_missing_bindings(
                    blueprint_dict["system"]["components"], 
                    existing_bindings
                )
                if missing_bindings:
                    if "bindings" not in blueprint_dict["system"]:
                        blueprint_dict["system"]["bindings"] = []
                    blueprint_dict["system"]["bindings"].extend(missing_bindings)
                    operations.append(f"Generated {len(missing_bindings)} missing bindings")

            # Add missing terminal components (CRITICAL for valid architecture)
            if self._add_missing_terminal_component(blueprint_dict):
                operations.append("Added missing terminal component (sink/store)")

            # Connect orphaned components
            connections_added = self._connect_orphaned_components(blueprint_dict)
            if connections_added > 0:
                operations.append(f"Connected {connections_added} orphaned components")

            # Fix system block issues
            if "system" in blueprint_dict:
                healed_system = self._heal_system_block(blueprint_dict["system"])
                if healed_system != blueprint_dict["system"]:
                    blueprint_dict["system"] = healed_system
                    operations.append("Healed system block")

        # Phase: SCHEMA (after port generation)
        if phase in ['schema', 'all']:
            # Fix schema compatibility issues between connected components
            # This requires ports to already exist
            if "system" in blueprint_dict:
                schema_healed = self._heal_schema_compatibility(blueprint_dict["system"])
                if schema_healed != blueprint_dict["system"]:
                    blueprint_dict["system"] = schema_healed
                    operations.append("Fixed schema compatibility issues")

        # Check for stagnation before returning
        if self._is_stagnating(operations):
            logger.warning("Healing may be stagnating - limited operations performed")
            # Clear the generated/rejected sets for next attempt to allow retrying with different strategies
            # But keep the history to track patterns
            if self.stagnation_count >= 3:
                logger.error("Maximum stagnation count reached - stopping healing to prevent infinite loops")
                # Don't clear sets on final stagnation to prevent error cascades
        
        if operations:
            logger.info(f"Blueprint healing completed with {len(operations)} operations: {', '.join(operations)}")
        else:
            logger.info("Blueprint healing completed - no issues found")

        return blueprint_dict

    def _fix_schema_version_placement(self, blueprint_dict: dict) -> dict:
        """Fix schema_version that's incorrectly placed inside system block"""
        if "system" in blueprint_dict and isinstance(blueprint_dict["system"], dict):
            if "schema_version" in blueprint_dict["system"]:
                # Move schema_version to root level
                result = blueprint_dict.copy()
                result["schema_version"] = result["system"].pop("schema_version")
                logger.debug("Moved schema_version from system block to root level")
                return result
        return blueprint_dict

    def _get_default_policy(self) -> Dict[str, Any]:
        """Get default policy block for blueprints"""
        return {
            "security": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "authentication_required": True
            },
            "resource_limits": {
                "max_memory_per_component": "512Mi",
                "max_cpu_per_component": "500m"
            },
            "validation": {
                "strict_mode": True
            }
        }

    def _heal_bindings(self, bindings: Any) -> List[Dict[str, Any]]:
        """Heal binding issues"""
        if not bindings:
            return []

        if not isinstance(bindings, list):
            logger.warning(f"Bindings is not a list: {type(bindings)}")
            return []

        healed_bindings = []
        for binding in bindings:
            if isinstance(binding, dict):
                # Fix empty binding objects
                if not binding:
                    logger.debug("Skipping empty binding object")
                    continue

                # Ensure required fields exist
                if "from" in binding and "to" in binding:
                    healed_bindings.append(binding)
                elif "from_component" in binding and "to_component" in binding:
                    # Convert old format to new format
                    healed_binding = {
                        "from": f"{binding['from_component']}.{binding.get('from_port', 'output')}",
                        "to": f"{binding['to_component']}.{binding.get('to_port', 'input')}"
                    }
                    healed_bindings.append(healed_binding)
                    logger.debug(f"Converted binding format: {healed_binding}")
                else:
                    logger.warning(f"Invalid binding structure: {binding}")
            else:
                logger.warning(f"Binding is not a dict: {type(binding)}")

        return healed_bindings

    def _add_missing_terminal_component(self, blueprint_dict: dict) -> bool:
        """
        Add a sink or store if none exists (required for valid architecture)
        
        Returns:
            True if a component was added, False otherwise
        """
        components = blueprint_dict.get("system", {}).get("components", [])
        
        # Check if any terminal component exists
        has_terminal = any(
            c.get("type") in ["Sink", "Store"] 
            for c in components
        )
        
        if not has_terminal:
            # Analyze existing components to determine appropriate terminal type
            has_api = any(c.get("type") == "APIEndpoint" for c in components)
            has_transformer = any(c.get("type") == "Transformer" for c in components)
            
            if has_api or has_transformer:
                # Add Store for persistence (more useful than pure Sink)
                components.append({
                    "name": "primary_store",
                    "type": "Store",
                    "description": "Primary data storage for processed information"
                })
                self.logger.info("Added missing Store component for data persistence")
            else:
                # Add simple Sink for data termination
                components.append({
                    "name": "data_sink",
                    "type": "Sink", 
                    "description": "Terminal component for data flow"
                })
                self.logger.info("Added missing Sink component for data termination")
            return True
        return False

    def _connect_orphaned_components(self, blueprint_dict: dict) -> int:
        """
        Connect orphaned sources to available sinks/stores
        
        Returns:
            Number of new connections created
        """
        components = blueprint_dict.get("system", {}).get("components", [])
        bindings = blueprint_dict.get("system", {}).get("bindings", [])
        
        if not bindings:
            blueprint_dict["system"]["bindings"] = []
            bindings = blueprint_dict["system"]["bindings"]
        
        # Find orphaned sources and terminals
        sources = [c for c in components if c.get("type") in ["Source", "EventSource"]]
        terminals = [c for c in components if c.get("type") in ["Sink", "Store"]]
        
        new_connections = 0
        
        for source in sources:
            source_name = source.get("name")
            # Check if source is already connected
            has_connection = any(
                b.get("from") == f"{source_name}.output" or
                b.get("from_component") == source_name
                for b in bindings
            )
            
            if not has_connection and terminals:
                # Connect to first available terminal
                terminal = terminals[0]
                bindings.append({
                    "from": f"{source_name}.output",
                    "to": f"{terminal.get('name')}.input",
                    "description": f"Auto-healed: Connect orphaned {source_name} to {terminal.get('name')}"
                })
                new_connections += 1
                self.logger.info(f"Connected orphaned source {source_name} to {terminal.get('name')}")
        
        return new_connections

    def _generate_missing_bindings(self, components: List[Dict[str, Any]], existing_bindings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate missing bindings based on component types and data flow patterns
        
        Creates logical connections between components based on their types:
        - Source → Transformer → Sink chains
        - APIEndpoint → Store connections for data persistence
        - Controller → other components for orchestration
        
        Args:
            components: List of component dictionaries
            existing_bindings: List of existing binding dictionaries
            
        Returns:
            List of newly generated binding dictionaries
        """
        if not components:
            return []
            
        logger.info(f"Analyzing {len(components)} components for missing bindings")
        
        # Parse existing bindings to avoid duplicates
        existing_connections = set()
        for binding in existing_bindings:
            if isinstance(binding, dict):
                if "from" in binding and "to" in binding:
                    # New format: "component.port"
                    existing_connections.add((binding["from"], binding["to"]))
                elif "from_component" in binding:
                    # Handle both to_component (singular) and to_components (plural)
                    from_port = binding.get("from_port", "output")
                    
                    # Check for to_components (plural - array format)
                    if "to_components" in binding:
                        to_components = binding.get("to_components", [])
                        to_ports = binding.get("to_ports", ["input"] * len(to_components))
                        for to_comp, to_port in zip(to_components, to_ports):
                            existing_connections.add((f"{binding['from_component']}.{from_port}", f"{to_comp}.{to_port}"))
                    # Check for to_component (singular - legacy format)
                    elif "to_component" in binding:
                        to_port = binding.get("to_port", "input")
                        existing_connections.add((f"{binding['from_component']}.{from_port}", f"{binding['to_component']}.{to_port}"))
        
        # Categorize components by type
        sources = [c for c in components if c.get("type") == "Source"]
        transformers = [c for c in components if c.get("type") == "Transformer"]
        
        # ADR 033: Stop-gap - conditionally treat Store as Sink based on flag
        if settings.HEAL_STORE_AS_SINK:
            sinks = [c for c in components if c.get("type") in {"Sink", "Store"}]
        else:
            sinks = [c for c in components if c.get("type") == "Sink"]
            
        api_endpoints = [c for c in components if c.get("type") == "APIEndpoint"]
        stores = [c for c in components if c.get("type") == "Store"]
        controllers = [c for c in components if c.get("type") == "Controller"]
        
        new_bindings = []
        
        # Pattern 1: Source → Transformer → Sink chains
        if sources and sinks:
            for source in sources:
                source_name = source.get("name")
                if not source_name:
                    continue
                    
                # Find best target (prefer Transformer, then Sink)
                target = None
                if transformers:
                    target = transformers[0]  # Use first transformer
                    target_port = "input"
                elif sinks:
                    target = sinks[0]  # Use first sink
                    target_port = "input"
                
                if target and target.get("name"):
                    # Check if this binding is allowed by the matrix
                    if self._should_create_binding(source_name, source.get("type"), 
                                                  target['name'], target.get("type")):
                        connection = (f"{source_name}.output", f"{target['name']}.{target_port}")
                        if connection not in existing_connections:
                            new_bindings.append({
                                "from_component": source_name,
                                "from_port": "output",
                                "to_components": [target['name']],
                                "to_ports": [target_port],
                                "description": f"Auto-generated: {source_name} data flow to {target['name']}",
                                "generated_by": "healer_initial"  # ADR 033: Binding provenance
                            })
                            existing_connections.add(connection)
                            logger.info(f"Generated binding: {connection[0]} → {connection[1]}")
        
        # Pattern 2: Transformer → Sink connections
        if transformers and sinks:
            for transformer in transformers:
                transformer_name = transformer.get("name")
                if not transformer_name:
                    continue
                    
                # Connect to first available sink
                for sink in sinks:
                    sink_name = sink.get("name")
                    if not sink_name:
                        continue
                        
                    # Check if this binding is allowed by the matrix
                    if self._should_create_binding(transformer_name, transformer.get("type"), 
                                                  sink_name, sink.get("type")):
                        connection = (f"{transformer_name}.output", f"{sink_name}.input")
                        if connection not in existing_connections:
                            new_bindings.append({
                                "from_component": transformer_name,
                                "from_port": "output",
                                "to_components": [sink_name],
                                "to_ports": ["input"],
                                "description": f"Auto-generated: {transformer_name} processed data to {sink_name}",
                                "generated_by": "healer_initial"  # ADR 033: Binding provenance
                            })
                            existing_connections.add(connection)
                            logger.info(f"Generated binding: {connection[0]} → {connection[1]}")
                            break  # Only connect to first sink to avoid duplicates
        
        # Pattern 3: APIEndpoint → Store connections for data persistence
        if api_endpoints and stores:
            for api in api_endpoints:
                api_name = api.get("name")
                if not api_name:
                    continue
                    
                # Connect to first available store
                for store in stores:
                    store_name = store.get("name")
                    if not store_name:
                        continue
                        
                    # Bidirectional connection for API-Store interaction
                    connections = [
                        (f"{api_name}.request", f"{store_name}.query"),
                        (f"{store_name}.response", f"{api_name}.data")
                    ]
                    
                    for connection in connections:
                        if connection not in existing_connections:
                            from_comp, from_port = connection[0].split('.')
                            to_comp, to_port = connection[1].split('.')
                            new_bindings.append({
                                "from_component": from_comp,
                                "from_port": from_port,
                                "to_components": [to_comp],
                                "to_ports": [to_port],
                                "description": f"Auto-generated: {api_name} ↔ {store_name} data persistence",
                                "generated_by": "healer_initial"  # ADR 033: Binding provenance
                            })
                            existing_connections.add(connection)
                            logger.info(f"Generated binding: {connection[0]} → {connection[1]}")
                            
                    break  # Only connect to first store to avoid duplicates
        
        # Pattern 4: Controller orchestration patterns
        if controllers:
            for controller in controllers:
                controller_name = controller.get("name")
                if not controller_name:
                    continue
                    
                # Controllers can coordinate with other components
                other_components = [c for c in components if c.get("type") not in ["Controller"] and c.get("name")]
                
                for target in other_components[:2]:  # Limit to 2 connections to avoid complexity
                    target_name = target.get("name")
                    if not target_name:
                        continue
                        
                    # Check if this binding is allowed by the matrix
                    if self._should_create_binding(controller_name, controller.get("type"), 
                                                  target_name, target.get("type")):
                        connection = (f"{controller_name}.control", f"{target_name}.control")
                        if connection not in existing_connections:
                            new_bindings.append({
                                "from_component": controller_name,
                                "from_port": "control",
                                "to_components": [target_name],
                                "to_ports": ["control"],
                                "description": f"Auto-generated: {controller_name} orchestration of {target_name}",
                                "generated_by": "healer_initial"  # ADR 033: Binding provenance
                            })
                            existing_connections.add(connection)
                            logger.info(f"Generated binding: {connection[0]} → {connection[1]}")
        
        logger.info(f"Generated {len(new_bindings)} missing bindings")
        return new_bindings

    def _heal_system_block(self, system: Dict[str, Any]) -> Dict[str, Any]:
        """Heal common system block issues"""
        # Ensure required fields
        if "name" not in system:
            system["name"] = "generated_system"
            logger.debug("Added missing system name")

        if "version" not in system:
            system["version"] = "1.0.0"
            logger.debug("Added missing system version")

        if "description" not in system:
            system["description"] = "System generated from natural language"
            logger.debug("Added missing system description")

        # Ensure components is a list
        if "components" in system and not isinstance(system["components"], list):
            logger.warning("Components is not a list, converting to empty list")
            system["components"] = []

        # Heal each component
        if "components" in system:
            healed_components = []
            for comp in system["components"]:
                if isinstance(comp, dict):
                    healed_comp = self._heal_component(comp)
                    healed_components.append(healed_comp)
                else:
                    logger.warning(f"Component is not a dict: {type(comp)}")
            system["components"] = healed_components

        return system

    def _heal_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Heal individual component issues"""
        # Ensure required fields
        if "name" not in component:
            component["name"] = "unnamed_component"
            logger.debug("Added missing component name")

        if "type" not in component:
            component["type"] = "Transformer"
            logger.debug("Added missing component type")

        # Fix common type casing issues
        type_map = {
            'source': 'Source',
            'transformer': 'Transformer',
            'accumulator': 'Accumulator',
            'store': 'Store',
            'controller': 'Controller',
            'sink': 'Sink',
            'streamprocessor': 'StreamProcessor',
            'model': 'Model',
            'apiendpoint': 'APIEndpoint',
            'api_endpoint': 'APIEndpoint',
            'router': 'Router'
        }

        if component["type"].lower() in type_map:
            original_type = component["type"]
            component["type"] = type_map[component["type"].lower()]
            logger.debug(f"Fixed component type casing: {original_type} -> {component['type']}")

        # Ensure inputs/outputs are lists
        if "inputs" in component and not isinstance(component["inputs"], list):
            component["inputs"] = []
            logger.debug("Fixed component inputs to be a list")

        if "outputs" in component and not isinstance(component["outputs"], list):
            component["outputs"] = []
            logger.debug("Fixed component outputs to be a list")

        return component

    def _heal_schema_compatibility(self, system: Dict[str, Any]) -> Dict[str, Any]:
        """Heal schema compatibility issues between connected components"""
        if "components" not in system or "bindings" not in system:
            return system
        
        components = system["components"]
        bindings = system["bindings"]
        
        # Build component lookup
        component_lookup = {comp.get("name"): comp for comp in components if comp.get("name")}
        
        # Track healing operations
        schema_fixes = []
        
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
                
            # Parse binding format (from_component.from_port -> to_component.to_port)
            from_part = binding.get("from", "")
            to_part = binding.get("to", "")
            
            # Alternative format (from_component, to_components)
            if not from_part and "from_component" in binding:
                from_component = binding.get("from_component")
                from_port = binding.get("from_port", "output")
                from_part = f"{from_component}.{from_port}"
                # Store original format for later updates
                binding["_uses_alt_format"] = True
            
            if not to_part and ("to_components" in binding or "to_component" in binding):
                # Handle both plural and singular forms
                if "to_components" in binding:
                    to_components = binding.get("to_components", [])
                    to_ports = binding.get("to_ports", ["input"])
                    if to_components and to_ports:
                        to_part = f"{to_components[0]}.{to_ports[0]}"
                elif "to_component" in binding:
                    to_component = binding.get("to_component")
                    to_port = binding.get("to_port", "input")
                    to_part = f"{to_component}.{to_port}"
            
            logger.debug(f"Processing binding: {binding}")
            logger.debug(f"From part: {from_part}, To part: {to_part}")
            
            if not from_part or not to_part:
                continue
            
            # Parse component and port names
            try:
                from_comp_name, from_port_name = from_part.split(".", 1)
                to_comp_name, to_port_name = to_part.split(".", 1)
            except ValueError:
                logger.warning(f"Invalid binding format: {from_part} -> {to_part}")
                continue
            
            # Get components
            from_comp = component_lookup.get(from_comp_name)
            to_comp = component_lookup.get(to_comp_name)
            
            if not from_comp or not to_comp:
                continue
            
            # Find port schemas
            from_schema = self._find_port_schema(from_comp, from_port_name, "outputs")
            to_schema = self._find_port_schema(to_comp, to_port_name, "inputs")
            
            if not from_schema or not to_schema:
                logger.debug(f"Skipping binding - missing schemas: from={from_schema}, to={to_schema}")
                continue
            
            # Check schema compatibility
            if not self._schemas_compatible(from_schema, to_schema):
                logger.info(f"Schema mismatch detected: {from_comp_name}.{from_port_name} ({from_schema}) -> {to_comp_name}.{to_port_name} ({to_schema})")
                
                # ALWAYS add transformation for schema mismatches instead of trying to auto-fix
                # This is safer and more explicit
                if "transformation" not in binding:
                    binding["transformation"] = f"convert_{from_schema}_to_{to_schema}"
                    schema_fixes.append(f"Added transformation for {from_comp_name}.{from_port_name} -> {to_comp_name}.{to_port_name}")
                    logger.info(f"Added transformation to handle schema mismatch: {from_schema} -> {to_schema}")
        
        if schema_fixes:
            logger.info(f"Applied {len(schema_fixes)} schema compatibility fixes")
        
        return system
    
    def _find_port_schema(self, component: Dict[str, Any], port_name: str, port_type: str) -> str:
        """Find schema for a specific port in a component"""
        ports = component.get(port_type, [])
        if not isinstance(ports, list):
            return None
        
        for port in ports:
            if isinstance(port, dict) and port.get("name") == port_name:
                # Try both possible field names
                return port.get("schema_type") or port.get("schema")
        
        return None
    
    def _update_port_schema(self, component: Dict[str, Any], port_name: str, port_type: str, new_schema: str):
        """Update schema for a specific port in a component"""
        ports = component.get(port_type, [])
        if not isinstance(ports, list):
            return
        
        for port in ports:
            if isinstance(port, dict) and port.get("name") == port_name:
                # Update the field that exists, prefer schema_type if present
                if "schema_type" in port:
                    port["schema_type"] = new_schema
                    # Also update schema field for ParsedPort compatibility
                    port["schema"] = new_schema
                elif "schema" in port:
                    port["schema"] = new_schema
                else:
                    # If neither exists, add both for maximum compatibility
                    port["schema_type"] = new_schema
                    port["schema"] = new_schema
                logger.debug(f"Updated port {port_name} schema to {new_schema}")
                break
    
    def _schemas_compatible(self, from_schema: str, to_schema: str) -> bool:
        """Check if two schemas are compatible"""
        if not from_schema or not to_schema:
            return True  # Can't validate, assume compatible
        
        # Exact match
        if from_schema == to_schema:
            return True
        
        # "any" type accepts anything
        if to_schema == "any":
            return True
        
        # Check for compatible types
        compatible_pairs = [
            ("object", "any"),
            ("integer", "number"),
            ("float", "number"),
            ("string", "any"),
            ("boolean", "any"),
            ("array", "list"),
            # Handle blueprint-specific schema names
            ("common_object_schema", "any"),
            ("common_integer_schema", "any"),
            ("common_string_schema", "any"),
            ("common_boolean_schema", "any"),
            ("common_array_schema", "any"),
            ("common_number_schema", "any"),
        ]
        
        for compat_from, compat_to in compatible_pairs:
            if (from_schema == compat_from and to_schema == compat_to) or \
               (from_schema == compat_to and to_schema == compat_from):
                return True
        
        return False
    
    def _can_auto_fix_schema(self, from_schema: str, to_schema: str) -> bool:
        """Check if schema mismatch can be automatically fixed"""
        # Only fix simple conversions that are safe
        safe_conversions = [
            ("object", "any"),
            ("integer", "number"),
            ("float", "number"),
            ("string", "any"),
            ("boolean", "any"),
            ("array", "any"),
            # Handle blueprint-specific schema names
            ("common_object_schema", "any"),
            ("common_integer_schema", "any"),
            ("common_string_schema", "any"),
            ("common_boolean_schema", "any"),
            ("common_array_schema", "any"),
            ("common_number_schema", "any"),
        ]
        
        for safe_from, safe_to in safe_conversions:
            if from_schema == safe_from:
                return True
        
        return False
    
    def _auto_fix_schema(self, from_schema: str, to_schema: str) -> str:
        """Automatically fix schema compatibility"""
        # Convert to more general type that can accept the input
        if from_schema in ["object", "integer", "float", "string", "boolean", "array"]:
            return "any"  # Most general type that accepts anything
        
        # Handle blueprint-specific schema names
        if from_schema in ["common_object_schema", "common_integer_schema", "common_string_schema", 
                          "common_boolean_schema", "common_array_schema", "common_number_schema"]:
            return "any"  # Most general type that accepts anything
        
        return from_schema  # Fallback to original


def heal_blueprint_yaml(yaml_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to heal a blueprint YAML dictionary

    Args:
        yaml_dict: The parsed YAML dictionary

    Returns:
        Healed blueprint dictionary
    """
    healer = BlueprintHealer()
    return healer.heal_blueprint(yaml_dict)

