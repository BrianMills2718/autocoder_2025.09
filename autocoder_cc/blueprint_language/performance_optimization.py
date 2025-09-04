#!/usr/bin/env python3
"""
Performance Optimization - P0.8-E1 Performance Optimization Implementation

Implements generation speed and quality improvements for enhanced component generation.
"""
import asyncio
import time
import functools
from typing import Dict, Any, List, Optional, Callable, Union, TypeVar, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from collections import deque
from enum import Enum
import hashlib
import pickle

from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer

logger = get_logger(__name__)
T = TypeVar('T')
R = TypeVar('R')


class CacheStrategy(Enum):
    """Caching strategies for performance optimization"""
    NONE = "none"              # No caching
    MEMORY = "memory"          # In-memory caching
    PERSISTENT = "persistent"  # Persistent disk caching
    DISTRIBUTED = "distributed"  # Distributed caching (future)


class ParallelismStrategy(Enum):
    """Parallelism strategies for performance optimization"""
    SEQUENTIAL = "sequential"      # No parallelism
    THREAD_POOL = "thread_pool"    # Thread-based parallelism
    PROCESS_POOL = "process_pool"  # Process-based parallelism
    ASYNC_CONCURRENT = "async_concurrent"  # Async concurrency


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization tracking"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    cache_hit: bool = False
    parallel_workers: int = 1
    items_processed: int = 0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    error_count: int = 0
    
    def complete(self):
        """Mark operation as complete and calculate duration"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "operation_name": self.operation_name,
            "duration_ms": self.duration_ms,
            "cache_hit": self.cache_hit,
            "parallel_workers": self.parallel_workers,
            "items_processed": self.items_processed,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "error_count": self.error_count
        }


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    cache_strategy: CacheStrategy = CacheStrategy.MEMORY
    parallelism_strategy: ParallelismStrategy = ParallelismStrategy.ASYNC_CONCURRENT
    max_workers: int = 4
    cache_size: int = 1000
    cache_ttl_seconds: int = 3600
    enable_metrics: bool = True
    optimize_memory: bool = True
    enable_batching: bool = True
    batch_size: int = 10


class PerformanceCache:
    """High-performance caching system for generation optimization"""
    
    def __init__(self, strategy: CacheStrategy = CacheStrategy.MEMORY, max_size: int = 1000, ttl_seconds: int = 3600):
        self.strategy = strategy
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self.metrics_collector = get_metrics_collector("performance_cache")
        
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function name and arguments"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else {}
        }
        key_str = pickle.dumps(key_data, protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.sha256(key_str).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self._memory_cache:
                value, timestamp = self._memory_cache[key]
                
                # Check TTL
                if time.time() - timestamp < self.ttl_seconds:
                    # Update access order
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    
                    self.metrics_collector.record_business_event("cache_hit", 1)
                    return value
                else:
                    # Expired
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
            
            self.metrics_collector.record_business_event("cache_miss", 1)
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self._lock:
            current_time = time.time()
            
            # Evict oldest if at capacity
            if len(self._memory_cache) >= self.max_size and key not in self._memory_cache:
                if self._access_order:
                    oldest_key = self._access_order.popleft()
                    self._memory_cache.pop(oldest_key, None)
            
            self._memory_cache[key] = (value, current_time)
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self.metrics_collector.record_business_event("cache_set", 1)
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._memory_cache.clear()
            self._access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._memory_cache),
                "max_size": self.max_size,
                "strategy": self.strategy.value,
                "ttl_seconds": self.ttl_seconds
            }


class PerformanceOptimizer:
    """Core performance optimizer for component generation"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.cache = PerformanceCache(
            self.config.cache_strategy,
            self.config.cache_size,
            self.config.cache_ttl_seconds
        )
        self.metrics_collector = get_metrics_collector("performance_optimizer")
        self.tracer = get_tracer("performance_optimizer")
        
        # Thread/Process pools for parallel execution
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
        
        # Performance metrics collection
        self._active_metrics: Dict[str, PerformanceMetrics] = {}
        self._completed_metrics: deque = deque(maxlen=1000)
        
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize thread and process pools"""
        if self.config.parallelism_strategy == ParallelismStrategy.THREAD_POOL:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        elif self.config.parallelism_strategy == ParallelismStrategy.PROCESS_POOL:
            self._process_pool = ProcessPoolExecutor(max_workers=self.config.max_workers)
    
    def cached(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to add caching to functions"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.config.cache_strategy == CacheStrategy.NONE:
                return func(*args, **kwargs)
            
            cache_key = self.cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    def async_cached(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to add caching to async functions"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.config.cache_strategy == CacheStrategy.NONE:
                return await func(*args, **kwargs)
            
            cache_key = self.cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            self.cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    def performance_monitored(self, operation_name: str = None):
        """Decorator to monitor function performance"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = operation_name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metrics = self._start_performance_tracking(op_name)
                
                try:
                    result = func(*args, **kwargs)
                    metrics.items_processed = 1
                    return result
                except Exception as e:
                    metrics.error_count += 1
                    raise
                finally:
                    self._end_performance_tracking(metrics)
            
            return wrapper
        return decorator
    
    def async_performance_monitored(self, operation_name: str = None):
        """Decorator to monitor async function performance"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = operation_name or func.__name__
            
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                metrics = self._start_performance_tracking(op_name)
                
                try:
                    result = await func(*args, **kwargs)
                    metrics.items_processed = 1
                    return result
                except Exception as e:
                    metrics.error_count += 1
                    raise
                finally:
                    self._end_performance_tracking(metrics)
            
            return wrapper
        return decorator
    
    def _start_performance_tracking(self, operation_name: str) -> PerformanceMetrics:
        """Start tracking performance for an operation"""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time()
        )
        
        metrics_id = f"{operation_name}_{id(metrics)}"
        self._active_metrics[metrics_id] = metrics
        
        return metrics
    
    def _end_performance_tracking(self, metrics: PerformanceMetrics):
        """End tracking performance for an operation"""
        metrics.complete()
        
        # Remove from active metrics
        metrics_id = None
        for mid, m in self._active_metrics.items():
            if m is metrics:
                metrics_id = mid
                break
        
        if metrics_id:
            del self._active_metrics[metrics_id]
        
        # Add to completed metrics
        self._completed_metrics.append(metrics)
        
        # Record in metrics collector
        if self.config.enable_metrics:
            self.metrics_collector.record_processing_time(metrics.duration_ms)
            if metrics.error_count > 0:
                self.metrics_collector.record_error("performance_tracked_error")
    
    async def parallel_execute(self, tasks: List[Callable], strategy: ParallelismStrategy = None) -> List[Any]:
        """Execute multiple tasks in parallel"""
        strategy = strategy or self.config.parallelism_strategy
        
        with self.tracer.span("parallel_execute") as span_id:
            if strategy == ParallelismStrategy.SEQUENTIAL:
                results = []
                for task in tasks:
                    if asyncio.iscoroutinefunction(task):
                        result = await task()
                    else:
                        result = task()
                    results.append(result)
                return results
            
            elif strategy == ParallelismStrategy.ASYNC_CONCURRENT:
                # Execute async tasks concurrently
                async_tasks = []
                for task in tasks:
                    if asyncio.iscoroutinefunction(task):
                        async_tasks.append(task())
                    else:
                        # Wrap sync function in async
                        async def async_wrapper():
                            return task()
                        async_tasks.append(async_wrapper())
                
                return await asyncio.gather(*async_tasks, return_exceptions=True)
            
            elif strategy == ParallelismStrategy.THREAD_POOL:
                if not self._thread_pool:
                    self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
                
                loop = asyncio.get_event_loop()
                futures = []
                
                for task in tasks:
                    if asyncio.iscoroutinefunction(task):
                        # Can't execute async functions in thread pool directly
                        # Convert to sync or skip
                        continue
                    else:
                        future = loop.run_in_executor(self._thread_pool, task)
                        futures.append(future)
                
                return await asyncio.gather(*futures, return_exceptions=True)
            
            else:
                # Default to async concurrent
                return await self.parallel_execute(tasks, ParallelismStrategy.ASYNC_CONCURRENT)
    
    async def batch_process(self, items: List[Any], processor: Callable[[List[Any]], List[Any]]) -> List[Any]:
        """Process items in batches for better performance"""
        if not self.config.enable_batching:
            # Process individually
            results = []
            for item in items:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor([item])
                else:
                    result = processor([item])
                results.extend(result)
            return results
        
        batch_size = self.config.batch_size
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        with self.tracer.span("batch_process") as span_id:
            batch_tasks = []
            for batch in batches:
                if asyncio.iscoroutinefunction(processor):
                    batch_tasks.append(processor(batch))
                else:
                    async def async_batch_processor():
                        return processor(batch)
                    batch_tasks.append(async_batch_processor())
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Flatten results
            all_results = []
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    logger.error(f"Batch processing error: {batch_result}")
                    continue
                if isinstance(batch_result, list):
                    all_results.extend(batch_result)
                else:
                    all_results.append(batch_result)
            
            return all_results
    
    def optimize_memory_usage(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to optimize memory usage"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.config.optimize_memory:
                return func(*args, **kwargs)
            
            # Force garbage collection before execution
            import gc
            gc.collect()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Force garbage collection after execution
                gc.collect()
        
        return wrapper
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance optimization summary"""
        # Calculate averages from completed metrics
        if not self._completed_metrics:
            return {
                "total_operations": 0,
                "cache_stats": self.cache.get_stats()
            }
        
        total_operations = len(self._completed_metrics)
        total_duration = sum(m.duration_ms for m in self._completed_metrics if m.duration_ms)
        avg_duration = total_duration / total_operations if total_operations > 0 else 0
        
        cache_hits = sum(1 for m in self._completed_metrics if m.cache_hit)
        cache_hit_rate = cache_hits / total_operations if total_operations > 0 else 0
        
        total_errors = sum(m.error_count for m in self._completed_metrics)
        error_rate = total_errors / total_operations if total_operations > 0 else 0
        
        return {
            "total_operations": total_operations,
            "avg_duration_ms": avg_duration,
            "cache_hit_rate": cache_hit_rate,
            "error_rate": error_rate,
            "total_errors": total_errors,
            "cache_stats": self.cache.get_stats(),
            "config": {
                "cache_strategy": self.config.cache_strategy.value,
                "parallelism_strategy": self.config.parallelism_strategy.value,
                "max_workers": self.config.max_workers,
                "batch_size": self.config.batch_size
            }
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
    
    def shutdown(self):
        """Shutdown performance optimizer and clean up resources"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True)


class OptimizedComponentGenerator:
    """Optimized component generator using performance enhancements"""
    
    def __init__(self, base_generator: Any, performance_config: PerformanceConfig = None):
        self.base_generator = base_generator
        self.optimizer = PerformanceOptimizer(performance_config)
        self.tracer = get_tracer("optimized_component_generator")
        
        # Apply optimizations to base generator methods
        self._optimize_base_generator()
    
    def _optimize_base_generator(self):
        """Apply performance optimizations to base generator"""
        # Cache expensive operations
        if hasattr(self.base_generator, 'generate_component_implementation'):
            original_method = self.base_generator.generate_component_implementation
            self.base_generator.generate_component_implementation = self.optimizer.async_cached(
                self.optimizer.async_performance_monitored("generate_component")(original_method)
            )
        
        if hasattr(self.base_generator, '_build_prompt'):
            original_method = self.base_generator._build_prompt
            self.base_generator._build_prompt = self.optimizer.cached(
                self.optimizer.performance_monitored("build_prompt")(original_method)
            )
        
        if hasattr(self.base_generator, '_validate_response'):
            original_method = self.base_generator._validate_response
            self.base_generator._validate_response = self.optimizer.performance_monitored("validate_response")(original_method)
    
    async def generate_components_batch(self, components: List[Any]) -> List[Any]:
        """Generate multiple components in an optimized batch"""
        with self.tracer.span("generate_components_batch") as span_id:
            async def generate_single(component):
                if hasattr(self.base_generator, 'generate_component_implementation'):
                    return await self.base_generator.generate_component_implementation(component)
                else:
                    return await self.base_generator._generate_component(component)
            
            # Create generation tasks
            generation_tasks = [lambda comp=comp: generate_single(comp) for comp in components]
            
            # Execute in parallel with performance optimization
            results = await self.optimizer.parallel_execute(generation_tasks)
            
            # Filter out exceptions
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_count = len(results) - len(successful_results)
            
            if failed_count > 0:
                logger.warning(f"Component generation batch had {failed_count} failures out of {len(components)} components")
            
            return successful_results
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get optimization performance metrics"""
        return self.optimizer.get_performance_summary()
    
    def clear_cache(self):
        """Clear generation caches"""
        self.optimizer.clear_cache()


# Global performance optimizer instance
global_optimizer = PerformanceOptimizer()


def optimize_performance(config: PerformanceConfig = None):
    """Decorator to apply performance optimizations to functions"""
    optimizer = PerformanceOptimizer(config) if config else global_optimizer
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply caching and performance monitoring
        optimized_func = optimizer.cached(
            optimizer.performance_monitored(func.__name__)(func)
        )
        return optimized_func
    
    return decorator


def async_optimize_performance(config: PerformanceConfig = None):
    """Decorator to apply performance optimizations to async functions"""
    optimizer = PerformanceOptimizer(config) if config else global_optimizer
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply caching and performance monitoring
        optimized_func = optimizer.async_cached(
            optimizer.async_performance_monitored(func.__name__)(func)
        )
        return optimized_func
    
    return decorator


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    return global_optimizer