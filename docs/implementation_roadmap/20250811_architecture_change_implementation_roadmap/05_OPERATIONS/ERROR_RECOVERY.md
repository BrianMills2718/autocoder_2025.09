# Error Recovery Patterns for Port-Based Architecture

## Overview
This document defines comprehensive error recovery patterns for the port-based architecture, ensuring system resilience, data integrity, and graceful degradation under failure conditions.

## 1. Error Classification

### 1.1 Error Taxonomy
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"    # System cannot continue
    HIGH = "high"           # Component must restart
    MEDIUM = "medium"       # Retry with backoff
    LOW = "low"            # Log and continue
    INFO = "info"          # Informational only

class ErrorCategory(Enum):
    """Error categories for routing recovery"""
    TRANSIENT = "transient"          # Temporary, retry likely to succeed
    PERMANENT = "permanent"          # Will not succeed on retry
    POISON_MESSAGE = "poison"        # Bad data causing failures
    RESOURCE = "resource"            # Resource exhaustion
    TIMEOUT = "timeout"              # Operation timeout
    VALIDATION = "validation"        # Data validation failure
    COMMUNICATION = "communication"  # Port/network issues
    DEPENDENCY = "dependency"        # External service failure

@dataclass
class ErrorContext:
    """Complete error context for recovery decisions"""
    error_id: str
    severity: ErrorSeverity
    category: ErrorCategory
    component_name: str
    port_name: Optional[str]
    message_id: Optional[str]
    error_message: str
    stack_trace: str
    occurrence_count: int = 1
    first_occurrence: float = 0.0
    last_occurrence: float = 0.0
    recovery_attempts: int = 0
    metadata: dict = None
```

## 2. Recovery Strategies

### 2.1 Retry Policies
```python
class RetryPolicy:
    """Configurable retry policies for different error types"""
    
    def __init__(self):
        self.policies = {
            ErrorCategory.TRANSIENT: ExponentialBackoffRetry(
                max_retries=3,
                base_delay_ms=100,
                max_delay_ms=5000,
                jitter=True
            ),
            ErrorCategory.TIMEOUT: LinearBackoffRetry(
                max_retries=2,
                delay_ms=1000
            ),
            ErrorCategory.RESOURCE: ExponentialBackoffRetry(
                max_retries=5,
                base_delay_ms=1000,
                max_delay_ms=30000
            ),
            ErrorCategory.PERMANENT: NoRetry(),
            ErrorCategory.POISON_MESSAGE: NoRetry(),
            ErrorCategory.VALIDATION: NoRetry()
        }
    
    def get_policy(self, error_category: ErrorCategory):
        """Get retry policy for error category"""
        return self.policies.get(error_category, NoRetry())

class ExponentialBackoffRetry:
    """Exponential backoff with jitter"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_ms: int = 100,
        max_delay_ms: int = 10000,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter = jitter
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    if self.jitter:
                        delay = delay * (0.5 + random.random())
                    
                    await anyio.sleep(delay / 1000)
                else:
                    raise RetryExhausted(
                        f"Failed after {self.max_retries} retries",
                        last_error
                    )
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt number"""
        delay = self.base_delay_ms * (2 ** attempt)
        return min(delay, self.max_delay_ms)
```

### 2.2 Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Circuit breaker to prevent cascade failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_count = 0
        
    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_count = 0
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
            
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_count += 1
            if self.half_open_count >= self.half_open_requests:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            
class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, reject calls
    HALF_OPEN = "half_open" # Testing recovery
```

### 2.3 Bulkhead Pattern
```python
class Bulkhead:
    """Isolate resources to prevent total failure"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = anyio.Semaphore(max_concurrent)
        self.in_flight = 0
        
    async def execute(self, func, *args, **kwargs):
        """Execute with resource isolation"""
        async with self.semaphore:
            self.in_flight += 1
            try:
                return await func(*args, **kwargs)
            finally:
                self.in_flight -= 1
    
    def get_utilization(self) -> float:
        """Get current resource utilization"""
        return self.in_flight / self.max_concurrent
```

## 3. Component-Level Recovery

