from typing import List

class ValidationException(Exception):
    """Base exception for validation errors"""
    pass

class HealingFailure(ValidationException):
    """Raised when healing attempts fail"""
    def __init__(self, message: str, attempts: int, errors: List[str]):
        self.attempts = attempts
        self.errors = errors
        super().__init__(message)

class ContextBuildException(ValidationException):
    """Raised when pipeline context cannot be built"""
    pass

class ConfigurationInvalid(ValidationException):
    """Raised when configuration is invalid and cannot be healed"""
    pass