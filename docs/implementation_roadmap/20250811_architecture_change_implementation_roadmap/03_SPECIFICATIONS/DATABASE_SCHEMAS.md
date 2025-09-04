# Database Schemas for Port-Based Architecture

⚠️ **CRITICAL DISCOVERY: Database layer is just documentation - no implementation exists**
- No connection pool management code
- No transaction handling implementation
- No migration runner
- Async database drivers not installed
- All schemas defined but zero code to use them

## Overview
This document defines the database schemas required for the port-based architecture, including component state storage, message persistence, checkpoint management, and metrics collection.

## 1. Core Schema Design Principles

### Universal Component Storage
- All components use JSONB for flexible data storage
- UUID primary keys for distributed consistency
- Timestamps for audit trails and debugging
- GIN indexes for efficient JSONB querying

### Port Message Persistence
- Optional message persistence for durability
- Dead letter queue for failed messages
- Message replay capability for debugging

### Checkpoint Management
- Atomic checkpoint writes with versioning
- Component state snapshots
- Recovery metadata

## 2. PostgreSQL Schemas

### 2.1 Component State Storage
```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Universal component state table
CREATE TABLE component_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) NOT NULL CHECK (component_type IN ('Source', 'Sink', 'Transformer', 'Splitter', 'Merger')),
    state_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(component_name, version)
);

-- Indexes for efficient querying
CREATE INDEX idx_component_state_name ON component_state (component_name);
CREATE INDEX idx_component_state_type ON component_state (component_type);
CREATE INDEX idx_component_state_created ON component_state (created_at);
CREATE INDEX idx_component_state_data_gin ON component_state USING gin(state_data);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_component_state_updated_at
BEFORE UPDATE ON component_state
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### 2.2 Port Message Queue
```sql
-- Port message persistence (optional, for durability)
CREATE TABLE port_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    port_name VARCHAR(255) NOT NULL,
    source_component VARCHAR(255) NOT NULL,
    target_component VARCHAR(255) NOT NULL,
    message_data JSONB NOT NULL,
    message_metadata JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dead_letter')),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    error_details JSONB
);

-- Indexes for message queue operations
CREATE INDEX idx_port_messages_status ON port_messages (status);
CREATE INDEX idx_port_messages_port ON port_messages (port_name);
CREATE INDEX idx_port_messages_created ON port_messages (created_at);
CREATE INDEX idx_port_messages_pending ON port_messages (status, created_at) WHERE status = 'pending';
CREATE INDEX idx_port_messages_retry ON port_messages (status, retry_count) WHERE status = 'failed' AND retry_count < max_retries;

-- Dead letter queue view
CREATE VIEW dead_letter_queue AS
SELECT * FROM port_messages
WHERE status = 'dead_letter' OR (status = 'failed' AND retry_count >= max_retries);
```

### 2.3 Checkpoint Storage
```sql
-- Checkpoint management for recovery
CREATE TABLE checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    checkpoint_name VARCHAR(255) NOT NULL,
    component_name VARCHAR(255) NOT NULL,
    checkpoint_data JSONB NOT NULL,
    checkpoint_metadata JSONB,
    version BIGINT NOT NULL,
    is_latest BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(checkpoint_name, version)
);

-- Indexes for checkpoint operations
CREATE INDEX idx_checkpoints_name ON checkpoints (checkpoint_name);
CREATE INDEX idx_checkpoints_component ON checkpoints (component_name);
CREATE INDEX idx_checkpoints_latest ON checkpoints (is_latest) WHERE is_latest = TRUE;
CREATE INDEX idx_checkpoints_expires ON checkpoints (expires_at) WHERE expires_at IS NOT NULL;

-- Function to mark old checkpoints as not latest
CREATE OR REPLACE FUNCTION update_checkpoint_latest()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_latest THEN
        UPDATE checkpoints 
        SET is_latest = FALSE 
        WHERE checkpoint_name = NEW.checkpoint_name 
        AND id != NEW.id 
        AND is_latest = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER checkpoint_latest_trigger
AFTER INSERT ON checkpoints
FOR EACH ROW
EXECUTE FUNCTION update_checkpoint_latest();
```

### 2.4 Metrics and Monitoring
```sql
-- Component metrics storage
CREATE TABLE component_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(50),
    metric_metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partition by day for efficient querying and retention
