#!/usr/bin/env python3
"""
Aggregator Component - Phase 2 Advanced Component Implementation
Batches and aggregates messages based on configurable size and timeout
"""

import anyio
import inspect
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from .composed_base import ComposedComponent
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Aggregator(ComposedComponent):
    """
    Aggregator component that batches messages based on size and timeout.
    
    Configuration:
    - batch_size: Maximum number of items per batch
    - timeout_seconds: Maximum time to wait before flushing batch
    - aggregation_strategy: How to aggregate items (collect, sum, average, count, concat)
    - flush_on_timeout: Whether to flush incomplete batches on timeout
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # Extract aggregation configuration
        self.batch_size = config.get("batch_size", 10)
        self.timeout_seconds = config.get("timeout_seconds", 30)
        self.aggregation_strategy = config.get("aggregation_strategy", "collect")
        self.flush_on_timeout = config.get("flush_on_timeout", True)
        
        # Validate configuration
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive integer")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive number")
        if self.aggregation_strategy not in ["collect", "sum", "average", "count", "concat", "custom"]:
            raise ValueError(f"Invalid aggregation_strategy: {self.aggregation_strategy}")
        
        # Validate custom aggregation function if strategy is custom
        if self.aggregation_strategy == "custom":
            self.custom_aggregation_func = config.get("custom_aggregation_func")
            if not callable(self.custom_aggregation_func):
                raise ValueError("custom_aggregation_func must be provided and callable for custom strategy")
        
        # Initialize internal state
        self.buffer = []
        self.last_flush_time = time.time()
        self.flush_lock = anyio.Lock()
        self.flush_task = None
        
        # Initialize aggregation statistics
        self.aggregation_stats = {
            "total_items_received": 0,
            "total_batches_produced": 0,
            "items_in_current_batch": 0,
            "timeout_flushes": 0,
            "size_flushes": 0,
            "aggregation_errors": 0,
            "current_batch_age_seconds": 0
        }
        
        # Initialize timeout monitor task to None - will be started on first process_item
        self.flush_task = None
        self._timeout_monitor_started = False
        
        self.structured_logger.info(
            f"Aggregator initialized with batch_size={self.batch_size}, timeout={self.timeout_seconds}s",
            operation="aggregator_init",
            tags={
                "batch_size": self.batch_size,
                "timeout_seconds": self.timeout_seconds,
                "aggregation_strategy": self.aggregation_strategy
            }
        )

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Aggregator component"""
        return [
            ConfigRequirement(
                name="aggregation_function",
                type="str",
                description="Function to use for aggregation",
                required=True,
                options=["sum", "avg", "min", "max", "count", "custom"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="group_by",
                type="list",
                description="Fields to group by",
                required=False,
                default=[],
                semantic_type=ConfigType.LIST
            ),
            ConfigRequirement(
                name="window_size",
                type="int",
                description="Size of aggregation window",
                required=False,
                default=100,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: x > 0
            )
        ]

    
    def _start_timeout_monitor(self):
        """Start the timeout monitoring task"""
        if self.flush_on_timeout and not self._timeout_monitor_started:
            # Task will be started when async context is available
            self._timeout_monitor_started = True
            self.flush_task = None
    
    async def _timeout_monitor(self):
        """Monitor for timeout-based flushing"""
        while True:
            try:
                await anyio.sleep(1)  # Check every second
                
                if self.buffer and await self.should_flush():
                    async with self.flush_lock:
                        if self.buffer:  # Double-check after acquiring lock
                            await self._flush_buffer_internal(reason="timeout")
                
            except anyio.get_cancelled_exc_class():
                break
            except Exception as e:
                self.structured_logger.error(
                    f"Timeout monitor error: {e}",
                    operation="timeout_monitor",
                    error=e
                )
                # Continue monitoring despite errors
    
    async def should_flush(self) -> bool:
        """Check if buffer should be flushed based on size or timeout"""
        # Check size-based flushing
        if len(self.buffer) >= self.batch_size:
            return True
        
        # Check timeout-based flushing
        if self.flush_on_timeout and self.buffer:
            current_time = time.time()
            batch_age = current_time - self.last_flush_time
            if batch_age >= self.timeout_seconds:
                return True
        
        return False
    
    async def aggregate_items(self, items: List[Any]) -> Any:
        """Aggregate items based on configured strategy"""
        if not items:
            if self.aggregation_strategy == "count":
                return 0
            elif self.aggregation_strategy == "average":
                return 0.0
            elif self.aggregation_strategy == "sum":
                return 0
            elif self.aggregation_strategy == "concat":
                return ""
            else:
                return None
        
        try:
            if self.aggregation_strategy == "collect":
                return items
            
            elif self.aggregation_strategy == "sum":
                return await self._aggregate_sum(items)
            
            elif self.aggregation_strategy == "average":
                return await self._aggregate_average(items)
            
            elif self.aggregation_strategy == "count":
                return len(items)
            
            elif self.aggregation_strategy == "concat":
                return await self._aggregate_concat(items)
            
            elif self.aggregation_strategy == "custom":
                return await self._aggregate_custom(items)
            
            else:
                raise ValueError(f"Unknown aggregation strategy: {self.aggregation_strategy}")
        
        except Exception as e:
            self.aggregation_stats["aggregation_errors"] += 1
            self.structured_logger.error(
                f"Aggregation failed: {e}",
                operation="aggregation",
                error=e,
                tags={
                    "strategy": self.aggregation_strategy,
                    "items_count": len(items)
                }
            )
            raise
    
    async def _aggregate_sum(self, items: List[Any]) -> Union[int, float]:
        """Sum aggregation strategy"""
        total = 0
        for item in items:
            if isinstance(item, (int, float)):
                total += item
            elif isinstance(item, dict) and "value" in item:
                total += item["value"]
            elif hasattr(item, 'value'):
                total += item.value
            else:
                # Try to convert to number
                try:
                    total += float(item)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot sum non-numeric item: {item}")
        return total
    
    async def _aggregate_average(self, items: List[Any]) -> float:
        """Average aggregation strategy"""
        if not items:
            return 0.0
        
        total = await self._aggregate_sum(items)
        return total / len(items)
    
    async def _aggregate_concat(self, items: List[Any]) -> str:
        """Concatenation aggregation strategy"""
        result = ""
        for item in items:
            if isinstance(item, str):
                result += item
            elif isinstance(item, dict) and "text" in item:
                result += item["text"]
            elif hasattr(item, 'text'):
                result += item.text
            else:
                result += str(item)
        return result
    
    async def _aggregate_custom(self, items: List[Any]) -> Any:
        """Custom aggregation strategy using user-provided function"""
        if self.custom_aggregation_func:
            if inspect.iscoroutinefunction(self.custom_aggregation_func):
                return await self.custom_aggregation_func(items)
            else:
                return self.custom_aggregation_func(items)
        else:
            raise ValueError("Custom aggregation function not provided")
    
    async def flush_buffer(self) -> Optional[Any]:
        """Flush current buffer and return aggregated result"""
        async with self.flush_lock:
            return await self._flush_buffer_internal(reason="manual")
    
    async def _flush_buffer_internal(self, reason: str = "unknown") -> Optional[Any]:
        """Internal flush buffer implementation (must be called with lock held)"""
        if not self.buffer:
            return None
        
        try:
            # Aggregate items
            aggregated_result = await self.aggregate_items(self.buffer)
            
            # Create result with metadata
            result = {
                "aggregated_data": aggregated_result,
                "batch_size": len(self.buffer),
                "aggregation_strategy": self.aggregation_strategy,
                "flush_reason": reason,
                "batch_timestamp": time.time(),
                "aggregator_name": self.name
            }
            
            # Update statistics
            self.aggregation_stats["total_batches_produced"] += 1
            if reason == "timeout":
                self.aggregation_stats["timeout_flushes"] += 1
            elif reason == "size":
                self.aggregation_stats["size_flushes"] += 1
            
            # Clear buffer and reset timing
            buffer_size = len(self.buffer)
            self.buffer = []
            self.last_flush_time = time.time()
            self.aggregation_stats["items_in_current_batch"] = 0
            
            self.structured_logger.info(
                f"Buffer flushed: {buffer_size} items aggregated",
                operation="buffer_flush",
                tags={
                    "batch_size": buffer_size,
                    "flush_reason": reason,
                    "aggregation_strategy": self.aggregation_strategy
                }
            )
            
            return result
        
        except Exception as e:
            # Don't increment error count here if it was already incremented in aggregate_items
            self.structured_logger.error(
                f"Buffer flush failed: {e}",
                operation="buffer_flush",
                error=e,
                tags={
                    "buffer_size": len(self.buffer),
                    "flush_reason": reason
                }
            )
            raise
    
    async def process_item(self, item: Any) -> Optional[Any]:
        """Process item through aggregator"""
        try:
            # Start timeout monitor if not already started
            if not self._timeout_monitor_started:
                self._start_timeout_monitor()
            
            # Validate input
            if item is None:
                self.structured_logger.warning(
                    "Received None item, skipping",
                    operation="item_processing"
                )
                return None
            
            # Update statistics
            self.aggregation_stats["total_items_received"] += 1
            
            # Add item to buffer
            async with self.flush_lock:
                self.buffer.append(item)
                self.aggregation_stats["items_in_current_batch"] = len(self.buffer)
                
                # Update batch age
                current_time = time.time()
                self.aggregation_stats["current_batch_age_seconds"] = current_time - self.last_flush_time
                
                # Check if we should flush due to size
                if len(self.buffer) >= self.batch_size:
                    result = await self._flush_buffer_internal(reason="size")
                    
                    # Record successful processing
                    self.metrics_collector.record_items_processed()
                    
                    self.structured_logger.debug(
                        f"Item processed and batch flushed due to size",
                        operation="item_processing",
                        tags={
                            "batch_size": self.batch_size,
                            "flush_reason": "size"
                        }
                    )
                    
                    return result
                
                # Item buffered, no flush needed yet
                self.structured_logger.debug(
                    f"Item buffered ({len(self.buffer)}/{self.batch_size})",
                    operation="item_processing",
                    tags={
                        "buffer_size": len(self.buffer),
                        "batch_size": self.batch_size
                    }
                )
                
                return None  # No output yet, still buffering
        
        except Exception as e:
            # Don't increment error count here if it was already incremented in aggregate_items
            self.metrics_collector.record_error(e.__class__.__name__)
            
            self.structured_logger.error(
                f"Item processing failed: {e}",
                operation="item_processing",
                error=e,
                tags={"item": str(item)}
            )
            
            # Re-raise to allow error handling upstream
            raise
    
    async def finalize(self) -> Optional[Any]:
        """Finalize aggregator and flush any remaining items"""
        # Cancel timeout monitor
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()
            try:
                await self.flush_task
            except anyio.get_cancelled_exc_class():
                pass
        
        # Flush any remaining items
        result = await self.flush_buffer()
        
        self.structured_logger.info(
            "Aggregator finalized",
            operation="finalization",
            tags={
                "final_buffer_size": len(self.buffer),
                "total_batches_produced": self.aggregation_stats["total_batches_produced"]
            }
        )
        
        return result
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'flush_task') and self.flush_task and not self.flush_task.done():
                self.flush_task.cancel()
        except RuntimeError:
            # Event loop might be closed
            pass
    
    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get aggregation statistics"""
        # Update current batch age
        if self.buffer:
            current_time = time.time()
            self.aggregation_stats["current_batch_age_seconds"] = current_time - self.last_flush_time
        
        return {
            **self.aggregation_stats,
            "batch_size": self.batch_size,
            "timeout_seconds": self.timeout_seconds,
            "aggregation_strategy": self.aggregation_strategy,
            "flush_on_timeout": self.flush_on_timeout
        }
    
    def reset_aggregation_stats(self) -> None:
        """Reset aggregation statistics"""
        self.aggregation_stats = {
            "total_items_received": 0,
            "total_batches_produced": 0,
            "items_in_current_batch": len(self.buffer),
            "timeout_flushes": 0,
            "size_flushes": 0,
            "aggregation_errors": 0,
            "current_batch_age_seconds": 0
        }
        
        self.structured_logger.info(
            "Aggregator statistics reset",
            operation="stats_reset"
        )
    
    @classmethod
    def get_required_config_fields(cls) -> List[str]:
        """Get list of required configuration fields"""
        return []  # All fields have defaults
    
    @classmethod
    def get_required_dependencies(cls) -> List[str]:
        """Get list of required dependencies"""
        return []  # No external dependencies required
    
    async def is_ready(self) -> bool:
        """Check if aggregator is ready to process items"""
        # Aggregator is ready if configuration is valid
        return (
            self.batch_size > 0 and
            self.timeout_seconds > 0 and
            self.aggregation_strategy in ["collect", "sum", "average", "count", "concat", "custom"]
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Aggregator health check"""
        return {
            "status": "healthy",
            "component": "Aggregator",
            "name": self.name,
            "batch_size": self.batch_size,
            "timeout_seconds": self.timeout_seconds,
            "aggregation_strategy": self.aggregation_strategy,
            "flush_on_timeout": self.flush_on_timeout,
            "current_buffer_size": len(self.buffer),
            "timeout_monitor_active": self.flush_task and not self.flush_task.done(),
            "statistics": self.get_aggregation_stats()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - finalize aggregator"""
        await self.finalize()