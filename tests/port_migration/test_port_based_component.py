#!/usr/bin/env python3
"""
Test file for PortBasedComponent - Phase 2 of TDD migration
Tests the base component class that uses ports instead of raw streams
"""
import pytest
import asyncio
from typing import Any, Dict
from pydantic import BaseModel
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.components.ports import Port, OutputPort, InputPort, create_connected_ports
from autocoder_cc.components.ports import PortRegistry

# Import the component base class (will fail initially - TDD)
try:
    from autocoder_cc.components.base import PortBasedComponent
except ImportError:
    # Placeholder for TDD
    class PortBasedComponent:
        pass


# Test schemas
class DataSchema(BaseModel):
    """Input data schema"""
    value: int
    
class ResultSchema(BaseModel):
    """Output result schema"""
    result: int
    
class ErrorSchema(BaseModel):
    """Error schema"""
    error: str
    details: Dict[str, Any] = {}


class TestPortBasedComponentCreation:
    """Test component creation and port management"""
    
    def test_component_creation(self):
        """Component should be created with port registry"""
        
        class TestComponent(PortBasedComponent):
            def configure_ports(self):
                """Configure component ports"""
                pass
        
        component = TestComponent()
        assert hasattr(component, 'input_ports')
        assert hasattr(component, 'output_ports')
        assert isinstance(component.input_ports, dict)
        assert isinstance(component.output_ports, dict)
    
    def test_port_declaration(self):
        """Component should declare ports in configure_ports"""
        
        class TestComponent(PortBasedComponent):
            def configure_ports(self):
                self.add_input_port("data_in", DataSchema)
                self.add_output_port("data_out", ResultSchema)
        
        component = TestComponent()
        
        # Ports should be created
        assert "data_in" in component.input_ports
        assert "data_out" in component.output_ports
        
        # Ports should have correct schemas
        assert component.input_ports["data_in"].schema == DataSchema
        assert component.output_ports["data_out"].schema == ResultSchema
    
    def test_multiple_ports(self):
        """Component should support multiple input and output ports"""
        
        class MultiPortComponent(PortBasedComponent):
            def configure_ports(self):
                # Multiple inputs
                self.add_input_port("input1", DataSchema)
                self.add_input_port("input2", DataSchema)
                
                # Multiple outputs
                self.add_output_port("output1", ResultSchema)
                self.add_output_port("output2", ResultSchema)
                self.add_output_port("errors", ErrorSchema)
        
        component = MultiPortComponent()
        
        assert len(component.input_ports) == 2
        assert len(component.output_ports) == 3
        assert "errors" in component.output_ports


