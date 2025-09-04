from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Autocoder 3.3 Observability Framework
Provides metrics collection, tracing, and monitoring capabilities
"""
import time
import anyio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import defaultdict, deque


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Represents a metric value with metadata"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    component: Optional[str] = None


@dataclass
class SpanContext:
    """Tracing span context"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)


class Span:
    """
    Distributed tracing span
    """
    
    def __init__(self, operation_name: str, context: SpanContext, tracer: 'Tracer'):
        self.operation_name = operation_name
        self.context = context
        self.tracer = tracer
        
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration_ms: Optional[float] = None
        
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.error: Optional[Exception] = None
        self.finished = False
    
    def set_tag(self, key: str, value: Any):
        """Set a tag on the span"""
        self.tags[key] = value
        return self
    
    def set_error(self, error: Exception):
        """Mark span as having an error"""
        self.error = error
        self.tags['error'] = True
        self.tags['error.message'] = str(error)
        self.tags['error.type'] = error.__class__.__name__
    
    def log(self, event: str, **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            'event': event,
            'timestamp': datetime.now(),
            **kwargs
        }
        self.logs.append(log_entry)
    
    def finish(self):
        """Finish the span"""
        if self.finished:
            return
        
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.finished = True
        
        # Notify tracer
        self.tracer._finish_span(self)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.set_error(exc_val)
        self.finish()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization"""
        return {
            'operation_name': self.operation_name,
            'trace_id': self.context.trace_id,
            'span_id': self.context.span_id,
            'parent_span_id': self.context.parent_span_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'tags': self.tags,
            'logs': [{**log, 'timestamp': log['timestamp'].isoformat()} for log in self.logs],
            'error': str(self.error) if self.error else None
        }


class Tracer:
    """
    Distributed tracing implementation
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.spans: List[Span] = []
        self.active_spans: Dict[str, Span] = {}
        self.span_counter = 0
        self.logger = get_logger(f"Tracer.{service_name}")
    
    def start_span(self, operation_name: str, parent_context: Optional[SpanContext] = None) -> Span:
        """Start a new tracing span"""
        
        # Generate trace and span IDs
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = f"trace_{int(time.time() * 1000)}_{self.span_counter}"
            parent_span_id = None
        
        span_id = f"span_{self.span_counter}_{int(time.time() * 1000000)}"
        self.span_counter += 1
        
        # Create span context
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=parent_context.baggage.copy() if parent_context else {}
        )
        
        # Create and register span
        span = Span(operation_name, context, self)
        self.active_spans[span_id] = span
        
        # Add service tag
        span.set_tag('service.name', self.service_name)
        
        self.logger.debug(f"Started span: {operation_name} (trace: {trace_id}, span: {span_id})")
        return span
    
    def span(self, operation_name: str, parent_context: Optional[SpanContext] = None) -> Span:
        """Context manager for creating spans"""
        return self.start_span(operation_name, parent_context)
    
    def _finish_span(self, span: Span):
        """Called when a span finishes"""
        if span.context.span_id in self.active_spans:
            del self.active_spans[span.context.span_id]
        
        self.spans.append(span)
        
        # Log span completion
        status = "ERROR" if span.error else "OK"
        self.logger.debug(f"Finished span: {span.operation_name} [{status}] ({span.duration_ms:.2f}ms)")
    
    def get_spans(self, trace_id: Optional[str] = None) -> List[Span]:
        """Get spans, optionally filtered by trace ID"""
        if trace_id:
            return [span for span in self.spans if span.context.trace_id == trace_id]
        return self.spans.copy()
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary information for a trace"""
        trace_spans = self.get_spans(trace_id)
        
        if not trace_spans:
            return {}
        
        # Calculate trace statistics
        total_duration = max(span.duration_ms or 0 for span in trace_spans)
        error_count = sum(1 for span in trace_spans if span.error)
        
        return {
            'trace_id': trace_id,
            'span_count': len(trace_spans),
            'total_duration_ms': total_duration,
            'error_count': error_count,
            'has_errors': error_count > 0,
            'operations': list(set(span.operation_name for span in trace_spans)),
            'start_time': min(span.start_time for span in trace_spans).isoformat(),
            'spans': [span.to_dict() for span in trace_spans]
        }


class MetricsCollector:
    """
    Metrics collection and aggregation system
    """
    
    def __init__(self, component_name: str, level: str = "basic"):
        self.component_name = component_name
        self.level = level
        
        # Metric storage
        self.metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # Configuration
        self.max_metric_history = 10000
        self.collection_interval = 60  # seconds
        
        # Background collection task management
        self.task_group: Optional[anyio.abc.TaskGroup] = None
        self.running = False
        
        self.logger = get_logger(f"MetricsCollector.{component_name}")
        self.logger.info(f"Initialized metrics collector for {component_name} (level: {level})")
    
    async def start_collection(self):
        """Start background metrics collection"""
        if self.running:
            return
        
        self.running = True
        self.task_group = anyio.create_task_group()
        await self.task_group.__aenter__()
        self.task_group.start_soon(self._collection_loop)
        self.logger.info("Started metrics collection")
    
    async def stop_collection(self):
        """Stop background metrics collection"""
        if not self.running:
            return
        
        self.running = False
        if self.task_group:
            try:
                await self.task_group.__aexit__(None, None, None)
                self.task_group = None
            except Exception:
                # Task group may already be closed
                pass
        
        self.logger.info("Stopped metrics collection")
    
    def record_counter(self, metric_name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record a counter metric (always increasing)"""
        labels = labels or {}
        
        self.counters[metric_name] += value
        
        metric = MetricValue(
            name=metric_name,
            value=self.counters[metric_name],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            labels=labels,
            component=self.component_name
        )
        
        self._store_metric(metric)
    
    def record_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric (current value)"""
        labels = labels or {}
        
        self.gauges[metric_name] = value
        
        metric = MetricValue(
            name=metric_name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            labels=labels,
            component=self.component_name
        )
        
        self._store_metric(metric)
    
    def record_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric (distribution of values)"""
        labels = labels or {}
        
        self.histograms[metric_name].append(value)
        
        metric = MetricValue(
            name=metric_name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=datetime.now(),
            labels=labels,
            component=self.component_name
        )
        
        self._store_metric(metric)
    
    def record_timer(self, metric_name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record a timer metric (duration measurement)"""
        labels = labels or {}
        
        self.timers[metric_name].append(duration_ms)
        
        metric = MetricValue(
            name=metric_name,
            value=duration_ms,
            metric_type=MetricType.TIMER,
            timestamp=datetime.now(),
            labels=labels,
            component=self.component_name
        )
        
        self._store_metric(metric)
    
    def record_success(self, metric_name: str, duration_ms: float = None, labels: Dict[str, str] = None):
        """Record a successful operation"""
        labels = labels or {}
        
        self.record_counter(f"{metric_name}_success", 1.0, labels)
        self.record_counter(f"{metric_name}_total", 1.0, labels)
        
        if duration_ms is not None:
            self.record_timer(f"{metric_name}_duration", duration_ms, labels)
    
    def record_failure(self, metric_name: str, error: str = None, labels: Dict[str, str] = None):
        """Record a failed operation"""
        labels = labels or {}
        if error:
            labels['error'] = error
        
        self.record_counter(f"{metric_name}_failure", 1.0, labels)
        self.record_counter(f"{metric_name}_total", 1.0, labels)
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        
        # Counter summary
        if metric_name in self.counters:
            return {
                'type': 'counter',
                'name': metric_name,
                'value': self.counters[metric_name],
                'component': self.component_name
            }
        
        # Gauge summary
        if metric_name in self.gauges:
            return {
                'type': 'gauge',
                'name': metric_name,
                'value': self.gauges[metric_name],
                'component': self.component_name
            }
        
        # Histogram summary
        if metric_name in self.histograms:
            values = list(self.histograms[metric_name])
            if values:
                return {
                    'type': 'histogram',
                    'name': metric_name,
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 50),
                    'p95': self._percentile(values, 95),
                    'p99': self._percentile(values, 99),
                    'component': self.component_name
                }
        
        # Timer summary
        if metric_name in self.timers:
            values = self.timers[metric_name]
            if values:
                return {
                    'type': 'timer',
                    'name': metric_name,
                    'count': len(values),
                    'min_ms': min(values),
                    'max_ms': max(values),
                    'avg_ms': sum(values) / len(values),
                    'p50_ms': self._percentile(values, 50),
                    'p95_ms': self._percentile(values, 95),
                    'p99_ms': self._percentile(values, 99),
                    'component': self.component_name
                }
        
        return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics summaries"""
        summaries = {}
        
        # Get all metric names
        all_metrics = set()
        all_metrics.update(self.counters.keys())
        all_metrics.update(self.gauges.keys())
        all_metrics.update(self.histograms.keys())
        all_metrics.update(self.timers.keys())
        
        for metric_name in all_metrics:
            summary = self.get_metric_summary(metric_name)
            if summary:
                summaries[metric_name] = summary
        
        return summaries
    
    def _store_metric(self, metric: MetricValue):
        """Store metric in history"""
        self.metrics[metric.name].append(metric)
        
        # Trim history if needed
        if len(self.metrics[metric.name]) > self.max_metric_history:
            self.metrics[metric.name] = self.metrics[metric.name][-self.max_metric_history:]
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = f + 1
        
        if f == c:
            return sorted_values[f]
        
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while self.running:
            try:
                # Collect system metrics if detailed level
                if self.level in ['detailed', 'debug']:
                    await self._collect_system_metrics()
                
                await anyio.sleep(self.collection_interval)
                
            except anyio.get_cancelled_exc_class():
                break
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await anyio.sleep(1)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.record_gauge('system_cpu_percent', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge('system_memory_percent', memory.percent)
            self.record_gauge('system_memory_used_bytes', memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_gauge('system_disk_percent', disk.percent)
            
        except ImportError:
            # psutil not available, skip system metrics
            pass
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def close(self):
        """Close metrics collector"""
        if self.task_group:
            # Note: close() is synchronous, so we just mark as not running
            # Actual cleanup should be done via stop_collection()
            self.running = False


class Timer:
    """
    Context manager for timing operations
    """
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str, labels: Dict[str, str] = None):
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.duration_ms = (time.time() - self.start_time) * 1000
            self.metrics_collector.record_timer(self.metric_name, self.duration_ms, self.labels)
    
    def get_duration_ms(self) -> Optional[float]:
        """Get the measured duration in milliseconds"""
        return self.duration_ms


def create_timer(metrics_collector: MetricsCollector, metric_name: str, labels: Dict[str, str] = None) -> Timer:
    """Create a timer context manager"""
    return Timer(metrics_collector, metric_name, labels)