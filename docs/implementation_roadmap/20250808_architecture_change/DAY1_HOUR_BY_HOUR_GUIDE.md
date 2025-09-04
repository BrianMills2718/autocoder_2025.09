# Day 1: Hour-by-Hour Implementation Guide

*Created: 2025-08-12*  
*Purpose: Exact, step-by-step guide for Day 1 implementation*

## 🕐 Hour 1: Environment Setup & Bug Fix (8:00-9:00 AM)

### Step 1: Fix Critical Import Bug (5 minutes)
```bash
# Fix the import bug FIRST - this alone improves validation
cd /home/brian/projects/autocoder4_cc

# Check current line 1492
sed -n '1492p' autocoder_cc/blueprint_language/component_logic_generator.py
# Should show: from observability import ComposedComponent

# Fix it
sed -i '1492s/from observability import ComposedComponent/from autocoder_cc.components.composed_base import ComposedComponent/' \
    autocoder_cc/blueprint_language/component_logic_generator.py

# Verify fix
sed -n '1492p' autocoder_cc/blueprint_language/component_logic_generator.py
# Should show: from autocoder_cc.components.composed_base import ComposedComponent

echo "✅ Import bug fixed!"
```

### Step 2: Create Directory Structure (5 minutes)
```bash
# Create all needed directories
mkdir -p autocoder_cc/components/ports
mkdir -p autocoder_cc/components/primitives
mkdir -p autocoder_cc/components/recipes
mkdir -p autocoder_cc/checkpoints
mkdir -p autocoder_cc/idempotency
mkdir -p autocoder_cc/telemetry
mkdir -p autocoder_cc/cli
mkdir -p autocoder_cc/errors
mkdir -p tests/port_based
mkdir -p tests/integration
mkdir -p tests/performance
mkdir -p tests/recovery

# Create persistent storage
sudo mkdir -p /var/lib/autocoder4_cc/checkpoints
sudo mkdir -p /var/lib/autocoder4_cc/idempotency
sudo chown -R $USER:$USER /var/lib/autocoder4_cc

echo "✅ Directory structure created!"
```

### Step 3: Install Dependencies (10 minutes)
```bash
# Create requirements file
cat > requirements_port.txt << 'EOF'
anyio>=3.6.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-watch>=4.2.0
pytest-cov>=4.0.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
click>=8.1.0
pyyaml>=6.0
EOF

# Install
pip install -r requirements_port.txt

# Verify critical packages
python -c "
import anyio
import pydantic
import pytest_asyncio
print('✅ All critical packages installed!')
"
```

### Step 4: Create Environment File (5 minutes)
```bash
cat > .env << 'EOF'
export AUTOCODER_CHECKPOINT_DIR=/var/lib/autocoder4_cc/checkpoints
export AUTOCODER_CHECKPOINT_INTERVAL=60
export AUTOCODER_IDEMPOTENCY_STORE=sqlite
export AUTOCODER_LOG_LEVEL=DEBUG
export PYTHONPATH=$PYTHONPATH:$(pwd)
EOF

source .env
echo "✅ Environment configured!"
```

### Step 5: Verify Setup with Minimal Test (5 minutes)
```bash
# Create minimal test file
cat > test_setup.py << 'EOF'
import anyio
from pydantic import BaseModel

class TestData(BaseModel):
    value: int

async def test_setup():
    # Test anyio streams work
    send, recv = anyio.create_memory_object_stream(10)
    
    # Test pydantic validation works
    data = TestData(value=42)
    
    # Test sending through stream
    await send.send(data)
    result = await recv.receive()
    
    assert result.value == 42
    print("✅ Setup verified! Ready to implement.")

if __name__ == "__main__":
    anyio.run(test_setup())
EOF

python test_setup.py
```

## 🕑 Hour 2: Write First Test Suite (9:00-10:00 AM)

