#!/usr/bin/env python3
"""
Test file for Port infrastructure - Phase 1 of TDD migration
Tests port creation, validation, and basic stream connection
"""
import pytest
import asyncio
from typing import Any, Dict
from pydantic import BaseModel, ValidationError
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# These imports will fail initially - that's expected in TDD
try:
    from autocoder_cc.components.ports import Port, OutputPort, InputPort, PortValidationError
    from autocoder_cc.components.ports import create_connected_ports, PortClosedError
except ImportError as e:
    print(f"Expected import error during TDD: {e}")
    # Create placeholder classes so tests can be written
    class Port:
        pass
    class OutputPort:
        pass
    class InputPort:
        pass
    class PortValidationError(Exception):
        pass
    class PortClosedError(Exception):
        pass
    def create_connected_ports(*args, **kwargs):
        pass


# Test schemas using Pydantic
class TodoItem(BaseModel):
    """Example schema for testing"""
    id: int
    title: str
    completed: bool = False
    
class ErrorSchema(BaseModel):
    """Schema for error messages"""
    error: str
    details: Dict[str, Any] = {}
    timestamp: float = None


class TestPortCreation:
    """Test basic port creation and configuration"""
    
    def test_output_port_creation(self):
        """Output port should be created with name and schema"""
        port = OutputPort("test_output", TodoItem)
        assert port.name == "test_output"
        assert port.schema == TodoItem
        assert port.stream is None  # Not connected yet
    
    def test_input_port_creation(self):
        """Input port should be created with name and schema"""
        port = InputPort("test_input", TodoItem)
        assert port.name == "test_input"
        assert port.schema == TodoItem
        assert port.stream is None  # Not connected yet
    
    def test_port_string_representation(self):
        """Ports should have useful string representation"""
        port = OutputPort("my_port", TodoItem)
        assert "my_port" in str(port)
        assert "TodoItem" in str(port)


class TestPortValidation:
    """Test data validation through ports"""
    
    @pytest.mark.asyncio
    async def test_valid_data_accepted(self):
        """Port should accept data matching schema"""
        port = OutputPort("test", TodoItem)
        
        # Create valid item
        item = TodoItem(id=1, title="Test Task", completed=False)
        
        # Should raise AttributeError about no stream, not validation error
        with pytest.raises(AttributeError, match="no connected stream"):
            await port.send(item)
    
    @pytest.mark.asyncio
    async def test_dict_coercion(self):
        """Port should coerce valid dicts to schema"""
        port = OutputPort("test", TodoItem)
        
        # Send dict that matches schema
        data = {"id": 2, "title": "Another Task"}
        
        # Should raise AttributeError about no stream, not validation error
        with pytest.raises(AttributeError, match="no connected stream"):
            await port.send(data)
    
    @pytest.mark.asyncio
    async def test_invalid_data_rejected(self):
        """Port should reject data not matching schema"""
        port = OutputPort("test", TodoItem)
        
        # Invalid data - id should be int
        invalid_data = {"id": "not_an_int", "title": "Task"}
        
        # Should raise validation error
        with pytest.raises((PortValidationError, ValidationError)):
            await port.send(invalid_data)
    
    @pytest.mark.asyncio
    async def test_missing_required_field(self):
        """Port should reject data missing required fields"""
        port = OutputPort("test", TodoItem)
        
        # Missing required 'title' field
        invalid_data = {"id": 3}
        
        with pytest.raises((PortValidationError, ValidationError)):
            await port.send(invalid_data)


class TestPortConnection:
    """Test connecting ports via streams"""
    
    @pytest.mark.asyncio
    async def test_port_connection(self):
        """Ports should connect via streams"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        # Connect them (this will use anyio streams)
        create_connected_ports(output, input)
        
        # Both should now have streams
        assert output.stream is not None
        assert input.stream is not None
    
    @pytest.mark.asyncio
    async def test_data_flow_through_ports(self):
        """Data should flow from output to input port"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        # Connect them
        create_connected_ports(output, input)
        
        # Send data through output
        item = TodoItem(id=1, title="Flow Test", completed=True)
        await output.send(item)
        
        # Receive from input
        received = await input.receive()
        
        # Should be the same data
        assert received.id == item.id
        assert received.title == item.title
        assert received.completed == item.completed
    
    @pytest.mark.asyncio
    async def test_multiple_items_flow(self):
        """Multiple items should flow in order"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        create_connected_ports(output, input)
        
        # Send multiple items
        items = [
            TodoItem(id=1, title="First"),
            TodoItem(id=2, title="Second"),
            TodoItem(id=3, title="Third")
        ]
        
        for item in items:
            await output.send(item)
        
        # Receive in order
        for original in items:
            received = await input.receive()
            assert received.id == original.id
            assert received.title == original.title
    
    @pytest.mark.asyncio
    async def test_type_validation_across_connection(self):
        """Type validation should work across connected ports"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        create_connected_ports(output, input)
        
        # Try to send invalid data
        with pytest.raises((PortValidationError, ValidationError)):
            await output.send({"id": "invalid", "title": "Test"})
        
        # Valid data should work
        await output.send(TodoItem(id=1, title="Valid"))
        received = await input.receive()
        assert received.id == 1


