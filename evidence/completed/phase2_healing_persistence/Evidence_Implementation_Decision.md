# Implementation Decision Based on Investigation Evidence

## Investigation Summary

### Task 0: Root Cause Analysis ✅
- **Finding**: Parser restarts from raw YAML each attempt, losing healing transformations
- **Current order**: Heal → Parse → Port Gen → Validate
- **Recommendation**: Stateful healing, not pipeline reordering

### Task 1: Deep Copy Safety ✅
- **Finding**: Deep copy is SAFE and PERFORMANT
- **Performance**: 1.8ms per copy for large blueprints
- **Recommendation**: Use copy.deepcopy() for stateful healing

### Task 2: Healer Idempotency ✅
- **Finding**: Healer is IDEMPOTENT
- **Stable across**: Multiple healings, same instance reuse
- **Note**: Healer modifies input dict in-place, need deep copy before calling

### Task 3: Port Generator Analysis ✅
- **Finding**: Port gen changes ports without updating bindings
- **Best solution**: Preserve ports referenced in bindings (Option C)
- **Current approach**: Implement stateful healing first (simpler)

### Task 4: Architectural Compliance ✅
- **Finding**: Solution aligns with architecture
- **ADR-033**: Store as terminal (HEAL_STORE_AS_SINK=true)
- **Auto-healing**: Applies to system-generated artifacts

## DECISION: Implement Option A - Stateful Healing

### Rationale:
1. **Lowest risk**: Minimal code changes required
2. **Evidence-based**: All tests show it will work
3. **Quick implementation**: ~5 hours vs 8-12 for alternatives
4. **Architecturally sound**: Aligns with all principles
5. **Future-proof**: Doesn't prevent Option B or C later

### Implementation Plan:

1. **Modify** `system_blueprint_parser.py:parse_file()`:
   - Use `working_blueprint` that persists across attempts
   - Deep copy before each healing call
   - Parse from working blueprint, not raw

2. **Ensure** healer idempotency:
   - Already verified as idempotent
   - Just need to check for existing transformations

3. **Test** thoroughly:
   - Persistence test
   - E2E generation test
   - No stubs verification

### Not Implementing (Yet):
- **Pipeline reordering**: More complex, same outcome
- **Smart port generation**: Would prevent issue but 12+ hours

## Next Steps:
1. Implement stateful healing in parser
2. Add transformation existence check in healer
3. Run comprehensive tests
4. Verify system generates without stubs