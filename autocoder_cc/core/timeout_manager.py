#!/usr/bin/env python3
"""
Timeout Manager - Centralized request-level timeout management
Implements Phase 2B: Standardized timeout handling across all LLM providers
"""

import asyncio
import time
import threading
from typing import Dict, Optional, Any, Callable, Awaitable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from autocoder_cc.observability import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

class TimeoutType(Enum):
    """Different types of operations with different timeout requirements"""
    HEALTH_CHECK = "health_check"
    LLM_GENERATION = "llm_generation" 
    COMPONENT_GENERATION = "component_generation"
    SYSTEM_VALIDATION = "system_validation"
    BLUEPRINT_PROCESSING = "blueprint_processing"
    RESOURCE_ALLOCATION = "resource_allocation"

@dataclass
class TimeoutConfig:
    """Configuration for different timeout types - ALL TIMEOUTS DISABLED"""
    health_check: float = float('inf')          # No timeout
    llm_generation: float = float('inf')       # No timeout  
    component_generation: float = float('inf') # No timeout
    system_validation: float = float('inf')    # No timeout
    blueprint_processing: float = float('inf') # No timeout
    resource_allocation: float = float('inf')   # No timeout
    
    def get_timeout(self, timeout_type: TimeoutType) -> float:
        """Get timeout value for a specific operation type"""
        return getattr(self, timeout_type.value)

