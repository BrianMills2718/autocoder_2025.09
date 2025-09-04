# ADR-0002: Checkpoint Storage Strategy

**Date**: 2025-01-15
**Status**: Accepted
**Decision**: SQLite for v1, defined triggers for Postgres migration

## Context

The port-based architecture requires persistent checkpointing for recovery and state management. Multiple approaches have been discussed:
- SQLite (file-based, simple)
- PostgreSQL (client-server, scalable)
- Mixed approach with migration path

## Decision

**v1: SQLite file per system**
**v2: Migrate to PostgreSQL when specific triggers are met**

### v1 Implementation Details

- One SQLite database file per system
- Location:
  - **Production**: `/var/lib/autocoder4_cc/checkpoints/{system_id}.db`
  - **Development**: `./.state/checkpoints/{system_id}.db` (portable, works on Windows/Mac/Linux)
  - **Override**: Via `AUTOCODER_STATE_DIR` environment variable
- Snapshot frequency: Every 60 seconds
- Retention: Keep last 10 snapshots
- Schema versioning: Embedded in database
- **Write budget**: Max 1 write/sec/component to avoid SQLite contention
  - Use WAL mode for better concurrency
  - Batch writes when possible
  - Move to PostgreSQL if sustained >10 writes/sec needed

### Migration Triggers to PostgreSQL

Migrate from SQLite to PostgreSQL when **ANY** of these conditions are met:

1. **Multi-Process Access**: Need to read/write checkpoints from multiple processes or nodes
2. **Performance Threshold**: 
   - Steady-state write rate > 1 write/second
   - Database file size > 1 GB
3. **Recovery Requirements**: RTO (Recovery Time Objective) < 10 seconds
4. **Compliance Requirements**:
   - Central backup requirements
   - Point-in-time recovery (PITR) needed
   - Audit logging requirements

## Rationale

### Why SQLite First

1. **Simplicity**: No server to manage, just files
2. **Zero Configuration**: Works out of the box
3. **Sufficient for MVP**: Most systems won't hit triggers initially
4. **Easy Backup**: File copy is a valid backup
5. **Portable**: Can develop/test anywhere

### Why Define Migration Path

1. **Scalability**: Clear path when limits are reached
2. **No Surprises**: Teams know when to migrate
3. **Gradual Migration**: Can migrate system by system
4. **Cost Effective**: Only run Postgres when needed

## Consequences

### Positive
- Simple v1 deployment
- Clear scaling strategy
- Per-system isolation
- Easy local development

### Negative
- Migration complexity when triggers hit
- Two checkpoint implementations to maintain
- SQLite limitations for concurrent access

### Neutral
- Must monitor for trigger conditions
- Different backup strategies for SQLite vs Postgres

## Implementation

### v1 SQLite Schema

```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    port_name TEXT NOT NULL,
    message_id TEXT NOT NULL,
    offset INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    data BLOB,
    UNIQUE(component_name, port_name, message_id)
);

CREATE INDEX idx_component_port ON checkpoints(component_name, port_name);
CREATE INDEX idx_timestamp ON checkpoints(timestamp);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO metadata (key, value) VALUES 
    ('schema_version', '1.0.0'),
    ('created_at', datetime('now'));
```

### Configuration

```python
# v1 SQLite configuration
CHECKPOINT_CONFIG = {
    "type": "sqlite",
    "path": "/var/lib/autocoder4_cc/checkpoints/{system_id}.db",
    "snapshot_interval_seconds": 60,
    "max_snapshots": 10,
    "wal_mode": True,  # Write-ahead logging for better concurrency
}

# v2 PostgreSQL configuration (when triggered)
CHECKPOINT_CONFIG = {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "autocoder4_cc",
    "schema": "checkpoints",
    "pool_size": 10,
    "max_overflow": 20,
}
```

### Monitoring for Triggers

```python
def should_migrate_to_postgres(system_id: str) -> bool:
    """Check if any migration triggers are met."""
    
    # Check database size
    db_path = f"/var/lib/autocoder4_cc/checkpoints/{system_id}.db"
    if os.path.getsize(db_path) > 1_000_000_000:  # 1 GB
        return True
    
    # Check write rate (from metrics)
    write_rate = metrics.get_rate("checkpoint_writes", system_id)
    if write_rate > 1.0:  # More than 1 write/second
        return True
    
    # Check recovery requirements (from config)
    if config.get("rto_seconds", 30) < 10:
        return True
    
    # Check for multi-process flag
    if config.get("multi_process_access", False):
        return True
    
    return False
```

## Migration Process

When triggers are met:

1. **Pause writes** to SQLite
2. **Export** SQLite data to SQL dump
3. **Import** into PostgreSQL
4. **Verify** data integrity
5. **Switch** configuration
6. **Resume** writes to PostgreSQL
7. **Archive** SQLite file

## Review Schedule

Review this decision:
- Quarterly metrics review of trigger hits
- When first system hits migration trigger
- After 10 systems migrate (reassess triggers)

## References

- [SQLite When to Use](https://www.sqlite.org/whentouse.html)
- [PostgreSQL vs SQLite](https://www.postgresql.org/about/)
- STATUS_SOT.md - Checkpoint strategy section