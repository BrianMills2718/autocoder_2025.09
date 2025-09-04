# ADR 033: Store vs Sink — Unified Categorization with Guarded Stop-Gap

**Date:** 2025-07-25  
**Status:** ✅ **APPROVED** (implement)  
**Impact:** **HIGH** — touches healer, validator, schema, tests  
**Complexity:** **MEDIUM** — moderate refactor, high verification  
**Drivers:** 25 blueprints rely on Store≠Sink; no CDC Stores today; permissive healing posture; strict perf and quality guardrails.

---

## 1. Context

Two subsystems disagree on what constitutes a terminal component (**terminal component** *(a node at which dataflow paths end; no further business outputs)*):

* **BlueprintHealer** is **type-based** *(classifies by declared type string)* and excludes `Store` from `Sink` when generating bindings.
* **ArchitecturalValidator** is **topology-based** *(classifies by graph degrees: in/out edge counts)* and declares any node with `out_degree==0` (**out_degree** *(number of outgoing edges from a node in the graph)*) a sink.

This mismatch deadlocks self-healing on common patterns such as `Source → Transformer → Store` because the healer will not target `Store`, then the validator marks everything orphaned (**orphaned** *(a node with neither valid inbound nor outbound bindings in the final graph)*).

Facts (2025-07-25):

* **25** blueprints contain both `Store` and `Sink` and rely on the distinction.
* **0%** of `Store` components have outputs today (no CDC).
* Schema can accept new boolean `terminal` (removed `emits` per simplification).
* Failure posture: **heal permissively** *(attempt repair, warn if ambiguous)*.
* Perf budget: **+10% or ≤3s**, alert if >5s.
* Rollout guard: auto-disable if validation pass rate drops **>5%** from baseline.
* User surfaces: **CLI + logs** (no UI warnings).

---

## 2. Decision

**Adopt a unified, topology-first categorization with a guarded stop-gap.**

### 2.1 Normative Policy

We replace type-based categorization with **topology-first inference** *(decide by ports/edges first, then metadata, then type)*.

**R1 — Outputs imply emission.** If `outputs` is non-empty, set `effective_role=TRANSFORMER` *(a component that forwards/produces data)*.

**R2 — Edge-confirmed emission.** If `out_degree > 0`, set `effective_role=TRANSFORMER`.

**R3 — Terminal default when inert.** If `outputs == []` **and** `out_degree == 0`, set `effective_role = SINK` *(a terminal component where dataflow ends)*.

**R4 — Explicit terminal (guarded).** `terminal:true` is allowed **only if** `out_degree == 0`. If violated, raise a **hard lint** *(an error that stops the run)*.

**R5 — Type prior (tie-breaker).** When R1–R4 do not decide, use type as a prior: `Store`/`Sink`/`APIEndpoint` bias to `SINK`; `Transformer`/`Model`/`StreamProcessor` bias to `TRANSFORMER`; `Source` bias to `SOURCE`.

**R7 — Bounded reconciliation.** After initial binding, run **one** reconciliation sweep to:
* ensure every `SOURCE` reaches some `SINK`, and
* flip any node misclassified by new edges (e.g., predicted `SINK` but now `out_degree>0`).

**R8 — Hard contradictions error out.**
* `terminal:true` with `out_degree>0` → **ERROR**.
* `outputs != []` with `terminal:true` → **ERROR**.

**R9 — Binding provenance.** Every binding carries `generated_by: user|healer_initial|reconciliation_r7` for debugging and telemetry.

### 2.2 Stop-Gap Strategy

Enable `heal.store_as_sink=true` immediately to treat `Store` as eligible terminal in the healer. Roll out unified categorization under `categorization.unified=true` with guards. During stop-gap:
- **Run role inference** for diagnostics and linting
- **Do not alter binding selection** based on inference
- **Suppress role delta warnings in CLI** (show only in logs with `stopgap_role_delta=true`)

---

## 3. Alternatives Considered

* **Option 1 — Treat Store as Sink in healer only.** Minimal, but preserves inconsistency; acceptable as emergency guard only.
* **Option 2 — Validator special-cases Store.** Inverts the inconsistency; risks masking real topology errors.
* **Option 4 — Smarter healer heuristics.** Helps binding coverage but still diverges from validator semantics.

Option 3 (unified categorization) uniquely eliminates the semantic split while remaining future-proof.

---

## 4. Implementation

### 4.1 Schema Changes

Remove `emits` field. Keep optional `terminal` only:

```yaml
components:
  - name: data_store
    type: Store
    terminal: true   # optional explicit terminal intent; must have no outgoing edges
```

Validation:
* `terminal:true` is valid only when `out_degree==0` and `outputs==[]`.
* Any contradiction is a hard error (R8).

### 4.2 New Module: `component_categorization.py`

