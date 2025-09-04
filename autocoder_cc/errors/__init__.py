"""
Error code system for AutoCoder4_CC.
Provides structured error handling without fallbacks or escape hatches.
"""

from .error_codes import (
    ErrorCode,
    AutocoderError,
    RecipeError,
    ValidationError,
    ComponentGenerationError,
    CircuitBreakerError,
    ConfigurationError
)

__all__ = [
    'ErrorCode',
    'AutocoderError', 
    'RecipeError',
    'ValidationError',
    'ComponentGenerationError',
    'CircuitBreakerError',
    'ConfigurationError'
]