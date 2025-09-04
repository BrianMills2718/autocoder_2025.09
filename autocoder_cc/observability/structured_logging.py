#!/usr/bin/env python3
"""
Structured Logging - Enterprise Roadmap v3 Phase 1
OpenTelemetry-compatible structured logging with JSON output
"""
import json
import logging
import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from autocoder_cc.core.config import settings


@dataclass
class LogEvent:
    """Structured log event"""
    timestamp: str
    level: str
    logger_name: str
    message: str
    component: Optional[str] = None
    operation: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, Union[int, float]]] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Convert to JSON string for structured output"""
        data = asdict(self)
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Extract structured data from record
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'message', 'exc_info', 'exc_text',
                          'stack_info', 'getMessage'):
                extra_data[key] = value
        
        # Create structured log event
        log_event = LogEvent(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            component=extra_data.get('component'),
            operation=extra_data.get('operation'),
            trace_id=extra_data.get('trace_id'),
            span_id=extra_data.get('span_id'),
            user_id=extra_data.get('user_id'),
            session_id=extra_data.get('session_id'),
            request_id=extra_data.get('request_id'),
            tags=extra_data.get('tags'),
            metrics=extra_data.get('metrics'),
            error=extra_data.get('error')
        )
        
        # Add exception information if present
        if record.exc_info:
            import traceback
            log_event.error = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return log_event.to_json()


class StructuredLogger:
    """
    Structured logger with OpenTelemetry integration and enterprise features.
    
    Features:
    - JSON structured output
    - OpenTelemetry trace/span correlation
    - Component and operation tagging
    - Metrics integration
    - Error context capture
    - Performance measurement
    """
    
    def __init__(self, name: str, component: Optional[str] = None):
        self.name = name
        self.component = component
        self.logger = logging.getLogger(name)
        
        # Configure structured logging if not already configured
        if not hasattr(self.logger, '_structured_configured'):
            self._configure_structured_logging()
            self.logger._structured_configured = True
    
    def _configure_structured_logging(self):
        """Configure structured JSON logging output"""
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Set level from configuration
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Console handler with structured formatter
        console_handler = logging.StreamHandler()
        
        if settings.STRUCTURED_LOGGING:
            # Use structured JSON formatter
            console_handler.setFormatter(StructuredFormatter())
        else:
            # Use traditional formatter for development
            formatter = logging.Formatter(settings.LOG_FORMAT)
            console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler for production (optional)
        if settings.ENVIRONMENT == 'production':
            log_file = Path(settings.TEMP_DIR) / 'autocoder.log'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def _get_trace_context(self) -> Dict[str, Optional[str]]:
        """Get OpenTelemetry trace context if available"""
        try:
            from opentelemetry import trace
            
            span = trace.get_current_span()
            if span and span.is_recording():
                span_context = span.get_span_context()
                return {
                    'trace_id': format(span_context.trace_id, '032x'),
                    'span_id': format(span_context.span_id, '016x')
                }
        except ImportError:
            # OpenTelemetry not available
            pass
        
        return {'trace_id': None, 'span_id': None}
    
    def _log_with_context(self, level: int, message: str, 
                         operation: Optional[str] = None,
                         tags: Optional[Dict[str, str]] = None,
                         metrics: Optional[Dict[str, Union[int, float]]] = None,
                         error: Optional[Exception] = None,
                         **kwargs):
        """Log with structured context"""
        
        # Get trace context
        trace_context = self._get_trace_context()
        
        # Prepare extra data
        extra = {
            'component': self.component,
            'operation': operation,
            'trace_id': trace_context['trace_id'],
            'span_id': trace_context['span_id'],
            'tags': tags,
            'metrics': metrics,
            **kwargs
        }
        
        # Add error context if provided
        if error:
            extra['error'] = {
                'type': error.__class__.__name__,
                'message': str(error)
            }
        
        # Log with extra context
        self.logger.log(level, message, extra=extra)
    
    def log(self, level: int, message: str, **kwargs):
        """Log message with specified level (compatible with standard logger interface)"""
        self._log_with_context(level, message, **kwargs)
    
    def debug(self, message: str, operation: Optional[str] = None, **kwargs):
        """Log debug message with structured context"""
        self._log_with_context(logging.DEBUG, message, operation=operation, **kwargs)
    
    def info(self, message: str, operation: Optional[str] = None, **kwargs):
        """Log info message with structured context"""
        self._log_with_context(logging.INFO, message, operation=operation, **kwargs)
    
    def warning(self, message: str, operation: Optional[str] = None, **kwargs):
        """Log warning message with structured context"""
        self._log_with_context(logging.WARNING, message, operation=operation, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, 
              operation: Optional[str] = None, **kwargs):
        """Log error message with structured context"""
        self._log_with_context(logging.ERROR, message, operation=operation, 
                              error=error, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None,
                operation: Optional[str] = None, **kwargs):
        """Log critical message with structured context"""
        self._log_with_context(logging.CRITICAL, message, operation=operation,
                              error=error, **kwargs)
    
    def operation_start(self, operation: str, **context) -> str:
        """Log operation start with timing"""
        operation_id = f"{operation}_{int(time.time() * 1000)}"
        
        self.info(
            f"Starting operation: {operation}",
            operation=operation,
            operation_id=operation_id,
            operation_phase="start",
            **context
        )
        
        return operation_id
    
    def operation_success(self, operation: str, operation_id: str,
                         duration_ms: Optional[float] = None, **context):
        """Log operation success with metrics"""
        metrics = {}
        if duration_ms is not None:
            metrics['duration_ms'] = duration_ms
        
        self.info(
            f"Operation completed successfully: {operation}",
            operation=operation,
            operation_id=operation_id,
            operation_phase="success",
            metrics=metrics,
            **context
        )
    
    def operation_error(self, operation: str, operation_id: str,
                       error: Exception, duration_ms: Optional[float] = None,
                       **context):
        """Log operation error with metrics"""
        metrics = {}
        if duration_ms is not None:
            metrics['duration_ms'] = duration_ms
        
        self.error(
            f"Operation failed: {operation}",
            operation=operation,
            operation_id=operation_id,
            operation_phase="error",
            error=error,
            metrics=metrics,
            **context
        )
    
    def component_health(self, health_status: str, **metrics):
        """Log component health status with metrics"""
        self.info(
            f"Component health check: {health_status}",
            operation="health_check",
            tags={'health_status': health_status},
            metrics=metrics
        )
    
    def business_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log business event for analytics"""
        self.info(
            f"Business event: {event_type}",
            operation="business_event",
            tags={'event_type': event_type},
            business_event=event_data
        )
    
    def security_event(self, event_type: str, severity: str, **context):
        """Log security event with appropriate severity"""
        level = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(severity.lower(), logging.WARNING)
        
        self._log_with_context(
            level,
            f"Security event: {event_type}",
            operation="security_event",
            tags={'event_type': event_type, 'severity': severity},
            **context
        )


