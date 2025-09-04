#!/usr/bin/env python3
"""
Metrics Collector Capability
============================

Provides metrics collection functionality for components.
Used by ComposedComponent via composition.
"""
import time
from typing import Dict, Any, List
from collections import defaultdict, deque


class MetricsCollector:
    """Collects and manages component metrics"""
    
    def __init__(self, component_name: str, max_history: int = 1000):
        self.component_name = component_name
        self.max_history = max_history
        
        # Metrics storage
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(lambda: deque(maxlen=max_history))
        self.last_updated = defaultdict(float)
        
        self.start_time = time.time()
    
    def record(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        tags = tags or {}
        metric_key = self._create_metric_key(metric_name, tags)
        
        # Auto-detect metric type based on name patterns
        if metric_name.endswith('_total') or metric_name.endswith('_count'):
            self.increment_counter(metric_key, value)
        elif metric_name.endswith('_duration') or metric_name.endswith('_time'):
            self.record_histogram(metric_key, value)
        else:
            self.set_gauge(metric_key, value)
    
    def increment_counter(self, metric_name: str, value: float = 1.0):
        """Increment a counter metric"""
        self.counters[metric_name] += value
        self.last_updated[metric_name] = time.time()
    
    def set_gauge(self, metric_name: str, value: float):
        """Set a gauge metric value"""
        self.gauges[metric_name] = value
        self.last_updated[metric_name] = time.time()
    
    def record_histogram(self, metric_name: str, value: float):
        """Record a histogram value"""
        self.histograms[metric_name].append(value)
        self.last_updated[metric_name] = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        metrics = {
            'component': self.component_name,
            'uptime': time.time() - self.start_time,
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {}
        }
        
        # Calculate histogram statistics
        for metric_name, values in self.histograms.items():
            if values:
                metrics['histograms'][metric_name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 50),
                    'p95': self._percentile(values, 95),
                    'p99': self._percentile(values, 99)
                }
        
        return metrics
    
    def get_status(self) -> Dict[str, Any]:
        """Get metrics collector status"""
        return {
            'component': self.component_name,
            'metrics_count': len(self.counters) + len(self.gauges) + len(self.histograms),
            'uptime': time.time() - self.start_time,
            'last_metric_time': max(self.last_updated.values()) if self.last_updated else None
        }
    
    def _create_metric_key(self, metric_name: str, tags: Dict[str, str]) -> str:
        """Create metric key with tags"""
        if not tags:
            return metric_name
        
        tag_string = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric_name}[{tag_string}]"
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.last_updated.clear()
        self.start_time = time.time()