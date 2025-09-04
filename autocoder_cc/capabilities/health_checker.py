from autocoder_cc.observability.structured_logging import get_logger
"""
Health check capability for component monitoring.
Used via composition instead of inheritance.

Phase 2B Enhancement: Now uses centralized timeout management for consistent 2s timeouts.
"""
import asyncio
import time
from typing import Dict, Any, Callable, Optional, List, Awaitable
from enum import Enum
from dataclasses import dataclass

# Phase 2B: Import centralized timeout management
from autocoder_cc.core.timeout_manager import get_timeout_manager, TimeoutType, TimeoutError


class HealthStatus(Enum):
    """Component health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}


class HealthChecker:
    """
    Provides health checking capabilities for components.
    
    Example usage:
        health_checker = HealthChecker()
        health_checker.add_check("database", check_database_connection)
        result = await health_checker.check_health()
    """
    
    def __init__(self, 
                 check_interval: float = 30.0,
                 failure_threshold: int = 3):
        """
        Initialize health checker.
        
        Args:
            check_interval: Seconds between automatic health checks
            failure_threshold: Consecutive failures before marking unhealthy
        """
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        
        self.checks: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self.check_results: Dict[str, HealthCheckResult] = {}
        self.failure_counts: Dict[str, int] = {}
        
        self.logger = get_logger(self.__class__.__name__)
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
    
    def add_check(self, 
                  name: str, 
                  check_func: Callable[[], Awaitable[bool]],
                  critical: bool = True):
        """
        Add a health check function.
        
        Args:
            name: Name of the check
            check_func: Async function that returns True if healthy
            critical: If True, failure affects overall health status
        """
        self.checks[name] = check_func
        self.failure_counts[name] = 0
        self.logger.debug(f"Added health check '{name}' (critical={critical})")
    
    async def check_health(self) -> HealthCheckResult:
        """
        Run all health checks and return overall status.
        
        Returns:
            HealthCheckResult with overall status and individual check details
        """
        check_tasks = []
        check_names = []
        
        # Run all checks concurrently
        for name, check_func in self.checks.items():
            check_names.append(name)
            check_tasks.append(self._run_single_check(name, check_func))
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        all_healthy = True
        any_degraded = False
        details = {}
        
        for name, result in zip(check_names, results):
            if isinstance(result, Exception):
                # Check failed with exception
                self.failure_counts[name] += 1
                details[name] = {
                    "status": "error",
                    "error": str(result),
                    "failure_count": self.failure_counts[name]
                }
                all_healthy = False
            elif result:
                # Check passed
                self.failure_counts[name] = 0
                details[name] = {"status": "healthy"}
            else:
                # Check returned False
                self.failure_counts[name] += 1
                details[name] = {
                    "status": "unhealthy",
                    "failure_count": self.failure_counts[name]
                }
                all_healthy = False
                
                if self.failure_counts[name] < self.failure_threshold:
                    any_degraded = True
        
        # Determine overall status
        if all_healthy:
            status = HealthStatus.HEALTHY
            message = "All health checks passed"
        elif any_degraded:
            status = HealthStatus.DEGRADED
            message = "Some health checks failing but below threshold"
        else:
            status = HealthStatus.UNHEALTHY
            message = "Multiple health checks failed"
        
        result = HealthCheckResult(
            status=status,
            message=message,
            details=details
        )
        
        # Store latest result
        self.check_results["overall"] = result
        
        return result
    
    async def _run_single_check(self, name: str, check_func: Callable) -> bool:
        """
        Run a single health check with centralized timeout management.
        
        Phase 2B Enhancement: Uses centralized timeout manager with 2s timeout
        instead of direct asyncio.wait_for with 10s timeout.
        """
        try:
            # Phase 2B: Use centralized timeout management for health checks
            timeout_manager = get_timeout_manager()
            operation_id = f"health_check_{name}_{int(time.time() * 1000)}"
            
            return await timeout_manager.run_with_timeout(
                operation=check_func,
                operation_id=operation_id,
                timeout_type=TimeoutType.HEALTH_CHECK,  # 2.0s timeout
                component_name=name
            )
            
        except TimeoutError as e:
            self.logger.error(f"Health check '{name}' timed out after {e.elapsed_time:.2f}s (limit: {e.timeout_value}s)")
            return False
        except Exception as e:
            self.logger.error(f"Health check '{name}' failed: {e}")
            raise
    
    async def start_monitoring(self):
        """Start automatic periodic health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Started health monitoring (interval={self.check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop automatic health monitoring."""
        self._running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None
        
        self.logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Background task for periodic health checks."""
        while self._running:
            try:
                result = await self.check_health()
                
                if result.status == HealthStatus.UNHEALTHY:
                    self.logger.error(f"Health check failed: {result.message}")
                elif result.status == HealthStatus.DEGRADED:
                    self.logger.warning(f"Health degraded: {result.message}")
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_latest_result(self) -> Optional[HealthCheckResult]:
        """Get the latest overall health check result."""
        return self.check_results.get("overall")
    
    def reset_failure_counts(self):
        """Reset all failure counters."""
        for name in self.failure_counts:
            self.failure_counts[name] = 0
        self.logger.info("Reset all failure counts")