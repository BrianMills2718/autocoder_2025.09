# External Feedback Integration

*Date: 2025-08-12*
*Status: Reviewing external LLM suggestions*

## Changes to Accept ✅

### 1. Clarify Checkpoint Storage
**Current**: "FILE-BASED" vs "SQLite" confusion
**Change to**: 
```
Checkpoint storage: SQLite (file-based) at /var/lib/autocoder4_cc/checkpoints/{system_name}.db
- One DB file per system
- Checkpoints table with retention of last 10 snapshots
- Row-level pruning by checkpoint_id
```

### 2. Transformer Contract Enhancement
**Current**: `Transformer: 1→1`
**Change to**: `Transformer: 1→{0..1}` 
- Returning None means drop/filter
- Eliminates need for separate Filter primitive
- Mathematically cleaner

### 3. Ingress Behavior Specification
**Add**:
```python
# On ingress timeout
if timeout_exceeded:
    return Response(
        status_code=503,
        headers={"Retry-After": "2"},
        body={"error": "Service temporarily unavailable"}
    )
```

### 4. Critical Metrics Addition
**Add to required metrics**:
- `buffer_utilization`: float (0.0-1.0) - Current fill percentage
- `message_age_ms`: int - Time from enqueue to dequeue

### 5. Concurrency Clarification
**Sink behavior**: "Drains all input ports concurrently via anyio.TaskGroup"
**Merger behavior**: "Fair-ish round-robin to prevent starvation"

### 6. Security Defaults
**Add**:
- Ingress payload cap: 64KB default (configurable per port)
- PII field masking: Simple field-name based (email, password, ssn, phone)

### 7. CI Import Guard
**Add to CI pipeline**:
```bash
# Fail if old import pattern found
if grep -r "from observability import ComposedComponent" autocoder_cc/; then
    echo "ERROR: Old import pattern detected!"
    exit 1
fi
```

### 8. Recipe Capability Flags
**Change from**: `"traits": ["persistence", "idempotency"]`
**Change to**:
```python
"config": {
    "persistent": true,  # Capability flag, not trait
    "idempotent": true  # Baked in at generation time
}
```

### 9. Rename Schema Version
**Change**: "Schema Version" → "Blueprint Schema Version: 2.0.0"
(Clarifies it's not Pydantic schema)

## Changes to Modify 🔧

### 1. PII Redaction Scope
**Their suggestion**: "best-effort PII redaction"
**Our modification**: 
- Simple field-name masking only (no regex in v1)
- Configurable on/off switch
- Limited to: email, password, ssn, phone, card_number

### 2. Merger Fairness
**Their suggestion**: "strict round-robin"
**Our modification**: 
- "Fair-ish scheduling" (prevent starvation but allow flexibility)
- Simple async iteration in v1
- Can add weighted priority in v2

## Changes to Reject ❌

None - all suggestions have value, though some need modification.

## Updated Technical Decisions

### Primitives (UPDATED)
```
Source:      0→N ports (generates data)
Sink:        N→0 ports (consumes data, concurrent drain)
Transformer: 1→{0..1} ports (None = drop/filter)
Splitter:    1→N ports (distributes data)
Merger:      N→1 ports (combines data, fair-ish scheduling)
```

### Checkpoint System (CLARIFIED)
```
Storage: SQLite file per system
Path: /var/lib/autocoder4_cc/checkpoints/{system_name}.db
Table: checkpoints (checkpoint_id, component_name, state_json, created_at)
Retention: Keep last 10 snapshots, row-level pruning
Frequency: Every 60 seconds
```

### Overflow Policies (ENHANCED)
```python
Internal ports: OverflowPolicy.BLOCK
Ingress ports:  OverflowPolicy.BLOCK_WITH_TIMEOUT
    - Default timeout: 2000ms (configurable via timeout_ms)
    - On timeout: HTTP 503 + Retry-After: 2
```

### Security Defaults (NEW)
```python
ingress_config = {
    "max_payload_kb": 64,  # Default cap
    "mask_pii_fields": ["email", "password", "ssn", "phone"],
    "timeout_ms": 2000
}
```

### Required Metrics (ENHANCED)
Per port:
- `messages_sent`: counter
- `messages_received`: counter
- `messages_dropped`: counter
- `buffer_utilization`: gauge (0.0-1.0) ← NEW
- `message_age_ms`: histogram ← NEW

## Implementation Priority

### Must Have for v1:
1. Transformer 1→{0..1} change
2. SQLite checkpoint clarification
3. HTTP 503 behavior
4. Buffer metrics
5. CI import guard

### Nice to Have for v1:
1. PII masking (simple version)
2. Payload cap
3. Fair-ish merger

### Can Defer to v2:
1. Advanced PII detection
2. Weighted merger priorities
3. Distributed checkpoints

## Summary

The external review is excellent and caught several important issues:
- **Critical fixes**: Checkpoint confusion, Transformer contract
- **Production readiness**: HTTP 503, metrics, security
- **Clarity improvements**: Concurrency specs, naming

We should integrate most suggestions with minor modifications for simplicity. This will make our implementation more robust and production-ready from day one.