```python
from enum import Enum, auto
from dataclasses import dataclass

class Role(Enum):
    SOURCE = auto()
    TRANSFORMER = auto()
    SINK = auto()  # terminal

@dataclass
class RoleView:
    declared: Role
    effective: Role
    reasons: list[str]

TYPE_PRIOR = {
    "Source": Role.SOURCE,
    "Transformer": Role.TRANSFORMER,
    "Sink": Role.SINK,
    "Store": Role.SINK,          # prior only; topology can override
    "APIEndpoint": Role.SINK,    # prior only
}

def declared_role(t: str) -> Role:
    return TYPE_PRIOR.get(t, Role.TRANSFORMER)

def infer_effective_role(comp: dict, in_deg: int, out_deg: int) -> RoleView:
    decl = declared_role(comp.get("type"))
    reasons = [f"declared={decl.name}"]

    # R1: outputs imply emission
    if comp.get("outputs"):
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
    eff = decl if decl != Role.SOURCE else Role.TRANSFORMER
    return RoleView(decl, eff, reasons + ["type prior fallback (R5)"])
```

### 4.3 Healer Changes (`blueprint_healer.py`)

Stop-gap (behind `heal.store_as_sink`):

```python
if flags.heal.store_as_sink:
    sinks = [c for c in components if c.get("type") in {"Sink", "Store"}]
else:
    sinks = [c for c in components if c.get("type") == "Sink"]
```

Unified path (behind `categorization.unified`):

```python
# Pass A: generate provisional bindings using type priors
bindings = generate_initial_bindings(components)
for binding in bindings:
    binding["generated_by"] = "healer_initial"

# Pass B: reconcile roles after graph construction
G = build_graph(components, bindings)
role_views = {
    comp["name"]: infer_effective_role(
        comp, G.in_degree(comp["name"]), G.out_degree(comp["name"])
    )
    for comp in components
}

# Bounded reconciliation to ensure SOURCE→SINK paths
bindings = reconcile_endpoints(bindings, components, role_views, G, max_corrections=1)

# Diagnostics (suppressed in CLI during stop-gap)
if not flags.heal.store_as_sink or flags.show_deltas_in_stopgap:
    diagnose_role_deltas(role_views, echo=cli.echo)
```

### 4.4 Validator Changes (`architectural_validator.py`)

```python
def _validate_data_flow(self, components, bindings):
    G = build_graph(components, bindings)
    
    # R8: Hard lints first
    self._lint_contradictions(components, G)
    
    # Infer effective roles
    role_views = {
        c["name"]: infer_effective_role(c, G.in_degree(c["name"]), G.out_degree(c["name"]))
        for c in components
    }
    
    # Validate using effective roles
    sinks = {n for n, rv in role_views.items() if rv.effective == Role.SINK}
    sources = {n for n, rv in role_views.items() if rv.effective == Role.SOURCE}
    
    if not sources:
        raise ValidationError("No sources found after role inference")
    if not sinks:
        raise ValidationError("No terminal components (SINK) found after role inference")
    
    # Ensure every source reaches a sink
    unreachable = []
    for s in sources:
        if not any(nx.has_path(G, s, t) for t in sinks):
            unreachable.append(s)
    
    if unreachable:
        raise ValidationError(
            f"{len(unreachable)} source(s) lack a terminal path",
            details=unreachable,
            code="ADR033-R7-NO-SINK-PATH"
        )
```

### 4.5 Reconciliation Algorithm

```python
def reconcile_endpoints(bindings, components, role_views, G, max_corrections=1):
    """Add minimal bindings so every SOURCE reaches at least one SINK."""
    
    name2comp = {c["name"]: c for c in components}
    use_contention = flags.reconciliation.use_contention_term
    
    for correction_round in range(max_corrections):
        sinks = {n for n, rv in role_views.items() if rv.effective == Role.SINK}
        sources = [n for n, rv in role_views.items() if rv.effective == Role.SOURCE]
        unresolved = [s for s in sources if not any(nx.has_path(G, s, t) for t in sinks)]
        
        if not unresolved:
            return bindings  # All sources reach sinks
        
        new_edges = []
        for s in unresolved:
            # Find dangling tails reachable from source
            tails = [n for n in nx.descendants(G, s) | {s} if G.out_degree(n) == 0]
            if not tails:
                tails = [s]
            
            # Find terminal candidates
            candidates = [
                n for n in G.nodes()
                if (
                    (not name2comp[n].get("outputs") and
                     name2comp[n].get("type") in {"Store", "Sink", "APIEndpoint"})
                    or name2comp[n].get("terminal") is True
                    or role_views[n].effective == Role.SINK
                )
            ]
            
            # Choose best tail-candidate pair
            best = choose_tail_and_candidate(
                G, s, tails, candidates, name2comp, sources, use_contention
            )
            
            if best:
                f, c = best
                # Verify edge won't violate R8
                if not would_violate_r8(name2comp[c], G.out_degree(c) + 1):
                    new_edges.append((f, c))
        
        # Add edges and update local roles
        for u, v in new_edges:
            bindings.append({
                "from": u,
                "to": v,
                "generated_by": "reconciliation_r7"
            })
            G.add_edge(u, v)
            
            # Update role for u (now has out_degree > 0)
            comp = name2comp[u]
            role_views[u] = infer_effective_role(
                comp, G.in_degree(u), G.out_degree(u)
            )
    
    # If still unresolved after max_corrections
    if unresolved:
        raise ReconciliationError(
            "Cannot satisfy all source→sink paths within bounded corrections",
            code="ADR033-R7-REPLAN-REQUIRED",
            sources=unresolved,
            suggested_edges=suggest_edges(G, unresolved, candidates)
        )
    
    return bindings
```

