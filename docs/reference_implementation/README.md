# Reference Implementation - GOLDEN STANDARD

## Purpose

This is the **GOLDEN STANDARD** reference implementation that shows exactly how components should be structured and how the system should work. All generated code must match this pattern.

## Key Design Decisions

### 1. Component Interface
Components inherit from `ComposedComponent` and implement:
- `__init__(name, config)` - Initialize with name and configuration
- `async setup(harness_context)` - Setup component (called by harness)
- `async process()` - Main processing loop (runs continuously)
- `async cleanup()` - Cleanup resources (called on shutdown)
- `get_health_status()` - Return health status dictionary

### 2. Component Communication
- Components communicate via direct method calls (`process_item()`)
- Bindings are established during initialization
- Components get references to other components they depend on

### 3. System Orchestration
The main.py orchestrates:
1. Loading configuration
2. Creating component instances
3. Establishing bindings
4. Calling setup() on all components
5. Starting process() tasks for all components
6. Monitoring health
7. Graceful shutdown via cleanup()

## File Structure

```
reference_implementation/
├── README.md                 # This file
├── config.yaml              # System configuration
├── main.py                  # System orchestrator
├── components/
│   ├── __init__.py
│   ├── task_store.py        # Store component (data persistence)
│   └── task_api.py          # API endpoint component
└── tests/
    └── test_reference.py    # Tests to verify it works
```

## Running the Reference Implementation

### 1. Direct Execution
```bash
cd reference_implementation
python main.py
```

### 2. With Custom Config
```bash
python main.py custom_config.yaml
```

### 3. Testing
```bash
pytest tests/test_reference.py -v
```

## Component Details

### TaskStore Component

**Purpose**: Manages data persistence for tasks

**Key Methods**:
- `process_item(item)` - Handles CRUD operations
- `add_item(item)` - Adds item to processing queue

**Supported Actions**:
- `create` - Create new task
- `get` - Retrieve task by ID
- `update` - Update existing task
- `delete` - Delete task
- `list` - List all tasks

**Configuration**:
```yaml
task_store:
  type: Store
  config:
    storage_type: memory  # or file, sqlite, postgres
```

### TaskAPI Component

**Purpose**: Provides REST API for task management

**Endpoints**:
- `GET /health` - Health check
- `GET /tasks` - List all tasks
- `POST /tasks` - Create new task
- `GET /tasks/{id}` - Get specific task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

**Configuration**:
```yaml
task_api:
  type: APIEndpoint
  config:
    port: 8080
    host: 0.0.0.0
```

## Validation Checklist

The reference implementation must pass these checks:

- [ ] Components inherit from `ComposedComponent`
- [ ] Components implement required methods (setup, process, cleanup)
- [ ] Components can be instantiated with config
- [ ] Components can communicate via bindings
- [ ] System can initialize all components
- [ ] System can run all components concurrently
- [ ] System can shutdown gracefully
- [ ] API endpoints are accessible
- [ ] Data operations work (CRUD)
- [ ] Health checks return correct status

## Testing the Implementation

### Manual Testing

1. **Start the system**:
```bash
python main.py
```

2. **Test API endpoints**:
```bash
# Health check
curl http://localhost:8080/health

# Create task
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "description": "Testing the system"}'

# List tasks
curl http://localhost:8080/tasks

# Get specific task
curl http://localhost:8080/tasks/1

# Update task
curl -X PUT http://localhost:8080/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Task", "completed": true}'

# Delete task
curl -X DELETE http://localhost:8080/tasks/1
```

3. **Shutdown gracefully**: Press Ctrl+C

### Automated Testing

Run the test suite:
```bash
pytest tests/test_reference.py -v
```

## What Makes This the Golden Standard?

1. **Simplicity**: Minimal dependencies, clear structure
2. **Correctness**: Follows actual expected interfaces
3. **Completeness**: Fully functional, not mocked
4. **Testability**: Can be validated end-to-end
5. **Clarity**: Well-documented and easy to understand

## Using as Template for Generation

When generating new components:

1. Copy the exact structure
2. Match the method signatures
3. Follow the same patterns
4. Maintain the same interface
5. Keep the same configuration approach

## Common Pitfalls to Avoid

1. **Don't use wrong base class** - Must inherit from `ComposedComponent`
2. **Don't skip required methods** - All three (setup, process, cleanup) are required
3. **Don't use wrong method names** - It's `cleanup()` not `teardown()`
4. **Don't forget async** - All lifecycle methods are async
5. **Don't ignore harness_context** - Setup receives context with component references

## Success Criteria

This reference implementation is successful when:

1. ✅ It runs without errors
2. ✅ All API endpoints work
3. ✅ Data persistence works
4. ✅ Components communicate correctly
5. ✅ System shuts down gracefully
6. ✅ Tests pass
7. ✅ It can be used as a template for generation