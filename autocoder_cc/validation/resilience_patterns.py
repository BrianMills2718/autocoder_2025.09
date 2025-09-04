"""
Resilience Patterns
Runtime resilience patterns for fail-soft behavior
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.observability.structured_logging import get_logger


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    enabled: bool = False  # DISABLED BY DEFAULT - NO FALLBACKS
    failure_threshold: int = 1  # FAIL FAST - NO RETRIES
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 1  # MINIMAL RETRY
    expected_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class RetryConfig:
    """Configuration for retry pattern"""
    enabled: bool = False  # DISABLED BY DEFAULT - NO RETRIES
    max_attempts: int = 1  # FAIL FAST - NO RETRIES
    initial_delay_ms: int = 0  # NO DELAY
    max_delay_ms: int = 0  # NO DELAY
    backoff_multiplier: float = 1.0  # NO BACKOFF
    jitter: bool = False  # NO JITTER
    retryable_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class TimeoutConfig:
    """Configuration for timeout pattern"""
    timeout_seconds: float = 30.0
    raise_on_timeout: bool = True


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead pattern"""
    max_concurrent_calls: int = 10
    queue_size: int = 100


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.logger = get_logger(f"{__name__}.circuit_breaker.{name}")
        
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # If disabled, just execute the function directly
        if not self.config.enabled:
            return await func(*args, **kwargs)
            
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} HALF_OPEN limit exceeded")
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.config.recovery_timeout_seconds
    
    async def _on_success(self):
        """Handle successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed operation"""
        if not any(isinstance(exception, exc_type) for exc_type in self.config.expected_exceptions):
            return  # Don't count unexpected exceptions
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} OPENED from HALF_OPEN")
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} OPENED due to failure threshold")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "half_open_calls": self.half_open_calls
        }


class RetryPattern:
    """Retry pattern with exponential backoff and jitter"""
    
    def __init__(self, name: str, config: RetryConfig):
        self.name = name
        self.config = config
        self.logger = get_logger(f"{__name__}.retry.{name}")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        # If disabled, just execute the function directly
        if not self.config.enabled:
            return await func(*args, **kwargs)
            
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying {self.name} (attempt {attempt + 1}/{self.config.max_attempts}) after {delay}ms")
                    await asyncio.sleep(delay / 1000.0)
                
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(f"Retry {self.name} succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._is_retryable(e):
                    self.logger.warning(f"Exception {type(e).__name__} is not retryable for {self.name}")
                    raise
                
                if attempt == self.config.max_attempts - 1:
                    self.logger.error(f"Retry {self.name} failed after {self.config.max_attempts} attempts")
                    raise
                
                self.logger.warning(f"Retry {self.name} attempt {attempt + 1} failed: {str(e)}")
        
        # This should never be reached, but just in case
        raise last_exception or Exception("Retry pattern failed with no exception")
    
    def _calculate_delay(self, attempt: int) -> int:
        """Calculate delay for retry attempt"""
        delay = self.config.initial_delay_ms * (self.config.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.config.max_delay_ms)
        
        if self.config.jitter:
            # Add jitter ±25%
            jitter_range = delay * 0.25
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return int(delay)
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)


