# START HERE - Complete Context for Port-Based Architecture Switch

*Created: 2025-08-10*
*Purpose: Entry point for any LLM/developer without prior context*

## Quick Summary for New LLMs

You are looking at the planning documents for AutoCoder4_CC's **COMPLETE SWITCH** (not migration) from RPC-based to port-based architecture. Read this document first to understand the context.

## What is AutoCoder4_CC?

An automated code generation system that:
1. Takes natural language descriptions
2. Generates complete software systems using LLMs
3. Uses blueprints to define system architecture
4. Self-heals generated code to achieve 100% deployment success

## Current Problem

- **0% validation success** with real validator (was getting 27.8% with mock validator)
- **Architecture mismatch**: System designed for streams but generates RPC-style code
- **Wrong component types**: Using 13 hardcoded types instead of mathematical primitives

## The Decision (FINAL - NO DEBATE)

We are doing a **FULL SWITCH** to port-based architecture:
- **NOT a migration** - Complete replacement
- **NO backwards compatibility** - Clean break
- **UNLIMITED time** - Quality over speed
- **100% success WITH self-healing** - Not 95%
- **Architectural beauty is priority** - Not quick fixes

## Key Documents to Read (In Order)

### 1. Core Decisions
- **FINAL_STRATEGY_DECISION.md** - The definitive strategy (read first)
- **RESOLVED_UNCERTAINTIES.md** - All technical decisions made

### 2. Architecture Design
- **port_stream_recipe_design.md** - Complete technical specification
- **SELF_HEALING_INTEGRATION_PLAN.md** - How to achieve 100% success

### 3. Implementation Planning
- **TEST_DRIVEN_MIGRATION_PLAN.md** - TDD approach (ignore "migration" in title)
- **README.md** - Overview of the switch plan

### 4. Historical Context (Optional)
- **INCONSISTENCIES_AND_UNCERTAINTIES_FINAL.md** - Shows what was resolved
- Various debate documents - Already resolved, just for history

## Core Architecture Components

### 1. Ports
- **What**: Typed wrappers around anyio streams with Pydantic validation
- **Why**: Type safety and contract enforcement
- **Example**: `OutputPort[TodoItem]` only accepts TodoItem objects

### 2. Five Mathematical Primitives
Instead of 13 hardcoded component types, we use 5 base types:

| Primitive | Inputs | Outputs | Purpose |
|-----------|--------|---------|----------|
| Source | 0 | N | Generate data |
| Sink | N | 0 | Consume data |
| Transformer | 1 | 1 | Transform data |
| Splitter | 1 | N | Distribute data |
| Merger | N | 1 | Combine data |

### 3. Recipes
- **What**: Configuration patterns that make primitives behave like domain types
- **Example**: Store = Transformer + {persistent: true, queryable: true}
- **When**: Applied at compile-time during code generation (NOT runtime)

### 4. Self-Healing
- **Transactional**: Always preserves working state, rollback if worse
- **Bounded**: Max 3 passes per stage
- **Escalating**: Component → AST → Template → Recipe → Blueprint
- **Observable**: Pattern database for debugging ONLY (NO ML/AI)

## Key Technical Decisions (ALL RESOLVED)

1. **Self-Healing**: Transactional with rollback, max 3 passes, escalation chain
2. **Recipes**: Compile-time expansion (not runtime)
3. **Buffers**: 1000 default, backpressure by default
4. **Errors**: Dedicated error collector pattern
5. **Testing**: Keep pytest framework, rewrite all tests

## What NOT to Do

❌ **DO NOT**:
- Suggest backwards compatibility (not needed)
- Propose incremental migration (full switch)
- Add ML/AI to self-healing (explicitly rejected)
- Worry about timelines (unlimited time)
- Compromise on architecture (beauty is priority)
- Keep RPC-style code (complete replacement)
- Use 13 component types (5 primitives only)

## Glossary

- **Port**: Typed interface to a stream with validation
- **Stream**: anyio.MemoryObjectStream for data transport
- **Recipe**: Configuration pattern for primitives
- **Blueprint**: YAML specification of system architecture
- **Self-healing**: Automatic fixing of generated code issues
- **Backpressure**: Blocking sender when buffer is full
- **Component**: A processing unit with ports
- **Primitive**: One of the 5 mathematical base types
- **Switch**: Complete replacement (we don't say "migration")

## Current State vs Target State

### Current (BROKEN)
```python
# RPC-style communication
await self.communicator.send_to_component("store", data)
response = await self.communicator.wait_for_response()

# 13 hardcoded component types
class Store(ComposedComponent): ...
class Controller(ComposedComponent): ...
# ... 11 more types
```

### Target (CORRECT)
```python
# Port-based communication
await self.output_ports["to_store"].send(data)
response = await self.input_ports["from_store"].receive()

# 5 primitives + recipes
class TodoStore(Transformer):  # Generated from Store recipe
    def configure_ports(self):
        self.add_input_port("items", TodoItem)
        self.add_output_port("stored", StoredItem)
```

## Implementation Phases (No Timeline)

1. **Port Infrastructure** - Build typed port system
2. **Mathematical Primitives** - Implement 5 base types
3. **Recipe System** - Configuration patterns
4. **Self-Healing Integration** - Achieve 100%
5. **Generation Pipeline** - New templates
6. **Validation** - Confirm 100% success

## Success Criteria

- **100% deployment success** on basic examples WITH self-healing
- **Clean architecture** with 5 primitives + recipes
- **No RPC code** remaining
- **Full test coverage** with new tests
- **Beautiful, maintainable code**

## Common Confusions to Avoid

1. **"Migration" terminology**: We use "SWITCH" - complete replacement
2. **"95% success"**: Target is 100% WITH self-healing
3. **"Keep 70% of code"**: Old planning, we're doing FULL switch
4. **"15-day timeline"**: We have UNLIMITED time
5. **"Backwards compatibility"**: NOT needed, clean break
6. **"ML for patterns"**: NO - pattern database for observability only

## For Implementation

When you start implementing:
1. Read FINAL_STRATEGY_DECISION.md first
2. Understand the 5 primitives
3. Review the recipe system
4. Focus on architectural beauty
5. Take unlimited time to do it right
6. Self-healing handles imperfection

## Questions This Answers

- **Q: Should we keep any RPC code?** A: No, full switch
- **Q: What about backwards compatibility?** A: Not needed
- **Q: How long do we have?** A: Unlimited time
- **Q: What's the success target?** A: 100% with self-healing
- **Q: Should we use ML for healing?** A: No, observability only
- **Q: Compile or runtime recipes?** A: Compile-time
- **Q: Which error pattern?** A: Error collector
- **Q: Keep existing tests?** A: Keep framework, rewrite tests

---

**Remember**: This is a FULL SWITCH to beautiful architecture with unlimited time. No compromises, no shortcuts, no backwards compatibility. Self-healing ensures 100% success even if initial generation isn't perfect.
