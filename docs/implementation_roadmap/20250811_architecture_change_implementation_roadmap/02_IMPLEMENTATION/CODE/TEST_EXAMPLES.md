# Test-Driven Development Examples

*Purpose: Concrete test examples to guide implementation*

## Test-First Philosophy

**Write the test → See it fail → Make it pass → Refactor**

## Port System Tests

### Test: Port Creation and Validation
```python
import pytest
from pydantic import BaseModel, ValidationError
import anyio

class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False

@pytest.mark.asyncio
async def test_port_validation():
    """Ports should validate data against schemas"""
    from autocoder_cc.components.ports import OutputPort
    
    port = OutputPort("out_test", TodoItem)
    
    # Valid data should pass
    valid_item = TodoItem(id=1, title="Test", completed=False)
    validated = port.validate(valid_item)
    assert validated.id == 1
    
    # Invalid data should fail
    with pytest.raises(ValidationError):
        port.validate({"id": "not_an_int", "title": "Test"})
```

### Test: Port Connection and Flow
```python
@pytest.mark.asyncio
async def test_port_connection():
    """Data should flow through connected ports"""
    from autocoder_cc.components.ports import create_connected_ports
    
    out_port, in_port = create_connected_ports("out_data", "in_data", TodoItem)
    
    # Send data
    item = TodoItem(id=1, title="Test Task")
    await out_port.send(item)
    
    # Receive data
    received = await in_port.receive()
    assert received.id == 1
    assert received.title == "Test Task"
    
    # Check metrics
    assert out_port.metrics.messages_out_total == 1
    assert in_port.metrics.messages_in_total == 1
```

### Test: Async Iteration
```python
@pytest.mark.asyncio
async def test_async_iteration():
    """InputPort should support async for loops"""
    from autocoder_cc.components.ports import create_connected_ports
    
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
        async for item in in_port:  # Tests __aiter__ and __anext__
            received.append(item)
        return received
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(sender)
        received_items = await receiver()
    
    assert len(received_items) == 3
    assert received_items[0].title == "Task 1"
```

## Component Tests

### Test: Component Port Declaration
```python
@pytest.mark.asyncio
async def test_component_ports():
    """Components should declare ports with correct prefixes"""
    from autocoder_cc.components.base import PortBasedComponent
    
    class TestComponent(PortBasedComponent):
        def configure_ports(self):
            self.add_input_port("in_data", DataSchema)
            self.add_output_port("out_result", ResultSchema)
            self.add_output_port("err_errors", ErrorSchema)
        
        async def process(self):
            pass
    
    component = TestComponent()
    assert "in_data" in component.input_ports
    assert "out_result" in component.output_ports
    assert "err_errors" in component.output_ports
    
    # Invalid names should fail
    with pytest.raises(ValueError, match="must start with"):
        component.add_input_port("data", DataSchema)  # Missing in_
```

### Test: Component Lifecycle
```python
@pytest.mark.asyncio
async def test_component_lifecycle():
    """Test setup → process → cleanup lifecycle"""
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
```

## Primitive Tests

### Test: Transformer Primitive
```python
@pytest.mark.asyncio
async def test_transformer():
    """Transformer should have exactly 1→1 ports"""
    from autocoder_cc.components.primitives import Transformer
    
    class Doubler(Transformer):
        def configure_ports(self):
            self.add_input_port("in_numbers", IntSchema)
            self.add_output_port("out_doubled", IntSchema)
        
        async def transform(self, item):
            return IntSchema(value=item.value * 2)
    
    # Test port validation
    doubler = Doubler()
    doubler.validate_port_count()  # Should not raise
    
    # Test transformation
    out_port, in_port = create_connected_ports("out_test", "in_numbers", IntSchema)
    result_out, result_in = create_connected_ports("out_doubled", "in_test", IntSchema)
    
    doubler.input_ports["in_numbers"] = in_port
    doubler.output_ports["out_doubled"] = result_out
    
    # Send test data
    await out_port.send(IntSchema(value=21))
    
    # Run transformer
    async with anyio.create_task_group() as tg:
        tg.start_soon(doubler.process)
        result = await result_in.receive()
    
    assert result.value == 42
```

## Integration Tests

### Test: Complete Component Integration
```python
@pytest.mark.asyncio
async def test_todo_store_integration():
    """Test complete TodoStore with real database"""
    from examples.todo_store import TodoStore, TodoCommand, TodoResponse
    
    store = TodoStore(config={"db_path": ":memory:"})
    
    # Wire up test ports
    cmd_out, cmd_in = create_connected_ports("out_test", "in_commands", TodoCommand)
    resp_out, resp_in = create_connected_ports("out_responses", "in_test", TodoResponse)
    
    store.input_ports["in_commands"] = cmd_in
    store.output_ports["out_responses"] = resp_out
    
    async with anyio.create_task_group() as tg:
        # Start component
        tg.start_soon(store.run)
        
        # Test create
        await cmd_out.send(TodoCommand(
            action="create",
            title="Test Todo"
        ))
        response = await resp_in.receive()
        assert response.success
        todo_id = response.data["id"]
        
        # Test query
        await cmd_out.send(TodoCommand(
            action="query",
            id=todo_id
        ))
        response = await resp_in.receive()
        assert response.data["title"] == "Test Todo"
        
        # Stop component
        await cmd_out.close()
```

## Performance Tests

### Test: Throughput Benchmark
```python
@pytest.mark.asyncio
async def test_throughput():
    """Should achieve 1000+ messages/second"""
    from autocoder_cc.components.ports import create_connected_ports
    import time
    
    out_port, in_port = create_connected_ports("out_test", "in_test", DataSchema)
    
    count = 10000
    start = time.monotonic()
    
    # Send messages
    for i in range(count):
        await out_port.send(DataSchema(value=i))
    
    # Receive messages
    for _ in range(count):
        await in_port.receive()
    
    duration = time.monotonic() - start
    throughput = count / duration
    
    assert throughput >= 1000, f"Only {throughput:.0f} msg/sec"
    print(f"✅ Throughput: {throughput:.0f} msg/sec")
```

### Test: Latency Measurement
```python
@pytest.mark.asyncio
async def test_latency():
    """Should achieve p95 < 50ms"""
    from autocoder_cc.utils.stats import p95
    
    latencies = []
    
    for _ in range(1000):
        start = time.monotonic()
        await out_port.send(test_data)
        await in_port.receive()
        latency_ms = (time.monotonic() - start) * 1000
        latencies.append(latency_ms)
    
    p95_value = p95(latencies)
    assert p95_value < 50, f"p95 latency {p95_value:.1f}ms > 50ms"
    print(f"✅ p95 latency: {p95_value:.1f}ms")
```

## Running Tests

```bash
# Run all tests
pytest tests/port_based/ -v

# Run with coverage
pytest tests/port_based/ --cov=autocoder_cc.components --cov-report=term-missing

# Run specific test
pytest tests/port_based/test_ports.py::test_port_validation -vvs

# Run performance tests
pytest tests/performance/ -v

# Watch mode for TDD
pytest-watch tests/port_based/ -- -v
```

---
*These tests define the expected behavior and guide implementation through TDD.*