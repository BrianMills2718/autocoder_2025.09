# Resolved Planning Uncertainties

*Created: 2025-08-10*
*Purpose: Document decisions on remaining uncertainties*

## Executive Summary

All major planning uncertainties have been resolved. This document captures the decisions and rationale.

## 1. Self-Healing Boundaries ✅ RESOLVED

### Decision: Transactional Healing with Rollback

```python
class HealingStrategy:
    MAX_PASSES = 3  # Bounded attempts
    
    def heal_with_rollback(self, code):
        checkpoint = code.copy()  # Save state
        
        for pass_num in range(MAX_PASSES):
            healed = apply_patterns(code)
            
            if is_valid(healed):
                return healed  # Success
            elif is_worse(healed, checkpoint):
                # ROLLBACK to checkpoint
                return escalate_to_previous_stage(checkpoint)
            else:
                code = healed  # Progress made
                
        return checkpoint  # Return best version
```

### Escalation Chain
If healing fails at one level, rollback and try:
1. Component-level → AST-level
2. AST-level → Template regeneration
3. Template → Recipe adjustment
4. Recipe → Blueprint modification

### Pattern Database
- **FOR OBSERVABILITY ONLY** - No ML, no automatic learning
- **PURPOSE**: Debugging and understanding failures
- **NOT FOR**: Automatic pattern learning or ML improvements

```python
class PatternDatabase:
    """Simple pattern tracking for observability"""
    def log_pattern(self, error, attempted_fix, success):
        # Just log for human analysis
        self.database.append({
            "timestamp": now(),
            "error": error,
            "fix_attempted": attempted_fix,
            "success": success
        })
    # NO ML, NO AUTOMATIC LEARNING
```

## 2. Recipe Implementation ✅ RESOLVED

### Decision: Compile-Time Expansion

**Recipes expand during code generation, NOT at runtime**

```python
def generate_component(spec):
    if spec.type in RECIPE_LIBRARY:
        recipe = RECIPE_LIBRARY[spec.type]
        # Expand at generation time
        base_code = PRIMITIVES[recipe.base_type]
        return apply_recipe_template(base_code, recipe)
```

**Rationale**:
- Simpler and more predictable
- No runtime overhead
- Generated code is standalone
- Easier to debug (can see actual code)

## 3. Port Buffer Management ✅ RESOLVED

### Decision: Fixed Buffers with Backpressure

```python
# Default configuration
DEFAULT_BUFFER_SIZE = 1000
DEFAULT_STRATEGY = "backpressure"  # Block when full

# Port priorities
BUFFER_POLICIES = {
    "critical": {"size": 1000, "policy": "block"},      # Never lose
    "normal":   {"size": 1000, "policy": "block"},      # Default safe
    "optional": {"size": 100,  "policy": "drop_oldest"} # OK to lose
}
```

**Rationale**:
- Predictable memory usage
- Natural flow control
- Safe by default (no data loss)
- Can tune per port if needed

## 4. Error Port Topology ✅ RESOLVED

### Decision: Dedicated Error Collector

```python
# Every component has error port
class Component:
    def configure_ports(self):
        self.add_output_port("errors", ErrorSchema)

# Single system-wide error collector
class ErrorCollector(Sink):
    def configure_ports(self):
        self.add_input_port("errors", ErrorSchema)
    
    async def consume(self, error):
        # Centralized error handling
        log(error)
        alert_if_critical(error)
        store_for_analysis(error)
```

**Rationale**:
- Single place to monitor all errors
- Simple, clear error flow
- Easy to add monitoring/alerting
- No complex routing logic

## 5. Testing Strategy ✅ RESOLVED

### Decision: Keep Framework, Rewrite Tests

**KEEP**:
- pytest infrastructure
- Test runners
- Coverage tools
- CI/CD integration

**REWRITE**:
- All component tests (for new architecture)
- All integration tests (port-based)
- All validation tests (self-healing aware)

**NEW**:
- Port connection tests
- Buffer overflow tests
- Backpressure tests
- Recipe expansion tests
- Self-healing rollback tests

**Rationale**:
- Test infrastructure is valuable
- Old tests test wrong architecture
- Need fresh tests for ports/recipes
- Ensures tests match new system

## Configuration Summary

These decisions create a coherent system:

1. **Compile-time recipes** → Predictable components
2. **Bounded healing with rollback** → Always improves or preserves
3. **Fixed buffers with backpressure** → Predictable resources
4. **Error collector pattern** → Central monitoring
5. **New tests for new architecture** → Proper validation

## What This Means for Implementation

### Self-Healing
- 3 passes maximum per stage
- Always preserve checkpoints
- Rollback if worse
- Escalate if stuck
- Log patterns for debugging ONLY

### Recipes
- Expand during generation
- No runtime composition
- Clear, debuggable output

### Ports
- 1000 buffer default
- Backpressure by default
- Three priority levels

### Errors
- Every component → error port
- All errors → collector
- Central logging/alerting

### Testing
- pytest stays
- Tests get rewritten
- Focus on port behavior

## NO LONGER UNCERTAIN

All major architectural decisions are now made:
- ✅ How self-healing works (rollback chain)
- ✅ When recipes expand (compile-time)
- ✅ Buffer management (fixed with backpressure)
- ✅ Error handling (collector pattern)
- ✅ Testing approach (keep framework, new tests)

**Ready to proceed with implementation planning.**