@dataclass
class TimeoutContext:
    """Context information for a timeout operation"""
    operation_id: str
    timeout_type: TimeoutType
    timeout_value: float
    start_time: float = field(default_factory=time.time)
    component_name: Optional[str] = None
    system_id: Optional[str] = None
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since operation started"""
        return time.time() - self.start_time
    
    @property
    def remaining_time(self) -> float:
        """Get remaining time before timeout"""
        return max(0.0, self.timeout_value - self.elapsed_time)
    
    @property
    def is_expired(self) -> bool:
        """Check if timeout has been exceeded"""
        # Never expire if timeout is infinite
        if self.timeout_value == float('inf'):
            return False
        return self.elapsed_time >= self.timeout_value

class TimeoutError(Exception):
    """Raised when an operation times out"""
    
    def __init__(self, context: TimeoutContext, message: Optional[str] = None):
        self.context = context
        self.timeout_type = context.timeout_type
        self.elapsed_time = context.elapsed_time
        self.timeout_value = context.timeout_value
        
        if message is None:
            message = (f"Operation '{context.operation_id}' of type '{context.timeout_type.value}' "
                      f"timed out after {self.elapsed_time:.2f}s (limit: {self.timeout_value}s)")
        
        super().__init__(message)

class TimeoutManager:
    """
    Centralized timeout management for all operations
    
    Features:
    - Per-operation-type timeout configuration
    - Request-level timeout tracking
    - Cumulative timeout prevention
    - Timeout context management
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[TimeoutConfig] = None):
        """
        Initialize timeout manager
        
        Args:
            config: Timeout configuration, uses defaults if None
        """
        self.config = config or TimeoutConfig()
        self._active_contexts: Dict[str, TimeoutContext] = {}
        self._lock = threading.RLock()
        self._stats = {
            'operations_started': 0,
            'operations_completed': 0,
            'operations_timed_out': 0,
            'total_time': 0.0
        }
        
        logger.info(f"TimeoutManager initialized with config: {self.config}")
    
    def create_context(self, 
                      operation_id: str,
                      timeout_type: TimeoutType,
                      component_name: Optional[str] = None,
                      system_id: Optional[str] = None,
                      custom_timeout: Optional[float] = None) -> TimeoutContext:
        """
        Create a new timeout context for an operation
        
        Args:
            operation_id: Unique identifier for the operation
            timeout_type: Type of operation for timeout lookup
            component_name: Optional component name for context
            system_id: Optional system ID for context
            custom_timeout: Optional custom timeout override
            
        Returns:
            TimeoutContext object
        """
        timeout_value = custom_timeout or self.config.get_timeout(timeout_type)
        
        context = TimeoutContext(
            operation_id=operation_id,
            timeout_type=timeout_type,
            timeout_value=timeout_value,
            component_name=component_name,
            system_id=system_id
        )
        
        with self._lock:
            self._active_contexts[operation_id] = context
            self._stats['operations_started'] += 1
        
        logger.debug(f"Created timeout context: {operation_id} ({timeout_type.value}, {timeout_value}s)")
        return context
    
    def complete_operation(self, operation_id: str) -> Optional[TimeoutContext]:
        """
        Mark an operation as completed and remove its context
        
        Args:
            operation_id: ID of the operation to complete
            
        Returns:
            The completed context or None if not found
        """
        with self._lock:
            context = self._active_contexts.pop(operation_id, None)
            if context:
                self._stats['operations_completed'] += 1
                self._stats['total_time'] += context.elapsed_time
                logger.debug(f"Completed operation: {operation_id} in {context.elapsed_time:.2f}s")
            else:
                logger.warning(f"Attempted to complete unknown operation: {operation_id}")
            
            return context
    
    def check_timeout(self, operation_id: str) -> TimeoutContext:
        """
        Check if an operation has timed out
        
        Args:
            operation_id: ID of the operation to check
            
        Returns:
            The timeout context
            
        Raises:
            TimeoutError: If the operation has timed out
            KeyError: If the operation ID is not found
        """
        with self._lock:
            context = self._active_contexts.get(operation_id)
            if context is None:
                raise KeyError(f"Operation '{operation_id}' not found in active contexts")
            
            if context.is_expired:
                self._stats['operations_timed_out'] += 1
                logger.error(f"Operation timed out: {operation_id} after {context.elapsed_time:.2f}s")
                raise TimeoutError(context)
            
            return context
    
    def get_active_operations(self) -> Dict[str, TimeoutContext]:
        """
        Get all currently active operation contexts
        
        Returns:
            Dictionary mapping operation IDs to contexts
        """
        with self._lock:
            return self._active_contexts.copy()
    
    def cleanup_expired_operations(self) -> int:
        """
        Clean up expired operation contexts
        
        Returns:
            Number of expired operations cleaned up
        """
        with self._lock:
            expired_ids = [
                op_id for op_id, context in self._active_contexts.items()
                if context.is_expired
            ]
            
            for op_id in expired_ids:
                context = self._active_contexts.pop(op_id)
                self._stats['operations_timed_out'] += 1
                logger.warning(f"Cleaned up expired operation: {op_id} "
                             f"(expired {context.elapsed_time - context.timeout_value:.2f}s ago)")
            
            return len(expired_ids)
    
    @asynccontextmanager
    async def timeout_context(self,
                             operation_id: str,
                             timeout_type: TimeoutType,
                             component_name: Optional[str] = None,
                             system_id: Optional[str] = None,
                             custom_timeout: Optional[float] = None):
        """
        Async context manager for timeout-controlled operations
        
        Args:
            operation_id: Unique identifier for the operation
            timeout_type: Type of operation for timeout lookup
            component_name: Optional component name for context
            system_id: Optional system ID for context
            custom_timeout: Optional custom timeout override
            
        Usage:
            async with timeout_manager.timeout_context("llm_call_1", TimeoutType.LLM_GENERATION):
                result = await some_llm_operation()
        """
        context = self.create_context(
            operation_id=operation_id,
            timeout_type=timeout_type,
            component_name=component_name,
            system_id=system_id,
            custom_timeout=custom_timeout
        )
        
        try:
            # Python 3.10 compatible implementation
            yield context
                
        except (asyncio.TimeoutError, TimeoutError):
            # Convert asyncio.TimeoutError to our custom TimeoutError
            self._stats['operations_timed_out'] += 1
            logger.error(f"Async operation timed out: {operation_id} after {context.elapsed_time:.2f}s")
            raise TimeoutError(context)
            
        finally:
            self.complete_operation(operation_id)
    
    async def run_with_timeout(self,
                              operation: Callable[[], Awaitable[T]],
                              operation_id: str,
                              timeout_type: TimeoutType,
                              component_name: Optional[str] = None,
                              system_id: Optional[str] = None,
                              custom_timeout: Optional[float] = None) -> T:
        """
        Run an async operation with timeout management
        
        Args:
            operation: Async function to execute
            operation_id: Unique identifier for the operation
            timeout_type: Type of operation for timeout lookup
            component_name: Optional component name for context
            system_id: Optional system ID for context
            custom_timeout: Optional custom timeout override
            
        Returns:
            Result of the operation
            
        Raises:
            TimeoutError: If the operation times out
        """
        context = self.create_context(
            operation_id=operation_id,
            timeout_type=timeout_type,
            component_name=component_name,
            system_id=system_id,
            custom_timeout=custom_timeout
        )
        
        try:
            logger.debug(f"Starting timed operation: {operation_id} "
                        f"({timeout_type.value}, {context.timeout_value}s)")
            
            # If timeout is infinite, run without timeout wrapper
            if context.timeout_value == float('inf'):
                result = await operation()
            else:
                # Use asyncio.wait_for for Python 3.10 compatibility
                result = await asyncio.wait_for(operation(), timeout=context.timeout_value)
            
            logger.debug(f"Completed timed operation: {operation_id} "
                        f"in {context.elapsed_time:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            # Convert asyncio.TimeoutError to our custom TimeoutError
            self._stats['operations_timed_out'] += 1
            logger.error(f"Operation timed out: {operation_id} after {context.elapsed_time:.2f}s")
            raise TimeoutError(context)
            
        finally:
            self.complete_operation(operation_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get timeout management statistics
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            stats = self._stats.copy()
            stats['active_operations'] = len(self._active_contexts)
            
            if stats['operations_completed'] > 0:
                stats['average_operation_time'] = stats['total_time'] / stats['operations_completed']
            else:
                stats['average_operation_time'] = 0.0
            
            if stats['operations_started'] > 0:
                stats['timeout_rate'] = stats['operations_timed_out'] / stats['operations_started']
            else:
                stats['timeout_rate'] = 0.0
            
            return stats
    
    def update_config(self, new_config: TimeoutConfig) -> None:
        """
        Update timeout configuration
        
        Args:
            new_config: New timeout configuration
        """
        with self._lock:
            old_config = self.config
            self.config = new_config
            logger.info(f"Updated timeout configuration from {old_config} to {new_config}")
    
    def __str__(self) -> str:
        """String representation of timeout manager status"""
        stats = self.get_statistics()
        return (f"TimeoutManager(active={stats['active_operations']}, "
               f"completed={stats['operations_completed']}, "
               f"timed_out={stats['operations_timed_out']}, "
               f"timeout_rate={stats['timeout_rate']:.2%})")


# Global timeout manager instance
_timeout_manager: Optional[TimeoutManager] = None
_manager_lock = threading.Lock()

def get_timeout_manager() -> TimeoutManager:
    """
    Get global timeout manager instance (singleton pattern)
    
    Returns:
        Global TimeoutManager instance
    """
    global _timeout_manager
    
    if _timeout_manager is None:
        with _manager_lock:
            if _timeout_manager is None:
                _timeout_manager = TimeoutManager()
                logger.info("Global TimeoutManager instance created")
    
    return _timeout_manager

def reset_timeout_manager() -> None:
    """
    Reset global timeout manager (primarily for testing)
    """
    global _timeout_manager
    
    with _manager_lock:
        _timeout_manager = None
        logger.info("Global TimeoutManager instance reset")