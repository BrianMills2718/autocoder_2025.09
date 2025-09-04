"""
Autocoder Exception System
Comprehensive exception handling for Autocoder 3.2+ components with categorization for self-healing.
"""

from typing import Any, Dict, List, Optional, Type, Tuple
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors for self-healing prioritization"""
    DEPENDENCY = "dependency"          # Missing components or connections
    SCHEMA = "schema"                 # Data type/format mismatches  
    RESOURCE = "resource"             # Resource allocation/cleanup issues
    EXECUTION = "execution"           # Runtime execution failures
    PROPERTY = "property"             # Property test violations
    CONTRACT = "contract"             # Contract test violations
    REASONABLENESS = "reasonableness" # Reasonableness check failures


class SeverityLevel(Enum):
    """Error severity levels"""
    CRITICAL = "critical"    # Blocks all system operation
    ERROR = "error"         # Blocks component operation
    WARNING = "warning"     # Degraded operation
    INFO = "info"          # Informational only


class AutocoderError(Exception):
    """Base exception for all Autocoder errors"""
    
    def __init__(
        self, 
        message: str,
        category: ErrorCategory = ErrorCategory.EXECUTION,
        severity: SeverityLevel = SeverityLevel.ERROR,
        component: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
        auto_heal: bool = True,
        details: Optional[Any] = None
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.component = component
        self.context = context or {}
        self.retry_count = retry_count
        self.auto_heal = auto_heal
        self.details = details
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message with context"""
        msg = f"[{self.category.value.upper()}] {self.message}"
        if self.component:
            msg = f"{self.component}: {msg}"
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "component": self.component,
            "context": self.context,
            "retry_count": self.retry_count,
            "auto_heal": self.auto_heal,
            "details": self.details,
            "error_type": self.__class__.__name__
        }


class ComponentError(AutocoderError):
    """Errors related to component lifecycle and operation"""
    
    def __init__(self, message: str, component: str, **kwargs):
        super().__init__(message, component=component, **kwargs)


class DependencyError(AutocoderError):
    """Errors related to missing or invalid dependencies"""
    
    def __init__(self, message: str, missing_dependency: str, **kwargs):
        context = kwargs.get("context", {})
        context["missing_dependency"] = missing_dependency
        kwargs["context"] = context
        super().__init__(
            message, 
            category=ErrorCategory.DEPENDENCY, 
            severity=SeverityLevel.CRITICAL,
            **kwargs
        )


