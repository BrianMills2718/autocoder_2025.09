# StreamProcessor Component (Stream-Based Implementation)

## Overview
Real-time stream processing with three specialized variants: windowing, joining, and deduplication.

## Implementation Details
**Base Class**: `Component` (from `autocoder_cc.orchestration.component`)  
**File**: `autocoder_cc/components/stream_processor.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Registry**: Registered as `ComposedComponent` in component registry  

## Configuration Schema
```yaml
- name: "event_processor"
  type: "StreamProcessor"
  config:
    variant: "windowing"           # Required: "windowing", "joining", "deduplication"
    window_size: 5.0              # Seconds (windowing variant only)
    join_key: "id"                # Field name (joining variant only)  
    dedup_key: "id"               # Field name (deduplication variant only)
```

## Variants

### Windowing Variant
**Purpose**: Groups messages into time-based windows  
**Stream Interface**:
- Input: `input` - Continuous message stream
- Output: `output` - Window results when time threshold reached

**Configuration**:
- `window_size`: Time window in seconds (default: 5.0)

**Behavior**: Collects messages for specified time, emits window when time expires

**Output Format**:
```json
{
  "window_start": 1691234567.89,
  "window_end": 1691234572.89,
  "items": [
    {"id": 1, "data": "item1"},
    {"id": 2, "data": "item2"}
  ],
  "count": 2
}
```

### Joining Variant  
**Purpose**: Joins messages from two input streams by key  
**Stream Interface**:
- Input: `left`, `right` - Two streams to join
- Output: `output` - Joined messages when keys match

**Configuration**:
- `join_key`: Field name to match between streams (default: "id")

**Behavior**: Buffers messages from both streams, emits join when matching keys found

**Output Format**:
```json
{
  "join_key": "user123",
  "left": {"id": "user123", "name": "John"},
  "right": {"id": "user123", "order": "order456"},
  "joined_at": 1691234567.89
}
```

### Deduplication Variant
**Purpose**: Removes duplicate messages from stream  
**Stream Interface**:
- Input: `input` - Stream with potential duplicates
- Output: `output` - Unique messages only

**Configuration**:
- `dedup_key`: Field to check for duplicates (default: entire message)

**Behavior**: Tracks seen messages, only forwards new unique messages

## Blueprint Examples

### Time-Based Windowing
```yaml
system:
  name: "windowing_example"
  components:
    - name: "event_source"
      type: "Source"
      config:
        source_type: "timer"
        interval: 1
    - name: "windower"
      type: "StreamProcessor"
      config:
        variant: "windowing"
        window_size: 10.0
    - name: "window_sink"
      type: "Sink"
      
  bindings:
    - from_component: "event_source"
      to_component: "windower"
      stream_name: "input"
    - from_component: "windower"
      to_component: "window_sink"
      stream_name: "output"
```

### Stream Joining
```yaml
system:
  name: "joining_example"
  components:
    - name: "user_stream"
      type: "Source"
    - name: "order_stream"  
      type: "Source"
    - name: "joiner"
      type: "StreamProcessor"
      config:
        variant: "joining"
        join_key: "user_id"
    - name: "joined_sink"
      type: "Sink"
      
  bindings:
    - from_component: "user_stream"
      to_component: "joiner"
      stream_name: "left"
    - from_component: "order_stream"
      to_component: "joiner"
      stream_name: "right"
    - from_component: "joiner"
      to_component: "joined_sink"
      stream_name: "output"
```

### Deduplication Processing
```yaml
system:
  name: "deduplication_example"
  components:
    - name: "data_source"
      type: "Source"
    - name: "deduplicator"
      type: "StreamProcessor"
      config:
        variant: "deduplication"
        dedup_key: "transaction_id"
    - name: "unique_sink"
      type: "Sink"
      
  bindings:
    - from_component: "data_source"
      to_component: "deduplicator"
      stream_name: "input"
    - from_component: "deduplicator"
      to_component: "unique_sink"
      stream_name: "output"
```

## Error Handling
- **Invalid variant**: Component initialization fails with clear error message
- **Missing streams**: Logs warning and gracefully handles missing input streams
- **Processing errors**: Uses `ConsistentErrorHandler` for comprehensive error management

## Performance Characteristics
- **Windowing**: Memory usage scales with window size and message volume
- **Joining**: Memory usage scales with buffer size (unbounded without TTL)
- **Deduplication**: Memory usage scales with unique message count (unbounded without TTL)

## Common Issues
**Problem**: "KeyError: 'input'" during processing  
**Solution**: Ensure binding provides expected stream name for variant

**Problem**: High memory usage in joining variant  
**Solution**: Consider implementing TTL for join buffers or process smaller batches

**Problem**: Duplicate detection not working  
**Solution**: Verify `dedup_key` field exists in input messages

## Implementation Notes
- All variants use `ConsistentErrorHandler` for error management
- Windowing emits final window on stream end or component cleanup
- Joining buffers are cleared after successful joins
- Deduplication maintains seen items set in memory (consider external storage for large volumes)

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and tested  
**Blueprint Format**: Stream-based (uses `bindings`)  