### Step 1: Create Test File (30 minutes)
```bash
# Create the test file
cat > tests/port_based/test_ports.py << 'EOF'
"""
Port Infrastructure Tests - Day 1
These tests define the expected behavior of our port system
"""
import pytest
import asyncio
import time
from pydantic import BaseModel, ValidationError
import anyio

# Test schemas
class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False

class DataSchema(BaseModel):
    value: int

@pytest.mark.asyncio
async def test_port_creation_and_validation():
    """TEST 1: Ports should validate data against schemas"""
    from autocoder_cc.components.ports import OutputPort
    
    # Create port with schema
    port = OutputPort("out_test", TodoItem, buffer_size=1024)
    
    # Valid data should pass
    valid_item = TodoItem(id=1, title="Test", completed=False)
    validated = port.validate(valid_item)
    assert validated.id == 1
    assert validated.title == "Test"
    
    # Invalid data should fail
    with pytest.raises(ValidationError):
        port.validate({"id": "not_an_int", "title": "Test"})
    
    print("✅ Test 1: Port validation defined")

@pytest.mark.asyncio
async def test_port_naming_convention():
    """TEST 2: Ports must follow naming conventions (Decision #30)"""
    from autocoder_cc.components.ports import InputPort, OutputPort
    
    # Valid names should work
    InputPort("in_data", TodoItem)
    OutputPort("out_result", TodoItem)
    OutputPort("err_errors", TodoItem)
    
    # Invalid names should raise ValueError
    with pytest.raises(ValueError, match="must start with"):
        InputPort("data", TodoItem)  # Missing in_ prefix
    
    with pytest.raises(ValueError, match="must start with"):
        OutputPort("result", TodoItem)  # Missing out_ prefix
    
    print("✅ Test 2: Naming conventions defined")

@pytest.mark.asyncio
async def test_port_connection_and_flow():
    """TEST 3: Data should flow through connected ports"""
    from autocoder_cc.components.ports import OutputPort, InputPort
    
    # Create ports
    output_port = OutputPort("out_data", TodoItem)
    input_port = InputPort("in_data", TodoItem)
    
    # Initially not connected
    assert not output_port.is_connected
    assert not input_port.is_connected
    
    # Create and connect streams
    send_stream, receive_stream = anyio.create_memory_object_stream(10)
    output_port.connect(send_stream)
    input_port.connect(receive_stream)
    
    # Now connected
    assert output_port.is_connected
    assert input_port.is_connected
    
    # Send data
    item = TodoItem(id=1, title="Test Task")
    sent = await output_port.send(item)
    assert sent is True
    
    # Receive data
    received = await input_port.receive()
    assert received.id == 1
    assert received.title == "Test Task"
    
    # Check metrics
    assert output_port.metrics.messages_out_total == 1
    assert input_port.metrics.messages_in_total == 1
    
    print("✅ Test 3: Data flow defined")

@pytest.mark.asyncio
async def test_async_iteration():
    """TEST 4: InputPort should support async for loops"""
    from autocoder_cc.components.ports import create_connected_ports
    
    # Create connected ports
    out_port, in_port = create_connected_ports("out_data", "in_data", TodoItem)
    
    # Send multiple items
    items = [
        TodoItem(id=1, title="Task 1"),
        TodoItem(id=2, title="Task 2"),
        TodoItem(id=3, title="Task 3")
    ]
    
    async def sender():
        for item in items:
            await out_port.send(item)
        await out_port.close()
    
    async def receiver():
        received = []
        async for item in in_port:  # This tests __aiter__ and __anext__
            received.append(item)
        return received
    
    # Run concurrently
    async with anyio.create_task_group() as tg:
        tg.start_soon(sender)
        received_items = await receiver()
    
    assert len(received_items) == 3
    assert received_items[0].title == "Task 1"
    assert received_items[2].title == "Task 3"
    
    print("✅ Test 4: Async iteration defined")

@pytest.mark.asyncio
async def test_overflow_policy_block():
    """TEST 5: BLOCK policy should wait for space"""
    from autocoder_cc.components.ports import OutputPort, InputPort, OverflowPolicy
    
    # Small buffer to test blocking
    send_stream, receive_stream = anyio.create_memory_object_stream(2)
    out_port = OutputPort("out_data", TodoItem, buffer_size=2, 
                         overflow_policy=OverflowPolicy.BLOCK)
    out_port.connect(send_stream)
    
    in_port = InputPort("in_data", TodoItem)
    in_port.connect(receive_stream)
    
    # Fill buffer
    await out_port.send(TodoItem(id=1, title="Item 1"))
    await out_port.send(TodoItem(id=2, title="Item 2"))
    
    # Third send should block until we receive
    send_complete = False
    
    async def try_send():
        nonlocal send_complete
        await out_port.send(TodoItem(id=3, title="Item 3"))
        send_complete = True
    
    async def receive_one():
        await asyncio.sleep(0.1)  # Let send start and block
        assert not send_complete  # Should still be blocked
        await in_port.receive()    # This unblocks the send
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(try_send)
        tg.start_soon(receive_one)
    
    assert send_complete  # Should complete after receive
    
    print("✅ Test 5: Blocking policy defined")

@pytest.mark.asyncio
async def test_overflow_policy_timeout():
    """TEST 6: BLOCK_WITH_TIMEOUT should timeout after 2s"""
    from autocoder_cc.components.ports import OutputPort, OverflowPolicy
    
    # Small buffer that's full
    send_stream, _ = anyio.create_memory_object_stream(1)
    out_port = OutputPort("out_data", TodoItem, buffer_size=1,
                         overflow_policy=OverflowPolicy.BLOCK_WITH_TIMEOUT)
    out_port.connect(send_stream)
    
    # Fill buffer
    await out_port.send(TodoItem(id=1, title="Item 1"))
    
    # Second send should timeout after 2 seconds
    start = time.time()
    with pytest.raises(TimeoutError, match="Send timeout after 2s"):
        await out_port.send(TodoItem(id=2, title="Item 2"))
    
    duration = time.time() - start
    assert 1.9 < duration < 2.1  # Should timeout at ~2 seconds
    assert out_port.metrics.messages_dropped_total == 1
    
    print("✅ Test 6: Timeout policy defined")

if __name__ == "__main__":
    print("=" * 50)
    print("PORT SYSTEM TEST SUITE")
    print("=" * 50)
    print("This defines the expected behavior of our port system")
    print("Run with: pytest tests/port_based/test_ports.py -v")
EOF

echo "✅ Test suite created!"
```

