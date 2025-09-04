## [5.2.1] – 2025-07-14
### Added
* **Documentation** – clarified generation-phase fail-hard vs runtime graceful-degradation.
* **Mandatory capability list** – SchemaValidator, RateLimiter, StateCapability, RetryHandler, CircuitBreaker, MetricsCollector.
### Changed
* Contributor Guide – recommends `CapabilityRegistry.get_capability_set()` for constructor wiring. 

## [5.3.0] – 2025-07-15
### Added
* **Typed IR Escape Hatch** – behind feature flags. Emits `generated/ir.<ver>.json` and validates against `schemas/typed_ir_v0_3.schema.json`.
* Feature flags: `EMIT_TYPED_IR`, `USE_TYPED_IR`, `CI_BLOCK_ON_IR`, `STRICT_IR` (defaults off).
* New helper `autocoder.ir.builder.build_ir` and CLI validator `tools/validate_ir.py`.
### Changed
* Generation pipeline optionally emits IR and performs non-blocking validation (Phase 0.5).
* Core configuration extended with IR flags.
### Experimental
* IR compiler path will arrive in Phase 2 – enabling `USE_TYPED_IR` currently raises `NotImplementedError`. 

## [Unreleased]

### Added
* **ADR-031 Port-Based Component Model GA** – Replaces Source/Transformer/Sink type system with explicit port semantics. Documentation, schema, CI lints, and migration guide added. 