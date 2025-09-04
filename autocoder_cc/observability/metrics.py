#!/usr/bin/env python3
"""
Metrics Collection - Enterprise Roadmap v3 Phase 1
OpenTelemetry-compatible metrics for component performance and system health
"""
import os
import time
import threading
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock
from autocoder_cc.core.config import settings
from autocoder_cc.observability.structured_logging import get_logger


@dataclass
class MetricPoint:
    """Single metric measurement point"""
    name: str
    value: Union[int, float]
    tags: Dict[str, str]
    timestamp: float
    metric_type: str  # counter, gauge, histogram, summary


@dataclass 
class MetricSeries:
    """Time series of metric points"""
    name: str
    metric_type: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    total_count: int = 0
    
    def add_point(self, value: Union[int, float], tags: Dict[str, str]):
        """Add a metric point to the series"""
        point = MetricPoint(
            name=self.name,
            value=value,
            tags=tags,
            timestamp=time.time(),
            metric_type=self.metric_type
        )
        self.points.append(point)
        self.total_count += 1


class MetricsCollector:
    """
    Metrics collector with OpenTelemetry integration and enterprise features.
    
    Features:
    - Counter, Gauge, Histogram metrics
    - Tag-based dimensionality
    - Time-windowed aggregations
    - Component-level metrics isolation
    - Performance monitoring
    - Health metrics
    - Business metrics
    """
    
    # Class-level server management for proper cleanup
    _prometheus_server = None
    _prometheus_server_started = False
    _server_shutdown_event = None
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.metrics: Dict[str, MetricSeries] = {}
        self.lock = Lock()
        self.logger = get_logger(f"MetricsCollector.{component_name}")
        
        # Check for generation mode flag to skip external connections
        self.generation_mode = os.getenv('AUTOCODER_GENERATION_MODE', 'false').lower() == 'true'
        
        if self.generation_mode:
            self.logger.info(f"Metrics collector {component_name} in generation mode - skipping external connections")
            # Initialize minimal stubs for generation mode
            self.meter = None
            self.otel_counters = {}
            self.otel_gauges = {}
            self.otel_histograms = {}
        else:
            # Initialize OpenTelemetry metrics if available
            self._init_otel_metrics()
            
            # Setup actual metric exporters if enabled
            if settings.ENABLE_METRICS:
                self._setup_metric_exporters()
    
    def _init_otel_metrics(self):
        """Initialize OpenTelemetry metrics instruments"""
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            
            # Set up meter - version parameter not supported in OpenTelemetry 1.21.0
            self.meter = metrics.get_meter(
                f"autocoder.{self.component_name}"
            )
            
            # Create common instruments
            self.otel_counters = {}
            self.otel_gauges = {}
            self.otel_histograms = {}
            
        except ImportError:
            # OpenTelemetry not available, use internal metrics only
            self.meter = None
            self.otel_counters = {}
            self.otel_gauges = {}
            self.otel_histograms = {}
    
    def _setup_metric_exporters(self):
        """Setup actual backend exporters for metrics"""
        try:
            from opentelemetry.exporter.prometheus import PrometheusMetricReader
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry import metrics
            import threading
            import http.server
            import socketserver
            
            # Setup Prometheus exporter
            prometheus_reader = PrometheusMetricReader()
            meter_provider = MeterProvider(metric_readers=[prometheus_reader])
            metrics.set_meter_provider(meter_provider)
            
            # Start Prometheus metrics server
            if MetricsCollector._prometheus_server_started:
                return  # Already started
            
            # Create shutdown event for graceful shutdown
            MetricsCollector._server_shutdown_event = threading.Event()
            
            def start_prometheus_server():
                """Start production-grade Prometheus metrics server"""
                try:
                    from prometheus_client import start_http_server, CONTENT_TYPE_LATEST, generate_latest
                    import http.server
                    import socketserver
                    import socket
                    
                    # Use prometheus_client's built-in production server for concurrent handling
                    try:
                        # This uses a threaded server that can handle concurrent requests
                        httpd = start_http_server(settings.METRICS_PORT)
                        MetricsCollector._prometheus_server = httpd
                        
                        module_logger = get_logger("MetricsCollector.PrometheusServer")
                        module_logger.info(f"Production Prometheus server running on port {settings.METRICS_PORT}")
                        
                        # Wait for shutdown signal
                        MetricsCollector._server_shutdown_event.wait()
                        
                        # Graceful shutdown
                        if hasattr(httpd, 'shutdown'):
                            httpd.shutdown()
                        module_logger.info("Prometheus server shut down gracefully")
                        
                    except Exception as e:
                        # Fallback to custom concurrent server implementation
                        module_logger = get_logger("MetricsCollector.PrometheusServer")
                        module_logger.warning(f"Built-in server failed ({e}), using custom concurrent implementation")
                        
                        class MetricsHandler(http.server.BaseHTTPRequestHandler):
                            def do_GET(self):
                                if self.path == '/metrics':
                                    # Serve Prometheus metrics
                                    self.send_response(200)
                                    self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                                    self.end_headers()
                                    self.wfile.write(generate_latest())
                                elif self.path == '/health':
                                    # Health check endpoint
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'text/plain')
                                    self.end_headers()
                                    self.wfile.write(b'OK')
                                else:
                                    self.send_response(404)
                                    self.end_headers()
                                    self.wfile.write(b'Not Found')
                            
                            def log_message(self, format, *args):
                                # Suppress default HTTP server logging
                                pass
                        
                        class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
                            """Thread per request HTTP server for concurrent handling"""
                            daemon_threads = True
                            allow_reuse_address = True
                        
                        httpd = ThreadedHTTPServer(("", settings.METRICS_PORT), MetricsHandler)
                        MetricsCollector._prometheus_server = httpd
                        
                        module_logger.info(f"Concurrent Prometheus server running on port {settings.METRICS_PORT}")
                        
                        # Serve until shutdown event with proper threading
                        httpd.timeout = 1.0
                        while not MetricsCollector._server_shutdown_event.is_set():
                            try:
                                httpd.handle_request()
                            except socket.timeout:
                                continue
                            except Exception as e:
                                module_logger.error(f"Error handling request: {e}")
                                continue
                        
                        httpd.server_close()
                        module_logger.info("Concurrent Prometheus server shut down")
                    
                except ImportError:
                    # FAIL FAST: Don't start a broken metrics server
                    module_logger = get_logger("MetricsCollector.PrometheusServer")
                    module_logger.error("prometheus_client not available - metrics server cannot start")
                    raise ImportError(
                        "prometheus_client library is required for metrics server. "
                        "Install with: pip install prometheus_client"
                    )
                    
                except Exception as e:
                    module_logger = get_logger("MetricsCollector.PrometheusServer")
                    module_logger.error(f"Failed to start Prometheus server: {e}")
            
            # Start server in background thread
            server_thread = threading.Thread(target=start_prometheus_server, daemon=True)
            server_thread.start()
            
            # Mark as started (class-level to avoid multiple servers)
            MetricsCollector._prometheus_server_started = True
            
        except ImportError as e:
            # FAIL FAST - No graceful degradation
            raise RuntimeError(
                "CRITICAL: Prometheus exporter not available. "
                "System requires metrics export capability. "
                "Install opentelemetry-exporter-prometheus: "
                "pip install opentelemetry-exporter-prometheus"
            ) from e
        except Exception as e:
            # FAIL FAST - Don't hide errors
            raise RuntimeError(
                f"CRITICAL: Failed to setup metric exporters: {e}. "
                "System cannot function without metrics collection."
            ) from e
    
    def _get_or_create_series(self, name: str, metric_type: str) -> MetricSeries:
        """Get or create metric series"""
        series_key = f"{name}:{metric_type}"
        
        if series_key not in self.metrics:
            self.metrics[series_key] = MetricSeries(
                name=name,
                metric_type=metric_type
            )
        
        return self.metrics[series_key]
    
    def _get_otel_counter(self, name: str):
        """Get or create OpenTelemetry counter"""
        if self.meter and name not in self.otel_counters:
            self.otel_counters[name] = self.meter.create_counter(
                name=f"{self.component_name}_{name}",
                description=f"Counter for {name} in {self.component_name}",
                unit="1"
            )
        return self.otel_counters.get(name)
    
    def _get_otel_gauge(self, name: str):
        """Get or create OpenTelemetry gauge"""
        if self.meter and name not in self.otel_gauges:
            self.otel_gauges[name] = self.meter.create_up_down_counter(
                name=f"{self.component_name}_{name}",
                description=f"Gauge for {name} in {self.component_name}",
                unit="1"
            )
        return self.otel_gauges.get(name)
    
    def _get_otel_histogram(self, name: str):
        """Get or create OpenTelemetry histogram"""
        if self.meter and name not in self.otel_histograms:
            self.otel_histograms[name] = self.meter.create_histogram(
                name=f"{self.component_name}_{name}",
                description=f"Histogram for {name} in {self.component_name}",
                unit="ms"
            )
        return self.otel_histograms.get(name)
    
    def counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Record counter metric (monotonically increasing)"""
        tags = tags or {}
        tags['component'] = self.component_name
        
        with self.lock:
            # Internal metrics
            series = self._get_or_create_series(name, 'counter')
            series.add_point(value, tags)
            
            # OpenTelemetry metrics
            otel_counter = self._get_otel_counter(name)
            if otel_counter:
                otel_counter.add(value, tags)
    
    def gauge(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Record gauge metric (current value)"""
        tags = tags or {}
        tags['component'] = self.component_name
        
        with self.lock:
            # Internal metrics
            series = self._get_or_create_series(name, 'gauge')
            series.add_point(value, tags)
            
            # OpenTelemetry metrics
            otel_gauge = self._get_otel_gauge(name)
            if otel_gauge:
                # For gauge, we set the absolute value
                if hasattr(otel_gauge, 'set'):
                    otel_gauge.set(value, tags)
                else:
                    # Fallback for up_down_counter
                    otel_gauge.add(value, tags)
    
    def histogram(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Record histogram metric (distribution of values)"""
        tags = tags or {}
        tags['component'] = self.component_name
        
        with self.lock:
            # Internal metrics
            series = self._get_or_create_series(name, 'histogram')
            series.add_point(value, tags)
            
            # OpenTelemetry metrics
            otel_histogram = self._get_otel_histogram(name)
            if otel_histogram:
                otel_histogram.record(value, tags)
    
    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record timing metric (specialized histogram for durations)"""
        self.histogram(f"{name}_duration", duration_ms, tags)
    
    def increment(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Increment counter by 1"""
        self.counter(name, 1, tags)
    
    def decrement(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Decrement gauge by 1"""
        self.gauge(name, -1, tags)
    
    # Component-specific metrics
    def record_component_start(self):
        """Record component start event"""
        self.counter('component_starts', tags={'event': 'start'})
        self.gauge('component_status', 1, tags={'status': 'running'})
    
    def record_component_stop(self):
        """Record component stop event"""
        self.counter('component_stops', tags={'event': 'stop'})
        self.gauge('component_status', 0, tags={'status': 'stopped'})
    
    def record_items_processed(self, count: int = 1):
        """Record number of items processed"""
        self.counter('items_processed', count)
    
    def record_processing_time(self, duration_ms: float):
        """Record item processing time"""
        self.timing('item_processing', duration_ms)
    
    def record_error(self, error_type: str):
        """Record error occurrence"""
        self.counter('errors', tags={'error_type': error_type})
    
    def record_system_generated(self, tags: Optional[Dict[str, str]] = None):
        """Record system generation event"""
        self.counter('system_generated', tags=tags)
    
    def record_generation_time(self, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record system generation time"""
        self.timing('generation', duration_ms, tags)
    
    def record_health_status(self, status: str, health_score: float):
        """Record component health status"""
        self.gauge('health_score', health_score, tags={'status': status})
        self.counter('health_checks', tags={'status': status})
    
    # Performance metrics
    def record_memory_usage(self, bytes_used: int):
        """Record memory usage"""
        self.gauge('memory_usage_bytes', bytes_used)
    
    def record_cpu_usage(self, percentage: float):
        """Record CPU usage percentage"""
        self.gauge('cpu_usage_percent', percentage)
    
    def record_queue_size(self, queue_name: str, size: int):
        """Record queue size"""
        self.gauge('queue_size', size, tags={'queue': queue_name})
    
    def record_active_connections(self, count: int):
        """Record number of active connections"""
        self.gauge('active_connections', count)
    
    def record_gauge(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """
        Record gauge metric - compatibility method for generated components.
        
        This method exists to support generated components that expect record_gauge()
        instead of the plain gauge() method. It simply delegates to gauge().
        
        Args:
            name: Metric name
            value: Gauge value (int or float)
            tags: Optional metric tags/labels
        """
        self.gauge(name, value, tags)
    
    # Business metrics
    def record_business_event(self, event_type: str, value: Union[int, float] = 1):
        """Record business event"""
        self.counter('business_events', value, tags={'event_type': event_type})
    
    def record_user_action(self, action: str, user_id: str):
        """Record user action"""
        self.counter('user_actions', tags={'action': action, 'user_id': user_id})
    
    def record_api_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Record API request metrics"""
        tags = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        }
        
        self.counter('api_requests', tags=tags)
        self.timing('api_request', duration_ms, tags)
        
        # Record error if status indicates failure
        if status_code >= 400:
            self.record_error(f"http_{status_code}")
    
    # Aggregation methods
    def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value"""
        series = self.metrics.get(f"{name}:counter")
        if not series:
            return 0
        
        if not tags:
            return len(series.points)
        
        # Filter by tags
        count = 0
        for point in series.points:
            if all(point.tags.get(k) == v for k, v in tags.items()):
                count += point.value
        
        return count
    
    def get_gauge_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get latest gauge value"""
        series = self.metrics.get(f"{name}:gauge")
        if not series or not series.points:
            return None
        
        # Get most recent matching point
        for point in reversed(series.points):
            if not tags or all(point.tags.get(k) == v for k, v in tags.items()):
                return point.value
        
        return None
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        series = self.metrics.get(f"{name}:histogram")
        if not series:
            # FAIL FAST - No graceful degradation
            raise ValueError(
                f"CRITICAL: Histogram '{name}' not found in metrics. "
                "Cannot get statistics for non-existent histogram."
            )
        
        # Filter points by tags
        values = []
        for point in series.points:
            if not tags or all(point.tags.get(k) == v for k, v in tags.items()):
                values.append(point.value)
        
        if not values:
            # FAIL FAST - No graceful degradation
            raise ValueError(
                f"CRITICAL: No values found for histogram '{name}' with tags {tags}. "
                "Cannot compute statistics without data."
            )
        
        values.sort()
        count = len(values)
        
        return {
            'count': count,
            'min': values[0],
            'max': values[-1],
            'mean': sum(values) / count,
            'p50': values[int(count * 0.5)],
            'p95': values[int(count * 0.95)],
            'p99': values[int(count * 0.99)]
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            'component': self.component_name,
            'timestamp': time.time(),
            'counters': {},
            'gauges': {},
            'histograms': {}
        }
        
        for series_key, series in self.metrics.items():
            name, metric_type = series_key.split(':', 1)
            
            if metric_type == 'counter':
                summary['counters'][name] = self.get_counter_value(name)
            elif metric_type == 'gauge':
                summary['gauges'][name] = self.get_gauge_value(name)
            elif metric_type == 'histogram':
                summary['histograms'][name] = self.get_histogram_stats(name)
        
        return summary
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for series_key, series in self.metrics.items():
            name, metric_type = series_key.split(':', 1)
            
            # Add help and type comments
            lines.append(f"# HELP {self.component_name}_{name} {name} metric for {self.component_name}")
            lines.append(f"# TYPE {self.component_name}_{name} {metric_type}")
            
            if metric_type == 'counter':
                value = self.get_counter_value(name)
                lines.append(f"{self.component_name}_{name}{{component=\"{self.component_name}\"}} {value}")
            elif metric_type == 'gauge':
                value = self.get_gauge_value(name)
                if value is not None:
                    lines.append(f"{self.component_name}_{name}{{component=\"{self.component_name}\"}} {value}")
        
        return '\n'.join(lines)
    
    def cleanup(self):
        """Cleanup metrics collector resources"""
        try:
            # Stop background Prometheus server if running
            if MetricsCollector._prometheus_server_started and MetricsCollector._server_shutdown_event:
                self.logger.info("Shutting down Prometheus metrics server...")
                MetricsCollector._server_shutdown_event.set()
                
                # Close server socket if available
                if MetricsCollector._prometheus_server:
                    try:
                        MetricsCollector._prometheus_server.shutdown()
                        MetricsCollector._prometheus_server.server_close()
                    except Exception as e:
                        self.logger.warning(f"Error closing Prometheus server: {e}")
                
                MetricsCollector._prometheus_server_started = False
                MetricsCollector._prometheus_server = None
                MetricsCollector._server_shutdown_event = None
            
            # Clear OpenTelemetry resources
            if hasattr(self, 'otel_counters'):
                self.otel_counters.clear()
            if hasattr(self, 'otel_gauges'):
                self.otel_gauges.clear()  
            if hasattr(self, 'otel_histograms'):
                self.otel_histograms.clear()
            
            # Clear metrics cache
            with self.lock:
                self.metrics.clear()
            
            self.logger.info(f"MetricsCollector for {self.component_name} cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during metrics collector cleanup: {e}")


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str, 
                 tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.metrics_collector.timing(self.metric_name, duration_ms, self.tags)
        
        # Record error if exception occurred
        if exc_type:
            self.metrics_collector.record_error(exc_type.__name__)
        
        return False  # Don't suppress exceptions


# Global metrics registry
_metrics_registry: Dict[str, MetricsCollector] = {}


def get_metrics_collector(component_name: str) -> MetricsCollector:
    """Get or create metrics collector for a component"""
    
    if component_name not in _metrics_registry:
        _metrics_registry[component_name] = MetricsCollector(component_name)
    
    return _metrics_registry[component_name]


def get_system_metrics() -> Dict[str, Any]:
    """Get system-wide metrics summary"""
    system_summary = {
        'timestamp': time.time(),
        'components': {}
    }
    
    for component_name, collector in _metrics_registry.items():
        system_summary['components'][component_name] = collector.get_metrics_summary()
    
    return system_summary


def export_all_prometheus() -> str:
    """Export all metrics in Prometheus format"""
    lines = []
    
    for component_name, collector in _metrics_registry.items():
        lines.append(collector.export_prometheus())
        lines.append('')  # Blank line between components
    
    return '\n'.join(lines)