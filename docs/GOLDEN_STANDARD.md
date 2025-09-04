# GOLDEN STANDARD - Reference Implementation

## Overview

This document describes the **GOLDEN STANDARD** reference implementation that all generated code must follow. This implementation has been tested and verified to work correctly end-to-end.

## Location

- **Primary**: `/reference_implementation/`
- **Documentation Copy**: `/docs/reference_implementation/`

## Key Architecture Decisions

### 1. Component Base Class
All components inherit from `ComposedComponent`:
```python
from autocoder_cc.components.composed_base import ComposedComponent

class TaskStore(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
```

### 2. Component Lifecycle Methods
Components implement these async methods:
- `async def setup(self, harness_context)` - Initialize component
- `async def process(self)` - Main processing loop (runs continuously)
- `async def cleanup(self)` - Cleanup resources

### 3. Data Processing Method
Components that process data implement:
```python
async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single item"""
```

### 4. Health Status
Components provide health status:
```python
def get_health_status(self) -> Dict[str, Any]:
    return {
        'healthy': self.running,
        'task_count': len(self.tasks),
        ...
    }
```

## Component Communication Pattern

### Direct Binding
Components communicate via direct method calls:
```python
# In API component
result = await self.store_component.process_item({
    'action': 'create',
    'data': task_data
})
```

### Binding Setup
Bindings are established during initialization:
```yaml
bindings:
  - source: task_api
    target: task_store
    protocol: direct
```

## System Orchestration Pattern

The `main.py` follows this pattern:

1. **Load Configuration**
```python
config = self.load_config(config_path)
```

2. **Create Components**
```python
self.components['task_store'] = TaskStore('task_store', store_config)
self.components['task_api'] = TaskAPI('task_api', api_config)
```

3. **Establish Bindings**
```python
source_comp.set_store_component(target_comp)
```

4. **Setup All Components**
```python
for name, component in self.components.items():
    await component.setup(harness_context)
```

5. **Start Processing**
```python
for name, component in self.components.items():
    task = asyncio.create_task(component.process())
    self.tasks.append(task)
```

6. **Graceful Shutdown**
```python
for name, component in self.components.items():
    await component.cleanup()
```

## Common Pitfalls Resolved

### 1. Metrics Collector Usage
The `metrics_collector.increment()` method signature:
```python
# Correct
self.metrics_collector.increment('tasks_created')

# Wrong
self.metrics_collector.increment('tasks_created', 1, {})
```

### 2. Avoiding Property Conflicts
Use underscore prefix for internal state to avoid conflicts with parent class:
```python
# Correct
self._next_id = 1

# Wrong (conflicts with parent class property)
self.next_id = 1
```

### 3. Error Handling
Always wrap processing in try-except with proper logging:
```python
try:
    # Process item
except Exception as e:
    self.logger.error(f"Error: {e}")
    return {'status': 'error', 'message': str(e)}
```

## Test Results

✅ **All 13 tests pass**:
- 4 TaskStore tests
- 3 TaskAPI tests
- 4 TodoSystem tests
- 2 Integration tests

## Files in Reference Implementation

```
reference_implementation/
├── README.md              # Detailed documentation
├── config.yaml           # System configuration
├── main.py               # System orchestrator
├── components/
│   ├── __init__.py
│   ├── task_store.py     # Store component (✅ tested)
│   └── task_api.py       # API component (✅ tested)
└── tests/
    ├── __init__.py
    └── test_reference.py # Test suite (✅ all pass)
```

## Using as Template

When generating new components:

1. **Copy the exact class structure** from reference components
2. **Use the same method signatures** (setup, process, cleanup)
3. **Follow the same error handling patterns**
4. **Match the configuration approach**
5. **Use the same import statements**

## Validation Checklist

Before declaring any generated system as working:

- [ ] Components inherit from `ComposedComponent`
- [ ] Components have `setup()`, `process()`, `cleanup()` methods
- [ ] Components can be instantiated with config
- [ ] Main.py follows the orchestration pattern
- [ ] Bindings work correctly
- [ ] System starts without errors
- [ ] System shuts down gracefully
- [ ] Tests pass

## Command to Test

```bash
# From project root
python -m pytest reference_implementation/tests/test_reference.py -v

# Result should be: 13 passed
```

## Next Steps

1. **Use this as the template** for all component generation
2. **Update validation** to expect this interface
3. **Fix generation** to produce this structure
4. **Test generated code** against reference tests

This is our **ground truth** - a working system we can point to and say "make it work exactly like this."