# ADR-2025-07-15  |  Core Clarifications & Direction

Date: **2025-07-15**

## Context
Architecture reviewers flagged several unclear or contradictory areas (schema migrations, capability wiring, security auto-integration, etc.).  The core engineering team provided authoritative answers on 2025-07-15.  This ADR captures those decisions and links open implementation tickets.

## Decisions

| # | Topic | Decision | Follow-up Ticket |
|---|-------|----------|------------------|
| 1 | **Schema/Migration Strategy** | Deprecate `schema_versioning.py`; Blueprint `schema_version` is single source of truth.  Generator emits database schema scripts under `database/`.  Validation gate aborts when the field is missing or versions are skipped. | `#BP-MIG-V1` |
| 2 | **Capability Ordering & Build-lock** | `ComponentRegistry` must verify `build.lock` with cosign and _sort_ the `capabilities` list by `CapabilityTier` before instantiation. | `#CAP-TIER-SORT` |
| 3 | **Mandatory Capabilities** | `ComposedComponent` **must** wire: `SchemaValidator`, `RateLimiter`, `StateCapability`, `RetryHandler`, `CircuitBreaker`, `MetricsCollector`.  Others remain optional. | `#CAP-MANDATORY-5` |
| 4 | **Security Auto-integration (Stage 1)** | Generator auto-wraps every FastAPI route with `@jwt_required` and `@requires_role("default")`.  Secrets pulled from `EnvironmentConfig/SecretsManager`.  Advanced RBAC & rotation in Phase 2. | `#SEC-AUTO-JWT` |
| 5 | **Policy Engine** | Feature kept but gated by `--enforce-policy` CLI flag until full implementation. | `#POLICY-ENGINE-FLAG` |
| 6 | **Concurrency Model** | Adopt helper `start_isolated_server()` that runs Uvicorn in one daemon thread; shutdown guard waits for join.  Future ticket for full async path. | `#CONC-THREAD-WRAP` |
| 7 | **Component Inheritance** | All concrete components now derive from `ComposedComponent`.  Future benchmark may re-introduce two-tier hierarchy. | `#COMP-ONE-BASE` |
| 8 | **EnvironmentConfig ↔ SecretsManager** | Merge: non-secret env vars stay in `EnvironmentConfig`; keys matching `(_KEY|_PASSWORD|_TOKEN)$` are resolved via `SecretsManager`. | `#CFG-SECRETS-MERGE` |
| 9 | **Healer Provenance** | `ast_healer` writes `healer_log.json` beside each patched file; CI fails if stamp missing. | `#HEAL-PROV` |
|10 | **Testing & Mocks** | `pytest` plugin forbids `unittest.mock` / `pytest-mock` unless `# ALLOW_MOCK_JUSTIFICATION:` comment present.  Deterministic stubs allowed. | `#TEST-NO-LAZY-MOCK` |
|11 | **LocalOrchestrator** | Positions as developer-only CLI (`autocoder run-local`).  Not production. | `#CLI-LOCAL-ONLY` |
|12 | **Stub Generators** | Delete skeletal generators; `ComponentGeneratorFactory` raises on unknown types. | `#GEN-PRUNE` |
|13 | **Docs Version Source** | Authoritative version lives in `autocoder/__init__.py::__version__`; Sphinx build checks for mismatch. | `#DOC-VER-SRC` |
|14 | **Observability Scope** | Scope down to baseline Prometheus RED metrics.  Advanced SLO dashboards -> Phase 2. | `#OBS-RED` |
|15 | **Secret Rotation** | Generator emits SealedSecrets manifests only.  Rotation controller deferred to Phase 2. | `#SEC-ROTATE-PH2` |

## Status
Accepted — All future code & documentation must comply.

## Consequences
* Existing docs updated to remove contradictions and flag Phase 2 work.  
* Deprecated files (`schema_versioning.py`) will be removed in `#BP-MIG-V1`.  
* CI pipelines need new checks: cosign verification, mock-usage guard, healer provenance.

--- 