# Standardized Project Numbers & Phases

*Date: 2025-08-10*  
*Purpose: Single source of truth for all counts and phase numbers*

## Official Component Type Count

### Current System (To Be Replaced)
- **13 domain-specific component types** (OFFICIAL COUNT)
  1. Store
  2. Controller  
  3. APIEndpoint
  4. Router
  5. Filter
  6. Aggregator
  7. Gateway
  8. Validator
  9. MessageQueue
  10. Transformer
  11. Monitor
  12. Scheduler
  13. Cache

### New System (Target)
- **5 mathematical primitives** (OFFICIAL COUNT)
  1. Source (0→N ports)
  2. Sink (N→0 ports)
  3. Transformer (1→1 ports)
  4. Splitter (1→N ports)
  5. Merger (N→1 ports)

- **13 recipes** that configure the 5 primitives to act like domain types

## Official File Counts

### Files to Replace/Modify
- **~250 files need modification** (OFFICIAL COUNT)
  - 86 files in blueprint_language/
  - 48 files in tests/
  - 28 files in components/
  - 25 files in generators/
  - 15 files in generation/
  - 12 files in validation/
  - 7 files in orchestration/
  - ~30 template files
  
### Total Codebase
- **~450 total files** in autocoder_cc
- **~75% need replacement** (not 30% as originally thought)
- **~25% infrastructure kept** (logging, config, tools)

## Official Implementation Phases

### STANDARD PHASE NUMBERING (Use These)

**Phase 1: Port Infrastructure**
- Create Port, InputPort, OutputPort classes
- Add Pydantic validation
- Wrap anyio streams

**Phase 2: Mathematical Primitives**  
- Implement 5 base component types
- Source, Sink, Transformer, Splitter, Merger
- Each inherits from PortBasedComponent

**Phase 3: Recipe System**
- Define 13 domain recipes
- Compile-time expansion logic
- Recipe to primitive mapping

**Phase 4: Self-Healing Integration**
- Transactional healing with rollback
- 5-level escalation chain
- Pattern database (observability only)

**Phase 5: Generation Pipeline**
- Replace all generators
- New templates for port-based
- Fix import bug (line 1492)

**Phase 6: Validation & Testing**
- Integration testing framework
- 100% success with self-healing
- Complete test coverage

### DEPRECATED NUMBERING (Do Not Use)
- ❌ Phase 0-5 (some docs use this)
- ❌ Phase 1-7 (IMPLEMENTATION_ASSESSMENT uses this)
- ❌ Different phase names/orders

## Success Metrics

### Validation Success Rate
- **Current: 0%** (due to import bug)
- **Target: 100%** with self-healing
- **NOT 95%** (old target, superseded)

### Test Coverage
- **Target: 100%** for port infrastructure
- **Target: 100%** for primitives
- **Target: 90%+** for generated code

## Reference This Document

When writing or updating documentation, always use these official numbers:
- **13 current component types** (not 14)
- **5 mathematical primitives** (not 4 or 6)
- **~250 files to modify** (not 450+)
- **~75% replacement** (not 30%)
- **Phase 1-6** implementation (not 0-5 or 1-7)
- **100% success target** (not 95%)

## Update Required In These Files

The following files need number updates to match:
1. IMPLEMENTATION_ASSESSMENT.md - Has Phase 7, should end at 6
2. IMPLEMENTATION_CHECKLIST.md - Has Phase 7, should end at 6
3. Any reference to "14 types" should be "13 types"
4. Any reference to "450+ files to replace" should be "~250 files to modify"

---

*This is the authoritative source for all project numbers*