# Resource Conflict Detection Rules

**Date**: 2025-08-30  
**Status**: Implemented  
**Component**: Validation Healing Strategies

## Overview

Resource conflict detection prevents the validation healing system from creating configurations that would conflict with already-used resources in the system. This ensures that multiple components don't try to use the same port, database URL, file path, or other exclusive resources.

## How It Works

### 1. Resource Extraction
During context building, the `PipelineContextBuilder.extract_used_resources()` method scans all components in the blueprint and extracts their configured resources into categories:

- **Ports**: Network ports used by services
- **Database URLs**: Database connection strings
- **File Paths**: File system paths for logs, data, etc.
- **API Paths**: REST API base paths and endpoints
- **Queue Names**: Message queue identifiers
- **Topic Names**: Pub/sub topic identifiers
- **Environment Variables**: Environment variable names

### 2. Conflict Detection
When healing strategies (DefaultValueStrategy, ExampleBasedStrategy) attempt to provide values, they check if the proposed value conflicts with already-used resources:

```python
def _has_conflict(self, field: str, value: Any, context: PipelineContext) -> bool:
    """Check if the value conflicts with already used resources"""
    # Check appropriate resource category based on field name
    # Return True if conflict detected
```

### 3. Strategy Fallback
If a conflict is detected, the strategy returns `None` instead of the conflicting value, which triggers the next healing strategy in the chain:

1. **DefaultValueStrategy** - Try default value, skip if conflicts
2. **ExampleBasedStrategy** - Try example value, skip if conflicts  
3. **ContextBasedStrategy** - Infer from context (conflict-aware)
4. **LLMGenerationStrategy** - Generate unique value with LLM

## Conflict Detection Rules

### Port Fields
**Field Names**: `port`, `server_port`, `listen_port`, `bind_port`  
**Resource Category**: `ports`  
**Conflict Type**: Exact match  
**Example**: Component A uses port 8080, Component B cannot use port 8080

### Database URL Fields
**Field Names**: `database_url`, `db_url`, `connection_string`, `postgres_url`, `mysql_url`  
**Resource Category**: `database_urls`  
**Conflict Type**: Exact match  
**Example**: Multiple components shouldn't connect to the same database with potential schema conflicts

### File Path Fields
**Field Names**: `file_path`, `input_path`, `output_path`, `log_path`, `data_file`, `output_file`  
**Resource Category**: `file_paths`  
**Conflict Type**: Exact match  
**Example**: Two components shouldn't write to the same log file

### API Path Fields
**Field Names**: `base_path`, `api_path`, `endpoint`, `route`  
**Resource Category**: `api_paths`  
**Conflict Type**: Exact match  
**Example**: Two API endpoints shouldn't use the same base path

### Queue/Topic Fields
**Field Names (Queues)**: `queue_name`, `queue`  
**Field Names (Topics)**: `topic_name`, `topic`, `channel`  
**Resource Categories**: `queue_names`, `topic_names`  
**Conflict Type**: Exact match within and across categories  
**Example**: Queue names and topic names share namespace to prevent confusion

### Environment Variable Fields
**Field Names**: `env_var`, `environment_variable`, `env_name`  
**Resource Category**: `environment_variables`  
**Conflict Type**: Exact match  
**Special Handling**: Also detects `${VAR_NAME}` syntax in values

## Implementation Details

### Resource Extraction
```python
def extract_used_resources(self, blueprint: Dict[str, Any]) -> Dict[str, set]:
    """Extract all used resources from components in blueprint"""
    resources = {
        "ports": set(),
        "database_urls": set(),
        "file_paths": set(),
        "api_paths": set(),
        "queue_names": set(),
        "topic_names": set(),
        "environment_variables": set()
    }
    
    # Scan all component configs
    for component in BlueprintContract.get_components(blueprint):
        config = component.get('config', {})
        # Extract resources based on field names...
```

### Conflict Checking
```python
def _has_conflict(self, field: str, value: Any, context: PipelineContext) -> bool:
    """Check if the value conflicts with already used resources"""
    # Backwards compatibility
    if not hasattr(context, 'used_resources') or not context.used_resources:
        return False
    
    # Check based on field name patterns
    if field in ['port', 'server_port', ...]:
        if value in context.used_resources.get('ports', set()):
            return True
    # ... more checks
```

## Benefits

1. **Prevents Runtime Failures**: Catches port binding errors at configuration time
2. **Automatic Resolution**: System automatically tries next strategy when conflict detected
3. **LLM Awareness**: When LLM is invoked, it receives full context of used resources
4. **Backwards Compatible**: Works with old contexts that don't have resource tracking
5. **Extensible**: Easy to add new resource types and field patterns

## Testing

Comprehensive test coverage in `tests/unit/validation/test_conflict_detection.py`:

- Port conflict detection
- Database URL conflict detection  
- File path conflict detection
- API path conflict detection
- Queue/topic name conflict detection
- Multiple field name variants
- Empty resource handling
- Backwards compatibility

## Future Enhancements

1. **Port Range Detection**: Detect conflicts in port ranges (e.g., 8080-8090)
2. **Path Prefix Conflicts**: Detect when paths share prefixes (e.g., `/api/v1` and `/api/v1/users`)
3. **Semantic Conflicts**: Use semantic understanding to detect logical conflicts
4. **Resource Reservation**: Allow components to reserve resources before configuration
5. **Conflict Resolution Hints**: Provide suggestions for alternative values

## Usage Example

```python
# Context with used resources
context = PipelineContext(
    system_name="microservices",
    system_description="API Gateway system",
    used_resources={
        "ports": {8080, 3000, 5432},
        "database_urls": {"postgresql://localhost/main"},
        "api_paths": {"/api/v1", "/health"}
    }
)

# Healing will skip conflicting defaults/examples
# and either infer from context or use LLM to generate unique values
healed_config = await healer.heal_configuration(context, requirements, errors)
```

## Related Documentation

- `SYSTEMATIC_OVERHAUL_PLAN_V3.md` - Overall validation enhancement plan
- `docs/architecture/healing-strategy-decision.md` - Healing strategy architecture
- `tests/unit/validation/test_conflict_detection.py` - Test specifications