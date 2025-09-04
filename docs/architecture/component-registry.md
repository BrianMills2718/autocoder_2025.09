# Component Registry Architecture

**Created**: 2025-08-29  
**Status**: Investigation Complete  
**Issue**: Registry design mismatch between classes and instances

## Overview

The ComponentRegistry manages component types and instances for the AutoCoder4_CC system. It follows a "V5.0 Validation-Driven Architecture" with fail-hard principles.

## Key Design

The registry maintains two separate collections:

1. **Component Classes** (`_component_classes`)
   - Stores component type definitions (e.g., Source, Transformer, Sink)
   - Populated at initialization via `_register_builtin_components()`
   - All 13 component types are registered as `ComposedComponent` class

2. **Component Instances** (`_component_instances`)
   - Stores created component instances
   - Empty at startup
   - Populated when `create_component()` is called

## The Problem

### Current Behavior
```python
# At initialization
component_registry._component_classes = {
    "Source": ComposedComponent,
    "Transformer": ComposedComponent,
    "Sink": ComposedComponent,
    # ... all 13 types
}

component_registry._component_instances = {}  # Empty!

# When diagnostic calls get_component("Source")
def get_component(self, name: str):
    if name not in self._component_instances:  # Looks in instances, not classes
        raise ComponentRegistryError("Component 'Source' not found")
```

### Root Cause
The diagnostic script tries to use `get_component()` to retrieve component classes, but this method only returns instances. There's no method to get component classes directly.

## Methods Available

- `register_component_class(type, class)` - Register a component type
- `create_component(name, type, config)` - Create and register an instance
- `get_component(name)` - Get a created instance by name
- `list_component_types()` - List registered component types
- **MISSING**: `get_component_class(type)` - Get class by type

## Component Requirements

The registry expects components to have these methods:
- `get_required_config_fields()` - Return list of required config fields
- `get_required_dependencies()` - Return list of required dependencies
- `get_config_requirements()` - **NOT MENTIONED** in registry code

The `get_config_requirements()` method we're looking for is not part of the registry's validation system. This suggests it might be:
1. Defined in individual component implementations
2. Part of a different validation system
3. Not yet implemented

## Solution Options

### Option 1: Add `get_component_class()` Method
```python
def get_component_class(self, component_type: str) -> Type[ComposedComponent]:
    """Get registered component class by type"""
    if component_type not in self._component_classes:
        raise ComponentRegistryError(
            f"Component type '{component_type}' not registered"
        )
    return self._component_classes[component_type]
```

### Option 2: Use Existing `components` Property
The registry already has a public accessor:
```python
@property
def components(self) -> Dict[str, Type[ComposedComponent]]:
    """Public accessor for component classes - required for tests"""
    return self._component_classes
```

We can use: `component_registry.components["Source"]`

### Option 3: Create Test Instances
Use `create_component()` to create instances, then check their methods:
```python
instance = component_registry.create_component("test_source", "Source", {})
has_method = hasattr(instance.__class__, 'get_config_requirements')
```

## ComposedComponent Design

All component types are registered as `ComposedComponent`, which suggests:
- Components use composition over inheritance
- Behavior is determined by configuration and capabilities
- All types share the same base class

This means `get_config_requirements()` would need to be:
1. Defined in `ComposedComponent` base class
2. Implemented differently based on component type
3. Or not exist at all (using different validation approach)

## Recommendations

1. **Immediate Fix**: Update diagnostic to use `component_registry.components` property
2. **Investigation Needed**: Check if `ComposedComponent` has `get_config_requirements()`
3. **Design Question**: Should we add type-specific classes or keep composition approach?

## V5.0 Philosophy

The "V5.0" mentions throughout the code indicate:
- Fail-hard validation (no fallbacks)
- Explicit registration required
- No partial initialization
- Complete configuration required (no defaults)

This is a design philosophy, not a version conflict issue.