# Blueprint Format: Unified Syntax Guide

## 🚨 RECOMMENDED FORMAT

### Use Unified Dot Notation (Optimal)
**When**: All current and future development  
**Status**: ✅ **WORKS NOW** and evolves smoothly to ports  
**Syntax**: Simple `from: "component.port"` notation  
**Parser Support**: Fully supported, extensible with metadata  

### Why This Format:
- ✅ **Already works** in current parser
- ✅ **Most readable**: Clear component.port syntax
- ✅ **Future-proof**: Evolves to typed ports naturally
- ✅ **Single standard**: Not three competing formats  

## 📋 UNIFIED BLUEPRINT FORMAT

### Complete Working Example
```yaml
schema_version: "1.0.0"
system:
  name: "todo_app"
  description: "Todo application using unified syntax"
  
  components:
    - name: "todo_store"
      type: "Store"
      description: "Persistent todo storage"
      config:
        storage_type: "memory"
        
    - name: "todo_api"
      type: "APIEndpoint"
      description: "REST API for todos"
      config:
        port: 8080
        endpoints:
          - path: "/todos"
            methods: ["GET", "POST"]
          - path: "/todos/{id}"
            methods: ["GET", "PUT", "DELETE"]
            
    - name: "todo_processor"
      type: "StreamProcessor"
      description: "Process todo operations"
      config:
        variant: "windowing"
        window_size: 5.0
  
  bindings:
    # RECOMMENDED: Clean dot notation
    - from: "todo_api.output"
      to: "todo_processor.input"
      
    - from: "todo_processor.output"
      to: "todo_store.input"
      
    # Optional metadata for complex cases
    - from: "todo_store.events"
      to: "todo_api.updates"
      transform: "event_to_notification"
      condition: "event.type == 'created'"
```

## 📝 SYNTAX REFERENCE

### Primary Format (Dot Notation)
```yaml
bindings:
  # Simple connection
  - from: "source.output"
    to: "destination.input"
    
  # With optional metadata
  - from: "processor.output"
    to: "store.input"
    transform: "json_to_dict"        # Optional transformation
    condition: "item.priority > 5"   # Optional condition
    retry:                           # Optional retry policy
      attempts: 3
      backoff: exponential
    
  # Fan-out to multiple targets
  - from: "event_source.output"
    to: ["logger.input", "metrics.input", "store.input"]
```

### Alternative Formats (Also Supported)
```yaml
# Explicit format (verbose but clear)
bindings:
  - from_component: "source"
    from_port: "output"
    to_component: "destination"
    to_port: "input"

# Both formats can include the same metadata
  - from_component: "processor"
    from_port: "output"
    to_component: "store"
    to_port: "input"
    transform: "json_to_dict"
    condition: "item.priority > 5"
```

### Common Port Names by Component Type
- **Sources**: Usually send to `"output"` port
- **Transformers**: Expect `"input"` port, send to `"output"` port
- **StreamProcessor**: 
  - Windowing/Deduplication: `"input"` → `"output"`
  - Joining: `"left"`, `"right"` → `"output"`
- **Controller**: 
  - Router: `"input"` → dynamic output port names based on routing rules
  - Terminator: `"input"` → `"output"` (with limits)
- **Model**: Multiple input ports → `"output"`
- **Accumulator**: `"input"` → `"output"`
- **WebSocket**: `"input"` → broadcasts to connected clients
- **Sinks**: Usually expect `"input"` port

## Component-Specific Binding Examples

### StreamProcessor Binding Patterns
```yaml
# Windowing - single input/output
bindings:
  - from_component: "data_source"
    from_port: "output"
    to_component: "windower"
    to_port: "input"
  - from_component: "windower"
    from_port: "output"
    to_component: "output_sink"
    to_port: "input"

# Joining - dual input, single output
bindings:
  - from_component: "left_source"
    from_port: "output"
    to_component: "joiner"
    to_port: "left"
  - from_component: "right_source"
    from_port: "output"
    to_component: "joiner"
    to_port: "right"
  - from_component: "joiner"
    from_port: "output"
    to_component: "result_sink"
    to_port: "input"
```

### Controller Binding Patterns
```yaml
# Router - single input, multiple outputs
bindings:
  - from_component: "data_source"
    from_port: "output"
    to_component: "router"
    to_port: "input"
  - from_component: "router"
    from_port: "priority"
    to_component: "high_priority_sink"
    to_port: "input"
  - from_component: "router"
    from_port: "bulk"
    to_component: "bulk_sink"
    to_port: "input"
  - from_component: "router"
    from_port: "default"
    to_component: "default_sink"
    to_port: "input"
```

### Model Multi-Stream Pattern
```yaml
# Model with multiple input streams
bindings:
  - from_component: "training_data"
    from_port: "output"
    to_component: "ml_model"
    to_port: "training"
  - from_component: "test_data"
    from_port: "output"
    to_component: "ml_model"
    to_port: "testing"
  - from_component: "ml_model"
    from_port: "output"
    to_component: "predictions_sink"
    to_port: "input"
```

## Complex Pipeline Examples

