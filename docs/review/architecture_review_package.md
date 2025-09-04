# Architecture Review Package

**Goal**: To provide a complete and logical understanding of the system's target state, principles, and contracts.

This document outlines the recommended reading order for an external architectural review. It begins with the highest-level overview and progressively drills down into the specific implementations and decision records.

---

### 0. Core Architecture Document
- **File**: `docs/reference/AUTOCODER4_CC_CORE_ARCHITECTURE.md`
- **Purpose**: This is the designated overview and the single source of truth for the target architecture. It provides the "10,000-foot view" and serves as the primary reference for all architectural concepts.

### 1. Vocabulary
- **File**: `docs/dev/vocabulary.md`
- **Purpose**: Defines the precise meaning of all key architectural terms, ensuring a common understanding for all subsequent documents.

### 2. The Component Model: Deep Dive
- **2.1. Detailed Model**: `docs/reference/architecture/component-model.md`
  - **Purpose**: A detailed breakdown of the `ComposedComponent` base class, the capability system, and the port-based semantics.
- **2.2. Decision Record**: `docs/reference/architecture/aggregate_architecture_adr_031_component_semantics.md`
  - **Purpose**: The complete decision record for **ADR-031**. This is essential for understanding the *why* behind the recent evolution to a port-based model.

### 3. Supporting Frameworks
- **3.1. Validation**: `docs/reference/architecture/validation-framework.md`
  - **Purpose**: Explains the critical cross-cutting concern of system validation and the "Graded Failure Policy."
- **3.2. Security**: `docs/reference/architecture/security-framework.md`
  - **Purpose**: Outlines the system's approach to security.

### 4. Implementation & Enforcement
- **4.1. Schema Contract**: `schemas/architecture.schema.json`
  - **Purpose**: The formal, machine-readable contract (JSON Schema) that enforces the architectural rules on all blueprints.
- **4.2. Base Class**: `autocoder_cc/components/composed_base.py`
  - **Purpose**: The source code for the fundamental component building block.
- **4.3. Gatekeeper**: `autocoder_cc/components/component_registry.py`
  - **Purpose**: The source code for the architectural "gatekeeper" that validates and instantiates components.

### 5. Developer Experience & Migration
- **5.1. Project Entrypoint**: `autocoder_cc/README.md`
  - **Purpose**: The main project README, showing how a developer first interacts with the system.
- **5.2. Migration Guide**: `docs/migrations/2025-07-adr-031-port-model.md`
  - **Purpose**: A practical guide for migrating from the old component model to the new one, making the architectural change concrete. 