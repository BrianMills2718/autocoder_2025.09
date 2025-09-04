"""
Endpoint reconciliation for unified categorization (ADR 033).
Ensures every SOURCE reaches at least one SINK with minimal bindings.
"""

import collections
from typing import Dict, List, Tuple, Optional, Set
import networkx as nx

from autocoder_cc.components.component_categorization import Role, infer_effective_role, would_violate_r8
from autocoder_cc.exceptions import ReconciliationError
from autocoder_cc.observability.structured_logging import get_logger
from autocoder_cc.core.config import Settings

logger = get_logger(__name__)
settings = Settings()

# Component type priorities for terminal selection
PRIORITY = {"Store": 0, "Sink": 1, "APIEndpoint": 2}
DEF_API_PENALTY = 0.25


def _shortest_paths_from(G: nx.DiGraph, start: str) -> Dict[str, int]:
    """Compute shortest path distances from start node using BFS."""
    dist = {start: 0}
    dq = collections.deque([start])
    while dq:
        u = dq.popleft()
        for v in G.successors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                dq.append(v)
    return dist


def _multi_source_bfs_undirected(G: nx.DiGraph, sources: Set[str]) -> Dict[str, int]:
    """Compute shortest distances from any source to all nodes (undirected view)."""
    UG = G.to_undirected(as_view=True)
    dist = {}
    dq = collections.deque()
    for s in sources:
        dist[s] = 0
        dq.append(s)
    while dq:
        u = dq.popleft()
        for v in UG.neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                dq.append(v)
    return dist


def _prefer(c_new: str, c_old: str, comp_by_name: Dict[str, dict]) -> bool:
    """Determine if c_new is preferred over c_old based on type priority."""
    t_new = comp_by_name[c_new].get("type")
    t_old = comp_by_name[c_old].get("type")
    p_new = PRIORITY.get(t_new, 9)
    p_old = PRIORITY.get(t_old, 9)
    if p_new != p_old:
        return p_new < p_old
    return c_new < c_old  # stable lexicographic tie-break


def choose_tail_and_candidate(
    G: nx.DiGraph,
    s: str,
    tails: List[str],
    candidates: List[str],
    components_by_name: Dict[str, dict],
    all_sources: List[str],
    use_contention: bool
) -> Optional[Tuple[str, str]]:
    """
    Choose the best tail-candidate pair using cost function.
    
    Cost = d_G(s,f) + d_G^S(c) + λ·1[type(c)=APIEndpoint]
    where:
    - d_G(s,f) = hop distance from source to tail
    - d_G^S(c) = distance from candidate to nearest other source (if use_contention)
    - λ = penalty for APIEndpoint types
    
    Returns:
        (tail, candidate) pair or None if no valid pair exists
    """
    # Precompute distances from source s to all nodes
    d_s = _shortest_paths_from(G, s)
    
    # Compute contention distances if enabled
    if use_contention and len(all_sources) > 1:
        other_sources = set(all_sources) - {s}
        d_S = _multi_source_bfs_undirected(G, other_sources)
    else:
        d_S = None
    
    def api_penalty(n: str) -> float:
        return DEF_API_PENALTY if components_by_name[n].get("type") == "APIEndpoint" else 0.0
    
    def cost(f: str, c: str) -> float:
        d1 = d_s.get(f, float("inf"))
        d2 = (d_S.get(c, float("inf")) if d_S is not None else 0.0)
        return d1 + d2 + api_penalty(c)
    
    best = None
    for f in tails:
        for c in candidates:
            cur = cost(f, c)
            if best is None or cur < best[0] or (cur == best[0] and _prefer(c, best[2], components_by_name)):
                best = (cur, f, c)
    
    return (best[1], best[2]) if best else None


