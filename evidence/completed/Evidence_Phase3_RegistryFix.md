# Evidence: Phase 3 - Component Registry Access Fix

**Date**: 2025-08-26  
**Task**: Fix component registry attribute access in tests

## Problem
The smoke test was trying to access `component_registry._registry` but the actual attribute is `_component_classes`.

## Investigation

### Component Registry Implementation
From `component_registry.py`:
```python
class ComponentRegistry:
    def __init__(self, *, lockfile_path: str | None = None):
        # ...
        # Registry of component classes (ComposedComponent-based)
        self._component_classes: Dict[str, Type[ComposedComponent]] = {}
        # ...
    
    @property
    def components(self) -> Dict[str, Type[ComposedComponent]]:
        """Public accessor for component classes - required for tests"""
        return self._component_classes

# Singleton instance at line 1327
component_registry = ComponentRegistry()
```

### Smoke Test Error
```python
# Old code (incorrect):
assert len(component_registry._registry) > 0  # ❌ AttributeError

# Problem: No attribute '_registry', the actual attribute is '_component_classes'
```

## Fix Applied

### Updated smoke_test.py (line 37)
```python
def test_component_registry():
    """Test that component registry initializes"""
    from autocoder_cc.components.component_registry import component_registry
    # Use the public property 'components' instead of private '_registry'
    assert len(component_registry.components) > 0
```

### Additional Fix: Async Test Marker
Also added missing `@pytest.mark.asyncio` decorator to async test in `test_recent_fixes.py` (line 168).

## Verification

The fix correctly:
1. Uses the public `components` property instead of private attribute
2. Accesses the correct underlying `_component_classes` dictionary
3. Follows Python convention of using public properties over private attributes

## Key Learning

Always use public properties when available instead of accessing private attributes directly. The ComponentRegistry provides the `components` property specifically for external access to the registry.