"""
Autocoder Observability Stack - Enterprise Roadmap v3 Phase 1
Structured logging, metrics, and tracing for production operations
"""
from .structured_logging import StructuredLogger, get_logger
from .metrics import MetricsCollector, get_metrics_collector
from .tracing import TracingManager, get_tracer

# Import Tracer from the legacy observability module for compatibility
try:
    from ..observability import Tracer
except ImportError:
    # Fallback if the legacy module is missing
    class Tracer:
        def __init__(self, name):
            self.name = name

__all__ = [
    'StructuredLogger',
    'get_logger',
    'MetricsCollector', 
    'get_metrics_collector',
    'TracingManager',
    'get_tracer',
    'Tracer'
]