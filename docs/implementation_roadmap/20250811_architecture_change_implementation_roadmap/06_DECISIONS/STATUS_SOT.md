# STATUS_SOT.md — Single Source of Truth

*Last Updated: 2025-08-23*
*This is the authoritative source for all status information. Any conflicting claims in other documents are obsolete.*

## Week 6 Status - COMPLETED ✅
*Completed: 2025-08-23*
- **Validation & Hardening**: ✅ 100% success rate achieved (target 95%)
- **Import Bug Fix**: ✅ Fixed line 1492 in component_logic_generator.py
- **Component Type Detection**: ✅ Implemented (13 types supported)
- **Schema-Aware Test Generator**: ✅ Implemented
- **Port Connection Validator**: ✅ Implemented
- **Comprehensive Test Suite**: ✅ 7/7 tests passing
- **Validation Dashboard**: ✅ Generated and operational
- **Evidence**: See EVIDENCE_VALIDATION_FIXES.md and VALIDATION_DASHBOARD.md

## Week 5 Status - COMPLETED ✅
*Completed: 2025-08-22*
- **Walking Skeleton**: ✅ All 4 components implemented
- **Message Delivery**: ✅ 100% (1000/1000 messages)
- **SIGTERM Handling**: ✅ Clean shutdown
- **Evidence**: See EVIDENCE_WALKING_SKELETON.md

## Week 3 Status - COMPLETED ✅
*Completed: 2025-08-22*
- **Blueprint Migration Tool**: ✅ Implemented and tested (RPC → Port conversion)
- **Database Connection Layer**: ✅ Implemented with SQLite support
- **Checkpoint Manager**: ✅ Implemented (Save/restore component state)
- **Integration Test**: ✅ All components working together
- **Evidence**: See EVIDENCE_WEEK3.md for full test outputs

## Week 1-2 Status - COMPLETED ✅
*Completed: Before 2025-08-22*
- **Primitives**: ✅ All 5 base classes implemented
- **Recipe System**: ✅ Built (23KB) but ❌ not integrated

## Architecture Primitives
- **Status**: ✅ IMPLEMENTED (Verified 2025-08-23)
- **Location**: `/autocoder_cc/components/primitives/`
- **Files**: base.py, source.py, sink.py, transformer.py, splitter.py, merger.py
- **Evidence**: All 6 files exist, total ~11KB, imports work
- **Decision**: Transformer = 1→{0..1} (may drop with guardrails)
- **Completed**: Week 1-2

## Recipe System
- **Status**: ✅ EXISTS in `/autocoder_cc/recipes/` but ❌ NOT integrated
- **Truth override**: Any claim of "fictional" or "0 lines" is WRONG - it EXISTS
- **Reality Snapshot** (as of 2025-08-23):
  ```bash
  $ wc -l autocoder_cc/recipes/*.py
    349 autocoder_cc/recipes/__init__.py
  10314 autocoder_cc/recipes/expander.py
  12897 autocoder_cc/recipes/registry.py
  23560 total
  ```
- **What exists**:
  - ✅ RecipeExpander class with expand_recipe() method
  - ✅ 13 recipes defined (Store, Controller, APIEndpoint, etc.)
  - ✅ Proper __init__.py with exports
- **What's missing**:
  - ❌ Integration with system_generator.py (~30-50 LOC change)
  - ❌ Templates for recipe-based generation
- **Decision**: Compile-time expansion in v1
- **Next step**: Phase 2 integration with generator

## Test Harness
- **Status**: ✅ MULTIPLE RUNNERS EXIST (needs consolidation)
- **Current**: 
  - RPC-based RealComponentTestRunner exists (28KB)
  - Port-based test runner EXISTS (6KB at `/autocoder_cc/tests/tools/port_test_runner.py`)
  - Component test runner (73KB)
  - Pipeline test runner (4KB)
- **Walking Skeleton**: ✅ E2E test passes with 4-component pipeline (100% success)
- **Issue**: Multiple test runners, unclear which is primary

## Async Framework
- **Decision**: ✅ anyio==4.9.0 (ADR-0001)
- **Version Policy**: CI pin anyio==4.9.0; dev range >=4.9.0,<5.0 (see ADR-0001)
- **Current reality**: ❌ MIXED STATE
  - 713 files still using asyncio (113 in core project)
  - 168 files using anyio
  - Some files import BOTH (undefined behavior)
  - Walking skeleton uses asyncio exclusively
