# Common Pitfalls and Solutions - Port Implementation

*Created: 2025-08-12*  
*Purpose: Prevent common mistakes during implementation*

## 🔴 CRITICAL PITFALLS

### Pitfall 1: Forgetting the Import Bug Fix
**Symptom**: 100% validation failures even after implementing ports  
**Cause**: Line 1492 still has wrong import  
**Solution**:
```bash
# CHECK FIRST:
sed -n '1492p' autocoder_cc/blueprint_language/component_logic_generator.py

# If it shows "from observability import", FIX IT:
sed -i '1492s/.*/from autocoder_cc.components.composed_base import ComposedComponent/' \
    autocoder_cc/blueprint_language/component_logic_generator.py
```

### Pitfall 2: Using asyncio Instead of anyio
**Symptom**: Timeout errors don't work correctly  
**Cause**: Mixed async libraries  
**Solution**:
```python
# WRONG:
import asyncio
asyncio.run(main())
asyncio.create_task(foo())

# RIGHT:
import anyio
anyio.run(main())
async with anyio.create_task_group() as tg:
    tg.start_soon(foo)
```

### Pitfall 3: Wrong Port Naming
**Symptom**: ValueError: Port name must start with...  
**Cause**: Not using prefixes  
**Solution**:
```python
# WRONG:
self.add_input_port("data", Schema)
self.add_output_port("result", Schema)

# RIGHT:
self.add_input_port("in_data", Schema)
self.add_output_port("out_result", Schema)
self.add_output_port("err_errors", Schema)
```

## 🟡 IMPLEMENTATION PITFALLS

### Pitfall 4: Forgetting to Connect Ports
**Symptom**: RuntimeError: Port not connected  
**Cause**: Created ports but didn't connect streams  
**Solution**:
```python
# WRONG - ports created but not connected:
out_port = OutputPort("out_data", Schema)
in_port = InputPort("in_data", Schema)
await out_port.send(data)  # RuntimeError!

# RIGHT - connect before using:
send_stream, receive_stream = anyio.create_memory_object_stream(1024)
out_port.connect(send_stream)
in_port.connect(receive_stream)
await out_port.send(data)  # Works!

# EASIER - use helper:
out_port, in_port = create_connected_ports("out_data", "in_data", Schema)
```

### Pitfall 5: Wrong Overflow Policy for Port Type
**Symptom**: Ingress ports blocking forever  
**Cause**: Using BLOCK instead of BLOCK_WITH_TIMEOUT  
**Solution**:
```python
# WRONG for ingress:
self.add_output_port("out_response", Response, 
                    overflow_policy=OverflowPolicy.BLOCK)  # Blocks forever!

# RIGHT for ingress:
self.add_output_port("out_response", Response,
                    overflow_policy=OverflowPolicy.BLOCK_WITH_TIMEOUT)  # 2s timeout

# Or use config:
def __init__(self, **config):
    config["is_ingress"] = True  # Component will auto-select policy
    super().__init__(**config)
```

### Pitfall 6: Not Handling EndOfStream
**Symptom**: Tests hang when using async for  
**Cause**: Stream never closed  
**Solution**:
```python
# WRONG - stream never ends:
async for item in input_port:
    process(item)
# Hangs forever!

# RIGHT - close output when done:
async def sender():
    for item in items:
        await out_port.send(item)
    await out_port.close()  # This triggers EndOfStream

async def receiver():
    async for item in in_port:  # Will stop when stream closes
        process(item)
```

## 🟢 TESTING PITFALLS

### Pitfall 7: Using Mocks in Tests
**Symptom**: Tests pass but real system fails  
**Cause**: Mocks hide real problems  
**Solution**:
```python
# WRONG - using mocks:
mock_port = Mock()
mock_port.send.return_value = asyncio.Future()

# RIGHT - use real ports:
out_port, in_port = create_connected_ports("out_test", "in_test", Schema)
await out_port.send(real_data)
result = await in_port.receive()
```

### Pitfall 8: Not Testing Backpressure
**Symptom**: System deadlocks under load  
**Cause**: Didn't test blocking behavior  
**Solution**:
```python
# TEST THIS:
@pytest.mark.asyncio
async def test_backpressure():
    # Small buffer to force blocking
    out_port, in_port = create_connected_ports(
        "out_test", "in_test", Schema, buffer_size=2
    )
    
    # Fill buffer
    await out_port.send(item1)
    await out_port.send(item2)
    
    # This should block
    blocked = False
    async def try_send():
        nonlocal blocked
        blocked = True
        await out_port.send(item3)  # Blocks until receive
    
    # Verify blocking behavior
    task = asyncio.create_task(try_send())
    await asyncio.sleep(0.1)
    assert blocked  # Should be blocked
    
    await in_port.receive()  # Unblock
    await task  # Should complete now
```

### Pitfall 9: Wrong Test Order
**Symptom**: Later tests fail mysteriously  
**Cause**: Tests not isolated  
**Solution**:
```python
# WRONG - shared state:
port = OutputPort("out_test", Schema)  # Module level!

@pytest.mark.asyncio
async def test_one():
    await port.send(data)  # Modifies shared port

@pytest.mark.asyncio  
async def test_two():
    await port.send(data)  # Port already used!

# RIGHT - isolated:
@pytest.mark.asyncio
async def test_one():
    port = OutputPort("out_test", Schema)  # Fresh port
    # ...

@pytest.mark.asyncio
async def test_two():
    port = OutputPort("out_test", Schema)  # Fresh port
    # ...
```

## 💾 CHECKPOINT PITFALLS