def reconcile_endpoints(
    bindings: List[Dict[str, any]],
    components: List[Dict[str, any]],
    role_views: Dict[str, any],
    G: nx.DiGraph,
    max_corrections: int = 1
) -> List[Dict[str, any]]:
    """
    Add minimal bindings so every SOURCE reaches at least one SINK.
    
    Never removes existing edges; bounded to max_corrections sweeps.
    
    Args:
        bindings: Current list of bindings
        components: List of component dictionaries
        role_views: Map of component name to RoleView
        G: NetworkX directed graph of current bindings
        max_corrections: Maximum correction sweeps (default 1)
        
    Returns:
        Updated bindings list with new reconciliation edges
        
    Raises:
        ReconciliationError: If sources cannot reach sinks within bounds
    """
    name2comp = {c["name"]: c for c in components}
    use_contention = settings.RECONCILIATION_USE_CONTENTION_TERM
    
    for correction_round in range(max_corrections):
        # Identify sources and sinks by effective role
        sinks = {n for n, rv in role_views.items() if rv.effective == Role.SINK}
        sources = [n for n, rv in role_views.items() if rv.effective == Role.SOURCE]
        
        # Find sources that don't reach any sink
        unresolved = []
        for s in sources:
            if not any(nx.has_path(G, s, t) for t in sinks):
                unresolved.append(s)
        
        if not unresolved:
            logger.info("All sources reach sinks - reconciliation complete")
            return bindings
        
        logger.info(f"Reconciliation round {correction_round + 1}: {len(unresolved)} sources need terminal paths")
        
        new_edges = []
        for s in unresolved:
            # Find dangling tails reachable from source
            reachable = nx.descendants(G, s) | {s}
            tails = [n for n in reachable if G.out_degree(n) == 0]
            if not tails:
                tails = [s]
            
            # Find terminal candidates
            candidates = []
            for n in G.nodes():
                comp = name2comp.get(n)
                if not comp:
                    continue
                    
                # Candidate if: no outputs and terminal type, or explicit terminal flag, or effective sink
                if (
                    (not comp.get("outputs") and comp.get("type") in {"Store", "Sink", "APIEndpoint"})
                    or comp.get("terminal") is True
                    or role_views.get(n, {}).effective == Role.SINK
                ):
                    candidates.append(n)
            
            # Choose best tail-candidate pair
            best = choose_tail_and_candidate(
                G, s, tails, candidates, name2comp, sources, use_contention
            )
            
            if best:
                f, c = best
                # Verify edge won't violate R8 for BOTH source and target components
                # Adding edge f → c means:
                # - c gets an incoming edge (no change to c's out_degree)  
                # - f gets an outgoing edge (f's out_degree increases by 1)
                current_out_deg_c = G.out_degree(c)
                new_out_deg_f = G.out_degree(f) + 1
                
                # Check target component won't violate R8
                target_r8_ok = not would_violate_r8(name2comp[c], current_out_deg_c)
                # Check source component won't violate R8 after gaining outgoing edge
                source_r8_ok = not would_violate_r8(name2comp[f], new_out_deg_f)
                
                if target_r8_ok and source_r8_ok:
                    new_edges.append((f, c))
                else:
                    if not target_r8_ok:
                        logger.warning(f"Cannot add edge {f} → {c}: target {c} would violate R8 constraints")
                    if not source_r8_ok:
                        logger.warning(f"Cannot add edge {f} → {c}: source {f} would violate R8 constraints with new outgoing edge")
        
        # Add edges and update local roles
        edges_added = 0
        for u, v in new_edges:
            bindings.append({
                "from": u,
                "to": v,
                "generated_by": "reconciliation_r7",
                "description": f"Reconciliation: ensure {u} reaches terminal"
            })
            G.add_edge(u, v)
            edges_added += 1
            
            # Update role for u (now has out_degree > 0)
            comp = name2comp[u]
            new_in_deg = G.in_degree(u)
            new_out_deg = G.out_degree(u)
            role_views[u] = infer_effective_role(comp, new_in_deg, new_out_deg)
            
            logger.info(f"Added reconciliation edge: {u} → {v}")
        
        logger.info(f"Added {edges_added} reconciliation edges in round {correction_round + 1}")
    
    # Check if any sources still unresolved after max_corrections
    sinks = {n for n, rv in role_views.items() if rv.effective == Role.SINK}
    sources = [n for n, rv in role_views.items() if rv.effective == Role.SOURCE]
    still_unresolved = []
    for s in sources:
        if not any(nx.has_path(G, s, t) for t in sinks):
            still_unresolved.append(s)
    
    if still_unresolved:
        # Suggest edges that could fix the issue
        suggested = []
        for s in still_unresolved:
            reachable = nx.descendants(G, s) | {s}
            tails = [n for n in reachable if G.out_degree(n) == 0]
            if tails and sinks:
                suggested.append(f"{tails[0]} → {list(sinks)[0]}")
        
        raise ReconciliationError(
            f"Cannot satisfy all source→sink paths within {max_corrections} corrections",
            details={
                "unresolved_sources": still_unresolved,
                "suggested_edges": suggested,
                "code": "ADR033-R7-REPLAN-REQUIRED"
            }
        )
    
    return bindings