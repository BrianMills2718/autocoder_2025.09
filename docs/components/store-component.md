# Store Component (Stream-Based Implementation)

## Overview
Production-ready data persistence component supporting both in-memory and database storage with comprehensive CRUD operations, direct database integration, and advanced V5.0 features.

## Implementation Details
**Base Class**: `ComposedComponent` (from `autocoder_cc.components.composed_base`)  
**File**: `autocoder_cc/components/store.py`  
**Enhanced Version**: `autocoder_cc/components/v5_enhanced_store.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Dependencies**: databases library for production database connectivity

## Store Variants

### Basic Store Component
**Class**: `Store`  
**Use Case**: General-purpose data persistence with memory and database support  
**Features**: CRUD operations, PostgreSQL/MySQL support, stream processing

### V5.0 Enhanced Store Component  
**Class**: `V5EnhancedStore`  
**Use Case**: Production environments requiring advanced database features  
**Features**: Schema validation, migration management, connection pooling, performance monitoring

## Configuration Schema

### Basic Store Configuration
```yaml
- name: "data_store"
  type: "Store"
  config:
    storage_type: "memory"           # Options: memory, database
    database_type: "postgresql"     # Options: postgresql, mysql
    database_url: "postgresql://user:pass@host:5432/db"  # Direct connection string
    table_name: "data_store"        # Database table name
```

### V5.0 Enhanced Store Configuration
```yaml
- name: "enhanced_store"
  type: "V5EnhancedStore"
  config:
    database:
      type: "postgresql"             # Database type
      connection_string: "postgresql://user:pass@host:5432/db"
      connection_pool:
        min_size: 5
        max_size: 20
      schema:
        tables: ["tasks", "users"]
        migrations:
          - version: "001"
            description: "Initial schema"
            sql: "CREATE TABLE tasks (id SERIAL PRIMARY KEY, data JSONB);"
    testing_mode: false              # Enable for testing without full database
```

## Key Features

### Basic Store Features
- **Memory Storage**: Fast in-memory data storage for development/testing
- **Database Integration**: Direct PostgreSQL and MySQL connectivity
- **CRUD Operations**: Create, Read, Update, Delete, List operations
- **Stream Processing**: Processes data from upstream components
- **Error Handling**: Comprehensive error management with `ConsistentErrorHandler`
- **Task Management**: Built-in task storage functionality for API integration

### V5.0 Enhanced Features
- **Schema Validation**: Real-time database schema validation
- **Migration Management**: Automatic database migration application
- **Connection Pooling**: Configurable database connection pooling
- **Performance Monitoring**: Detailed operation performance tracking
- **Multi-Database Support**: Enhanced PostgreSQL, MySQL, SQLite support
- **Transaction Management**: Advanced transaction handling with rollback support
- **Validation Pipeline**: Comprehensive data and query validation

## CRUD Operations API

### Task Management Interface
Both Store variants implement a consistent task management interface:

```python
# Create task
result = await store.process_item({
    "action": "create",
    "data": {"title": "New Task", "completed": False}
})
# Returns: {"status": "success", "id": "1", "data": {...}}

# Get task
result = await store.process_item({
    "action": "get",
    "id": "1"
})
# Returns: {"status": "success", "data": {...}} or {"status": "not_found"}

# Update task
result = await store.process_item({
    "action": "update",
    "id": "1",
    "data": {"completed": True}
})
# Returns: {"status": "success", "data": {...}} or {"status": "not_found"}

# Delete task
result = await store.process_item({
    "action": "delete",
    "id": "1"
})
# Returns: {"status": "success"} or {"status": "not_found"}

# List all tasks
result = await store.process_item({
    "action": "list"
})
# Returns: {"status": "success", "data": [...]}
```

### Health Status
```python
health = store.get_health_status()
# Returns: {
#   "status": "healthy",
#   "items_count": 10,
#   "storage_type": "memory",
#   "task_count": 5,
#   "next_id": 6
# }
```

## Blueprint Examples

### Basic Memory Store
```yaml
system:
  name: "memory_storage_system"
  components:
    - name: "task_api"
      type: "FastAPIEndpoint"
      config:
        port: 8000
    - name: "task_store"
      type: "Store"
      config:
        storage_type: "memory"
        
  bindings:
    - from_component: "task_api"
      to_component: "task_store"
      stream_name: "input"
