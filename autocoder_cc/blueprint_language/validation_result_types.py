"""Validation result types for blueprint validation."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation failures."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationFailure:
    """Represents a single validation failure."""
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    location: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    success: bool
    failures: List[ValidationFailure] = None
    warnings: List[ValidationFailure] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.failures is None:
            self.failures = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.failures) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def add_failure(self, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR, 
                    location: str = None, context: Dict[str, Any] = None):
        """Add a validation failure."""
        failure = ValidationFailure(message, severity, location, context)
        if severity == ValidationSeverity.WARNING:
            self.warnings.append(failure)
        else:
            self.failures.append(failure)
            self.success = False
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.failures.extend(other.failures)
        self.warnings.extend(other.warnings)
        if other.has_errors:
            self.success = False
        if other.metadata:
            if self.metadata is None:
                self.metadata = {}
            self.metadata.update(other.metadata)