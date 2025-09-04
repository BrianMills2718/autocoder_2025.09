"""
Boundary Semantics Engine

Implements advanced VR1 commitment predicate validation for complex termination patterns
including WebSocket handshakes, gRPC streams, and observability-only termination.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Union, Callable, Any
from enum import Enum
import logging

from .vr1_validator import VR1Validator, TerminationMode, ReachabilityResult, PathTraversalState
from ..blueprint_language.blueprint_parser import ParsedComponent, ParsedPort


class CommitmentType(Enum):
    """Advanced commitment predicate types"""
    SIMPLE_REPLY = "simple_reply"                    # Basic satisfies_reply=true
    SIMPLE_DURABLE = "simple_durable"                # Basic durable component input
    SIMPLE_OBSERVABILITY = "simple_observability"    # Basic observability_export=true
    
    COMPOUND_HANDSHAKE = "compound_handshake"        # WebSocket: connection AND messaging
    COMPOUND_STREAMING = "compound_streaming"        # gRPC: multiple stream terminations
    CONDITIONAL_OBSERVABILITY = "conditional_observability"  # monitored_bus_ok dependent


@dataclass
class CommitmentPredicate:
    """
    Complex termination condition that may require multiple simultaneous paths
    """
    commitment_type: CommitmentType
    required_paths: List[Dict[str, Any]] = field(default_factory=list)
    optional_paths: List[Dict[str, Any]] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    

class BoundarySemantics:
    """
    Advanced boundary semantics engine for complex VR1 validation patterns
    """
    
    def __init__(self, vr1_validator: VR1Validator):
        self.vr1_validator = vr1_validator
        self.blueprint = vr1_validator.blueprint
        self.logger = logging.getLogger(__name__)
        
    def validate_advanced_commitments(self) -> List[ReachabilityResult]:
        """
        Validate advanced commitment predicates beyond basic VR1
        
        Returns:
            List of ReachabilityResult with enhanced commitment validation
        """
        results = []
        
        # Get all boundary ingress points
        ingress_points = self.vr1_validator._identify_boundary_ingress()
        
        for comp_name, port_name in ingress_points:
            component = self.vr1_validator.components_by_name[comp_name]
            ingress_port = self.vr1_validator._find_port(component, port_name, is_input=True)
            
            # Determine commitment predicate for this ingress
            predicate = self._build_commitment_predicate(component, ingress_port)
            
            # Validate commitment predicate
            result = self._validate_commitment_predicate(comp_name, port_name, predicate)
            results.append(result)
            
        return results
    
    def _build_commitment_predicate(self, component: ParsedComponent, 
                                  ingress_port: ParsedPort) -> CommitmentPredicate:
        """
        Build commitment predicate based on component type and port semantics
        """
        component_type = component.type
        
        if component_type == "WebSocket":
            return self._build_websocket_predicate(component, ingress_port)
        elif component_type == "gRPCEndpoint":
            return self._build_grpc_predicate(component, ingress_port)
        elif self._has_monitored_bus_allowance(component):
            return self._build_observability_predicate(component, ingress_port)
        else:
            return self._build_simple_predicate(component, ingress_port)
    
    def _build_websocket_predicate(self, component: ParsedComponent, 
                                 ingress_port: ParsedPort) -> CommitmentPredicate:
        """
        Build WebSocket handshake commitment predicate
        
        WebSocket requires:
        1. connection_request → connection_status (handshake)
        2. message_in → message_out OR observability (ongoing messaging)
        """
        if ingress_port.name == "connection_request":
            # Connection handshake: must reach connection_status
            return CommitmentPredicate(
                commitment_type=CommitmentType.COMPOUND_HANDSHAKE,
                required_paths=[{
                    "from_port": "connection_request",
                    "termination_type": "reply_satisfaction",
                    "target_port": "connection_status",
                    "satisfies_reply": True
                }],
                conditions={"websocket_handshake": True}
            )
        
        elif ingress_port.name == "message_in":
            # Message handling: may terminate at message_out OR observability
            return CommitmentPredicate(
                commitment_type=CommitmentType.CONDITIONAL_OBSERVABILITY,
                required_paths=[{
                    "from_port": "message_in", 
                    "termination_type": "reply_satisfaction_or_observability",
                    "alternatives": ["message_out", "observability_export"]
                }],
                conditions={"websocket_messaging": True, "monitored_bus_ok": getattr(component, 'monitored_bus_ok', False)}
            )
        
        else:
            return self._build_simple_predicate(component, ingress_port)
    
    def _build_grpc_predicate(self, component: ParsedComponent,
                            ingress_port: ParsedPort) -> CommitmentPredicate:
        """
        Build gRPC commitment predicate for unary and streaming patterns
        """
        if "unary" in ingress_port.name:
            # gRPC Unary: request → response (1:1)
            return CommitmentPredicate(
                commitment_type=CommitmentType.SIMPLE_REPLY,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "reply_satisfaction", 
                    "satisfies_reply": True
                }]
            )
        
        elif "stream" in ingress_port.name:
            # gRPC Streaming: may have multiple termination points
            return CommitmentPredicate(
                commitment_type=CommitmentType.COMPOUND_STREAMING,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "streaming_termination",
                    "stream_semantics": True
                }],
                conditions={"grpc_streaming": True}
            )
        
        else:
            return self._build_simple_predicate(component, ingress_port)

    def _build_observability_predicate(self, component: ParsedComponent,
                                     ingress_port: ParsedPort) -> CommitmentPredicate:
        """
        Build predicate for components with monitored_bus_ok=true
        
        These components may terminate at observability exports only
        """
        if getattr(component, 'monitored_bus_ok', False):
            return CommitmentPredicate(
                commitment_type=CommitmentType.CONDITIONAL_OBSERVABILITY,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "observability_or_standard",
                    "allow_observability_only": True
                }],
                conditions={"monitored_bus_ok": True}
            )
        else:
            return self._build_simple_predicate(component, ingress_port)

    def _build_simple_predicate(self, component: ParsedComponent,
                               ingress_port: ParsedPort) -> CommitmentPredicate:
        """Build simple commitment predicate for standard cases"""
        
        if getattr(ingress_port, 'reply_required', False):
            return CommitmentPredicate(
                commitment_type=CommitmentType.SIMPLE_REPLY,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "reply_satisfaction",
                    "satisfies_reply": True
                }]
            )
        elif getattr(ingress_port, 'boundary_ingress', False):
            return CommitmentPredicate(
                commitment_type=CommitmentType.SIMPLE_DURABLE,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "durable_input",
                    "durable": True
                }]
            )
        else:
            return CommitmentPredicate(
                commitment_type=CommitmentType.SIMPLE_OBSERVABILITY,
                required_paths=[{
                    "from_port": ingress_port.name,
                    "termination_type": "observability_export",
                    "observability_export": True
                }]
            )

    def _validate_observability_termination(self, state: PathTraversalState,
                                          predicate: CommitmentPredicate) -> tuple[bool, Dict[str, Any]]:
        """
        Validate observability-only termination with monitored_bus_ok
        """
        component = self.vr1_validator.components_by_name[state.current_component]
        current_port = self.vr1_validator._find_port(component, state.current_port, is_input=False)
        
        if not current_port:
            return False, {}
        
        # Check if observability export is allowed
        if (getattr(current_port, 'observability_export', False) and 
            predicate.conditions.get("monitored_bus_ok", False)):
            
            return True, {
                "termination_type": "observability_only",
                "port": f"{state.current_component}.{state.current_port}",
                "observability_export": True,
                "monitored_bus_ok": True,
                "justification": "Component explicitly allows observability-only termination"
            }
        
        # Fall back to standard termination validation
        return self._validate_standard_termination(state, predicate)

    def _validate_standard_termination(self, state: PathTraversalState,
                                     predicate: CommitmentPredicate) -> tuple[bool, Dict[str, Any]]:
        """Validate standard termination using VR1 validator"""
        
        # Map predicate to appropriate TerminationMode
        if predicate.commitment_type == CommitmentType.SIMPLE_REPLY:
            termination_mode = TerminationMode.REPLY_COMMITMENT
        elif predicate.commitment_type == CommitmentType.SIMPLE_DURABLE:
            termination_mode = TerminationMode.DURABLE_COMMITMENT
        else:
            termination_mode = TerminationMode.OBSERVABILITY_OK
        
        return self.vr1_validator._check_termination_commitment(state, termination_mode)

    def _has_monitored_bus_allowance(self, component: ParsedComponent) -> bool:
        """Check if component allows observability-only termination"""
        return getattr(component, 'monitored_bus_ok', False)

    def _validate_commitment_predicate(self, comp_name: str, port_name: str,
                                     predicate: CommitmentPredicate) -> ReachabilityResult:
        """
        Validate complex commitment predicate with multiple required paths
        """
        ingress_point = f"{comp_name}.{port_name}"
        
        if predicate.commitment_type in [CommitmentType.SIMPLE_REPLY, 
                                       CommitmentType.SIMPLE_DURABLE,
                                       CommitmentType.SIMPLE_OBSERVABILITY]:
            # Delegate to basic VR1 validator
            return self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
        
        # Handle compound commitment predicates
        all_paths_satisfied = True
        validation_errors = []
        path_results = {}
        
        for required_path in predicate.required_paths:
            path_satisfied, path_details = self._validate_required_path(
                comp_name, port_name, required_path, predicate.conditions
            )
            
            path_results[required_path.get("from_port", "unknown")] = {
                "satisfied": path_satisfied,
                "details": path_details
            }
            
            if not path_satisfied:
                all_paths_satisfied = False
                validation_errors.append(self._create_path_error(required_path, path_details))
        
        # For WebSocket handshake and compound cases, we need to check if the basic VR1 validation passes
        if predicate.commitment_type == CommitmentType.COMPOUND_HANDSHAKE:
            # For WebSocket handshake, validate the basic connection
            basic_result = self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
            all_paths_satisfied = basic_result.termination_found
            
        elif predicate.commitment_type == CommitmentType.CONDITIONAL_OBSERVABILITY:
            # For conditional observability, check if the paths validation succeeded
            # all_paths_satisfied is already set from the path validation loop
            pass
        
        return ReachabilityResult(
            ingress_point=ingress_point,
            termination_found=all_paths_satisfied,
            termination_mode=None,  # Complex predicate doesn't map to simple mode
            termination_details={
                "commitment_type": predicate.commitment_type.value,
                "path_results": path_results,
                "conditions": predicate.conditions
            },
            validation_errors=validation_errors if not all_paths_satisfied else []
        )

    def _validate_required_path(self, comp_name: str, port_name: str, 
                              path_spec: Dict[str, Any],
                              conditions: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """
        Validate a single required path within a compound commitment
        """
        termination_type = path_spec.get("termination_type", "unknown")
        
        if termination_type == "reply_satisfaction":
            return self._validate_reply_satisfaction_path(comp_name, port_name, path_spec)
        
        elif termination_type == "reply_satisfaction_or_observability":
            # Try reply satisfaction first, then observability
            reply_ok, reply_details = self._validate_reply_satisfaction_path(comp_name, port_name, path_spec)
            if reply_ok:
                return True, reply_details
                
            if conditions.get("monitored_bus_ok", False):
                obs_ok, obs_details = self._validate_observability_path(comp_name, port_name, path_spec)
                return obs_ok, obs_details
            
            return False, {"error": "Neither reply satisfaction nor observability termination found"}
        
        elif termination_type == "observability_or_standard":
            # Observability OR any standard termination
            if conditions.get("monitored_bus_ok", False):
                obs_ok, obs_details = self._validate_observability_path(comp_name, port_name, path_spec)
                if obs_ok:
                    return True, obs_details
            
            # Fall back to standard validation
            standard_result = self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
            return standard_result.termination_found, standard_result.termination_details
        
        elif termination_type == "streaming_termination":
            return self._validate_grpc_streaming(comp_name, port_name)
        
        else:
            return False, {"error": f"Unknown termination type: {termination_type}"}

    def _validate_reply_satisfaction_path(self, comp_name: str, port_name: str,
                                        path_spec: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Validate reply satisfaction path"""
        result = self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
        
        if (result.termination_found and 
            result.termination_mode == TerminationMode.REPLY_COMMITMENT):
            return True, result.termination_details
        
        return False, {"error": "Reply satisfaction path not found"}

    def _validate_observability_path(self, comp_name: str, port_name: str,
                                   path_spec: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Validate observability export path"""
        # Check if component has monitored_bus_ok and observability export ports
        component = self.vr1_validator.components_by_name[comp_name]
        
        if not getattr(component, 'monitored_bus_ok', False):
            return False, {"error": "Component does not allow observability-only termination"}
        
        # Look for observability export ports
        observability_ports = [p for p in component.outputs if getattr(p, 'observability_export', False)]
        
        if not observability_ports:
            return False, {"error": "No observability export ports found"}
        
        # For single-component blueprints, validate that input can reach output through component coupling
        if port_name in [p.name for p in component.inputs]:
            coupled_outputs = self.vr1_validator._get_coupled_outputs(component, port_name)
            observability_outputs = [p.name for p in observability_ports]
            
            # Check if any coupled output is an observability export
            if any(output in observability_outputs for output in coupled_outputs):
                return True, {
                    "termination_type": "observability_export",
                    "observability_ports": observability_outputs,
                    "monitored_bus_ok": True
                }
        
        return False, {"error": "Observability export path not reachable from input"}

    def _validate_websocket_handshake(self, comp_name: str, port_name: str) -> tuple[bool, Dict[str, Any]]:
        """
        Validate WebSocket connection handshake semantics
        
        Must ensure connection_request can reach connection_status with satisfies_reply=true
        """
        if port_name != "connection_request":
            return False, {"error": "WebSocket handshake validation requires connection_request port"}
        
        # Use specialized traversal for WebSocket handshake
        component = self.vr1_validator.components_by_name[comp_name]
        connection_status_port = self.vr1_validator._find_port(component, "connection_status", is_input=False)
        
        if not connection_status_port or not getattr(connection_status_port, 'satisfies_reply', False):
            return False, {
                "error": "WebSocket handshake requires connection_status port with satisfies_reply=true",
                "found_port": connection_status_port is not None,
                "satisfies_reply": getattr(connection_status_port, 'satisfies_reply', False) if connection_status_port else False
            }
        
        # Validate reachability using standard VR1 algorithm
        result = self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
        
        if result.termination_found:
            return True, {
                "websocket_handshake": True,
                "connection_established": True,
                "path_trace": result.path_trace
            }
        
        return False, {"error": "WebSocket handshake path not reachable"}

    def _validate_grpc_streaming(self, comp_name: str, port_name: str) -> tuple[bool, Dict[str, Any]]:
        """
        Validate gRPC streaming patterns with potential multiple terminations
        """
        # gRPC streaming may terminate at:
        # 1. Response stream ports
        # 2. Status/error ports  
        # 3. Observability exports (if monitored_bus_ok=true)
        
        component = self.vr1_validator.components_by_name[comp_name]
        
        # Look for streaming response ports
        streaming_outputs = [
            port for port in component.outputs 
            if "stream" in port.name or "response" in port.name
        ]
        
        if not streaming_outputs:
            return False, {"error": "gRPC streaming component has no streaming output ports"}
        
        # Validate at least one streaming termination is reachable
        for output_port in streaming_outputs:
            if (getattr(output_port, 'satisfies_reply', False) or 
                getattr(output_port, 'observability_export', False)):
                result = self.vr1_validator._validate_ingress_reachability(comp_name, port_name)
                if result.termination_found:
                    return True, {
                        "grpc_streaming": True,
                        "terminating_port": output_port.name,
                        "path_trace": result.path_trace
                    }
        
        return False, {"error": "No reachable gRPC streaming termination found"}

    def _create_path_error(self, path_spec: Dict[str, Any], path_details: Dict[str, Any]):
        """Create validation error for failed path"""
        from ..blueprint_language.validation_result_types import ValidationFailure
        
        return ValidationFailure(
            component_name=None,
            failure_type=None,  # Will need proper types
            error_message=f"Required path failed: {path_spec.get('termination_type', 'unknown')}",
            context={
                "path_spec": path_spec,
                "path_details": path_details
            }
        )