class TestPortBuffering:
    """Test port buffer management"""
    
    @pytest.mark.asyncio
    async def test_buffer_size_configuration(self):
        """Ports should support buffer size configuration"""
        output = OutputPort("out", TodoItem, buffer_size=10)
        input = InputPort("in", TodoItem)
        
        create_connected_ports(output, input, buffer_size=10)
        
        # Should be able to send up to buffer size without blocking
        for i in range(10):
            await output.send(TodoItem(id=i, title=f"Item {i}"))
    
    @pytest.mark.asyncio
    async def test_backpressure(self):
        """Port should handle backpressure when buffer full"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        # Small buffer to test backpressure
        create_connected_ports(output, input, buffer_size=2)
        
        # Fill buffer
        await output.send(TodoItem(id=1, title="First"))
        await output.send(TodoItem(id=2, title="Second"))
        
        # Third send should block until we receive
        send_task = asyncio.create_task(
            output.send(TodoItem(id=3, title="Third"))
        )
        
        # Should not complete immediately
        await asyncio.sleep(0.1)
        assert not send_task.done()
        
        # Receive one item to make space
        await input.receive()
        
        # Now send should complete
        await send_task


class TestPortWithMultipleSchemas:
    """Test ports with different schemas"""
    
    @pytest.mark.asyncio
    async def test_error_port(self):
        """Error port should handle error schema"""
        error_port = OutputPort("errors", ErrorSchema)
        
        error = ErrorSchema(
            error="Test error",
            details={"code": 500},
            timestamp=1234567890.0
        )
        
        # Should accept error schema
        try:
            await error_port.send(error)
        except AttributeError:  # No stream connected
            pass
    
    @pytest.mark.asyncio
    async def test_mixed_port_types(self):
        """System should support ports with different schemas"""
        todo_out = OutputPort("todos", TodoItem)
        error_out = OutputPort("errors", ErrorSchema)
        
        todo_in = InputPort("todos", TodoItem)
        error_in = InputPort("errors", ErrorSchema)
        
        # Connect matching types
        create_connected_ports(todo_out, todo_in)
        create_connected_ports(error_out, error_in)
        
        # Send different types through different ports
        await todo_out.send(TodoItem(id=1, title="Task"))
        await error_out.send(ErrorSchema(error="Error occurred"))
        
        # Receive from appropriate ports
        todo = await todo_in.receive()
        error = await error_in.receive()
        
        assert isinstance(todo, TodoItem)
        assert isinstance(error, ErrorSchema)


class TestPortHelpers:
    """Test helper functions for ports"""
    
    def test_port_equality(self):
        """Ports with same name and schema should be equal"""
        port1 = OutputPort("test", TodoItem)
        port2 = OutputPort("test", TodoItem)
        port3 = OutputPort("other", TodoItem)
        
        assert port1 == port2
        assert port1 != port3
    
    @pytest.mark.asyncio
    async def test_port_timeout(self):
        """Input port should support receive timeout"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        create_connected_ports(output, input)
        
        # Try to receive with timeout when nothing sent
        with pytest.raises(asyncio.TimeoutError):
            await input.receive(timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_port_close(self):
        """Ports should support closing"""
        output = OutputPort("out", TodoItem)
        input = InputPort("in", TodoItem)
        
        create_connected_ports(output, input)
        
        # Send some data
        await output.send(TodoItem(id=1, title="Test"))
        
        # Input should receive the item
        item = await input.receive()
        assert item.id == 1
        
        # Close output port
        await output.close()
        
        # Then should get closed signal when trying to receive
        with pytest.raises(PortClosedError):
            await input.receive()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
