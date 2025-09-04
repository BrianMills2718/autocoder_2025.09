# ADR 028: Disaster Recovery and State Persistence

*   **Status**: APPROVED
*   **Date**: 2025-07-18
*   **Deciders**: Architecture Team
*   **Consulted**: Infrastructure Working Group
*   **Supersedes**: N/A
*   **Superseded by**: N/A

## Context and Problem Statement

The architecture mentions state resumption for the `LocalOrchestrator` for local development, but it does not define a strategy for persistent state and disaster recovery in a production cloud environment. A system crash or restart would currently lead to total state loss for any long-running, stateful processes.

## Decision Drivers

*   Production systems must be resilient to crashes and restarts.
*   We need a consistent, pluggable mechanism for persisting the state of the `SystemExecutionHarness` and its components.
*   The chosen strategy must be compatible with cloud-native environments (e.g., Kubernetes).

## Considered Options

*   Redis-based state persistence with snapshot/restore.
*   Database-backed state with transaction support.
*   File-based state with cloud storage backend.

## Decision Outcome

**APPROVED**: Pluggable state adapters with Redis snapshot as default enterprise option:

### State Persistence Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class StateAdapter(ABC):
    @abstractmethod
    async def save_state(self, component_id: str, state: Dict[str, Any]) -> None:
        """Save component state."""
        pass
    
    @abstractmethod
    async def load_state(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Load component state."""
        pass
    
    @abstractmethod
    async def delete_state(self, component_id: str) -> None:
        """Delete component state."""
        pass
```

### Redis Snapshot Adapter
```python
class RedisStateAdapter(StateAdapter):
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl
    
    async def save_state(self, component_id: str, state: Dict[str, Any]) -> None:
        key = f"autocoder:state:{component_id}"
        await self.redis.setex(key, self.ttl, json.dumps(state))
```

### Configuration
```yaml
# config.yaml
state_persistence:
  adapter: "redis"
  redis_url: "${REDIS_URL}"
  ttl: 3600
  snapshot_interval: 60
```

### Component State Management
```python
class StatefulComponent(Component):
    def __init__(self):
        self.state = {}
        self.state_adapter = get_state_adapter()
    
    async def checkpoint_state(self) -> None:
        """Save current state to persistent storage."""
        await self.state_adapter.save_state(self.id, self.state)
    
    async def restore_state(self) -> None:
        """Restore state from persistent storage."""
        state = await self.state_adapter.load_state(self.id)
        if state:
            self.state = state
```

### Disaster Recovery
- **Automatic checkpointing**: Periodic state snapshots
- **Graceful shutdown**: State preservation on shutdown
- **Startup recovery**: State restoration on startup
- **State validation**: Integrity checks on restore

## Consequences

### Positive
- Production-grade disaster recovery
- Pluggable state persistence
- Cloud-native compatibility
- Automatic state management

### Negative
- Additional infrastructure dependency
- State serialization overhead
- Potential state consistency issues

### Neutral
- Maintains architectural flexibility
- Enables enterprise deployments
- Provides clear state boundaries 