### 3.1 Component Recovery Manager
```python
class ComponentRecoveryManager:
    """Manage component-level error recovery"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.error_history = deque(maxlen=100)
        self.recovery_strategies = {}
        self.health_checker = HealthChecker()
        
    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryAction:
        """Determine and execute recovery action"""
        
        # Create error context
        error_context = self.create_error_context(error, context)
        self.error_history.append(error_context)
        
        # Determine recovery action
        action = self.determine_recovery_action(error_context)
        
        # Execute recovery
        await self.execute_recovery(action, error_context)
        
        return action
    
    def determine_recovery_action(
        self,
        error_context: ErrorContext
    ) -> RecoveryAction:
        """Determine appropriate recovery action"""
        
        # Check error patterns
        if self.is_poison_message(error_context):
            return RecoveryAction.QUARANTINE_MESSAGE
            
        if self.is_resource_exhaustion(error_context):
            return RecoveryAction.THROTTLE
            
        if self.is_persistent_failure(error_context):
            return RecoveryAction.RESTART_COMPONENT
            
        if error_context.category == ErrorCategory.TRANSIENT:
            return RecoveryAction.RETRY
            
        return RecoveryAction.LOG_AND_CONTINUE
    
    def is_poison_message(self, error_context: ErrorContext) -> bool:
        """Detect poison message pattern"""
        if error_context.message_id:
            # Check if same message failed multiple times
            failures = [
                e for e in self.error_history
                if e.message_id == error_context.message_id
            ]
            return len(failures) >= 3
        return False
    
    def is_resource_exhaustion(self, error_context: ErrorContext) -> bool:
        """Detect resource exhaustion"""
        return (
            error_context.category == ErrorCategory.RESOURCE or
            "out of memory" in error_context.error_message.lower() or
            "too many open files" in error_context.error_message.lower()
        )
    
    def is_persistent_failure(self, error_context: ErrorContext) -> bool:
        """Detect persistent failure requiring restart"""
        recent_errors = [
            e for e in self.error_history
            if time.monotonic() - e.last_occurrence < 60
        ]
        return len(recent_errors) >= 10
    
    async def execute_recovery(
        self,
        action: RecoveryAction,
        error_context: ErrorContext
    ):
        """Execute recovery action"""
        
        if action == RecoveryAction.RETRY:
            await self.retry_operation(error_context)
            
        elif action == RecoveryAction.QUARANTINE_MESSAGE:
            await self.quarantine_message(error_context)
            
        elif action == RecoveryAction.THROTTLE:
            await self.apply_throttling()
            
        elif action == RecoveryAction.RESTART_COMPONENT:
            await self.restart_component()
            
        elif action == RecoveryAction.LOG_AND_CONTINUE:
            self.log_error(error_context)

class RecoveryAction(Enum):
    RETRY = "retry"
    QUARANTINE_MESSAGE = "quarantine"
    THROTTLE = "throttle"
    RESTART_COMPONENT = "restart"
    LOG_AND_CONTINUE = "log_continue"
    CIRCUIT_BREAK = "circuit_break"
```

## 4. Port-Level Recovery

### 4.1 Port Recovery Mechanisms
```python
class PortRecoveryManager:
    """Manage port-specific error recovery"""
    
    def __init__(self, port_name: str, capacity: int):
        self.port_name = port_name
        self.capacity = capacity
        self.overflow_handler = OverflowHandler()
        self.dead_letter_queue = DeadLetterQueue()
        
    async def handle_port_error(
        self,
        error_type: str,
        message: Optional[Message] = None
    ):
        """Handle port-specific errors"""
        
        if error_type == "overflow":
            await self.handle_overflow(message)
            
        elif error_type == "connection_lost":
            await self.handle_connection_lost()
            
        elif error_type == "send_failure":
            await self.handle_send_failure(message)
            
        elif error_type == "receive_timeout":
            await self.handle_receive_timeout()
    
    async def handle_overflow(self, message: Message):
        """Handle port buffer overflow"""
        strategy = self.overflow_handler.get_strategy()
        
        if strategy == OverflowStrategy.DROP_OLDEST:
            # Remove oldest message from buffer
            await self.drop_oldest_message()
            await self.retry_send(message)
            
        elif strategy == OverflowStrategy.DROP_NEWEST:
            # Drop the new message
            await self.dead_letter_queue.add(
                message,
                reason="Port overflow - dropped newest"
            )
            
        elif strategy == OverflowStrategy.BLOCK:
            # Wait with timeout
            try:
                await anyio.wait_for(
                    self.wait_for_space(),
                    timeout=5.0
                )
                await self.retry_send(message)
            except TimeoutError:
                await self.dead_letter_queue.add(
                    message,
                    reason="Port overflow - timeout"
                )
    
    async def handle_connection_lost(self):
        """Handle lost port connection"""
        max_reconnect_attempts = 5
        
        for attempt in range(max_reconnect_attempts):
            try:
                await self.reconnect_port()
                return
            except Exception as e:
                delay = 2 ** attempt  # Exponential backoff
                await anyio.sleep(delay)
        
        # Failed to reconnect
        raise PortConnectionError(
            f"Failed to reconnect port {self.port_name}"
        )

class OverflowStrategy(Enum):
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    BLOCK = "block"
    SPILL_TO_DISK = "spill_to_disk"
```