class TestPortBasedComponentProcessing:
    """Test component processing with ports"""
    
    @pytest.mark.asyncio
    async def test_simple_processing(self):
        """Component should process data through ports"""
        
        class Doubler(PortBasedComponent):
            """Component that doubles input values"""
            
            def configure_ports(self):
                self.add_input_port("numbers", DataSchema)
                self.add_output_port("doubled", ResultSchema)
            
            async def process(self):
                """Process data: double the input"""
                async for data in self.input_ports["numbers"]:
                    doubled_value = data.value * 2
                    result = ResultSchema(result=doubled_value)
                    await self.output_ports["doubled"].send(result)
        
        # Create and wire component
        component = Doubler()
        
        # Create external ports to connect
        input_port = OutputPort("test_in", DataSchema)
        output_port = InputPort("test_out", ResultSchema)
        
        # Wire them
        create_connected_ports(input_port, component.input_ports["numbers"])
        create_connected_ports(component.output_ports["doubled"], output_port)
        
        # Start processing in background
        process_task = asyncio.create_task(component.process())
        
        # Send test data
        await input_port.send(DataSchema(value=5))
        
        # Receive result
        result = await output_port.receive()
        assert result.result == 10
        
        # Clean up
        process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Component should handle errors via error port"""
        
        class SafeDivider(PortBasedComponent):
            """Component that divides by 2, with error handling"""
            
            def configure_ports(self):
                self.add_input_port("numbers", DataSchema)
                self.add_output_port("divided", ResultSchema)
                self.add_output_port("errors", ErrorSchema)
            
            async def process(self):
                """Process with error handling"""
                async for data in self.input_ports["numbers"]:
                    try:
                        if data.value == 0:
                            raise ValueError("Cannot process zero")
                        
                        result = ResultSchema(result=data.value // 2)
                        await self.output_ports["divided"].send(result)
                        
                    except Exception as e:
                        error = ErrorSchema(
                            error=str(e),
                            details={"input_value": data.value}
                        )
                        await self.output_ports["errors"].send(error)
        
        component = SafeDivider()
        
        # Wire up all ports
        input_port = OutputPort("test_in", DataSchema)
        output_port = InputPort("test_out", ResultSchema)
        error_port = InputPort("test_err", ErrorSchema)
        
        create_connected_ports(input_port, component.input_ports["numbers"])
        create_connected_ports(component.output_ports["divided"], output_port)
        create_connected_ports(component.output_ports["errors"], error_port)
        
        # Start processing
        process_task = asyncio.create_task(component.process())
        
        # Send valid data
        await input_port.send(DataSchema(value=10))
        result = await output_port.receive()
        assert result.result == 5
        
        # Send invalid data (zero)
        await input_port.send(DataSchema(value=0))
        error = await error_port.receive()
        assert "Cannot process zero" in error.error
        assert error.details["input_value"] == 0
        
        # Clean up
        process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            pass


class TestComponentLifecycle:
    """Test component lifecycle methods"""
    
    @pytest.mark.asyncio
    async def test_setup_and_cleanup(self):
        """Component should support setup and cleanup"""
        
        class LifecycleComponent(PortBasedComponent):
            def __init__(self):
                super().__init__()
                self.setup_called = False
                self.cleanup_called = False
            
            def configure_ports(self):
                self.add_input_port("input", DataSchema)
                self.add_output_port("output", ResultSchema)
            
            async def setup(self):
                """Initialize component"""
                self.setup_called = True
                await super().setup()
            
            async def cleanup(self):
                """Clean up component"""
                self.cleanup_called = True
                await super().cleanup()
        
        component = LifecycleComponent()
        
        # Setup should initialize
        await component.setup()
        assert component.setup_called
        
        # Cleanup should clean up
        await component.cleanup()
        assert component.cleanup_called
    
    @pytest.mark.asyncio
    async def test_port_closing_on_cleanup(self):
        """Component should close all ports on cleanup"""
        
        class TestComponent(PortBasedComponent):
            def configure_ports(self):
                self.add_input_port("input", DataSchema)
                self.add_output_port("output", ResultSchema)
        
        component = TestComponent()
        
        # Connect ports
        in_port = OutputPort("test_in", DataSchema)
        out_port = InputPort("test_out", ResultSchema)
        
        create_connected_ports(in_port, component.input_ports["input"])
        create_connected_ports(component.output_ports["output"], out_port)
        
        # Cleanup should close ports
        await component.cleanup()
        
        # All ports should be closed
        assert component.input_ports["input"]._closed
        assert component.output_ports["output"]._closed


class TestComponentComposition:
    """Test composing components together"""
    
    @pytest.mark.asyncio
    async def test_component_pipeline(self):
        """Components should work in a pipeline"""
        
        class Adder(PortBasedComponent):
            """Add 10 to input"""
            def configure_ports(self):
                self.add_input_port("in", DataSchema)
                self.add_output_port("out", DataSchema)
            
            async def process(self):
                async for data in self.input_ports["in"]:
                    result = DataSchema(value=data.value + 10)
                    await self.output_ports["out"].send(result)
        
        class Multiplier(PortBasedComponent):
            """Multiply by 2"""
            def configure_ports(self):
                self.add_input_port("in", DataSchema)
                self.add_output_port("out", ResultSchema)
            
            async def process(self):
                async for data in self.input_ports["in"]:
                    result = ResultSchema(result=data.value * 2)
                    await self.output_ports["out"].send(result)
        
        # Create pipeline: input -> Adder -> Multiplier -> output
        adder = Adder()
        multiplier = Multiplier()
        
        # External ports
        input_port = OutputPort("pipeline_in", DataSchema)
        output_port = InputPort("pipeline_out", ResultSchema)
        
        # Wire the pipeline
        create_connected_ports(input_port, adder.input_ports["in"])
        create_connected_ports(adder.output_ports["out"], multiplier.input_ports["in"])
        create_connected_ports(multiplier.output_ports["out"], output_port)
        
        # Start both components
        adder_task = asyncio.create_task(adder.process())
        mult_task = asyncio.create_task(multiplier.process())
        
        # Send data through pipeline
        await input_port.send(DataSchema(value=5))  # 5 + 10 = 15, 15 * 2 = 30
        
        # Get result
        result = await output_port.receive()
        assert result.result == 30
        
        # Clean up
        adder_task.cancel()
        mult_task.cancel()
        try:
            await adder_task
            await mult_task
        except asyncio.CancelledError:
            pass


class TestComponentHelpers:
    """Test helper methods for components"""
    
    def test_component_name(self):
        """Component should have a name"""
        
        class NamedComponent(PortBasedComponent):
            def configure_ports(self):
                pass
        
        component = NamedComponent(name="my_component")
        assert component.name == "my_component"
        
        # Default name should be class name
        component2 = NamedComponent()
        assert component2.name == "NamedComponent"
    
    def test_component_string_representation(self):
        """Component should have useful string representation"""
        
        class TestComponent(PortBasedComponent):
            def configure_ports(self):
                self.add_input_port("in", DataSchema)
                self.add_output_port("out", ResultSchema)
        
        component = TestComponent(name="test")
        string_repr = str(component)
        
        assert "test" in string_repr
        assert "TestComponent" in string_repr or "PortBasedComponent" in string_repr


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
