#!/usr/bin/env python3
"""
Intermediate System Healer
Automatically fixes architectural issues in intermediate systems before blueprint generation

This healer addresses common LLM generation issues:
- Port name mismatches between components and bindings
- Orphaned components with ports but no connections
- Missing component configurations
- Type mismatches and inconsistencies
"""
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .intermediate_format import IntermediateSystem, IntermediateComponent, IntermediateBinding, IntermediatePort


@dataclass
class HealingOperation:
    """Represents a healing operation performed on the system"""
    operation_type: str
    component: str
    description: str
    before_value: Optional[str] = None
    after_value: Optional[str] = None


@dataclass
class IntermediateHealingResult:
    """Result of intermediate system healing"""
    success: bool
    original_system: IntermediateSystem
    healed_system: Optional[IntermediateSystem] = None
    operations_performed: List[HealingOperation] = None
    validation_errors_fixed: int = 0
    remaining_errors: List[str] = None


class IntermediateSystemHealer:
    """
    Heals architectural issues in intermediate systems
    
    This healer applies common fixes for LLM-generated intermediate systems:
    1. Port name normalization and matching
    2. Orphaned component connection or removal
    3. Missing configuration injection
    4. Component type correction
    5. Binding consistency enforcement
    """
    
    def __init__(self):
        self.operations_log = []
    
    def heal_system(self, system: IntermediateSystem) -> IntermediateHealingResult:
        """
        Apply comprehensive healing to an intermediate system
        
        Args:
            system: The intermediate system to heal
            
        Returns:
            HealingResult with the healed system and operations performed
        """
        self.operations_log = []
        
        try:
            # Create a working copy
            healed_system = self._deep_copy_system(system)
            
            # Apply healing operations in order
            self._heal_port_mismatches(healed_system)
            self._heal_schema_mismatches(healed_system)
            self._heal_orphaned_components(healed_system)
            self._heal_missing_configurations(healed_system)
            self._heal_component_types(healed_system)
            self._normalize_naming_conventions(healed_system)
            
            # Validate the healed system
            validation_errors = self._validate_system(healed_system)
            
            return IntermediateHealingResult(
                success=len(validation_errors) == 0,
                original_system=system,
                healed_system=healed_system,
                operations_performed=self.operations_log.copy(),
                validation_errors_fixed=self._count_original_errors(system) - len(validation_errors),
                remaining_errors=validation_errors
            )
            
        except Exception as e:
            return IntermediateHealingResult(
                success=False,
                original_system=system,
                remaining_errors=[f"Healing failed: {str(e)}"]
            )
    
    def _heal_port_mismatches(self, system: IntermediateSystem) -> None:
        """Fix port name mismatches between components and bindings"""
        
        # Build component port mappings and identify terminal components
        component_ports = {}
        terminal_components = set()  # Components that should not have outputs
        
        for comp in system.components:
            component_ports[comp.name] = {
                'inputs': {port.name: port for port in comp.inputs},
                'outputs': {port.name: port for port in comp.outputs}
            }
            
            # Identify terminal components (Store and Sink types)
            if comp.type in ['Store', 'Sink']:
                terminal_components.add(comp.name)
                
                # Remove any output ports from terminal components
                if comp.outputs:
                    self._log_operation(
                        "port_removal", comp.name,
                        f"Removed {len(comp.outputs)} output ports from terminal component {comp.name} (type: {comp.type})",
                        f"{[p.name for p in comp.outputs]}",
                        "[]"
                    )
                    comp.outputs = []
                    component_ports[comp.name]['outputs'] = {}
        
        # Check and fix each binding
        bindings_to_remove = []
        
        for binding in system.bindings:
            # Check if binding is from a terminal component (Store/Sink)
            if binding.from_component in terminal_components:
                # Terminal components should not have output bindings
                bindings_to_remove.append(binding)
                self._log_operation(
                    "binding_removal", binding.from_component,
                    f"Removed invalid binding from terminal component {binding.from_component} (type: Store/Sink)",
                    f"{binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}",
                    "removed"
                )
                continue
            
            # Fix from_port mismatches
            if binding.from_component in component_ports:
                available_outputs = component_ports[binding.from_component]['outputs']
                if binding.from_port not in available_outputs:
                    # Try fuzzy matching
                    best_match = self._find_best_port_match(binding.from_port, list(available_outputs.keys()))
                    if best_match:
                        self._log_operation(
                            "port_name_fix", binding.from_component,
                            f"Fixed output port name: {binding.from_port} → {best_match}",
                            binding.from_port, best_match
                        )
                        binding.from_port = best_match
                    else:
                        # For non-terminal components, create missing output port
                        if binding.from_component not in terminal_components:
                            new_port = IntermediatePort(
                                name=binding.from_port,
                                schema_type="object",
                                description=f"Auto-generated output port for {binding.from_port}"
                            )
                            component_ports[binding.from_component]['outputs'][binding.from_port] = new_port
                            
                            # Add to actual component
                            for comp in system.components:
                                if comp.name == binding.from_component:
                                    comp.outputs.append(new_port)
                                    break
                            
                            self._log_operation(
                                "port_creation", binding.from_component,
                                f"Created missing output port: {binding.from_port}"
                            )
                        else:
                            # For terminal components, mark binding for removal
                            bindings_to_remove.append(binding)
                            self._log_operation(
                                "binding_removal", binding.from_component,
                                f"Cannot create output port on terminal component {binding.from_component}"
                            )
            
            # Fix to_port mismatches
            if binding.to_component in component_ports:
                available_inputs = component_ports[binding.to_component]['inputs']
                if binding.to_port not in available_inputs:
                    # Try fuzzy matching
                    best_match = self._find_best_port_match(binding.to_port, list(available_inputs.keys()))
                    if best_match:
                        self._log_operation(
                            "port_name_fix", binding.to_component,
                            f"Fixed input port name: {binding.to_port} → {best_match}",
                            binding.to_port, best_match
                        )
                        binding.to_port = best_match
                    else:
                        # Create missing input port
                        new_port = IntermediatePort(
                            name=binding.to_port,
                            schema_type="object",
                            description=f"Auto-generated input port for {binding.to_port}"
                        )
                        component_ports[binding.to_component]['inputs'][binding.to_port] = new_port
                        
                        # Add to actual component
                        for comp in system.components:
                            if comp.name == binding.to_component:
                                comp.inputs.append(new_port)
                                break
                        
                        self._log_operation(
                            "port_creation", binding.to_component,
                            f"Created missing input port: {binding.to_port}"
                        )
        
        # Remove invalid bindings
        for binding in bindings_to_remove:
            system.bindings.remove(binding)
    
    def _heal_schema_mismatches(self, system: IntermediateSystem) -> None:
        """Fix schema type mismatches between component bindings"""
        
        # Build component port mappings with schema types
        component_ports = {}
        for comp in system.components:
            inputs = {}
            outputs = {}
            
            for port in comp.inputs:
                inputs[port.name] = port.schema_type
                
            for port in comp.outputs:
                outputs[port.name] = port.schema_type
            
            component_ports[comp.name] = {
                'inputs': inputs,
                'outputs': outputs
            }
        
        # Check and fix schema mismatches in bindings
        for binding in system.bindings:
            if (binding.from_component in component_ports and 
                binding.to_component in component_ports):
                
                from_schema = component_ports[binding.from_component]['outputs'].get(binding.from_port)
                to_schema = component_ports[binding.to_component]['inputs'].get(binding.to_port)
                
                if from_schema and to_schema and from_schema != to_schema:
                    # Common schema conversions
                    if self._can_auto_convert_schema(from_schema, to_schema):
                        # Fix the schema type to match
                        target_schema = self._get_compatible_schema(from_schema, to_schema)
                        
                        # Update the receiving port to match sending port
                        for comp in system.components:
                            if comp.name == binding.to_component:
                                for port in comp.inputs:
                                    if port.name == binding.to_port:
                                        old_schema = port.schema_type
                                        port.schema_type = target_schema
                                        
                                        self._log_operation(
                                            "schema_fix", comp.name,
                                            f"Fixed input port {port.name} schema: {old_schema} → {target_schema}",
                                            old_schema, target_schema
                                        )
                                        break
                                break
    
    def _can_auto_convert_schema(self, from_schema: str, to_schema: str) -> bool:
        """Check if schema types can be automatically converted"""
        
        # Compatible conversions
        compatible_pairs = [
            ('array', 'object'),  # array can be wrapped in object
            ('object', 'array'),  # object can be placed in array
            ('string', 'object'), # string can be wrapped in object  
            ('number', 'object'), # number can be wrapped in object
            ('integer', 'number'), # integer is a number
            ('boolean', 'object'), # boolean can be wrapped in object
        ]
        
        return (from_schema, to_schema) in compatible_pairs
    
    def _get_compatible_schema(self, from_schema: str, to_schema: str) -> str:
        """Get the most compatible schema type for conversion"""
        
        # For array → object mismatches, use object (more flexible)
        if from_schema == 'array' and to_schema == 'object':
            return 'object'
        
        # For object → array mismatches, use object (more flexible) 
        if from_schema == 'object' and to_schema == 'array':
            return 'object'
        
        # For specific → generic mismatches, use object (most flexible)
        if to_schema == 'object':
            return 'object'
        
        # Default to the receiving schema
        return to_schema
    
    def _heal_orphaned_components(self, system: IntermediateSystem) -> None:
        """Fix orphaned components by connecting them or removing unused ones"""
        
        # Find connected components
        connected_components = set()
        for binding in system.bindings:
            connected_components.add(binding.from_component)
            connected_components.add(binding.to_component)
        
        # Process orphaned components
        for comp in system.components:
            if comp.name not in connected_components and (comp.inputs or comp.outputs):
                # Skip certain component types that can be orphaned
                if comp.type in ['Source', 'Sink', 'APIEndpoint']:
                    continue
                
                # Try to connect the orphaned component
                self._connect_orphaned_component(system, comp, connected_components)
    
    def _connect_orphaned_component(self, system: IntermediateSystem, orphaned_comp: IntermediateComponent, connected_components: Set[str]) -> None:
        """Attempt to connect an orphaned component to the system"""
        
        # Simple heuristics for connection
        if orphaned_comp.type == "Controller" and "auth" in orphaned_comp.name.lower():
            # Authentication controllers often connect to APIs and databases
            self._connect_auth_controller(system, orphaned_comp)
        
        elif orphaned_comp.type == "Store":
            # Stores often receive data from APIs or transformers
            self._connect_store_component(system, orphaned_comp)
        
        elif orphaned_comp.type == "Transformer":
            # Transformers often sit between APIs and stores
            self._connect_transformer_component(system, orphaned_comp)
        
        else:
            # Generic connection attempt
            self._attempt_generic_connection(system, orphaned_comp)
    
    def _connect_auth_controller(self, system: IntermediateSystem, auth_comp: IntermediateComponent) -> None:
        """Connect an authentication controller to relevant components"""
        
        # Find user-related components
        user_apis = [comp for comp in system.components if "user" in comp.name.lower() and comp.type == "APIEndpoint"]
        user_stores = [comp for comp in system.components if "user" in comp.name.lower() and comp.type == "Store"]
        
        if user_apis and auth_comp.inputs:
            # Connect user API to auth controller
            api_comp = user_apis[0]
            if api_comp.outputs:
                # Create binding from user API to auth controller
                new_binding = IntermediateBinding(
                    from_component=api_comp.name,
                    from_port=api_comp.outputs[0].name,
                    to_component=auth_comp.name,
                    to_port=auth_comp.inputs[0].name
                )
                system.bindings.append(new_binding)
                
                self._log_operation(
                    "orphan_connection", auth_comp.name,
                    f"Connected {api_comp.name} → {auth_comp.name}"
                )
        
        if user_stores and auth_comp.outputs:
            # Connect auth controller to user store
            store_comp = user_stores[0]
            if store_comp.inputs:
                new_binding = IntermediateBinding(
                    from_component=auth_comp.name,
                    from_port=auth_comp.outputs[0].name,
                    to_component=store_comp.name,
                    to_port=store_comp.inputs[0].name
                )
                system.bindings.append(new_binding)
                
                self._log_operation(
                    "orphan_connection", auth_comp.name,
                    f"Connected {auth_comp.name} → {store_comp.name}"
                )
    
    def _connect_store_component(self, system: IntermediateSystem, store_comp: IntermediateComponent) -> None:
        """Connect a store component to data producers"""
        
        if not store_comp.inputs:
            return
        
        # Find components that could write to this store
        data_producers = [comp for comp in system.components 
                         if comp.type in ["APIEndpoint", "Transformer", "Controller"] 
                         and comp.outputs
                         and self._is_semantically_related(comp.name, store_comp.name)]
        
        if data_producers:
            producer = data_producers[0]
            new_binding = IntermediateBinding(
                from_component=producer.name,
                from_port=producer.outputs[0].name,
                to_component=store_comp.name,
                to_port=store_comp.inputs[0].name
            )
            system.bindings.append(new_binding)
            
            self._log_operation(
                "orphan_connection", store_comp.name,
                f"Connected {producer.name} → {store_comp.name}"
            )
    
    def _connect_transformer_component(self, system: IntermediateSystem, transformer_comp: IntermediateComponent) -> None:
        """Connect a transformer component between related components"""
        
        if not (transformer_comp.inputs and transformer_comp.outputs):
            return
        
        # Find potential input sources
        input_sources = [comp for comp in system.components 
                        if comp.type in ["APIEndpoint", "Source"] 
                        and comp.outputs
                        and self._is_semantically_related(comp.name, transformer_comp.name)]
        
        # Find potential output targets
        output_targets = [comp for comp in system.components 
                         if comp.type in ["Store", "Sink"] 
                         and comp.inputs
                         and self._is_semantically_related(comp.name, transformer_comp.name)]
        
        if input_sources and output_targets:
            source = input_sources[0]
            target = output_targets[0]
            
            # Create input binding
            input_binding = IntermediateBinding(
                from_component=source.name,
                from_port=source.outputs[0].name,
                to_component=transformer_comp.name,
                to_port=transformer_comp.inputs[0].name
            )
            system.bindings.append(input_binding)
            
            # Create output binding
            output_binding = IntermediateBinding(
                from_component=transformer_comp.name,
                from_port=transformer_comp.outputs[0].name,
                to_component=target.name,
                to_port=target.inputs[0].name
            )
            system.bindings.append(output_binding)
            
            self._log_operation(
                "orphan_connection", transformer_comp.name,
                f"Connected {source.name} → {transformer_comp.name} → {target.name}"
            )
    
    def _attempt_generic_connection(self, system: IntermediateSystem, orphaned_comp: IntermediateComponent) -> None:
        """Attempt a generic connection for an orphaned component"""
        
        # Simple heuristic: connect to semantically similar components
        if orphaned_comp.inputs:
            # Look for output providers
            providers = [comp for comp in system.components 
                        if comp.outputs and comp != orphaned_comp
                        and self._is_semantically_related(comp.name, orphaned_comp.name)]
            
            if providers:
                provider = providers[0]
                new_binding = IntermediateBinding(
                    from_component=provider.name,
                    from_port=provider.outputs[0].name,
                    to_component=orphaned_comp.name,
                    to_port=orphaned_comp.inputs[0].name
                )
                system.bindings.append(new_binding)
                
                self._log_operation(
                    "orphan_connection", orphaned_comp.name,
                    f"Connected {provider.name} → {orphaned_comp.name}"
                )
    
    def _heal_missing_configurations(self, system: IntermediateSystem) -> None:
        """Add missing required configurations to components"""
        
        for comp in system.components:
            if comp.type == "APIEndpoint" and "port" not in comp.config:
                # Assign unique port
                port = 8080 + hash(comp.name) % 1000
                comp.config["port"] = port
                
                self._log_operation(
                    "config_injection", comp.name,
                    f"Added missing port configuration: {port}"
                )
            
            elif comp.type == "Store" and "storage_type" not in comp.config:
                # Default to postgresql
                comp.config["storage_type"] = "postgresql"
                
                self._log_operation(
                    "config_injection", comp.name,
                    "Added missing storage_type: postgresql"
                )
            
            elif comp.type == "Model" and "model_type" not in comp.config:
                # Infer model type from name
                if "sentiment" in comp.name.lower():
                    comp.config["model_type"] = "sentiment_analysis"
                else:
                    comp.config["model_type"] = "classification"
                
                self._log_operation(
                    "config_injection", comp.name,
                    f"Added missing model_type: {comp.config['model_type']}"
                )
    
    def _heal_component_types(self, system: IntermediateSystem) -> None:
        """Fix component types based on usage patterns"""
        
        # Analyze binding patterns to infer correct types
        component_roles = self._analyze_component_roles(system)
        
        for comp in system.components:
            suggested_type = component_roles.get(comp.name, {}).get("suggested_type")
            if suggested_type and suggested_type != comp.type:
                self._log_operation(
                    "type_correction", comp.name,
                    f"Corrected component type: {comp.type} → {suggested_type}",
                    comp.type, suggested_type
                )
                comp.type = suggested_type
    
    def _normalize_naming_conventions(self, system: IntermediateSystem) -> None:
        """Ensure all names follow snake_case conventions"""
        
        # Component names
        for comp in system.components:
            normalized_name = self._normalize_name(comp.name)
            if normalized_name != comp.name:
                old_name = comp.name
                comp.name = normalized_name
                
                # Update bindings
                for binding in system.bindings:
                    if binding.from_component == old_name:
                        binding.from_component = normalized_name
                    if binding.to_component == old_name:
                        binding.to_component = normalized_name
                
                self._log_operation(
                    "name_normalization", normalized_name,
                    f"Normalized component name: {old_name} → {normalized_name}",
                    old_name, normalized_name
                )
            
            # Port names
            for port in comp.inputs + comp.outputs:
                normalized_port = self._normalize_name(port.name)
                if normalized_port != port.name:
                    old_port = port.name
                    port.name = normalized_port
                    
                    # Update bindings
                    for binding in system.bindings:
                        if binding.from_component == comp.name and binding.from_port == old_port:
                            binding.from_port = normalized_port
                        if binding.to_component == comp.name and binding.to_port == old_port:
                            binding.to_port = normalized_port
                    
                    self._log_operation(
                        "name_normalization", comp.name,
                        f"Normalized port name: {old_port} → {normalized_port}",
                        old_port, normalized_port
                    )
    
    def _find_best_port_match(self, target_port: str, available_ports: List[str]) -> Optional[str]:
        """Find the best matching port name using fuzzy matching"""
        
        if not available_ports:
            return None
        
        # Exact match (case insensitive)
        for port in available_ports:
            if port.lower() == target_port.lower():
                return port
        
        # Semantic similarity
        target_words = set(re.findall(r'\w+', target_port.lower()))
        best_match = None
        best_score = 0
        
        for port in available_ports:
            port_words = set(re.findall(r'\w+', port.lower()))
            common_words = target_words & port_words
            score = len(common_words) / max(len(target_words), len(port_words))
            
            if score > best_score and score > 0.3:  # Minimum similarity threshold
                best_score = score
                best_match = port
        
        return best_match
    
    def _is_semantically_related(self, name1: str, name2: str) -> bool:
        """Check if two component names are semantically related"""
        
        words1 = set(re.findall(r'\w+', name1.lower()))
        words2 = set(re.findall(r'\w+', name2.lower()))
        
        # Check for common domain words
        common_words = words1 & words2
        return len(common_words) > 0 or self._have_domain_relationship(words1, words2)
    
    def _have_domain_relationship(self, words1: Set[str], words2: Set[str]) -> bool:
        """Check if two word sets have domain relationships"""
        
        domain_groups = [
            {"user", "auth", "login", "profile", "account"},
            {"product", "catalog", "inventory", "item"},
            {"order", "cart", "checkout", "payment"},
            {"analytics", "report", "metric", "data"},
            {"notification", "email", "sms", "alert"}
        ]
        
        for group in domain_groups:
            if (words1 & group) and (words2 & group):
                return True
        
        return False
    
    def _analyze_component_roles(self, system: IntermediateSystem) -> Dict[str, Dict[str, Any]]:
        """Analyze binding patterns to determine component roles"""
        
        roles = {}
        
        # Count inputs and outputs for each component in bindings
        for comp in system.components:
            input_count = sum(1 for b in system.bindings if b.to_component == comp.name)
            output_count = sum(1 for b in system.bindings if b.from_component == comp.name)
            
            # Suggest type based on pattern
            suggested_type = comp.type  # Default to current type
            
            # CRITICAL: Check Store BEFORE Sink to prevent confusion
            # Store components persist data for retrieval (database, warehouse, etc)
            # Sink components consume data without storing (alerts, notifications, etc)
            
            # CRITICAL: Don't change Controllers to Stores - Controllers need both inputs and outputs
            if comp.type == "Controller":
                # Controllers should remain Controllers unless they have NO outputs
                if output_count > 0:
                    suggested_type = "Controller"  # Keep as Controller
                else:
                    # Only change if it truly has no outputs and matches Store pattern
                    store_keywords = ["db", "database", "store", "storage", "repository", "warehouse", "persist"]
                    if any(keyword in comp.name.lower() for keyword in store_keywords):
                        suggested_type = "Store"
                    else:
                        suggested_type = "Controller"  # Keep as Controller by default
            else:
                # Check for Store patterns first (highest priority)
                store_keywords = ["db", "database", "store", "storage", "repository", "warehouse", "persist"]
                if any(keyword in comp.name.lower() for keyword in store_keywords):
                    suggested_type = "Store"
                elif any(keyword in comp.description.lower() for keyword in store_keywords) if hasattr(comp, 'description') and comp.description else False:
                    suggested_type = "Store"
                # Check for Sink patterns (alerts, notifications, external sends)
                elif input_count > 0 and output_count == 0:
                    sink_keywords = ["alert", "notify", "email", "sms", "log", "export", "send"]
                    if any(keyword in comp.name.lower() for keyword in sink_keywords):
                        suggested_type = "Sink"
                    elif comp.type == "Sink":  # Keep existing Sink designation
                        suggested_type = "Sink"
                    # If no sink keywords and has inputs but no outputs, check if it's already a Store
                    elif comp.type == "Store":
                        suggested_type = "Store"  # Preserve Store type
                    else:
                        # Only suggest Sink if we're sure it's not a Store
                        suggested_type = "Sink"
                # Check for APIEndpoint BEFORE Source to preserve API components
                elif "api" in comp.name.lower() or "endpoint" in comp.name.lower():
                    suggested_type = "APIEndpoint"
                elif input_count == 0 and output_count > 0:
                    # Only suggest Source if it's not an API component
                    if not ("api" in comp.name.lower() or "endpoint" in comp.name.lower()):
                        suggested_type = "Source"
                    else:
                        suggested_type = comp.type  # Keep original type
            
            roles[comp.name] = {
                "input_count": input_count,
                "output_count": output_count,
                "suggested_type": suggested_type
            }
        
        return roles
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name to snake_case"""
        
        # Convert to snake_case
        normalized = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        normalized = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', normalized)
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized)
        normalized = normalized.lower().strip('_')
        
        # Ensure it starts with a letter
        if normalized and not normalized[0].isalpha():
            normalized = 'component_' + normalized
        
        return normalized or 'unnamed_component'
    
    def _deep_copy_system(self, system: IntermediateSystem) -> IntermediateSystem:
        """Create a deep copy of the intermediate system for healing using raw objects"""
        
        # Create new components using raw objects (no Pydantic validation)
        new_components = []
        for comp in system.components:
            # Create raw port objects
            new_inputs = []
            for port in comp.inputs:
                raw_port = type('IntermediatePort', (), {
                    'name': port.name,
                    'schema_type': port.schema_type,
                    'description': getattr(port, 'description', ''),
                    'required': getattr(port, 'required', True)
                })()
                new_inputs.append(raw_port)
            
            new_outputs = []
            for port in comp.outputs:
                raw_port = type('IntermediatePort', (), {
                    'name': port.name,
                    'schema_type': port.schema_type,
                    'description': getattr(port, 'description', ''),
                    'required': getattr(port, 'required', True)
                })()
                new_outputs.append(raw_port)
            
            # Create raw component object
            new_comp = type('IntermediateComponent', (), {
                'name': comp.name,
                'type': comp.type,
                'description': comp.description,
                'inputs': new_inputs,
                'outputs': new_outputs,
                'config': getattr(comp, 'config', {}).copy()
            })()
            new_components.append(new_comp)
        
        # Create new bindings using raw objects
        new_bindings = []
        for binding in system.bindings:
            raw_binding = type('IntermediateBinding', (), {
                'from_component': binding.from_component,
                'from_port': binding.from_port,
                'to_component': binding.to_component,
                'to_port': binding.to_port
            })()
            new_bindings.append(raw_binding)
        
        # Create raw system object
        return type('IntermediateSystem', (), {
            'name': system.name,
            'description': system.description,
            'version': system.version,
            'components': new_components,
            'bindings': new_bindings,
            'environment': system.environment
        })()
    
    def _validate_system(self, system: IntermediateSystem) -> List[str]:
        """Validate the system and return any remaining errors - Manual validation only"""
        
        errors = []
        
        try:
            # Completely manual validation without any Pydantic interaction
            if not hasattr(system, 'components') or not system.components:
                errors.append("System has no components")
                return errors
            
            if not hasattr(system, 'bindings'):
                errors.append("System has no bindings attribute")
                return errors
            
            # Check for basic system structure
            component_names = set()
            component_ports = {}
            
            # Validate components and build port mappings
            for comp in system.components:
                if not hasattr(comp, 'name') or not comp.name:
                    errors.append("Component missing name")
                    continue
                    
                if comp.name in component_names:
                    errors.append(f"Duplicate component name: {comp.name}")
                component_names.add(comp.name)
                
                # Build port mappings safely
                inputs = set()
                outputs = set()
                
                if hasattr(comp, 'inputs') and comp.inputs:
                    for port in comp.inputs:
                        if hasattr(port, 'name') and port.name:
                            inputs.add(port.name)
                
                if hasattr(comp, 'outputs') and comp.outputs:
                    for port in comp.outputs:
                        if hasattr(port, 'name') and port.name:
                            outputs.add(port.name)
                
                component_ports[comp.name] = {
                    'inputs': inputs,
                    'outputs': outputs
                }
            
            # Validate bindings
            if system.bindings:
                for binding in system.bindings:
                    if not hasattr(binding, 'from_component'):
                        errors.append("Binding missing from_component")
                        continue
                    if not hasattr(binding, 'to_component'):
                        errors.append("Binding missing to_component")
                        continue
                    if not hasattr(binding, 'from_port'):
                        errors.append("Binding missing from_port")
                        continue
                    if not hasattr(binding, 'to_port'):
                        errors.append("Binding missing to_port")
                        continue
                    
                    # Check component existence
                    if binding.from_component not in component_names:
                        errors.append(f"Binding references unknown component: {binding.from_component}")
                        continue
                    if binding.to_component not in component_names:
                        errors.append(f"Binding references unknown component: {binding.to_component}")
                        continue
                    
                    # Check port existence
                    from_comp_ports = component_ports.get(binding.from_component, {})
                    to_comp_ports = component_ports.get(binding.to_component, {})
                    
                    if binding.from_port not in from_comp_ports.get('outputs', set()):
                        available = list(from_comp_ports.get('outputs', set()))
                        errors.append(f"Component '{binding.from_component}' has no output port '{binding.from_port}'. Available: {available}")
                    
                    if binding.to_port not in to_comp_ports.get('inputs', set()):
                        available = list(to_comp_ports.get('inputs', set()))
                        errors.append(f"Component '{binding.to_component}' has no input port '{binding.to_port}'. Available: {available}")
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _count_original_errors(self, system: IntermediateSystem) -> int:
        """Count validation errors in the original system"""
        
        return len(self._validate_system(system))
    
    def _log_operation(self, operation_type: str, component: str, description: str, 
                      before_value: Optional[str] = None, after_value: Optional[str] = None) -> None:
        """Log a healing operation"""
        
        operation = HealingOperation(
            operation_type=operation_type,
            component=component,
            description=description,
            before_value=before_value,
            after_value=after_value
        )
        self.operations_log.append(operation)


def heal_intermediate_system(system: IntermediateSystem) -> IntermediateHealingResult:
    """
    Convenience function to heal an intermediate system
    
    Args:
        system: The intermediate system to heal
        
    Returns:
        HealingResult with success status and healed system
    """
    healer = IntermediateSystemHealer()
    return healer.heal_system(system)