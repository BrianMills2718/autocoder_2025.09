#!/usr/bin/env python3
"""
Standalone ComposedComponent - Auto-Generated
Composed component template without framework dependencies (Sink variant)
"""

try:
    from .standalone_harness_component import HarnessComponent
except ImportError:
    from standalone_harness_component import HarnessComponent
from typing import Dict, Any, Optional
import time
import anyio


class ComposedComponent(HarnessComponent):
    """Standalone composed component with process_item() method pattern"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = config.get('component_type', 'sink') if config else 'sink'
        self.logger.info(f"ComposedComponent {self.name} ({self.component_type}) initialized")
    
    async def run(self) -> None:
        """
        Main execution logic for composed component.
        Handles different component types through capability composition.
        """
        if self.component_type == 'source':
            await self._run_as_source()
        elif self.component_type == 'transformer':
            await self._run_as_transformer()
        elif self.component_type == 'sink':
            await self._run_as_sink()
        else:
            self.logger.error(f"Unknown component type: {self.component_type}")
    
    async def _run_as_source(self) -> None:
        """Run component as a data source"""
        for i in range(self.config.get('data_count', 10)):
            data = await self.process_item(None)  # Sources don't need input
            
            for stream_name, stream in self.send_streams.items():
                await stream.send(data)
                
            if self.config.get('data_delay', 0) > 0:
                await anyio.sleep(self.config['data_delay'])
    
    async def _run_as_transformer(self) -> None:
        """Run component as a data transformer"""
        async for data in self.receive_stream:
            transformed_data = await self.process_item(data)
            
            for stream_name, stream in self.send_streams.items():
                await stream.send(transformed_data)
    
    async def _run_as_sink(self) -> None:
        """Run component as a data sink"""
        async for data in self.receive_stream:
            result = await self.process_item(data)
            # Sinks typically don't forward data, but may log results
            if result:
                self.logger.info(f"Sink processed data: {result}")
    
    async def process_item(self, item: Any = None) -> Any:
        """
        Composed processing method - override in generated components.
        This is a template - generated components will have real implementations.
        """
        if self.component_type == 'source':
            # Generate data for source components
            return {"message": f"Template source data", "timestamp": time.time()}
        elif self.component_type == 'transformer':
            # Transform data for transformer components
            if input_data:
                return {"original": input_data, "transformed": True, "timestamp": time.time()}
            return {"error": "No input data to transform"}
        elif self.component_type == 'sink':
            # Handle data output for sink components
            if input_data:
                return {"status": "processed", "data_received": True, "timestamp": time.time()}
            return {"status": "no_data"}
        else:
            return {"error": f"Unknown component type: {self.component_type}"}
