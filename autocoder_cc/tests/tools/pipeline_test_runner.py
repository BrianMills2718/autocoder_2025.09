"""Test runner for multi-component pipelines."""
import asyncio
from typing import List, Dict, Any, Tuple
from autocoder_cc.tests.tools.port_test_runner import PortBasedTestRunner, TestResult
from autocoder_cc.observability import get_logger

class PipelineTestRunner(PortBasedTestRunner):
    """Test runner for component pipelines."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("PipelineTestRunner")
        
    async def test_pipeline(self,
                           components: List[Any],
                           test_data: List[Dict[str, Any]],
                           timeout: float = 30.0) -> TestResult:
        """Test a pipeline of connected components."""
        self.logger.info(f"Testing pipeline with {len(components)} components")
        
        pipeline_name = " → ".join(c.name for c in components)
        start_time = asyncio.get_event_loop().time()
        errors = []
        messages_sent = 0
        messages_received = 0
        
        try:
            # Setup all components
            for component in components:
                await component.setup()
            
            # Connect components in sequence
            for i in range(len(components) - 1):
                source_comp = components[i]
                target_comp = components[i + 1]
                
                # Find output port on source
                output_port = None
                if hasattr(source_comp, 'output_ports'):
                    # Get first output port
                    output_port = next(iter(source_comp.output_ports.values()))
                
                # Find input port on target
                input_port = None
                if hasattr(target_comp, 'input_ports'):
                    # Get first input port
                    input_port = next(iter(target_comp.input_ports.values()))
                
                if output_port and input_port:
                    await self._connect_ports(output_port, input_port)
                    self.logger.info(f"Connected {source_comp.name} → {target_comp.name}")
                else:
                    errors.append(f"Cannot connect {source_comp.name} to {target_comp.name}")
            
            # Send test data through first component
            first_component = components[0]
            messages_sent = len(test_data)
            
            if hasattr(first_component, 'process'):
                for data in test_data:
                    await first_component.process(data)
            
            # Wait for processing
            await asyncio.sleep(1.0)  # Allow messages to propagate
            
            # Check last component for output
            last_component = components[-1]
            
            if hasattr(last_component, 'received_messages'):
                messages_received = len(last_component.received_messages)
            
            # Cleanup
            for component in components:
                await component.cleanup()
                
        except Exception as e:
            errors.append(f"Pipeline error: {str(e)}")
        
        # Calculate latency
        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000
        
        # Create result
        result = TestResult(
            component_name=pipeline_name,
            test_name=f"pipeline_test",
            success=len(errors) == 0,
            messages_sent=messages_sent,
            messages_received=messages_received,
            errors=errors,
            latency_ms=latency_ms,
            metadata={
                "pipeline_length": len(components),
                "components": [c.name for c in components]
            }
        )
        
        self.results.append(result)
        return result
    
    async def test_full_system(self,
                              source_comp: Any,
                              transformer_comp: Any,
                              sink_comp: Any,
                              test_data: List[Dict[str, Any]]) -> TestResult:
        """Test a complete source → transformer → sink system."""
        self.logger.info("Testing full system")
        
        components = [source_comp, transformer_comp, sink_comp]
        return await self.test_pipeline(components, test_data)