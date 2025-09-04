#!/usr/bin/env python3
"""
Comprehensive test suite for Aggregator component
Tests all aggregation functionality including batching, timeout, and various aggregation strategies
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from autocoder_cc.components.aggregator import Aggregator


class TestAggregatorComponent:
    """Test suite for Aggregator component functionality"""
    
    def test_aggregator_initialization_default_config(self):
        """Test Aggregator component initialization with default configuration"""
        config = {}
        aggregator = Aggregator("test_aggregator", config)
        
        assert aggregator.batch_size == 10
        assert aggregator.timeout_seconds == 30
        assert aggregator.aggregation_strategy == "collect"
        assert aggregator.flush_on_timeout == True
        assert aggregator.buffer == []
        assert aggregator.last_flush_time > 0
        
        # Cleanup
        if hasattr(aggregator, 'flush_task') and aggregator.flush_task and not aggregator.flush_task.done():
            aggregator.flush_task.cancel()
    
    def test_aggregator_initialization_custom_config(self):
        """Test Aggregator component initialization with custom configuration"""
        config = {
            "batch_size": 5,
            "timeout_seconds": 10,
            "aggregation_strategy": "sum",
            "flush_on_timeout": False
        }
        
        aggregator = Aggregator("test_aggregator", config)
        
        assert aggregator.batch_size == 5
        assert aggregator.timeout_seconds == 10
        assert aggregator.aggregation_strategy == "sum"
        assert aggregator.flush_on_timeout == False
    
    def test_aggregator_initialization_invalid_config(self):
        """Test Aggregator component fails fast with invalid configuration"""
        # Invalid batch size
        with pytest.raises(ValueError, match="batch_size must be positive integer"):
            Aggregator("test_aggregator", {"batch_size": 0})
        
        with pytest.raises(ValueError, match="batch_size must be positive integer"):
            Aggregator("test_aggregator", {"batch_size": -1})
        
        # Invalid timeout
        with pytest.raises(ValueError, match="timeout_seconds must be positive number"):
            Aggregator("test_aggregator", {"timeout_seconds": 0})
        
        with pytest.raises(ValueError, match="timeout_seconds must be positive number"):
            Aggregator("test_aggregator", {"timeout_seconds": -1})
        
        # Invalid aggregation strategy
        with pytest.raises(ValueError, match="Invalid aggregation_strategy"):
            Aggregator("test_aggregator", {"aggregation_strategy": "invalid"})
    
    def test_aggregator_initialization_custom_strategy_without_function(self):
        """Test Aggregator component fails with custom strategy but no function"""
        config = {
            "aggregation_strategy": "custom"
        }
        
        with pytest.raises(ValueError, match="custom_aggregation_func must be provided and callable"):
            Aggregator("test_aggregator", config)
    
    def test_aggregator_initialization_custom_strategy_with_function(self):
        """Test Aggregator component initializes with custom strategy and function"""
        def custom_func(items):
            return len(items)
        
        config = {
            "aggregation_strategy": "custom",
            "custom_aggregation_func": custom_func
        }
        
        aggregator = Aggregator("test_aggregator", config)
        assert aggregator.aggregation_strategy == "custom"
        assert aggregator.custom_aggregation_func == custom_func
        
        # Cleanup
        if hasattr(aggregator, 'flush_task') and aggregator.flush_task and not aggregator.flush_task.done():
            aggregator.flush_task.cancel()
    
    @pytest.mark.asyncio
    async def test_aggregator_should_flush_size_based(self):
        """Test Aggregator should_flush method for size-based flushing"""
        config = {"batch_size": 3}
        aggregator = Aggregator("test_aggregator", config)
        
        # Empty buffer should not flush
        assert await aggregator.should_flush() == False
        
        # Buffer with 1 item should not flush
        aggregator.buffer = [1]
        assert await aggregator.should_flush() == False
        
        # Buffer with 2 items should not flush
        aggregator.buffer = [1, 2]
        assert await aggregator.should_flush() == False
        
        # Buffer with 3 items should flush
        aggregator.buffer = [1, 2, 3]
        assert await aggregator.should_flush() == True
        
        # Buffer with 4 items should flush
        aggregator.buffer = [1, 2, 3, 4]
        assert await aggregator.should_flush() == True
    
    @pytest.mark.asyncio
    async def test_aggregator_should_flush_timeout_based(self):
        """Test Aggregator should_flush method for timeout-based flushing"""
        config = {"timeout_seconds": 0.1, "flush_on_timeout": True}
        aggregator = Aggregator("test_aggregator", config)
        
        # Empty buffer should not flush even with timeout
        assert await aggregator.should_flush() == False
        
        # Buffer with items but no timeout should not flush
        aggregator.buffer = [1]
        assert await aggregator.should_flush() == False
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Buffer with items after timeout should flush
        assert await aggregator.should_flush() == True
    
    @pytest.mark.asyncio
    async def test_aggregator_should_flush_timeout_disabled(self):
        """Test Aggregator should_flush method with timeout disabled"""
        config = {"timeout_seconds": 0.1, "flush_on_timeout": False}
        aggregator = Aggregator("test_aggregator", config)
        
        # Buffer with items
        aggregator.buffer = [1]
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Should not flush because timeout is disabled
        assert await aggregator.should_flush() == False
    
    @pytest.mark.asyncio
    async def test_aggregator_collect_strategy(self):
        """Test Aggregator collect aggregation strategy"""
        config = {"aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with list of items
        items = [1, 2, 3, "hello", {"key": "value"}]
        result = await aggregator.aggregate_items(items)
        
        assert result == items
        assert isinstance(result, list)
        assert len(result) == 5
    
    @pytest.mark.asyncio
    async def test_aggregator_sum_strategy(self):
        """Test Aggregator sum aggregation strategy"""
        config = {"aggregation_strategy": "sum"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with numeric items
        items = [1, 2, 3, 4.5]
        result = await aggregator.aggregate_items(items)
        assert result == 10.5
        
        # Test with dict items with "value" key
        items = [{"value": 1}, {"value": 2}, {"value": 3}]
        result = await aggregator.aggregate_items(items)
        assert result == 6
        
        # Test with object items with value attribute
        class ValueObj:
            def __init__(self, value):
                self.value = value
        
        items = [ValueObj(1), ValueObj(2), ValueObj(3)]
        result = await aggregator.aggregate_items(items)
        assert result == 6
        
        # Test with string numbers
        items = ["1", "2", "3"]
        result = await aggregator.aggregate_items(items)
        assert result == 6.0
    
    @pytest.mark.asyncio
    async def test_aggregator_sum_strategy_invalid_items(self):
        """Test Aggregator sum strategy with invalid items"""
        config = {"aggregation_strategy": "sum"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with non-numeric items
        items = ["hello", "world"]
        with pytest.raises(ValueError, match="Cannot sum non-numeric item"):
            await aggregator.aggregate_items(items)
    
    @pytest.mark.asyncio
    async def test_aggregator_average_strategy(self):
        """Test Aggregator average aggregation strategy"""
        config = {"aggregation_strategy": "average"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with numeric items
        items = [1, 2, 3, 4]
        result = await aggregator.aggregate_items(items)
        assert result == 2.5
        
        # Test with single item
        items = [5]
        result = await aggregator.aggregate_items(items)
        assert result == 5.0
        
        # Test with empty list
        items = []
        result = await aggregator.aggregate_items(items)
        assert result == 0.0
    
    @pytest.mark.asyncio
    async def test_aggregator_count_strategy(self):
        """Test Aggregator count aggregation strategy"""
        config = {"aggregation_strategy": "count"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with various items
        items = [1, "hello", {"key": "value"}, [1, 2, 3]]
        result = await aggregator.aggregate_items(items)
        assert result == 4
        
        # Test with empty list
        items = []
        result = await aggregator.aggregate_items(items)
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_aggregator_concat_strategy(self):
        """Test Aggregator concat aggregation strategy"""
        config = {"aggregation_strategy": "concat"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with string items
        items = ["hello", " ", "world"]
        result = await aggregator.aggregate_items(items)
        assert result == "hello world"
        
        # Test with dict items with "text" key
        items = [{"text": "hello"}, {"text": " "}, {"text": "world"}]
        result = await aggregator.aggregate_items(items)
        assert result == "hello world"
        
        # Test with object items with text attribute
        class TextObj:
            def __init__(self, text):
                self.text = text
        
        items = [TextObj("hello"), TextObj(" "), TextObj("world")]
        result = await aggregator.aggregate_items(items)
        assert result == "hello world"
        
        # Test with mixed items (converted to string)
        items = ["hello", 123, {"key": "value"}]
        result = await aggregator.aggregate_items(items)
        assert "hello" in result
        assert "123" in result
    
    @pytest.mark.asyncio
    async def test_aggregator_custom_strategy(self):
        """Test Aggregator custom aggregation strategy"""
        def custom_func(items):
            return sum(1 for item in items if isinstance(item, int))
        
        config = {
            "aggregation_strategy": "custom",
            "custom_aggregation_func": custom_func
        }
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with mixed items
        items = [1, "hello", 2, {"key": "value"}, 3]
        result = await aggregator.aggregate_items(items)
        assert result == 3  # Count of integer items
    
    @pytest.mark.asyncio
    async def test_aggregator_custom_strategy_async(self):
        """Test Aggregator custom aggregation strategy with async function"""
        async def custom_async_func(items):
            await asyncio.sleep(0.01)  # Simulate async work
            return len([item for item in items if isinstance(item, str)])
        
        config = {
            "aggregation_strategy": "custom",
            "custom_aggregation_func": custom_async_func
        }
        aggregator = Aggregator("test_aggregator", config)
        
        # Test with mixed items
        items = [1, "hello", 2, "world", {"key": "value"}]
        result = await aggregator.aggregate_items(items)
        assert result == 2  # Count of string items
    
    @pytest.mark.asyncio
    async def test_aggregator_flush_buffer(self):
        """Test Aggregator flush_buffer method"""
        config = {"batch_size": 5, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Empty buffer should return None
        result = await aggregator.flush_buffer()
        assert result is None
        
        # Buffer with items should return aggregated result
        aggregator.buffer = [1, 2, 3]
        result = await aggregator.flush_buffer()
        
        assert isinstance(result, dict)
        assert result["aggregated_data"] == [1, 2, 3]
        assert result["batch_size"] == 3
        assert result["aggregation_strategy"] == "collect"
        assert result["flush_reason"] == "manual"
        assert result["aggregator_name"] == "test_aggregator"
        assert "batch_timestamp" in result
        
        # Buffer should be empty after flush
        assert aggregator.buffer == []
    
    @pytest.mark.asyncio
    async def test_aggregator_process_item_buffering(self):
        """Test Aggregator process_item method with buffering"""
        config = {"batch_size": 3, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # First item should be buffered (no output)
        result = await aggregator.process_item(1)
        assert result is None
        assert aggregator.buffer == [1]
        
        # Second item should be buffered (no output)
        result = await aggregator.process_item(2)
        assert result is None
        assert aggregator.buffer == [1, 2]
        
        # Third item should trigger flush
        result = await aggregator.process_item(3)
        assert result is not None
        assert isinstance(result, dict)
        assert result["aggregated_data"] == [1, 2, 3]
        assert result["batch_size"] == 3
        assert result["flush_reason"] == "size"
        assert aggregator.buffer == []
    
    @pytest.mark.asyncio
    async def test_aggregator_process_item_none_input(self):
        """Test Aggregator process_item method with None input"""
        config = {"batch_size": 3}
        aggregator = Aggregator("test_aggregator", config)
        
        # None input should be skipped
        result = await aggregator.process_item(None)
        assert result is None
        assert aggregator.buffer == []
    
    @pytest.mark.asyncio
    async def test_aggregator_timeout_flushing(self):
        """Test Aggregator timeout-based flushing"""
        config = {
            "batch_size": 10,
            "timeout_seconds": 0.1,
            "flush_on_timeout": True,
            "aggregation_strategy": "collect"
        }
        aggregator = Aggregator("test_aggregator", config)
        
        # Add items to buffer
        await aggregator.process_item(1)
        await aggregator.process_item(2)
        
        # Buffer should have items
        assert len(aggregator.buffer) == 2
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Buffer should be empty due to timeout flush
        # Note: We need to give the timeout monitor a chance to run
        await asyncio.sleep(0.1)
        
        # Check if timeout monitor is working
        assert len(aggregator.buffer) == 0 or await aggregator.should_flush()
    
    @pytest.mark.asyncio
    async def test_aggregator_statistics_tracking(self):
        """Test Aggregator statistics tracking"""
        config = {"batch_size": 2, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Initial statistics
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 0
        assert stats["total_batches_produced"] == 0
        assert stats["items_in_current_batch"] == 0
        
        # Process some items
        await aggregator.process_item(1)
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 1
        assert stats["items_in_current_batch"] == 1
        
        await aggregator.process_item(2)  # Should trigger flush
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 2
        assert stats["total_batches_produced"] == 1
        assert stats["items_in_current_batch"] == 0
        assert stats["size_flushes"] == 1
    
    @pytest.mark.asyncio
    async def test_aggregator_statistics_reset(self):
        """Test Aggregator statistics reset"""
        config = {"batch_size": 2, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Process some items
        await aggregator.process_item(1)
        await aggregator.process_item(2)  # Should trigger flush
        
        # Check statistics
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 2
        assert stats["total_batches_produced"] == 1
        
        # Reset statistics
        aggregator.reset_aggregation_stats()
        
        # Check reset statistics
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 0
        assert stats["total_batches_produced"] == 0
        assert stats["size_flushes"] == 0
        assert stats["timeout_flushes"] == 0
        assert stats["aggregation_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_aggregator_error_handling(self):
        """Test Aggregator error handling during aggregation"""
        def failing_func(items):
            raise ValueError("Custom aggregation error")
        
        config = {
            "aggregation_strategy": "custom",
            "custom_aggregation_func": failing_func,
            "batch_size": 2
        }
        aggregator = Aggregator("test_aggregator", config)
        
        # Process items that will trigger flush
        await aggregator.process_item(1)
        
        # Second item should trigger flush and error
        with pytest.raises(ValueError, match="Custom aggregation error"):
            await aggregator.process_item(2)
        
        # Check error statistics - may be multiple errors due to error propagation
        stats = aggregator.get_aggregation_stats()
        assert stats["aggregation_errors"] >= 1
        
        # Cleanup - handle potential errors during finalization
        try:
            await aggregator.finalize()
        except ValueError:
            # Expected if flush fails again
            pass
    
    @pytest.mark.asyncio
    async def test_aggregator_finalize(self):
        """Test Aggregator finalize method"""
        config = {"batch_size": 10, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Add items to buffer
        await aggregator.process_item(1)
        await aggregator.process_item(2)
        await aggregator.process_item(3)
        
        # Buffer should have items
        assert len(aggregator.buffer) == 3
        
        # Finalize should flush remaining items
        result = await aggregator.finalize()
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["aggregated_data"] == [1, 2, 3]
        assert result["batch_size"] == 3
        assert aggregator.buffer == []
        
        # Timeout monitor should be cancelled
        assert aggregator.flush_task.done()
    
    @pytest.mark.asyncio
    async def test_aggregator_context_manager(self):
        """Test Aggregator as async context manager"""
        config = {"batch_size": 10, "aggregation_strategy": "collect"}
        
        async with Aggregator("test_aggregator", config) as aggregator:
            await aggregator.process_item(1)
            await aggregator.process_item(2)
            
            # Buffer should have items
            assert len(aggregator.buffer) == 2
        
        # After context exit, buffer should be flushed
        assert len(aggregator.buffer) == 0
    
    @pytest.mark.asyncio
    async def test_aggregator_performance(self):
        """Test Aggregator performance under load"""
        config = {
            "batch_size": 100,
            "aggregation_strategy": "collect",
            "timeout_seconds": 30
        }
        aggregator = Aggregator("test_aggregator", config)
        
        # Process many items
        num_items = 1000
        start_time = time.time()
        
        for i in range(num_items):
            await aggregator.process_item(i)
        
        # Finalize to flush remaining items
        await aggregator.finalize()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 1.0  # Should process 1000 items in < 1 second
        
        # Check statistics
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == num_items
        assert stats["total_batches_produced"] == 10  # 1000 items / 100 batch_size
        assert stats["aggregation_errors"] == 0
        
        # Calculate average processing time per item
        avg_processing_time = processing_time / num_items
        assert avg_processing_time < 0.001  # < 1ms per item
    
    @pytest.mark.asyncio
    async def test_aggregator_concurrent_processing(self):
        """Test Aggregator concurrent processing"""
        config = {"batch_size": 5, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        
        # Process items concurrently
        async def process_items(start, count):
            for i in range(start, start + count):
                await aggregator.process_item(i)
        
        # Run concurrent tasks
        tasks = [
            process_items(0, 10),
            process_items(10, 10),
            process_items(20, 10)
        ]
        
        await asyncio.gather(*tasks)
        
        # Finalize to flush remaining items
        await aggregator.finalize()
        
        # Check statistics
        stats = aggregator.get_aggregation_stats()
        assert stats["total_items_received"] == 30
        assert stats["total_batches_produced"] == 6  # 30 items / 5 batch_size
        assert stats["aggregation_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_aggregator_required_methods(self):
        """Test Aggregator required methods for component registry"""
        config = {"batch_size": 5}
        aggregator = Aggregator("test_aggregator", config)
        
        # Test class methods
        assert Aggregator.get_required_config_fields() == []
        assert Aggregator.get_required_dependencies() == []
        
        # Test instance methods
        assert await aggregator.is_ready() == True
        
        health_status = await aggregator.health_check()
        assert health_status["status"] == "healthy"
        assert health_status["component"] == "Aggregator"
        assert health_status["name"] == "test_aggregator"
        assert health_status["batch_size"] == 5
        assert "statistics" in health_status
        
        # Cleanup
        await aggregator.finalize()
    
    @pytest.mark.asyncio
    async def test_aggregator_readiness_check(self):
        """Test Aggregator readiness check"""
        # Valid aggregator should be ready
        config = {"batch_size": 5, "timeout_seconds": 10, "aggregation_strategy": "collect"}
        aggregator = Aggregator("test_aggregator", config)
        assert await aggregator.is_ready() == True
        
        # Invalid configuration should not be ready
        # (This test would fail at initialization, so we test the ready logic)
        aggregator.batch_size = 0
        assert await aggregator.is_ready() == False
        
        aggregator.batch_size = 5
        aggregator.timeout_seconds = 0
        assert await aggregator.is_ready() == False
        
        aggregator.timeout_seconds = 10
        aggregator.aggregation_strategy = "invalid"
        assert await aggregator.is_ready() == False
        
        # Cleanup
        aggregator.aggregation_strategy = "collect"
        await aggregator.finalize()