```

### Database Store
```yaml
system:
  name: "database_storage_system"
  components:
    - name: "api_server"
      type: "FastAPIEndpoint"
      config:
        port: 8000
    - name: "persistent_store"
      type: "Store"
      config:
        storage_type: "database"
        database_type: "postgresql"
        database_url: "postgresql://postgres:password@localhost:5432/tasks"
        table_name: "application_data"
        
  bindings:
    - from_component: "api_server"
      to_component: "persistent_store"
      stream_name: "input"
```

### V5.0 Enhanced Production Store
```yaml
system:
  name: "production_storage_system"
  components:
    - name: "production_api"
      type: "FastAPIEndpoint"
      config:
        port: 80
    - name: "production_store"
      type: "V5EnhancedStore"
      config:
        database:
          type: "postgresql"
          connection_string: "postgresql://app_user:secure_pass@db-cluster:5432/production_db"
          connection_pool:
            min_size: 10
            max_size: 50
            timeout: 30
          schema:
            tables: ["tasks", "users", "audit_log"]
            migrations:
              - version: "001"
                description: "Initial application schema"
                sql: |
                  CREATE TABLE tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  );
              - version: "002"
                description: "Add user management"
                sql: |
                  CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  );
    - name: "metrics_endpoint"
      type: "MetricsEndpoint"
      config:
        port: 9090
        
  bindings:
    - from_component: "production_api"
      to_component: "production_store"
      stream_name: "input"
```

### Multi-Store System
```yaml
system:
  name: "multi_store_system"
  components:
    - name: "user_api"
      type: "FastAPIEndpoint"
      config:
        port: 8001
    - name: "order_api"
      type: "FastAPIEndpoint"
      config:
        port: 8002
    - name: "user_store"
      type: "Store"
      config:
        storage_type: "database"
        database_type: "postgresql"
        database_url: "postgresql://user:pass@db:5432/users"
        table_name: "user_data"
    - name: "order_store"
      type: "V5EnhancedStore"
      config:
        database:
          type: "postgresql"
          connection_string: "postgresql://user:pass@db:5432/orders"
          schema:
            tables: ["orders", "order_items"]
    - name: "cache_store"
      type: "Store"
      config:
        storage_type: "memory"
        
  bindings:
    - from_component: "user_api"
      to_component: "user_store"
      stream_name: "input"
    - from_component: "order_api"
      to_component: "order_store"
      stream_name: "input"
    - from_component: "user_api"
      to_component: "cache_store"
      stream_name: "cache"
```

## When to Use Each Variant

### Use Basic Store When:
- **Rapid Development**: Need quick setup without complex database requirements
- **Simple Applications**: Basic CRUD operations are sufficient
- **Resource Constraints**: Limited infrastructure or simple deployment requirements
- **Testing/Development**: Fast iteration without database setup overhead
- **Legacy Compatibility**: Existing systems that need straightforward storage

### Use V5.0 Enhanced Store When:
- **Production Systems**: Mission-critical applications requiring reliability
- **Complex Data Requirements**: Need schema validation and migration management
- **High Performance**: Require connection pooling and performance monitoring
- **Enterprise Environments**: Need comprehensive database management features
- **Compliance Requirements**: Need detailed audit trails and validation
- **Scalable Applications**: Planning for growth and operational complexity

## Database Support

### Supported Database Types
| Database | Basic Store | V5.0 Enhanced | Features |
|---|---|---|---|
| **Memory** | ✅ | ✅ (testing) | Fast, no persistence |
| **PostgreSQL** | ✅ | ✅ | Full features, JSONB support |
| **MySQL** | ✅ | ✅ | Full features, JSON support |
| **SQLite** | ❌ | ✅ (testing) | V5.0 testing mode only |

### Connection String Examples
```yaml
# PostgreSQL
database_url: "postgresql://username:password@host:5432/database"

# MySQL
database_url: "mysql://username:password@host:3306/database"

# SQLite (V5.0 testing only)
connection_string: "sqlite:///path/to/database.db"
```

## Advanced Features

### V5.0 Schema Validation
```python
# Automatic schema validation on setup
validation_result = await store.validate_schema_integrity()
# Validates database schema matches blueprint definition

# Data validation before storage
result = await store.store_data_with_validation({
    "id": "task_1",
    "title": "Important Task",
    "timestamp": "2025-08-03T10:00:00Z"
})
```

### V5.0 Migration Management
```python
# Automatic migration application during setup
await store.apply_schema_migrations()

