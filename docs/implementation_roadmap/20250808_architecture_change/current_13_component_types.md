# Current 13+ Component Types in AutoCoder4_CC

*Generated: 2025-08-10*
*Purpose: Document all existing component types before migration to 5-type system*

## The Current Component Types (Actually 18+, not 13)

Based on analysis of `/autocoder_cc/components/`, the system currently has these component types:

### Core Data Flow Components (5)
1. **Source** - Generates data (0 inputs, 1+ outputs)
2. **Sink** - Consumes data (1+ inputs, 0 outputs)
3. **Transformer** - Transforms data (1 input, 1 output)
4. **Router** - Routes data to different paths based on rules
5. **Filter** - Filters data based on conditions

### Domain-Specific Components (7)
6. **Store** - Persistent data storage with CRUD operations
7. **Controller** - Orchestrates operations across multiple components
8. **APIEndpoint** - HTTP/REST API interface
9. **Model** - Business logic and data processing
10. **MessageBus** - Pub/sub messaging infrastructure
11. **Accumulator** - Stateful aggregation of data over time
12. **Aggregator** - Combines multiple inputs into single output

### Specialized Components (6+)
13. **StreamProcessor** - Processes streaming data
14. **WebSocket** - WebSocket connection handler
15. **MetricsEndpoint** - Metrics and monitoring endpoint
16. **CommandHandler** - CQRS command processing
17. **QueryHandler** - CQRS query processing
18. **ComposedBase** - Base class for composed components

## How These Map to the 5-Type System

### Direct Mappings (Already Correct)
- Source → Source
- Sink → Sink  
- Transformer → Transformer

### Components That Become Transformers + Traits
- Store → Transformer + persistent + queryable
- Controller → Transformer + orchestrator + stateful
- Model → Transformer + business_logic
- Filter → Transformer + predicate
- Accumulator → Transformer + stateful + windowed
- StreamProcessor → Transformer + streaming
- CommandHandler → Transformer + command_pattern
- QueryHandler → Transformer + query_pattern

### Components That Become Sources + Traits
- APIEndpoint → Source + http + authenticated
- WebSocket → Source + websocket + bidirectional
- MetricsEndpoint → Source + metrics + monitoring

### Components That Become Sinks + Traits
- (Store could also be Sink in write-only scenarios)

### Components That Need New Types
- Router → Splitter (1 input, N outputs)
- Aggregator → Merger (N inputs, 1 output)
- MessageBus → Combination of Splitter + Merger

## Missing from Current System
- **Splitter** - Explicit 1-to-N distribution (Router is close but different semantics)
- **Merger** - Explicit N-to-1 combination (Aggregator is close but has aggregation logic)

## Why This Matters for Migration

The current 18+ types create:
1. **Complex validation rules** - Each type has unique connection rules
2. **LLM confusion** - Too many similar types to choose from
3. **Maintenance burden** - Each type needs separate implementation
4. **Testing complexity** - Each type needs unique test strategies

The 5-type system with recipes will:
1. **Simplify validation** - Only 5 connection rules to check
2. **Improve LLM accuracy** - Clear, orthogonal choices
3. **Reduce code** - 5 base classes + configuration
4. **Simplify testing** - Test 5 types + verify traits

## Migration Impact

### Components to Keep As-Is
- Source (already a primitive)
- Sink (already a primitive)  
- Transformer (already a primitive)

### Components to Convert to Recipes
- All 15+ domain-specific and specialized components

### Components to Create New
- Splitter (for Router-like behavior)
- Merger (for Aggregator-like behavior)

This explains why the validation is complex - we're trying to validate connections between 18+ types when we only need 5!