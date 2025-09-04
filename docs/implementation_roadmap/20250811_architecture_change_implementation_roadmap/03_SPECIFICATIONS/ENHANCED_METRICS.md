# Enhanced Metrics Implementation

*Purpose: Buffer utilization and message age tracking*

## Buffer Utilization Tracking

```python
# File: autocoder_cc/components/ports/counted_stream.py

from typing import Any
import anyio

class BufferStats:
    """Shared buffer statistics"""
    __slots__ = ("depth", "capacity")
    
    def __init__(self, capacity: int):
        self.depth = 0
        self.capacity = capacity

class CountingSendStream:
    """Wrapper that tracks buffer depth on send"""
    
    def __init__(self, inner_send, stats: BufferStats, metrics):
        self._inner_send = inner_send
        self._stats = stats
        self._metrics = metrics
    
    async def send(self, obj: Any):
        await self._inner_send.send(obj)
        self._stats.depth += 1
        # Update buffer utilization gauge
        utilization = self._stats.depth / self._stats.capacity
        self._metrics.buffer_utilization = utilization
    
    async def aclose(self):
        await self._inner_send.aclose()

class CountingReceiveStream:
    """Wrapper that tracks buffer depth on receive"""
    
    def __init__(self, inner_recv, stats: BufferStats, metrics):
        self._inner_recv = inner_recv
        self._stats = stats
        self._metrics = metrics
    
    async def receive(self) -> Any:
        obj = await self._inner_recv.receive()
        if self._stats.depth > 0:
            self._stats.depth -= 1
            # Update buffer utilization gauge
            utilization = self._stats.depth / self._stats.capacity
            self._metrics.buffer_utilization = utilization
        return obj
    
    def statistics(self):
        """Return statistics compatible with anyio streams"""
        return type('Stats', (), {
            'current_buffer_used': self._stats.depth,
            'max_buffer_size': self._stats.capacity
        })()

def create_counted_stream(buffer_size: int, output_metrics, input_metrics):
    """Create streams with buffer tracking"""
    send, recv = anyio.create_memory_object_stream(buffer_size)
    stats = BufferStats(buffer_size)
    
    counting_send = CountingSendStream(send, stats, output_metrics)
    counting_recv = CountingReceiveStream(recv, stats, input_metrics)
    
    return counting_send, counting_recv
```

## Message Age Tracking

```python
# File: autocoder_cc/components/ports/metrics.py (updated)

import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class PortMetrics:
    """Enhanced metrics with buffer utilization and message age"""
    
    def __init__(self, port_name: str):
        self.port_name = port_name
        # Counters
        self.messages_in_total = 0
        self.messages_out_total = 0
        self.messages_dropped_total = 0
        self.errors_total = 0
        # Gauges
        self.queue_depth = 0
        self.buffer_utilization = 0.0  # NEW: 0.0 to 1.0
        # Timing
        self.process_latency_ms_sum = 0.0
        self.process_latency_ms_count = 0
        self.blocked_duration_ms = 0.0
        self.last_activity = time.time()
        # Message age histogram
        self.message_age_ms_sum = 0.0  # NEW
        self.message_age_ms_count = 0  # NEW
        self.message_age_ms_max = 0.0  # NEW
    
    def record_latency(self, latency_ms: float):
        """Track processing latency"""
        self.process_latency_ms_sum += latency_ms
        self.process_latency_ms_count += 1
    
    def observe_message_age(self, age_ms: float):
        """Track message age (event time to processing time)"""
        self.message_age_ms_sum += age_ms
        self.message_age_ms_count += 1
        self.message_age_ms_max = max(self.message_age_ms_max, age_ms)
    
    def get_avg_latency_ms(self) -> float:
        """Calculate average processing latency"""
        if self.process_latency_ms_count == 0:
            return 0.0
        return self.process_latency_ms_sum / self.process_latency_ms_count
    
    def get_avg_message_age_ms(self) -> float:
        """Calculate average message age"""
        if self.message_age_ms_count == 0:
            return 0.0
        return self.message_age_ms_sum / self.message_age_ms_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all metrics as dictionary"""
        return {
            "port_name": self.port_name,
            "messages_in_total": self.messages_in_total,
            "messages_out_total": self.messages_out_total,
            "messages_dropped_total": self.messages_dropped_total,
            "errors_total": self.errors_total,
            "queue_depth": self.queue_depth,
            "buffer_utilization": self.buffer_utilization,  # NEW
            "avg_latency_ms": self.get_avg_latency_ms(),
            "avg_message_age_ms": self.get_avg_message_age_ms(),  # NEW
            "max_message_age_ms": self.message_age_ms_max,  # NEW
            "blocked_duration_ms": self.blocked_duration_ms,
            "last_activity": self.last_activity
        }
```

