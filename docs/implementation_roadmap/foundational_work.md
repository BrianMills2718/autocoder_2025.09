# Roadmap: Foundational Work

This initial workstream is the **Tier-0 Priority** for the project. Its mission is to resolve the deep architectural contradictions that violate our core principles of radical explicitness and determinism. This is a **Contradiction Resolution** phase.

---

## Phase 1: Foundational Hardening

*   **Goal**: To ship a "Hello, World" v1.0 slice with a hardened, internally consistent core.
*   **Definition of Done**:
    *   `./scripts/e2e.sh` passes, demonstrating an end-to-end, three-component pipeline that is versioned, signed, and observable.
    *   The build artifact is verifiably reproducible from a "frozen" blueprint.
    *   Authentication uses public-key cryptography (RS256+JWKS).
    *   Deployment uses cluster-native service discovery, not hash-based port allocation.
    *   Core capabilities (`MetricsCollector`, etc.) are non-bypassable by default.
    *   A watchdog sidecar is running and observable.
    *   The build process is strict by default.
    *   All LLM outputs for a frozen build are version-controlled.

### P0 Tasks (To be completed in Phase 1)

1.  **Unify Component Model & Schemas**: Complete the unification of the `ComposedComponent` model and the removal of the legacy schema system.
2.  **Implement True Determinism via "Freeze" Step**:
    *   **Task**:
        1.  The `CapabilityTier` execution order will be calculated and stored in `build.lock`. The runtime will read this order exclusively.
        2.  All LLM outputs (generated code snippets, validation rationales) for a frozen build will be version-controlled.
        3.  A CI "freeze" job will re-run generation with `temperature = 0` and commit these artifacts.
    *   **Acceptance**: Running the e2e script twice on the same frozen blueprint produces an identical `ir.v1.json` hash and uses the committed LLM outputs.
3.  **Resolve Capability Opt-Out Policy**:
    *   **Status**: ADR-029 **APPROVED** - ComponentRegistry-based kernel enforcement
    *   **Task**: Implement the approved kernel enforcement. Define a minimal, mandatory "capability kernel" that cannot be bypassed. The ComponentRegistry validates that all components include the mandatory kernel capabilities.
    *   **Acceptance**: Attempting to generate a component that bypasses a kernel capability fails CI.
4.  **Front-load RS256 + JWKS Authentication**:
    *   **Task**: Implement JWT auth using RS256 and a `/jwks.json` endpoint. This includes the design and implementation of a key rotation mechanism. (Ticket #312)
    *   **Acceptance**: Integration tests validate JWTs using only the JWKS endpoint.
5.  **Replace Port Hashing with Service Discovery**:
    *   **Task**: Refactor the generator to use cluster-native service discovery (e.g., Kubernetes service names) and delete the hash-based port allocation logic.
    *   **Acceptance**: Two instances of the "Hello, World" slice can be deployed to the same cluster without port conflicts.
6.  **Ship Watchdog Sidecar**:
    *   **Task**: Implement and attach a lightweight, out-of-band watchdog exporter sidecar. This sidecar must be capable of triggering a hard kill if the main process becomes unresponsive.
    *   **Acceptance**: After killing a component's main process, the watchdog sidecar continues to expose a metric (`up == 0`) within 5 seconds.
7.  **Enforce Strict Validation by Default**:
    *   **Task**: Change the system default to `validation.strict_mode = true`. Add a `--allow-warnings` flag for local, exploratory builds.
    *   **Acceptance**: A build with warnings fails CI by default.

---

## Phase 2: Core Contracts

*   **Goal**: To finalize the core developer contracts for capabilities and the blueprint language.
*   **Definition of Done**:
    *   Capability hook signatures are frozen.
    *   The blueprint parser has a firm deprecation plan for legacy syntax.

### P0 Tasks (To be completed in Phase 2)

1.  **Implement Capability Hook Contract**:
    *   **Status**: ADR-019 **APPROVED** - Typed, async-first, three-phase hook interface
    *   **Task**: Implement the approved capability hook contract with `before_process`, `around_process`, `after_process` methods.
    *   **Tweak**: Add static and runtime asserts to enforce `CapabilityTier` ordering.

2.  **Implement LLM Provider Abstraction**:
    *   **Status**: ADR-027 **APPROVED** - Remote-only MVP with thin SPI
    *   **Task**: Build the thin provider SPI with entry point registration and one concrete provider (OpenAI).
    *   **Acceptance**: Components can access LLMs through the ProviderManager capability.

3.  **Implement Performance Budget Framework**:
    *   **Status**: ADR-030 **APPROVED** - Static budgets with build-time enforcement
    *   **Task**: Create capability_budgets.yaml, benchmark harness, and CI enforcement step.
    *   **Acceptance**: PRs fail if capability performance regresses beyond 10% threshold.
2.  **Set Hard Deprecation for Legacy Bindings**:
    *   **Task**: Set a hard deadline of `2025-12-31` for legacy dot-notation bindings. Scaffold and complete the `autocoder migrate-bindings` CLI. **Remove the legacy parser entirely.**
    *   **Acceptance**: A blueprint using legacy syntax fails validation on 2026-01-01.
3.  **Make Security Decorators Opt-In**:
    *   **Task**: Remove all implicit JWT-wrapping behavior. Require an explicit `authentication: jwt` block in the blueprint for any route that requires protection.
    *   **Acceptance**: The generator fails if a protected route is defined without the explicit `authentication` block. 