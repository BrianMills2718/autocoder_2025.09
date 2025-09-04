# APIEndpoint Component (Stream-Based Implementation)

## Overview
Base API endpoint component with comprehensive input validation, security features, and stream-based integration for HTTP/WebSocket services.

## Implementation Details
**Base Class**: `ComposedComponent` (from `autocoder_cc.components.composed_base`)  
**File**: `autocoder_cc/components/api_endpoint.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Dependencies**: Component generation required for actual server implementation

## Configuration Schema
```yaml
- name: "api_server"
  type: "APIEndpoint"
  config:
    port: 8080                    # Required: Server port
    host: "0.0.0.0"              # Bind address (default: 0.0.0.0)
```

## Key Features

### Security and Validation
- **Input Sanitization**: Comprehensive input validation with `InputSanitizer`
- **XSS Prevention**: Automatic XSS attack prevention
- **SQL Injection Protection**: SQL injection detection and prevention
- **Path Traversal Protection**: Path traversal attack prevention
- **JSON Validation**: Secure JSON parsing and validation

### Stream Integration
- **Inbound Stream Processing**: Can receive data from other components
- **Outbound Stream Generation**: Can send processed data to downstream components
- **Request/Response Flow**: Handles HTTP requests and generates appropriate responses

### Error Handling
- **Comprehensive Error Management**: Uses `ConsistentErrorHandler`
- **Graceful Shutdown**: Proper server shutdown handling
- **Fail-Fast Behavior**: Clear error messages for configuration issues

## Security Features

### Input Validation Methods
```python
# Validate general request data
sanitized_data = component.validate_request_data(request_data)

# Validate JSON requests
parsed_data = component.sanitize_json_request(json_string)

# Validate query parameters
clean_params = component.validate_query_parameters(query_params)

# Validate path parameters
safe_paths = component.validate_path_parameters(path_params)
```

### Security Violation Handling
```python
try:
    sanitized_data = self.validate_request_data(request_data)
except InputSanitizationError as e:
    # Critical security violation detected
    for violation in e.violations:
        print(f"Security issue: {violation.description}")
    # Request is rejected
```

## Usage Pattern

### Generated Component Implementation
APIEndpoint is designed to be extended by generated components. The base class provides:

1. **Security Infrastructure**: Input validation and sanitization
2. **Server Lifecycle**: Setup, startup, and shutdown management
3. **Stream Integration**: Connection to the component pipeline
4. **Error Handling**: Comprehensive error management

### Generated Component Requirements
Generated APIEndpoint components must implement:

```python
class GeneratedMyAPI(APIEndpoint):
    async def _start_server(self):
        """Must implement actual server startup"""
        # Create your HTTP server (FastAPI, Flask, etc.)
        # Bind to self.host and self.port
        # Set self.server for lifecycle management
        
    async def _stop_server(self):
        """Must implement server shutdown"""
        # Gracefully stop the server
        # Clean up resources
```

## Blueprint Examples

### Basic API Endpoint
```yaml
system:
  name: "web_api_system"
  components:
    - name: "web_api"
      type: "APIEndpoint"
      config:
        port: 8080
        host: "0.0.0.0"
    - name: "data_processor"
      type: "Transformer"
    - name: "data_store"
      type: "Store"
      
  bindings:
    - from_component: "web_api"
      to_component: "data_processor"
      stream_name: "input"
    - from_component: "data_processor"
      to_component: "data_store"
      stream_name: "input"
```

### API with Stream Processing
```yaml
system:
  name: "api_processing_pipeline"
  components:
    - name: "public_api"
      type: "APIEndpoint"
      config:
        port: 3000
    - name: "request_validator"
      type: "Filter"
    - name: "business_logic"
      type: "StreamProcessor"
      config:
        variant: "windowing"
        window_size: 5.0
    - name: "response_cache"
      type: "Store"
      
  bindings:
    - from_component: "public_api"
      to_component: "request_validator"
      stream_name: "input"
    - from_component: "request_validator"
      to_component: "business_logic"
      stream_name: "input"
    - from_component: "business_logic"
      to_component: "response_cache"
      stream_name: "input"
