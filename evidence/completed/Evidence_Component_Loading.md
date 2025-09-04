# Evidence: Component Loading & Discovery Investigation
Date: 2025-08-28  
Component: Uncertainty #1 - Component Loading Mechanism

## Investigation Summary

### How Component Loading Works

1. **Component Type Registration**
   - Component types are registered in `ComponentRegistry` (component_registry.py:95-114)
   - Built-in types: Source, Transformer, Sink, Store, Controller, APIEndpoint, Model, Router, Aggregator, Filter, etc.
   - All component types map to the SAME base class: `ComposedComponent`
   - Example registration:
     ```python
     self.register_component_class("Source", ComposedComponent)
     self.register_component_class("DataSink", ComposedComponent)  
     self.register_component_class("Filter", ComposedComponent)
     ```

2. **Component Type Mapping**
   - `component_type_registry.py` defines COMPONENT_TYPE_REGISTRY with specifications
   - Maps string types like "DataSink" to base classes
   - BUT all types actually use `ComposedComponent` in the registry

3. **Dynamic Component Creation**
   - `create_component()` method in ComponentRegistry:
     - Takes component_type (string), name, and config
     - Looks up class from registry (always ComposedComponent)
     - Creates instance: `component_class(name, config)`
     - Sets component_type attribute on instance

4. **Component Discovery Flow**
   ```
   Blueprint "DataSink" → ComponentRegistry.create_component() 
                        → Look up "DataSink" in registry
                        → Get ComposedComponent class
                        → Create ComposedComponent(name, config)
                        → Set component.component_type = "DataSink"
   ```

## Key Findings

### ✅ RESOLVED: How "DataSink" Maps to Python Class

**Answer**: All component types ("DataSink", "Source", "Filter", etc.) map to the SAME class: `ComposedComponent`

- The component TYPE is just metadata stored in `component.component_type`
- Behavior is determined by:
  1. Configuration passed to component
  2. Capabilities composed based on config
  3. Generated code that might extend ComposedComponent

### Component Class Hierarchy

```
Component (base in orchestration/component.py)
    ↓
ComposedComponent (composed_base.py) - ALL components use this
    - Has capabilities composed based on config
    - Has observability injected
    - Has error handling
```

### Generated Components

When components are generated:
1. They typically inherit from primitive types (Source, Sink, Transformer)
2. These primitive types inherit from ComposedComponent
3. Generated code is standalone and doesn't use the registry directly

## Configuration Access Pattern

Based on examination of ComposedComponent and generated code:

1. **In ComposedComponent**:
   - Config passed to `__init__(name, config)`
   - Stored in `self.config`
   - Accessed as `self.config.get('key', default)`

2. **In Generated Components**:
   - Inherit from base types (Sink, Source, etc.)
   - Access config via `self.config` inherited from parent
   - Example in sink.py:69: `output_config = self.config.get("output", {})`

## Impact on MVP Implementation

### Good News:
1. ✅ All components use same base class (ComposedComponent)
2. ✅ Config access is consistent: `self.config`
3. ✅ Component loading is centralized through ComponentRegistry

### Considerations:
1. Adding `get_required_config_fields()` to ComposedComponent will affect ALL components
2. Component type is just metadata, not a different class
3. Registry already validates some aspects but not config completeness

## Next Investigation Steps

1. ✅ Component loading mechanism understood
2. ⏳ Test impact of modifying ComposedComponent base class
3. ⏳ Verify how generated components would handle new methods
4. ⏳ Check integration points for validation injection