### Pitfall 10: Non-Atomic Checkpoint Writes
**Symptom**: Corrupted checkpoints after crash  
**Cause**: Not using atomic write pattern  
**Solution**:
```python
# WRONG - can corrupt on crash:
with open(checkpoint_file, 'w') as f:
    json.dump(state, f)  # Crash here = corrupt file

# RIGHT - atomic write:
temp_file = checkpoint_file.with_suffix('.tmp')
with open(temp_file, 'w') as f:
    json.dump(state, f)
    os.fsync(f.fileno())  # Ensure on disk
temp_file.rename(checkpoint_file)  # Atomic operation
os.fsync(os.open(checkpoint_file.parent, os.O_RDONLY))  # Sync directory
```

### Pitfall 11: Not Cleaning Old Checkpoints
**Symptom**: Disk fills up over time  
**Cause**: Never deleting old checkpoints  
**Solution**:
```python
def save_checkpoint(self, state):
    # Save new checkpoint
    checkpoint_id = self._save(state)
    
    # IMPORTANT - cleanup old ones:
    self._cleanup_old_checkpoints()  # Keep only last 10
    
    return checkpoint_id

def _cleanup_old_checkpoints(self):
    conn.execute("""
        DELETE FROM checkpoints 
        WHERE id NOT IN (
            SELECT id FROM checkpoints 
            ORDER BY epoch DESC 
            LIMIT 10  -- Decision #46
        )
    """)
```

## 🔄 RECIPE PITFALLS

### Pitfall 12: Runtime Recipe Expansion
**Symptom**: Performance degradation  
**Cause**: Expanding recipes at runtime  
**Solution**:
```python
# WRONG - runtime expansion:
class Component:
    def __init__(self, recipe):
        self.recipe = recipe
    
    async def process(self):
        behavior = expand_recipe(self.recipe)  # Every message!
        return behavior.process(data)

# RIGHT - compile-time expansion:
# Generate code once during blueprint processing:
code = expand_recipe("Store", "TodoStore")
write_file("todo_store.py", code)

# Then import and use:
from generated.todo_store import TodoStore
```

### Pitfall 13: Mixing Primitives and Domain Types
**Symptom**: Confusion about component types  
**Cause**: Not understanding primitive vs recipe  
**Solution**:
```python
# WRONG - creating domain type directly:
class Store(PortBasedComponent):  # This is a domain type!
    # ...

# RIGHT - use primitive with recipe:
class TodoStore(Transformer):  # Primitive!
    """Generated from Store recipe"""
    # Transformer with persistence traits
```

## 🎯 PERFORMANCE PITFALLS

### Pitfall 14: Small Buffer Sizes
**Symptom**: Poor throughput  
**Cause**: Buffer too small causes blocking  
**Solution**:
```python
# WRONG - tiny buffer:
create_connected_ports("out", "in", Schema, buffer_size=10)

# RIGHT - adequate buffer:
create_connected_ports("out", "in", Schema, buffer_size=1024)  # Default

# For high throughput:
create_connected_ports("out", "in", Schema, buffer_size=10000)
```

### Pitfall 15: Not Tracking Metrics
**Symptom**: Can't debug performance issues  
**Cause**: Not checking port metrics  
**Solution**:
```python
# Always check metrics when debugging:
metrics = component.get_metrics()
for port_name, port_metrics in metrics["output_ports"].items():
    print(f"{port_name}:")
    print(f"  Sent: {port_metrics['messages_out_total']}")
    print(f"  Dropped: {port_metrics['messages_dropped_total']}")
    print(f"  Avg latency: {port_metrics['avg_latency_ms']}ms")
    print(f"  Blocked time: {port_metrics['blocked_duration_ms']}ms")
```

## 🐛 DEBUGGING PITFALLS

### Pitfall 16: Silent Validation Errors
**Symptom**: Data not flowing, no errors  
**Cause**: Validation failing silently  
**Solution**:
```python
# Add logging to see validation errors:
import logging
logging.basicConfig(level=logging.DEBUG)

# Or catch and log:
try:
    await port.send(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Now you can see what's wrong
```

### Pitfall 17: Deadlock from Circular Dependencies
**Symptom**: System hangs  
**Cause**: A→B→A port cycle with full buffers  
**Solution**:
```python
# Avoid cycles, or use large buffers:
# A → B
# ↑   ↓
# D ← C

# If cycle needed, ensure adequate buffers:
buffer_size = 10000  # Large enough to prevent deadlock
```

## 🚀 QUICK FIXES

### System Hangs
```bash
# Check for blocking:
strace -p <pid>  # See if blocked on futex_wait

# Check buffer status:
python -c "
from autocoder_cc.components.ports import create_connected_ports
# ... recreate scenario and check metrics
"
```

### Import Errors
```bash
# Always set PYTHONPATH:
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Or in code:
import sys
sys.path.insert(0, '/path/to/project')
```

### Test Failures
```bash
# Run with maximum verbosity:
pytest test_file.py::test_name -vvs --tb=long

# Check async warnings:
pytest test_file.py -W error::RuntimeWarning
```

### Performance Issues
```python
# Profile async code:
import asyncio
import cProfile

def profile_async():
    pr = cProfile.Profile()
    pr.enable()
    asyncio.run(main())
    pr.disable()
    pr.print_stats(sort='cumtime')
```

## ✅ PREVENTION CHECKLIST

Before each coding session:
- [ ] Source .env file
- [ ] Verify import bug is fixed
- [ ] Check PYTHONPATH is set
- [ ] Pull latest changes
- [ ] Run existing tests

Before committing:
- [ ] All tests pass
- [ ] Coverage > 80%
- [ ] No mocks in tests
- [ ] Metrics implemented
- [ ] Overflow policies correct

Before moving to next phase:
- [ ] Current phase 100% complete
- [ ] Documentation updated
- [ ] Performance targets met
- [ ] No TODO comments left

---

*Keep this document open while implementing to avoid common mistakes.*