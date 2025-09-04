# Architectural Decision: Enhanced 4-Step Healing with Conflict Detection

**Date**: 2025-08-30  
**Status**: Revised  
**Context**: Configuration validation and healing strategy for AutoCoder4_CC
**Previous Decision**: LLM-first approach (2025-08-29)

## Revised Decision

We will **keep the existing 4-step healing strategy** (Default → Example → Context → LLM) but **enhance it with resource conflict detection** to prevent issues like port conflicts.

## Background

### Current Implementation (Keeping)
The system uses a 4-step healing strategy:
1. Try default values
2. Try example values
3. Try context-based copying
4. Fall back to LLM generation

### Identified Problems
- **Port conflicts**: Multiple components might use default port 8080
- **Resource conflicts**: Database URLs, file paths could collide
- **Context blindness**: Non-LLM strategies don't check for conflicts

### Why Not LLM-First?
Investigation revealed the current approach is actually sophisticated:
- Efficient (uses fast strategies when possible)
- Cost-effective (only calls LLM when necessary)
- Still gets LLM intelligence for complex cases
- Already validates after healing and retries with LLM if needed

## Enhanced Approach: Conflict-Aware 4-Step Healing

### Strategy
Keep the existing 4-step approach but enhance it:
1. **Extract used resources** during context building
2. **Check for conflicts** in DefaultValueStrategy
3. **Check for conflicts** in ExampleBasedStrategy
4. **Pass resource context** to LLM when fallback occurs
5. **Let natural fallback** handle conflicts elegantly

### Implementation
- Add `used_resources` to PipelineContext
- Modify strategies to check conflicts before returning values
- Return None from strategy if conflict detected (triggers next strategy)
- LLM naturally handles complex cases with full context

### Benefits of Enhanced Approach
- **Best of both worlds**: Fast defaults when safe, intelligent LLM when needed
- **Automatic conflict resolution**: Strategies skip conflicting values
- **Minimal changes**: Enhances existing system rather than replacing it
- **Natural fallback**: System already designed to escalate to LLM
- **Cost-effective**: Still minimizes LLM calls

### Implementation Advantages
- **Less disruptive**: Small, focused changes
- **Already tested**: Core healing logic proven to work
- **Maintains efficiency**: Fast strategies still used when appropriate
- **Progressive enhancement**: Can add more conflict types over time

## Implementation Details

### Context Building
```python
healing_context = {
    "component_name": "api_gateway",
    "component_type": "APIEndpoint",
    "validation_errors": [...],
    "full_blueprint": {...},
    "used_resources": {
        "ports": [8080, 8081, 3000],
        "databases": ["postgresql://localhost/main"],
        "file_paths": ["/data/input.csv"]
    },
    "component_relationships": {
        "upstream": ["auth_service"],
        "downstream": ["database_store", "cache"]
    }
}
```

### LLM Prompt Structure
```
You are configuring component 'api_gateway' of type 'APIEndpoint'.

Current validation errors:
- Missing required field 'port'
- Missing required field 'base_path'

System context:
- Ports already in use: 8080, 8081, 3000
- This component receives data from: auth_service
- This component sends data to: database_store, cache

Generate a valid configuration that:
1. Fixes all validation errors
2. Avoids resource conflicts
3. Integrates properly with connected components
```

## Consequences

### Positive
- **Higher success rate**: Intelligent healing handles complex scenarios
- **No resource conflicts**: LLM ensures uniqueness
- **Better integration**: Components configured with awareness of each other
- **Maintainable**: Single code path easier than complex fallback chain

### Negative
- **Testing complexity**: Non-deterministic outputs harder to test
- **Debug challenges**: Different outputs for same input
- **LLM dependency**: System requires LLM availability

### Mitigations
- **Test outcomes, not values**: Verify configs are valid, not specific
- **Comprehensive logging**: Log full context and LLM decisions
- **Fallback to error**: If LLM unavailable, fail with clear message

## Decision Rationale

Given the project priorities:
- **Robustness** > Determinism
- **Quality** > Speed  
- **Flexibility** > Simplicity
- **LLM costs/time** explicitly not a concern

The LLM-first approach aligns perfectly with these priorities.

## References
- SYSTEMATIC_OVERHAUL_PLAN_V3.md (updated to reflect this decision)
- Original discussion: Phase 4 planning review
- Stakeholder input: "I don't care about the number of LLM calls or time, I just want robustness and quality"