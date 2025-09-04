"""
Structured error codes for fail-fast behavior.
NO FALLBACKS, NO RECOVERY, JUST CLEAR ERRORS.
"""

from enum import Enum
from typing import Dict, Any, Optional
import json
import traceback
from datetime import datetime


class ErrorCode(Enum):
    """All error codes in the system."""
    
    # Recipe errors (1000-1099)
    RECIPE_NOT_FOUND = 1001
    RECIPE_INVALID_STRUCTURE = 1002
    RECIPE_NO_IMPLEMENTATION = 1003
    RECIPE_EXPANSION_FAILED = 1004
    
    # Validation errors (2000-2099)
    VALIDATION_FAILED = 2001
    VALIDATION_AST_INVALID = 2002
    VALIDATION_SCHEMA_MISMATCH = 2003
    VALIDATION_BYPASSED_ILLEGALLY = 2004
    
    # Component generation errors (3000-3099)
    COMPONENT_GENERATION_FAILED = 3001
    COMPONENT_LLM_FAILED = 3002
    COMPONENT_WRITE_FAILED = 3003
    COMPONENT_IMPORT_FAILED = 3004
    
    # Circuit breaker errors (4000-4099)
    CIRCUIT_BREAKER_OPEN = 4001
    CIRCUIT_BREAKER_NOT_CONFIGURED = 4002
    
    # LLM errors (5000-5099)
    LLM_NO_PRIMARY_MODEL = 5001
    LLM_RESPONSE_INVALID = 5002
    LLM_FALLBACK_DISABLED = 5003
    LLM_API_ERROR = 5004
    
    # Configuration errors (6000-6099)
    CONFIG_MISSING_REQUIRED = 6001
    CONFIG_INVALID_VALUE = 6002
    CONFIG_ENV_NOT_SET = 6003


class AutocoderError(Exception):
    """
    Base exception with structured error information.
    NO FALLBACKS - FAIL FAST WITH CLEAR DEBUGGING INFO.
    """
    
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.stack_trace = traceback.format_stack()
        
        # Build comprehensive error message
        error_parts = [
            f"[ERROR {code.value}] {code.name}",
            f"Message: {message}",
            f"Timestamp: {self.timestamp}"
        ]
        
        if details:
            error_parts.append(f"Details: {json.dumps(details, indent=2)}")
        
        super().__init__("\n".join(error_parts))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error_code": self.code.value,
            "error_name": self.code.name,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "stack_trace": self.stack_trace
        }


class RecipeError(AutocoderError):
    """Recipe-specific errors."""
    pass


class ValidationError(AutocoderError):
    """Validation-specific errors."""
    pass


class ComponentGenerationError(AutocoderError):
    """Component generation errors."""
    pass


class CircuitBreakerError(AutocoderError):
    """Circuit breaker errors."""
    pass


class ConfigurationError(AutocoderError):
    """Configuration errors."""
    pass