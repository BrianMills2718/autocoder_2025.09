"""
VR1 Boundary-Termination Validator

Implements port-faithful reachability validation that treats termination as a path 
property rather than node classification. Enables validation of modern API patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any
from enum import Enum
import logging
import uuid
from collections import defaultdict, deque

from ..blueprint_language.blueprint_parser import ParsedBlueprint, ParsedComponent, ParsedPort
from ..blueprint_language.validation_result_types import ValidationResult, ValidationFailure


class TerminationMode(Enum):
    """VR1 termination commitment types"""
    REPLY_COMMITMENT = "reply_commitment"      # Must reach satisfies_reply=true
    DURABLE_COMMITMENT = "durable_commitment"  # Must reach durable component input
    OBSERVABILITY_OK = "observability_ok"     # May terminate at observability export


@dataclass
class PathTraversalState:
    """State tracking for VR1 path traversal"""
    current_component: str
    current_port: str
    hops_used: int
    visited_components: Set[str] = field(default_factory=set)
    visited_edges: Set[Tuple[str, str, str, str]] = field(default_factory=set)
    path_trace: List[str] = field(default_factory=list)


@dataclass
class ReachabilityResult:
    """Result of VR1 reachability analysis"""
    ingress_point: str
    termination_found: bool
    termination_mode: Optional[TerminationMode]
    termination_details: Dict[str, Any] = field(default_factory=dict)
    path_trace: List[str] = field(default_factory=list)
    validation_errors: List[ValidationFailure] = field(default_factory=list)


class VR1Validator:
    """
    VR1 Boundary-Termination Validator
    
    Implements port-faithful path traversal with boundary semantics to validate
    that ingress points can reach appropriate termination commitments.
    """
    
    def __init__(self, blueprint: ParsedBlueprint):
        self.blueprint = blueprint
        self.logger = logging.getLogger(__name__)
        
        # VR1 configuration constants
        self.MAX_INGRESS_HOPS = 10  # Cutoff for ingress→termination paths
        self.MAX_OUTPUT_HOPS = 5    # Cutoff for output→input traversal
        
        # Build internal graph representation
        self.components_by_name = {blueprint.component.name: blueprint.component}
        self.connection_graph = self._build_connection_graph()
        
    def validate_boundary_termination(self) -> ValidationResult:
        """
        Main VR1 validation entry point with comprehensive telemetry
        
        Returns:
            ValidationResult with success/failure and detailed error taxonomy
        """
        # Import telemetry here to avoid circular imports
        from .vr1_telemetry import vr1_telemetry, VR1TelemetryContext
        from .vr1_error_taxonomy import VR1ErrorFactory
        
        # Create telemetry context
        session_id = str(uuid.uuid4())
        telemetry_context = VR1TelemetryContext(
            session_id=session_id,
            blueprint_name=getattr(self.blueprint, 'name', None),
            blueprint_version=getattr(self.blueprint, 'version', None),
            component_count=1,  # Single component blueprints for now
            connection_count=len(self.connection_graph),
            feature_flags={"boundary_termination_enabled": True}
        )
        
        with vr1_telemetry.validation_session(telemetry_context):
            try:
                # Phase 1: Identify boundary ingress points
                ingress_points = self._identify_boundary_ingress()
                telemetry_context.ingress_count = len(ingress_points)
                
                if not ingress_points:
                    result = ValidationResult(
                        passed=True,
                        level=None,  # VR1 validation doesn't map to existing levels
                        metadata={"message": "No boundary ingress points found - internal system validated by construction"}
                    )
                    vr1_telemetry.record_validation_result(True, [])
                    return result
                
                # Phase 2: Validate each ingress point can reach termination
                all_results = []
                validation_failures = []
                vr1_errors = []
                
                for ingress_comp, ingress_port in ingress_points:
                    result = self._validate_ingress_reachability(ingress_comp, ingress_port)
                    all_results.append(result)
                    validation_failures.extend(result.validation_errors)
                    
                    # Record path hops for telemetry
                    if result.path_trace:
                        vr1_telemetry.record_path_hops(len(result.path_trace))
                    
                    # Convert to VR1 errors if termination not found
                    if not result.termination_found:
                        vr1_error = VR1ErrorFactory.reply_commitment_unmet(
                            ingress_comp, ingress_port, result.path_trace
                        )
                        vr1_errors.append(vr1_error)
                
                # Phase 3: Aggregate results
                all_terminated = all(r.termination_found for r in all_results)
                
                if all_terminated:
                    final_result = ValidationResult(
                        passed=True,
                        level=None,
                        metadata={
                            "message": f"VR1 validation passed: all {len(ingress_points)} ingress points reach valid termination",
                            "ingress_count": len(ingress_points), 
                            "reachability_results": all_results
                        }
                    )
                else:
                    failed_ingress = [r.ingress_point for r in all_results if not r.termination_found]
                    final_result = ValidationResult(
                        passed=False,
                        level=None,
                        failures=validation_failures,
                        metadata={
                            "message": f"VR1 validation failed: {len(failed_ingress)} ingress points cannot reach termination",
                            "failed_ingress": failed_ingress, 
                            "reachability_results": all_results
                        }
                    )
                
                # Record telemetry
                vr1_telemetry.record_validation_result(all_terminated, vr1_errors)
                
                return final_result
                    
            except Exception as e:
                self.logger.exception("VR1 validation failed with exception")
                
                # Create and record exception error
                exception_error = VR1ErrorFactory.validation_exception(str(e), type(e).__name__)
                vr1_telemetry.record_validation_error(exception_error)
                
                return ValidationResult(
                    passed=False,
                    level=None,
                    failures=[ValidationFailure(
                        component_name=None,
                        failure_type=None,  # Will need to import proper types
                        error_message=f"VR1 validator internal error: {str(e)}",
                        context={"exception_type": type(e).__name__}
                    )]
                )

    def _identify_boundary_ingress(self) -> List[Tuple[str, str]]:
        """Identify all boundary ingress points in the blueprint"""
        ingress_points = []
        
        # For single-component blueprints, check the component's input ports
        component = self.blueprint.component
        for port in component.inputs:
            if getattr(port, 'boundary_ingress', False):
                ingress_points.append((component.name, port.name))
        
        return ingress_points

    def _build_connection_graph(self) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
        """
        Build connection graph for single-component blueprint
        
        For single components, connections are internal (input -> output via component logic)
        """
        # For single-component blueprints, connections are handled by component traversal
        # This would be expanded for multi-component systems
        return {}

    def _validate_ingress_reachability(self, comp_name: str, port_name: str) -> ReachabilityResult:
        """
        Validate that an ingress point can reach appropriate termination
        
        Uses port-faithful traversal that respects component type I/O coupling
        """
        component = self.components_by_name[comp_name]
        ingress_port = self._find_port(component, port_name, is_input=True)
        
        if not ingress_port:
            return ReachabilityResult(
                ingress_point=f"{comp_name}.{port_name}",
                termination_found=False,
                termination_mode=None,
                validation_errors=[ValidationFailure(
                    component_name=comp_name,
                    failure_type=None,  # Will need proper type
                    error_message=f"Ingress port {comp_name}.{port_name} not found",
                    context={"component": comp_name, "port": port_name}
                )]
            )
        
        # Determine termination commitment based on ingress port
        termination_mode = self._determine_termination_commitment(ingress_port)
        
        # Initialize traversal state
        initial_state = PathTraversalState(
            current_component=comp_name,
            current_port=port_name,
            hops_used=0,
            path_trace=[f"{comp_name}.{port_name}(ingress)"]
        )
        
        # Execute port-faithful reachability search
        termination_found, termination_details, final_state = self._execute_reachability_search(
            initial_state, termination_mode
        )
        
        return ReachabilityResult(
            ingress_point=f"{comp_name}.{port_name}",
            termination_found=termination_found,
            termination_mode=termination_mode,
            termination_details=termination_details,
            path_trace=final_state.path_trace,
            validation_errors=[]
        )

    def _execute_reachability_search(self, initial_state: PathTraversalState, 
                                   termination_mode: TerminationMode) -> Tuple[bool, Dict[str, Any], PathTraversalState]:
        """
        Execute breadth-first search with port-faithful traversal rules
        
        Returns:
            (termination_found, termination_details, final_state)
        """
        search_queue = deque([initial_state])
        visited_states = set()
        
        while search_queue:
            current_state = search_queue.popleft()
            
            # Check hop limit
            if current_state.hops_used >= self.MAX_INGRESS_HOPS:
                continue
                
            # Avoid cycles
            state_key = (current_state.current_component, current_state.current_port, 
                        tuple(sorted(current_state.visited_components)))
            if state_key in visited_states:
                continue
            visited_states.add(state_key)
            
            # Check if current position satisfies termination commitment
            is_terminated, termination_details = self._check_termination_commitment(
                current_state, termination_mode
            )
            
            if is_terminated:
                return True, termination_details, current_state
            
            # Generate next reachable states using port-faithful traversal
            next_states = self._generate_next_states(current_state)
            search_queue.extend(next_states)
        
        # No termination found
        return False, {}, current_state

    def _generate_next_states(self, state: PathTraversalState) -> List[PathTraversalState]:
        """
        Generate next reachable states using port-faithful component traversal
        
        Respects component type input→output coupling rules
        """
        component = self.components_by_name[state.current_component]
        next_states = []
        
        # Phase 1: Internal component traversal (input → output)
        if state.current_port in [p.name for p in component.inputs]:
            # Currently at input port - traverse to coupled outputs
            coupled_outputs = self._get_coupled_outputs(component, state.current_port)
            
            for output_port_name in coupled_outputs:
                new_state = PathTraversalState(
                    current_component=state.current_component,
                    current_port=output_port_name,
                    hops_used=state.hops_used,  # Internal traversal is "free"
                    visited_components=state.visited_components.copy(),
                    visited_edges=state.visited_edges.copy(),
                    path_trace=state.path_trace + [f"{state.current_component}.{output_port_name}(internal)"]
                )
                next_states.append(new_state)
        
        # Phase 2: External component traversal (output → connected inputs)
        # For single-component blueprints, this would connect to external systems
        # In multi-component systems, this would follow connection_graph
        if state.current_port in [p.name for p in component.outputs]:
            # Currently at output port - for single components, this is a termination point
            pass
        
        return next_states

    def _get_coupled_outputs(self, component: ParsedComponent, input_port_name: str) -> List[str]:
        """
        Get output ports coupled to an input port based on component type
        
        Implements component-specific I/O coupling rules for port-faithful traversal
        """
        component_type = component.type
        
        if component_type == "APIEndpoint":
            # APIEndpoint: request → response (1:1 coupling)
            if input_port_name == "request":
                return ["response"] if self._has_output_port(component, "response") else []
            return []
        
        elif component_type == "Controller":
            # Controller: input → output (1:1 coupling, flexible naming)
            input_names = [p.name for p in component.inputs]
            output_names = [p.name for p in component.outputs]
            
            if input_port_name in input_names and output_names:
                # Controller couples all inputs to all outputs (transformer pattern)
                return output_names
            return []
        
        elif component_type == "Store":
            # Store: write → write_status, read → data (specific coupling)
            if input_port_name == "write":
                return ["write_status"] if self._has_output_port(component, "write_status") else []
            elif input_port_name == "read":
                return ["data"] if self._has_output_port(component, "data") else []
            return []
        
        elif component_type == "Transformer":
            # Transformer: couples all inputs to all outputs (pure function)
            output_names = [p.name for p in component.outputs]
            return output_names
        
        elif component_type == "WebSocket":
            # WebSocket: connection_request → connection_status, message_in → message_out
            if input_port_name == "connection_request":
                return ["connection_status"] if self._has_output_port(component, "connection_status") else []
            elif input_port_name == "message_in":
                return ["message_out"] if self._has_output_port(component, "message_out") else []
            return []
        
        elif component_type in ["EventBus", "MessageQueue"]:
            # EventBus/MessageQueue: couples all inputs to all outputs (fan-out)
            output_names = [p.name for p in component.outputs]
            return output_names
        
        else:
            # Default: couples all inputs to all outputs (conservative)
            self.logger.warning(f"Unknown component type '{component_type}', using default coupling")
            output_names = [p.name for p in component.outputs]
            return output_names

    def _has_output_port(self, component: ParsedComponent, port_name: str) -> bool:
        """Check if component has output port with given name"""
        return any(port.name == port_name for port in component.outputs)

    def _determine_termination_commitment(self, ingress_port: ParsedPort) -> TerminationMode:
        """Determine what termination commitment an ingress port requires"""
        
        if getattr(ingress_port, 'reply_required', False):
            return TerminationMode.REPLY_COMMITMENT
        elif getattr(ingress_port, 'boundary_ingress', False):
            # Boundary ingress without reply requirement needs durable termination
            return TerminationMode.DURABLE_COMMITMENT
        else:
            # Internal ingress allows observability termination
            return TerminationMode.OBSERVABILITY_OK

    def _check_termination_commitment(self, state: PathTraversalState, 
                                    termination_mode: TerminationMode) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if current state satisfies the required termination commitment
        """
        component = self.components_by_name[state.current_component]
        
        if termination_mode == TerminationMode.REPLY_COMMITMENT:
            # Must reach satisfies_reply=true port (output port)
            current_port = self._find_port(component, state.current_port, is_input=False)
            if current_port and getattr(current_port, 'satisfies_reply', False):
                return True, {
                    "termination_type": "reply_satisfaction",
                    "port": f"{state.current_component}.{state.current_port}",
                    "satisfies_reply": True
                }
        
        elif termination_mode == TerminationMode.DURABLE_COMMITMENT:
            # Must reach durable component input
            input_port = self._find_port(component, state.current_port, is_input=True)
            if input_port and getattr(component, 'durable', False):
                return True, {
                    "termination_type": "durable_input",
                    "component": state.current_component,
                    "port": state.current_port,
                    "durable": True
                }
        
        elif termination_mode == TerminationMode.OBSERVABILITY_OK:
            # May terminate at observability export (output port)
            current_port = self._find_port(component, state.current_port, is_input=False)
            if current_port and getattr(current_port, 'observability_export', False):
                return True, {
                    "termination_type": "observability_export", 
                    "port": f"{state.current_component}.{state.current_port}",
                    "observability_export": True
                }
            # Also allow reply satisfaction or durable termination
            reply_satisfied, reply_details = self._check_termination_commitment(
                state, TerminationMode.REPLY_COMMITMENT
            )
            if reply_satisfied:
                return True, reply_details
                
            durable_satisfied, durable_details = self._check_termination_commitment(
                state, TerminationMode.DURABLE_COMMITMENT  
            )
            if durable_satisfied:
                return True, durable_details
        
        return False, {}

    def _find_port(self, component: ParsedComponent, port_name: str, is_input: bool) -> Optional[ParsedPort]:
        """Find a port by name in component inputs or outputs"""
        ports = component.inputs if is_input else component.outputs
        return next((port for port in ports if port.name == port_name), None)