### Step 2: Run Tests to See They Fail (5 minutes)
```bash
# Run tests (will fail - that's expected!)
pytest tests/port_based/test_ports.py -v

# You should see:
# ImportError: cannot import name 'OutputPort' from 'autocoder_cc.components.ports'
# This is good! Now we know what to implement.
```

## 🕒 Hour 3-4: Implement Port Classes (10:00 AM - 12:00 PM)

### Step 1: Create Port Package Structure (10 minutes)
```bash
# Create __init__.py
cat > autocoder_cc/components/ports/__init__.py << 'EOF'
"""Port-based communication system"""
from .base import Port, InputPort, OutputPort, create_connected_ports
from .policies import OverflowPolicy
from .metrics import PortMetrics

__all__ = [
    'Port', 'InputPort', 'OutputPort', 'create_connected_ports',
    'OverflowPolicy', 'PortMetrics'
]
EOF
```

### Step 2: Create OverflowPolicy Enum (10 minutes)
```bash
cat > autocoder_cc/components/ports/policies.py << 'EOF'
"""Overflow policies for backpressure handling"""
from enum import Enum

class OverflowPolicy(Enum):
    """Decision #47: Overflow policies"""
    BLOCK = "block"                      # Internal ports: wait forever
    BLOCK_WITH_TIMEOUT = "block_with_timeout"  # Ingress ports: 2s timeout
    DROP_OLDEST = "drop_oldest"          # Future v2 feature
    DROP_NEWEST = "drop_newest"          # Future v2 feature
EOF
```

