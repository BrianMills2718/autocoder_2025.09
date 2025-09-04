#!/usr/bin/env python3
"""Circuit Breaker Capability - FAIL-FAST implementation with real functionality"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any
from autocoder_cc.observability.structured_logging import get_logger

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for failure isolation with automatic recovery"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, success_threshold=3, **kwargs):
        # FAIL-FAST: Validate configuration
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive (fail-fast principle)")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive (fail-fast principle)")
        if success_threshold <= 0:
            raise ValueError("success_threshold must be positive (fail-fast principle)")
            
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.logger = get_logger("CircuitBreaker")
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.total_requests = 0
        self.total_failures = 0
    
    async def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker - FAIL-FAST when open"""
        if not callable(operation):
            raise ValueError("operation must be callable (fail-fast principle)")
            
        self.total_requests += 1
        
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.logger.info("Circuit breaker transitioning to HALF_OPEN for testing")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # FAIL-FAST: Circuit is open
                raise RuntimeError("Circuit breaker is OPEN - failing fast to prevent cascade failures")
        
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            # Success - handle state transitions
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.logger.info("Circuit breaker transitioning to CLOSED - service recovered")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset failure count on success
            
            return result
            
        except Exception as e:
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            self.logger.warning(f"Operation failed through circuit breaker: {e}")
            
            # Handle state transitions on failure
            if self.state == CircuitState.HALF_OPEN:
                self.logger.warning("Circuit breaker transitioning to OPEN - service still failing")
                self.state = CircuitState.OPEN
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.logger.warning(f"Circuit breaker OPENING - {self.failure_count} failures exceeded threshold")
                self.state = CircuitState.OPEN
            
            raise
    
    def get_status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate": self.total_failures / max(self.total_requests, 1)
        }
