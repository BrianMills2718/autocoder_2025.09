# ADR 023: Capability Re-entrancy Policy

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Component Model Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

It is unclear if a capability (like a `RetryHandler`) is allowed to re-invoke the component's processing logic. This could potentially re-trigger the full capability chain from the beginning, leading to unexpected behavior or infinite loops.

## Decision Drivers

*   The interaction between capabilities and the component's core logic must be deterministic and safe.
*   We must prevent infinite loops caused by re-entrant capability calls.
*   The policy must be clear and easy for capability developers to follow.

## Considered Options

*   Strictly forbid re-entrancy.
*   Allow re-entrancy but only for the core business logic, bypassing the rest of the capability chain.
*   Allow full re-entrancy and rely on developers to implement safeguards (e.g., retry counters).

## Decision Outcome

**APPROVED**: Re-entrancy disallowed by default with explicit decorator for exceptions:

### Default Policy
- **Capability-to-capability calls are disallowed by default**
- **Re-entrant calls to component processing logic are forbidden**
- **Capabilities must not invoke other capabilities directly**

### Explicit Re-entrancy
```python
from autocoder.capabilities import allow_reentrant

class RetryHandler(Capability):
    @allow_reentrant
    async def around_process(self, context: ProcessContext, next_hook: Callable) -> Any:
        """Explicitly allowed to retry the processing logic."""
        try:
            return await next_hook(context)
        except TransientError:
            # Retry logic - explicitly allowed
            return await next_hook(context)
```

### Safety Mechanisms
- **Re-entrancy Guard**: Automatic detection of re-entrant calls
- **Stack Depth Limit**: Maximum re-entrancy depth (default: 1)
- **Audit Logging**: All re-entrant calls are logged for debugging

### Allowed Patterns
- **Retry Logic**: Explicit retry with `@allow_reentrant`
- **Circuit Breaker**: State changes without re-entrancy
- **Metrics Collection**: Observability without re-entrancy

## Consequences

### Positive
- Prevents infinite loops and unexpected behavior
- Clear policy for capability developers
- Explicit opt-in for re-entrancy when needed
- Automatic safety mechanisms

### Negative
- More complex capability implementation for retry logic
- Requires explicit decorator for legitimate re-entrancy
- Potential performance overhead from guards

### Neutral
- Maintains architectural consistency
- Enables safe retry and resilience patterns
- Provides clear re-entrancy boundaries 