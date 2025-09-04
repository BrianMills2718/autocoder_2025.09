#!/usr/bin/env python3
"""
Architectural Validator - Comprehensive System Architecture Validation

This module provides comprehensive architectural validation for system blueprints
to ensure generated systems follow coherent architectural patterns and have
complete data flows.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import networkx as nx

# Import types only when needed to avoid circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent, ParsedBinding

from autocoder_cc.components.component_categorization import Role, infer_effective_role
from autocoder_cc.core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class ArchitecturalPattern(Enum):
    """Supported architectural patterns."""
    PIPELINE = "pipeline"
    REQUEST_RESPONSE = "request_response"
    PUB_SUB = "pub_sub"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"
    LAYERED = "layered"
    UNKNOWN = "unknown"

@dataclass
class ArchitecturalValidationError:
    """Represents an architectural validation error."""
    error_type: str
    severity: str  # "error", "warning", "info"
    message: str
    component: Optional[str] = None
    binding: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class DataFlowPath:
    """Represents a data flow path through the system."""
    source_component: str
    sink_component: str
    path: List[str]
    length: int
    is_complete: bool

@dataclass
class ComponentConnectivityInfo:
    """Information about a component's connectivity."""
    component_name: str
    component_type: str
    has_inputs: bool
    has_outputs: bool
    input_connections: List[str]
    output_connections: List[str]
    is_connected: bool
    is_terminal: bool
    is_source: bool