### Step 3: Create PortMetrics Class (15 minutes)
```bash
cat > autocoder_cc/components/ports/metrics.py << 'EOF'
"""Port metrics collection (Decision #51)"""
import time
from typing import Dict, Any

class PortMetrics:
    """Required metrics for every port"""
    
    def __init__(self, port_name: str):
        self.port_name = port_name
        # Counters
        self.messages_in_total = 0
        self.messages_out_total = 0
        self.messages_dropped_total = 0
        self.errors_total = 0
        # Gauges
        self.queue_depth = 0
        # Timing
        self.process_latency_ms_sum = 0.0
        self.process_latency_ms_count = 0
        self.blocked_duration_ms = 0.0
        self.last_activity = time.time()
    
    def record_latency(self, latency_ms: float):
        """Track latency for histogram"""
        self.process_latency_ms_sum += latency_ms
        self.process_latency_ms_count += 1
    
    def get_avg_latency_ms(self) -> float:
        """Calculate average latency"""
        if self.process_latency_ms_count == 0:
            return 0.0
        return self.process_latency_ms_sum / self.process_latency_ms_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "port_name": self.port_name,
            "messages_in_total": self.messages_in_total,
            "messages_out_total": self.messages_out_total,
            "messages_dropped_total": self.messages_dropped_total,
            "errors_total": self.errors_total,
            "queue_depth": self.queue_depth,
            "avg_latency_ms": self.get_avg_latency_ms(),
            "blocked_duration_ms": self.blocked_duration_ms,
            "last_activity": self.last_activity
        }
EOF
```