class SchemaError(AutocoderError):
    """Errors related to schema validation and type mismatches"""
    
    def __init__(
        self, 
        message: str, 
        field_path: str = "", 
        expected_type: Optional[Type] = None,
        actual_value: Any = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "field_path": field_path,
            "expected_type": expected_type.__name__ if expected_type else None,
            "actual_value": str(actual_value)[:100] if actual_value is not None else None
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.SCHEMA,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class ResourceError(AutocoderError):
    """Errors related to resource allocation and cleanup"""
    
    def __init__(self, message: str, resource_type: str, **kwargs):
        context = kwargs.get("context", {})
        context["resource_type"] = resource_type
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class ExecutionError(AutocoderError):
    """Errors during component execution"""
    
    def __init__(self, message: str, execution_phase: str = "unknown", **kwargs):
        context = kwargs.get("context", {})
        context["execution_phase"] = execution_phase
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.EXECUTION,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class PropertyTestError(AutocoderError):
    """Errors when property tests fail"""
    
    def __init__(
        self, 
        message: str, 
        property_name: str,
        expected_property: str,
        actual_result: Any = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "property_name": property_name,
            "expected_property": expected_property,
            "actual_result": str(actual_result)[:100] if actual_result is not None else None
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.PROPERTY,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class ContractTestError(AutocoderError):
    """Errors when contract tests fail"""
    
    def __init__(
        self, 
        message: str, 
        contract_name: str,
        contract_expression: str,
        input_data: Any = None,
        output_data: Any = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "contract_name": contract_name,
            "contract_expression": contract_expression,
            "input_data": str(input_data)[:100] if input_data is not None else None,
            "output_data": str(output_data)[:100] if output_data is not None else None
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.CONTRACT,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class ReasonablenessError(AutocoderError):
    """Errors when reasonableness checks fail"""
    
    def __init__(
        self, 
        message: str, 
        check_name: str,
        expected_range: Optional[str] = None,
        actual_value: Any = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "check_name": check_name,
            "expected_range": expected_range,
            "actual_value": str(actual_value)[:100] if actual_value is not None else None
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.REASONABLENESS,
            severity=SeverityLevel.WARNING,
            **kwargs
        )


class ValidationError(AutocoderError):
    """General validation errors (backwards compatibility)"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.SCHEMA, **kwargs)


class BindingError(AutocoderError):
    """Errors during component binding"""
    
    def __init__(
        self, 
        message: str, 
        source_component: str,
        target_component: str,
        port_name: str = "",
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "source_component": source_component,
            "target_component": target_component,
            "port_name": port_name
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.CRITICAL,
            **kwargs
        )


class ConfigurationError(AutocoderError):
    """Errors in component or system configuration"""
    
    def __init__(self, message: str, config_key: str = "", **kwargs):
        context = kwargs.get("context", {})
        context["config_key"] = config_key
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class TimeoutError(AutocoderError):
    """Errors when operations timeout"""
    
    def __init__(
        self, 
        message: str, 
        operation: str,
        timeout_ms: int,
        elapsed_ms: int,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "operation": operation,
            "timeout_ms": timeout_ms,
            "elapsed_ms": elapsed_ms
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.EXECUTION,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class SelfHealingError(AutocoderError):
    """Errors during self-healing attempts"""
    
    def __init__(
        self, 
        message: str, 
        original_error: AutocoderError,
        healing_attempt: int = 1,
        max_attempts: int = 3,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "original_error": original_error.to_dict(),
            "healing_attempt": healing_attempt,
            "max_attempts": max_attempts
        })
        kwargs["context"] = context
        kwargs["auto_heal"] = healing_attempt < max_attempts
        super().__init__(
            message,
            category=original_error.category,
            severity=SeverityLevel.CRITICAL,
            **kwargs
        )


class ErrorAggregator:
    """Collects and categorizes multiple errors for batch self-healing"""
    
    def __init__(self):
        self.errors: List[AutocoderError] = []
        self.errors_by_category: Dict[ErrorCategory, List[AutocoderError]] = {
            category: [] for category in ErrorCategory
        }
    
    def add_error(self, error: AutocoderError):
        """Add an error to the aggregator"""
        self.errors.append(error)
        self.errors_by_category[error.category].append(error)
    
    def get_healing_order(self) -> List[List[AutocoderError]]:
        """Get errors in self-healing priority order"""
        healing_order = [
            ErrorCategory.DEPENDENCY,
            ErrorCategory.SCHEMA,
            ErrorCategory.RESOURCE,
            ErrorCategory.EXECUTION,
            ErrorCategory.PROPERTY,
            ErrorCategory.CONTRACT,
            ErrorCategory.REASONABLENESS
        ]
        
        return [
            self.errors_by_category[category] 
            for category in healing_order 
            if self.errors_by_category[category]
        ]
    
    def has_critical_errors(self) -> bool:
        """Check if any critical errors exist"""
        return any(error.severity == SeverityLevel.CRITICAL for error in self.errors)
    
    def get_summary(self) -> Dict[str, int]:
        """Get error count summary by category"""
        return {
            category.value: len(errors) 
            for category, errors in self.errors_by_category.items()
            if errors
        }
    
    def clear(self):
        """Clear all errors"""
        self.errors.clear()
        for category_list in self.errors_by_category.values():
            category_list.clear()


def handle_error_with_context(
    error: Exception, 
    component: str = "", 
    operation: str = "",
    auto_convert: bool = True
) -> AutocoderError:
    """Convert generic exceptions to AutocoderError with context"""
    if isinstance(error, AutocoderError):
        return error
    
    if not auto_convert:
        raise error
    
    # Convert common Python exceptions to appropriate AutocoderError types
    if isinstance(error, KeyError):
        return SchemaError(
            f"Missing required field: {str(error)}",
            component=component,
            context={"operation": operation, "original_error": str(error)}
        )
    elif isinstance(error, TypeError):
        return SchemaError(
            f"Type mismatch: {str(error)}",
            component=component,
            context={"operation": operation, "original_error": str(error)}
        )
    elif isinstance(error, ValueError):
        return ExecutionError(
            f"Invalid value: {str(error)}",
            component=component,
            execution_phase=operation,
            context={"original_error": str(error)}
        )
    elif isinstance(error, ConnectionError):
        return ResourceError(
            f"Connection failed: {str(error)}",
            resource_type="connection",
            component=component,
            context={"operation": operation, "original_error": str(error)}
        )
    elif isinstance(error, FileNotFoundError):
        return DependencyError(
            f"Required file not found: {str(error)}",
            missing_dependency=str(error),
            component=component,
            context={"operation": operation}
        )
    else:
        return ExecutionError(
            f"Unexpected error: {str(error)}",
            component=component,
            execution_phase=operation,
            context={"error_type": type(error).__name__, "original_error": str(error)}
        )


class ReconciliationError(AutocoderError):
    """Errors during ADR 033 endpoint reconciliation"""
    
    def __init__(
        self,
        message: str,
        code: str = "",
        sources: Optional[List[str]] = None,
        suggested_edges: Optional[List[Tuple[str, str]]] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        context.update({
            "code": code,
            "sources": sources or [],
            "suggested_edges": suggested_edges or []
        })
        kwargs["context"] = context
        super().__init__(
            message,
            category=ErrorCategory.DEPENDENCY,
            severity=SeverityLevel.ERROR,
            **kwargs
        )


class SignatureMismatch(AutocoderError):
    """Raised when build.lock signature does not verify."""
    def __init__(self, message: str = "Signature mismatch", **kwargs):
        super().__init__(message, category=ErrorCategory.DEPENDENCY, severity=SeverityLevel.CRITICAL, **kwargs)