## Updated Port Implementation with Enhanced Metrics

```python
# File: autocoder_cc/components/ports/base.py (partial update)

from .counted_stream import create_counted_stream
from datetime import datetime, timezone

class InputPort(Port[T]):
    """Enhanced input port with message age tracking"""
    
    async def receive(self) -> Optional[T]:
        """Receive and validate data with age tracking"""
        if not self._connected:
            raise RuntimeError(f"Port {self.name} not connected")
        
        start_time = time.monotonic()
        
        try:
            # Receive from stream
            data = await self._stream.receive()
            
            # Validate
            validated = self.validate(data)
            
            # Track message age if event_time present
            event_time = getattr(validated, "event_time", None)
            if event_time:
                if isinstance(event_time, datetime):
                    if event_time.tzinfo is None:
                        event_time = event_time.replace(tzinfo=timezone.utc)
                    age_ms = (datetime.now(timezone.utc) - event_time).total_seconds() * 1000.0
                    self.metrics.observe_message_age(age_ms)
            
            # Update metrics
            self.metrics.messages_in_total += 1
            if hasattr(self._stream, 'statistics'):
                stats = self._stream.statistics()
                self.metrics.queue_depth = stats.current_buffer_used
                self.metrics.buffer_utilization = stats.current_buffer_used / stats.max_buffer_size
            
            return validated
            
        except anyio.EndOfStream:
            return None
        except Exception as e:
            self.metrics.errors_total += 1
            raise e
        finally:
            duration_ms = (time.monotonic() - start_time) * 1000
            self.metrics.record_latency(duration_ms)
            self.metrics.last_activity = time.time()

def create_connected_ports(
    output_name: str,
    input_name: str,
    schema: Type[BaseModel],
    buffer_size: int = 1024,
    overflow_policy: OverflowPolicy = OverflowPolicy.BLOCK
) -> Tuple[OutputPort, InputPort]:
    """Create pre-connected ports with buffer tracking"""
    # Create ports
    output_port = OutputPort(output_name, schema, buffer_size, overflow_policy)
    input_port = InputPort(input_name, schema, buffer_size)
    
    # Create counted streams with shared buffer stats
    send_stream, receive_stream = create_counted_stream(
        buffer_size, 
        output_port.metrics,
        input_port.metrics
    )
    
    # Connect them
    output_port.connect(send_stream)
    input_port.connect(receive_stream)
    
    return output_port, input_port
```

## Usage Example

```python
# Message with event time
from datetime import datetime, timezone
from pydantic import BaseModel

class TimestampedMessage(BaseModel):
    event_time: datetime
    data: str

# Send message with timestamp
message = TimestampedMessage(
    event_time=datetime.now(timezone.utc),
    data="Hello World"
)
await output_port.send(message)

# Receive and automatically track age
received = await input_port.receive()

# Check metrics
print(f"Buffer utilization: {input_port.metrics.buffer_utilization:.1%}")
print(f"Avg message age: {input_port.metrics.get_avg_message_age_ms():.1f}ms")
print(f"Max message age: {input_port.metrics.message_age_ms_max:.1f}ms")
```

## Ingress Backpressure with HTTP 503

```python
# File: autocoder_cc/components/recipes/api_endpoint.py

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import anyio

class APIEndpoint(Source):
    """HTTP ingress with proper backpressure handling"""
    
    async def handle_request(self, request_data: dict) -> Response:
        """Handle incoming HTTP request with backpressure"""
        try:
            # Get timeout from config (default 2000ms)
            timeout_s = self.config.get("timeout_ms", 2000) / 1000.0
            
            # Try to send with timeout
            with anyio.fail_after(timeout_s):
                await self.output_ports["out_requests"].send(request_data)
            
            # Success - return 202 Accepted
            return JSONResponse(
                {"status": "accepted", "message": "Request queued"},
                status_code=202
            )
            
        except TimeoutError:
            # Backpressure - return 503 with retry hint
            self.metrics.ingress_503_total += 1
            return JSONResponse(
                {"error": "backpressure", "message": "System overloaded, please retry"},
                status_code=503,
                headers={"Retry-After": str(int(timeout_s))}
            )
```

---
*These enhancements provide critical observability for production systems.*