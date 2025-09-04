# Migration Guide: StandaloneComponentBase to ComposedComponent

## Overview

This guide helps you migrate components from the deprecated `StandaloneComponentBase` to the correct `ComposedComponent` base class.

## Key Changes

### Base Class

**Before:**
```python
from autocoder_cc.components.standalone_base import StandaloneComponentBase

class MyComponent(StandaloneComponentBase):
    pass
```

**After:**
```python
from autocoder_cc.components.composed_base import ComposedComponent

class MyComponent(ComposedComponent):
    pass
```

### Lifecycle Methods

**Before:**
```python
class MyComponent(StandaloneComponentBase):
    def setup(self):
        # Initialize
        pass
    
    def process(self, item):
        # Process synchronously
        return result
    
    def teardown(self):
        # Clean up
        pass
```

**After:**
```python
class MyComponent(ComposedComponent):
    def setup(self):
        # Initialize (same)
        pass
    
    async def process_item(self, item: Any) -> Any:
        # Process asynchronously
        return result
    
    def cleanup(self):
        # Clean up (renamed from teardown)
        pass
```

### Component Structure

**Reference Implementation:**
```python
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent

class GeneratedStore_MyStore(ComposedComponent):
    """Store component using ComposedComponent pattern."""
    
    def __init__(self, name: str = "my_store", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        # Initialize internal state with underscore prefix
        self._storage = {}
        self._next_id = 1
        
    def setup(self):
        """Initialize component resources."""
        self.logger.info(f"Setting up {self.name}")
        self._status = 'healthy'
        
    async def process_item(self, item: Any) -> Any:
        """Process store operations asynchronously."""
        action = item.get('action', 'unknown')
        
        if action == 'create':
            item_id = f"item_{self._next_id}"
            self._next_id += 1
            self._storage[item_id] = item.get('data')
            self.metrics_collector.increment('items_created')
            return {'status': 'created', 'id': item_id}
            
        elif action == 'get':
            item_id = item.get('id')
            if item_id in self._storage:
                return {'status': 'found', 'data': self._storage[item_id]}
            return {'status': 'not_found', 'id': item_id}
            
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
            
    def cleanup(self):
        """Clean up resources."""
        self.logger.info(f"Cleaning up {self.name}")
        self._storage.clear()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Return component health status."""
        return {
            'status': self._status,
            'component': self.name,
            'items_count': len(self._storage),
            'timestamp': 'current_time'
        }
```

## API Component with Bindings

**Reference Implementation:**
```python
class GeneratedAPI_MyAPI(ComposedComponent):
    """API component with store binding."""
    
    def __init__(self, name: str = "my_api", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        self.port = config.get('port', 8080) if config else 8080
        self.store_component = None
        
    def set_store_component(self, store):
        """Bind store component for data operations."""
        self.store_component = store
        self.logger.info(f"Bound store {store.name} to API {self.name}")
        
    async def process_item(self, item: Any) -> Any:
        """Process API requests."""
        if not self.store_component:
            return {'status': 'error', 'message': 'No store component bound'}
            
        action = item.get('action')
        
        if action == 'create_item':
            # Forward to store
            store_request = {
                'action': 'create',
                'data': item.get('data')
            }
            return await self.store_component.process_item(store_request)
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
```

## Key Differences

### 1. Async Processing
- `process_item` is now `async` and returns `Any`
- Use `await` when calling other components

### 2. Method Names
- `teardown()` → `cleanup()`
- `process()` → `async process_item()`

### 3. Internal State
- Use underscore prefix for internal variables (e.g., `self._storage`)
- Prevents conflicts with base class attributes

### 4. Metrics API
- Use `self.metrics_collector.increment(name)` not `increment(name, value, tags)`
- Simpler API for common operations

### 5. Error Handling
- Use `self.handle_error(exception, context)` for consistent error handling
- Returns error responses rather than raising exceptions

## Common Patterns

### Store Components
- Implement CRUD operations via action-based dispatch
- Return consistent status codes: 'created', 'found', 'not_found', 'updated', 'deleted'
- Track metrics for each operation type

### API Components
- Include `set_store_component()` method for binding
- Check if store is bound before processing
- Transform API requests to store operations

### Processing Components
- Accept any input type via `process_item`
- Return processed results with status
- Handle errors gracefully

## Testing Your Migration

### Unit Tests
```python
import unittest
import asyncio

class TestMigratedComponent(unittest.TestCase):
    def test_component_inheritance(self):
        """Verify component uses ComposedComponent."""
        from my_component import MyComponent
        from autocoder_cc.components.composed_base import ComposedComponent
        
        component = MyComponent("test")
        self.assertIsInstance(component, ComposedComponent)
        
    def test_async_processing(self):
        """Test async process_item method."""
        component = MyComponent("test")
        
        async def test():
            result = await component.process_item({'test': 'data'})
            return result
            
        result = asyncio.run(test())
        self.assertIsNotNone(result)
        
    def test_lifecycle_methods(self):
        """Verify lifecycle methods exist."""
        component = MyComponent("test")
        
        # Should have these methods
        self.assertTrue(hasattr(component, 'setup'))
        self.assertTrue(hasattr(component, 'cleanup'))
        self.assertTrue(hasattr(component, 'process_item'))
        
        # Should NOT have old methods
        self.assertFalse(hasattr(component, 'teardown'))
```

### Integration Tests
```python
def test_component_binding():
    """Test component binding pattern."""
    store = MyStore("store")
    api = MyAPI("api")
    
    # Bind components
    api.set_store_component(store)
    
    # Test integration
    async def test():
        result = await api.process_item({
            'action': 'create_item',
            'data': {'test': 'value'}
        })
        return result
        
    result = asyncio.run(test())
    assert result['status'] == 'created'
```

## Validation Checklist

- [ ] All components inherit from `ComposedComponent`
- [ ] No references to `StandaloneComponentBase` remain
- [ ] `process_item` is async and returns Any
- [ ] Uses `cleanup()` not `teardown()`
- [ ] Internal state uses underscore prefix
- [ ] API components have `set_store_component()` method
- [ ] Store components return consistent status codes
- [ ] All tests pass with new pattern

## Resources

- [Reference Implementation](/reference_implementation/)
- [Component Base Classes](/autocoder_cc/components/composed_base.py)
- [Test Examples](/tests/unit/core/)
- [CLAUDE.md](/CLAUDE.md) - Current task list