### 4.2 Dead Letter Queue
```python
class DeadLetterQueue:
    """Manage messages that cannot be processed"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue = deque(maxlen=max_size)
        self.storage = DLQStorage()
        
    async def add(
        self,
        message: Message,
        reason: str,
        error: Optional[Exception] = None
    ):
        """Add message to dead letter queue"""
        
        dlq_entry = {
            "message": message,
            "reason": reason,
            "error": str(error) if error else None,
            "timestamp": datetime.utcnow(),
            "attempts": message.metadata.get("retry_count", 0)
        }
        
        self.queue.append(dlq_entry)
        
        # Persist to storage
        await self.storage.persist(dlq_entry)
        
        # Alert if queue is getting full
        if len(self.queue) > self.max_size * 0.8:
            await self.send_alert(
                "DLQ near capacity",
                f"Dead letter queue at {len(self.queue)}/{self.max_size}"
            )
    
    async def reprocess(
        self,
        filter_func=None,
        max_messages: int = 100
    ) -> List[Message]:
        """Attempt to reprocess messages from DLQ"""
        
        messages_to_reprocess = []
        
        for entry in list(self.queue):
            if filter_func and not filter_func(entry):
                continue
                
            messages_to_reprocess.append(entry["message"])
            
            if len(messages_to_reprocess) >= max_messages:
                break
        
        # Remove from queue
        for msg in messages_to_reprocess:
            self.queue.remove(
                next(e for e in self.queue if e["message"] == msg)
            )
        
        return messages_to_reprocess
    
    async def inspect(self) -> List[Dict]:
        """Inspect DLQ contents for debugging"""
        return [
            {
                "message_id": e["message"].metadata.get("id"),
                "reason": e["reason"],
                "timestamp": e["timestamp"],
                "attempts": e["attempts"]
            }
            for e in self.queue
        ]
```

## 5. System-Level Recovery

### 5.1 Cascade Failure Prevention
```python
class CascadeFailureManager:
    """Prevent cascade failures across system"""
    
    def __init__(self):
        self.component_health = {}
        self.dependency_graph = {}
        self.circuit_breakers = {}
        
    async def monitor_system_health(self):
        """Continuous system health monitoring"""
        
        while True:
            # Check all components
            for component_name in self.component_health:
                health = await self.check_component_health(component_name)
                
                if health.status == HealthStatus.UNHEALTHY:
                    await self.handle_unhealthy_component(component_name)
                    
                elif health.status == HealthStatus.DEGRADED:
                    await self.handle_degraded_component(component_name)
            
            # Check for cascade patterns
            if self.detect_cascade_pattern():
                await self.activate_emergency_mode()
            
            await anyio.sleep(5)  # Check every 5 seconds
    
    def detect_cascade_pattern(self) -> bool:
        """Detect cascade failure pattern"""
        
        unhealthy_count = sum(
            1 for h in self.component_health.values()
            if h.status == HealthStatus.UNHEALTHY
        )
        
        # Cascade detected if >30% components unhealthy
        total_components = len(self.component_health)
        return unhealthy_count > total_components * 0.3
    
    async def activate_emergency_mode(self):
        """Activate emergency mode to prevent total failure"""
        
        print("🚨 EMERGENCY MODE ACTIVATED - Cascade failure detected")
        
        # 1. Open all circuit breakers
        for cb in self.circuit_breakers.values():
            cb.state = CircuitState.OPEN
        
        # 2. Throttle all inputs
        await self.throttle_all_sources(rate=0.1)  # 10% of normal
        
        # 3. Drain queues
        await self.drain_all_queues()
        
        # 4. Alert operations team
        await self.send_emergency_alert()
        
        # 5. Wait for stabilization
        await anyio.sleep(30)
        
        # 6. Gradual recovery
        await self.gradual_recovery()
    
    async def gradual_recovery(self):
        """Gradually recover from emergency mode"""
        
        recovery_steps = [0.1, 0.25, 0.5, 0.75, 1.0]
        
        for step in recovery_steps:
            print(f"Recovery: {step * 100}% capacity")
            
            # Increase throttle
            await self.throttle_all_sources(rate=step)
            
            # Check stability
            await anyio.sleep(30)
            
            if self.detect_cascade_pattern():
                print("Recovery failed, returning to emergency mode")
                await self.activate_emergency_mode()
                return
        
        print("✅ System recovered successfully")
```

