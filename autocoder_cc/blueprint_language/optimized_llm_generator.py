#!/usr/bin/env python3
"""
Optimized LLM Component Generator - P0.8-E1 Performance Integration

Integrates performance optimizations with the existing LLM component generator.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from .llm_component_generator import LLMComponentGenerator, ComponentGenerationError
from .performance_optimization import (
    PerformanceOptimizer, PerformanceConfig, OptimizedComponentGenerator,
    CacheStrategy, ParallelismStrategy, async_optimize_performance
)
from .system_blueprint_parser import ParsedComponent, ParsedSystemBlueprint
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer

logger = get_logger(__name__)


@dataclass
class GenerationPerformanceMetrics:
    """Performance metrics specific to component generation"""
    total_components: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    cache_hits: int = 0
    total_generation_time_ms: float = 0
    avg_generation_time_ms: float = 0
    parallel_batches: int = 0
    optimization_enabled: bool = True


class OptimizedLLMComponentGenerator:
    """Performance-optimized wrapper for LLM component generator"""
    
    def __init__(self, 
                 base_generator: LLMComponentGenerator = None,
                 performance_config: PerformanceConfig = None):
        # Initialize base generator
        self.base_generator = base_generator or LLMComponentGenerator()
        
        # Default performance configuration optimized for LLM generation
        default_config = PerformanceConfig(
            cache_strategy=CacheStrategy.MEMORY,
            parallelism_strategy=ParallelismStrategy.ASYNC_CONCURRENT,
            max_workers=3,  # Conservative for LLM API limits
            cache_size=500,
            cache_ttl_seconds=1800,  # 30 minutes
            enable_metrics=True,
            optimize_memory=True,
            enable_batching=True,
            batch_size=5  # Batch size for LLM requests
        )
        
        self.config = performance_config or default_config
        self.optimizer = PerformanceOptimizer(self.config)
        self.metrics = GenerationPerformanceMetrics(optimization_enabled=True)
        
        self.metrics_collector = get_metrics_collector("optimized_llm_generator")
        self.tracer = get_tracer("optimized_llm_generator")
        
        # Apply optimizations to critical methods
        self._apply_optimizations()
    
    def _apply_optimizations(self):
        """Apply performance optimizations to LLM generator methods"""
        # Cache component generation (expensive LLM calls)
        if hasattr(self.base_generator, 'generate_component_implementation'):
            original_method = self.base_generator.generate_component_implementation
            self.base_generator.generate_component_implementation = self._create_optimized_generation_method(original_method)
        
        # Cache prompt building (computational overhead)
        if hasattr(self.base_generator, '_build_prompt'):
            original_method = self.base_generator._build_prompt
            self.base_generator._build_prompt = self.optimizer.cached(original_method)
        
        # Cache validation (regex and parsing overhead)
        if hasattr(self.base_generator, '_validate_response'):
            original_method = self.base_generator._validate_response
            self.base_generator._validate_response = self.optimizer.cached(original_method)
        
        # Cache template selection
        if hasattr(self.base_generator, '_select_template'):
            original_method = self.base_generator._select_template
            self.base_generator._select_template = self.optimizer.cached(original_method)
    
    def _create_optimized_generation_method(self, original_method):
        """Create optimized version of component generation method"""
        @self.optimizer.async_cached
        @self.optimizer.async_performance_monitored("llm_component_generation")
        async def optimized_generation(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await original_method(*args, **kwargs)
                
                # Update success metrics
                self.metrics.successful_generations += 1
                
                # Check if result came from cache
                cache_key = self.optimizer.cache._generate_key(original_method.__name__, *args, **kwargs)
                if self.optimizer.cache.get(cache_key) is not None:
                    self.metrics.cache_hits += 1
                
                return result
                
            except Exception as e:
                self.metrics.failed_generations += 1
                logger.error(f"Optimized LLM generation failed: {e}")
                raise
            
            finally:
                generation_time = (time.time() - start_time) * 1000
                self.metrics.total_generation_time_ms += generation_time
                self.metrics.total_components += 1
                
                if self.metrics.total_components > 0:
                    self.metrics.avg_generation_time_ms = (
                        self.metrics.total_generation_time_ms / self.metrics.total_components
                    )
                
                # Record metrics
                self.metrics_collector.record_processing_time(generation_time)
        
        return optimized_generation
    
    async def generate_component_implementation_enhanced(self, 
                                                       component: ParsedComponent,
                                                       system_blueprint: ParsedSystemBlueprint = None,
                                                       context: Dict[str, Any] = None) -> str:
        """Enhanced component generation with performance optimizations"""
        with self.tracer.span("generate_component_enhanced") as span_id:
            # Use optimized generation method
            if hasattr(self.base_generator, 'generate_component_implementation_enhanced'):
                return await self.base_generator.generate_component_implementation_enhanced(
                    component, system_blueprint, context
                )
            elif hasattr(self.base_generator, 'generate_component_implementation'):
                return await self.base_generator.generate_component_implementation(component)
            else:
                raise ComponentGenerationError("No suitable generation method found in base generator")
    
    async def generate_components_batch_optimized(self, 
                                                components: List[ParsedComponent],
                                                system_blueprint: ParsedSystemBlueprint = None,
                                                context: Dict[str, Any] = None) -> List[str]:
        """Generate multiple components with batch optimization"""
        with self.tracer.span("generate_components_batch") as span_id:
            if not components:
                return []
            
            start_time = time.time()
            
            try:
                # Create generation tasks
                generation_tasks = []
                for component in components:
                    async def generate_component_task(comp=component):
                        return await self.generate_component_implementation_enhanced(
                            comp, system_blueprint, context
                        )
                    generation_tasks.append(generate_component_task)
                
                # Execute in parallel batches
                if self.config.enable_batching and len(components) > self.config.batch_size:
                    # Process in batches
                    batches = [
                        generation_tasks[i:i + self.config.batch_size] 
                        for i in range(0, len(generation_tasks), self.config.batch_size)
                    ]
                    
                    all_results = []
                    for batch in batches:
                        batch_results = await self.optimizer.parallel_execute(batch)
                        all_results.extend(batch_results)
                        self.metrics.parallel_batches += 1
                    
                    results = all_results
                else:
                    # Execute all in parallel
                    results = await self.optimizer.parallel_execute(generation_tasks)
                
                # Filter successful results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                failed_count = len(results) - len(successful_results)
                
                if failed_count > 0:
                    logger.warning(f"Batch generation had {failed_count} failures out of {len(components)} components")
                
                return successful_results
                
            except Exception as e:
                logger.error(f"Batch component generation failed: {e}")
                raise
            
            finally:
                batch_time = (time.time() - start_time) * 1000
                self.metrics_collector.record_business_event("batch_generation_completed", len(components))
                self.metrics_collector.record_processing_time(batch_time)
    
    async def generate_with_quality_optimization(self,
                                               component: ParsedComponent,
                                               system_blueprint: ParsedSystemBlueprint = None,
                                               context: Dict[str, Any] = None,
                                               max_retries: int = 2) -> str:
        """Generate component with quality optimization through intelligent retries"""
        with self.tracer.span("generate_with_quality_optimization") as span_id:
            best_result = None
            best_quality_score = 0
            
            for attempt in range(max_retries + 1):
                try:
                    # Generate component
                    result = await self.generate_component_implementation_enhanced(
                        component, system_blueprint, context
                    )
                    
                    # Evaluate quality (simple heuristics for now)
                    quality_score = self._evaluate_generation_quality(result, component)
                    
                    # Update best result if this is better
                    if quality_score > best_quality_score:
                        best_result = result
                        best_quality_score = quality_score
                    
                    # If quality is good enough, return early
                    if quality_score >= 0.8:  # 80% quality threshold
                        break
                    
                    # If not the last attempt and quality is poor, try again
                    if attempt < max_retries and quality_score < 0.5:
                        logger.info(f"Generation quality low ({quality_score:.2f}), retrying... (attempt {attempt + 1})")
                        
                        # Clear cache for this specific generation to force new attempt
                        if hasattr(self.base_generator, 'generate_component_implementation'):
                            cache_key = self.optimizer.cache._generate_key(
                                self.base_generator.generate_component_implementation.__name__,
                                component
                            )
                            # Remove from cache to force regeneration
                            if cache_key in self.optimizer.cache._memory_cache:
                                del self.optimizer.cache._memory_cache[cache_key]
                        
                        continue
                
                except Exception as e:
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries:
                        raise
                    continue
            
            if best_result is None:
                raise ComponentGenerationError("All generation attempts failed")
            
            logger.info(f"Final generation quality score: {best_quality_score:.2f}")
            return best_result
    
    def _evaluate_generation_quality(self, generated_code: str, component: ParsedComponent) -> float:
        """Evaluate the quality of generated code (simple heuristic)"""
        quality_score = 0.0
        
        # Basic code structure checks
        if "class " in generated_code:
            quality_score += 0.2
        
        if "def " in generated_code:
            quality_score += 0.2
        
        if "async def" in generated_code:
            quality_score += 0.1
        
        # Component-specific checks
        component_name = component.name.lower()
        if component_name in generated_code.lower():
            quality_score += 0.1
        
        # Check for imports
        if "import " in generated_code:
            quality_score += 0.1
        
        # Check for docstrings
        if '"""' in generated_code or "'''" in generated_code:
            quality_score += 0.1
        
        # Check for error handling
        if "try:" in generated_code or "except " in generated_code:
            quality_score += 0.1
        
        # Code length heuristic (not too short, not too long)
        code_lines = len(generated_code.split('\n'))
        if 20 <= code_lines <= 200:
            quality_score += 0.1
        
        return min(quality_score, 1.0)  # Cap at 1.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        base_metrics = self.optimizer.get_performance_summary()
        
        generation_metrics = {
            "total_components": self.metrics.total_components,
            "successful_generations": self.metrics.successful_generations,
            "failed_generations": self.metrics.failed_generations,
            "success_rate": (
                self.metrics.successful_generations / self.metrics.total_components 
                if self.metrics.total_components > 0 else 0
            ),
            "cache_hits": self.metrics.cache_hits,
            "cache_hit_rate": (
                self.metrics.cache_hits / self.metrics.total_components 
                if self.metrics.total_components > 0 else 0
            ),
            "avg_generation_time_ms": self.metrics.avg_generation_time_ms,
            "parallel_batches": self.metrics.parallel_batches,
            "optimization_enabled": self.metrics.optimization_enabled
        }
        
        return {
            "llm_generation_metrics": generation_metrics,
            "base_performance_metrics": base_metrics
        }
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = GenerationPerformanceMetrics(optimization_enabled=True)
        self.optimizer.cache.clear()
    
    def get_cache_efficiency(self) -> Dict[str, Any]:
        """Get cache efficiency statistics"""
        cache_stats = self.optimizer.cache.get_stats()
        
        return {
            "cache_utilization": cache_stats["size"] / cache_stats["max_size"] if cache_stats["max_size"] > 0 else 0,
            "cache_stats": cache_stats,
            "hit_rate": (
                self.metrics.cache_hits / self.metrics.total_components 
                if self.metrics.total_components > 0 else 0
            )
        }
    
    def optimize_for_batch_generation(self):
        """Optimize configuration for batch generation scenarios"""
        self.config.enable_batching = True
        self.config.batch_size = 8
        self.config.parallelism_strategy = ParallelismStrategy.ASYNC_CONCURRENT
        self.config.max_workers = 4
        
        # Reinitialize optimizer with new config
        self.optimizer = PerformanceOptimizer(self.config)
        self._apply_optimizations()
        
        logger.info("Optimized configuration for batch generation")
    
    def optimize_for_single_generation(self):
        """Optimize configuration for single component generation"""
        self.config.enable_batching = False
        self.config.parallelism_strategy = ParallelismStrategy.SEQUENTIAL
        self.config.cache_strategy = CacheStrategy.MEMORY
        
        # Reinitialize optimizer with new config
        self.optimizer = PerformanceOptimizer(self.config)
        self._apply_optimizations()
        
        logger.info("Optimized configuration for single component generation")
    
    def shutdown(self):
        """Shutdown optimizer and clean up resources"""
        self.optimizer.shutdown()


# Factory function for creating optimized generators
def create_optimized_llm_generator(performance_config: PerformanceConfig = None) -> OptimizedLLMComponentGenerator:
    """Create an optimized LLM component generator"""
    return OptimizedLLMComponentGenerator(performance_config=performance_config)


# Default optimized generator instance
default_optimized_generator = OptimizedLLMComponentGenerator()


def get_optimized_llm_generator() -> OptimizedLLMComponentGenerator:
    """Get the default optimized LLM generator"""
    return default_optimized_generator