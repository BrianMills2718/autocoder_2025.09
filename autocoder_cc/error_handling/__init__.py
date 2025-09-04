"""
Error Handling Module for Autocoder V5.2

Provides consistent error handling utilities and patterns for all components.
"""

from .consistent_handler import (
    ConsistentErrorHandler,
    ErrorContext,
    handle_errors,
    ErrorMetrics,
    get_global_error_metrics,
    register_error_handler
)

__all__ = [
    "ConsistentErrorHandler",
    "ErrorContext", 
    "handle_errors",
    "ErrorMetrics",
    "get_global_error_metrics",
    "register_error_handler"
]