### 5.2 Checkpoint Recovery
```python
class CheckpointRecoveryManager:
    """Manage checkpoint-based recovery"""
    
    def __init__(self):
        self.checkpoint_store = CheckpointStore()
        self.recovery_coordinator = RecoveryCoordinator()
        
    async def create_checkpoint(
        self,
        component_name: str,
        state: Dict[str, Any]
    ):
        """Create component checkpoint"""
        
        checkpoint = {
            "component": component_name,
            "state": state,
            "timestamp": datetime.utcnow(),
            "version": self.get_component_version(component_name)
        }
        
        await self.checkpoint_store.save(checkpoint)
    
    async def recover_from_checkpoint(
        self,
        component_name: str,
        checkpoint_id: Optional[str] = None
    ):
        """Recover component from checkpoint"""
        
        # Get latest checkpoint if not specified
        if not checkpoint_id:
            checkpoint = await self.checkpoint_store.get_latest(component_name)
        else:
            checkpoint = await self.checkpoint_store.get(checkpoint_id)
        
        if not checkpoint:
            raise NoCheckpointError(f"No checkpoint for {component_name}")
        
        # Coordinate recovery
        await self.recovery_coordinator.prepare_recovery(component_name)
        
        # Restore state
        await self.restore_component_state(
            component_name,
            checkpoint["state"]
        )
        
        # Resume processing
        await self.recovery_coordinator.resume_processing(component_name)
        
        print(f"✅ Recovered {component_name} from checkpoint {checkpoint['timestamp']}")
    
    async def coordinated_recovery(self, failed_components: List[str]):
        """Coordinate recovery of multiple components"""
        
        # Determine recovery order based on dependencies
        recovery_order = self.determine_recovery_order(failed_components)
        
        for component in recovery_order:
            try:
                await self.recover_from_checkpoint(component)
            except Exception as e:
                print(f"Failed to recover {component}: {e}")
                # Try alternative recovery
                await self.alternative_recovery(component)
```

## 6. Error Monitoring and Alerting

### 6.1 Error Metrics Collection
```python
class ErrorMetricsCollector:
    """Collect and analyze error metrics"""
    
    def __init__(self):
        self.error_counts = Counter()
        self.error_rates = {}
        self.error_patterns = []
        
    async def record_error(
        self,
        error_context: ErrorContext
    ):
        """Record error for analysis"""
        
        # Count by category
        self.error_counts[error_context.category] += 1
        
        # Calculate rates
        self.update_error_rate(error_context)
        
        # Detect patterns
        pattern = self.detect_pattern(error_context)
        if pattern:
            self.error_patterns.append(pattern)
            await self.alert_on_pattern(pattern)
    
    def update_error_rate(self, error_context: ErrorContext):
        """Update error rate calculations"""
        
        key = f"{error_context.component_name}:{error_context.category}"
        
        if key not in self.error_rates:
            self.error_rates[key] = ErrorRate()
        
        self.error_rates[key].add_error()
    
    def detect_pattern(self, error_context: ErrorContext) -> Optional[ErrorPattern]:
        """Detect error patterns"""
        
        # Check for spike
        if self.is_error_spike(error_context):
            return ErrorPattern(
                type="spike",
                component=error_context.component_name,
                details="Sudden increase in errors"
            )
        
        # Check for recurring
        if self.is_recurring_error(error_context):
            return ErrorPattern(
                type="recurring",
                component=error_context.component_name,
                details="Error recurring at regular intervals"
            )
        
        return None
    
    async def alert_on_pattern(self, pattern: ErrorPattern):
        """Send alert for detected pattern"""
        
        alert = {
            "severity": "high",
            "pattern": pattern.type,
            "component": pattern.component,
            "details": pattern.details,
            "timestamp": datetime.utcnow()
        }
        
        await self.send_alert(alert)
```

