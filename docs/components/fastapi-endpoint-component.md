# FastAPIEndpoint Component (Stream-Based Implementation)

## Overview
Production-ready FastAPI server implementation with comprehensive CRUD endpoints, store integration, and built-in task management capabilities.

## Implementation Details
**Base Class**: `APIEndpoint` (extends base API functionality)  
**File**: `autocoder_cc/components/fastapi_endpoint.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  
**Dependencies**: FastAPI, uvicorn

## Configuration Schema
```yaml
- name: "task_api"
  type: "FastAPIEndpoint"
  config:
    host: "localhost"            # Server host (default: localhost)
    port: 8000                   # Server port (default: 8000)
```

## Key Features

### FastAPI Application
- **Automatic App Generation**: Creates FastAPI app with comprehensive endpoints
- **OpenAPI Documentation**: Built-in Swagger UI and API documentation
- **Async Request Handling**: Full async/await support for high performance
- **Uvicorn Server**: Production ASGI server with threading support

### Built-in CRUD Endpoints
- **Health Check**: `GET /health` - Component and system health status
- **Task Management**: Complete CRUD operations for task entities
- **Legacy Support**: Backward-compatible API endpoints
- **Input Validation**: Comprehensive request validation and sanitization

### Store Integration
- **Store Component Binding**: Automatic integration with Store components
- **CRUD Operations**: Create, Read, Update, Delete operations via store
- **Error Handling**: Proper HTTP status codes and error responses
- **Data Validation**: Request/response validation with store operations

## API Endpoints

### Health Endpoint
```http
GET /health
```
**Response**:
```json
{
  "status": "ok",
  "health": {
    "status": "healthy",
    "api_ready": true,
    "endpoint": "localhost:8000",
    "healthy": true,
    "port": 8000,
    "host": "localhost",
    "store_connected": true,
    "endpoints": ["/health", "/tasks", "/tasks/{task_id}", "/api/task_api"]
  }
}
```

### Task CRUD Endpoints

#### List All Tasks
```http
GET /tasks
```
**Response**:
```json
{
  "tasks": [
    {"id": "1", "title": "Task 1", "completed": false},
    {"id": "2", "title": "Task 2", "completed": true}
  ]
}
```

#### Create Task
```http
POST /tasks
Content-Type: application/json

{
  "title": "New Task",
  "description": "Task description",
  "completed": false
}
```
**Response**:
```json
{
  "task": {
    "id": "3",
    "title": "New Task", 
    "description": "Task description",
    "completed": false
  },
  "id": "3"
}
```

#### Get Specific Task
```http
GET /tasks/{task_id}
```
**Response**:
```json
{
  "task": {
    "id": "1",
    "title": "Task 1",
    "completed": false
  }
}
```

#### Update Task
```http
PUT /tasks/{task_id}
Content-Type: application/json

{
  "title": "Updated Task",
  "completed": true
}
```
**Response**:
```json
{
  "task": {
    "id": "1",
    "title": "Updated Task",
    "completed": true
  }
}
```

#### Delete Task
```http
DELETE /tasks/{task_id}
```
**Response**:
```json
{
  "message": "Task deleted successfully"
}
```

### Legacy Data Endpoint
```http
POST /api/{component_name}
Content-Type: application/json

{
  "data": "any_data"
}
```
**Response**:
```json
{
  "received": {"data": "any_data"},
  "component": "task_api",
  "status": "processed",
  "timestamp": 1691234567.89
}
```

## Blueprint Examples

### Basic Task API
```yaml
system:
  name: "task_management_api"
  components:
    - name: "task_api"
      type: "FastAPIEndpoint"
      config:
        host: "localhost"
        port: 8000
    - name: "task_store"
      type: "Store"
      config:
        storage_type: "memory"
      
  bindings:
    - from_component: "task_api"
      to_component: "task_store"
      stream_name: "input"
```

### Production API with Processing
```yaml
system:
  name: "production_task_api"
  components:
    - name: "public_api"
      type: "FastAPIEndpoint"
      config:
        host: "0.0.0.0"
        port: 80
    - name: "request_validator"
      type: "Filter"
    - name: "business_processor"
      type: "StreamProcessor"
      config:
        variant: "deduplication"
        dedup_key: "id"
    - name: "persistent_store"
      type: "Store"
      config:
        storage_type: "database"
        connection_string: "postgresql://user:pass@db:5432/tasks"
    - name: "audit_log"
      type: "Sink"
      
  bindings:
    - from_component: "public_api"
      to_component: "request_validator"
      stream_name: "input"
    - from_component: "request_validator"
      to_component: "business_processor"
      stream_name: "input"
    - from_component: "business_processor"
      to_component: "persistent_store"
      stream_name: "input"
    - from_component: "business_processor"
      to_component: "audit_log"
      stream_name: "input"