- **Migration approach**: Manual, per-file checklist (see ANYIO_MIGRATION_PLAN.md)
- **NOT**: Mass sed replacement (unsafe)

## System Generator
- **Status**: ✅ Exists but needs modification
- **Size**: 2,199 lines (NOT 104K as some docs claim)
- **Required change**: Add recipe support (~30-50 LOC across import/init/generate)

## Validation Gates
- **Current**: 7 validation-related files exist
- **Decision**: Keep only integration_validation_gate.py (97 lines)
- **Delete**: 6 other validation files after walking skeleton works

## Validation/Metrics
- **Current validation rate**: 0% (NOT 27.8% as docs claim)
- **v1 scope**: Counters + gauges only (NO histograms, NO performance metrics)
- **v2 scope**: Histograms with defined buckets + performance metrics

## PII Masking
- **v1 scope**: Top-level keys only
- **Default denylist**: ["email","password","ssn","phone","token","api_key","secret","credit_card"]
- **v2 scope**: Recursive masking + structured paths

## Checkpointing
- **v1**: SQLite file per system
- **v2 trigger**: See ADR-0002 for Postgres migration criteria

## Timeline
- **Baseline**: 6 weeks including 50% buffer
- **NOT**: Half-day or hours (any doc claiming this is fantasy)
- **Phase exits**: See "Exit Criteria" below

## Git Safety
- **Rollback point**: ✅ Created `rollback-point-20250114`
- **Strategy**: Aggressive changes allowed with git safety net

## Exit Criteria

### Phase 0 – Status Cleanup (Today)
- [x] STATUS_SOT.md exists
- [ ] Linked from START_HERE.md
- [ ] Conflicting claims marked obsolete
- [ ] Dependency versions pinned

### Phase 1 – Foundations (Weeks 1-2)
- ❌ All 14 files migrated from asyncio to anyio (0/713 files migrated)
- ❌ No `asyncio` hits in scan_asyncio.sh (713 files still use asyncio)
- ✅ 5 primitive base classes exist & import successfully
- ✅ Walking skeleton compiles and runs

### Phase 2 – Integration (Weeks 3-4)
- [x] Blueprint migration tool implemented (Week 3) ✅
- [x] Database connection layer with SQLite (Week 3) ✅
- [x] Checkpoint manager implemented (Week 3) ✅
- [ ] Generator emits 2+ recipe-based components
- [ ] Generated files pass ruff+mypy checks
- [ ] E2E test passes at 1k msg/s with p95 < 50ms

### Phase 3 – Hardening (Weeks 5-6)
- [ ] Error envelope on all components
- [ ] Basic metrics wired (counters/gauges)
- [ ] SQLite checkpoints verified under load

## Walking Skeleton Definition

**Status**: ✅ COMPLETED (Week 5)

**Topology**:
- ApiSource (Source) → Validator (Transformer) → Controller (Splitter) → Store (Sink)

**Components**: ✅ All 4 implemented
- `/autocoder_cc/components/walking_skeleton/api_source.py` (3102 bytes)
- `/autocoder_cc/components/walking_skeleton/validator.py` (3923 bytes)
- `/autocoder_cc/components/walking_skeleton/controller.py` (4270 bytes)
- `/autocoder_cc/components/walking_skeleton/store.py` (3796 bytes)

**Acceptance Criteria** ✅ ALL MET:
- ✅ Process 1000 messages total with 0 unintended drops (100% delivery achieved)
- ✅ All messages reach Store component
- ✅ Clean SIGTERM handling
- ✅ SQLite contains expected records
- ✅ errors_total == 0
- Note: Uses asyncio, not anyio (migration pending)

## Merger Fairness (v1)
- **Strategy**: Round-robin with burst cap
- **Burst**: 32 messages/input before switch
- **Age nudge**: Every 512 messages, check oldest
- **NOT**: Complex credit systems (v2)

## Truth Table (Updated 2025-08-23)

| Component | Documented | Exists | Works | Integrated |
|-----------|------------|--------|-------|------------|
| Primitives | ✅ | ✅ | ✅ | ✅ |
| Recipes | ✅ | ✅ | ⚠️ | ❌ |
| Port Test Runner | ✅ | ✅ | ⚠️ | ⚠️ |
| Anyio Migration | ✅ | ❌ | ❌ | ❌ |
| Walking Skeleton | ✅ | ✅ | ✅ | ✅ |
| Validation System | ✅ | ✅ | ✅ | ✅ |

---
*This document is the single source of truth. Check here first before believing any other status claims.*