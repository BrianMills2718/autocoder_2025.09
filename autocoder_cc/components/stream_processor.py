#!/usr/bin/env python3
"""
StreamProcessor Component - Handles windowing, joining, and deduplication operations
"""

import anyio
import time
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque
from autocoder_cc.orchestration.component import Component
from autocoder_cc.error_handling.consistent_handler import ConsistentErrorHandler, handle_errors
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class StreamProcessor(Component):
    """
    StreamProcessor component for advanced stream operations.
    
    Supports three variants:
    - windowing: Groups items into time-based windows
    - joining: Joins items from two input streams
    - deduplication: Removes duplicate items from stream
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.variant = self.config.get('variant', 'windowing')
        
        # Initialize ConsistentErrorHandler for universal error coverage
        self.error_handler = ConsistentErrorHandler(f"StreamProcessor.{name}")
        
        # Variant-specific state
        if self.variant == 'windowing':
            self.window_size = self.config.get('window_size', 5.0)  # seconds
            self.window_data = deque()
            self.last_window_time = time.time()
            
        elif self.variant == 'joining':
            self.left_buffer = {}  # key -> item
            self.right_buffer = {}  # key -> item
            self.join_key = self.config.get('join_key', 'id')
            
        elif self.variant == 'deduplication':
            self.seen_items: Set[str] = set()
            self.dedup_key = self.config.get('dedup_key', None)  # If None, use entire item
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize StreamProcessor"""
        self.logger.info(f"StreamProcessor '{self.name}' initialized with variant: {self.variant}")
        self._status.is_running = True

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for StreamProcessor component"""
        return [
            ConfigRequirement(
                name="processing_mode",
                type="str",
                description="Mode of stream processing",
                required=True,
                options=["continuous", "batch", "micro_batch"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="checkpoint_interval",
                type="int",
                description="Interval for checkpointing in seconds",
                required=False,
                default=60,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="parallelism",
                type="int",
                description="Number of parallel processing threads",
                required=False,
                default=1,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: x > 0
            )
        ]

    
    @handle_errors(component_name="StreamProcessor", operation="process")
    async def process(self) -> None:
        """Main processing loop based on variant with consistent error handling"""
        if self.variant == 'windowing':
            await self._process_windowing()
        elif self.variant == 'joining':
            await self._process_joining()
        elif self.variant == 'deduplication':
            await self._process_deduplication()
        else:
            error_msg = f"Unknown variant: {self.variant}"
            self.logger.error(error_msg)
            await self.error_handler.handle_exception(
                ValueError(error_msg),
                context={"variant": self.variant, "available_variants": ["windowing", "joining", "deduplication"]},
                operation="process_variant_validation"
            )
    
    async def _process_windowing(self) -> None:
        """Process windowing variant - group items into time windows"""
        self.logger.info("Starting windowing stream processing")
        
        async for item in self.receive_streams.get('input', []):
            try:
                current_time = time.time()
                self.window_data.append((current_time, item))
                
                self.logger.info(f"Received item for windowing: {item}")
                
                # Check if window should be emitted
                if current_time - self.last_window_time >= self.window_size:
                    await self._emit_window()
                    self.last_window_time = current_time
                
                self.increment_processed()
            except Exception as e:
                await self.error_handler.handle_exception(
                    e,
                    context={"item": str(item), "window_size": self.window_size, "window_data_count": len(self.window_data)},
                    operation="windowing_item_processing"
                )
                
        # Emit final window when stream ends
        try:
            if self.window_data:
                await self._emit_window()
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"final_window_data_count": len(self.window_data)},
                operation="windowing_final_window_emission"
            )
    
    async def _emit_window(self) -> None:
        """Emit current window as aggregated result"""
        if not self.window_data:
            return
        
        # Collect all items in current window
        window_items = []
        for timestamp, item in self.window_data:
            window_items.append(item)
        
        if window_items:
            window_result = {
                'window_start': self.last_window_time,
                'window_end': time.time(),
                'items': window_items,
                'count': len(window_items)
            }
            
            self.logger.info(f"Window creation event: emitting window with {len(window_items)} items")
            
            if 'output' in self.send_streams:
                await self.send_streams['output'].send(window_result)
            
            # Clear window data after emission
            self.window_data.clear()
    
    async def _process_joining(self) -> None:
        """Process joining variant - join items from two streams"""
        self.logger.info("Starting joining stream processing")
        
        try:
            # Use task group to process both streams concurrently
            async with anyio.create_task_group() as tg:
                if 'left' in self.receive_streams:
                    tg.start_soon(self._process_left_stream)
                if 'right' in self.receive_streams:
                    tg.start_soon(self._process_right_stream)
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"left_buffer_size": len(self.left_buffer), "right_buffer_size": len(self.right_buffer), "join_key": self.join_key},
                operation="joining_stream_processing"
            )
    
    async def _process_left_stream(self) -> None:
        """Process left stream for joining"""
        async for item in self.receive_streams['left']:
            key = item.get(self.join_key) if isinstance(item, dict) else str(item)
            self.left_buffer[key] = item
            
            self.logger.info(f"Left stream item received: {item}")
            
            # Check for match in right buffer
            if key in self.right_buffer:
                await self._emit_joined_item(key)
            else:
                self.logger.info(f"Left item with key {key} has no match in right stream yet")
            
            self.increment_processed()
    
    async def _process_right_stream(self) -> None:
        """Process right stream for joining"""
        async for item in self.receive_streams['right']:
            key = item.get(self.join_key) if isinstance(item, dict) else str(item)
            self.right_buffer[key] = item
            
            self.logger.info(f"Right stream item received: {item}")
            
            # Check for match in left buffer
            if key in self.left_buffer:
                await self._emit_joined_item(key)
            else:
                self.logger.info(f"Right item with key {key} has no match in left stream yet")
            
            self.increment_processed()
    
    async def _emit_joined_item(self, key: str) -> None:
        """Emit joined item from both streams"""
        left_item = self.left_buffer.pop(key, None)
        right_item = self.right_buffer.pop(key, None)
        
        if left_item is not None and right_item is not None:
            joined_item = {
                'join_key': key,
                'left': left_item,
                'right': right_item,
                'joined_at': time.time()
            }
            
            self.logger.info(f"Emitting joined item: {joined_item}")
            
            if 'output' in self.send_streams:
                await self.send_streams['output'].send(joined_item)
    
    async def _process_deduplication(self) -> None:
        """Process deduplication variant - remove duplicate items"""
        self.logger.info("Starting deduplication stream processing")
        
        async for item in self.receive_streams.get('input', []):
            try:
                # Determine deduplication key
                if self.dedup_key and isinstance(item, dict):
                    dedup_value = str(item.get(self.dedup_key, item))
                else:
                    dedup_value = str(item)
                
                self.logger.info(f"Received item for deduplication: {item}")
                
                # Check if we've seen this item before
                if dedup_value not in self.seen_items:
                    self.seen_items.add(dedup_value)
                    
                    self.logger.info(f"Unique item - sending to output stream: {item}")
                    
                    if 'output' in self.send_streams:
                        await self.send_streams['output'].send(item)
                else:
                    self.logger.info(f"Duplicate item detected - filtering out: {item}")
                
                self.increment_processed()
            except Exception as e:
                await self.error_handler.handle_exception(
                    e,
                    context={"item": str(item), "dedup_key": self.dedup_key, "seen_items_count": len(self.seen_items)},
                    operation="deduplication_item_processing"
                )
    
    async def cleanup(self) -> None:
        """Cleanup StreamProcessor resources"""
        # Emit final window if windowing
        if self.variant == 'windowing' and self.window_data:
            await self._emit_window()
        
        self.logger.info(f"StreamProcessor '{self.name}' cleanup completed")
        self._status.is_running = False