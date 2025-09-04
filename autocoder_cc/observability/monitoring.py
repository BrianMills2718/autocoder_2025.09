#!/usr/bin/env python3
"""
Comprehensive Monitoring with Sentry Integration
================================================

Phase 3A Implementation: Error tracking, performance monitoring, and operational visibility
Focus: LLM hanging detection, port binding failures, blueprint issues
"""

import os
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import sentry_sdk
from sentry_sdk import configure_scope, capture_exception, capture_message, start_transaction, set_tag, set_extra
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from autocoder_cc.observability import get_logger
from autocoder_cc.core.timeout_manager import TimeoutError

logger = get_logger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    component_name: Optional[str] = None
    system_id: Optional[str] = None

@dataclass
class AlertEvent:
    """Alert event data"""
    alert_type: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    component_name: Optional[str] = None
    system_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

class SentryMonitoring:
    """
    Sentry-based monitoring and alerting system
    
    Features:
    - Error tracking and performance monitoring
    - Real-time failure detection and alerting
    - LLM hanging detection
    - Port binding failure monitoring
    - Blueprint issue tracking
    - Performance metrics collection
    """
    
    def __init__(self, 
                 dsn: Optional[str] = None,
                 environment: str = "development",
                 enable_tracing: bool = True,
                 sample_rate: float = 0.1):
        """
        Initialize Sentry monitoring
        
        Args:
            dsn: Sentry DSN (Data Source Name)
            environment: Environment name (development, staging, production)
            enable_tracing: Whether to enable performance tracing
            sample_rate: Sample rate for performance monitoring (0.0 to 1.0)
        """
        self.dsn = dsn or os.getenv('SENTRY_DSN')
        self.environment = environment
        self.enable_tracing = enable_tracing
        self.sample_rate = sample_rate
        
        self._metrics_buffer: List[PerformanceMetric] = []
        self._alert_buffer: List[AlertEvent] = []
        self._buffer_lock = threading.RLock()
        
        self._initialize_sentry()
        
        logger.info(f"SentryMonitoring initialized: env={environment}, "
                   f"tracing={enable_tracing}, sample_rate={sample_rate}")
    
    def _initialize_sentry(self):
        """Initialize Sentry SDK with appropriate configuration"""
        if not self.dsn:
            logger.warning("No Sentry DSN provided. Monitoring will be disabled in production.")
            return
        
        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=None,        # Capture records from all loggers
            event_level="ERROR"  # Send error records as events
        )
        
        # Configure threading integration for async contexts
        threading_integration = ThreadingIntegration(
            propagate_hub=True
        )
        
        # Initialize Sentry
        sentry_sdk.init(
            dsn=self.dsn,
            environment=self.environment,
            integrations=[logging_integration, threading_integration],
            traces_sample_rate=self.sample_rate if self.enable_tracing else 0.0,
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            before_send=self._before_send_filter,
            before_send_transaction=self._before_send_transaction_filter
        )
        
        # Set global tags
        with configure_scope() as scope:
            scope.set_tag("service", "autocoder_cc")
            scope.set_tag("version", "5.2.0")
    
    def _before_send_filter(self, event, hint):
        """Filter events before sending to Sentry"""
        # Don't send debug-level events in production
        if self.environment == 'production' and event.get('level') == 'debug':
            return None
        
        # Add custom context
        if 'extra' not in event:
            event['extra'] = {}
        
        event['extra']['monitoring_timestamp'] = time.time()
        
        return event
    
    def _before_send_transaction_filter(self, event, hint):
        """Filter transaction events before sending to Sentry"""
        # Skip very short transactions (< 10ms) to reduce noise
        duration = event.get('spans', [{}])[0].get('timestamp', 0) - event.get('start_timestamp', 0) 
        if duration < 0.01:  # 10ms
            return None
            
        return event
    
    @contextmanager
    def monitor_operation(self, 
                         operation_name: str,
                         component_name: Optional[str] = None,
                         system_id: Optional[str] = None,
                         expected_duration: Optional[float] = None):
        """
        Context manager for monitoring operations with automatic alerting
        
        Args:
            operation_name: Name of the operation being monitored
            component_name: Optional component name for context
            system_id: Optional system ID for context
            expected_duration: Expected operation duration in seconds (for hang detection)
        """
        start_time = time.time()
        transaction = None
        
        try:
            # Start Sentry transaction for performance monitoring
            if self.enable_tracing:
                transaction = start_transaction(
                    op="autocoder.operation",
                    name=operation_name
                )
                transaction.set_tag("component", component_name or "unknown")
                transaction.set_tag("system_id", system_id or "unknown")
            
            # Set operation context
            with configure_scope() as scope:
                scope.set_tag("operation", operation_name)
                if component_name:
                    scope.set_tag("component", component_name)
                if system_id:
                    scope.set_tag("system_id", system_id)
            
            yield self
            
            # Record successful completion
            duration = time.time() - start_time
            self._record_performance_metric(
                metric_name="operation_duration",
                value=duration,
                unit="seconds",
                tags={
                    "operation": operation_name,
                    "status": "success",
                    "component": component_name or "unknown"
                },
                component_name=component_name,
                system_id=system_id
            )
            
            # Check for potential hanging (if expected duration provided)
            if expected_duration and duration > expected_duration * 2:
                self._create_alert(
                    alert_type="operation_slow",
                    severity=AlertSeverity.MEDIUM,
                    message=f"Operation '{operation_name}' took {duration:.2f}s (expected {expected_duration}s)",
                    component_name=component_name,
                    system_id=system_id,
                    additional_data={
                        "actual_duration": duration,
                        "expected_duration": expected_duration,
                        "slowness_ratio": duration / expected_duration
                    }
                )
            
        except TimeoutError as e:
            # Handle timeout errors specifically
            duration = time.time() - start_time
            self._handle_timeout_error(e, operation_name, component_name, system_id, duration)
            raise
            
        except Exception as e:
            # Handle general errors
            duration = time.time() - start_time
            self._handle_operation_error(e, operation_name, component_name, system_id, duration)
            raise
            
        finally:
            if transaction:
                transaction.finish()
    
    def monitor_llm_generation(self, 
                              provider: str,
                              model: str,
                              component_name: Optional[str] = None,
                              system_id: Optional[str] = None):
        """
        Specialized monitoring for LLM generation operations
        
        Args:
            provider: LLM provider name (gemini, openai, anthropic)
            model: Model name
            component_name: Component being generated
            system_id: System ID
        """
        return self.monitor_operation(
            operation_name=f"llm_generation_{provider}_{model}",
            component_name=component_name,
            system_id=system_id,
            expected_duration=30.0  # LLM calls should complete within 30s
        )
    
    def monitor_port_allocation(self, 
                               component_name: str,
                               system_id: Optional[str] = None):
        """
        Monitor port allocation operations
        
        Args:
            component_name: Name of component requesting port
            system_id: System ID
        """
        return self.monitor_operation(
            operation_name="port_allocation",
            component_name=component_name,
            system_id=system_id,
            expected_duration=5.0  # Port allocation should be fast
        )
    
    def monitor_blueprint_processing(self, 
                                   blueprint_name: str,
                                   system_id: Optional[str] = None):
        """
        Monitor blueprint processing operations
        
        Args:
            blueprint_name: Name of blueprint being processed
            system_id: System ID
        """
        return self.monitor_operation(
            operation_name="blueprint_processing",
            component_name=blueprint_name,
            system_id=system_id,
            expected_duration=15.0  # Blueprint processing moderate duration
        )
    
    def report_port_binding_failure(self, 
                                   component_name: str,
                                   port: int,
                                   error_message: str,
                                   system_id: Optional[str] = None):
        """
        Report port binding failures
        
        Args:
            component_name: Component that failed to bind port
            port: Port number that failed to bind
            error_message: Error message from binding failure
            system_id: System ID
        """
        self._create_alert(
            alert_type="port_binding_failure",
            severity=AlertSeverity.HIGH,
            message=f"Component '{component_name}' failed to bind port {port}: {error_message}",
            component_name=component_name,
            system_id=system_id,
            additional_data={
                "port": port,
                "error_message": error_message
            }
        )
        
        # Also capture as Sentry error
        with configure_scope() as scope:
            scope.set_tag("alert_type", "port_binding_failure")
            scope.set_tag("component", component_name)
            scope.set_tag("port", str(port))
            scope.set_extra("error_details", error_message)
            
            capture_message(
                f"Port binding failure: {component_name} port {port}",
                level="error"
            )
    
    def report_blueprint_issue(self, 
                              issue_type: str,
                              component_name: str,
                              line_number: int,
                              message: str,
                              system_id: Optional[str] = None):
        """
        Report blueprint validation issues
        
        Args:
            issue_type: Type of blueprint issue
            component_name: Component with the issue
            line_number: Line number of issue
            message: Issue description
            system_id: System ID
        """
        severity = AlertSeverity.HIGH if issue_type == "error" else AlertSeverity.MEDIUM
        
        self._create_alert(
            alert_type="blueprint_issue",
            severity=severity,
            message=f"Blueprint issue in '{component_name}' line {line_number}: {message}",
            component_name=component_name,
            system_id=system_id,
            additional_data={
                "issue_type": issue_type,
                "line_number": line_number,
                "issue_message": message
            }
        )
    
    def report_llm_hanging(self, 
                          provider: str,
                          model: str,
                          duration: float,
                          component_name: Optional[str] = None,
                          system_id: Optional[str] = None):
        """
        Report LLM hanging incidents
        
        Args:
            provider: LLM provider that hung
            model: Model that hung
            duration: How long the operation ran before timing out
            component_name: Component being generated when hanging occurred
            system_id: System ID
        """
        self._create_alert(
            alert_type="llm_hanging",
            severity=AlertSeverity.CRITICAL,
            message=f"LLM hanging detected: {provider}/{model} hung for {duration:.2f}s",
            component_name=component_name,
            system_id=system_id,
            additional_data={
                "provider": provider,
                "model": model,
                "hang_duration": duration
            }
        )
        
        # High priority Sentry error
        with configure_scope() as scope:
            scope.set_tag("alert_type", "llm_hanging")
            scope.set_tag("provider", provider)
            scope.set_tag("model", model)
            scope.set_extra("hang_duration", duration)
            scope.set_level("error")
            
            capture_message(
                f"LLM hanging: {provider}/{model} hung for {duration:.2f}s",
                level="error"
            )
    
    def _handle_timeout_error(self, 
                             error: TimeoutError,
                             operation_name: str,
                             component_name: Optional[str],
                             system_id: Optional[str],
                             duration: float):
        """Handle timeout errors with specific monitoring"""
        self._create_alert(
            alert_type="operation_timeout",
            severity=AlertSeverity.HIGH,
            message=f"Operation '{operation_name}' timed out after {duration:.2f}s",
            component_name=component_name,
            system_id=system_id,
            additional_data={
                "timeout_duration": duration,
                "timeout_limit": error.timeout_value,
                "timeout_type": error.timeout_type.value
            }
        )
        
        # Record timeout metric
        self._record_performance_metric(
            metric_name="operation_timeout",
            value=duration,
            unit="seconds",
            tags={
                "operation": operation_name,
                "timeout_type": error.timeout_type.value,
                "component": component_name or "unknown"
            },
            component_name=component_name,
            system_id=system_id
        )
        
        # Capture in Sentry
        capture_exception(error)
    
    def _handle_operation_error(self, 
                               error: Exception,
                               operation_name: str,
                               component_name: Optional[str],
                               system_id: Optional[str],
                               duration: float):
        """Handle general operation errors"""
        self._create_alert(
            alert_type="operation_error",
            severity=AlertSeverity.HIGH,
            message=f"Operation '{operation_name}' failed: {str(error)}",
            component_name=component_name,
            system_id=system_id,
            additional_data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "operation_duration": duration
            }
        )
        
        # Record error metric
        self._record_performance_metric(
            metric_name="operation_error",
            value=1,
            unit="count",
            tags={
                "operation": operation_name,
                "error_type": type(error).__name__,
                "component": component_name or "unknown"
            },
            component_name=component_name,
            system_id=system_id
        )
        
        # Capture in Sentry
        capture_exception(error)
    
    def _record_performance_metric(self, 
                                  metric_name: str,
                                  value: float,
                                  unit: str,
                                  tags: Dict[str, str] = None,
                                  component_name: Optional[str] = None,
                                  system_id: Optional[str] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {},
            component_name=component_name,
            system_id=system_id
        )
        
        with self._buffer_lock:
            self._metrics_buffer.append(metric)
        
        logger.debug(f"Performance metric recorded: {metric_name}={value} {unit}")
    
    def _create_alert(self, 
                     alert_type: str,
                     severity: AlertSeverity,
                     message: str,
                     component_name: Optional[str] = None,
                     system_id: Optional[str] = None,
                     additional_data: Dict[str, Any] = None):
        """Create and buffer an alert event"""
        alert = AlertEvent(
            alert_type=alert_type,
            severity=severity,
            message=message,
            component_name=component_name,
            system_id=system_id,
            additional_data=additional_data or {}
        )
        
        with self._buffer_lock:
            self._alert_buffer.append(alert)
        
        # Log alert locally
        log_level = {
            AlertSeverity.CRITICAL: "error",
            AlertSeverity.HIGH: "error", 
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "info",
            AlertSeverity.INFO: "info"
        }.get(severity, "info")
        
        getattr(logger, log_level)(f"ALERT [{severity.value.upper()}] {message}")
    
    def get_performance_metrics(self, clear_buffer: bool = True) -> List[PerformanceMetric]:
        """Get buffered performance metrics"""
        with self._buffer_lock:
            metrics = self._metrics_buffer.copy()
            if clear_buffer:
                self._metrics_buffer.clear()
        
        return metrics
    
    def get_alerts(self, clear_buffer: bool = True) -> List[AlertEvent]:
        """Get buffered alert events"""
        with self._buffer_lock:
            alerts = self._alert_buffer.copy()
            if clear_buffer:
                self._alert_buffer.clear()
        
        return alerts
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring data"""
        metrics = self.get_performance_metrics(clear_buffer=False)
        alerts = self.get_alerts(clear_buffer=False)
        
        # Group metrics by name
        metric_summary = {}
        for metric in metrics:
            if metric.metric_name not in metric_summary:
                metric_summary[metric.metric_name] = []
            metric_summary[metric.metric_name].append(metric.value)
        
        # Group alerts by severity
        alert_summary = {}
        for alert in alerts:
            severity = alert.severity.value
            alert_summary[severity] = alert_summary.get(severity, 0) + 1
        
        return {
            "metrics_count": len(metrics),
            "alerts_count": len(alerts),
            "metric_types": list(metric_summary.keys()),
            "alert_severities": alert_summary,
            "monitoring_active": bool(self.dsn)
        }


# Global monitoring instance
_monitoring: Optional[SentryMonitoring] = None
_monitoring_lock = threading.Lock()

def get_monitoring() -> SentryMonitoring:
    """
    Get global monitoring instance (singleton pattern)
    
    Returns:
        Global SentryMonitoring instance
    """
    global _monitoring
    
    if _monitoring is None:
        with _monitoring_lock:
            if _monitoring is None:
                environment = os.getenv('ENVIRONMENT', 'development')
                _monitoring = SentryMonitoring(environment=environment)
                logger.info("Global SentryMonitoring instance created")
    
    return _monitoring

def reset_monitoring() -> None:
    """
    Reset global monitoring instance (primarily for testing)
    """
    global _monitoring
    
    with _monitoring_lock:
        _monitoring = None
        logger.info("Global SentryMonitoring instance reset")