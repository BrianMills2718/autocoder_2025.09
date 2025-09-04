"""
VR1 Telemetry System

Prometheus metrics, performance monitoring, and structured logging for VR1 validation
"""

import time
import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, asdict

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .vr1_error_taxonomy import VR1ValidationError, VR1ErrorType, VR1ErrorCategory


# Prometheus metrics (when available)
if PROMETHEUS_AVAILABLE:
    vr1_validations_total = Counter(
        'vr1_validations_total', 
        'Total VR1 validations performed',
        ['result', 'blueprint_version']
    )
    
    vr1_validation_duration = Histogram(
        'vr1_validation_duration_seconds',
        'VR1 validation duration in seconds',
        ['blueprint_version', 'component_count_bucket']
    )
    
    vr1_errors_total = Counter(
        'vr1_errors_total',
        'Total VR1 validation errors by type',
        ['error_type', 'error_category']
    )
    
    vr1_ingress_points = Gauge(
        'vr1_ingress_points',
        'Number of boundary ingress points in validated blueprint'
    )
    
    vr1_path_hops = Histogram(
        'vr1_path_hops',
        'Number of hops in VR1 reachability paths',
        buckets=(1, 2, 3, 5, 10, 15, 20, 30)
    )


@dataclass
class VR1TelemetryContext:
    """Telemetry context for VR1 validation session"""
    session_id: str
    blueprint_name: Optional[str] = None
    blueprint_version: Optional[str] = None
    component_count: int = 0
    connection_count: int = 0
    ingress_count: int = 0
    validation_start_time: Optional[float] = None
    validation_end_time: Optional[float] = None
    feature_flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = {}


class VR1TelemetryCollector:
    """
    Comprehensive telemetry collection for VR1 validation
    """
    
    def __init__(self, logger_name: str = "vr1_validator"):
        self.logger = logging.getLogger(logger_name)
        self.context: Optional[VR1TelemetryContext] = None
        
        # Configure structured logging
        self._configure_structured_logging()
    
    def _configure_structured_logging(self):
        """Configure JSON structured logging for VR1 validation"""
        
        # Create JSON formatter
        class VR1JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add VR1-specific context if available
                if hasattr(record, 'vr1_context'):
                    log_entry["vr1_context"] = record.vr1_context
                
                # Add trace ID for correlation
                if hasattr(record, 'trace_id'):
                    log_entry["trace_id"] = record.trace_id
                
                return json.dumps(log_entry)
        
        # Apply formatter to VR1 loggers
        vr1_loggers = [
            "vr1_validator", "boundary_semantics", "vr1_error_taxonomy"
        ]
        
        for logger_name in vr1_loggers:
            logger = logging.getLogger(logger_name)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(VR1JsonFormatter())
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
    
    @contextmanager
    def validation_session(self, context: VR1TelemetryContext):
        """Context manager for VR1 validation telemetry session"""
        self.context = context
        self.context.validation_start_time = time.time()
        
        # Log session start
        self._log_validation_start()
        
        try:
            yield self
        except Exception as e:
            self._log_validation_exception(e)
            raise
        finally:
            if self.context:
                self.context.validation_end_time = time.time()
                self._log_validation_end()
                self._record_metrics()
                self.context = None
    
    def record_validation_result(self, is_valid: bool, errors: List[VR1ValidationError]):
        """Record validation result and errors"""
        # Record overall result
        result = "success" if is_valid else "failure"
        
        if PROMETHEUS_AVAILABLE and self.context:
            vr1_validations_total.labels(
                result=result,
                blueprint_version=self.context.blueprint_version or "unknown"
            ).inc()
            
            vr1_ingress_points.set(self.context.ingress_count)
        
        # Record individual errors
        for error in errors:
            self.record_validation_error(error)
        
        # Structured logging (only if context available)
        if self.context:
            self.logger.info(
                f"VR1 validation {result}",
                extra={
                    "vr1_context": {
                        "session_id": self.context.session_id,
                        "result": result,
                        "error_count": len(errors),
                        "ingress_count": self.context.ingress_count
                    },
                    "trace_id": self.context.session_id
                }
            )
    
    def record_validation_error(self, error: VR1ValidationError):
        """Record individual validation error with telemetry"""
        
        if PROMETHEUS_AVAILABLE:
            vr1_errors_total.labels(
                error_type=error.error_type.value,
                error_category=error.error_category.value
            ).inc()
        
        # Structured error logging with PII redaction
        self.logger.error(
            f"VR1 validation error: {error.message}",
            extra={
                "vr1_context": {
                    "session_id": self.context.session_id if self.context else "unknown",
                    "error": error.to_dict()  # Already PII-sanitized
                },
                "trace_id": self.context.session_id if self.context else "unknown"
            }
        )
    
    def record_path_hops(self, hops: int):
        """Record path traversal hop count"""
        if PROMETHEUS_AVAILABLE:
            vr1_path_hops.observe(hops)
    
    def _log_validation_start(self):
        """Log validation session start"""
        if not self.context:
            return
            
        self.logger.info(
            "VR1 validation session started",
            extra={
                "vr1_context": {
                    "session_id": self.context.session_id,
                    "blueprint_name": self.context.blueprint_name,
                    "component_count": self.context.component_count,
                    "connection_count": self.context.connection_count,
                    "feature_flags": self.context.feature_flags
                },
                "trace_id": self.context.session_id
            }
        )
    
    def _log_validation_end(self):
        """Log validation session end with duration"""
        if not self.context:
            return
            
        duration = (self.context.validation_end_time or 0) - (self.context.validation_start_time or 0)
        
        self.logger.info(
            "VR1 validation session completed",
            extra={
                "vr1_context": {
                    "session_id": self.context.session_id,
                    "duration_seconds": duration,
                    "ingress_count": self.context.ingress_count
                },
                "trace_id": self.context.session_id
            }
        )
    
    def _log_validation_exception(self, exception: Exception):
        """Log validation exception"""
        if not self.context:
            return
            
        self.logger.exception(
            f"VR1 validation session failed with exception: {str(exception)}",
            extra={
                "vr1_context": {
                    "session_id": self.context.session_id,
                    "exception_type": type(exception).__name__
                },
                "trace_id": self.context.session_id
            }
        )
    
    def _record_metrics(self):
        """Record final metrics for validation session"""
        if not PROMETHEUS_AVAILABLE or not self.context:
            return
        
        duration = (self.context.validation_end_time or 0) - (self.context.validation_start_time or 0)
        
        # Bucket component count for metrics
        if self.context.component_count <= 5:
            bucket = "small"
        elif self.context.component_count <= 20:
            bucket = "medium"
        else:
            bucket = "large"
        
        vr1_validation_duration.labels(
            blueprint_version=self.context.blueprint_version or "unknown",
            component_count_bucket=bucket
        ).observe(duration)


# Global telemetry collector instance
vr1_telemetry = VR1TelemetryCollector()