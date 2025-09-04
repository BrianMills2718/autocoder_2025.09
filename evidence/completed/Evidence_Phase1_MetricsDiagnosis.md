# Evidence: Phase 1 - Metrics API Diagnosis

**Date**: 2025-08-26 15:15  
**Task**: Diagnose why sink components fail with AttributeError

## Finding: record_gauge Method Missing

### What the generated sink calls:
```python
# From test_diagnostic/scaffolds/hello_world_api_system/components/hello_world_log_sink.py:44
self.metrics_collector.record_gauge("last_item_processed_timestamp", time.time(), tags={"component": self.name})
```

### What MetricsCollector actually has:
```python
# From autocoder_cc/observability/metrics.py
def counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):  # Line 292
def gauge(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):  # Line 307
def histogram(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):  # Line 327
# NO record_gauge method exists!
```

### Other record_* methods that DO exist:
- record_component_start() - Line 355
- record_component_stop() - Line 360
- record_items_processed() - Line 365
- record_processing_time() - Line 369
- record_error() - Line 373
- record_system_generated() - Line 377
- record_generation_time() - Line 381
- record_health_status() - Line 385
- record_memory_usage() - Line 391
- record_cpu_usage() - Line 395
- record_queue_size() - Line 399
- record_active_connections() - Line 403
- record_business_event() - Line 408
- record_user_action() - Line 412
- record_api_request() - Line 416

## Root Cause
The generated code expects `record_gauge()` but MetricsCollector only provides `gauge()`. This is a naming mismatch - the generator is using a `record_*` prefix pattern for gauge metrics when it should use the plain `gauge()` method.

## Solution
Add a `record_gauge()` method to MetricsCollector that wraps the existing `gauge()` method for backward compatibility.