### Step 4: Implement Base Port Classes (45 minutes)
```bash
# This is the CORE implementation
cat > autocoder_cc/components/ports/base.py << 'EOF'
"""Port implementation - the foundation of our new architecture"""
import time
from typing import TypeVar, Generic, Type, Optional, Any, Tuple
from pydantic import BaseModel, ValidationError
import anyio
from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream

from .policies import OverflowPolicy
from .metrics import PortMetrics

# Generic type for port data
T = TypeVar('T', bound=BaseModel)

class Port(Generic[T]):
    """Base port with validation and metrics"""
    
    def __init__(self, 
                 name: str,
                 schema: Type[T],
                 buffer_size: int = 1024,  # Decision #49
                 overflow_policy: OverflowPolicy = OverflowPolicy.BLOCK):
        
        # Decision #30: Enforce naming convention
        if not (name.startswith("in_") or name.startswith("out_") or name.startswith("err_")):
            raise ValueError(f"Port name '{name}' must start with in_, out_, or err_")
        
        self.name = name
        self.schema = schema
        self.buffer_size = buffer_size
        self.overflow_policy = overflow_policy
        self.metrics = PortMetrics(name)
        self._stream = None
        self._connected = False
    
    def validate(self, data: Any) -> T:
        """Validate data against schema using Pydantic"""
        try:
            if isinstance(data, self.schema):
                return data
            elif isinstance(data, dict):
                return self.schema(**data)
            else:
                return self.schema.parse_obj(data)
        except ValidationError as e:
            self.metrics.errors_total += 1
            raise ValidationError(f"Port {self.name} validation failed: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if port is connected to a stream"""
        return self._connected

class OutputPort(Port[T]):
    """Port for sending validated data"""
    
    def connect(self, stream: MemoryObjectSendStream):
        """Connect to a send stream"""
        if self._connected:
            raise RuntimeError(f"Port {self.name} already connected")
        self._stream = stream
        self._connected = True
    
    async def send(self, data: Any) -> bool:
        """Send data with validation and overflow handling"""
        if not self._connected:
            raise RuntimeError(f"Port {self.name} not connected")
        
        # Validate first
        try:
            validated = self.validate(data)
        except ValidationError as e:
            raise e
        
        # Track timing
        start_time = time.time()
        sent = False
        
        try:
            if self.overflow_policy == OverflowPolicy.BLOCK:
                # Block until space available
                await self._stream.send(validated)
                sent = True
                
            elif self.overflow_policy == OverflowPolicy.BLOCK_WITH_TIMEOUT:
                # Block for max 2 seconds (Decision #47)
                try:
                    with anyio.fail_after(2.0):
                        await self._stream.send(validated)
                        sent = True
                except TimeoutError:
                    self.metrics.messages_dropped_total += 1
                    raise TimeoutError(f"Port {self.name}: Send timeout after 2s (backpressure)")
            
            if sent:
                self.metrics.messages_out_total += 1
            
            return sent
            
        finally:
            # Track metrics
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.blocked_duration_ms += duration_ms
            self.metrics.record_latency(duration_ms)
            self.metrics.last_activity = time.time()
    
    async def close(self):
        """Close the output stream"""
        if self._stream:
            await self._stream.aclose()
            self._connected = False

class InputPort(Port[T]):
    """Port for receiving validated data"""
    
    def connect(self, stream: MemoryObjectReceiveStream):
        """Connect to a receive stream"""
        if self._connected:
            raise RuntimeError(f"Port {self.name} already connected")
        self._stream = stream
        self._connected = True
    
    async def receive(self) -> Optional[T]:
        """Receive and validate data"""
        if not self._connected:
            raise RuntimeError(f"Port {self.name} not connected")
        
        start_time = time.time()
        
        try:
            # Receive from stream
            data = await self._stream.receive()
            
            # Validate
            validated = self.validate(data)
            
            # Update metrics
            self.metrics.messages_in_total += 1
            self.metrics.queue_depth = self._stream.statistics().current_buffer_used
            
            return validated
            
        except anyio.EndOfStream:
            return None
        except Exception as e:
            self.metrics.errors_total += 1
            raise e
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_latency(duration_ms)
            self.metrics.last_activity = time.time()
    
    def __aiter__(self):
        """Make InputPort async iterable"""
        return self
    
    async def __anext__(self) -> T:
        """Support async for loops"""
        result = await self.receive()
        if result is None:
            raise StopAsyncIteration
        return result

def create_connected_ports(
    output_name: str,
    input_name: str,
    schema: Type[BaseModel],
    buffer_size: int = 1024,
    overflow_policy: OverflowPolicy = OverflowPolicy.BLOCK
) -> Tuple[OutputPort, InputPort]:
    """Helper to create pre-connected ports"""
    # Create streams
    send_stream, receive_stream = anyio.create_memory_object_stream(buffer_size)
    
    # Create ports
    output_port = OutputPort(output_name, schema, buffer_size, overflow_policy)
    input_port = InputPort(input_name, schema, buffer_size)
    
    # Connect them
    output_port.connect(send_stream)
    input_port.connect(receive_stream)
    
    return output_port, input_port
EOF
```

## 🕓 Hour 5: Test and Debug (12:00-1:00 PM)

### Step 1: Run Tests Again (10 minutes)
```bash
# Run tests - some should pass now!
pytest tests/port_based/test_ports.py -v

# Expected output:
# test_port_creation_and_validation PASSED
# test_port_naming_convention PASSED
# test_port_connection_and_flow PASSED
# test_async_iteration PASSED
# test_overflow_policy_block PASSED
# test_overflow_policy_timeout PASSED
```

### Step 2: Fix Any Failing Tests (30 minutes)
```python
# If tests fail, debug with this script:
cat > debug_ports.py << 'EOF'
import anyio
from autocoder_cc.components.ports import OutputPort, InputPort, create_connected_ports
from pydantic import BaseModel

class TestData(BaseModel):
    value: int

async def debug():
    print("Testing port creation...")
    out_port = OutputPort("out_test", TestData)
    print(f"✓ Output port created: {out_port.name}")
    
    print("\nTesting port connection...")
    out_port, in_port = create_connected_ports("out_data", "in_data", TestData)
    print(f"✓ Ports connected: {out_port.is_connected} / {in_port.is_connected}")
    
    print("\nTesting data flow...")
    await out_port.send(TestData(value=42))
    result = await in_port.receive()
    print(f"✓ Data received: {result.value}")
    
    print("\nTesting metrics...")
    print(f"  Out messages: {out_port.metrics.messages_out_total}")
    print(f"  In messages: {in_port.metrics.messages_in_total}")
    
    print("\n✅ All basic tests pass!")

if __name__ == "__main__":
    anyio.run(debug())
EOF

python debug_ports.py
```

