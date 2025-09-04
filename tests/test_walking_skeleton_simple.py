#!/usr/bin/env python3
"""
Simple Walking Skeleton Test - Demonstrates basic port-based pipeline.

A simpler test with just: Source → Transformer → Sink
"""
import anyio
import signal
import sys
from pathlib import Path
from typing import Dict, Any
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cc.components.primitives import Source, Sink, Transformer


class TestSource(Source):
    """Source that generates test messages."""
    
    async def _generate_message(self, index: int) -> Dict[str, Any]:
        """Generate a simple test message."""
        return {
            "index": index,
            "source": self.name,
            "timestamp": time.time(),
            "data": f"message_{index}"
        }


class TestTransformer(Transformer):
    """Transformer that adds processing info."""
    
    async def transform(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform by adding processing info."""
        # Drop every 10th message to test drop handling
        if message.get('index', 0) % 10 == 0:
            return None  # Drop
        
        # Transform the message
        message['processed'] = True
        message['processed_at'] = time.time()
        message['value_doubled'] = message.get('index', 0) * 2
        return message


class TestSink(Sink):
    """Sink that collects received messages."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.messages_received = []
    
    async def _process_message(self, message: Dict[str, Any], source: str):
        """Process and store received message."""
        self.messages_received.append(message)
        if len(self.messages_received) % 100 == 0:
            self.logger.info(f"Received {len(self.messages_received)} messages")


async def run_simple_pipeline():
    """Run a simple 3-component pipeline."""
    print("🚀 Starting simple walking skeleton test...")
    
    # Create components
    source = TestSource('test_source', {
        'generate_count': 1000,  # 1000 messages as per plan
        'delay': 0.001  # 1ms between messages
    })
    
    transformer = TestTransformer('test_transformer', {
        'require_output': False  # Allow dropping
    })
    
    sink = TestSink('test_sink', {})
    
    # Wire components together using simple stream connections
    # We'll use anyio memory object streams directly for simplicity
    from anyio import create_memory_object_stream
    
    # Source → Transformer
    source_to_transformer_send, source_to_transformer_recv = create_memory_object_stream(50)
    
    # Transformer → Sink  
    transformer_to_sink_send, transformer_to_sink_recv = create_memory_object_stream(50)
    
    # Override process methods to use the streams
    async def source_process():
        """Custom source process that sends to stream."""
        count = source.config.get('generate_count', 10)
        delay = source.config.get('delay', 0.1)
        
        for i in range(count):
            message = await source._generate_message(i)
            await source_to_transformer_send.send(message)
            if delay > 0:
                await anyio.sleep(delay)
        await source_to_transformer_send.aclose()
        source.logger.info(f"Generated {count} messages")
    
    async def transformer_process():
        """Custom transformer process using streams."""
        count_in = 0
        count_out = 0
        count_dropped = 0
        
        async for message in source_to_transformer_recv:
            count_in += 1
            transformed = await transformer.transform(message)
            if transformed is not None:
                await transformer_to_sink_send.send(transformed)
                count_out += 1
            else:
                count_dropped += 1
        
        await transformer_to_sink_send.aclose()
        transformer.logger.info(
            f"Processed {count_in} messages: "
            f"{count_out} passed, {count_dropped} dropped"
        )
    
    async def sink_process():
        """Custom sink process using streams."""
        async for message in transformer_to_sink_recv:
            await sink._process_message(message, "transformer")
        sink.logger.info(f"Received {len(sink.messages_received)} messages total")
    
    # Run all components
    start_time = time.time()
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(source_process)
        tg.start_soon(transformer_process)
        tg.start_soon(sink_process)
    
    elapsed = time.time() - start_time
    
    # Print results
    print("\n📊 Simple Walking Skeleton Results:")
    print(f"   ⏱️  Execution time: {elapsed:.2f} seconds")
    print(f"   📤 Messages generated: {source.config['generate_count']}")
    print(f"   📥 Messages received: {len(sink.messages_received)}")
    
    # Expected: 1000 generated, 100 dropped (every 10th), 900 received
    expected_received = 900
    if len(sink.messages_received) == expected_received:
        print(f"   ✅ Correct count: {expected_received} messages received")
        print("\n✅ Simple walking skeleton test PASSED!")
        return True
    else:
        print(f"   ❌ Expected {expected_received}, got {len(sink.messages_received)}")
        print("\n❌ Simple walking skeleton test FAILED!")
        return False


async def main():
    """Main entry point."""
    try:
        success = await run_simple_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)