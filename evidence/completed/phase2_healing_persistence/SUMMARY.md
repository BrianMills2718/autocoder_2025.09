# Healing Persistence Fix - Implementation Summary

## Root Cause Identified

The blueprint healing persistence issue had TWO root causes:

### Root Cause 1: Parser Restarting from Raw YAML ✅ FIXED
- **Problem**: The parser was restarting from `raw_blueprint` on each attempt, losing all healing transformations
- **Solution**: Modified `system_blueprint_parser.py` to use `working_blueprint` that persists across attempts
- **Evidence**: Changes implemented in lines 337-372 of `system_blueprint_parser.py`

### Root Cause 2: Healing Cannot Detect Schema Mismatches Before Port Generation
- **Problem**: The healer's `_heal_schema_compatibility` method requires ports to be defined on components to detect schema mismatches
- **Current Flow**: Heal → Parse → Port Gen → Validate
- **Issue**: Store components don't have inputs defined until AFTER port generation runs
- **Evidence**: `evidence/current/healing_debug.md` shows healer cannot detect mismatch when Store has no inputs

## Implementation Completed

### 1. Stateful Healing Implementation ✅
Modified `autocoder_cc/blueprint_language/system_blueprint_parser.py`:
- Uses `working_blueprint` that persists across attempts
- Deep copies before passing to healer (healer modifies in-place)
- Syncs port changes back via `_update_working_blueprint_from_parsed`

### 2. Supporting Fixes ✅
- Fixed duplicate binding detection in healer (lines 352-365)
- Fixed Store port template to use 'input' instead of 'store' (line 90-98 of port_auto_generator.py)
- Added proper deep copying to prevent state corruption

## Evidence Files Created
1. `evidence/current/ROOT_CAUSE_FOUND.md` - Initial discovery of parser restart issue
2. `evidence/current/healing_persistence_test.md` - Test showing healer doesn't detect schema mismatch
3. `evidence/current/healing_debug.md` - Debug output showing Store has no inputs before port generation
4. `evidence/current/schema_healing_debug.md` - Earlier test showing healing works when ports exist

## Architectural Decision

The fix implements **Option A: Stateful Healing** from the investigation:
- Maintains `working_blueprint` across attempts
- Preserves healing transformations between iterations
- Uses deep copy to prevent corruption
- Syncs port changes back to working blueprint

This aligns with:
- **ADR-031**: Two-layer fail-hard architecture (parser fails hard on errors)
- **ADR-033**: Store/Sink topology categorization
- **Core Principle**: Fail-fast with clear errors rather than silently dropping transformations

## Outstanding Issue

### Schema Mismatch Detection Timing
**Problem**: Healer cannot detect schema mismatches until AFTER port generation
**Options**:
1. Run port generation BEFORE healing (changes pipeline order)
2. Have healer infer expected ports based on component types
3. Add a second healing pass after port generation

**Recommendation**: Option 3 - Add second healing pass after port generation to catch schema mismatches that weren't visible initially.

## Test Results
- Parser persistence fix: ✅ Implemented and verified
- Schema healing when ports exist: ✅ Works (see schema_healing_debug.md)
- Schema healing before ports exist: ❌ Cannot work (fundamental limitation)
- End-to-end system generation: ⚠️ Interrupted by LLM API failure (unrelated issue)

## Next Steps
1. Add second healing pass after port generation
2. Create integration test that verifies full pipeline with healing persistence
3. Document the two-phase healing approach in architecture docs