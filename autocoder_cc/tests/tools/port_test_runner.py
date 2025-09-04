"""Port-based test runner for component validation."""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from autocoder_cc.observability import get_logger
from autocoder_cc.components.primitives.base import Source, Sink, Transformer
from autocoder_cc.components.ports import Port, InputPort, OutputPort

@dataclass
class TestResult:
    """Result of a component test."""
    component_name: str
    test_name: str
    success: bool
    messages_sent: int
    messages_received: int
    errors: List[str]
    latency_ms: float
    metadata: Dict[str, Any]

class PortBasedTestRunner:
    """Test runner for port-based components."""
    
    def __init__(self):
        self.logger = get_logger("PortBasedTestRunner")
        self.results: List[TestResult] = []
        
    async def test_component(self, 
                            component: Any,
                            test_data: List[Dict[str, Any]],
                            timeout: float = 10.0) -> TestResult:
        """Test a single component with test data."""
        self.logger.info(f"Testing component: {component.name}")
        
        start_time = asyncio.get_event_loop().time()
        messages_sent = 0
        messages_received = 0
        errors = []
        
        try:
            # Setup component
            await component.setup()
            
            # Create test ports
            if hasattr(component, 'input_ports'):
                for port_name, port in component.input_ports.items():
                    # Connect test source to input port
                    test_source = TestSource(f"test_source_{port_name}", test_data)
                    await self._connect_ports(test_source.output_port, port)
            
            # Collect output
            output_collector = TestSink(f"test_sink_{component.name}")
            if hasattr(component, 'output_ports'):
                for port_name, port in component.output_ports.items():
                    await self._connect_ports(port, output_collector.input_port)
            
            # Run test
            test_task = asyncio.create_task(self._run_test(
                component, test_data, output_collector
            ))
            
            # Wait with timeout
            messages_sent = len(test_data)
            await asyncio.wait_for(test_task, timeout=timeout)
            messages_received = len(output_collector.received_messages)
            
            # Cleanup
            await component.cleanup()
            
        except asyncio.TimeoutError:
            errors.append(f"Test timed out after {timeout} seconds")
        except Exception as e:
            errors.append(f"Test error: {str(e)}")
        
        # Calculate latency
        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000
        
        # Create result
        result = TestResult(
            component_name=component.name,
            test_name=f"test_{component.name}",
            success=len(errors) == 0 and messages_received > 0,
            messages_sent=messages_sent,
            messages_received=messages_received,
            errors=errors,
            latency_ms=latency_ms,
            metadata={
                "component_type": type(component).__name__,
                "timeout": timeout
            }
        )
        
        self.results.append(result)
        self.logger.info(f"Test result: {result.success} ({messages_received}/{messages_sent} messages)")
        
        return result
    
    async def _connect_ports(self, output_port: OutputPort, input_port: InputPort):
        """Connect two ports together."""
        # Port connection logic
        output_port.connect(input_port)
        self.logger.debug(f"Connected {output_port.name} to {input_port.name}")
    
    async def _run_test(self, component: Any, test_data: List[Dict], 
                        output_collector: 'TestSink'):
        """Run the actual test."""
        # Send test data through component
        if hasattr(component, 'process'):
            for data in test_data:
                await component.process(data)
        elif hasattr(component, 'generate'):
            # For sources
            await component.generate()
        elif hasattr(component, 'consume'):
            # For sinks
            for data in test_data:
                await component.consume(data)
    
    def generate_report(self) -> str:
        """Generate test report."""
        report = ["# Port-Based Test Report\n"]
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Successful: {successful}")
        report.append(f"Failed: {total_tests - successful}")
        report.append(f"Success Rate: {(successful/total_tests)*100:.1f}%\n")
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            report.append(f"{status} {result.component_name}:")
            report.append(f"  - Messages: {result.messages_received}/{result.messages_sent}")
            report.append(f"  - Latency: {result.latency_ms:.2f}ms")
            if result.errors:
                report.append(f"  - Errors: {', '.join(result.errors)}")
        
        return '\n'.join(report)


class TestSource(Source):
    """Test source that emits predefined test data."""
    
    def __init__(self, name: str, test_data: List[Dict[str, Any]]):
        super().__init__(name, {})
        self.test_data = test_data
        self.output_port = OutputPort("out")
        
    async def generate(self):
        """Generate test messages."""
        for data in self.test_data:
            await self.output_port.send(data)


class TestSink(Sink):
    """Test sink that collects received messages."""
    
    def __init__(self, name: str):
        super().__init__(name, {})
        self.received_messages: List[Dict[str, Any]] = []
        self.input_port = InputPort("in")
        
    async def consume(self, item: Dict[str, Any]):
        """Collect received message."""
        self.received_messages.append(item)