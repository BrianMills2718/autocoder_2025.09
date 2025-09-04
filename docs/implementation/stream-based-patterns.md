# Stream-Based Component Implementation Patterns

## Core Implementation Pattern

### Basic Component Structure
```python
from autocoder_cc.orchestration.component import Component
from autocoder_cc.error_handling.consistent_handler import ConsistentErrorHandler, handle_errors

class MyComponent(Component):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # Initialize error handler
        self.error_handler = ConsistentErrorHandler(f"MyComponent.{name}")
        
        # Component-specific configuration
        self.variant = self.config.get('variant', 'default')
        
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize component"""
        self.logger.info(f"MyComponent '{self.name}' initialized")
        self._status.is_running = True
    
    @handle_errors(component_name="MyComponent", operation="process")
    async def process(self) -> None:
        """Main processing loop with error handling"""
        # Implement variant-specific processing
        if self.variant == 'type_a':
            await self._process_type_a()
        elif self.variant == 'type_b':
            await self._process_type_b()
        else:
            await self._process_default()
    
    async def _process_default(self) -> None:
        """Default processing implementation"""
        # Standard stream processing pattern
        async for item in self.receive_streams.get('input', []):
            try:
                result = await self.transform_item(item)
                
                # Send to output streams
                if 'output' in self.send_streams:
                    await self.send_streams['output'].send(result)
                    
            except Exception as e:
                await self.error_handler.handle_exception(
                    e,
                    context={"item": item, "component": self.name},
                    operation="process_item"
                )
                
    async def transform_item(self, item: Any) -> Any:
        """Override this method for custom transformation logic"""
        return item  # Default: pass-through
        
    async def cleanup(self) -> None:
        """Component cleanup"""
        self._status.is_running = False
        self.logger.info(f"MyComponent '{self.name}' cleaned up")
```

## Multi-Stream Patterns

### Concurrent Stream Processing
```python
async def _process_multi_stream(self) -> None:
    """Process multiple input streams concurrently"""
    async with anyio.create_task_group() as tg:
        for stream_name, stream in self.receive_streams.items():
            tg.start_soon(self._process_single_stream, stream_name, stream)

async def _process_single_stream(self, stream_name: str, stream) -> None:
    """Process a single named stream"""
    async for item in stream:
        result = await self.transform_for_stream(stream_name, item)
        await self._send_to_appropriate_output(stream_name, result)
```

### Dynamic Output Routing
```python
async def _route_to_output(self, item: Any) -> None:
    """Route item to appropriate output stream based on content"""
    output_stream = self._determine_output_stream(item)
    
    if output_stream in self.send_streams:
        await self.send_streams[output_stream].send(item)
    elif 'default' in self.send_streams:
        await self.send_streams['default'].send(item)
    else:
        self.logger.warning(f"No output stream for item: {item}")

def _determine_output_stream(self, item: Any) -> str:
    """Override to implement custom routing logic"""
    return 'output'  # Default routing
```

## Configuration Patterns

### Variant-Based Configuration
```python
def __init__(self, name: str, config: Dict[str, Any] = None):
    super().__init__(name, config)
    self.variant = self.config.get('variant', 'default')
    
    # Variant-specific initialization
    if self.variant == 'windowing':
        self.window_size = self.config.get('window_size', 5.0)
        self.window_data = deque()
    elif self.variant == 'joining':
        self.join_key = self.config.get('join_key', 'id')
        self.left_buffer = {}
        self.right_buffer = {}
```

### Redis Integration Pattern
```python
def __init__(self, name: str, config: Dict[str, Any] = None):
    super().__init__(name, config)
    # Redis configuration parsing
    self.redis_url = config.get('redis_url')
    if not self.redis_url:
        host = config.get('host', 'localhost')
        port = config.get('port', 6379)
        password = config.get('password', None)
        db = config.get('db', 0)
        
        if password:
            self.redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            self.redis_url = f"redis://{host}:{port}/{db}"

async def setup(self, harness_context=None):
    """Setup with Redis connection"""
    await super().setup(harness_context)
    # Initialize Redis connection
    self.redis_client = await self._connect_redis()

async def _connect_redis(self):
    """Connect to Redis with error handling"""
    try:
        import redis.asyncio as redis
        client = redis.from_url(self.redis_url)
        await client.ping()  # Test connection
        return client
    except Exception as e:
        await self.error_handler.handle_exception(
            e,
            context={"redis_url": self.redis_url},
            operation="redis_connection"
        )
        raise
```

