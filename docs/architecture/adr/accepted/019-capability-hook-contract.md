# ADR 019: Capability Hook Contract

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Component Model Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

While `ComposedComponent` provides the *mechanism* for hooks, the *contract* is not formally defined. Capabilities don't have a clear, enforceable interface for how they interact with the component lifecycle. This leads to ambiguity about execution order, method signatures, and error handling.

## Decision Drivers

*   We need a clear, enforceable interface for capabilities.
*   The execution order of hooks must be deterministic.
*   Method signatures must be consistent and support `async` operations.
*   Error handling within hooks must be well-defined.

## Considered Options

*   Define a formal interface with `ABC` and abstract methods.
*   Rely on convention and documentation.
*   Use a decorator-based system for hook registration.

## Decision Outcome

**APPROVED**: Capabilities implement a typed, async-first, three-phase hook interface:

### Hook Interface
```python
class CapabilityHook(ABC):
    @abstractmethod
    async def before_process(self, context: ProcessContext) -> None:
        """Pre-processing hook called before item processing."""
        pass
    
    @abstractmethod
    async def around_process(self, context: ProcessContext, next_hook: Callable) -> Any:
        """Around-processing hook that can wrap the processing chain."""
        pass
    
    @abstractmethod
    async def after_process(self, context: ProcessContext, result: Any) -> None:
        """Post-processing hook called after item processing."""
        pass
```

### Execution Order
1. **before_process**: All capabilities execute in registration order
2. **around_process**: Capabilities wrap each other (last registered = outermost)
3. **after_process**: All capabilities execute in reverse registration order

### Error Handling
- Hooks can raise exceptions to abort processing
- `around_process` exceptions propagate to outer hooks
- Failed hooks are logged with context for debugging

## Consequences

### Positive
- Clear, enforceable interface for all capabilities
- Deterministic execution order
- Consistent async support
- Well-defined error handling semantics

### Negative
- Requires updating all existing capabilities
- Adds complexity to capability implementation
- Potential performance overhead from hook calls

### Neutral
- Maintains backward compatibility through adapter pattern
- Enables future capability enhancements 