# Troubleshooting Guide

*Purpose: Solutions to common problems*

## Import Errors

### Problem: `ImportError: cannot import name 'OutputPort'`
```bash
# Solution 1: Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Solution 2: Check file exists
ls autocoder_cc/components/ports/base.py

# Solution 3: Check __init__.py
cat autocoder_cc/components/ports/__init__.py
# Should have: from .base import OutputPort, InputPort
```

### Problem: `from observability import ComposedComponent` fails
```bash
# This is THE critical bug - fix immediately:
sed -i '1492s/.*/from autocoder_cc.components.composed_base import ComposedComponent/' \
    autocoder_cc/blueprint_language/component_logic_generator.py
```

## Port Errors

### Problem: `ValueError: Port name must start with in_, out_, or err_`
```python
# Wrong:
self.add_input_port("data", Schema)

# Right:
self.add_input_port("in_data", Schema)
```

### Problem: `RuntimeError: Port not connected`
```python
# Wrong - using port before connecting:
port = OutputPort("out_data", Schema)
await port.send(data)  # Error!

# Right - connect first:
port = OutputPort("out_data", Schema)
send_stream, _ = anyio.create_memory_object_stream(1024)
port.connect(send_stream)
await port.send(data)  # Works
```

### Problem: `TimeoutError: Send timeout after 2s`
```python
# Cause: Buffer full, receiver not consuming

# Solution 1: Increase buffer
OutputPort("out_data", Schema, buffer_size=10000)

# Solution 2: Ensure receiver is running
async with anyio.create_task_group() as tg:
    tg.start_soon(sender)
    tg.start_soon(receiver)  # Must run concurrently
```

## Async Errors

### Problem: Using `asyncio` instead of `anyio`
```python
# Wrong:
import asyncio
asyncio.run(main())

# Right:
import anyio
anyio.run(main())
```

### Problem: Stream never ends in tests
```python
# Wrong - stream stays open:
async for item in port:
    process(item)
# Hangs forever

# Right - close when done:
await output_port.close()  # Triggers EndOfStream
```

## Test Failures

### Problem: Tests hang
```bash
# Debug with timeout:
pytest test_file.py -v --timeout=10

# Or check for blocking:
strace -p $(pgrep pytest)
```

### Problem: Coverage too low
```bash
# Find uncovered lines:
pytest tests/ --cov=autocoder_cc.components --cov-report=term-missing

# Shows exactly which lines aren't tested
```

### Problem: Mocks causing false positives
```python
# Wrong - using mocks:
mock_port = Mock()

# Right - use real ports:
out_port, in_port = create_connected_ports("out_test", "in_test", Schema)
```

## Performance Issues

### Problem: Throughput < 1000 msg/sec
```python
# Check buffer size:
create_connected_ports("out", "in", Schema, buffer_size=10000)

# Profile to find bottleneck:
import cProfile
pr = cProfile.Profile()
pr.enable()
anyio.run(benchmark())
pr.disable()
pr.print_stats(sort='cumtime')
```

### Problem: High latency
```python
# Check metrics:
print(f"Avg latency: {port.metrics.get_avg_latency_ms()}ms")
print(f"Blocked time: {port.metrics.blocked_duration_ms}ms")

# If blocked time high, increase buffers
```

## Checkpoint Issues

### Problem: Checkpoint corruption
```python
# Always use atomic writes:
temp_file = Path(f"{checkpoint_id}.tmp")
with open(temp_file, 'w') as f:
    json.dump(state, f)
    os.fsync(f.fileno())  # Critical!
temp_file.rename(checkpoint_file)  # Atomic
```

### Problem: Can't find checkpoints
```bash
# Check location:
ls /var/lib/autocoder4_cc/checkpoints/

# Check permissions:
ls -la /var/lib/autocoder4_cc/

# Fix if needed:
sudo chown -R $USER:$USER /var/lib/autocoder4_cc/
```

## Generation Issues

### Problem: Still generating RPC code
```python
# Check template is updated:
grep -n "communication.py" autocoder_cc/blueprint_language/*.py

# Should find NO references to communication.py
# All should use ports instead
```

### Problem: Generated components don't validate
```python
# Run healer first:
from autocoder_cc.healing import BasicHealer
healer = BasicHealer()
fixed_code = await healer.heal(generated_code)

# Healer fixes:
# - Import paths
# - Async/await
# - Port naming
```

## Common Mistakes

### Using wrong Python version
```bash
python --version  # Must be 3.10+
```

### Forgetting to source .env
```bash
source .env  # Do this every session
```

### Not fixing import bug first
```bash
# This MUST be line 1 of implementation:
grep -n "from observability import" autocoder_cc/blueprint_language/component_logic_generator.py
# If found, fix immediately
```

### Small buffers causing deadlock
```python
# Never use buffer < 100:
buffer_size=1024  # Good default
buffer_size=10    # Too small, will deadlock
```

## Quick Fixes

### Reset everything
```bash
# Clean start:
rm -rf autocoder_cc/components/ports
rm -rf tests/port_based
git checkout -- .
source .env
```

### Verify setup
```python
# Quick test:
python -c "
import anyio
from pydantic import BaseModel
class T(BaseModel): v: int
print('✅ Dependencies OK')
"
```

### Run single test
```bash
# Debug one test:
pytest path/to/test.py::test_function_name -vvs
```

### Check what's imported
```python
# See all imports:
python -c "import autocoder_cc.components.ports; print(dir(autocoder_cc.components.ports))"
```

## When All Else Fails

1. **Check the import bug** (line 1492)
2. **Source .env** 
3. **Use anyio not asyncio**
4. **Ensure ports are connected**
5. **Check buffer sizes (1024+)**
6. **No mocks in tests**
7. **Close streams when done**

## Get Help

If stuck after trying above:
1. Check [CRITICAL_DECISIONS.md](CRITICAL_DECISIONS.md) for design decisions
2. Review [CODE_REFERENCE.md](CODE_REFERENCE.md) for working examples
3. Look at test files for patterns
4. Simplify to minimal failing example

---

*Most problems are one of the above. Fix systematically.*