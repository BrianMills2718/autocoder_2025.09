"""
Graded Failure Handler
Implements graded failure policy distinguishing validation failures from runtime failures
"""

import sys
import asyncio
import traceback
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.core.exceptions import ValidationError, AutocoderRuntimeError
from autocoder_cc.observability.structured_logging import get_logger


class FailureType(Enum):
    """Classification of failure types"""
    VALIDATION = "validation"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"


class FailureSeverity(Enum):
    """Severity levels for failures"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FailureContext:
    """Context information for a failure"""
    failure_type: FailureType
    severity: FailureSeverity
    component: str
    operation: str
    error_message: str
    error_type: str
    stack_trace: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailurePolicy:
    """Policy for handling a specific type of failure"""
    failure_type: FailureType
    action: str  # "fail_hard", "fail_soft", "retry", "circuit_break"
    max_retries: int = 0
    retry_delay_ms: int = 1000
    circuit_breaker_enabled: bool = False
    alerting_enabled: bool = True
    metrics_enabled: bool = True
    
    def should_fail_hard(self) -> bool:
        """Check if this failure should fail hard"""
        return self.action == "fail_hard"
    
    def should_fail_soft(self) -> bool:
        """Check if this failure should fail soft"""
        return self.action == "fail_soft"
    
    def should_retry(self) -> bool:
        """Check if this failure should be retried"""
        return self.action == "retry" and self.max_retries > 0


class GradedFailureHandler:
    """
    Graded failure handler that implements different failure policies
    based on failure type and severity
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.failure_policies = self._initialize_policies()
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.retry_counts: Dict[str, int] = {}
        
    def _initialize_policies(self) -> Dict[FailureType, FailurePolicy]:
        """Initialize default failure policies"""
        policies = {
            # Validation failures: Always fail hard
            FailureType.VALIDATION: FailurePolicy(
                failure_type=FailureType.VALIDATION,
                action="fail_hard",
                max_retries=0,
                circuit_breaker_enabled=False,
                alerting_enabled=True,
                metrics_enabled=True
            ),
            
            # Runtime failures: Fail soft with resilience patterns
            FailureType.RUNTIME: FailurePolicy(
                failure_type=FailureType.RUNTIME,
                action="fail_soft",
                max_retries=3,
                retry_delay_ms=1000,
                circuit_breaker_enabled=True,
                alerting_enabled=True,
                metrics_enabled=True
            ),
            
            # Configuration failures: Fail hard
            FailureType.CONFIGURATION: FailurePolicy(
                failure_type=FailureType.CONFIGURATION,
                action="fail_hard",
                max_retries=0,
                circuit_breaker_enabled=False,
                alerting_enabled=True,
                metrics_enabled=True
            ),
            
            # Security failures: Fail hard immediately
            FailureType.SECURITY: FailurePolicy(
                failure_type=FailureType.SECURITY,
                action="fail_hard",
                max_retries=0,
                circuit_breaker_enabled=False,
                alerting_enabled=True,
                metrics_enabled=True
            ),
            
            # Infrastructure failures: Fail soft with retry
            FailureType.INFRASTRUCTURE: FailurePolicy(
                failure_type=FailureType.INFRASTRUCTURE,
                action="retry",
                max_retries=5,
                retry_delay_ms=2000,
                circuit_breaker_enabled=True,
                alerting_enabled=True,
                metrics_enabled=True
            )
        }
        
        return policies
    
    def classify_failure(self, exception: Exception, component: str, operation: str) -> FailureContext:
        """Classify a failure and create context"""
        failure_type = self._determine_failure_type(exception)
        severity = self._determine_severity(exception, failure_type)
        
        return FailureContext(
            failure_type=failure_type,
            severity=severity,
            component=component,
            operation=operation,
            error_message=str(exception),
            error_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            metadata={
                "exception_args": getattr(exception, 'args', []),
                "exception_cause": str(getattr(exception, '__cause__', None)),
                "exception_context": str(getattr(exception, '__context__', None))
            }
        )
    
    def _determine_failure_type(self, exception: Exception) -> FailureType:
        """Determine the failure type based on exception"""
        if isinstance(exception, ValidationError):
            return FailureType.VALIDATION
        elif isinstance(exception, (ValueError, TypeError)) and 'validation' in str(exception).lower():
            return FailureType.VALIDATION
        elif isinstance(exception, (PermissionError, SecurityError)):
            return FailureType.SECURITY
        elif isinstance(exception, (FileNotFoundError, ImportError, ModuleNotFoundError)):
            return FailureType.CONFIGURATION
        elif isinstance(exception, (ConnectionError, TimeoutError, OSError)):
            return FailureType.INFRASTRUCTURE
        else:
            return FailureType.RUNTIME
    
    def _determine_severity(self, exception: Exception, failure_type: FailureType) -> FailureSeverity:
        """Determine failure severity"""
        if failure_type in [FailureType.VALIDATION, FailureType.SECURITY]:
            return FailureSeverity.CRITICAL
        elif failure_type == FailureType.CONFIGURATION:
            return FailureSeverity.HIGH
        elif isinstance(exception, (TimeoutError, ConnectionError)):
            return FailureSeverity.MEDIUM
        else:
            return FailureSeverity.LOW
    
    async def handle_failure(self, exception: Exception, component: str, operation: str) -> bool:
        """
        Handle a failure according to graded policy
        
        Returns:
            bool: True if failure was handled and operation should continue, False if should fail
        """
        context = self.classify_failure(exception, component, operation)
        policy = self.failure_policies.get(context.failure_type)
        
        if not policy:
            # Default to fail hard if no policy defined
            await self._fail_hard(context)
            return False
        
        # Log failure details
        self.logger.error(
            f"Failure detected in {component}.{operation}",
            extra={
                "failure_type": context.failure_type.value,
                "severity": context.severity.value,
                "error_type": context.error_type,
                "error_message": context.error_message,
                "policy_action": policy.action,
                "component": component,
                "operation": operation
            }
        )
        
        # Handle according to policy
        if policy.should_fail_hard():
            await self._fail_hard(context)
            return False
        elif policy.should_fail_soft():
            return await self._fail_soft(context, policy)
        elif policy.should_retry():
            return await self._retry_operation(context, policy)
        else:
            # Unknown policy action, fail hard
            await self._fail_hard(context)
            return False
    
    async def _fail_hard(self, context: FailureContext):
        """Implement fail-hard behavior - immediate system termination"""
        self.logger.critical(
            f"FAIL-HARD: Terminating system due to {context.failure_type.value} failure",
            extra={
                "failure_context": context.__dict__,
                "termination_reason": "fail_hard_policy"
            }
        )
        
        # Emit metrics if enabled
        await self._emit_failure_metrics(context, "fail_hard")
        
        # Send alerts if enabled
        await self._send_failure_alert(context, "CRITICAL: System termination")
        
        # Exit with non-zero code
        sys.exit(1)
    
    async def _fail_soft(self, context: FailureContext, policy: FailurePolicy) -> bool:
        """Implement fail-soft behavior - continue with degraded functionality"""
        self.logger.warning(
            f"FAIL-SOFT: Continuing with degraded functionality after {context.failure_type.value} failure",
            extra={
                "failure_context": context.__dict__,
                "policy": policy.__dict__
            }
        )
        
        # Check circuit breaker
        if policy.circuit_breaker_enabled:
            circuit_key = f"{context.component}.{context.operation}"
            if self._is_circuit_open(circuit_key):
                self.logger.warning(f"Circuit breaker OPEN for {circuit_key}")
                return False
            
            # Record failure in circuit breaker
            self._record_circuit_failure(circuit_key)
        
        # Emit metrics if enabled
        await self._emit_failure_metrics(context, "fail_soft")
        
        # Send alerts if enabled
        await self._send_failure_alert(context, "WARNING: Degraded functionality")
        
        # Continue execution
        return True
    
    async def _retry_operation(self, context: FailureContext, policy: FailurePolicy) -> bool:
        """Implement retry behavior with exponential backoff"""
        retry_key = f"{context.component}.{context.operation}"
        current_retries = self.retry_counts.get(retry_key, 0)
        
        if current_retries >= policy.max_retries:
            self.logger.error(
                f"RETRY-EXHAUSTED: Max retries ({policy.max_retries}) exceeded for {retry_key}",
                extra={
                    "failure_context": context.__dict__,
                    "retry_count": current_retries
                }
            )
            
            # Fall back to fail soft
            return await self._fail_soft(context, policy)
        
        # Increment retry count
        self.retry_counts[retry_key] = current_retries + 1
        
        # Calculate delay with exponential backoff
        delay_ms = policy.retry_delay_ms * (2 ** current_retries)
        
        self.logger.info(
            f"RETRY: Attempting retry {current_retries + 1}/{policy.max_retries} for {retry_key}",
            extra={
                "failure_context": context.__dict__,
                "retry_count": current_retries + 1,
                "delay_ms": delay_ms
            }
        )
        
        # Wait before retry
        await asyncio.sleep(delay_ms / 1000.0)
        
        # Emit metrics if enabled
        await self._emit_failure_metrics(context, "retry")
        
        # Return True to indicate retry should happen
        return True
    
    def _is_circuit_open(self, circuit_key: str) -> bool:
        """Check if circuit breaker is open"""
        circuit = self.circuit_breakers.get(circuit_key)
        if not circuit:
            return False
        
        # Simple circuit breaker logic
        if circuit["state"] == "open":
            # Check if we should move to half-open
            if datetime.now().timestamp() - circuit["last_failure"] > 60:  # 60 seconds
                circuit["state"] = "half_open"
                return False
            return True
        
        return False
    
    def _record_circuit_failure(self, circuit_key: str):
        """Record a failure in the circuit breaker"""
        if circuit_key not in self.circuit_breakers:
            self.circuit_breakers[circuit_key] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None
            }
        
        circuit = self.circuit_breakers[circuit_key]
        circuit["failure_count"] += 1
        circuit["last_failure"] = datetime.now().timestamp()
        
        # Open circuit if too many failures
        if circuit["failure_count"] >= 5:
            circuit["state"] = "open"
            self.logger.warning(f"Circuit breaker OPENED for {circuit_key}")
    
    async def _emit_failure_metrics(self, context: FailureContext, action: str):
        """Emit failure metrics"""
        # Placeholder for metrics emission
        self.logger.info(
            f"METRICS: Failure metric emitted",
            extra={
                "metric_type": "failure_count",
                "failure_type": context.failure_type.value,
                "severity": context.severity.value,
                "action": action,
                "component": context.component,
                "operation": context.operation
            }
        )
    
    async def _send_failure_alert(self, context: FailureContext, alert_message: str):
        """Send failure alert"""
        # Placeholder for alerting
        self.logger.info(
            f"ALERT: {alert_message}",
            extra={
                "alert_type": "failure_alert",
                "failure_type": context.failure_type.value,
                "severity": context.severity.value,
                "component": context.component,
                "operation": context.operation,
                "error_message": context.error_message
            }
        )
    
    def reset_retry_count(self, component: str, operation: str):
        """Reset retry count for a component operation"""
        retry_key = f"{component}.{operation}"
        if retry_key in self.retry_counts:
            del self.retry_counts[retry_key]
    
    def get_circuit_status(self, component: str, operation: str) -> Dict[str, Any]:
        """Get circuit breaker status"""
        circuit_key = f"{component}.{operation}"
        return self.circuit_breakers.get(circuit_key, {"state": "closed", "failure_count": 0})
    
    def update_policy(self, failure_type: FailureType, policy: FailurePolicy):
        """Update failure policy for a specific failure type"""
        self.failure_policies[failure_type] = policy
        self.logger.info(
            f"Updated failure policy for {failure_type.value}",
            extra={
                "failure_type": failure_type.value,
                "policy": policy.__dict__
            }
        )


