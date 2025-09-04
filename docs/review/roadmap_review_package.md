# Roadmap Review Package

**Goal**: To provide a clear understanding of the project's development status, current priorities, and future plans to achieve the target architecture.

This document outlines the recommended reading order for an external roadmap review. It begins with the high-level status overview and then details the current and future workstreams.

---

### 0. Roadmap Overview
- **File**: `docs/implementation_roadmap/overview.md`
- **Purpose**: This is the designated overview and the single source of truth for the **current status** of the project. It states which roadmap is active and links to all other relevant planning documents.

### 1. Current Active Roadmap
- **File**: `docs/implementation_roadmap/p0_the_forge.md`
- **Purpose**: Details the tasks in the currently active "P0: The Forge" roadmap, which is the team's top priority.

### 2. Future Workstreams (Guild Roadmaps)
- **Purpose**: These documents outline the detailed plans for subsequent phases of development that will begin after "The Forge" is complete.
- **2.1. Observability**: `docs/implementation_roadmap/guild_observability_and_healing.md`
- **2.2. Resilience**: `docs/implementation_roadmap/guild_resilience_and_messaging.md`
- **2.3. Security**: `docs/implementation_roadmap/guild_security_and_policy.md`

### 3. Historical Context & Process Enforcement
- **3.1. Changelog**: `CHANGELOG.md`
  - **Purpose**: Provides a historical record of what has been delivered in previous versions.
- **3.2. CI Enforcement**: `.github/workflows/docs_validation.yml`
  - **Purpose**: Shows how the architectural principles and documentation standards are automatically enforced through CI, ensuring the documentation stays in sync with the plan. 