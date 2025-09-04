# Determinism Testing and Utility Functions

*Purpose: Ensure reproducible behavior and provide utility functions*

## Determinism Smoke Test

```python
# File: tests/port_based/test_determinism.py

import pytest
import random
import anyio
from typing import List, Any

@pytest.mark.asyncio
async def test_determinism_smoke():
    """
    Simple determinism test - same seed should produce same output.
    Catches accidental clock/RNG/map-order flakiness.
    """
    
    async def run_pipeline_once() -> List[Any]:
        """Run pipeline with fixed seed and collect outputs"""
        # Fix all sources of non-determinism
        random.seed(12345)
        
        # Create a simple pipeline
        from autocoder_cc.components.ports import create_connected_ports
        from autocoder_cc.components.primitives import Transformer
        from pydantic import BaseModel
        
        class NumberData(BaseModel):
            value: int
        
        class RandomTransformer(Transformer):
            """Test transformer that uses random numbers"""
            
            def configure_ports(self):
                self.add_input_port("in_numbers", NumberData)
                self.add_output_port("out_numbers", NumberData)
            
            async def transform(self, item: NumberData) -> NumberData:
                # Use random but with fixed seed
                random_add = random.randint(1, 100)
                return NumberData(value=item.value + random_add)
        
        # Create and wire components
        transformer = RandomTransformer()
        out_port, in_port = create_connected_ports("out_test", "in_numbers", NumberData)
        result_out, result_in = create_connected_ports("out_numbers", "in_test", NumberData)
        
        transformer.input_ports["in_numbers"] = in_port
        transformer.output_ports["out_numbers"] = result_out
        
        # Run test
        outputs = []
        
        async def sender():
            for i in range(10):
                await out_port.send(NumberData(value=i))
            await out_port.close()
        
        async def receiver():
            async for item in result_in:
                outputs.append(item.value)
        
        async def processor():
            await transformer.process()
        
        async with anyio.create_task_group() as tg:
            tg.start_soon(sender)
            tg.start_soon(processor)
            tg.start_soon(receiver)
        
        return outputs
    
    # Run twice with same seed
    outputs_a = await run_pipeline_once()
    outputs_b = await run_pipeline_once()
    
    # Should be identical
    assert outputs_a == outputs_b, f"Non-deterministic output: {outputs_a} != {outputs_b}"
    print(f"✅ Determinism test passed: {len(outputs_a)} identical outputs")

@pytest.mark.asyncio
async def test_stable_topological_sort():
    """Ensure component wiring is deterministic"""
    
    def create_system() -> dict:
        """Create a system and return wiring order"""
        components = {
            "component_c": {"depends_on": ["component_a"]},
            "component_a": {"depends_on": []},
            "component_b": {"depends_on": ["component_a"]},
        }
        
        # Sort by name for deterministic ordering
        sorted_components = sorted(components.items(), key=lambda x: x[0])
        return [name for name, _ in sorted_components]
    
    # Create multiple times
    orders = [create_system() for _ in range(10)]
    
    # All should be identical
    first = orders[0]
    for order in orders[1:]:
        assert order == first, f"Non-deterministic ordering: {order} != {first}"
    
    print(f"✅ Topological sort is stable: {first}")
```

## Percentile Calculation Without NumPy

```python
# File: autocoder_cc/utils/stats.py

from typing import List, Union

def percentile(values: List[Union[int, float]], p: float) -> float:
    """
    Calculate percentile without numpy.
    
    Args:
        values: List of numeric values
        p: Percentile (0.0 to 1.0, e.g., 0.95 for p95)
    
    Returns:
        The percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 1:
        return float(sorted_values[0])
    
    # Calculate index
    idx = p * (n - 1)
    lower = int(idx)
    upper = min(lower + 1, n - 1)
    
    # Interpolate if needed
    if lower == upper:
        return float(sorted_values[lower])
    
    weight = idx - lower
    return float(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)

def p50(values: List[Union[int, float]]) -> float:
    """Calculate median (p50)"""
    return percentile(values, 0.50)

def p95(values: List[Union[int, float]]) -> float:
    """Calculate p95"""
    return percentile(values, 0.95)

def p99(values: List[Union[int, float]]) -> float:
    """Calculate p99"""
    return percentile(values, 0.99)

# Simple versions if you prefer no interpolation
def p95_simple(latencies_ms: List[float]) -> float:
    """Simple p95 without interpolation"""
    s = sorted(latencies_ms)
    if not s:
        return 0.0
    idx = int(0.95 * (len(s) - 1))
    return float(s[idx])
```

