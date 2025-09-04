# Accumulator Component (Stream-Based Implementation)

## Overview
Redis-backed persistent state management for atomic accumulation operations with production-ready reliability.

## Implementation Details
**Base Class**: `ComposedComponent` (from `autocoder_cc.components.composed_base`)  
**File**: `autocoder_cc/components/accumulator.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Dependencies**: Redis server for persistent storage

## Configuration Schema
```yaml
- name: "state_accumulator"
  type: "Accumulator"
  config:
    redis_url: "redis://localhost:6379/0"  # Direct URL configuration
    # OR individual components:
    host: "localhost"
    port: 6379
    password: "optional_password"
    db: 0
```

## Key Features

### Redis Integration
- **Atomic Operations**: Uses Redis atomic commands (`INCRBYFLOAT`, Lua scripts)
- **Persistent State**: All accumulation state survives component restarts
- **Connection Resilience**: Fallback connection strategies for reliability
- **Connection Pooling**: Efficient Redis connection management

### Supported Operations
- **Addition**: Atomic increment/decrement with `INCRBYFLOAT`
- **Multiplication**: Atomic multiplication using Lua scripts
- **Reset**: Clear accumulator to zero
- **Get Total**: Retrieve current accumulated value

### Production Features
- **Error Recovery**: Comprehensive error handling with fallback
- **Dependency Injection**: ConfigProtocol integration for settings
- **Connection Testing**: Validates Redis connectivity during setup
- **Detailed Logging**: All operations logged with context

## Accumulation Operations

### Addition Operation
```json
// Input
{
  "key": "user_score",
  "value": 25.5,
  "operation": "add"
}

// Output
{
  "operation": "add",
  "key": "user_score",
  "input_value": 25.5,
  "new_total": 125.5,
  "success": true,
  "redis_host": "localhost",
  "redis_port": 6379,
  "original_data": {...}
}
```

### Multiplication Operation
```json
// Input
{
  "key": "multiplier",
  "value": 2.0,
  "operation": "multiply"
}

// Output (uses Lua script for atomicity)
{
  "operation": "multiply",
  "key": "multiplier",
  "input_value": 2.0,
  "new_total": 200.0,
  "success": true
}
```

### Get Total Operation
```json
// Input
{
  "key": "user_score",
  "operation": "get_total"
}

// Output
{
  "operation": "get_total",
  "key": "user_score",
  "new_total": 125.5,
  "success": true
}
```

### Reset Operation
```json
// Input
{
  "key": "user_score",
  "operation": "reset"
}

// Output
{
  "operation": "reset",
  "key": "user_score",
  "new_total": 0.0,
  "success": true
}
```

## Blueprint Examples

### Basic Accumulation Pipeline
```yaml
system:
  name: "accumulation_system"
  components:
    - name: "score_source"
      type: "Source"
    - name: "score_accumulator"
      type: "Accumulator"
      config:
        redis_url: "redis://localhost:6379/0"
    - name: "result_sink"
      type: "Sink"
      
  bindings:
    - from_component: "score_source"
      to_component: "score_accumulator"
      stream_name: "input"
    - from_component: "score_accumulator"
      to_component: "result_sink"
      stream_name: "output"
```

### Multi-Key Accumulation
```yaml
system:
  name: "multi_accumulator"
  components:
    - name: "transaction_stream"
      type: "Source"
    - name: "financial_accumulator"
      type: "Accumulator"
      config:
        host: "redis.production.com"
        port: 6379
        password: "secure_password"
        db: 1
    - name: "balance_reporter"
      type: "Sink"
      
  bindings:
    - from_component: "transaction_stream"
      to_component: "financial_accumulator"
      stream_name: "input"
    - from_component: "financial_accumulator"
      to_component: "balance_reporter"
      stream_name: "output"
```

### Accumulator with Processing Pipeline
```yaml
system:
  name: "processing_accumulation"
  components:
    - name: "events"
      type: "Source"
    - name: "event_filter"
      type: "Filter"
    - name: "accumulator"
      type: "Accumulator"
      config:
        redis_url: "redis://redis-cluster:6379/2"
    - name: "metrics_output"
      type: "Sink"
      
  bindings:
    - from_component: "events"
      to_component: "event_filter"
      stream_name: "input"
    - from_component: "event_filter"
      to_component: "accumulator"
      stream_name: "input"
    - from_component: "accumulator"
      to_component: "metrics_output"
      stream_name: "output"
```

## Configuration Options

### Redis URL Format
```yaml
config:
  redis_url: "redis://[password@]host:port/db"
```

Examples:
- `redis://localhost:6379/0` - No password, default port
- `redis://:mypass@redis.example.com:6379/1` - With password and custom DB
- `redis://redis-cluster:6380/2` - Custom port and DB

### Individual Component Configuration
```yaml
config:
  host: "redis.production.com"
  port: 6379
  password: "production_password"
  db: 3
```

## Error Handling
- **Connection Failures**: Component fails during setup if Redis unavailable
- **URL Fallback**: Tries redis_url first, falls back to individual components
- **Operation Errors**: Invalid operations return error response without crashing
- **Type Validation**: Non-numeric values for accumulation are converted or rejected
- **Comprehensive Logging**: All Redis operations logged with success/failure status

## Performance Characteristics
- **Atomic Operations**: All accumulations use Redis atomic commands
- **Network Overhead**: Each operation requires Redis round-trip
- **Persistence**: State survives component and Redis restarts
- **Concurrency**: Multiple components can safely accumulate to same keys

## Common Issues
**Problem**: "Redis client not connected" error  
**Solution**: Verify Redis server is running and accessible at configured host/port

**Problem**: "Cannot accumulate non-numeric value" error  
**Solution**: Ensure `value` field contains numeric data (int/float/string number)

**Problem**: Connection timeout during setup  
**Solution**: Check network connectivity and Redis server status

**Problem**: Operations failing silently  
**Solution**: Check operation field is valid: "add", "multiply", "get_total", "reset"

## Production Deployment

### Redis High Availability
- Use Redis Cluster or Sentinel for production
- Configure appropriate connection timeouts
- Monitor Redis memory usage for large accumulations

### Security Considerations
- Use Redis AUTH with strong passwords
- Consider Redis over TLS for sensitive data
- Implement key namespace isolation per application

### Monitoring
- Monitor Redis connection health
- Track accumulation operation success rates
- Alert on Redis memory usage thresholds

## Implementation Notes
- Uses `redis.asyncio` for async operations
- Multiplication operations use Lua scripts for atomicity
- Connection testing during setup prevents runtime failures
- Supports both URL and component-based configuration
- All operations include original data in response for traceability

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and tested  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Dependencies**: Redis server required  