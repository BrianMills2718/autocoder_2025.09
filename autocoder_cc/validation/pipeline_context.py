from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class DataFlowPattern(Enum):
    """Common data flow patterns in systems"""
    STREAM = "stream"          # Source → Transform → Sink
    API = "api"                # APIEndpoint → Controller → Store
    BATCH = "batch"            # Source → Accumulator → Processor → Store
    REALTIME = "realtime"      # WebSocket → Router → Aggregator
    PIPELINE = "pipeline"      # Multi-stage transformation

@dataclass
class ValidationError:
    """Represents a configuration validation error"""
    component: str
    field: str
    error_type: str  # missing, invalid, conflict
    message: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "component": self.component,
            "field": self.field,
            "error_type": self.error_type,
            "message": self.message,
            "suggestion": self.suggestion
        }

@dataclass
class PipelineContext:
    """
    Rich context for understanding component configuration needs.
    This is the 'brain' that understands the entire system.
    """
    # System-level context
    system_name: str
    system_description: str
    system_capabilities: List[str] = field(default_factory=list)
    deployment_target: str = "local"  # "local", "docker", "kubernetes"
    environment: str = "development"  # "development", "staging", "production"
    
    # Component-specific context
    component_name: str = ""
    component_type: str = ""  # "Source", "Transformer", etc.
    component_role: str = ""  # Human-readable role description
    
    # Pipeline relationships
    upstream_components: List[Dict[str, str]] = field(default_factory=list)
    downstream_components: List[Dict[str, str]] = field(default_factory=list)
    data_flow_pattern: Optional[DataFlowPattern] = None
    
    # Data flow information
    input_data_schema: Optional[Dict[str, Any]] = None
    output_data_schema: Optional[Dict[str, Any]] = None
    data_flow_description: Optional[str] = None
    expected_throughput: Optional[str] = None  # "high", "medium", "low"
    
    # Current state (use factories for mutable defaults)
    existing_config: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[ValidationError] = field(default_factory=list)
    
    # Resource tracking for conflict detection
    used_resources: Dict[str, Any] = field(default_factory=lambda: {
        "ports": set(),
        "database_urls": set(),
        "file_paths": set(),
        "api_paths": set(),
        "queue_names": set(),
        "topic_names": set(),
        "environment_variables": set()
    })
    
    def to_prompt_context(self) -> str:
        """Convert to LLM-friendly context description"""
        context_parts = [
            f"System: {self.system_name}",
            f"Description: {self.system_description}",
            f"Component: {self.component_name} ({self.component_type})",
            f"Role: {self.component_role}",
            f"Environment: {self.environment}",
            f"Deployment: {self.deployment_target}"
        ]
        
        if self.upstream_components:
            upstream = ", ".join([f"{c['name']} ({c['type']})" for c in self.upstream_components])
            context_parts.append(f"Upstream: {upstream}")
            
        if self.downstream_components:
            downstream = ", ".join([f"{c['name']} ({c['type']})" for c in self.downstream_components])
            context_parts.append(f"Downstream: {downstream}")
            
        if self.data_flow_description:
            context_parts.append(f"Data Flow: {self.data_flow_description}")
            
        return "\n".join(context_parts)
        
    def get_upstream_outputs(self) -> List[Dict[str, Any]]:
        """Get output schemas from upstream components"""
        # Implementation to extract upstream output schemas
        outputs = []
        for component in self.upstream_components:
            # In real implementation, would query component registry
            outputs.append({
                "component": component["name"],
                "schema": {}  # Would be populated from component metadata
            })
        return outputs
        
    def get_downstream_expectations(self) -> List[Dict[str, Any]]:
        """Get input expectations from downstream components"""
        # Implementation to understand downstream requirements
        expectations = []
        for component in self.downstream_components:
            expectations.append({
                "component": component["name"],
                "expected_schema": {}  # Would be populated from component metadata
            })
        return expectations