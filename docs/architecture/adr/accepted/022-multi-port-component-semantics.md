# ADR 022: Multi-Port Component Semantics

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Component Model Working Group
*   **Supersedes**: Legacy Source/Transformer/Sink model
*   **Superseded by**: N/A

## Context and Problem Statement

A component may have outputs that fit different logical types (e.g., a primary data output and a secondary metrics output). Our current `Source/Transformer/Sink` model is too simple to accurately describe these components, leading to ambiguity.

## Decision Drivers

*   The component type system must accurately reflect the behavior of complex, real-world components.
*   Clarity in component classification is essential for monitoring, dashboard generation, and developer understanding.
*   We need to avoid workarounds like classifying a component as a `Transformer` just because it has both inputs and outputs.

## Considered Options

*   Introduce a new `Hybrid` component type.
*   Introduce a vocabulary for different *port types* (e.g., `data_port`, `control_port`, `metrics_port`).
*   Allow a component to declare multiple types (e.g., `type: [Source, Sink]`).

## Decision Outcome

**APPROVED**: Port-based component model replacing the rigid Source/Transformer/Sink trichotomy:

### Port Descriptors
```yaml
# architecture.yaml
ports:
  data_in:
    type: "data_in"
    schema: "UserData"
    required: true
  data_out:
    type: "data_out" 
    schema: "ProcessedData"
    required: true
  metrics_out:
    type: "metrics_out"
    schema: "ComponentMetrics"
    required: false
```

### Semantic Classes
- **data_in**: Primary input data
- **data_out**: Primary output data  
- **control_in**: Control/configuration input
- **control_out**: Control/status output
- **metrics_out**: Observability metrics
- **error_out**: Error reporting

### Component Role Derivation
Component roles are derived from port topology:
- **Source**: Has `data_out` ports, no `data_in` ports
- **Sink**: Has `data_in` ports, no `data_out` ports
- **Transformer**: Has both `data_in` and `data_out` ports
- **Hybrid**: Has additional semantic port types

### Aggregation and Distribution
```yaml
# blueprint.yaml
bindings:
  - from: "processor.data_out"
    to: "aggregator.data_in"
    policy: "round_robin"  # or "hash", "broadcast"
```

## Consequences

### Positive
- Accurate representation of complex component behavior
- Clear semantic classification of ports
- Flexible component role derivation
- Explicit aggregation/distribution policies

### Negative
- More complex component definitions
- Migration required from legacy model
- Additional schema validation overhead

### Neutral
- Maintains backward compatibility
- Enables future component enhancements
- Provides clear port semantics 