CREATE INDEX idx_component_metrics_time ON component_metrics (timestamp);
CREATE INDEX idx_component_metrics_component ON component_metrics (component_name, timestamp);
CREATE INDEX idx_component_metrics_name ON component_metrics (metric_name, timestamp);

-- Port metrics
CREATE TABLE port_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    port_name VARCHAR(255) NOT NULL,
    messages_sent BIGINT DEFAULT 0,
    messages_received BIGINT DEFAULT 0,
    avg_send_duration_ms DOUBLE PRECISION,
    avg_receive_duration_ms DOUBLE PRECISION,
    avg_message_age_ms DOUBLE PRECISION,
    buffer_utilization DOUBLE PRECISION,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_port_metrics_time ON port_metrics (timestamp);
CREATE INDEX idx_port_metrics_port ON port_metrics (port_name, timestamp);

-- System health status
CREATE TABLE system_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_name VARCHAR(255) NOT NULL,
    health_status VARCHAR(20) NOT NULL CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    health_details JSONB,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_system_health_component ON system_health (component_name);
CREATE INDEX idx_system_health_status ON system_health (health_status);
CREATE INDEX idx_system_health_heartbeat ON system_health (last_heartbeat);
```

### 2.5 Sink Component Storage
```sql
-- Generic storage for Sink components
CREATE TABLE sink_storage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sink_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100),
    data JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sink_storage_name ON sink_storage (sink_name);
CREATE INDEX idx_sink_storage_created ON sink_storage (created_at);
CREATE INDEX idx_sink_storage_data_gin ON sink_storage USING gin(data);

CREATE TRIGGER update_sink_storage_updated_at
BEFORE UPDATE ON sink_storage
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

## 3. SQLite Schemas (For Testing/Development)

### 3.1 Simplified Schema for SQLite
```sql
-- Component state (SQLite version)
CREATE TABLE component_state (
    id TEXT PRIMARY KEY,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL CHECK (component_type IN ('Source', 'Sink', 'Transformer', 'Splitter', 'Merger')),
    state_data TEXT NOT NULL, -- JSON stored as TEXT
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(component_name, version)
);

CREATE INDEX idx_component_state_name ON component_state (component_name);
CREATE INDEX idx_component_state_type ON component_state (component_type);

-- Port messages (SQLite version)
CREATE TABLE port_messages (
    id TEXT PRIMARY KEY,
    port_name TEXT NOT NULL,
    source_component TEXT NOT NULL,
    target_component TEXT NOT NULL,
    message_data TEXT NOT NULL, -- JSON as TEXT
    message_metadata TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT,
    completed_at TEXT
);

CREATE INDEX idx_port_messages_status ON port_messages (status);
CREATE INDEX idx_port_messages_port ON port_messages (port_name);

-- Checkpoints (SQLite version)
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    checkpoint_name TEXT NOT NULL,
    component_name TEXT NOT NULL,
    checkpoint_data TEXT NOT NULL, -- JSON as TEXT
    version INTEGER NOT NULL,
    is_latest INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(checkpoint_name, version)
);

CREATE INDEX idx_checkpoints_name ON checkpoints (checkpoint_name);
CREATE INDEX idx_checkpoints_latest ON checkpoints (is_latest);

-- Metrics (SQLite version)
CREATE TABLE component_metrics (
    id TEXT PRIMARY KEY,
    component_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_component_metrics_component ON component_metrics (component_name);
CREATE INDEX idx_component_metrics_name ON component_metrics (metric_name);
```

## 4. Database Configuration Management