class TimeoutPattern:
    """Timeout pattern for operations"""
    
    def __init__(self, name: str, config: TimeoutConfig):
        self.name = name
        self.config = config
        self.logger = get_logger(f"{__name__}.timeout.{name}")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with timeout protection"""
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Operation {self.name} timed out after {self.config.timeout_seconds}s")
            if self.config.raise_on_timeout:
                raise TimeoutError(f"Operation {self.name} timed out after {self.config.timeout_seconds}s")
            return None


class BulkheadPattern:
    """Bulkhead pattern for resource isolation"""
    
    def __init__(self, name: str, config: BulkheadConfig):
        self.name = name
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        self.queue = asyncio.Queue(maxsize=config.queue_size)
        self.active_calls = 0
        self.logger = get_logger(f"{__name__}.bulkhead.{name}")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        if self.active_calls >= self.config.max_concurrent_calls:
            if self.queue.full():
                raise BulkheadFullError(f"Bulkhead {self.name} is full")
            
            # Queue the request
            await self.queue.put((func, args, kwargs))
            self.logger.info(f"Queued request for bulkhead {self.name}")
        
        async with self.semaphore:
            self.active_calls += 1
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                self.active_calls -= 1
                
                # Process next queued request if any
                if not self.queue.empty():
                    try:
                        next_func, next_args, next_kwargs = self.queue.get_nowait()
                        asyncio.create_task(self.call(next_func, *next_args, **next_kwargs))
                    except asyncio.QueueEmpty:
                        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        return {
            "name": self.name,
            "active_calls": self.active_calls,
            "queue_size": self.queue.qsize(),
            "max_concurrent_calls": self.config.max_concurrent_calls,
            "max_queue_size": self.config.queue_size
        }


class ResilienceOrchestrator:
    """Orchestrates multiple resilience patterns"""
    
    def __init__(self, name: str):
        self.name = name
        self.patterns: List[Any] = []
        self.logger = get_logger(f"{__name__}.orchestrator.{name}")
    
    def add_circuit_breaker(self, config: CircuitBreakerConfig) -> 'ResilienceOrchestrator':
        """Add circuit breaker pattern"""
        self.patterns.append(CircuitBreaker(self.name, config))
        return self
    
    def add_retry(self, config: RetryConfig) -> 'ResilienceOrchestrator':
        """Add retry pattern"""
        self.patterns.append(RetryPattern(self.name, config))
        return self
    
    def add_timeout(self, config: TimeoutConfig) -> 'ResilienceOrchestrator':
        """Add timeout pattern"""
        self.patterns.append(TimeoutPattern(self.name, config))
        return self
    
    def add_bulkhead(self, config: BulkheadConfig) -> 'ResilienceOrchestrator':
        """Add bulkhead pattern"""
        self.patterns.append(BulkheadPattern(self.name, config))
        return self
    
    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function through all resilience patterns"""
        # Chain the patterns together
        current_func = func
        
        # Apply patterns in reverse order (last added is applied first)
        for pattern in reversed(self.patterns):
            original_func = current_func
            # Create a closure to capture the pattern and original function
            def make_wrapped_func(p, f):
                async def wrapped(*a, **k):
                    return await p.call(f, *a, **k)
                return wrapped
            current_func = make_wrapped_func(pattern, original_func)
        
        return await current_func(*args, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all patterns"""
        status = {"name": self.name, "patterns": []}
        
        for pattern in self.patterns:
            if hasattr(pattern, 'get_state'):
                status["patterns"].append(pattern.get_state())
            elif hasattr(pattern, 'get_stats'):
                status["patterns"].append(pattern.get_stats())
            else:
                status["patterns"].append({"type": type(pattern).__name__, "name": pattern.name})
        
        return status


# Custom exceptions
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class BulkheadFullError(Exception):
    """Raised when bulkhead is full"""
    pass


def create_standard_resilience_orchestrator(name: str) -> ResilienceOrchestrator:
    """Create a standard resilience orchestrator with DISABLED patterns by default"""
    # ALL RESILIENCE PATTERNS DISABLED BY DEFAULT - FAIL FAST
    return (ResilienceOrchestrator(name)
            .add_timeout(TimeoutConfig(timeout_seconds=30.0))
            .add_circuit_breaker(CircuitBreakerConfig(
                enabled=False,  # DISABLED BY DEFAULT
                failure_threshold=1,
                recovery_timeout_seconds=60,
                expected_exceptions=[ConnectionError, TimeoutError]
            ))
            .add_retry(RetryConfig(
                enabled=False,  # DISABLED BY DEFAULT
                max_attempts=1,
                initial_delay_ms=0,
                retryable_exceptions=[ConnectionError, TimeoutError]
            ))
            .add_bulkhead(BulkheadConfig(
                max_concurrent_calls=10,
                queue_size=100
            )))


async def test_resilience_patterns():
    """Test resilience patterns"""
    print("Testing resilience patterns...")
    
    # Test circuit breaker
    print("\n1. Testing circuit breaker:")
    circuit_breaker = CircuitBreaker("test_circuit", CircuitBreakerConfig(failure_threshold=2))
    
    async def failing_operation():
        raise ConnectionError("Connection failed")
    
    # Test failures
    for i in range(3):
        try:
            await circuit_breaker.call(failing_operation)
        except Exception as e:
            print(f"   Attempt {i+1}: {type(e).__name__}: {e}")
    
    print(f"   Circuit breaker state: {circuit_breaker.get_state()}")
    
    # Test retry pattern
    print("\n2. Testing retry pattern:")
    retry = RetryPattern("test_retry", RetryConfig(max_attempts=3, initial_delay_ms=100))
    
    attempt_count = 0
    async def eventually_succeeds():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"Attempt {attempt_count} failed")
        return f"Success on attempt {attempt_count}"
    
    try:
        result = await retry.call(eventually_succeeds)
        print(f"   Retry result: {result}")
    except Exception as e:
        print(f"   Retry failed: {e}")
    
    # Test timeout pattern
    print("\n3. Testing timeout pattern:")
    timeout = TimeoutPattern("test_timeout", TimeoutConfig(timeout_seconds=0.1))
    
    async def slow_operation():
        await asyncio.sleep(0.2)
        return "This should timeout"
    
    try:
        result = await timeout.call(slow_operation)
        print(f"   Timeout result: {result}")
    except Exception as e:
        print(f"   Timeout caught: {type(e).__name__}: {e}")
    
    # Test orchestrator
    print("\n4. Testing resilience orchestrator:")
    orchestrator = create_standard_resilience_orchestrator("test_orchestrator")
    
    async def test_operation():
        return "Operation successful"
    
    try:
        result = await orchestrator.execute(test_operation)
        print(f"   Orchestrator result: {result}")
    except Exception as e:
        print(f"   Orchestrator failed: {e}")
    
    print(f"   Orchestrator status: {orchestrator.get_status()}")
    
    print("\n✅ All resilience pattern tests completed")


if __name__ == "__main__":
    asyncio.run(test_resilience_patterns())