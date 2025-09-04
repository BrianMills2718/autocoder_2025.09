# ADR 029: Capability Kernel Enforcement (MVP)

*   **Status**: Accepted
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Review Team
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

The architecture documentation claimed that certain capabilities (SchemaValidator, RateLimiter, MetricsCollector) formed a "non-bypassable" Capability Kernel, but the implementation allowed all capabilities to be disabled through configuration flags. This created a contradiction between architectural principles and operational reality.

Additionally, the system lacked performance guarantees, making it vulnerable to performance degradation without early detection.

## Decision Drivers

*   **Architectural Integrity**: The Capability Kernel must provide foundational guarantees for system correctness and observability
*   **Production Readiness**: MVP must ship with enforceable quality guarantees
*   **Performance Protection**: System must detect and prevent performance regressions
*   **Audit Compliance**: SOC-2/ISO-27001 requirements demand provable security controls
*   **Developer Experience**: Balance between safety and operational flexibility

## Considered Options

### Option 1: Strict Kernel (Always On)
*   Kernel capabilities (SchemaValidator, RateLimiter, MetricsCollector) are **never** bypassable
*   All tuning done through parameters only (e.g., `rate_limit.rate = 1e6` to effectively disable)
*   Zero governance overhead
*   **Pros**: Strongest guarantees, simplest implementation
*   **Cons**: No escape hatch for extreme performance requirements

### Option 2: Audited Bypass (Risk-Ticket Required)
*   Kernel on by default, but `unsafe_ignore_capabilities` list allowed with Jira ticket
*   CI gate validates ticket format and existence
*   Runtime logging of bypass events
*   **Pros**: Maximum flexibility with audit trail
*   **Cons**: ~1 week of governance implementation work

### Option 3: Basic/Advanced Config with Warnings
*   Kernel on by default, simple YAML flag to disable
*   Runtime warning banners, no CI enforcement
*   **Pros**: Minimal implementation overhead
*   **Cons**: Relies on culture rather than enforcement

## Decision Outcome

**Adopt Option 1 (Strict Kernel) for MVP with performance budgets.**

### Implementation Details

1. **Kernel Capabilities (Always On)**:
   *   SchemaValidator (Tier 10) - Data contract enforcement
   *   RateLimiter (Tier 20) - Backpressure and DoS protection  
   *   MetricsCollector (Tier 90) - Observability and monitoring

2. **Performance Budgets**:
   *   Published budgets in `capability_budgets.yaml` with p95 latency and memory limits
   *   CI micro-benchmarks fail builds that exceed budgets
   *   Same numbers feed Prometheus alert rules for runtime monitoring
   *   No automatic bypass - regressions must be fixed or budgets formally updated

3. **Configuration**:
   *   Remove all `*_enabled` flags for kernel capabilities from schema
   *   Kernel capabilities instantiated unconditionally in `ComposedComponent`
   *   Tuning available only through parameters (e.g., `rate_limit.rate`, `schema_validator.strict_mode`)

### Migration Path

*   **MVP**: Ship with strict kernel enforcement
*   **Post-MVP**: Layer Option 2 (audited bypass) as additive feature without breaking changes
*   **Breaking Changes**: None - existing blueprints that disable kernel capabilities will be invalidated, but this is acceptable for MVP

## Consequences

### Positive
*   **Guaranteed Quality**: Every component is always validated, rate-limited, and observable
*   **Simplified Mental Model**: No conditional capability paths to reason about
*   **Audit Compliance**: Clear evidence of mandatory security controls
*   **Performance Protection**: Early detection of regressions prevents production issues

### Negative
*   **Reduced Flexibility**: No escape hatch for extreme performance requirements
*   **Potential Overhead**: Kernel capabilities always consume some resources
*   **Migration Work**: Existing blueprints that disable kernel capabilities need updates

### Risks
*   **Performance Edge Cases**: Some components may genuinely need kernel bypass for extreme performance
*   **Mitigation**: Post-MVP audited bypass mechanism will address this

## Implementation Timeline

*   **Week 1**: Update schema and runtime code to enforce strict kernel
*   **Week 2**: Implement performance budget framework and CI benchmarks
*   **Week 3**: Update documentation and migration guides
*   **Post-MVP**: Implement audited bypass mechanism (Option 2) as additive feature 