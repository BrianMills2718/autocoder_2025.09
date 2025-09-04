#!/usr/bin/env python3
"""
Distributed Tracing - Enterprise Roadmap v3 Phase 1
OpenTelemetry-compatible distributed tracing for component communication
"""
import time
import uuid
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from contextlib import contextmanager
from threading import local
from autocoder_cc.core.config import settings
from .otel_config import configure_otel_logging


@dataclass
class SpanData:
    """Internal span data for tracing"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    component: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error, timeout
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    def is_finished(self) -> bool:
        """Check if span is finished"""
        return self.end_time is not None


class TracingManager:
    """
    Distributed tracing manager with OpenTelemetry integration.
    
    Features:
    - Distributed trace context propagation
    - Component communication tracing
    - Performance timing
    - Error and exception tracking
    - Tag-based span annotation
    - Jaeger/Zipkin export compatibility
    """
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.active_spans: Dict[str, SpanData] = {}
        self.finished_spans: List[SpanData] = []
        self.context = local()
        
        # Configure OpenTelemetry logging to suppress warnings in development
        configure_otel_logging()
        
        # Initialize OpenTelemetry tracing if available
        self._init_otel_tracing()
    
    def _init_otel_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            
            # Set up tracer - version parameter not supported in OpenTelemetry 1.21.0
            self.tracer = trace.get_tracer(
                f"autocoder.{self.component_name}"
            )
            
            # Check if tracing endpoint is configured and we're not in development
            # Skip exporter setup in development to avoid connection warnings
            if settings.ENABLE_TRACING and settings.TRACING_ENDPOINT and settings.ENVIRONMENT != "development":
                self._setup_otel_exporters()
            
        except ImportError:
            # OpenTelemetry not available
            self.tracer = None
    
    def _setup_otel_exporters(self):
        """Setup OpenTelemetry exporters"""
        try:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry import trace
            
            # Setup TracerProvider if not already set
            if not hasattr(trace.get_tracer_provider(), 'add_span_processor'):
                trace.set_tracer_provider(TracerProvider())
            
            # Determine exporter type from endpoint
            if 'jaeger' in settings.TRACING_ENDPOINT.lower():
                exporter = JaegerExporter(
                    agent_host_name=settings.JAEGER_AGENT_HOST,
                    agent_port=settings.JAEGER_AGENT_PORT,
                )
            else:
                # Default to OTLP
                exporter = OTLPSpanExporter(
                    endpoint=settings.TRACING_ENDPOINT,
                    insecure=True  # Use insecure for local development
                )
            
            # Add span processor
            span_processor = BatchSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
        except ImportError:
            # Exporters not available
            pass
        except Exception as e:
            # Handle any other OpenTelemetry setup errors gracefully
            pass
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        return uuid.uuid4().hex[:16]
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return uuid.uuid4().hex
    
    def _get_current_span_context(self) -> Optional[SpanData]:
        """Get current span from context"""
        return getattr(self.context, 'current_span', None)
    
    def _set_current_span_context(self, span: Optional[SpanData]):
        """Set current span in context"""
        self.context.current_span = span
    
    def start_span(self, operation_name: str, 
                   parent_span_id: Optional[str] = None,
                   tags: Optional[Dict[str, str]] = None) -> str:
        """
        Start a new span.
        
        Args:
            operation_name: Name of the operation being traced
            parent_span_id: ID of parent span (if any)
            tags: Additional tags for the span
            
        Returns:
            Span ID for the created span
        """
        # Get or create trace context
        current_span = self._get_current_span_context()
        
        if current_span and not parent_span_id:
            # Use current span as parent
            parent_span_id = current_span.span_id
            trace_id = current_span.trace_id
        elif parent_span_id:
            # Find parent span to get trace ID
            parent_span = self.active_spans.get(parent_span_id)
            trace_id = parent_span.trace_id if parent_span else self._generate_trace_id()
        else:
            # New trace
            trace_id = self._generate_trace_id()
        
        # Create span
        span_id = self._generate_span_id()
        span_data = SpanData(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            component=self.component_name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        # Store active span
        self.active_spans[span_id] = span_data
        
        # Set as current span
        self._set_current_span_context(span_data)
        
        # Start OpenTelemetry span if available
        if self.tracer:
            otel_span = self.tracer.start_span(
                name=f"{self.component_name}.{operation_name}",
                attributes={
                    'component': self.component_name,
                    'operation': operation_name,
                    **span_data.tags
                }
            )
            span_data.otel_span = otel_span
        
        return span_id
    
    def finish_span(self, span_id: str, status: str = "ok", 
                   error: Optional[Exception] = None):
        """
        Finish a span.
        
        Args:
            span_id: ID of span to finish
            status: Final status (ok, error, timeout)
            error: Exception if span failed
        """
        try:
            from opentelemetry import trace
        except ImportError:
            trace = None
        span_data = self.active_spans.get(span_id)
        if not span_data:
            return
        
        # Set end time and status
        span_data.end_time = time.time()
        span_data.status = status
        
        # Add error information if provided
        if error:
            span_data.tags['error'] = str(error)
            span_data.tags['error.type'] = error.__class__.__name__
            span_data.logs.append({
                'timestamp': time.time(),
                'level': 'error',
                'message': str(error)
            })
        
        # Finish OpenTelemetry span
        if hasattr(span_data, 'otel_span'):
            otel_span = span_data.otel_span
            
            if error and trace:
                otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
                otel_span.record_exception(error)
            
            otel_span.end()
        
        # Move to finished spans
        self.finished_spans.append(span_data)
        del self.active_spans[span_id]
        
        # Update current span context
        if self._get_current_span_context() == span_data:
            parent_span = None
            if span_data.parent_span_id:
                parent_span = self.active_spans.get(span_data.parent_span_id)
            self._set_current_span_context(parent_span)
    
    def add_span_tag(self, span_id: str, key: str, value: str):
        """Add tag to active span"""
        span_data = self.active_spans.get(span_id)
        if span_data:
            span_data.tags[key] = value
            
            # Update OpenTelemetry span if available
            if hasattr(span_data, 'otel_span'):
                span_data.otel_span.set_attribute(key, value)
    
    def add_span_log(self, span_id: str, message: str, level: str = "info", 
                    **fields):
        """Add log entry to active span"""
        span_data = self.active_spans.get(span_id)
        if span_data:
            log_entry = {
                'timestamp': time.time(),
                'level': level,
                'message': message,
                **fields
            }
            span_data.logs.append(log_entry)
            
            # Add as event to OpenTelemetry span
            if hasattr(span_data, 'otel_span'):
                span_data.otel_span.add_event(
                    name=message,
                    attributes=fields
                )
    
    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID"""
        current_span = self._get_current_span_context()
        return current_span.span_id if current_span else None
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        current_span = self._get_current_span_context()
        return current_span.trace_id if current_span else None
    
    def inject_trace_context(self) -> Dict[str, str]:
        """
        Inject trace context for propagation to other services.
        
        Returns:
            Dictionary with trace context headers
        """
        current_span = self._get_current_span_context()
        if not current_span:
            return {}
        
        return {
            'x-trace-id': current_span.trace_id,
            'x-span-id': current_span.span_id,
            'x-parent-span-id': current_span.parent_span_id or ''
        }
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Extract trace context from headers.
        
        Args:
            headers: HTTP headers or similar context
            
        Returns:
            Extracted trace context or None
        """
        trace_id = headers.get('x-trace-id')
        span_id = headers.get('x-span-id')
        parent_span_id = headers.get('x-parent-span-id')
        
        if trace_id and span_id:
            return {
                'trace_id': trace_id,
                'parent_span_id': span_id,  # Incoming span becomes parent
                'remote_parent': parent_span_id or None
            }
        
        return None
    
    def create_child_span(self, operation_name: str, 
                         tags: Optional[Dict[str, str]] = None) -> str:
        """Create child span of current span"""
        current_span = self._get_current_span_context()
        parent_span_id = current_span.span_id if current_span else None
        
        return self.start_span(operation_name, parent_span_id, tags)
    
    @contextmanager
    def span(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for automatic span lifecycle"""
        span_id = self.start_span(operation_name, tags=tags)
        
        try:
            yield span_id
            self.finish_span(span_id, "ok")
        except Exception as e:
            self.finish_span(span_id, "error", e)
            raise
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a complete trace"""
        trace_spans = []
        
        # Get finished spans for this trace
        for span in self.finished_spans:
            if span.trace_id == trace_id:
                trace_spans.append({
                    'span_id': span.span_id,
                    'parent_span_id': span.parent_span_id,
                    'operation_name': span.operation_name,
                    'component': span.component,
                    'start_time': span.start_time,
                    'duration_ms': span.duration_ms,
                    'status': span.status,
                    'tags': span.tags
                })
        
        # Get active spans for this trace
        for span in self.active_spans.values():
            if span.trace_id == trace_id:
                trace_spans.append({
                    'span_id': span.span_id,
                    'parent_span_id': span.parent_span_id,
                    'operation_name': span.operation_name,
                    'component': span.component,
                    'start_time': span.start_time,
                    'duration_ms': None,  # Still active
                    'status': 'active',
                    'tags': span.tags
                })
        
        # Calculate trace statistics
        total_duration = 0
        error_count = 0
        for span in trace_spans:
            if span['duration_ms']:
                total_duration = max(total_duration, span['duration_ms'])
            if span['status'] == 'error':
                error_count += 1
        
        return {
            'trace_id': trace_id,
            'span_count': len(trace_spans),
            'total_duration_ms': total_duration,
            'error_count': error_count,
            'spans': trace_spans
        }
    
    def export_jaeger_format(self) -> Dict[str, Any]:
        """Export traces in Jaeger format"""
        traces = {}
        
        # Group spans by trace_id
        for span in self.finished_spans:
            if span.trace_id not in traces:
                traces[span.trace_id] = []
            
            jaeger_span = {
                'traceID': span.trace_id,
                'spanID': span.span_id,
                'parentSpanID': span.parent_span_id,
                'operationName': span.operation_name,
                'startTime': int(span.start_time * 1000000),  # microseconds
                'duration': int((span.duration_ms or 0) * 1000),  # microseconds
                'tags': [
                    {'key': k, 'type': 'string', 'value': v}
                    for k, v in span.tags.items()
                ],
                'logs': [
                    {
                        'timestamp': int(log['timestamp'] * 1000000),
                        'fields': [
                            {'key': k, 'value': str(v)}
                            for k, v in log.items() if k != 'timestamp'
                        ]
                    }
                    for log in span.logs
                ],
                'process': {
                    'serviceName': self.component_name,
                    'tags': [
                        {'key': 'component', 'type': 'string', 'value': self.component_name}
                    ]
                }
            }
            
            traces[span.trace_id].append(jaeger_span)
        
        return {
            'data': [
                {
                    'traceID': trace_id,
                    'spans': spans,
                    'processes': {
                        'p1': {
                            'serviceName': self.component_name,
                            'tags': []
                        }
                    }
                }
                for trace_id, spans in traces.items()
            ]
        }


# Global tracer registry
_tracer_registry: Dict[str, TracingManager] = {}


def get_tracer(component_name: str) -> TracingManager:
    """Get or create tracer for a component"""
    
    if component_name not in _tracer_registry:
        _tracer_registry[component_name] = TracingManager(component_name)
    
    return _tracer_registry[component_name]


def get_all_traces() -> Dict[str, Any]:
    """Get all traces from all components"""
    all_traces = {}
    
    for component_name, tracer in _tracer_registry.items():
        all_traces[component_name] = tracer.export_jaeger_format()
    
    return all_traces