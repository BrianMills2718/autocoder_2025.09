# Critical Implementation Decisions

*Purpose: Only the decisions you need to implement the system*
*Updated: 2025-08-12 - All decisions now MADE*

## ✅ DECISIONS MADE

1. **Asyncio → Anyio**: **USE ANYIO** (refactor existing)
2. **Blueprint Schema Version**: **USE 2.0.0** (major breaking change)
3. **Trait System**: **REMOVE** (use capability flags in config instead)
4. **Checkpoint Strategy**: **SQLite (file-based)** per system

## 🏗️ Architecture Decisions

### 1. Five Mathematical Primitives (Not 13+ Types)
```
Source:      0→N ports (generates data)
Sink:        N→0 ports (consumes data, concurrent drain via task group)
Transformer: 1→{0..1} ports (processes data, returning None = drop/filter)
Splitter:    1→N ports (distributes data)
Merger:      N→1 ports (combines data, fair-ish fan-in to prevent starvation)
```

### 2. Port-Based Communication
- Typed ports using `anyio.MemoryObjectStream`
- Pydantic validation on all data
- No RPC, no communication.py files

### 3. Port Naming Convention (Enforced)
```python
Input ports:  "in_*"   # e.g., in_data, in_commands
Output ports: "out_*"  # e.g., out_result, out_response
Error ports:  "err_*"  # e.g., err_validation, err_timeout
```

## 🔧 Technical Decisions

### 4. Overflow Policies
```python
Internal ports: OverflowPolicy.BLOCK              # Wait forever
Ingress ports:  OverflowPolicy.BLOCK_WITH_TIMEOUT # Default 2000ms timeout
```
**Ingress behavior**: On timeout, return HTTP 503 with `Retry-After: 2` header
**Payload cap**: 64KB default at ingress (configurable), return 413 if exceeded

### 5. Buffer Settings
- Default size: 1024
- Configurable per port
- Backpressure when full
- Track `buffer_utilization` (0.0-1.0) as gauge

### 6. Checkpoint System
- Storage: SQLite (file-based) at `/var/lib/autocoder4_cc/checkpoints/{system_name}.db`
- Table: `checkpoints(checkpoint_id TEXT PRIMARY KEY, component_name TEXT, created_at INTEGER, state BLOB)`
- Frequency: Every 60 seconds
- Retention: Keep last 10 snapshots per system (row-level pruning)
- Atomic writes: temp file → rename with fsync

### 7. Idempotency Store
- Storage: SQLite (upgrade path to Postgres)
- Path: `/var/lib/autocoder4_cc/idempotency.db`
- Key format: `(key, action)` primary key
- TTL: 7 days cleanup

### 8. Error Envelope Format
```json
{
  "ts": "2025-08-11T10:30:00Z",
  "system": "todo_system",
  "component": "todo_store",
  "port": "in_data",
  "input_offset": 123,
  "category": "validation|runtime|io",
  "message": "Error description",
  "payload": {},  // PII fields masked before emission
  "trace_id": "abc-123"
}
```
**PII Masking**: Fields named `email`, `password`, `ssn`, `phone`, `token`, `api_key`, `secret`, `credit_card` are masked (configurable via `redaction_enabled=true`)

### 9. Required Metrics (Per Port)
- `messages_in_total`: counter
- `messages_out_total`: counter
- `messages_dropped_total`: counter
- `errors_total`: counter
- `queue_depth`: gauge
- `buffer_utilization`: gauge (0.0-1.0) 
- `message_age_ms`: histogram (enqueue → dequeue time)
- `process_latency_ms`: histogram
- `blocked_duration_ms`: histogram
- `last_checkpoint_epoch`: gauge

**Critical**: Use `time.monotonic_ns()` for all duration measurements

## 📊 Performance Targets

### 9. v1 Requirements
- Validation success: 80% (not 100%)
- Throughput: 1000 msg/sec
- p95 latency: < 50ms
- Test coverage: 80%+

### 10. v2 Goals (Future)
- Validation success: 100%
- Advanced self-healing
- Dynamic ports
- Distributed execution

## 🛠️ Implementation Approach

### 11. Test-Driven Development
1. Write test first
2. Run test (should fail)
3. Implement until test passes
4. Refactor if needed
5. Commit when all tests green

### 12. No Backwards Compatibility
- Complete replacement, not migration
- No support for old RPC components
- Clean break from existing system

### 13. Fix Import Bug First
```python
# Line 1492 in component_logic_generator.py
# WRONG: from observability import ComposedComponent
# RIGHT: from autocoder_cc.components.composed_base import ComposedComponent
```

### 14. Recipe System
- Compile-time expansion (not runtime)
- Recipes map domain types to primitives
- Example: Store → Transformer with persistence traits

### 15. No Mock Testing
- Real integration tests only
- Components must actually connect
- Use in-memory SQLite for DB tests

## 📁 File Structure

### 16. New Code Locations
```
/autocoder_cc/components/ports/       # Port implementation
/autocoder_cc/components/primitives/  # 5 mathematical primitives
/autocoder_cc/components/recipes/     # Recipe definitions
/tests/port_based/                    # All new tests
```

### 17. Files to Replace
- ~135 component files (30% of codebase)
- All communication.py files
- All RPC-related code

### 18. Files to Keep
- ~315 infrastructure files (70% of codebase)
- LLM providers
- Observability
- Tools and utilities

## 🚫 What NOT to Do

### 19. Avoid These Patterns
- ❌ No RPC calls
- ❌ No communication.py generation
- ❌ No mock objects in tests
- ❌ No runtime recipe expansion
- ❌ No dynamic port creation (v1)
- ❌ No backwards compatibility code

### 20. Common Mistakes to Avoid
- Using `asyncio` instead of `anyio`
- Forgetting port prefixes (in_, out_, err_)
- Small buffer sizes (< 1024)
- Non-atomic checkpoint writes
- Testing components in isolation

## ✅ Quick Validation

Before implementing any feature, ask:
1. Does it use ports (not RPC)?
2. Is it one of the 5 primitives?
3. Are ports named correctly?
4. Is there a test written first?
5. Does it meet v1 targets (80%)?

---

*These 20 decisions are all you need. Everything else is historical context.*