class OperationTimer:
    """Context manager for timing operations with structured logging"""
    
    def __init__(self, logger: StructuredLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
        self.operation_id = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.operation_id = self.logger.operation_start(self.operation, **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            self.logger.operation_success(
                self.operation, 
                self.operation_id,
                duration_ms=duration_ms,
                **self.context
            )
        else:
            self.logger.operation_error(
                self.operation,
                self.operation_id, 
                exc_val,
                duration_ms=duration_ms,
                **self.context
            )
        
        return False  # Don't suppress exceptions


# Global logger registry for component-specific loggers
_logger_registry: Dict[str, StructuredLogger] = {}


def get_logger(name: str, component: Optional[str] = None) -> StructuredLogger:
    """Get or create a structured logger for a component"""
    
    cache_key = f"{name}:{component or 'default'}"
    
    if cache_key not in _logger_registry:
        _logger_registry[cache_key] = StructuredLogger(name, component)
    
    return _logger_registry[cache_key]


def configure_global_logging():
    """Configure global logging settings for the application"""
    
    # Set root logger level
    root_logger = logging.getLogger()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Suppress noisy third-party loggers in production
    if settings.ENVIRONMENT == 'production':
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Enable debug logging for autocoder components in debug mode
    if settings.DEBUG_MODE:
        logging.getLogger('autocoder').setLevel(logging.DEBUG)


# Configure global logging on import
configure_global_logging()