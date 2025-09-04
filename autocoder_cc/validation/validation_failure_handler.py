"""
Validation Failure Handler
Implements fail-hard behavior for validation failures
"""

import sys
import os
import traceback
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.core.exceptions import ValidationError
from autocoder_cc.observability.structured_logging import get_logger


class ValidationFailureType(Enum):
    """Types of validation failures"""
    SCHEMA_VALIDATION = "schema_validation"
    TYPE_VALIDATION = "type_validation"
    CONSTRAINT_VALIDATION = "constraint_validation"
    SECURITY_VALIDATION = "security_validation"
    CONFIGURATION_VALIDATION = "configuration_validation"
    BLUEPRINT_VALIDATION = "blueprint_validation"
    COMPONENT_VALIDATION = "component_validation"
    INTEGRATION_VALIDATION = "integration_validation"


@dataclass
class ValidationFailureContext:
    """Context for validation failure"""
    failure_type: ValidationFailureType
    component: str
    operation: str
    error_message: str
    error_details: Dict[str, Any]
    stack_trace: str
    timestamp: datetime = field(default_factory=datetime.now)
    validation_data: Optional[Dict[str, Any]] = None
    expected_schema: Optional[str] = None
    actual_data: Optional[Any] = None


class ValidationFailureHandler:
    """
    Handles validation failures with fail-hard behavior
    All validation failures result in immediate system termination
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.failure_count = 0
        self.failure_history: List[ValidationFailureContext] = []
        
    def handle_validation_failure(
        self,
        failure_type: ValidationFailureType,
        component: str,
        operation: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        validation_data: Optional[Dict[str, Any]] = None,
        expected_schema: Optional[str] = None,
        actual_data: Optional[Any] = None
    ) -> None:
        """
        Handle validation failure with fail-hard behavior
        This method never returns - it terminates the system
        """
        context = ValidationFailureContext(
            failure_type=failure_type,
            component=component,
            operation=operation,
            error_message=error_message,
            error_details=error_details or {},
            stack_trace=traceback.format_exc(),
            validation_data=validation_data,
            expected_schema=expected_schema,
            actual_data=actual_data
        )
        
        # Record failure
        self.failure_count += 1
        self.failure_history.append(context)
        
        # Log critical failure
        self._log_critical_failure(context)
        
        # Generate failure report
        self._generate_failure_report(context)
        
        # Terminate system immediately
        self._terminate_system(context)
    
    def _log_critical_failure(self, context: ValidationFailureContext):
        """Log critical validation failure"""
        self.logger.critical(
            f"VALIDATION FAILURE: {context.failure_type.value} in {context.component}.{context.operation}",
            extra={
                "failure_type": context.failure_type.value,
                "component": context.component,
                "operation": context.operation,
                "error_message": context.error_message,
                "error_details": context.error_details,
                "failure_count": self.failure_count,
                "timestamp": context.timestamp.isoformat(),
                "validation_data": context.validation_data,
                "expected_schema": context.expected_schema,
                "actual_data": str(context.actual_data) if context.actual_data else None,
                "stack_trace": context.stack_trace
            }
        )
    
    def _generate_failure_report(self, context: ValidationFailureContext):
        """Generate detailed failure report"""
        report_dir = Path("validation_failure_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp_str = context.timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"validation_failure_{timestamp_str}.txt"
        
        report_content = [
            "=" * 80,
            "VALIDATION FAILURE REPORT",
            "=" * 80,
            f"Timestamp: {context.timestamp.isoformat()}",
            f"Failure Type: {context.failure_type.value}",
            f"Component: {context.component}",
            f"Operation: {context.operation}",
            f"Error Message: {context.error_message}",
            "",
            "Error Details:",
            "-" * 40,
        ]
        
        for key, value in context.error_details.items():
            report_content.append(f"{key}: {value}")
        
        if context.validation_data:
            report_content.extend([
                "",
                "Validation Data:",
                "-" * 40,
                str(context.validation_data)
            ])
        
        if context.expected_schema:
            report_content.extend([
                "",
                "Expected Schema:",
                "-" * 40,
                context.expected_schema
            ])
        
        if context.actual_data:
            report_content.extend([
                "",
                "Actual Data:",
                "-" * 40,
                str(context.actual_data)
            ])
        
        report_content.extend([
            "",
            "Stack Trace:",
            "-" * 40,
            context.stack_trace,
            "",
            "System Information:",
            "-" * 40,
            f"Python Version: {sys.version}",
            f"Platform: {sys.platform}",
            f"Current Working Directory: {os.getcwd()}",
            f"Process ID: {os.getpid()}",
            "",
            "Environment Variables:",
            "-" * 40,
        ])
        
        # Add relevant environment variables
        for key, value in os.environ.items():
            if any(keyword in key.upper() for keyword in ['ENVIRONMENT', 'LOG', 'DEBUG', 'CONFIG']):
                report_content.append(f"{key}: {value}")
        
        report_content.extend([
            "",
            "=" * 80,
            "END OF VALIDATION FAILURE REPORT",
            "=" * 80
        ])
        
        try:
            with open(report_file, 'w') as f:
                f.write('\n'.join(report_content))
            
            self.logger.info(f"Validation failure report generated: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to generate validation failure report: {e}")
    
    def _terminate_system(self, context: ValidationFailureContext):
        """Terminate system immediately"""
        self.logger.critical(
            f"SYSTEM TERMINATION: Validation failure in {context.component}.{context.operation} requires immediate shutdown",
            extra={
                "termination_reason": "validation_failure",
                "failure_type": context.failure_type.value,
                "component": context.component,
                "operation": context.operation,
                "total_failures": self.failure_count
            }
        )
        
        # Print final error message to stderr
        print(f"CRITICAL VALIDATION FAILURE: {context.error_message}", file=sys.stderr)
        print(f"Component: {context.component}", file=sys.stderr)
        print(f"Operation: {context.operation}", file=sys.stderr)
        print(f"Failure Type: {context.failure_type.value}", file=sys.stderr)
        print("System terminating immediately due to validation failure.", file=sys.stderr)
        
        # Exit with specific error code for validation failures
        sys.exit(2)  # Exit code 2 for validation failures
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get validation failure statistics"""
        failure_types = {}
        components = {}
        
        for failure in self.failure_history:
            failure_type = failure.failure_type.value
            component = failure.component
            
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
            components[component] = components.get(component, 0) + 1
        
        return {
            "total_failures": self.failure_count,
            "failure_types": failure_types,
            "components": components,
            "first_failure": self.failure_history[0].timestamp.isoformat() if self.failure_history else None,
            "last_failure": self.failure_history[-1].timestamp.isoformat() if self.failure_history else None
        }


