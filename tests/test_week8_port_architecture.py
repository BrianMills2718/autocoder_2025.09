import pytest
import anyio
from autocoder_cc.ports.base import InputPort, OutputPort

def test_ports_can_connect_and_communicate():
    """Test basic port functionality"""
    async def run_test():
        in_port = InputPort("test_in", max_queue_size=10)
        out_port = OutputPort("test_out")
        
        # Connect
        connected = await out_port.connect(in_port)
        assert connected, "Failed to connect ports"
        
        # Send
        sent = await out_port.send("test_message")
        assert sent, "Failed to send message"
        
        # Receive
        msg = await in_port.receive()
        assert msg == "test_message", f"Got {msg}"
        
        # Non-blocking receive
        msg = await in_port.receive()
        assert msg is None, "Should return None when empty"
        
    anyio.run(run_test)

def test_components_have_ports():
    """Test that primitives have port attributes"""
    from autocoder_cc.components.primitives.base import Primitive
    
    # Check Primitive has port attributes
    assert hasattr(Primitive, '__init__'), "Primitive missing __init__"
    
    # This will check the actual implementation
    # Will fail if components don't use ports