### Data Processing Pipeline
```yaml
system:
  name: "data_processing_pipeline"
  components:
    - name: "raw_data"
      type: "Source"
    - name: "data_filter"
      type: "Filter"
    - name: "data_processor"
      type: "StreamProcessor"
      config:
        variant: "windowing"
        window_size: 10.0
    - name: "ml_analyzer"
      type: "Model"
      config:
        model_type: "analytics"
    - name: "result_router"
      type: "Controller"
      config:
        variant: "router"
    - name: "high_value_store"
      type: "Store"
    - name: "standard_store"
      type: "Store"
      
  bindings:
    - from_component: "raw_data"
      from_port: "output"
      to_component: "data_filter"
      to_port: "input"
    - from_component: "data_filter"
      from_port: "output"
      to_component: "data_processor"
      to_port: "input"
    - from_component: "data_processor"
      from_port: "output"
      to_component: "ml_analyzer"
      to_port: "input"
    - from_component: "ml_analyzer"
      from_port: "output"
      to_component: "result_router"
      to_port: "input"
    - from_component: "result_router"
      from_port: "high_value"
      to_component: "high_value_store"
      to_port: "input"
    - from_component: "result_router"
      from_port: "default"
      to_component: "standard_store"
      to_port: "input"
```

### Real-Time Monitoring System
```yaml
system:
  name: "realtime_monitoring"
  components:
    - name: "metrics_collector"
      type: "Source"
    - name: "metrics_accumulator"
      type: "Accumulator"
      config:
        redis_url: "redis://localhost:6379/0"
    - name: "alert_processor"
      type: "StreamProcessor"
      config:
        variant: "deduplication"
        dedup_key: "alert_id"
    - name: "websocket_broadcaster"
      type: "WebSocket"
      config:
        port: 8080
        max_connections: 200
    - name: "metrics_store"
      type: "Store"
      
  bindings:
    - from_component: "metrics_collector"
      from_port: "output"
      to_component: "metrics_accumulator"
      to_port: "input"
    - from_component: "metrics_accumulator"
      from_port: "output"
      to_component: "alert_processor"
      to_port: "input"
    - from_component: "alert_processor"
      from_port: "output"
      to_component: "websocket_broadcaster"
      to_port: "input"
    - from_component: "metrics_accumulator"
      from_port: "output"
      to_component: "metrics_store"
      to_port: "input"
```

## Port-Based Format (FUTURE - DON'T USE YET)

### Complete Example (For Reference Only)
```yaml
schema_version: "2.0.0"  # Future version
system:
  name: "todo_app_ports"
  description: "Todo application using future port-based model"
  
  components:
    - name: "todo_store"
      type: "Store"
      ports:
        data_input:
          semantic_class: "data_in"
          schema: "TodoSchema"
        query_input:
          semantic_class: "query_in"
          schema: "QuerySchema"
        data_output:
          semantic_class: "data_out"
          schema: "TodoSchema"
          
    - name: "todo_api"
      type: "APIEndpoint"
      ports:
        request_input:
          semantic_class: "request_in"
          schema: "HTTPRequestSchema"
        data_output:
          semantic_class: "data_out"
          schema: "TodoSchema"
  
  connections:  # NOT "bindings"
    - from_port: "todo_api.data_output"
      to_port: "todo_store.data_input"
      validation:
        schema_check: true
        type_safety: true
```

### Port-Based Syntax Rules (Future)
```yaml
connections:  # NOT "bindings"
  - from_port: "component.port_name"    # Explicit port specification
    to_port: "component.port_name"      # Explicit port specification
    validation:                         # Schema validation rules
      schema_check: true
      type_safety: true
```

## Migration Phases

### Current Phase: Stream Foundation
- **Status**: Production ready
- **Action**: Use dot notation for all blueprints
- **Focus**: Build working systems with proven patterns

### Next Phase: Type Enhancement
- **Status**: Planning stage
- **Action**: Add optional type wrappers to streams
- **Focus**: Gradual type safety without breaking changes

### Future Phase: Port Abstraction
- **Status**: Design stage  
- **Action**: Introduce port aliases over streams
- **Focus**: Both syntaxes work simultaneously

### Long-term Vision: Unified Ports
- **Status**: Research stage
- **Action**: Full port model with schema validation
- **Focus**: Optional migration, legacy support maintained

## Common Pitfalls

### Wrong Format Usage
```yaml
# ❌ WRONG - Don't mix formats
bindings:
  - from_port: "component.output"    # Port syntax in stream format
    to_port: "other.input"
    
connections:
  - from_component: "source"         # Stream syntax in port format
    to_component: "sink"
```

```yaml
# ✅ CORRECT - Use consistent stream format
bindings:
  - from_component: "source"
    from_port: "output"
    to_component: "sink"
    to_port: "input"
```

### Missing Port Specifications
```yaml
# ❌ WRONG - Missing port specifications
bindings:
  - from_component: "source"
    to_component: "processor"
    
# ✅ CORRECT - Include explicit port specifications
bindings:
  - from_component: "source"
    from_port: "output"
    to_component: "processor"
    to_port: "input"
```

### Invalid Component References
```yaml
# ❌ WRONG - Component not defined
bindings:
  - from_component: "undefined_component"
    from_port: "output"
    to_component: "processor"
    to_port: "input"
    
# ✅ CORRECT - Component must be defined in components section
components:
  - name: "data_source"
    type: "Source"
bindings:
  - from_component: "data_source"
    from_port: "output"
    to_component: "processor"
    to_port: "input"
```

## Blueprint Validation

### Validation Commands
```bash
# Validate blueprint syntax
autocoder validate examples/todo_app.yaml

# Test component instantiation
autocoder test-components examples/todo_app.yaml

# Generate system from blueprint
autocoder generate examples/todo_app.yaml
```

### Common Validation Errors
- **Component not found**: Referenced component not in components section
- **Invalid port name**: Port name not supported by target component
- **Missing port specification**: Binding missing from_port or to_port fields
- **Circular dependencies**: Components forming circular reference loops
- **Missing required config**: Component missing required configuration fields

---
**Last Updated**: 2025-08-03  
**Current Status**: Stream-based format active and working  
**Future Status**: Port-based format planned for 2025  
**Recommendation**: Use stream-based format for all current development  