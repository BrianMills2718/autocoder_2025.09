# ADR-0001: Anyio Version Policy - Pin in CI, Range in Dev

**Date**: 2025-01-15
**Status**: Accepted
**Decision**: Pin exactly in CI (4.9.0), allow range in dev (>=4.9.0,<5.0)

## Context

The port-based architecture requires migrating from asyncio to anyio for structured concurrency. Multiple conflicting version recommendations exist in documentation:
- Some docs specify anyio>=4.9.0,<5.0
- Some older docs suggested anyio==4.3.* (now obsolete)
- Current installation has anyio==4.9.0

## Decision

**Dual strategy for reproducibility + flexibility:**
- **CI/Production**: Pin exactly via `constraints.txt`: `anyio==4.9.0`
- **Development**: Allow range via `pyproject.toml`: `anyio>=4.9.0,<5.0`

## Rationale

1. **Already Installed**: Version 4.9.0 is currently installed and working
2. **Python 3.12 Compatibility**: Supports modern Python versions
3. **Stable API**: The 4.x series has stabilized the core APIs we need
4. **No Downgrade Risk**: Avoiding downgrade prevents potential compatibility issues
5. **Upper Bound Protection**: `<5.0` prevents unexpected breaking changes

## Consequences

### Positive
- No installation changes required
- Latest bug fixes and performance improvements
- Better Python 3.11+ support
- Structured concurrency patterns are mature

### Negative
- Must ensure all code uses 4.x API patterns (not 3.x)
- Some online examples may be for 3.x and need adaptation

### Neutral
- Task group API is mandatory (no free-floating tasks)
- Must use streams instead of queues

## Implementation

### constraints.txt (CI/Production - Pinned)
```
anyio==4.9.0
```

### pyproject.toml (Development - Range)
```toml
[project.dependencies]
anyio = ">=4.9.0,<5.0"
```

### CI Usage
```bash
# Install with constraints for reproducible builds
pip install -c constraints.txt -e .
```

## Migration Notes

Key differences from asyncio:
- No `create_task()` - must use task groups
- Streams instead of Queues
- `fail_after()` instead of `wait_for()`
- No event loop access needed

## Review Schedule

Review this decision:
- After MVP ships (assess if 4.9.0 was stable)
- When anyio 5.0 releases (evaluate upgrade)
- If performance issues arise

## References

- [Anyio Documentation](https://anyio.readthedocs.io/)
- [Anyio 4.0 Migration Guide](https://anyio.readthedocs.io/en/stable/migration.html)
- STATUS_SOT.md - Single source of truth for versions