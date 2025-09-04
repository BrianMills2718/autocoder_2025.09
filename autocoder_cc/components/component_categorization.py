"""
Component role categorization for unified Store vs Sink handling.
Implements ADR 033: Topology-first inference for component roles.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional


class Role(Enum):
    """Component roles in the data flow architecture."""
    SOURCE = auto()
    TRANSFORMER = auto()
    SINK = auto()  # terminal - where dataflow ends


@dataclass
class RoleView:
    """View of a component's role with reasoning."""
    declared: Role
    effective: Role
    reasons: List[str]


# Type to role mapping - used as priors when topology is ambiguous
TYPE_PRIOR: Dict[str, Role] = {
    "Source": Role.SOURCE,
    "EventSource": Role.SOURCE,
    "Transformer": Role.TRANSFORMER,
    "Model": Role.TRANSFORMER,
    "StreamProcessor": Role.TRANSFORMER,
    "Router": Role.TRANSFORMER,
    "Controller": Role.TRANSFORMER,
    "Accumulator": Role.TRANSFORMER,
    "Aggregator": Role.TRANSFORMER,
    "Filter": Role.TRANSFORMER,
    "Sink": Role.SINK,
    "Store": Role.SINK,          # prior only; topology can override
    "APIEndpoint": Role.SINK,    # prior only; topology can override
    "WebSocket": Role.SINK,      # prior only; topology can override
}


def declared_role(component_type: str) -> Role:
    """Get the declared role based on component type."""
    return TYPE_PRIOR.get(component_type, Role.TRANSFORMER)


def infer_effective_role(comp: dict, in_deg: int, out_deg: int) -> RoleView:
    """
    Topology-first inference of component role.
    
    Rules (in order):
      R1: outputs → TRANSFORMER
      R2: out_degree > 0 → TRANSFORMER
      R4: terminal:true → SINK (only if no outgoing edges)
      R3: no outputs and out_degree == 0 → SINK
      R5: type prior fallback (rarely used)
    
    Args:
        comp: Component dictionary with 'type', 'outputs', 'terminal' fields
        in_deg: Number of incoming edges in the graph
        out_deg: Number of outgoing edges in the graph
        
    Returns:
        RoleView with declared role, effective role, and reasoning
    """
    comp_type = comp.get("type", "Unknown")
    decl = declared_role(comp_type)
    reasons = [f"declared={decl.name}"]
    
    # R1: outputs imply emission (except for Sources which originate data, and Stores when configured)
    outputs = comp.get("outputs") or []
    if outputs:
        if decl == Role.SOURCE:
            return RoleView(decl, Role.SOURCE, reasons + ["source with outputs (R1 exception)"])
        
        # R1 Store exception: When HEAL_STORE_AS_SINK is enabled, Stores with outputs remain Stores
        if decl == Role.SINK and comp.get("type") == "Store":
            from autocoder_cc.core.config import Settings
            settings = Settings()
            if settings.HEAL_STORE_AS_SINK:
                return RoleView(decl, Role.SINK, reasons + ["store as sink with outputs (R1 store exception)"])
        
        return RoleView(decl, Role.TRANSFORMER, reasons + ["outputs present (R1)"])
    
    # R2: edge-confirmed emission
    if out_deg > 0:
        return RoleView(decl, Role.TRANSFORMER, reasons + ["out_degree>0 (R2)"])
    
    # R4: explicit terminal (guarded)
    if comp.get("terminal") is True:
        return RoleView(decl, Role.SINK, reasons + ["terminal:true (R4)"])
    
    # R3: inert terminal default
    if out_deg == 0:
        return RoleView(decl, Role.SINK, reasons + ["no outputs & out_degree==0 (R3)"])
    
    # R5: type prior fallback (defensive - should rarely trigger)
    # This only happens with degraded inputs (e.g., graph not built yet)
    # We avoid classifying as SOURCE without evidence to prevent imposing
    # unreachable-path obligations
    eff = decl if decl != Role.SOURCE else Role.TRANSFORMER
    return RoleView(decl, eff, reasons + ["type prior fallback (R5)"])


def would_violate_r8(comp: dict, new_out_deg: int) -> bool:
    """
    Check if adding an edge would violate R8 hard constraints.
    
    R8 violations:
    - terminal:true with out_degree > 0
    - outputs != [] with terminal:true
    
    Args:
        comp: Component dictionary
        new_out_deg: What the out_degree would be after adding edge
        
    Returns:
        True if adding edge would violate R8
    """
    outputs = comp.get("outputs") or []
    terminal = comp.get("terminal", False)
    
    # terminal:true with outputs is already a violation
    if terminal and outputs:
        return True
    
    # terminal:true with new edge would violate
    if terminal and new_out_deg > 0:
        return True
    
    return False


def diagnose_role_deltas(role_views: Dict[str, RoleView], echo=None, logger=None) -> List[tuple]:
    """
    Diagnose and report role changes between declared and effective.
    
    Args:
        role_views: Map of component name to RoleView
        echo: Optional CLI echo function for warnings
        logger: Optional logger for detailed output
        
    Returns:
        List of (name, declared, effective, reasons) for components that changed
    """
    flips = [
        (name, rv.declared.name, rv.effective.name, rv.reasons)
        for name, rv in role_views.items()
        if rv.declared != rv.effective
    ]
    
    if flips:
        if echo:
            echo(f"⚠️ Role reconciliation changed {len(flips)} component(s). Use --verbose for details.")
        
        if logger:
            for name, decl, eff, reasons in flips:
                logger.warning(
                    "role_flip name=%s declared=%s effective=%s reasons=%s",
                    name, decl, eff, reasons
                )
    
    return flips