### 4.6 CLI Messaging

Stop-gap mode (default):
- **CLI**: Show only hard lints (R8) and reachability failures
- **Logs**: All role deltas at INFO level with `stopgap_role_delta=true`

Unified mode or with `--show-deltas-in-stopgap`:
```
⚠️ Role reconciliation changed 2 components. Run with --verbose for details.
```

Verbose:
```
- data_store: declared=SINK → effective=SINK (out_degree==0)
- data_api: declared=SINK → effective=TRANSFORMER (outputs present)
```

---

## 5. Testing

### 5.1 Test Matrix

| Test | Scenario | Expected Result |
|------|----------|-----------------|
| A | Source → Store (direct) | Store is SINK, binding created |
| B | Source → Transformer → Store | Store is SINK, path validated |
| C | Source → Transformer → Sink | Standard flow works |
| D | APIEndpoint → Store | Both can be terminals |
| E | Controller → Store → Sink | Store is TRANSFORMER (has output) |
| F | Multiple Sources → Single Store | All sources reach store |
| G | Single Source → Multiple Stores | Source reaches all stores |
| H | Circular dependencies | Detected and reported |
| I | Orphaned components | Validation fails |
| J | Components with no ports | Type prior applies |
| K | Store with outputs | effective=TRANSFORMER |
| L | APIEndpoint with outputs | effective=TRANSFORMER |
| M | Router with dead-letter only | Terminal if out_degree==0 |
| N | terminal:true with outputs | ERROR (ADR033-R8-TERM-OUTPUTS) |
| O | terminal:true with out_degree>0 | ERROR (ADR033-R8-TERM-OUTDEG) |
| P | Reconciliation succeeds | Edge added with provenance |
| Q | Reconciliation fails | ADR033-R7-REPLAN-REQUIRED |
| R | Cost prefers nearer tail | Validated by test |
| S | Store preferred over APIEndpoint | Type priority works |

### 5.2 Property Tests

1. **Invariant**: After healing, every SOURCE has a path to at least one SINK
2. **Determinism**: Same blueprint always produces same bindings (given same flags)
3. **Provenance**: Every binding has valid `generated_by` field
4. **No oscillation**: Reconciliation converges in ≤1 correction

---

## 6. Rollout Plan

### 6.1 Phases

1. **Phase 0** (2025-07-25): Land stop-gap
   - `heal.store_as_sink=true` (default)
   - `categorization.unified=false` (default)
   
2. **Phase 1**: Deploy unified module (off by default)
   - Test in staging with both flags on
   
3. **Phase 2**: Regression test
   - Run 25 dual Store/Sink blueprints
   - Record baseline metrics
   
4. **Phase 3**: Canary rollout
   - 10% traffic with `categorization.unified=true`
   - Monitor metrics closely
   
5. **Phase 4**: Full rollout
   - 100% unified categorization
   - Keep stop-gap as safety valve
   
6. **Phase 5**: Cleanup
   - Remove stop-gap after 2 stable releases

### 6.2 Guardrails

**Validation Pass Rate**:
- Auto-disable if rate drops >5% over 60-minute rolling window (3 consecutive)
- Immediate rollback if >10% drop in any 15-minute window

**Performance**:
- Alert if p95 latency increases >5s or >10% for 2 consecutive 15-minute windows
- Auto-disable if sustained for 60 minutes

**Telemetry**:
```
cc_roles_flips_total{declared, effective}
cc_roles_fallback_hits_total
cc_reconciliation_edges_added_total{contention="on|off"}
cc_reconciliation_sources_fixed_total{contention="on|off"}
cc_heal_reconciliations_total
cc_validation_pass_rate
cc_generation_duration_seconds{p50,p95}
cc_lints_total{code, severity}
```

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Silent emission via stray binding | Component unexpectedly emits data | R2 forces TRANSFORMER role; validator ensures sink path exists |
| User confusion about terminal flag | Broken blueprints | R8 hard errors with clear messages |
| Performance regression | Slow generation | Bounded reconciliation; performance guards |
| Backward compatibility | Existing blueprints fail | Feature flags; gradual rollout; telemetry |

---

## 8. Decision Log

| Date | Decision | Rationale | Approver |
|------|----------|-----------|----------|
| 2025-07-25 | Adopt unified categorization with stop-gap | Resolves architectural mismatch; unblocks users | TBD |

---

## 9. References

- `/autocoder_cc/healing/blueprint_healer.py` - Binding generation logic
- `/autocoder_cc/blueprint_language/architectural_validator.py` - Validation logic
- `/autocoder_cc/components/component_registry.py` - Component type definitions
- `test_validation_edge_cases.py` - Edge case tests
- ADR 031: Component Semantics - Component type definitions
- DECISION_STORE_VS_SINK_CATEGORIZATION.md - Initial analysis
- DECISION_CLARIFYING_ANSWERS.md - Requirements data