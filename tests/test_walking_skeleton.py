#!/usr/bin/env python3
"""
Walking Skeleton Test - Demonstrates port-based architecture end-to-end.

This test creates a simple pipeline using the 5 mathematical primitives:
Source → Transformer → Splitter → Merger → Sink

Success Criteria (from plan):
- 1000 messages total processed
- 0 messages dropped
- Clean SIGTERM handling
"""
import anyio
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autocoder_cc.components.primitives import (
    Source, Sink, Transformer, Splitter, Merger
)
from autocoder_cc.components.ports import Port, create_port_pair


class MessageCounter:
    """Helper to track message counts."""
    def __init__(self):
        self.sent = 0
        self.received = 0
        self.dropped = 0
        self.transformed = 0
        self.split = 0
        self.merged = 0


class CountingSource(Source):
    """Source that counts messages sent."""
    def __init__(self, name: str, config: Dict[str, Any], counter: MessageCounter):
        super().__init__(name, config)
        self.counter = counter
    
    async def _generate_message(self, index: int) -> Dict[str, Any]:
        """Generate a message with tracking."""
        message = await super()._generate_message(index)
        self.counter.sent += 1
        return message


class FilteringTransformer(Transformer):
    """Transformer that filters even numbers."""
    def __init__(self, name: str, config: Dict[str, Any], counter: MessageCounter):
        super().__init__(name, config)
        self.counter = counter
    
    async def transform(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform and optionally drop messages."""
        index = message.get('index', 0)
        
        # Drop every 10th message to test drop handling
        if index % 10 == 0:
            self.counter.dropped += 1
            return None  # Drop message
        
        # Transform the message
        message['transformed'] = True
        message['doubled'] = index * 2
        self.counter.transformed += 1
        return message


class CountingSplitter(Splitter):
    """Splitter that counts messages split."""
    def __init__(self, name: str, config: Dict[str, Any], counter: MessageCounter):
        super().__init__(name, config)
        self.counter = counter
    
    async def _broadcast_message(self, message: Dict[str, Any]):
        """Count messages being split."""
        await super()._broadcast_message(message)
        self.counter.split += 1


class CountingMerger(Merger):
    """Merger that counts messages merged."""
    def __init__(self, name: str, config: Dict[str, Any], counter: MessageCounter):
        super().__init__(name, config)
        self.counter = counter
    
    def _get_fifo_message(self) -> Dict[str, Any]:
        """Count messages being merged."""
        message = super()._get_fifo_message()
        if message:
            self.counter.merged += 1
        return message


class CountingSink(Sink):
    """Sink that counts messages received."""
    def __init__(self, name: str, config: Dict[str, Any], counter: MessageCounter):
        super().__init__(name, config)
        self.counter = counter
    
    async def _process_message(self, message: Dict[str, Any], source: str):
        """Count received messages."""
        await super()._process_message(message, source)
        self.counter.received += 1


async def create_pipeline(message_count: int = 1000) -> MessageCounter:
    """Create and run the walking skeleton pipeline."""
    counter = MessageCounter()
    
    # Create components
    source = CountingSource('source', {
        'generate_count': message_count,
        'delay': 0.001  # 1ms delay between messages
    }, counter)
    
    transformer = FilteringTransformer('transformer', {
        'require_output': False  # Allow dropping
    }, counter)
    
    splitter = CountingSplitter('splitter', {
        'routing_mode': 'broadcast'
    }, counter)
    
    merger = CountingMerger('merger', {
        'merge_strategy': 'fifo',
        'buffer_size': 100
    }, counter)
    
    sink = CountingSink('sink', {}, counter)
    
    # Create ports and connect components
    # Source → Transformer
    source_to_transformer_send, source_to_transformer_recv = create_port_pair(
        "source_to_transformer", dict, buffer_size=100
    )
    source.output_ports['out'] = source_to_transformer_send
    transformer.input_ports['in'] = source_to_transformer_recv
    
    # Transformer → Splitter
    transformer_to_splitter_send, transformer_to_splitter_recv = create_port_pair(
        "transformer_to_splitter", dict, buffer_size=100
    )
    transformer.output_ports['out'] = transformer_to_splitter_send
    splitter.input_ports['in'] = transformer_to_splitter_recv
    
    # Splitter → Merger (2 paths for testing)
    splitter_to_merger_1_send, splitter_to_merger_1_recv = create_port_pair(
        "splitter_to_merger_1", dict, buffer_size=100
    )
    splitter_to_merger_2_send, splitter_to_merger_2_recv = create_port_pair(
        "splitter_to_merger_2", dict, buffer_size=100
    )
    splitter.output_ports['out1'] = splitter_to_merger_1_send
    splitter.output_ports['out2'] = splitter_to_merger_2_send
    merger.input_ports['in1'] = splitter_to_merger_1_recv
    merger.input_ports['in2'] = splitter_to_merger_2_recv
    
    # Merger → Sink
    merger_to_sink_send, merger_to_sink_recv = create_port_pair(
        "merger_to_sink", dict, buffer_size=100
    )
    merger.output_ports['out'] = merger_to_sink_send
    sink.input_ports['in'] = merger_to_sink_recv
    
    # Setup signal handler for clean shutdown
    shutdown_event = anyio.Event()
    
    def signal_handler(signum, frame):
        print(f"\n📍 Received signal {signum}, shutting down gracefully...")
        shutdown_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run all components concurrently
    print("🚀 Starting walking skeleton pipeline...")
    print(f"   Generating {message_count} messages")
    
    start_time = time.time()
    
    async with anyio.create_task_group() as tg:
        # Start all components
        tg.start_soon(source.run)
        tg.start_soon(transformer.run)
        tg.start_soon(splitter.run)
        tg.start_soon(merger.run)
        tg.start_soon(sink.run)
        
        # Monitor for shutdown
        async def monitor_shutdown():
            await shutdown_event.wait()
            print("⏹️  Initiating shutdown...")
            # Cleanup will happen when task group exits
        
        tg.start_soon(monitor_shutdown)
    
    elapsed_time = time.time() - start_time
    
    # Print results
    print("\n📊 Walking Skeleton Results:")
    print(f"   ⏱️  Execution time: {elapsed_time:.2f} seconds")
    print(f"   📤 Messages sent: {counter.sent}")
    print(f"   🔄 Messages transformed: {counter.transformed}")
    print(f"   ❌ Messages dropped: {counter.dropped}")
    print(f"   📡 Messages split: {counter.split}")
    print(f"   🔀 Messages merged: {counter.merged}")
    print(f"   📥 Messages received: {counter.received}")
    print(f"   📈 Throughput: {counter.sent / elapsed_time:.0f} msg/sec")
    
    # Verify success criteria
    success = True
    if counter.sent != message_count:
        print(f"   ⚠️  Expected {message_count} messages sent, got {counter.sent}")
        success = False
    
    expected_dropped = message_count // 10  # We drop every 10th message
    if counter.dropped != expected_dropped:
        print(f"   ⚠️  Expected {expected_dropped} messages dropped, got {counter.dropped}")
        success = False
    
    # Account for splits (each non-dropped message goes to 2 outputs)
    expected_received = (counter.sent - counter.dropped) * 2
    if counter.received != expected_received:
        print(f"   ⚠️  Expected {expected_received} messages received, got {counter.received}")
        success = False
    
    if success:
        print("\n✅ Walking skeleton test PASSED!")
        print("   - Port-based architecture working end-to-end")
        print("   - All primitives functioning correctly")
        print("   - Message flow and counting accurate")
    else:
        print("\n❌ Walking skeleton test FAILED - see warnings above")
    
    return counter


async def main():
    """Run the walking skeleton test."""
    try:
        # Run with 1000 messages as specified in plan
        counter = await create_pipeline(1000)
        
        # Exit with appropriate code
        expected_dropped = 100  # 1000 / 10
        expected_received = (1000 - expected_dropped) * 2  # Split to 2 paths
        
        if (counter.sent == 1000 and 
            counter.dropped == expected_dropped and
            counter.received == expected_received):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)