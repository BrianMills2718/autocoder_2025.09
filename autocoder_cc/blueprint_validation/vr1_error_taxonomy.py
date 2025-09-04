"""
VR1 Error Taxonomy

Comprehensive error classification system for VR1 boundary-termination validation
with 27 distinct error types covering all failure modes.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import json
import re


class VR1ErrorCategory(Enum):
    """Top-level VR1 error categories"""
    INGRESS_ISSUES = "ingress_issues"              # Boundary ingress problems
    REACHABILITY_ISSUES = "reachability_issues"    # Path traversal failures  
    TERMINATION_ISSUES = "termination_issues"      # Commitment validation failures
    STRUCTURAL_ISSUES = "structural_issues"        # Blueprint structure problems
    SEMANTIC_ISSUES = "semantic_issues"            # Logic/semantic inconsistencies


class VR1ErrorType(Enum):
    """Complete VR1 error taxonomy - 27 distinct error types"""
    
    # INGRESS_ISSUES (5 types)
    NO_BOUNDARY_INGRESS = "no_boundary_ingress"                    # No boundary_ingress=true ports found
    INGRESS_PORT_NOT_FOUND = "ingress_port_not_found"             # Declared ingress port missing
    INVALID_INGRESS_CONFIG = "invalid_ingress_config"             # Malformed ingress port configuration
    CONFLICTING_INGRESS_FLAGS = "conflicting_ingress_flags"       # Contradictory boundary flags
    INGRESS_WITHOUT_COMPONENT = "ingress_without_component"       # Ingress port on missing component
    
    # REACHABILITY_ISSUES (8 types)
    NO_REACHABLE_TERMINATION = "no_reachable_termination"         # Cannot reach any valid termination
    HOP_LIMIT_EXCEEDED = "hop_limit_exceeded"                     # Exceeded MAX_INGRESS_HOPS cutoff
    DISCONNECTED_COMPONENT = "disconnected_component"             # Component not connected to graph
    INVALID_CONNECTION = "invalid_connection"                     # Malformed component connection
    MISSING_OUTPUT_PORT = "missing_output_port"                   # Expected output port not found
    MISSING_INPUT_PORT = "missing_input_port"                     # Expected input port not found
    SCC_CYCLE_DETECTED = "scc_cycle_detected"                     # Strongly connected component cycle
    PORT_COUPLING_VIOLATION = "port_coupling_violation"           # Component type I/O coupling violated
    
    # TERMINATION_ISSUES (7 types)
    REPLY_COMMITMENT_UNMET = "reply_commitment_unmet"             # reply_required but no satisfies_reply
    DURABLE_COMMITMENT_UNMET = "durable_commitment_unmet"         # boundary_ingress but no durable input
    OBSERVABILITY_COMMITMENT_UNMET = "observability_commitment_unmet"  # No observability path when required
    WEBSOCKET_HANDSHAKE_FAILED = "websocket_handshake_failed"     # WebSocket connection handshake failed
    GRPC_STREAMING_FAILED = "grpc_streaming_failed"               # gRPC streaming termination failed
    COMPOUND_COMMITMENT_FAILED = "compound_commitment_failed"     # Multi-path commitment predicate failed
    TERMINATION_SEMANTICS_INVALID = "termination_semantics_invalid"  # Invalid termination configuration
    
    # STRUCTURAL_ISSUES (4 types)
    COMPONENT_NOT_FOUND = "component_not_found"                   # Referenced component missing
    MALFORMED_BLUEPRINT = "malformed_blueprint"                   # Blueprint structure invalid
    MISSING_COMPONENT_TYPE = "missing_component_type"             # Component type not specified
    INVALID_COMPONENT_TYPE = "invalid_component_type"             # Unknown component type
    
    # SEMANTIC_ISSUES (3 types)
    INCONSISTENT_BOUNDARY_SEMANTICS = "inconsistent_boundary_semantics"  # Contradictory boundary flags
    DURABILITY_INCONSISTENCY = "durability_inconsistency"         # Durability logic inconsistent
    MONITORED_BUS_MISCONFIGURATION = "monitored_bus_misconfiguration"   # monitored_bus_ok configuration error


@dataclass
class VR1ErrorContext:
    """Rich context information for VR1 validation errors"""
    component_name: Optional[str] = None
    port_name: Optional[str] = None
    connection_source: Optional[str] = None
    connection_target: Optional[str] = None
    path_trace: List[str] = field(default_factory=list)
    hops_traversed: Optional[int] = None
    expected_termination: Optional[str] = None
    actual_termination: Optional[str] = None
    component_type: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VR1ValidationError:
    """Enhanced validation error with VR1 taxonomy and rich context"""
    error_type: VR1ErrorType
    error_category: VR1ErrorCategory
    message: str
    context: VR1ErrorContext = field(default_factory=VR1ErrorContext)
    suggestions: List[str] = field(default_factory=list)
    error_code: str = field(init=False)
    
    def __post_init__(self):
        """Generate structured error code"""
        self.error_code = f"VR1-{self.error_category.value.upper()}-{self.error_type.value.upper()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging"""
        return {
            "error_code": self.error_code,
            "error_type": self.error_type.value,
            "error_category": self.error_category.value,
            "message": self.message,
            "context": self._sanitize_context(),
            "suggestions": self.suggestions
        }
    
    def _sanitize_context(self) -> Dict[str, Any]:
        """Sanitize context for PII and sensitive data"""
        sanitized = {}
        
        # Safe fields that don't contain PII
        safe_fields = [
            "component_name", "port_name", "connection_source", "connection_target",
            "hops_traversed", "expected_termination", "actual_termination", "component_type"
        ]
        
        for field in safe_fields:
            value = getattr(self.context, field, None)
            if value is not None:
                sanitized[field] = value
        
        # Sanitize path trace (remove potential PII in port data)
        if self.context.path_trace:
            sanitized["path_trace"] = [self._sanitize_path_step(step) for step in self.context.path_trace]
        
        # Sanitize additional context
        if self.context.additional_context:
            sanitized["additional_context"] = self._sanitize_additional_context(
                self.context.additional_context
            )
        
        return sanitized
    
    def _sanitize_path_step(self, step: str) -> str:
        """Remove potential PII from path trace steps"""
        # Remove any data values, keep only component.port structure
        return re.sub(r'\(.*?\)', '(data)', step)
    
    def _sanitize_additional_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from additional context fields"""
        sanitized = {}
        
        # Allow structural information, block potential PII
        safe_keys = [
            "blueprint_version", "validation_mode", "feature_flags", "component_count",
            "connection_count", "validation_duration_ms", "ingress_count"
        ]
        
        for key, value in context.items():
            if key in safe_keys:
                sanitized[key] = value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, str) and len(value) < 20 and not self._contains_sensitive_patterns(value):  # Short, safe strings
                sanitized[key] = value
            else:
                sanitized[key] = "[REDACTED]"
        
        return sanitized
    
    def _contains_sensitive_patterns(self, value: str) -> bool:
        """Check if string contains patterns that might be sensitive data"""
        sensitive_patterns = [
            "user", "email", "password", "token", "key", "secret", "sensitive", "data"
        ]
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in sensitive_patterns)


class VR1ErrorFactory:
    """Factory for creating standardized VR1 validation errors"""
    
    @staticmethod
    def no_boundary_ingress() -> VR1ValidationError:
        """No boundary ingress points found in blueprint"""
        return VR1ValidationError(
            error_type=VR1ErrorType.NO_BOUNDARY_INGRESS,
            error_category=VR1ErrorCategory.INGRESS_ISSUES,
            message="No boundary ingress points found - blueprint has no external entry points",
            suggestions=[
                "Add boundary_ingress=true to at least one input port",
                "Verify component inputs are properly configured",
                "Check if this is an internal-only blueprint"
            ]
        )
    
    @staticmethod
    def reply_commitment_unmet(component: str, port: str, path_trace: List[str]) -> VR1ValidationError:
        """Reply commitment unmet - ingress requires reply but cannot reach satisfies_reply=true"""
        return VR1ValidationError(
            error_type=VR1ErrorType.REPLY_COMMITMENT_UNMET,
            error_category=VR1ErrorCategory.TERMINATION_ISSUES,
            message=f"Reply commitment unmet: {component}.{port} requires reply but cannot reach satisfies_reply=true port",
            context=VR1ErrorContext(
                component_name=component,
                port_name=port,
                path_trace=path_trace,
                expected_termination="satisfies_reply=true"
            ),
            suggestions=[
                "Add satisfies_reply=true to appropriate output port",
                "Verify path connectivity to response port",
                "Check component coupling rules for reply routing"
            ]
        )
    
    @staticmethod
    def hop_limit_exceeded(component: str, port: str, hops: int, limit: int) -> VR1ValidationError:
        """Hop limit exceeded during reachability search"""
        return VR1ValidationError(
            error_type=VR1ErrorType.HOP_LIMIT_EXCEEDED,
            error_category=VR1ErrorCategory.REACHABILITY_ISSUES,
            message=f"Hop limit exceeded: {component}.{port} traversed {hops} hops (limit: {limit})",
            context=VR1ErrorContext(
                component_name=component,
                port_name=port,
                hops_traversed=hops,
                additional_context={"hop_limit": limit}
            ),
            suggestions=[
                "Simplify blueprint architecture to reduce path length",
                "Check for cycles causing excessive path traversal",
                "Consider increasing hop limit if architecture requires deep paths"
            ]
        )
    
    @staticmethod
    def durable_commitment_unmet(component: str, port: str, path_trace: List[str]) -> VR1ValidationError:
        """Durable commitment unmet - boundary ingress cannot reach durable component"""
        return VR1ValidationError(
            error_type=VR1ErrorType.DURABLE_COMMITMENT_UNMET,
            error_category=VR1ErrorCategory.TERMINATION_ISSUES,
            message=f"Durable commitment unmet: {component}.{port} cannot reach durable component input",
            context=VR1ErrorContext(
                component_name=component,
                port_name=port,
                path_trace=path_trace,
                expected_termination="durable component input"
            ),
            suggestions=[
                "Add durable=true to terminating components (Store, Database)",
                "Verify path connectivity to persistent storage",
                "Check if termination should be at observability export instead"
            ]
        )
    
    @staticmethod
    def websocket_handshake_failed(component: str, details: Dict[str, Any]) -> VR1ValidationError:
        """WebSocket handshake validation failed"""
        return VR1ValidationError(
            error_type=VR1ErrorType.WEBSOCKET_HANDSHAKE_FAILED,
            error_category=VR1ErrorCategory.TERMINATION_ISSUES,
            message=f"WebSocket handshake failed: connection_request cannot reach connection_status",
            context=VR1ErrorContext(
                component_name=component,
                port_name="connection_request",
                expected_termination="connection_status with satisfies_reply=true",
                additional_context=details
            ),
            suggestions=[
                "Add connection_status output port with satisfies_reply=true",
                "Verify WebSocket component coupling rules",
                "Check that connection_request maps to connection_status"
            ]
        )
    
    @staticmethod
    def missing_output_port(component: str, port: str, component_type: str) -> VR1ValidationError:
        """Expected output port not found on component"""
        return VR1ValidationError(
            error_type=VR1ErrorType.MISSING_OUTPUT_PORT,
            error_category=VR1ErrorCategory.REACHABILITY_ISSUES,
            message=f"Missing output port: {component}.{port} expected for {component_type}",
            context=VR1ErrorContext(
                component_name=component,
                port_name=port,
                component_type=component_type
            ),
            suggestions=[
                f"Add {port} output port to {component_type} component",
                "Check component type coupling requirements",
                "Verify port naming conventions"
            ]
        )
    
    @staticmethod
    def invalid_component_type(component: str, component_type: str) -> VR1ValidationError:
        """Unknown or invalid component type"""
        return VR1ValidationError(
            error_type=VR1ErrorType.INVALID_COMPONENT_TYPE,
            error_category=VR1ErrorCategory.STRUCTURAL_ISSUES,
            message=f"Invalid component type: {component} has unknown type '{component_type}'",
            context=VR1ErrorContext(
                component_name=component,
                component_type=component_type
            ),
            suggestions=[
                "Use valid component types: APIEndpoint, WebSocket, Store, Controller, etc.",
                "Check for typos in component type",
                "Verify component type is supported by VR1 validation"
            ]
        )
    
    @staticmethod
    def port_coupling_violation(component: str, component_type: str, input_port: str, 
                              expected_outputs: List[str]) -> VR1ValidationError:
        """Component type I/O coupling rules violated"""
        return VR1ValidationError(
            error_type=VR1ErrorType.PORT_COUPLING_VIOLATION,
            error_category=VR1ErrorCategory.REACHABILITY_ISSUES,
            message=f"Port coupling violation: {component_type}.{input_port} should couple to {expected_outputs}",
            context=VR1ErrorContext(
                component_name=component,
                port_name=input_port,
                component_type=component_type,
                additional_context={"expected_outputs": expected_outputs}
            ),
            suggestions=[
                f"Add expected output ports: {', '.join(expected_outputs)}",
                f"Check {component_type} component coupling requirements",
                "Verify port-faithful traversal logic"
            ]
        )
    
    @staticmethod
    def inconsistent_boundary_semantics(component: str, port: str, 
                                      conflicting_flags: List[str]) -> VR1ValidationError:
        """Contradictory boundary semantics flags"""
        return VR1ValidationError(
            error_type=VR1ErrorType.INCONSISTENT_BOUNDARY_SEMANTICS,
            error_category=VR1ErrorCategory.SEMANTIC_ISSUES,
            message=f"Inconsistent boundary semantics: {component}.{port} has conflicting flags: {conflicting_flags}",
            context=VR1ErrorContext(
                component_name=component,
                port_name=port,
                additional_context={"conflicting_flags": conflicting_flags}
            ),
            suggestions=[
                "Review boundary semantics configuration",
                "Ensure flags are logically consistent",
                "Check VR1 boundary semantics documentation"
            ]
        )
    
    @staticmethod
    def validation_exception(error_message: str, exception_type: str) -> VR1ValidationError:
        """Internal validation exception occurred"""
        return VR1ValidationError(
            error_type=VR1ErrorType.MALFORMED_BLUEPRINT,  # Generic structural issue
            error_category=VR1ErrorCategory.STRUCTURAL_ISSUES,
            message=f"Validation exception: {error_message}",
            context=VR1ErrorContext(
                additional_context={"exception_type": exception_type}
            ),
            suggestions=[
                "Check blueprint structure and syntax",
                "Verify all required fields are present",
                "Review blueprint against schema"
            ]
        )