# Migration history tracking
# Migrations are recorded in migration_history table
```

### V5.0 Performance Monitoring
```python
# Get performance summary
summary = store.performance_monitor.get_performance_summary()
# Returns: {
#   "total_operations": 1500,
#   "successful_operations": 1495,
#   "failed_operations": 5,
#   "average_duration": 0.025,
#   "success_rate": 0.997
# }
```

### Testing Mode (V5.0 Enhanced)
```yaml
# Enable testing mode for CI/CD or development
config:
  testing_mode: true  # Uses SQLite instead of production database
```

## Error Handling

### Common Error Scenarios
```python
# Database connection failures
try:
    await store.setup()
except DatabaseConnectionError as e:
    # Handle connection issues
    print(f"Database connection failed: {e}")

# Schema validation failures (V5.0)
try:
    await store.validate_schema_integrity()
except DatabaseSchemaValidationError as e:
    # Handle schema mismatches
    print(f"Schema validation failed: {e}")

# Data validation failures (V5.0)
try:
    result = await store.store_data_with_validation(data)
except DataValidationError as e:
    # Handle invalid data
    print(f"Data validation failed: {e}")
```

### Error Response Patterns
```python
# Consistent error responses
{
    "status": "error",
    "message": "Descriptive error message",
    "error_type": "validation_error"
}

# Not found responses
{
    "status": "not_found",
    "action": "get",
    "id": "non_existent_id"
}
```

## Performance Characteristics

### Basic Store Performance
- **Memory Storage**: <1ms operation latency
- **Database Storage**: 5-50ms depending on database and network
- **Memory Usage**: ~10MB base + stored data
- **Throughput**: 1000+ operations/second for memory, database-dependent for persistence

### V5.0 Enhanced Performance
- **Schema Validation**: +1-5ms per operation
- **Connection Pooling**: Reduces connection overhead by 50-80%
- **Performance Monitoring**: <1ms overhead per operation
- **Memory Usage**: ~30MB base + monitoring data + connection pool

## Common Issues

**Problem**: "Database client not connected" error  
**Solution**: Ensure database configuration is correct and database is accessible

**Problem**: V5.0 setup fails with schema validation errors  
**Solution**: Check database schema matches configuration, run migrations if needed

**Problem**: Memory store losing data  
**Solution**: Memory storage is not persistent - use database storage for persistence

**Problem**: V5.0 testing mode using wrong database  
**Solution**: Ensure `testing_mode: true` is set for test environments

**Problem**: Connection pool exhaustion (V5.0)  
**Solution**: Increase `max_size` in connection pool configuration

## Migration Guide

### From Basic Store to V5.0 Enhanced
```yaml
# Before (Basic Store)
- name: "data_store"
  type: "Store"
  config:
    storage_type: "database"
    database_url: "postgresql://user:pass@host:5432/db"

# After (V5.0 Enhanced)
- name: "data_store"
  type: "V5EnhancedStore"
  config:
    database:
      type: "postgresql"
      connection_string: "postgresql://user:pass@host:5432/db"
      connection_pool:
        min_size: 5
        max_size: 20
      schema:
        tables: ["data_store"]
```

## Production Deployment

### Basic Store Production Setup
```yaml
config:
  storage_type: "database"
  database_type: "postgresql"
  database_url: "postgresql://app_user:${DB_PASSWORD}@db-primary:5432/production"
  table_name: "application_data"
```

### V5.0 Enhanced Production Setup
```yaml
config:
  database:
    type: "postgresql"
    connection_string: "postgresql://app_user:${DB_PASSWORD}@db-cluster:5432/production"
    connection_pool:
      min_size: 10
      max_size: 100
      timeout: 30
    schema:
      tables: ["tasks", "users", "audit_logs"]
      migrations: []  # Managed separately in production
  testing_mode: false
```

### Health Check Integration
```bash
# Check store health via API
curl http://localhost:8000/health

# Expected healthy response
{
  "status": "ok",
  "health": {
    "status": "healthy",
    "store_connected": true,
    "task_count": 150
  }
}
```

## Implementation Notes
- Basic Store: Direct database connections with simple connection management
- V5.0 Enhanced: Advanced database integration with enterprise features
- Both variants: Full CRUD operation support and stream-based integration
- Testing support: V5.0 provides strategic testing mode for CI/CD environments
- Performance: V5.0 includes comprehensive monitoring and optimization features

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Both variants fully implemented and production-ready  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Dependencies**: databases library, PostgreSQL/MySQL drivers  
**Recommendation**: Use V5EnhancedStore for production, basic Store for development/simple use cases