## Updated Performance Test

```python
# File: tests/performance/benchmark.py

import time
import anyio
from typing import List
from autocoder_cc.utils.stats import p50, p95, p99

@pytest.mark.asyncio
async def test_throughput_and_latency():
    """Test throughput and latency without numpy"""
    from autocoder_cc.components.ports import create_connected_ports
    from pydantic import BaseModel
    
    class DataSchema(BaseModel):
        value: int
        timestamp: float = 0.0
    
    out_port, in_port = create_connected_ports("out_test", "in_test", DataSchema)
    
    count = 10000
    latencies: List[float] = []
    
    # Measure throughput
    start = time.monotonic()
    
    # Send messages with timestamps
    for i in range(count):
        msg = DataSchema(value=i, timestamp=time.monotonic())
        await out_port.send(msg)
    
    # Receive and measure latency
    for _ in range(count):
        msg = await in_port.receive()
        latency_ms = (time.monotonic() - msg.timestamp) * 1000
        latencies.append(latency_ms)
    
    duration = time.monotonic() - start
    throughput = count / duration
    
    # Calculate percentiles without numpy
    median = p50(latencies)
    p95_value = p95(latencies)
    p99_value = p99(latencies)
    
    print(f"Throughput: {throughput:.0f} msg/sec")
    print(f"Latency p50: {median:.2f}ms")
    print(f"Latency p95: {p95_value:.2f}ms")
    print(f"Latency p99: {p99_value:.2f}ms")
    
    # Assert performance targets
    assert throughput >= 1000, f"Throughput {throughput:.0f} < 1000 msg/sec"
    assert p95_value < 50, f"p95 latency {p95_value:.2f}ms > 50ms"
    
    print("✅ Performance targets met!")
```

## Dead Letter Queue Flag (No-Op for v1)

```python
# File: autocoder_cc/components/base.py (addition)

class PortBasedComponent(ABC):
    """Enhanced base class with DLQ flag"""
    
    def __init__(self, 
                 name: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.input_ports: Dict[str, InputPort] = {}
        self.output_ports: Dict[str, OutputPort] = {}
        self._running = False
        
        # DLQ configuration (no-op in v1, ready for v2)
        self.dlq_enabled = self.config.get("dlq_enabled", False)
        self.dlq_path = self.config.get("dlq_path", f"/var/log/autocoder4_cc/dlq/{self.name}.jsonl")
        
        # Configure ports
        self.configure_ports()
        
        # Add DLQ port if enabled (v2 feature)
        if self.dlq_enabled:
            # Ready for v2: self.add_output_port("err_dlq", StandardErrorEnvelope)
            pass  # No-op in v1
```

## Configurable Overflow Timeout

```python
# File: autocoder_cc/components/ports/policies.py (updated)

from enum import Enum
from dataclasses import dataclass

class OverflowPolicy(Enum):
    """Overflow policies with configurable timeout"""
    BLOCK = "block"
    BLOCK_WITH_TIMEOUT = "block_with_timeout"
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"

@dataclass
class OverflowConfig:
    """Configuration for overflow policies"""
    policy: OverflowPolicy = OverflowPolicy.BLOCK
    timeout_ms: int = 2000  # Default 2 seconds
```

## Security: Payload Size Cap

```python
# File: autocoder_cc/errors/envelope.py (updated)

class StandardErrorEnvelope(BaseModel):
    """Enhanced error envelope with size limits"""
    
    # ... existing fields ...
    
    @validator('payload')
    def limit_payload_size(cls, v):
        """Cap payload at 64KB"""
        import json
        serialized = json.dumps(v)
        if len(serialized) > 65536:  # 64KB
            # Truncate and add marker
            return {"truncated": True, "size": len(serialized), "preview": serialized[:1000]}
        return v
    
    @validator('payload')
    def redact_pii(cls, v):
        """Redact fields marked as PII"""
        # Simple PII redaction - enhance as needed
        pii_fields = ['ssn', 'credit_card', 'password', 'token', 'secret']
        
        def redact_dict(d):
            result = {}
            for key, value in d.items():
                if any(pii in key.lower() for pii in pii_fields):
                    result[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    result[key] = redact_dict(value)
                else:
                    result[key] = value
            return result
        
        if isinstance(v, dict):
            return redact_dict(v)
        return v
```

---
*These additions ensure deterministic behavior and provide essential utilities without external dependencies.*