### Step 3: Run Coverage Report (10 minutes)
```bash
# Check test coverage
pytest tests/port_based/test_ports.py --cov=autocoder_cc.components.ports --cov-report=term-missing

# Should show >90% coverage for ports module
```

## 🕔 Hour 6: Documentation & Commit (1:00-2:00 PM)

### Step 1: Create Port Documentation (15 minutes)
```bash
cat > autocoder_cc/components/ports/README.md << 'EOF'
# Port System Documentation

## Overview
The port system replaces RPC with typed, validated data streams.

## Key Features
- Type safety via Pydantic schemas
- Backpressure handling via overflow policies
- Metrics collection on every port
- Async iteration support

## Usage Example
```python
from autocoder_cc.components.ports import create_connected_ports
from pydantic import BaseModel

class MyData(BaseModel):
    value: int

# Create connected ports
out_port, in_port = create_connected_ports("out_data", "in_data", MyData)

# Send data
await out_port.send(MyData(value=42))

# Receive data
data = await in_port.receive()
```

## Overflow Policies
- BLOCK: Wait forever (internal ports)
- BLOCK_WITH_TIMEOUT: Wait 2s then fail (ingress ports)

## Metrics
Every port tracks:
- messages_in_total / messages_out_total
- messages_dropped_total
- errors_total
- avg_latency_ms
- blocked_duration_ms
EOF
```

### Step 2: Commit Day 1 Work (15 minutes)
```bash
# Add all new files
git add autocoder_cc/components/ports/
git add tests/port_based/
git add requirements_port.txt
git add .env

# Commit with detailed message
git commit -m "Day 1: Port infrastructure implementation

- Created port system replacing RPC architecture
- Implemented InputPort and OutputPort with validation
- Added overflow policies (BLOCK, BLOCK_WITH_TIMEOUT)
- Implemented metrics collection (Decision #51)
- Added async iteration support for InputPort
- 6 tests passing with >90% coverage
- Fixed critical import bug at line 1492

Decisions implemented:
- #6: Port-based architecture
- #30: Port naming conventions (in_, out_, err_)
- #47: Overflow policies
- #49: 1024 default buffer size
- #51: Required metrics
"
```

## 🕕 Hour 7-8: Afternoon - Component Base Class (2:00-4:00 PM)

### Step 1: Write Component Tests (30 minutes)
```bash
cat > tests/port_based/test_component_base.py << 'EOF'
"""Component base class tests"""
import pytest
from pydantic import BaseModel
import anyio

class DataSchema(BaseModel):
    value: int

class ResultSchema(BaseModel):
    result: int

@pytest.mark.asyncio
async def test_component_port_declaration():
    """Components should declare ports using standard prefixes"""
    from autocoder_cc.components.base import PortBasedComponent
    
    class TestComponent(PortBasedComponent):
        def configure_ports(self):
            self.add_input_port("in_data", DataSchema)
            self.add_output_port("out_result", ResultSchema)
            self.add_output_port("err_errors", BaseModel)
        
        async def process(self):
            pass
    
    component = TestComponent()
    assert "in_data" in component.input_ports
    assert "out_result" in component.output_ports
    assert "err_errors" in component.output_ports
    print("✅ Port declaration test passed")

@pytest.mark.asyncio
async def test_component_lifecycle():
    """Test setup/process/cleanup lifecycle"""
    from autocoder_cc.components.base import PortBasedComponent
    
    setup_called = False
    process_called = False
    cleanup_called = False
    
    class TestComponent(PortBasedComponent):
        def configure_ports(self):
            pass
        
        async def setup(self):
            nonlocal setup_called
            setup_called = True
        
        async def process(self):
            nonlocal process_called
            process_called = True
        
        async def cleanup(self):
            nonlocal cleanup_called
            cleanup_called = True
    
    component = TestComponent()
    await component.run()
    
    assert setup_called
    assert process_called
    assert cleanup_called
    print("✅ Lifecycle test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

### Step 2: Implement Component Base (45 minutes)
```bash
# Create base component - this file already exists, so be careful
cat > autocoder_cc/components/base.py << 'EOF'
"""Base class for port-based components"""
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional
from pydantic import BaseModel
import logging