```

### Multi-Service API
```yaml
system:
  name: "microservices_platform"
  components:
    - name: "user_api"
      type: "FastAPIEndpoint"
      config:
        host: "0.0.0.0"
        port: 8001
    - name: "order_api"
      type: "FastAPIEndpoint"
      config:
        host: "0.0.0.0"
        port: 8002
    - name: "shared_processor"
      type: "Controller"
      config:
        variant: "router"
    - name: "user_store"
      type: "Store"
    - name: "order_store"
      type: "Store"
      
  bindings:
    - from_component: "user_api"
      to_component: "shared_processor"
      stream_name: "input"
    - from_component: "order_api"
      to_component: "shared_processor"
      stream_name: "input"
    - from_component: "shared_processor"
      to_component: "user_store"
      stream_name: "user_output"
    - from_component: "shared_processor"
      to_component: "order_store"
      stream_name: "order_output"
```

## Store Integration

### Automatic Store Binding
FastAPIEndpoint automatically detects and integrates with Store components:

```python
# Store component is automatically bound via streams
# CRUD operations route through store component
# HTTP responses generated from store operation results
```

### Store Operation Mapping
| HTTP Method | Store Action | Response |
|---|---|---|
| `GET /tasks` | `{"action": "list"}` | Array of tasks |
| `POST /tasks` | `{"action": "create", "data": task}` | Created task with ID |
| `GET /tasks/{id}` | `{"action": "get", "id": id}` | Single task or 404 |
| `PUT /tasks/{id}` | `{"action": "update", "id": id, "data": task}` | Updated task or 404 |
| `DELETE /tasks/{id}` | `{"action": "delete", "id": id}` | Success message or 404 |

### Store Response Handling
```python
# Store responses are automatically converted to HTTP responses:
# {"status": "success", "data": {...}} → 200 OK
# {"status": "not_found"} → 404 Not Found  
# {"status": "error", "message": "..."} → 400/500 based on error
```

## Advanced Usage

### Custom Store Component Binding
```python
# In generated FastAPIEndpoint
await self.set_store_component(store_component)

# Store operations become available in endpoints
result = await self.store_component.process_item({
    "action": "custom_operation",
    "data": request_data
})
```

### Custom Endpoint Extension
```python
class CustomFastAPIEndpoint(FastAPIEndpoint):
    async def _start_server(self):
        await super()._start_server()
        
        # Add custom endpoints
        @self.app.get("/custom")
        async def custom_endpoint():
            return {"message": "Custom endpoint"}
```

### Input Validation Integration
```python
# Built-in validation for all endpoints
@self.app.post("/secure-endpoint")
async def secure_endpoint(data: dict):
    # Input automatically validated via parent APIEndpoint
    sanitized_data = self.validate_request_data(data)
    return {"validated": sanitized_data}
```

## Error Handling

### HTTP Status Code Mapping
- **200**: Successful operation
- **400**: Invalid request data or store operation failure
- **404**: Resource not found (task ID doesn't exist)
- **500**: Internal server error or store connection failure
- **503**: Store component not connected

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

## Performance Characteristics
- **Server Startup**: ~1-2 seconds for FastAPI app initialization
- **Request Throughput**: 1000+ requests/second with async processing
- **Memory Usage**: ~50MB base + request processing overhead
- **Store Integration**: Minimal latency overhead for stream communication

## Common Issues
**Problem**: "Store not connected" errors  
**Solution**: Ensure Store component is properly bound via stream connections

**Problem**: Server not starting on specified port  
**Solution**: Check port availability and firewall settings

**Problem**: 503 Service Unavailable responses  
**Solution**: Verify store component is running and responsive

**Problem**: CORS errors in browser  
**Solution**: Configure CORS middleware in FastAPI app

## Production Deployment

### HTTPS Configuration
```python
# Use reverse proxy (nginx) or configure uvicorn with SSL
config = uvicorn.Config(
    app=self.app,
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### Performance Tuning
```yaml
config:
  host: "0.0.0.0"
  port: 80
  workers: 4              # Multiple worker processes
  max_connections: 1000   # Connection limit
  timeout: 30            # Request timeout
```

### Health Check Integration
```bash
# Health check for load balancer
curl http://localhost:8000/health

# Expected response for healthy service
{"status": "ok", "health": {"status": "healthy", ...}}
```

## Implementation Notes
- Extends APIEndpoint base class for security features
- Uses uvicorn server in separate thread for async compatibility
- Automatic OpenAPI schema generation
- Built-in request/response validation
- Production-ready with proper error handling and logging

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and production-ready  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Dependencies**: FastAPI, uvicorn  