### WebSocket Server Pattern
```python
def __init__(self, name: str, config: Dict[str, Any] = None):
    super().__init__(name, config)
    self.port = config.get('port', 8080)
    self.host = config.get('host', '0.0.0.0')
    self.max_connections = config.get('max_connections', 100)
    self.heartbeat_interval = config.get('heartbeat_interval', 30)
    
    # Connection tracking
    self._connected_clients = set()
    self._server = None
    self._heartbeat_task = None

async def start_server(self):
    """Start WebSocket server"""
    import websockets
    self._server = await websockets.serve(
        self.handle_connection,
        self.host,
        self.port
    )
    self._heartbeat_task = asyncio.create_task(self._send_heartbeat())
```

## Error Handling Patterns

### Comprehensive Error Handling
```python
@handle_errors(component_name="MyComponent", operation="process")
async def process(self) -> None:
    """Main processing with comprehensive error handling"""
    try:
        await self._process_implementation()
    except Exception as e:
        await self.error_handler.handle_exception(
            e,
            context={
                "component": self.name,
                "operation": "main_process",
                "variant": self.variant
            },
            operation="process"
        )
        raise

async def _process_with_item_error_handling(self) -> None:
    """Process with per-item error handling"""
    async for item in self.receive_streams.get('input', []):
        try:
            result = await self.transform_item(item)
            await self._send_result(result)
        except Exception as e:
            # Log error but continue processing other items
            await self.error_handler.handle_exception(
                e,
                context={"item": item, "component": self.name},
                operation="process_item"
            )
            # Optionally send to error stream
            if 'error' in self.send_streams:
                await self.send_streams['error'].send({
                    'error': str(e),
                    'item': item,
                    'timestamp': time.time()
                })
```

### Stream Connection Safety
```python
# Problem: KeyError when accessing streams
async for item in self.receive_streams['input']:  # Crashes if no 'input' stream

# Solution: Use get() with default
async for item in self.receive_streams.get('input', []):  # Safe
```

### Resource Cleanup Pattern
```python
async def cleanup(self) -> None:
    """Proper resource cleanup"""
    try:
        # Close Redis connections
        if hasattr(self, 'redis_client') and self.redis_client:
            await self.redis_client.close()
            
        # Close file handles
        if hasattr(self, 'file_handle') and self.file_handle:
            self.file_handle.close()
            
        # Close output streams when done producing
        for stream in self.send_streams.values():
            try:
                await stream.aclose()
            except Exception as e:
                self.logger.warning(f"Error closing stream: {e}")
                
    finally:
        self._status.is_running = False
        await super().cleanup()
```

## Testing Patterns

### Component Unit Testing
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_component_processing():
    """Test component processing logic"""
    # Setup
    component = MyComponent("test", {"variant": "test_variant"})
    await component.setup()
    
    # Mock streams
    input_stream = AsyncMock()
    output_stream = AsyncMock()
    
    component.receive_streams = {'input': input_stream}
    component.send_streams = {'output': output_stream}
    
    # Test data
    test_items = [{'id': 1, 'data': 'test1'}, {'id': 2, 'data': 'test2'}]
    input_stream.__aiter__.return_value = test_items
    
    # Execute
    await component.process()
    
    # Verify
    assert output_stream.send.call_count == len(test_items)
    
    # Cleanup
    await component.cleanup()

@pytest.mark.asyncio
async def test_component_error_handling():
    """Test component error handling"""
    component = MyComponent("test", {})
    component.transform_item = Mock(side_effect=ValueError("Test error"))
    
    # Should handle error gracefully without crashing
    await component.process()
    
    # Verify error was logged
    assert component.error_handler.handle_exception.called