### 6.2 Alert Management
```python
class AlertManager:
    """Manage error alerts and escalation"""
    
    def __init__(self):
        self.alert_rules = self.load_alert_rules()
        self.alert_history = deque(maxlen=1000)
        self.escalation_policy = EscalationPolicy()
        
    async def process_error(
        self,
        error_context: ErrorContext
    ):
        """Process error and determine if alert needed"""
        
        # Check alert rules
        for rule in self.alert_rules:
            if self.matches_rule(error_context, rule):
                await self.send_alert(error_context, rule)
    
    def matches_rule(
        self,
        error_context: ErrorContext,
        rule: AlertRule
    ) -> bool:
        """Check if error matches alert rule"""
        
        return (
            error_context.severity >= rule.min_severity and
            (not rule.component_filter or 
             error_context.component_name in rule.component_filter) and
            (not rule.category_filter or
             error_context.category in rule.category_filter)
        )
    
    async def send_alert(
        self,
        error_context: ErrorContext,
        rule: AlertRule
    ):
        """Send alert based on rule"""
        
        alert = Alert(
            error_context=error_context,
            rule=rule,
            timestamp=datetime.utcnow()
        )
        
        # Check for duplicate suppression
        if self.is_duplicate_alert(alert):
            return
        
        # Send to appropriate channel
        if rule.alert_channel == "email":
            await self.send_email_alert(alert)
        elif rule.alert_channel == "slack":
            await self.send_slack_alert(alert)
        elif rule.alert_channel == "pager":
            await self.send_pager_alert(alert)
        
        # Record alert
        self.alert_history.append(alert)
        
        # Check escalation
        if self.requires_escalation(alert):
            await self.escalation_policy.escalate(alert)
```

## 7. Recovery Testing

### 7.1 Chaos Engineering
```python
class ChaosEngineer:
    """Test error recovery with controlled failures"""
    
    def __init__(self):
        self.failure_injectors = {
            "network": NetworkFailureInjector(),
            "resource": ResourceFailureInjector(),
            "component": ComponentFailureInjector(),
            "message": MessageCorruptionInjector()
        }
        
    async def run_chaos_test(
        self,
        test_scenario: str,
        duration_seconds: int = 60
    ):
        """Run chaos engineering test"""
        
        print(f"🔥 Starting chaos test: {test_scenario}")
        
        # Start monitoring
        monitor = RecoveryMonitor()
        await monitor.start()
        
        # Inject failures
        if test_scenario == "cascade_failure":
            await self.test_cascade_failure()
        elif test_scenario == "poison_message":
            await self.test_poison_message()
        elif test_scenario == "resource_exhaustion":
            await self.test_resource_exhaustion()
        elif test_scenario == "network_partition":
            await self.test_network_partition()
        
        # Wait for duration
        await anyio.sleep(duration_seconds)
        
        # Stop failures
        await self.stop_all_failures()
        
        # Collect results
        results = await monitor.get_results()
        
        # Validate recovery
        self.validate_recovery(results)
        
        return results
    
    async def test_cascade_failure(self):
        """Test cascade failure recovery"""
        
        # Kill critical component
        await self.failure_injectors["component"].kill("controller")
        
        # Overload remaining components
        await self.failure_injectors["resource"].exhaust_memory("store")
        
        # Create network issues
        await self.failure_injectors["network"].add_latency(1000)
    
    def validate_recovery(self, results: Dict):
        """Validate system recovered properly"""
        
        assertions = [
            results["recovery_time"] < 60,  # Recovered within 1 minute
            results["data_loss"] == 0,       # No data loss
            results["final_health"] == "healthy",  # System healthy
            results["alerts_sent"] > 0       # Alerts were sent
        ]
        
        if all(assertions):
            print("✅ Chaos test passed - system recovered successfully")
        else:
            print("❌ Chaos test failed - recovery incomplete")
            print(f"Results: {results}")
```

## Summary

This error recovery system provides:

1. **Comprehensive error classification** for targeted recovery
2. **Multiple recovery strategies** (retry, circuit breaker, bulkhead)
3. **Component-level recovery** with automatic restart
4. **Port-level recovery** with overflow handling
5. **System-level cascade prevention**
6. **Dead letter queue** for poison messages
7. **Checkpoint-based recovery** for stateful components
8. **Error monitoring and alerting** with pattern detection
9. **Chaos engineering** for recovery testing

The system ensures high availability, data integrity, and graceful degradation under failure conditions.