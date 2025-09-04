from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
MetricsEndpoint - Production observability endpoint for system monitoring

Exposes comprehensive system health, metrics, and observability data
through HTTP endpoints for external monitoring systems.
"""

import json
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging

from autocoder_cc.orchestration.component import Component


class MetricsEndpoint(Component):
    """
    Production metrics endpoint component
    
    Provides HTTP endpoints for:
    - /health - System health summary
    - /metrics - Detailed performance metrics
    - /alerts - Active alerts and recommendations
    - /components - Component-level status
    """
    
    def __init__(self, name: str = "metrics_endpoint", config: Dict[str, Any] = None):
        super().__init__(name)
        
        # Simplified port resolution: expect ResourceOrchestrator to provide allocated port
        if isinstance(config, int):
            # Legacy usage: MetricsEndpoint("metrics", 9000)
            self.port = config
        elif isinstance(config, dict):
            # Standard usage: MetricsEndpoint("metrics", {"port": 9000})
            port = config.get('port')
            if port is None:
                raise ValueError(f"MetricsEndpoint {name} requires 'port' in configuration (ResourceOrchestrator should provide allocated port)")
            self.port = int(port)
        else:
            raise ValueError(f"MetricsEndpoint {name} requires config dict with 'port' key")
        self.app = FastAPI(title="System Metrics API", version="1.0.0")
        self.server = None
        self.harness_ref = None
        self.logger = get_logger(f"MetricsEndpoint.{self.port}")
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for metrics endpoints"""
        
        @self.app.get("/health")
        async def health_endpoint():
            """System health summary for load balancers"""
            if not self.harness_ref:
                return JSONResponse(
                    status_code=503,
                    content={"status": "service_unavailable", "message": "Harness not available"}
                )
            
            try:
                health_summary = self.harness_ref.get_system_health_summary()
                
                # Simple health response for load balancers
                response = {
                    "status": health_summary["system_status"],
                    "health_score": health_summary["health_score"],
                    "uptime_seconds": health_summary["uptime_seconds"],
                    "components": {
                        "total": health_summary["total_components"],
                        "healthy": health_summary["healthy_components"],
                        "running": health_summary["running_components"]
                    },
                    "timestamp": time.time()
                }
                
                # Return appropriate HTTP status
                status_code = 200 if health_summary["system_status"] == "healthy" else 503
                return JSONResponse(status_code=status_code, content=response)
                
            except Exception as e:
                self.logger.error(f"Health endpoint error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": str(e)}
                )
        
        @self.app.get("/metrics/json")
        async def metrics_json_endpoint():
            """Detailed system metrics for monitoring in JSON format"""
            if not self.harness_ref:
                raise HTTPException(status_code=503, detail="Harness not available")
            
            try:
                detailed_metrics = await self.harness_ref.get_detailed_metrics()
                return detailed_metrics
                
            except Exception as e:
                self.logger.error(f"Metrics endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts")
        async def alerts_endpoint():
            """Active alerts and recommendations"""
            if not self.harness_ref:
                raise HTTPException(status_code=503, detail="Harness not available")
            
            try:
                detailed_metrics = await self.harness_ref.get_detailed_metrics()
                return {
                    "alerts": detailed_metrics["alerts"],
                    "recommendations": detailed_metrics["recommendations"],
                    "timestamp": time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Alerts endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/components")
        async def components_endpoint():
            """Component-level status and metrics"""
            if not self.harness_ref:
                raise HTTPException(status_code=503, detail="Harness not available")
            
            try:
                detailed_metrics = await self.harness_ref.get_detailed_metrics()
                return {
                    "components": detailed_metrics["detailed_components"],
                    "circuit_breakers": detailed_metrics["circuit_breakers"],
                    "streaming": detailed_metrics["streaming"],
                    "timestamp": time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Components endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/")
        async def root_endpoint():
            """API documentation"""
            return {
                "service": "System Metrics API",
                "version": "1.0.0",
                "endpoints": {
                    "/health": "System health summary",
                    "/metrics": "Detailed performance metrics", 
                    "/alerts": "Active alerts and recommendations",
                    "/components": "Component-level status"
                },
                "timestamp": time.time()
            }
    
    async def setup(self, context: Dict[str, Any]):
        """Setup the metrics endpoint"""
        self.logger.info(f"Setting up metrics endpoint on port {self.port}")
        
        # Get reference to harness for metrics collection
        self.harness_ref = context.get("harness")
        
        # Configure uvicorn server
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0", 
            port=self.port,
            log_level="info",
            access_log=False  # Reduce noise in logs
        )
        self.server = uvicorn.Server(config)
        
        self.logger.info(f"Metrics API configured on port {self.port}")
    
    async def process(self):
        """Run the metrics server"""
        if not self.server:
            raise RuntimeError("Metrics endpoint not setup")
        
        self.logger.info(f"Starting metrics server on port {self.port}")
        
        try:
            await self.server.serve()
        except Exception as e:
            self.logger.error(f"Metrics server error: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup the metrics endpoint"""
        if self.server:
            self.logger.info(f"Shutting down metrics server on port {self.port}")
            self.server.should_exit = True
            
            # Give it a moment to shutdown gracefully
            import anyio
            await anyio.sleep(0.5)
    
    async def health_check(self) -> bool:
        """Check if metrics endpoint is healthy"""
        if not self.server:
            return False
        
        # Check if server is running
        return not self.server.should_exit


class ProductionMetricsEndpoint(MetricsEndpoint):
    """Extended metrics endpoint with production features"""
    
    def __init__(self, name: str = "production_metrics", port: int = None, enable_cors: bool = True):
        super().__init__(name, port)
        self.enable_cors = enable_cors
        
        if enable_cors:
            from fastapi.middleware.cors import CORSMiddleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Configure appropriately for production
                allow_credentials=True,
                allow_methods=["GET"],
                allow_headers=["*"],
            )
    
    def _setup_routes(self):
        """Setup production routes with additional endpoints"""
        super()._setup_routes()
        
        @self.app.get("/metrics")
        async def prometheus_metrics():
            """Prometheus-compatible metrics export in standard format"""
            if not self.harness_ref:
                raise HTTPException(status_code=503, detail="Harness not available")
            
            try:
                metrics = await self.harness_ref.get_detailed_metrics()
                
                # Convert to Prometheus text exposition format
                prometheus_lines = []
                
                # System-level metrics
                prometheus_lines.append("# HELP system_health_score System health score (0.0 to 1.0)")
                prometheus_lines.append("# TYPE system_health_score gauge")
                prometheus_lines.append(f"system_health_score {metrics['health_score']}")
                
                prometheus_lines.append("# HELP system_uptime_seconds System uptime in seconds")
                prometheus_lines.append("# TYPE system_uptime_seconds counter")
                prometheus_lines.append(f"system_uptime_seconds {metrics['uptime_seconds']}")
                
                prometheus_lines.append("# HELP system_error_rate System-wide error rate")
                prometheus_lines.append("# TYPE system_error_rate gauge")
                prometheus_lines.append(f"system_error_rate {metrics['performance']['error_rate']}")
                
                prometheus_lines.append("# HELP system_memory_usage_mb Memory usage in MB")
                prometheus_lines.append("# TYPE system_memory_usage_mb gauge")
                prometheus_lines.append(f"system_memory_usage_mb {metrics['performance']['memory_usage_mb']}")
                
                prometheus_lines.append("# HELP system_cpu_usage_percent CPU usage percentage")
                prometheus_lines.append("# TYPE system_cpu_usage_percent gauge")
                prometheus_lines.append(f"system_cpu_usage_percent {metrics['performance']['cpu_usage_percent']}")
                
                prometheus_lines.append("# HELP system_items_per_second System throughput in items per second")
                prometheus_lines.append("# TYPE system_items_per_second gauge")
                prometheus_lines.append(f"system_items_per_second {metrics['performance']['items_per_second']}")
                
                # Component-level metrics
                prometheus_lines.append("# HELP component_health Component health status (1=healthy, 0=unhealthy)")
                prometheus_lines.append("# TYPE component_health gauge")
                for comp_name, comp_data in metrics['detailed_components'].items():
                    # Check if component is healthy (prefer is_healthy, fallback to health_status)
                    if 'is_healthy' in comp_data:
                        health_value = 1 if comp_data['is_healthy'] else 0
                    else:
                        health_value = 1 if comp_data.get('health_status') == 'healthy' else 0
                    prometheus_lines.append(f'component_health{{component="{comp_name}"}} {health_value}')
                
                prometheus_lines.append("# HELP component_items_processed Total items processed by component")
                prometheus_lines.append("# TYPE component_items_processed counter")
                for comp_name, comp_data in metrics['detailed_components'].items():
                    prometheus_lines.append(f'component_items_processed{{component="{comp_name}"}} {comp_data["items_processed"]}')
                
                prometheus_lines.append("# HELP component_errors_total Total errors encountered by component")
                prometheus_lines.append("# TYPE component_errors_total counter")
                for comp_name, comp_data in metrics['detailed_components'].items():
                    # Use error_count if available, fallback to errors_encountered
                    error_count = comp_data.get("errors_encountered", comp_data.get("error_count", 0))
                    prometheus_lines.append(f'component_errors_total{{component="{comp_name}"}} {error_count}')
                
                # Circuit breaker metrics
                prometheus_lines.append("# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)")
                prometheus_lines.append("# TYPE circuit_breaker_state gauge")
                for comp_name, cb_data in metrics['circuit_breakers'].items():
                    state_value = {"closed": 0, "open": 1, "half_open": 2}.get(cb_data.get("state", "closed"), 0)
                    prometheus_lines.append(f'circuit_breaker_state{{component="{comp_name}"}} {state_value}')
                
                # Trace metrics
                prometheus_lines.append("# HELP active_traces_total Number of active distributed traces")
                prometheus_lines.append("# TYPE active_traces_total gauge")
                prometheus_lines.append(f"active_traces_total {metrics['traces']['total_traces']}")
                
                prometheus_lines.append("# HELP active_spans_total Number of active tracing spans")
                prometheus_lines.append("# TYPE active_spans_total gauge")
                prometheus_lines.append(f"active_spans_total {metrics['traces']['active_spans']}")
                
                # Alert metrics
                alert_counts = {"critical": 0, "warning": 0, "info": 0}
                for alert in metrics['alerts']:
                    level = alert.get('level', 'info')
                    alert_counts[level] = alert_counts.get(level, 0) + 1
                
                prometheus_lines.append("# HELP system_alerts_total Number of active alerts by severity")
                prometheus_lines.append("# TYPE system_alerts_total gauge")
                for level, count in alert_counts.items():
                    prometheus_lines.append(f'system_alerts_total{{severity="{level}"}} {count}')
                
                return "\n".join(prometheus_lines) + "\n"
                
            except Exception as e:
                self.logger.error(f"Prometheus endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/prometheus")
        async def prometheus_legacy():
            """Legacy prometheus endpoint - redirects to /metrics"""
            return await prometheus_metrics()