```

### Integration Testing Pattern
```python
@pytest.mark.asyncio
async def test_component_integration():
    """Test component in system context"""
    from autocoder_cc.components.component_registry import component_registry
    
    # Create component via registry
    component = component_registry.create_component(
        'MyComponent', 
        'test_instance', 
        {'variant': 'production'}
    )
    
    # Test component loads correctly
    assert component.name == 'test_instance'
    assert component.variant == 'production'
    
    # Test setup and cleanup
    await component.setup()
    assert component._status.is_running
    
    await component.cleanup()
    assert not component._status.is_running
```

## Performance Patterns

### Batching Pattern
```python
async def _process_batched(self, batch_size: int = 100) -> None:
    """Process items in batches for efficiency"""
    batch = []
    
    async for item in self.receive_streams.get('input', []):
        batch.append(item)
        
        if len(batch) >= batch_size:
            await self._process_batch(batch)
            batch.clear()
    
    # Process remaining items
    if batch:
        await self._process_batch(batch)

async def _process_batch(self, items: List[Any]) -> None:
    """Process a batch of items efficiently"""
    results = await self._batch_transform(items)
    
    for result in results:
        if 'output' in self.send_streams:
            await self.send_streams['output'].send(result)
```

### Buffering Pattern
```python
def __init__(self, name: str, config: Dict[str, Any] = None):
    super().__init__(name, config)
    self.buffer_size = config.get('buffer_size', 1000)
    self.flush_interval = config.get('flush_interval', 5.0)
    self.buffer = []
    self.last_flush = time.time()

async def _buffered_send(self, item: Any) -> None:
    """Buffer items before sending"""
    self.buffer.append(item)
    
    # Flush if buffer full or time elapsed
    if (len(self.buffer) >= self.buffer_size or 
        time.time() - self.last_flush >= self.flush_interval):
        await self._flush_buffer()

async def _flush_buffer(self) -> None:
    """Flush buffered items"""
    if self.buffer and 'output' in self.send_streams:
        for item in self.buffer:
            await self.send_streams['output'].send(item)
        self.buffer.clear()
        self.last_flush = time.time()
```

## Component Registration Pattern

### Component Registry Integration
```python
# In component file
from autocoder_cc.components.component_registry import component_registry

class MyComponent(Component):
    # Implementation here
    pass

# Register component
component_registry.register("MyComponent", MyComponent)
```

### Factory Pattern for Components
```python
@component_registry.register("ConfigurableComponent")
class ConfigurableComponent(Component):
    @classmethod
    def create_variant(cls, variant: str, name: str, config: Dict[str, Any]):
        """Factory method for creating component variants"""
        if variant == 'processor':
            return ProcessorComponent(name, config)
        elif variant == 'analyzer':
            return AnalyzerComponent(name, config)
        else:
            return cls(name, config)
```

## Common Implementation Issues

### Stream Access Errors
```python
# ❌ WRONG - Can cause KeyError
async for item in self.receive_streams['input']:
    pass

# ✅ CORRECT - Safe access with default
async for item in self.receive_streams.get('input', []):
    pass
```

### Resource Leaks
```python
# ❌ WRONG - May leak resources
async def cleanup(self):
    await self.redis_client.close()  # May fail

# ✅ CORRECT - Proper error handling
async def cleanup(self):
    try:
        if hasattr(self, 'redis_client') and self.redis_client:
            await self.redis_client.close()
    except Exception as e:
        self.logger.warning(f"Cleanup error: {e}")
    finally:
        await super().cleanup()
```

### Error Propagation
```python
# ❌ WRONG - Silently ignores errors
try:
    result = await self.process_item(item)
except Exception:
    pass  # Error lost

# ✅ CORRECT - Proper error handling
try:
    result = await self.process_item(item)
except Exception as e:
    await self.error_handler.handle_exception(e, context={"item": item})
    # Decide whether to re-raise or continue
```

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Production patterns documented  
**Usage**: Follow these patterns for stream-based component development  
**Next**: See component-specific documentation for detailed examples  