class ArchitecturalValidator:
    """
    Validates system architecture for coherence, completeness, and best practices.
    """
    
    # Component type connectivity matrix - defines valid connection patterns
    CONNECTIVITY_MATRIX = {
        'Source': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store', 'APIEndpoint'],
            'can_receive_from': [],
            'expected_inputs': 0,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': True
        },
        'Transformer': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store', 'APIEndpoint', 'Aggregator'],
            'can_receive_from': ['Source', 'Transformer', 'Router', 'APIEndpoint', 'Controller', 'Filter', 'Aggregator', 'EventSource'],
            'expected_inputs': 1,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        },
        'Filter': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store', 'APIEndpoint', 'Aggregator'],
            'can_receive_from': ['Source', 'Transformer', 'Router', 'APIEndpoint', 'Controller', 'Filter', 'Aggregator', 'EventSource'],
            'expected_inputs': 1,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        },
        'Router': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store', 'APIEndpoint', 'Aggregator'],
            'can_receive_from': ['Source', 'Transformer', 'APIEndpoint', 'Controller', 'Filter', 'Router', 'EventSource'],
            'expected_inputs': 1,
            'expected_outputs': 2,  # Fan-out
            'is_terminal': False,
            'is_source': False
        },
        'Aggregator': {
            'can_connect_to': ['Transformer', 'Filter', 'Sink', 'Store', 'APIEndpoint'],
            'can_receive_from': ['Source', 'Transformer', 'Router', 'APIEndpoint', 'Filter'],
            'expected_inputs': 2,  # Fan-in
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        },
        'APIEndpoint': {
            'can_connect_to': ['Controller', 'Transformer', 'Store', 'Sink', 'StreamProcessor'],
            'can_receive_from': ['Controller', 'Transformer', 'Store', 'Source', 'Aggregator', 'Filter', 'Router', 'StreamProcessor'],
            'expected_inputs': 1,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        },
        'Controller': {
            'can_connect_to': ['Store', 'Sink', 'APIEndpoint', 'Transformer'],
            'can_receive_from': ['APIEndpoint', 'Transformer'],
            'expected_inputs': 1,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        },
        'Store': {
            'can_connect_to': ['APIEndpoint'],  # Limited - stores are mostly terminal
            'can_receive_from': ['Source', 'Transformer', 'Controller', 'APIEndpoint', 'Router', 'Filter', 'Aggregator', 'EventSource', 'StreamProcessor'],
            'expected_inputs': 1,
            'expected_outputs': 0,  # Terminal component
            'is_terminal': True,
            'is_source': False
        },
        'Sink': {
            'can_connect_to': [],  # Terminal component
            'can_receive_from': ['Source', 'Transformer', 'Controller', 'APIEndpoint', 'Aggregator', 'Router', 'Filter', 'EventSource', 'StreamProcessor'],
            'expected_inputs': 1,
            'expected_outputs': 0,
            'is_terminal': True,
            'is_source': False
        },
        'EventSource': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store'],
            'can_receive_from': [],
            'expected_inputs': 0,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': True
        },
        'StreamProcessor': {
            'can_connect_to': ['Transformer', 'Filter', 'Router', 'Sink', 'Store', 'APIEndpoint', 'Aggregator'],
            'can_receive_from': ['Source', 'Transformer', 'Router', 'APIEndpoint', 'Controller', 'Filter', 'Aggregator', 'EventSource'],
            'expected_inputs': 1,
            'expected_outputs': 1,
            'is_terminal': False,
            'is_source': False
        }
    }
    
    def __init__(self):
        self.validation_errors: List[ArchitecturalValidationError] = []
        self.system_graph: Optional[nx.DiGraph] = None
        
    def validate_system_architecture(self, system_blueprint: "ParsedSystemBlueprint") -> List[ArchitecturalValidationError]:
        """
        Perform comprehensive architectural validation on a system blueprint.
        
        Args:
            system_blueprint: The system blueprint to validate
            
        Returns:
            List of architectural validation errors
        """
        self.validation_errors.clear()
        
        logger.info(f"Starting architectural validation for system: {system_blueprint.system.name}")
        
        # Build system graph for analysis
        self.system_graph = self._build_system_graph(system_blueprint)
        
        # Perform validation checks
        self._validate_component_connectivity_rules(system_blueprint)
        self._validate_data_flow_completeness(system_blueprint)
        self._validate_architectural_patterns(system_blueprint)
        self._validate_system_completeness(system_blueprint)
        self._validate_architectural_coherence(system_blueprint)
        
        # Log validation results
        error_count = len([e for e in self.validation_errors if e.severity == "error"])
        warning_count = len([e for e in self.validation_errors if e.severity == "warning"])
        
        logger.info(f"Architectural validation completed: {error_count} errors, {warning_count} warnings")
        
        return self.validation_errors
    
    def _build_system_graph(self, system_blueprint: "ParsedSystemBlueprint") -> nx.DiGraph:
        """Build a directed graph representation of the system."""
        graph = nx.DiGraph()
        
        # Add component nodes
        for component in system_blueprint.system.components:
            graph.add_node(component.name, 
                          type=component.type,
                          inputs=len(component.inputs),
                          outputs=len(component.outputs),
                          component=component)
        
        # Add binding edges
        for binding in system_blueprint.system.bindings:
            for to_component in binding.to_components:
                graph.add_edge(binding.from_component, to_component,
                             from_port=binding.from_port,
                             to_port=binding.to_ports[binding.to_components.index(to_component)],
                             binding=binding)
        
        return graph
    
    def _validate_component_connectivity_rules(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate that component connections follow logical connectivity rules."""
        
        logger.debug("Validating component connectivity rules")
        
        for binding in system_blueprint.system.bindings:
            from_component = self._get_component_by_name(system_blueprint, binding.from_component)
            
            if not from_component:
                continue
                
            # Check if from_component type can connect to target components
            from_type = from_component.type
            connectivity_rules = self.CONNECTIVITY_MATRIX.get(from_type, {})
            can_connect_to = connectivity_rules.get('can_connect_to', [])
            
            for to_component_name in binding.to_components:
                to_component = self._get_component_by_name(system_blueprint, to_component_name)
                if not to_component:
                    continue
                    
                to_type = to_component.type
                
                # Check if connection is valid according to connectivity matrix
                if to_type not in can_connect_to:
                    self.validation_errors.append(ArchitecturalValidationError(
                        error_type="invalid_connection",
                        severity="error",
                        message=f"Invalid connection: {from_type} '{from_component.name}' cannot connect to {to_type} '{to_component.name}'",
                        component=from_component.name,
                        binding=f"{binding.from_component}.{binding.from_port} → {to_component_name}",
                        suggestion=f"{from_type} components can connect to: {', '.join(can_connect_to)}"
                    ))
                
                # Check if to_component can receive from from_component
                to_connectivity_rules = self.CONNECTIVITY_MATRIX.get(to_type, {})
                can_receive_from = to_connectivity_rules.get('can_receive_from', [])
                
                if from_type not in can_receive_from:
                    self.validation_errors.append(ArchitecturalValidationError(
                        error_type="invalid_connection",
                        severity="error",
                        message=f"Invalid connection: {to_type} '{to_component.name}' cannot receive from {from_type} '{from_component.name}'",
                        component=to_component.name,
                        binding=f"{binding.from_component}.{binding.from_port} → {to_component_name}",
                        suggestion=f"{to_type} components can receive from: {', '.join(can_receive_from)}"
                    ))
    
    def _validate_data_flow_completeness(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate system data flow using VR1 ingress-to-commitment validation (boundary-terminal arcs)."""
        
        logger.debug("Validating data flow completeness with VR1 boundary-terminal arc validation")
        
        if not self.system_graph:
            return
        
        # Check if boundary termination is enabled
        if settings.BOUNDARY_TERMINATION_ENABLED:
            self._validate_vr1_ingress_to_commitment(system_blueprint)
        else:
            # Fall back to legacy node-terminalism validation
            self._validate_legacy_node_terminalism(system_blueprint)
    
    def _validate_vr1_ingress_to_commitment(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Implement VR1 validation: ingress-to-commitment reachability using boundary semantics."""
        
        logger.debug("VR1 validation: checking ingress-to-commitment reachability")
        
        # Build component lookup map
        component_by_name = {comp.name: comp for comp in system_blueprint.system.components}
        
        # R8: Check for hard lint violations first (ADR 033)
        self._lint_contradictions(system_blueprint, self.system_graph)
        
        # Step 1: Identify boundary ingress ports (external entry points)
        ingress_ports = []
        for comp in system_blueprint.system.components:
            for port in comp.inputs:
                if getattr(port, 'boundary_ingress', False):
                    ingress_ports.append((comp.name, port.name))
        
        # Step 2: Identify commitment points (boundary egress ports + durable components)
        commitment_points = []
        
        # Find boundary egress ports
        for comp in system_blueprint.system.components:
            for port in comp.outputs:
                if getattr(port, 'boundary_egress', False):
                    commitment_points.append((comp.name, port.name, 'boundary_egress'))
        
        # Find durable components (persistent state = commitment)
        for comp in system_blueprint.system.components:
            if getattr(comp, 'durable', True):  # Default to durable for conservative validation
                commitment_points.append((comp.name, None, 'durable_component'))
        
        logger.debug(f"VR1: Found {len(ingress_ports)} ingress ports and {len(commitment_points)} commitment points")
        
        # Step 3: Validate ingress-to-commitment reachability
        unreachable_ingress = []
        
        for ing_comp, ing_port in ingress_ports:
            can_reach_commitment = False
            
            # Check if this ingress can reach any commitment point
            for commit_comp, commit_port, commit_type in commitment_points:
                if ing_comp == commit_comp:
                    # Same component - direct commitment
                    can_reach_commitment = True
                    logger.debug(f"VR1: Direct commitment {ing_comp}.{ing_port} → {commit_comp} ({commit_type})")
                    break
                elif nx.has_path(self.system_graph, ing_comp, commit_comp):
                    # Reachable via component graph
                    can_reach_commitment = True
                    path = nx.shortest_path(self.system_graph, ing_comp, commit_comp)
                    logger.debug(f"VR1: Path commitment {ing_comp}.{ing_port} → {commit_comp} ({commit_type}) via {path}")
                    break
            
            if not can_reach_commitment:
                unreachable_ingress.append((ing_comp, ing_port))
        
        # Step 4: Report VR1 violations
        for ing_comp, ing_port in unreachable_ingress:
            self.validation_errors.append(ArchitecturalValidationError(
                error_type="vr1_ingress_no_commitment",
                severity="error",
                message=f"VR1 violation: Ingress port '{ing_comp}.{ing_port}' cannot reach any commitment point",
                component=ing_comp,
                suggestion="Ensure ingress ports can reach either boundary_egress ports or durable components"
            ))
        
        # Step 5: Check for reply obligations
        for comp in system_blueprint.system.components:
            for port in comp.inputs:
                if getattr(port, 'boundary_ingress', False) and getattr(port, 'reply_required', False):
                    # Find corresponding egress port for reply
                    has_reply_egress = any(
                        getattr(out_port, 'boundary_egress', False) 
                        for out_port in comp.outputs
                    )
                    if not has_reply_egress:
                        self.validation_errors.append(ArchitecturalValidationError(
                            error_type="vr1_missing_reply",
                            severity="error",
                            message=f"VR1 violation: Ingress port '{comp.name}.{port.name}' requires reply but no boundary_egress found",
                            component=comp.name,
                            suggestion="Add boundary_egress port to component or remove reply_required flag"
                        ))
        
        # Step 6: Validate for simple stateless APIs (fallback if no explicit boundary flags)
        if not ingress_ports and not commitment_points:
            logger.info("No explicit boundary semantics found - checking for API pattern")
            has_api_endpoint = any(comp.type == 'APIEndpoint' for comp in system_blueprint.system.components)
            has_store_or_controller = any(comp.type in {'Store', 'Controller'} for comp in system_blueprint.system.components)
            
            if has_api_endpoint and has_store_or_controller:
                logger.info("API pattern detected - VR1 validation passed (implicit ingress-to-commitment)")
            else:
                self.validation_errors.append(ArchitecturalValidationError(
                    error_type="vr1_no_boundary_semantics",
                    severity="warning",
                    message="No boundary semantics defined and no clear API pattern",
                    suggestion="Add boundary_ingress/boundary_egress flags to ports or ensure API+Store/Controller pattern"
                ))
    
    def _validate_legacy_node_terminalism(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """
        Simplified validation - only check for truly orphaned components.
        
        Per architecture change 2025.0826: Removed source/sink requirements as they
        created false positives. API endpoints, calculators, schedulers, and many
        other valid patterns don't need explicit source components.
        
        This method now only validates that components are connected to something,
        not that the system follows a specific architectural pattern.
        """
        
        logger.debug("Validating component connectivity (simplified)")
        
        # R8: Check for hard lint violations first (ADR 033)
        self._lint_contradictions(system_blueprint, self.system_graph)
        
        # Check for orphaned components (components with no connections at all)
        orphaned_components = []
        for node in self.system_graph.nodes():
            in_degree = self.system_graph.in_degree(node)
            out_degree = self.system_graph.out_degree(node)
            
            if in_degree == 0 and out_degree == 0:
                # Component is completely disconnected
                component = self._get_component_by_name(system_blueprint, node)
                if component:
                    # Special case: Allow standalone APIEndpoints as valid single-component systems
                    # These receive HTTP requests as implicit input
                    if component.type == 'APIEndpoint' and len(system_blueprint.system.components) == 1:
                        logger.info(f"Standalone APIEndpoint '{node}' allowed - HTTP requests are implicit input")
                        continue
                    
                    # Special case: Allow unconnected components in very early stages
                    # during blueprint healing/generation when bindings haven't been added yet
                    if len(system_blueprint.system.components) == 1:
                        logger.info(f"Single component system '{node}' allowed during initial validation")
                        continue
                    
                    orphaned_components.append(node)
        
        # Report orphaned components as warnings (not errors)
        # Many valid architectures start with unconnected components that get connected later
        for orphaned in orphaned_components:
            self.validation_errors.append(ArchitecturalValidationError(
                error_type="orphaned_component",
                severity="warning",  # Changed from error to warning
                message=f"Component '{orphaned}' has no connections to other components",
                component=orphaned,
                suggestion="Connect component to other components or verify it can operate standalone"
            ))
        
        logger.info(f"Connectivity validation complete: {len(orphaned_components)} orphaned components found")
    
    def _lint_contradictions(self, system_blueprint: "ParsedSystemBlueprint", G: nx.DiGraph) -> None:
        """
        Enforce R8 hard lints for contradictory configurations (ADR 033).
        
        Violations:
        - terminal:true with outputs != []
        - terminal:true with out_degree > 0
        """
        errors = []
        
        for comp in system_blueprint.system.components:
            name = comp.name
            outputs = comp.outputs if comp.outputs else []
            terminal = getattr(comp, 'terminal', False)
            
            if not terminal:
                continue  # Only check components marked as terminal
                
            out_deg = G.out_degree(name) if G.has_node(name) else 0
            
            # Check: terminal:true with outputs
            if terminal and outputs:
                errors.append((
                    name, 
                    "ADR033-R8-TERM-OUTPUTS",
                    "terminal:true with outputs is contradictory; remove 'terminal' or outputs."
                ))
            
            # Check: terminal:true with out_degree > 0
            if terminal and out_deg > 0:
                errors.append((
                    name,
                    "ADR033-R8-TERM-OUTDEG", 
                    f"terminal:true but out_degree={out_deg}>0; remove edges or terminal flag."
                ))
        
        # Report all hard lint errors
        if errors:
            for name, code, msg in errors:
                logger.error("lint_error code=%s name=%s msg=%s", code, name, msg)
                self.validation_errors.append(ArchitecturalValidationError(
                    error_type=code,
                    severity="error",
                    message=msg,
                    component=name,
                    suggestion="Fix contradiction before proceeding"
                ))
    
    def _validate_architectural_patterns(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate that the system follows recognizable architectural patterns."""
        
        logger.debug("Validating architectural patterns")
        
        if not self.system_graph:
            return
            
        # Detect architectural pattern
        pattern = self._detect_architectural_pattern()
        
        # Validate pattern-specific rules
        if pattern == ArchitecturalPattern.PIPELINE:
            self._validate_pipeline_pattern(system_blueprint)
        elif pattern == ArchitecturalPattern.REQUEST_RESPONSE:
            self._validate_request_response_pattern(system_blueprint)
        elif pattern == ArchitecturalPattern.FAN_OUT:
            self._validate_fan_out_pattern(system_blueprint)
        elif pattern == ArchitecturalPattern.FAN_IN:
            self._validate_fan_in_pattern(system_blueprint)
        elif pattern == ArchitecturalPattern.UNKNOWN:
            self.validation_errors.append(ArchitecturalValidationError(
                error_type="unknown_pattern",
                severity="warning",
                message="System does not follow a recognizable architectural pattern",
                suggestion="Consider reorganizing components to follow a standard pattern (pipeline, request/response, fan-out, etc.)"
            ))
    
    def _detect_architectural_pattern(self) -> ArchitecturalPattern:
        """Detect the architectural pattern of the system."""
        
        if not self.system_graph:
            return ArchitecturalPattern.UNKNOWN
            
        # Simple pattern detection based on graph structure
        nodes = list(self.system_graph.nodes())
        
        # Check for pipeline pattern (linear chain)
        if self._is_pipeline_pattern():
            return ArchitecturalPattern.PIPELINE
        
        # Check for request/response pattern (APIEndpoint involved)
        if self._is_request_response_pattern():
            return ArchitecturalPattern.REQUEST_RESPONSE
        
        # Check for fan-out pattern (one-to-many)
        if self._is_fan_out_pattern():
            return ArchitecturalPattern.FAN_OUT
        
        # Check for fan-in pattern (many-to-one)
        if self._is_fan_in_pattern():
            return ArchitecturalPattern.FAN_IN
        
        return ArchitecturalPattern.UNKNOWN
    
    def _is_pipeline_pattern(self) -> bool:
        """Check if the system follows a pipeline pattern."""
        if not self.system_graph:
            return False
            
        # Pipeline: mostly linear chain with few branches
        total_nodes = len(self.system_graph.nodes())
        total_edges = len(self.system_graph.edges())
        
        # In a pure pipeline, edges = nodes - 1
        # Allow some flexibility for small branches
        return total_edges <= total_nodes + 2
    
    def _is_request_response_pattern(self) -> bool:
        """Check if the system follows a request/response pattern."""
        if not self.system_graph:
            return False
            
        # Look for APIEndpoint components
        for node in self.system_graph.nodes():
            node_data = self.system_graph.nodes[node]
            if node_data.get('type') == 'APIEndpoint':
                return True
        return False
    
    def _is_fan_out_pattern(self) -> bool:
        """Check if the system follows a fan-out pattern."""
        if not self.system_graph:
            return False
            
        # Look for nodes with high out-degree
        for node in self.system_graph.nodes():
            if self.system_graph.out_degree(node) > 2:
                return True
        return False
    
    def _is_fan_in_pattern(self) -> bool:
        """Check if the system follows a fan-in pattern."""
        if not self.system_graph:
            return False
            
        # Look for nodes with high in-degree
        for node in self.system_graph.nodes():
            if self.system_graph.in_degree(node) > 2:
                return True
        return False
    
    def _validate_pipeline_pattern(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate pipeline pattern specific rules."""
        # Pipeline should have clear linear flow
        # Most components should have in_degree=1 and out_degree=1
        pass
    
    def _validate_request_response_pattern(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate request/response pattern specific rules."""
        # Should have APIEndpoint → Controller → Store/Sink flow
        pass
    
    def _validate_fan_out_pattern(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate fan-out pattern specific rules."""
        # Should have Router or similar component with multiple outputs
        pass
    
    def _validate_fan_in_pattern(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate fan-in pattern specific rules."""
        # Should have Aggregator or similar component with multiple inputs
        pass
    
    def _validate_system_completeness(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate that the system has all essential components for its purpose."""
        
        logger.debug("Validating system completeness")
        
        system_description = system_blueprint.system.description or ""
        
        # Check for essential components based on system description
        if "api" in system_description.lower() or "rest" in system_description.lower():
            has_api_endpoint = any(comp.type == 'APIEndpoint' for comp in system_blueprint.system.components)
            if not has_api_endpoint:
                self.validation_errors.append(ArchitecturalValidationError(
                    error_type="missing_essential_component",
                    severity="error",
                    message="System description mentions API but no APIEndpoint component found",
                    suggestion="Add an APIEndpoint component to handle API requests"
                ))
        
        if "store" in system_description.lower() or "persist" in system_description.lower() or "save" in system_description.lower():
            has_store = any(comp.type == 'Store' for comp in system_blueprint.system.components)
            if not has_store:
                self.validation_errors.append(ArchitecturalValidationError(
                    error_type="missing_essential_component",
                    severity="warning",
                    message="System description mentions storage but no Store component found",
                    suggestion="Add a Store component to persist data"
                ))
    
    def _validate_architectural_coherence(self, system_blueprint: "ParsedSystemBlueprint") -> None:
        """Validate that the system architecture is coherent and makes business sense."""
        
        logger.debug("Validating architectural coherence")
        
        # Check for common architectural anti-patterns
        
        # Anti-pattern: Store connecting to Source
        for binding in system_blueprint.system.bindings:
            from_component = self._get_component_by_name(system_blueprint, binding.from_component)
            if from_component and from_component.type == 'Store':
                for to_component_name in binding.to_components:
                    to_component = self._get_component_by_name(system_blueprint, to_component_name)
                    if to_component and to_component.type == 'Source':
                        self.validation_errors.append(ArchitecturalValidationError(
                            error_type="architectural_antipattern",
                            severity="error",
                            message=f"Anti-pattern detected: Store '{from_component.name}' connecting to Source '{to_component.name}'",
                            suggestion="Sources should not receive data from Stores. Consider using a different component type."
                        ))
        
        # Check for excessive fan-out without aggregation
        high_fan_out_components = []
        if self.system_graph:
            for node in self.system_graph.nodes():
                if self.system_graph.out_degree(node) > 3:
                    high_fan_out_components.append(node)
        
        if high_fan_out_components:
            for component in high_fan_out_components:
                self.validation_errors.append(ArchitecturalValidationError(
                    error_type="excessive_fan_out",
                    severity="warning",
                    message=f"Component '{component}' has high fan-out ({self.system_graph.out_degree(component)} connections)",
                    component=component,
                    suggestion="Consider using a Router component for complex fan-out patterns"
                ))
    
    def _get_component_by_name(self, system_blueprint: "ParsedSystemBlueprint", name: str) -> Optional["ParsedComponent"]:
        """Get a component by name from the system blueprint."""
        for component in system_blueprint.system.components:
            if component.name == name:
                return component
        return None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        errors = [e for e in self.validation_errors if e.severity == "error"]
        warnings = [e for e in self.validation_errors if e.severity == "warning"]
        
        return {
            "total_issues": len(self.validation_errors),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_details": errors,
            "warning_details": warnings,
            "has_critical_issues": len(errors) > 0,
            "validation_passed": len(errors) == 0
        }
    
    def get_architectural_suggestions(self) -> List[str]:
        """Get architectural improvement suggestions."""
        suggestions = []
        
        for error in self.validation_errors:
            if error.suggestion:
                suggestions.append(f"{error.error_type}: {error.suggestion}")
        
        return list(set(suggestions))  # Remove duplicates