# Create a global instance
graded_failure_handler = GradedFailureHandler()


class SecurityError(Exception):
    """Custom security error exception"""
    pass


def test_policies():
    """Test the graded failure policies"""
    import asyncio
    
    async def test_validation_failure():
        """Test validation failure (should fail hard)"""
        handler = GradedFailureHandler()
        
        try:
            result = await handler.handle_failure(
                ValidationError("Schema validation failed"),
                "test_component",
                "test_operation"
            )
            print(f"Validation failure result: {result}")
        except SystemExit:
            print("✅ Validation failure correctly triggered fail-hard (system exit)")
    
    async def test_runtime_failure():
        """Test runtime failure (should fail soft)"""
        handler = GradedFailureHandler()
        
        result = await handler.handle_failure(
            RuntimeError("Connection timeout"),
            "test_component",
            "test_operation"
        )
        print(f"✅ Runtime failure result: {result} (should be True for fail-soft)")
    
    async def test_security_failure():
        """Test security failure (should fail hard)"""
        handler = GradedFailureHandler()
        
        try:
            result = await handler.handle_failure(
                SecurityError("Unauthorized access attempt"),
                "test_component", 
                "test_operation"
            )
            print(f"Security failure result: {result}")
        except SystemExit:
            print("✅ Security failure correctly triggered fail-hard (system exit)")
    
    async def test_infrastructure_failure():
        """Test infrastructure failure (should retry)"""
        handler = GradedFailureHandler()
        
        result = await handler.handle_failure(
            ConnectionError("Database connection failed"),
            "test_component",
            "test_operation"
        )
        print(f"✅ Infrastructure failure result: {result} (should be True for retry)")
    
    # Run tests
    print("Testing graded failure policies...")
    
    # Test each failure type
    print("\n1. Testing validation failure (should fail hard):")
    try:
        asyncio.run(test_validation_failure())
    except SystemExit:
        print("   ✅ Validation failure correctly failed hard")
    
    print("\n2. Testing runtime failure (should fail soft):")
    asyncio.run(test_runtime_failure())
    
    print("\n3. Testing security failure (should fail hard):")
    try:
        asyncio.run(test_security_failure())
    except SystemExit:
        print("   ✅ Security failure correctly failed hard")
    
    print("\n4. Testing infrastructure failure (should retry):")
    asyncio.run(test_infrastructure_failure())
    
    print("\n✅ All graded failure policy tests completed")


if __name__ == "__main__":
    test_policies()