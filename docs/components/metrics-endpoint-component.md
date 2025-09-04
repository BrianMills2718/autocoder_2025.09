# MetricsEndpoint Component (Stream-Based Implementation)

## Overview
Production observability endpoint providing comprehensive system health, performance metrics, and monitoring data through HTTP endpoints for external monitoring systems.

## Implementation Details
**Base Class**: `Component` (from `autocoder_cc.orchestration.component`)  
**File**: `autocoder_cc/components/metrics_endpoint.py`  
**Communication**: Direct harness integration for metrics collection  
**Dependencies**: FastAPI, uvicorn

## Configuration Schema
```yaml
- name: "system_metrics"
  type: "MetricsEndpoint"
  config:
    port: 9000                   # Required: Metrics server port
```

## Key Features

### Comprehensive Metrics Collection
- **System Health**: Overall system status and health scores
- **Component Metrics**: Individual component performance and status
- **Performance Data**: CPU, memory, throughput, and error rates
- **Alert Management**: Active alerts and recommendations
- **Circuit Breaker Status**: Component resilience monitoring

### Multiple Export Formats
- **JSON Format**: Structured metrics for programmatic access
- **Prometheus Format**: Industry-standard metrics exposition
- **Health Check**: Simple status for load balancers
- **Component Details**: Granular component-level metrics

### Production Features
- **CORS Support**: Cross-origin requests for web dashboards
- **Rate Limiting**: Protection against metric scraping abuse  
- **Graceful Shutdown**: Proper server lifecycle management
- **Error Resilience**: Continues operation even if harness is unavailable

## API Endpoints

### Health Check Endpoint
```http
GET /health
```
**Purpose**: System health summary for load balancers  
**Response**:
```json
{
  "status": "healthy",
  "health_score": 0.95,
  "uptime_seconds": 3600,
  "components": {
    "total": 5,
    "healthy": 5,
    "running": 5
  },
  "timestamp": 1691234567.89
}
```
**Status Codes**:
- `200`: System healthy
- `503`: System unhealthy or degraded

### Detailed Metrics (JSON)
```http
GET /metrics/json
```
**Purpose**: Comprehensive metrics in JSON format  
**Response**:
```json
{
  "health_score": 0.95,
  "uptime_seconds": 3600,
  "system_status": "healthy",
  "performance": {
    "error_rate": 0.01,
    "memory_usage_mb": 512,
    "cpu_usage_percent": 25.5,
    "items_per_second": 150.2
  },
  "detailed_components": {
    "task_api": {
      "is_healthy": true,
      "items_processed": 1500,
      "errors_encountered": 2,
      "status": "running"
    },
    "task_store": {
      "is_healthy": true,
      "items_processed": 1450,
      "errors_encountered": 0,
      "status": "running"
    }
  },
  "circuit_breakers": {
    "task_api": {
      "state": "closed",
      "failure_count": 0,
      "last_failure": null
    }
  },
  "traces": {
    "total_traces": 45,
    "active_spans": 12
  },
  "alerts": [
    {
      "level": "warning",
      "message": "High memory usage detected",
      "component": "task_store",
      "timestamp": 1691234567.89
    }
  ],
  "recommendations": [
    {
      "type": "performance",
      "message": "Consider increasing memory allocation",
      "component": "task_store"
    }
  ]
}
```

### Prometheus Metrics
```http
GET /metrics
```
**Purpose**: Prometheus-compatible metrics exposition  
**Response** (text/plain):
```
# HELP system_health_score System health score (0.0 to 1.0)
# TYPE system_health_score gauge
system_health_score 0.95

# HELP system_uptime_seconds System uptime in seconds
# TYPE system_uptime_seconds counter
system_uptime_seconds 3600

# HELP system_error_rate System-wide error rate
# TYPE system_error_rate gauge
system_error_rate 0.01

# HELP component_health Component health status (1=healthy, 0=unhealthy)
# TYPE component_health gauge
component_health{component="task_api"} 1
component_health{component="task_store"} 1

# HELP component_items_processed Total items processed by component
# TYPE component_items_processed counter
component_items_processed{component="task_api"} 1500
component_items_processed{component="task_store"} 1450

# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)
# TYPE circuit_breaker_state gauge
circuit_breaker_state{component="task_api"} 0
```

### Active Alerts
```http
GET /alerts
```
**Purpose**: Current alerts and recommendations  
**Response**:
```json
{
  "alerts": [
    {
      "level": "warning",
      "message": "High memory usage detected",
      "component": "task_store",
      "timestamp": 1691234567.89
    }
  ],
  "recommendations": [
    {
      "type": "performance",
      "message": "Consider increasing memory allocation",
      "component": "task_store"
    }
  ],
  "timestamp": 1691234567.89
}
```

### Component Status
```http
GET /components
```
**Purpose**: Component-level detailed status  
**Response**:
```json
{
  "components": {
    "task_api": {
      "is_healthy": true,
      "items_processed": 1500,
      "errors_encountered": 2,
      "status": "running",
      "last_activity": 1691234567.89
    },
    "task_store": {
      "is_healthy": true,
      "items_processed": 1450,
      "errors_encountered": 0,
      "status": "running",
      "last_activity": 1691234567.89
    }
  },
  "circuit_breakers": {
    "task_api": {
      "state": "closed",
      "failure_count": 0,
      "last_failure": null
    }
  },
  "streaming": {
    "active_streams": 3,
    "total_messages": 15000,
    "message_rate": 50.2
  },
  "timestamp": 1691234567.89
}
```