### 4.1 Configuration Structure
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database configuration for components"""
    database_type: str  # postgresql, mysql, sqlite
    host: str
    port: int
    database_name: str
    username: str
    password: Optional[str] = None
    
    # Connection pool settings
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    
    # Performance settings
    statement_timeout: int = 30000  # ms
    lock_timeout: int = 10000  # ms
    idle_in_transaction_timeout: int = 60000  # ms
    
    # Retry settings
    max_retries: int = 3
    retry_delay_ms: int = 1000
    exponential_backoff: bool = True
```

### 4.2 Environment-Specific Configurations
```yaml
# config/database.yaml
development:
  database_type: sqlite
  database_name: ./data/dev.db
  
testing:
  database_type: sqlite
  database_name: :memory:
  
staging:
  database_type: postgresql
  host: staging-db.internal
  port: 5432
  database_name: autocoder_staging
  username: autocoder_user
  min_connections: 5
  max_connections: 20
  
production:
  database_type: postgresql
  host: ${DB_HOST}
  port: ${DB_PORT}
  database_name: ${DB_NAME}
  username: ${DB_USER}
  password: ${DB_PASSWORD}
  min_connections: 10
  max_connections: 50
  statement_timeout: 60000
  ssl_mode: require
```

## 5. Migration Strategy

### 5.1 Schema Versioning
```sql
-- Schema version tracking
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Initial version
INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial port-based architecture schema');
```

### 5.2 Migration Scripts Structure
```
migrations/
├── 001_initial_schema.sql
├── 002_add_metrics_tables.sql
├── 003_add_checkpoint_support.sql
├── 004_add_port_persistence.sql
└── 005_add_performance_indexes.sql
```

### 5.3 Rollback Support
```sql
-- Each migration should include rollback
-- Example: 002_add_metrics_tables.sql

-- UP
CREATE TABLE component_metrics (...);

-- DOWN (stored separately or as comments)
-- DROP TABLE component_metrics;
```

## 6. Data Retention Policies

### 6.1 Retention Rules
```sql
-- Automated cleanup for old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete metrics older than 30 days
    DELETE FROM component_metrics 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Delete completed messages older than 7 days
    DELETE FROM port_messages 
    WHERE status = 'completed' 
    AND completed_at < NOW() - INTERVAL '7 days';
    
    -- Delete old checkpoints (keep last 10 per component)
    DELETE FROM checkpoints 
    WHERE id NOT IN (
        SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY component_name 
                ORDER BY created_at DESC
            ) as rn 
            FROM checkpoints
        ) t WHERE rn <= 10
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (using pg_cron or external scheduler)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data()');
```

## 7. Performance Optimization

### 7.1 Table Partitioning (PostgreSQL)
```sql
-- Partition metrics by day for better performance
CREATE TABLE component_metrics_partitioned (
    LIKE component_metrics INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create partitions
CREATE TABLE component_metrics_2025_08_10 
PARTITION OF component_metrics_partitioned
FOR VALUES FROM ('2025-08-10') TO ('2025-08-11');

CREATE TABLE component_metrics_2025_08_11 
PARTITION OF component_metrics_partitioned
FOR VALUES FROM ('2025-08-11') TO ('2025-08-12');

-- Automated partition creation would be handled by a maintenance job
```

### 7.2 Query Optimization
```sql
-- Materialized view for component statistics
CREATE MATERIALIZED VIEW component_statistics AS
SELECT 
    component_name,
    COUNT(*) as total_messages,
    AVG(metric_value) as avg_throughput,
    MAX(timestamp) as last_activity
FROM component_metrics
WHERE metric_name = 'throughput'
GROUP BY component_name;

CREATE INDEX idx_component_statistics_name ON component_statistics (component_name);

-- Refresh periodically
-- REFRESH MATERIALIZED VIEW CONCURRENTLY component_statistics;
```

## 8. Backup and Recovery

### 8.1 Backup Strategy
```bash
# PostgreSQL backup
pg_dump -h localhost -U autocoder_user -d autocoder_db \
    --schema-only > schema_backup.sql
    
pg_dump -h localhost -U autocoder_user -d autocoder_db \
    --data-only --table=checkpoints > checkpoints_backup.sql
```

### 8.2 Point-in-Time Recovery
```sql
-- Enable WAL archiving for PITR (postgresql.conf)
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /backup/wal/%f'
```

## Summary

This database schema provides:
1. **Flexible component state storage** using JSONB
2. **Message persistence** for durability and replay
3. **Checkpoint management** for recovery
4. **Comprehensive metrics** collection
5. **Health monitoring** capabilities
6. **Performance optimization** through indexing and partitioning
7. **Data retention** policies
8. **Migration support** with versioning

The schema is designed to support both development (SQLite) and production (PostgreSQL) environments while maintaining consistency in the data model.