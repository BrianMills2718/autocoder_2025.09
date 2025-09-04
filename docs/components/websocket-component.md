# WebSocket Component (Stream-Based Implementation)

## Overview
Real-time bidirectional communication server with connection management, heartbeat support, and message broadcasting capabilities.

## Implementation Details
**Base Class**: `ComposedComponent` (from `autocoder_cc.components.composed_base`)  
**File**: `autocoder_cc/components/websocket.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Dependencies**: `websockets` library for WebSocket protocol support

## Configuration Schema
```yaml
- name: "realtime_server"
  type: "WebSocket"
  config:
    port: 8080                    # Server port (default: 8080)
    host: "0.0.0.0"              # Bind address (default: 0.0.0.0)
    max_connections: 100         # Maximum concurrent connections (default: 100)
    heartbeat_interval: 30       # Heartbeat ping interval in seconds (default: 30)
```

## Key Features

### Real-Time Server
- **WebSocket Protocol**: Full WebSocket server implementation
- **Connection Management**: Tracks active client connections
- **Message Broadcasting**: Sends data to all connected clients
- **Standalone Capable**: Can run as independent WebSocket server

### Connection Management
- **Connection Limits**: Enforces maximum concurrent connections
- **Automatic Cleanup**: Removes disconnected clients automatically
- **Connection Tracking**: Maintains active client registry
- **Graceful Disconnection**: Handles client disconnections gracefully

### Heartbeat System
- **Ping/Pong**: Sends periodic ping frames to maintain connections
- **Health Monitoring**: Detects and removes stale connections
- **Configurable Interval**: Adjustable heartbeat frequency
- **Automatic Cleanup**: Removes unresponsive clients

### Message Processing
- **Broadcast Mode**: Sends stream data to all connected clients
- **JSON Serialization**: Automatically converts objects to JSON
- **Error Recovery**: Continues operation when individual clients fail
- **Delivery Tracking**: Reports successful delivery counts

## Usage Patterns

### Stream-Based Broadcasting
When used in stream-based architecture, WebSocket component receives data via streams and broadcasts to connected clients:

```python
# Component receives data via receive_streams['input']
# Broadcasts to all connected WebSocket clients
# Returns delivery status via send_streams['output']
```

### Standalone Server
Can be started as independent WebSocket server:

```python
websocket_component = WebSocketComponent("server", config)
await websocket_component.start_server()
```

## Blueprint Examples

### Real-Time Data Broadcasting
```yaml
system:
  name: "realtime_dashboard"
  components:
    - name: "metrics_source"
      type: "Source"
    - name: "websocket_server"
      type: "WebSocket"
      config:
        port: 8080
        host: "0.0.0.0"
        max_connections: 200
        heartbeat_interval: 15
    - name: "broadcast_log"
      type: "Sink"
      
  bindings:
    - from_component: "metrics_source"
      to_component: "websocket_server"
      stream_name: "input"
    - from_component: "websocket_server"
      to_component: "broadcast_log"
      stream_name: "output"
```

### Multi-Source Real-Time Updates
```yaml
system:
  name: "live_updates"
  components:
    - name: "user_events"
      type: "Source"
    - name: "system_alerts"
      type: "Source"
    - name: "event_merger"
      type: "StreamProcessor"
      config:
        variant: "joining"
    - name: "websocket_broadcaster"
      type: "WebSocket"
      config:
        port: 3000
        max_connections: 500
      
  bindings:
    - from_component: "user_events"
      to_component: "event_merger"
      stream_name: "left"
    - from_component: "system_alerts"
      to_component: "event_merger"
      stream_name: "right"
    - from_component: "event_merger"
      to_component: "websocket_broadcaster"
      stream_name: "input"
```

### WebSocket with Processing Pipeline
```yaml
system:
  name: "processed_realtime"
  components:
    - name: "raw_data"
      type: "Source"
    - name: "data_filter"
      type: "Filter"
    - name: "data_transformer"
      type: "Transformer"
    - name: "realtime_output"
      type: "WebSocket"
      config:
        port: 8888
        heartbeat_interval: 10
      
  bindings:
    - from_component: "raw_data"
      to_component: "data_filter"
      stream_name: "input"
    - from_component: "data_filter"
      to_component: "data_transformer"
      stream_name: "input"
    - from_component: "data_transformer"
      to_component: "realtime_output"
      stream_name: "input"
```

## Message Broadcasting

### Broadcast Response Format
```json
{
  "broadcast_to": 15,
  "disconnected": 2,
  "message": {
    "timestamp": "2025-08-03T10:15:30Z",
    "data": "realtime update"
  }
}
```

### Client Connection Example
```javascript
// Client-side JavaScript
const ws = new WebSocket('ws://localhost:8080');

ws.onopen = function() {
    console.log('Connected to WebSocket server');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onclose = function() {
    console.log('WebSocket connection closed');
};
```

## Configuration Options

### Network Settings
- **port**: Server listening port (1-65535)
- **host**: Network interface to bind ("0.0.0.0" for all interfaces)

### Connection Management
- **max_connections**: Maximum concurrent client connections
- **heartbeat_interval**: Seconds between ping frames

### Performance Tuning
```yaml
# High-throughput configuration
config:
  port: 8080
  max_connections: 1000
  heartbeat_interval: 60    # Longer interval for high volume

# Low-latency configuration  
config:
  port: 8080
  max_connections: 50
  heartbeat_interval: 5     # Shorter interval for responsiveness
```

## Error Handling
- **Connection Limits**: Rejects connections when max_connections reached
- **Send Failures**: Continues broadcasting to other clients when individual sends fail
- **Heartbeat Failures**: Automatically removes unresponsive clients
- **Server Errors**: Logs errors without crashing the component

## Performance Characteristics
- **Connection Overhead**: ~1KB memory per connected client
- **Broadcast Performance**: O(n) where n = number of connected clients
- **Heartbeat Impact**: Minimal CPU usage for connection health checks
- **Message Throughput**: Limited by client connection quality and processing speed

## Common Issues
**Problem**: "Max connections reached" error  
**Solution**: Increase `max_connections` or implement connection pooling

**Problem**: Clients disconnecting frequently  
**Solution**: Check network stability and adjust `heartbeat_interval`

**Problem**: Messages not reaching all clients  
**Solution**: Check client connection status and error logs for send failures

**Problem**: Server not starting  
**Solution**: Verify port is available and not in use by another process

## Client Integration

### JavaScript Client
```javascript
const ws = new WebSocket('ws://localhost:8080');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateUI(data);
};
```

### Python Client
```python
import websockets
import asyncio

async def client():
    async with websockets.connect("ws://localhost:8080") as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(client())
```

## Production Deployment

### Security Considerations
- Use WSS (WebSocket Secure) in production
- Implement authentication/authorization
- Consider rate limiting for message broadcasting
- Monitor connection counts and resource usage

### Scaling Considerations
- WebSocket servers are stateful (connections tied to specific instances)
- Consider load balancing with sticky sessions
- Monitor memory usage per connection
- Implement connection limits appropriate for server resources

## Implementation Notes
- Uses `websockets` library for protocol implementation
- Automatically cleans up disconnected clients
- JSON serialization handles complex data types
- Heartbeat system prevents connection accumulation
- Thread-safe connection management with async/await

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and tested  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Dependencies**: `websockets` library required  