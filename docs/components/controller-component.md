# Controller Component (Stream-Based Implementation)

## Overview
Dynamic routing and flow control with two specialized variants: router and terminator.

## Implementation Details
**Base Class**: `Component` (from `autocoder_cc.orchestration.component`)  
**File**: `autocoder_cc/components/controller.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  

## Configuration Schema
```yaml
- name: "flow_controller"
  type: "Controller"
  config:
    variant: "router"             # Required: "router", "terminator"
    routing_rules: {}             # Routing logic (router variant)
    default_output: "default"     # Fallback route (router variant)
    max_items: 10                # Item limit (terminator variant)
    timeout_seconds: 30          # Time limit (terminator variant)
```

## Variants

### Router Variant
**Purpose**: Routes items to different output streams based on content  
**Stream Interface**:
- Input: `input` - Items to route
- Output: Multiple named streams based on routing logic

**Configuration**:
- `routing_rules`: Dictionary of routing rules (optional)
- `default_output`: Fallback stream name (default: "default")

**Behavior**: Analyzes each item and routes to appropriate output stream

**Routing Logic**:
1. **Explicit routing**: Items with `route_to` field
2. **Category-based**: Items with `category` field
3. **Value-based**: Items with numeric `value` field
4. **Type-based**: Items with `type` field
5. **Default**: Fallback to `default_output`

### Terminator Variant
**Purpose**: Controls loop termination based on conditions  
**Stream Interface**:
- Input: `input` - Items to process and count
- Output: `output` - Items forwarded before termination

**Configuration**:
- `max_items`: Maximum items to process (default: 10)
- `timeout_seconds`: Maximum processing time (default: 30)

**Behavior**: Forwards items until termination condition met

**Termination Conditions**:
1. **Item limit**: Reached `max_items` count
2. **Timeout**: Exceeded `timeout_seconds` duration

## Blueprint Examples

### Dynamic Routing by Category
```yaml
system:
  name: "routing_example"
  components:
    - name: "data_source"
      type: "Source"
    - name: "router"
      type: "Controller"
      config:
        variant: "router"
        default_output: "general"
    - name: "priority_sink"
      type: "Sink"
    - name: "bulk_sink"
      type: "Sink"
    - name: "error_sink"
      type: "Sink"
    - name: "general_sink"
      type: "Sink"
      
  bindings:
    - from_component: "data_source"
      to_component: "router"
      stream_name: "input"
    - from_component: "router"
      to_component: "priority_sink"
      stream_name: "priority"
    - from_component: "router"
      to_component: "bulk_sink"
      stream_name: "bulk"
    - from_component: "router"
      to_component: "error_sink"
      stream_name: "errors"
    - from_component: "router"
      to_component: "general_sink"
      stream_name: "general"
```

### Flow Termination Control
```yaml
system:
  name: "termination_example"
  components:
    - name: "data_generator"
      type: "Source"
    - name: "terminator"
      type: "Controller"
      config:
        variant: "terminator"
        max_items: 100
        timeout_seconds: 60
    - name: "processed_sink"
      type: "Sink"
      
  bindings:
    - from_component: "data_generator"
      to_component: "terminator"
      stream_name: "input"
    - from_component: "terminator"
      to_component: "processed_sink"
      stream_name: "output"
```

## Routing Examples

### Message Routing Patterns
```json
// Explicit routing
{
  "data": "important message",
  "route_to": "priority"
}

// Category-based routing
{
  "data": "urgent task",
  "category": "high_priority"
}

// Value-based routing  
{
  "data": "transaction",
  "value": 150
}

// Type-based routing
{
  "data": "user event",
  "type": "analytics"
}
```

### Output Stream Mapping
| Input Condition | Output Stream |
|---|---|
| `route_to: "custom"` | `"custom"` |
| `category: "high_priority"` | `"priority"` |
| `category: "low_priority"` | `"bulk"` |
| `category: "error"` | `"errors"` |
| `value > 100` | `"high_value"` |
| `value > 50` | `"medium_value"` |
| `value ≤ 50` | `"low_value"` |
| `type: "analytics"` | `"analytics_output"` |
| No matching condition | `default_output` |

## Error Handling
- **Invalid variant**: Component initialization fails with clear error message
- **Missing output streams**: Routes to default output with warning
- **Processing errors**: Uses `ConsistentErrorHandler` for comprehensive error management
- **Termination tracking**: Maintains accurate counts even with errors

## Performance Characteristics
- **Router**: O(1) routing decisions, memory usage minimal
- **Terminator**: O(1) termination checks, tracks item count and time
- **Output streams**: Can handle multiple concurrent output streams

## Common Issues
**Problem**: Items not routed correctly  
**Solution**: Verify input items have expected routing fields (`category`, `value`, `type`)

**Problem**: Terminator not stopping  
**Solution**: Check `max_items` and `timeout_seconds` configuration values

**Problem**: Missing output streams  
**Solution**: Ensure all expected output streams are defined in bindings

## Advanced Usage

### Custom Routing Logic
For complex routing needs, extend the `_determine_output_stream` method or use explicit `route_to` fields in your data.

### Termination Monitoring
The terminator variant logs detailed information about why termination occurred:
- Item count reached: `"Item limit reached: 100/100"`
- Timeout reached: `"Timeout reached: 60.15s/60s"`

## Implementation Notes
- Router maintains no internal state between items
- Terminator tracks processing start time and item count
- Both variants use `ConsistentErrorHandler` for error management
- Items are forwarded immediately in terminator variant (no buffering)

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and tested  
**Blueprint Format**: Stream-based (uses `bindings`)  