# Global validation failure handler instance
validation_failure_handler = ValidationFailureHandler()


def handle_schema_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    expected_schema: str,
    actual_data: Any,
    validation_errors: List[str]
):
    """Handle schema validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.SCHEMA_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={"validation_errors": validation_errors},
        expected_schema=expected_schema,
        actual_data=actual_data
    )


def handle_type_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    expected_type: str,
    actual_type: str,
    actual_value: Any
):
    """Handle type validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.TYPE_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "expected_type": expected_type,
            "actual_type": actual_type,
            "actual_value": str(actual_value)
        },
        actual_data=actual_value
    )


def handle_constraint_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    constraint_name: str,
    constraint_value: Any,
    actual_value: Any
):
    """Handle constraint validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.CONSTRAINT_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "constraint_name": constraint_name,
            "constraint_value": constraint_value,
            "actual_value": actual_value
        },
        actual_data=actual_value
    )


def handle_security_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    security_rule: str,
    violation_details: Dict[str, Any]
):
    """Handle security validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.SECURITY_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "security_rule": security_rule,
            "violation_details": violation_details
        }
    )


def handle_configuration_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    config_key: str,
    config_value: Any,
    validation_rule: str
):
    """Handle configuration validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.CONFIGURATION_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "config_key": config_key,
            "config_value": config_value,
            "validation_rule": validation_rule
        }
    )


def handle_blueprint_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    blueprint_path: str,
    validation_errors: List[str]
):
    """Handle blueprint validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.BLUEPRINT_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "blueprint_path": blueprint_path,
            "validation_errors": validation_errors
        }
    )


def handle_component_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    component_type: str,
    validation_errors: List[str]
):
    """Handle component validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.COMPONENT_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "component_type": component_type,
            "validation_errors": validation_errors
        }
    )


def handle_integration_validation_failure(
    component: str,
    operation: str,
    error_message: str,
    integration_type: str,
    validation_errors: List[str]
):
    """Handle integration validation failure"""
    validation_failure_handler.handle_validation_failure(
        failure_type=ValidationFailureType.INTEGRATION_VALIDATION,
        component=component,
        operation=operation,
        error_message=error_message,
        error_details={
            "integration_type": integration_type,
            "validation_errors": validation_errors
        }
    )


def test_validation_failure_handler():
    """Test validation failure handler"""
    print("Testing validation failure handler...")
    
    # Test schema validation failure
    print("\n1. Testing schema validation failure:")
    try:
        handle_schema_validation_failure(
            component="test_component",
            operation="test_operation",
            error_message="Schema validation failed",
            expected_schema="test_schema",
            actual_data={"invalid": "data"},
            validation_errors=["Field 'required_field' is missing"]
        )
    except SystemExit as e:
        print(f"   ✅ Schema validation failure correctly terminated system with exit code: {e.code}")
    
    # Test type validation failure
    print("\n2. Testing type validation failure:")
    try:
        handle_type_validation_failure(
            component="test_component",
            operation="test_operation",
            error_message="Type validation failed",
            expected_type="str",
            actual_type="int",
            actual_value=42
        )
    except SystemExit as e:
        print(f"   ✅ Type validation failure correctly terminated system with exit code: {e.code}")
    
    # Test constraint validation failure
    print("\n3. Testing constraint validation failure:")
    try:
        handle_constraint_validation_failure(
            component="test_component",
            operation="test_operation",
            error_message="Constraint validation failed",
            constraint_name="max_length",
            constraint_value=10,
            actual_value="This string is too long"
        )
    except SystemExit as e:
        print(f"   ✅ Constraint validation failure correctly terminated system with exit code: {e.code}")
    
    # Test security validation failure
    print("\n4. Testing security validation failure:")
    try:
        handle_security_validation_failure(
            component="test_component",
            operation="test_operation",
            error_message="Security validation failed",
            security_rule="no_hardcoded_secrets",
            violation_details={"secret_type": "api_key", "location": "line 42"}
        )
    except SystemExit as e:
        print(f"   ✅ Security validation failure correctly terminated system with exit code: {e.code}")
    
    print("\n✅ All validation failure tests completed (system would terminate on real failures)")


if __name__ == "__main__":
    test_validation_failure_handler()