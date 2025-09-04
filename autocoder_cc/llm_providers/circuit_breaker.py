"""Circuit Breaker Pattern for LLM Provider Health Checks

Implements a circuit breaker to prevent cascading failures when providers
are experiencing issues. This is part of P1.0 Foundation Stabilization.
"""
import time
from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from ..core.config import settings
from ..observability.structured_logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"     # Normal operation, requests allowed
    OPEN = "open"         # Circuit tripped, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Statistics for circuit breaker decisions"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_at: float = field(default_factory=time.time)


class ProviderCircuitBreaker:
    """Circuit breaker for LLM provider health checks
    
    Prevents repeated attempts to unhealthy providers, allowing them
    time to recover before retrying.
    """
    
    def __init__(self):
        self.circuits: Dict[str, CircuitStats] = {}
        self.states: Dict[str, CircuitState] = {}
        self.failure_threshold = settings.CIRCUIT_BREAKER_THRESHOLD
        self.recovery_timeout = settings.CIRCUIT_BREAKER_RECOVERY_TIME
        
    def _get_or_create_circuit(self, provider_name: str) -> CircuitStats:
        """Get or create circuit stats for a provider"""
        if provider_name not in self.circuits:
            self.circuits[provider_name] = CircuitStats()
            self.states[provider_name] = CircuitState.CLOSED
        return self.circuits[provider_name]
    
    def _get_state(self, provider_name: str) -> CircuitState:
        """Get current circuit state"""
        return self.states.get(provider_name, CircuitState.CLOSED)
    
    def _set_state(self, provider_name: str, state: CircuitState):
        """Set circuit state and log transition"""
        old_state = self._get_state(provider_name)
        if old_state != state:
            self.states[provider_name] = state
            stats = self._get_or_create_circuit(provider_name)
            stats.state_changed_at = time.time()
            logger.info(
                f"Circuit breaker state change for {provider_name}: "
                f"{old_state.value} -> {state.value}"
            )
    
    def is_open(self, provider_name: str) -> bool:
        """Check if circuit is open (blocking requests)"""
        state = self._get_state(provider_name)
        
        if state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            stats = self._get_or_create_circuit(provider_name)
            if time.time() - stats.state_changed_at >= self.recovery_timeout:
                # Move to half-open state to test recovery
                self._set_state(provider_name, CircuitState.HALF_OPEN)
                logger.info(f"Circuit breaker moving to HALF_OPEN for {provider_name}")
                return False
            return True
            
        return False
    
    def can_attempt(self, provider_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a request can be attempted
        
        Returns:
            (allowed, reason) - whether request is allowed and reason if blocked
        """
        state = self._get_state(provider_name)
        
        if state == CircuitState.OPEN:
            stats = self._get_or_create_circuit(provider_name)
            time_until_recovery = self.recovery_timeout - (time.time() - stats.state_changed_at)
            
            if time_until_recovery > 0:
                return False, f"Circuit open, recovery in {int(time_until_recovery)}s"
            else:
                # Move to half-open for testing
                self._set_state(provider_name, CircuitState.HALF_OPEN)
                return True, None
                
        return True, None
    
    def record_success(self, provider_name: str):
        """Record a successful health check"""
        stats = self._get_or_create_circuit(provider_name)
        stats.success_count += 1
        stats.last_success_time = time.time()
        
        state = self._get_state(provider_name)
        
        if state == CircuitState.HALF_OPEN:
            # Success in half-open state closes the circuit
            stats.failure_count = 0  # Reset failure count
            self._set_state(provider_name, CircuitState.CLOSED)
            logger.info(f"Circuit breaker closed for {provider_name} after successful test")
        elif state == CircuitState.OPEN:
            # This shouldn't happen, but handle it
            logger.warning(f"Success recorded while circuit open for {provider_name}")
    
    def record_failure(self, provider_name: str, error: Optional[Exception] = None):
        """Record a failed health check"""
        stats = self._get_or_create_circuit(provider_name)
        stats.failure_count += 1
        stats.last_failure_time = time.time()
        
        state = self._get_state(provider_name)
        
        if state == CircuitState.HALF_OPEN:
            # Failure in half-open state reopens the circuit
            self._set_state(provider_name, CircuitState.OPEN)
            logger.warning(
                f"Circuit breaker reopened for {provider_name} after test failure"
                f"{f': {error}' if error else ''}"
            )
        elif state == CircuitState.CLOSED:
            # Check if we've hit the failure threshold
            if stats.failure_count >= self.failure_threshold:
                self._set_state(provider_name, CircuitState.OPEN)
                logger.error(
                    f"Circuit breaker opened for {provider_name} after "
                    f"{stats.failure_count} failures"
                    f"{f'. Last error: {error}' if error else ''}"
                )
    
    def get_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all circuits for monitoring"""
        status = {}
        for provider_name in self.circuits:
            stats = self.circuits[provider_name]
            state = self._get_state(provider_name)
            
            status[provider_name] = {
                "state": state.value,
                "failure_count": stats.failure_count,
                "success_count": stats.success_count,
                "last_failure": stats.last_failure_time,
                "last_success": stats.last_success_time,
                "state_changed_at": stats.state_changed_at,
                "time_in_state": time.time() - stats.state_changed_at
            }
            
        return status
    
    def reset(self, provider_name: Optional[str] = None):
        """Reset circuit breaker state
        
        Args:
            provider_name: Specific provider to reset, or None for all
        """
        if provider_name:
            if provider_name in self.circuits:
                del self.circuits[provider_name]
            if provider_name in self.states:
                del self.states[provider_name]
            logger.info(f"Circuit breaker reset for {provider_name}")
        else:
            self.circuits.clear()
            self.states.clear()
            logger.info("All circuit breakers reset")


# Global circuit breaker instance
_circuit_breaker: Optional[ProviderCircuitBreaker] = None


def get_circuit_breaker() -> ProviderCircuitBreaker:
    """Get the global circuit breaker instance"""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = ProviderCircuitBreaker()
    return _circuit_breaker