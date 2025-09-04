# ADR 024: Batched Processing Contracts

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Performance Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

The current component and capability lifecycle hooks (`before_receive`, `after_send`) assume single-item processing. This model is inefficient and potentially incorrect for components that are designed to operate on batches of data for performance reasons.

## Decision Drivers

*   The architecture must efficiently support high-throughput, batch-oriented components.
*   Capability hooks must be able to operate correctly on batches of items without ambiguity.
*   The contract for batch processing must be explicit to avoid incorrect metric collection or partial error handling.

## Considered Options

*   Introduce new hook variants specifically for batches (e.g., `before_receive_batch`).
*   Overload existing hooks and inspect the payload type (e.g., `isinstance(data, list)`).
*   Require batch-processing components to internally loop and call the single-item hooks for each item.

## Decision Outcome

**APPROVED**: Harness-aggregated batching with explicit configuration:

### Batching Configuration
```yaml
# blueprint.yaml
batching:
  max_items: 100
  max_ms: 1000
  error_mode: "fail_fast"  # or "continue", "partial"
```

### Batch Processing Contract
```python
class BatchProcessor(Component):
    async def process_batch(self, items: List[Any]) -> List[Any]:
        """Process a batch of items efficiently."""
        # Vectorized processing
        results = await self.vectorized_process(items)
        return results
```

### Capability Hook Support
```python
class MetricsCapability(Capability):
    async def before_process(self, context: ProcessContext) -> None:
        """Called once per batch, not per item."""
        batch_size = len(context.items)
        self.metrics.record_batch_size(batch_size)
    
    async def after_process(self, context: ProcessContext, results: List[Any]) -> None:
        """Called once per batch with all results."""
        self.metrics.record_batch_processing_time(context.duration)
```

### Error Handling Modes
- **fail_fast**: Stop processing on first error
- **continue**: Process all items, collect errors
- **partial**: Return successful results with error list

### Performance Benefits
- **Reduced overhead**: One capability chain per batch
- **Vectorized processing**: Efficient bulk operations
- **Better throughput**: Optimized for high-volume data

## Consequences

### Positive
- Significant performance improvement for batch operations
- Clear contract for batch processing
- Flexible error handling strategies
- Maintains capability chain consistency

### Negative
- More complex capability implementation
- Potential memory usage for large batches
- Error handling complexity

### Neutral
- Maintains architectural consistency
- Enables high-throughput processing
- Provides clear batch semantics 