"""
Core Exceptions
Common exception classes for the autocoder system
"""

from typing import Optional, Any


class AutocoderError(Exception):
    """Base exception for autocoder system"""
    pass


class ValidationError(AutocoderError):
    """Validation error with context"""
    
    def __init__(self, message: str, path: Optional[str] = None, 
                 component: Optional[str] = None, severity: str = "error"):
        super().__init__(message)
        self.message = message
        self.path = path
        self.component = component
        self.severity = severity
    
    def __str__(self) -> str:
        if self.path:
            return f"{self.path}: {self.message}"
        return self.message


class BlueprintParsingError(AutocoderError):
    """Error parsing blueprint files"""
    pass


class ComponentLoadError(AutocoderError):
    """Error loading components"""
    pass


class ConfigurationError(AutocoderError):
    """Configuration error"""
    pass


class SchemaError(AutocoderError):
    """Schema validation error"""
    pass


class SecurityError(AutocoderError):
    """Security validation error"""
    pass


class ResourceConflictError(AutocoderError):
    """Resource conflict error"""
    pass


class DependencyError(AutocoderError):
    """Dependency resolution error"""
    pass


class GenerationError(AutocoderError):
    """Code generation error"""
    pass


class ExecutionError(AutocoderError):
    """System execution error"""
    pass


class AutocoderRuntimeError(AutocoderError):
    """Runtime error (as opposed to validation error)"""
    pass