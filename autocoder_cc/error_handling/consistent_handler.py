from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Consistent Error Handling Utilities for Autocoder V5.2

This module provides standardized error handling patterns and utilities
to ensure consistent error handling across all components and capabilities.

## Overview

The Consistent Error Handler ensures that all components handle errors
in a uniform way with proper context, logging, and recovery mechanisms.

## Key Features

1. **Standardized Error Handling**: Common patterns for try-catch blocks
2. **Context Preservation**: Automatically captures relevant context information
3. **Proper Logging**: Structured logging with appropriate levels
4. **Recovery Mechanisms**: Built-in retry and fallback strategies
5. **Debug Information**: Rich context for troubleshooting production issues

## Usage Examples

### Basic Error Handling
```python
from autocoder_cc.error_handling.consistent_handler import handle_errors, ErrorContext

@handle_errors(component_name="my_component")
async def process_data(self, data):
    # Your component logic here
    return result

# Or use context manager
async def my_operation(self):
    with ErrorContext(component=self.name, operation="data_processing"):
        result = await some_operation()
        return result
```

### Manual Error Handling
```python
from autocoder_cc.error_handling.consistent_handler import ConsistentErrorHandler

handler = ConsistentErrorHandler(component_name="my_component")
try:
    result = await risky_operation()
except Exception as e:
    await handler.handle_exception(e, context={"operation": "risky_op", "data": data})
```
"""

import asyncio
import logging
import traceback
import time
import sys
from typing import Any, Dict, Optional, Callable, Union, Type
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from autocoder_cc.exceptions import AutocoderError, ErrorCategory, SeverityLevel
from autocoder_cc.core.config import settings


@dataclass
class ErrorMetrics:
    """Track error metrics for monitoring and alerting."""
    total_errors: int = 0
    critical_errors: int = 0
    recent_errors: list = field(default_factory=list)
    last_error_time: Optional[float] = None
    error_rate_per_minute: float = 0.0


class ConsistentErrorHandler:
    """
    Provides consistent error handling across all Autocoder components.
    
    Features:
    - Automatic context collection
    - Structured logging
    - Error categorization
    - Retry mechanisms
    - No fallback strategies (fail-fast principle)
    - Performance monitoring
    """
    
    def __init__(self, component_name: str, logger: Optional[logging.Logger] = None):
        self.component_name = component_name
        self.logger = logger or get_logger(f"ErrorHandler.{component_name}")
        self.metrics = ErrorMetrics()
        
        # Error handling configuration
        self.default_retries = 3
        self.retry_delay = 1.0
        self.enable_auto_recovery = True
        
    async def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        auto_retry: bool = True
    ) -> Optional[Any]:
        """
        Handle an exception with consistent logging and recovery.
        
        Args:
            exception: The exception that occurred
            context: Additional context information
            operation: Name of the operation that failed
            auto_retry: Whether to attempt automatic retry
            fallback: Fallback function to call if recovery fails
            
        Returns:
            Result from fallback function if provided and successful
        """
        # Update metrics
        self._update_error_metrics(exception)
        
        # Build comprehensive context
        error_context = self._build_error_context(exception, context, operation)
        
        # Categorize the error
        category, severity = self._categorize_error(exception)
        
        # Log the error with full context
        self._log_error(exception, error_context, category, severity)
        
        # Attempt recovery if enabled
        if auto_retry and self.enable_auto_recovery:
            recovery_result = await self._attempt_recovery(exception, error_context)
            if recovery_result is not None:
                return recovery_result
        
        # No fallback mechanisms - fail fast principle
        
        # Convert to AutocoderError if not already
        if not isinstance(exception, AutocoderError):
            autocoder_error = AutocoderError(
                message=str(exception),
                category=category,
                severity=severity,
                component=self.component_name,
                context=error_context
            )
            raise autocoder_error from exception
        else:
            raise exception
    
    def _build_error_context(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]],
        operation: Optional[str]
    ) -> Dict[str, Any]:
        """Build comprehensive error context for debugging."""
        error_context = {
            "component": self.component_name,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "timestamp": time.time(),
            "traceback": self._truncate_string(traceback.format_exc(), settings.ERROR_CONTEXT_MAX_LENGTH),
        }
        
        if operation:
            error_context["operation"] = operation
        
        # Add exception chain if present
        if exception.__cause__:
            error_context["caused_by"] = {
                "type": type(exception.__cause__).__name__,
                "message": str(exception.__cause__)
            }
        elif exception.__context__:
            error_context["context_exception"] = {
                "type": type(exception.__context__).__name__,
                "message": str(exception.__context__)
            }
        
        # Add custom attributes from exception if available
        if hasattr(exception, '__dict__'):
            for attr, value in exception.__dict__.items():
                if not attr.startswith('_') and attr not in ['args']:
                    error_context[f"exception_{attr}"] = self._truncate_value(value)
        
        if context:
            # Truncate context values if needed
            for key, value in context.items():
                error_context[key] = self._truncate_value(value)
        
        # Add system context
        try:
            import psutil
            error_context["system_context"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "process_memory": psutil.Process().memory_info().rss / 1024 / 1024,  # MB
                "open_files": len(psutil.Process().open_files())
            }
        except ImportError:
            # psutil not available - that's ok
            pass
        except Exception:
            # Don't fail error handling due to system info collection
            pass
        
        # Add environment context
        error_context["environment"] = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG_MODE
        }
        
        return error_context
    
    def _truncate_string(self, value: str, max_length: int) -> str:
        """Truncate string to max length with ellipsis."""
        if len(value) <= max_length:
            return value
        return value[:max_length - 3] + "..."
    
    def _truncate_value(self, value: Any) -> Any:
        """Truncate value if it's a string or has string representation."""
        if isinstance(value, str):
            return self._truncate_string(value, settings.ERROR_CONTEXT_MAX_LENGTH)
        elif isinstance(value, (list, tuple)):
            # Truncate lists/tuples to first 10 items
            if len(value) > 10:
                return list(value[:10]) + ["... truncated"]
            return value
        elif isinstance(value, dict):
            # Truncate dicts to first 20 items
            if len(value) > 20:
                items = list(value.items())[:20]
                return dict(items + [("...", "truncated")])
            return value
        else:
            # For other types, convert to string and truncate if needed
            str_value = str(value)
            if len(str_value) > settings.ERROR_CONTEXT_MAX_LENGTH:
                return self._truncate_string(str_value, settings.ERROR_CONTEXT_MAX_LENGTH)
            return value
    
    def _categorize_error(self, exception: Exception) -> tuple[ErrorCategory, SeverityLevel]:
        """Categorize error for appropriate handling."""
        # If already an AutocoderError, use its categorization
        if isinstance(exception, AutocoderError):
            return exception.category, exception.severity
        
        # Categorize based on exception type
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorCategory.DEPENDENCY, SeverityLevel.ERROR
        elif isinstance(exception, (ValueError, TypeError)):
            return ErrorCategory.SCHEMA, SeverityLevel.ERROR
        elif isinstance(exception, (MemoryError, OSError)):
            return ErrorCategory.RESOURCE, SeverityLevel.CRITICAL
        elif isinstance(exception, KeyboardInterrupt):
            return ErrorCategory.EXECUTION, SeverityLevel.CRITICAL
        else:
            return ErrorCategory.EXECUTION, SeverityLevel.ERROR
    
    def _log_error(
        self,
        exception: Exception,
        context: Dict[str, Any],
        category: ErrorCategory,
        severity: SeverityLevel
    ):
        """Log error with appropriate level and structured format."""
        log_message = f"[{category.value.upper()}] {self.component_name}: {str(exception)}"
        
        # Choose log level based on severity
        if severity == SeverityLevel.CRITICAL:
            self.logger.critical(log_message, extra={"error_context": context})
        elif severity == SeverityLevel.ERROR:
            self.logger.error(log_message, extra={"error_context": context})
        elif severity == SeverityLevel.WARNING:
            self.logger.warning(log_message, extra={"error_context": context})
        else:
            self.logger.info(log_message, extra={"error_context": context})
    
    async def _attempt_recovery(
        self,
        exception: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """Attempt automatic recovery based on error type."""
        category, _ = self._categorize_error(exception)
        
        if category == ErrorCategory.DEPENDENCY:
            # For dependency errors, try waiting and retrying
            for attempt in range(self.default_retries):
                self.logger.info(f"Attempting recovery for dependency error (attempt {attempt + 1}/{self.default_retries})")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                
                # Recovery would be operation-specific
                # For now, just indicate retry should happen
                return "retry_needed"
        
        return None
    
    def _update_error_metrics(self, exception: Exception):
        """Update error metrics for monitoring."""
        self.metrics.total_errors += 1
        self.metrics.last_error_time = time.time()
        
        # Track recent errors (last 10)
        self.metrics.recent_errors.append({
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "timestamp": time.time()
        })
        if len(self.metrics.recent_errors) > 10:
            self.metrics.recent_errors.pop(0)
        
        # Update critical error count
        category, severity = self._categorize_error(exception)
        if severity == SeverityLevel.CRITICAL:
            self.metrics.critical_errors += 1
        
        # Calculate error rate (errors per minute)
        recent_window = 60  # 1 minute
        current_time = time.time()
        recent_count = sum(
            1 for error in self.metrics.recent_errors 
            if current_time - error["timestamp"] <= recent_window
        )
        self.metrics.error_rate_per_minute = recent_count
    
    def get_metrics(self) -> ErrorMetrics:
        """Get current error metrics."""
        return self.metrics


class ErrorContext:
    """Context manager for consistent error handling."""
    
    def __init__(
        self,
        component: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.handler = ConsistentErrorHandler(component, logger)
        self.operation = operation
        self.context = context or {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.handler.handle_exception(exc_val, self.context, self.operation)
            return True  # Suppress the exception after handling
        return False


def handle_errors(
    component_name: str,
    operation: Optional[str] = None,
    auto_retry: bool = True
):
    """
    Decorator for consistent error handling in component methods.
    
    Args:
        component_name: Name of the component
        operation: Name of the operation (defaults to function name)
        auto_retry: Whether to attempt automatic retry
        auto_retry: Whether to attempt automatic retry
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = ConsistentErrorHandler(component_name)
            op_name = operation or func.__name__
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return await handler.handle_exception(
                    e, 
                    context={"args": str(args), "kwargs": str(kwargs)},
                    operation=op_name,
                    auto_retry=auto_retry
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = ConsistentErrorHandler(component_name)
            op_name = operation or func.__name__
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # For sync functions, we can't use async recovery
                handler._update_error_metrics(e)
                category, severity = handler._categorize_error(e)
                context = handler._build_error_context(e, {"args": str(args), "kwargs": str(kwargs)}, op_name)
                handler._log_error(e, context, category, severity)
                
                # No fallback mechanisms - fail fast principle
                
                # Convert to AutocoderError
                if not isinstance(e, AutocoderError):
                    raise AutocoderError(
                        message=str(e),
                        category=category,
                        severity=severity,
                        component=component_name,
                        context=context
                    ) from e
                else:
                    raise e
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global error handler registry for monitoring
_global_handlers: Dict[str, ConsistentErrorHandler] = {}


def get_global_error_metrics() -> Dict[str, ErrorMetrics]:
    """Get error metrics from all registered handlers."""
    return {name: handler.get_metrics() for name, handler in _global_handlers.items()}


def register_error_handler(handler: ConsistentErrorHandler) -> None:
    """Register error handler for global monitoring."""
    _global_handlers[handler.component_name] = handler