```

### Multi-API System
```yaml
system:
  name: "microservices_apis"
  components:
    - name: "user_api"
      type: "APIEndpoint"
      config:
        port: 8001
    - name: "order_api"
      type: "APIEndpoint"
      config:
        port: 8002
    - name: "notification_api"
      type: "APIEndpoint"
      config:
        port: 8003
    - name: "central_processor"
      type: "Controller"
      config:
        variant: "router"
    - name: "unified_store"
      type: "Store"
      
  bindings:
    - from_component: "user_api"
      to_component: "central_processor"
      stream_name: "input"
    - from_component: "order_api"
      to_component: "central_processor"
      stream_name: "input"
    - from_component: "notification_api"
      to_component: "central_processor"
      stream_name: "input"
    - from_component: "central_processor"
      to_component: "unified_store"
      stream_name: "default"
```

## Advanced Usage

### Custom Stream Processing
```python
class CustomAPIEndpoint(APIEndpoint):
    async def _handle_inbound_stream_data(self, data):
        """Override to process inbound stream data"""
        # Process data from other components
        processed = await self.custom_processing(data)
        
        # Make available for API responses
        self.cached_data = processed
        
        return processed
```

### Security Configuration
```python
# Configure strict input validation
config = {
    "port": 8080,
    "security": {
        "strict_mode": True,
        "max_request_size": "10MB",
        "rate_limiting": {
            "requests_per_minute": 100
        }
    }
}
```

## Error Handling Patterns

### Request Validation Errors
```python
try:
    sanitized_data = self.validate_request_data(request_data)
    # Process sanitized data safely
except InputSanitizationError as e:
    # Security violation - reject request
    return {"error": "Invalid input", "status": 400}
```

### Server Lifecycle Errors
```python
# Base APIEndpoint handles these automatically:
# - Port already in use
# - Invalid host binding
# - Server startup failures
# - Graceful shutdown issues
```

## Performance Characteristics
- **Security Overhead**: Input validation adds ~1-5ms per request
- **Memory Usage**: Minimal overhead for validation state
- **Concurrency**: Depends on generated server implementation
- **Throughput**: Limited by validation complexity and server choice

## Common Issues
**Problem**: "APIEndpoint cannot be started" error  
**Solution**: Base APIEndpoint requires component generation - use FastAPIEndpoint or implement custom server

**Problem**: "Port already in use" error  
**Solution**: Check port availability or change port configuration

**Problem**: Input validation rejecting valid requests  
**Solution**: Review InputSanitizer rules or adjust strict_mode setting

**Problem**: Server not shutting down gracefully  
**Solution**: Ensure generated component implements proper _stop_server method

## Integration with Other Components

### FastAPI Integration
Use `FastAPIEndpoint` for ready-to-use FastAPI server implementation.

### WebSocket Integration
Use `WebSocketComponent` for real-time bidirectional communication.

### Metrics Integration
Use `MetricsEndpoint` for system monitoring and observability.

## Security Best Practices
1. **Always validate input**: Use provided validation methods
2. **Configure appropriate timeouts**: Prevent resource exhaustion
3. **Use HTTPS in production**: Enable TLS for encrypted communication
4. **Implement rate limiting**: Protect against abuse
5. **Monitor security violations**: Log and alert on validation failures

## Implementation Notes
- Base class provides security infrastructure only
- Actual server implementation required via component generation
- Supports any HTTP server framework (FastAPI, Flask, etc.)
- Stream integration enables complex data processing pipelines
- Comprehensive error handling prevents security vulnerabilities

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Base class implemented, requires generation  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Security Level**: High - comprehensive input validation included  