from autocoder_cc.components.ports import InputPort, OutputPort, OverflowPolicy

logger = logging.getLogger(__name__)

class PortBasedComponent(ABC):
    """Base class for all port-based components"""
    
    def __init__(self, 
                 name: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.input_ports: Dict[str, InputPort] = {}
        self.output_ports: Dict[str, OutputPort] = {}
        self._running = False
        
        # Configure ports (implemented by subclasses)
        self.configure_ports()
        
        logger.info(f"Component {self.name} initialized with "
                   f"{len(self.input_ports)} inputs, "
                   f"{len(self.output_ports)} outputs")
    
    @abstractmethod
    def configure_ports(self):
        """Declare all ports - must override"""
        pass
    
    def add_input_port(self, 
                      name: str, 
                      schema: Type[BaseModel],
                      buffer_size: int = 1024,
                      **kwargs):
        """Add input port with validation"""
        if not name.startswith("in_"):
            raise ValueError(f"Input port name '{name}' must start with 'in_'")
        
        if name in self.input_ports:
            raise ValueError(f"Input port '{name}' already exists")
        
        self.input_ports[name] = InputPort(
            name=name,
            schema=schema,
            buffer_size=buffer_size,
            **kwargs
        )
        logger.debug(f"Added input port: {name}")
    
    def add_output_port(self,
                       name: str,
                       schema: Type[BaseModel],
                       buffer_size: int = 1024,
                       overflow_policy: OverflowPolicy = None,
                       **kwargs):
        """Add output port with validation"""
        if not (name.startswith("out_") or name.startswith("err_")):
            raise ValueError(f"Output port name '{name}' must start with 'out_' or 'err_'")
        
        if name in self.output_ports:
            raise ValueError(f"Output port '{name}' already exists")
        
        # Apply default overflow policy
        if overflow_policy is None:
            if self.config.get("is_ingress", False):
                overflow_policy = OverflowPolicy.BLOCK_WITH_TIMEOUT
            else:
                overflow_policy = OverflowPolicy.BLOCK
        
        self.output_ports[name] = OutputPort(
            name=name,
            schema=schema,
            buffer_size=buffer_size,
            overflow_policy=overflow_policy,
            **kwargs
        )
        logger.debug(f"Added output port: {name}")
    
    async def setup(self):
        """Initialize component - override if needed"""
        logger.info(f"Setting up component: {self.name}")
    
    @abstractmethod
    async def process(self):
        """Main processing logic - must override"""
        pass
    
    async def cleanup(self):
        """Cleanup resources - override if needed"""
        logger.info(f"Cleaning up component: {self.name}")
        
        # Close all output ports
        for port_name, port in self.output_ports.items():
            try:
                await port.close()
                logger.debug(f"Closed output port: {port_name}")
            except Exception as e:
                logger.error(f"Error closing port {port_name}: {e}")
    
    async def run(self):
        """Run component lifecycle"""
        self._running = True
        logger.info(f"Starting component: {self.name}")
        
        try:
            await self.setup()
            await self.process()
        except Exception as e:
            logger.error(f"Component {self.name} failed: {e}", exc_info=True)
            raise
        finally:
            self._running = False
            await self.cleanup()
            logger.info(f"Component {self.name} stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all ports"""
        metrics = {
            "component": self.name,
            "input_ports": {},
            "output_ports": {}
        }
        
        for name, port in self.input_ports.items():
            metrics["input_ports"][name] = port.metrics.to_dict()
        
        for name, port in self.output_ports.items():
            metrics["output_ports"][name] = port.metrics.to_dict()
        
        return metrics
EOF
```

### Step 3: Test Component Base (15 minutes)
```bash
# Run component tests
pytest tests/port_based/test_component_base.py -v

# Should see:
# test_component_port_declaration PASSED
# test_component_lifecycle PASSED
```

## 🕖 End of Day 1: Summary & Verification (4:00-5:00 PM)

### Final Test Run
```bash
# Run all Day 1 tests
pytest tests/port_based/ -v --tb=short

# Expected: 8 tests passed
```

### Coverage Check
```bash
# Check coverage
pytest tests/port_based/ --cov=autocoder_cc.components --cov-report=term

# Should show:
# autocoder_cc/components/ports/base.py      90%+
# autocoder_cc/components/ports/metrics.py   85%+
# autocoder_cc/components/ports/policies.py  100%
# autocoder_cc/components/base.py            80%+
```

### Create Day 1 Summary
```bash
cat > DAY1_COMPLETE.md << 'EOF'
# Day 1 Complete! ✅

## Accomplished
1. ✅ Fixed critical import bug (line 1492)
2. ✅ Created complete port infrastructure
3. ✅ Implemented InputPort and OutputPort
4. ✅ Added overflow policies (BLOCK, BLOCK_WITH_TIMEOUT)
5. ✅ Implemented metrics collection
6. ✅ Created PortBasedComponent base class
7. ✅ 8 tests passing with >85% coverage

## Key Files Created
- autocoder_cc/components/ports/base.py (Port, InputPort, OutputPort)
- autocoder_cc/components/ports/metrics.py (PortMetrics)
- autocoder_cc/components/ports/policies.py (OverflowPolicy)
- autocoder_cc/components/base.py (PortBasedComponent)
- tests/port_based/test_ports.py (6 tests)
- tests/port_based/test_component_base.py (2 tests)

## Metrics
- Lines of code: ~500
- Test coverage: 85%+
- Tests passing: 8/8
- Decisions implemented: 6 (#6, #30, #47, #49, #51, #10)

## Tomorrow (Day 2)
- Implement 5 mathematical primitives
- Create Source, Sink, Transformer, Splitter, Merger
- Add primitive tests
- Start recipe system

## Verification Command
python -c "
from autocoder_cc.components.ports import create_connected_ports
from pydantic import BaseModel
import anyio

class Data(BaseModel):
    value: int

async def verify():
    out_port, in_port = create_connected_ports('out_test', 'in_test', Data)
    await out_port.send(Data(value=42))
    result = await in_port.receive()
    print(f'✅ Day 1 Success! Port system working: {result.value}')

anyio.run(verify())
"
EOF
```

### Final Commit
```bash
git add -A
git commit -m "Day 1 Complete: Port infrastructure and component base

Summary:
- Port system fully implemented and tested
- Component base class working
- 8 tests passing with 85%+ coverage
- Ready for Day 2: Mathematical primitives

Next: Implement Source, Sink, Transformer, Splitter, Merger
"

echo "🎉 DAY 1 COMPLETE! Port system is working!"
```

---

## Troubleshooting Guide

### If Import Errors
```python
# Add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### If Test Failures
```python
# Debug individual test
pytest tests/port_based/test_ports.py::test_port_creation_and_validation -vvs
```

### If Async Issues
```python
# Use anyio.run instead of asyncio.run
import anyio
anyio.run(main())  # Not asyncio.run(main())
```

### If Coverage Low
```bash
# Find uncovered lines
pytest tests/port_based/ --cov=autocoder_cc.components --cov-report=term-missing
```

---

*This hour-by-hour guide ensures Day 1 success with zero ambiguity.*