### API Documentation
```http
GET /
```
**Purpose**: Endpoint discovery and API information  
**Response**:
```json
{
  "service": "System Metrics API",
  "version": "1.0.0",
  "endpoints": {
    "/health": "System health summary",
    "/metrics": "Detailed performance metrics", 
    "/alerts": "Active alerts and recommendations",
    "/components": "Component-level status"
  },
  "timestamp": 1691234567.89
}
```

## Blueprint Examples

### Basic Metrics Endpoint
```yaml
system:
  name: "monitored_system"
  components:
    - name: "app_server"
      type: "FastAPIEndpoint"
      config:
        port: 8000
    - name: "data_store"
      type: "Store"
    - name: "system_metrics"
      type: "MetricsEndpoint"
      config:
        port: 9000
        
  bindings:
    - from_component: "app_server"
      to_component: "data_store"
      stream_name: "input"
```

### Production Monitoring Setup
```yaml
system:
  name: "production_monitoring"
  components:
    - name: "public_api"
      type: "FastAPIEndpoint"
      config:
        port: 80
    - name: "business_logic"
      type: "StreamProcessor"
      config:
        variant: "windowing"
    - name: "persistent_store"
      type: "Store"
    - name: "metrics_server"
      type: "MetricsEndpoint"
      config:
        port: 9090
    - name: "health_check"
      type: "MetricsEndpoint"
      config:
        port: 8080
        
  bindings:
    - from_component: "public_api"
      to_component: "business_logic"
      stream_name: "input"
    - from_component: "business_logic"
      to_component: "persistent_store"
      stream_name: "input"
```

### Multi-Environment Metrics
```yaml
system:
  name: "multi_env_metrics"
  components:
    - name: "app_cluster"
      type: "Controller"
      config:
        variant: "router"
    - name: "production_metrics"
      type: "MetricsEndpoint"
      config:
        port: 9000
    - name: "staging_metrics"  
      type: "MetricsEndpoint"
      config:
        port: 9001
    - name: "development_metrics"
      type: "MetricsEndpoint"
      config:
        port: 9002
```

## Production Usage

### Prometheus Integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'autocoder-metrics'
    static_configs:
      - targets: ['localhost:9000']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "AutoCoder System Metrics",
    "panels": [
      {
        "title": "System Health Score",
        "targets": [{"expr": "system_health_score"}]
      },
      {
        "title": "Component Health",
        "targets": [{"expr": "component_health"}]
      },
      {
        "title": "Error Rate",
        "targets": [{"expr": "system_error_rate"}]
      }
    ]
  }
}
```

### Load Balancer Health Check
```nginx
# nginx.conf
upstream app_servers {
    server app1:8000;
    server app2:8000;
}

# Health check configuration
location /health {
    proxy_pass http://localhost:9000/health;
    proxy_connect_timeout 1s;
    proxy_read_timeout 3s;
}
```

### Alerting Rules
```yaml
# alertmanager rules
groups:
  - name: autocoder.rules
    rules:
      - alert: SystemUnhealthy
        expr: system_health_score < 0.8
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "AutoCoder system health degraded"
          
      - alert: ComponentDown
        expr: component_health == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Component {{ $labels.component }} is unhealthy"
```

## Advanced Features

### Production Metrics Endpoint
```python
# Use ProductionMetricsEndpoint for enhanced features
production_metrics = ProductionMetricsEndpoint(
    name="prod_metrics",
    port=9090,
    enable_cors=True  # For web dashboard access
)
```

### Custom Metrics Collection
```python
# Extend MetricsEndpoint for custom metrics
class CustomMetricsEndpoint(MetricsEndpoint):
    def _setup_routes(self):
        super()._setup_routes()
        
        @self.app.get("/custom-metrics")
        async def custom_metrics():
            return await self.collect_custom_metrics()
```

## Error Handling
- **Harness Unavailable**: Returns 503 with clear error message
- **Metrics Collection Failure**: Logs error, returns partial data when possible
- **Server Startup Issues**: Clear error messages with port and configuration details
- **Resource Exhaustion**: Graceful degradation of metrics collection

## Performance Characteristics
- **Metrics Collection**: ~10-50ms depending on system complexity
- **Memory Usage**: ~20MB base + metrics data storage
- **HTTP Response Time**: <100ms for health checks, <500ms for detailed metrics
- **Concurrent Requests**: Handles 100+ concurrent requests

## Common Issues
**Problem**: "Harness not available" errors  
**Solution**: Ensure MetricsEndpoint is properly configured with harness context

**Problem**: Prometheus scraping failures  
**Solution**: Check network connectivity and metrics endpoint accessibility

**Problem**: Incomplete metrics data  
**Solution**: Verify all components are properly instrumented and reporting

**Problem**: High memory usage for metrics  
**Solution**: Consider sampling for high-volume systems

## Security Considerations
- **Network Access**: Restrict metrics endpoint access to monitoring systems
- **Authentication**: Consider adding authentication for sensitive environments
- **Rate Limiting**: Built-in protection against metric scraping abuse
- **Data Exposure**: Review metrics for sensitive information leakage

## Implementation Notes
- Uses FastAPI for robust HTTP server functionality
- Direct integration with system harness for accurate metrics
- Prometheus text exposition format for industry compatibility
- CORS support for web-based monitoring dashboards
- Graceful error handling prevents monitoring system failures

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and production-ready  
**Blueprint Format**: Stream-based (uses `bindings`)  
**Dependencies**: FastAPI, uvicorn  
**Monitoring Integration**: Prometheus, Grafana compatible  