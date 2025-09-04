# ADR 021: Performance Safeguards for Hot-Loop Components

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Performance Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

Forcing all components through the full capability chain may introduce unacceptable latency for performance-sensitive components like `StreamProcessor`. The current `no_capabilities()` approach is all-or-nothing.

## Decision Drivers

*   Architectural consistency must be balanced with production performance requirements.
*   There must be a clear, official performance budget for component overhead.
*   A granular mechanism is needed to bypass specific capabilities when necessary.

## Considered Options

*   A global `bypass_capabilities: ['RateLimiter']` key in the blueprint.
*   A code-level decorator to mark methods as "fast-path".
*   Relying solely on developers to implement efficient capabilities.

## Decision Outcome

**APPROVED**: Dual-rail performance enforcement with build-time micro-benchmarks and runtime self-profiling:

### Performance Budget
- **Component Overhead**: ≤ 10 µs per message
- **Capability Chain**: ≤ 5 µs per capability
- **Hot-Loop Components**: ≤ 2 µs total overhead

### Build-Time Enforcement
```yaml
# performance.yaml
budgets:
  component_overhead: 10us
  capability_chain: 5us
  hot_loop: 2us

micro_benchmarks:
  - name: "capability_hook_latency"
    threshold: 5us
  - name: "component_composition_overhead"
    threshold: 10us
```

### Runtime Safeguards
- Self-profiling with Prometheus metrics
- Automatic alerting when budgets exceeded
- Graceful degradation for non-critical capabilities

### Bypass Mechanism
```yaml
# blueprint.yaml
bypass_capabilities:
  - "RateLimiter"  # For hot-loop components
  - "MetricsCollector"  # When performance critical
```

## Consequences

### Positive
- Clear performance expectations for all components
- Build-time detection of performance regressions
- Runtime monitoring and alerting
- Granular capability bypass for hot-loop components

### Negative
- Additional complexity in build pipeline
- Performance testing overhead
- Risk of bypassing important capabilities

### Neutral
- Maintains architectural consistency
- Enables performance optimization
- Provides clear performance budgets 