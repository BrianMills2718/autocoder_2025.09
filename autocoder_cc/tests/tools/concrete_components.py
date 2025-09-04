"""Concrete implementations of abstract primitives for testing purposes."""
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from autocoder_cc.components.primitives.base import Source, Sink, Transformer, Splitter, Merger
# Import port classes if they exist
try:
    from autocoder_cc.ports.base import InputPort, OutputPort
    PORTS_AVAILABLE = True
except ImportError:
    PORTS_AVAILABLE = False


# Simple test schemas for ports
class TestMessage(BaseModel):
    """Simple test message schema."""
    id: Optional[int] = None
    value: Optional[str] = None
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class TestableSource(Source[Dict[str, Any]]):
    """Concrete Source implementation for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.test_data = config.get('test_data', [])
        # For testing, we'll use simple handler-based approach instead of ports
        self._output_handler = None
        self.generated_count = 0
        # Add port support if available
        if PORTS_AVAILABLE:
            from autocoder_cc.observability import get_logger
            self.logger = get_logger(f"TestableSource.{name}")
            self.output_port = OutputPort(f"{name}.out")
    
    async def setup(self):
        """Setup component."""
        if hasattr(self, 'logger'):
            self.logger.info(f"Setting up {self.name}")
        
    async def generate(self):
        """Generate test data items."""
        self.logger.info(f"Generating {len(self.test_data)} items")
        for i, item in enumerate(self.test_data):
            self.logger.debug(f"Generated item {i}: {item}")
            await self.emit(item)
            self.generated_count += 1
            # Small delay to prevent overwhelming the system (optimized for performance)
            if self.generated_count % 100 == 0:  # Only sleep every 100 messages
                await asyncio.sleep(0.001)  # Reduced to 1ms
    
    async def emit(self, item: Dict[str, Any]):
        """Emit data through output handler or port."""
        # Try port first if available
        if PORTS_AVAILABLE and hasattr(self, 'output_port'):
            sent = await self.output_port.send(item)
            if sent > 0:
                return
        # Fall back to handler
        if self._output_handler:
            await self._output_handler(item)
            
    def set_output_handler(self, handler):
        """Set handler for output data."""
        self._output_handler = handler
    
    async def cleanup(self):
        """Cleanup component."""
        if PORTS_AVAILABLE and hasattr(self, 'output_port'):
            self.output_port.disconnect()
            self.logger.info(f"Cleaned up {self.name}")


class TestableSink(Sink[Dict[str, Any]]):
    """Concrete Sink implementation for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.received_messages: List[Dict[str, Any]] = []
        # Add port support if available
        if PORTS_AVAILABLE:
            from autocoder_cc.observability import get_logger
            self.logger = get_logger(f"TestableSink.{name}")
            self.input_port = InputPort(f"{name}.in")
            # Don't set handler - we'll use the consume loop instead
        
    async def setup(self):
        """Setup component."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            self.logger.info(f"Setting up {self.name}")
            # Start consume loop for port
            asyncio.create_task(self._consume_loop())
    
    async def _consume_loop(self):
        """Continuously consume messages from input port."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            while True:
                try:
                    message = await self.input_port.receive()
                    if message:
                        await self.consume(message)
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    self.logger.error(f"Consume loop error: {e}")
                    await asyncio.sleep(0.1)
    
    async def consume(self, item: Dict[str, Any]) -> None:
        """Consume a data item."""
        if hasattr(self, 'logger'):
            self.logger.debug(f"Consumed item: {item}")
        self.received_messages.append(item.copy())
        
        # Apply any sink-specific processing
        if 'transform_on_consume' in self.config:
            item['sink_processed'] = True
            item['sink_timestamp'] = asyncio.get_event_loop().time()
    
    async def cleanup(self):
        """Cleanup component."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            self.input_port.disconnect()
            self.logger.info(f"Cleaned up {self.name}")


class TestableTransformer(Transformer[Dict[str, Any], Dict[str, Any]]):
    """Concrete Transformer implementation for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.transform_rule = config.get('transform_rule', 'passthrough')
        self.processed_count = 0
        self._output_handler = None
        # Add port support if available
        if PORTS_AVAILABLE:
            from autocoder_cc.observability import get_logger
            self.logger = get_logger(f"TestableTransformer.{name}")
            self.input_port = InputPort(f"{name}.in")
            self.output_port = OutputPort(f"{name}.out")
            # Don't set handler - we'll use the process loop instead
        
    async def transform(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform an item based on configured rule."""
        if hasattr(self, 'logger'):
            self.logger.debug(f"Transforming item: {item}")
        
        # Apply transformation based on rule
        if self.transform_rule == 'passthrough':
            result = item.copy()
            result['transformed_by'] = self.name
            
        elif self.transform_rule == 'double':
            # Double numeric values
            result = item.copy()
            if 'value' in result:
                result['value'] = result.get('value', 0) * 2
            result['transformed_by'] = self.name
            
        elif self.transform_rule == 'uppercase':
            # Uppercase string values
            result = item.copy()
            if 'message' in result:
                result['message'] = result['message'].upper()
            result['transformed_by'] = self.name
            
        elif self.transform_rule == 'uppercase_values':
            result = {}
            for key, value in item.items():
                if isinstance(value, str):
                    result[key] = value.upper()
                else:
                    result[key] = value
            result['transformed_by'] = self.name
            
        elif self.transform_rule == 'add_metadata':
            result = item.copy()
            result['metadata'] = {
                'transformed_by': self.name,
                'processed_at': asyncio.get_event_loop().time(),
                'original_keys': list(item.keys())
            }
            
        elif self.transform_rule == 'filter_numeric':
            # Filter out non-numeric values, return None if no numeric values
            result = {k: v for k, v in item.items() if isinstance(v, (int, float))}
            if not result:
                return None  # Drop the item
            result['transformed_by'] = self.name
            
        else:
            # Default passthrough
            result = item.copy()
            result['transformed_by'] = self.name
            
        self.processed_count += 1
        return result
        
    def set_output_handler(self, handler):
        """Set handler for output data."""
        self._output_handler = handler
        
    async def setup(self):
        """Setup component."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            self.logger.info(f"Setting up {self.name}")
            # Start processing loop
            asyncio.create_task(self._process_loop())
    
    async def _process_loop(self):
        """Continuously process messages from input port."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            while True:
                try:
                    message = await self.input_port.receive()
                    if message:
                        await self.process(message)
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    self.logger.error(f"Process loop error: {e}")
                    await asyncio.sleep(0.1)
    
    async def process(self, item: Dict[str, Any]):
        """Process item through transformation and emit result."""
        result = await self.transform(item)
        if result is not None:
            # Try port first if available
            if PORTS_AVAILABLE and hasattr(self, 'output_port'):
                await self.output_port.send(result)
            # Also use handler if set
            elif self._output_handler:
                await self._output_handler(result)
    
    async def cleanup(self):
        """Cleanup component."""
        if PORTS_AVAILABLE and hasattr(self, 'input_port'):
            self.input_port.disconnect()
            self.output_port.disconnect()
            self.logger.info(f"Cleaned up {self.name}")


class TestableSplitter(Splitter[Dict[str, Any]]):
    """Concrete Splitter implementation for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.split_rule = config.get('split_rule', 'round_robin')
        self.split_count = 0
        self._output_handlers = {}
        
    async def split(self, item: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Split input to multiple outputs."""
        self.logger.debug(f"Splitting item: {item}")
        
        if self.split_rule == 'round_robin':
            # Alternate between left and right
            target = 'left' if self.split_count % 2 == 0 else 'right'
            result = {target: item.copy()}
            
        elif self.split_rule == 'by_type':
            # Split based on 'type' field
            item_type = item.get('type', 'unknown')
            if item_type in ['user', 'customer']:
                result = {'left': item.copy()}
            elif item_type in ['admin', 'system']:
                result = {'right': item.copy()}
            else:
                result = {'default': item.copy()}
                
        elif self.split_rule == 'duplicate':
            # Send to both outputs
            result = {
                'left': item.copy(),
                'right': item.copy()
            }
            
        else:
            # Default to left output
            result = {'left': item.copy()}
            
        # Add split metadata
        for output_item in result.values():
            output_item['split_by'] = self.name
            output_item['split_rule'] = self.split_rule
            
        self.split_count += 1
        return result


class TestableMerger(Merger[Dict[str, Any]]):
    """Concrete Merger implementation for testing."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.merge_rule = config.get('merge_rule', 'combine_fields')
        self.merge_count = 0
        self._output_handler = None
        
    async def merge(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple inputs into single output."""
        self.logger.debug(f"Merging {len(items)} items")
        
        if not items:
            return {}
            
        if len(items) == 1:
            result = items[0].copy()
            result['merged_by'] = self.name
            return result
            
        if self.merge_rule == 'combine_fields':
            # Merge all fields, later items override earlier ones
            result = {}
            for item in items:
                result.update(item)
            result['merged_by'] = self.name
            result['merge_sources'] = len(items)
            
        elif self.merge_rule == 'concatenate_values':
            # Concatenate string values, sum numeric values
            result = {}
            for item in items:
                for key, value in item.items():
                    if key in result:
                        if isinstance(result[key], str) and isinstance(value, str):
                            result[key] = result[key] + " " + value
                        elif isinstance(result[key], (int, float)) and isinstance(value, (int, float)):
                            result[key] = result[key] + value
                        else:
                            result[key] = value  # Override with latest
                    else:
                        result[key] = value
            result['merged_by'] = self.name
            
        elif self.merge_rule == 'first_wins':
            # First item wins conflicts
            result = items[0].copy()
            for item in items[1:]:
                for key, value in item.items():
                    if key not in result:
                        result[key] = value
            result['merged_by'] = self.name
            
        else:
            # Default combine fields
            result = {}
            for item in items:
                result.update(item)
            result['merged_by'] = self.name
            
        self.merge_count += 1
        return result


# Helper functions for creating test components
def create_test_source(name: str, test_data: List[Dict[str, Any]]) -> TestableSource:
    """Create a test source with predefined data."""
    return TestableSource(name, {'test_data': test_data})


def create_test_transformer(name: str, rule: str = 'passthrough') -> TestableTransformer:
    """Create a test transformer with specified rule."""
    return TestableTransformer(name, {'transform_rule': rule})


def create_test_sink(name: str) -> TestableSink:
    """Create a test sink."""
    return TestableSink(name, {})


def create_test_splitter(name: str, rule: str = 'round_robin') -> TestableSplitter:
    """Create a test splitter with specified rule."""
    return TestableSplitter(name, {'split_rule': rule})


def create_test_merger(name: str, rule: str = 'combine_fields') -> TestableMerger:
    """Create a test merger with specified rule."""
    return TestableMerger(name, {'merge_rule': rule})