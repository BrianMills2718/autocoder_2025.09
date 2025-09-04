#!/usr/bin/env python3
"""
Controller Component - Handles routing and flow control operations
"""

import anyio
import time
from typing import Any, Dict, List, Optional, Callable
from autocoder_cc.orchestration.component import Component
from autocoder_cc.error_handling.consistent_handler import ConsistentErrorHandler, handle_errors
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Controller(Component):
    """
    Controller component for dynamic routing and flow control.
    
    Supports two variants:
    - router: Routes items to different output streams based on content
    - terminator: Controls loop termination based on conditions
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.variant = self.config.get('variant', 'router')
        
        # Initialize ConsistentErrorHandler for universal error coverage
        self.error_handler = ConsistentErrorHandler(f"Controller.{name}")
        
        # Variant-specific state
        if self.variant == 'router':
            self.routing_rules = self.config.get('routing_rules', {})
            self.default_output = self.config.get('default_output', 'default')
            
        elif self.variant == 'terminator':
            self.max_items = self.config.get('max_items', 10)
            self.timeout_seconds = self.config.get('timeout_seconds', 30)
            self.items_processed = 0
            self.start_time = None
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize Controller"""
        self.logger.info(f"Controller '{self.name}' initialized with variant: {self.variant}")
        if self.variant == 'terminator':
            self.start_time = time.time()
        self._status.is_running = True

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Controller component"""
        return [
            ConfigRequirement(
                name="control_strategy",
                type="str",
                description="Strategy for control logic",
                required=True,
                options=["threshold", "rate_limit", "circuit_breaker", "backpressure"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="threshold_value",
                type="float",
                description="Threshold value for control decisions",
                required=False,
                default=0.8,
                semantic_type=ConfigType.FLOAT,
                depends_on={"control_strategy": "threshold"}
            ),
            ConfigRequirement(
                name="rate_limit",
                type="int",
                description="Maximum rate per second",
                required=False,
                default=100,
                semantic_type=ConfigType.INTEGER,
                depends_on={"control_strategy": "rate_limit"}
            )
        ]

    
    @handle_errors(component_name="Controller", operation="process")
    async def process(self) -> None:
        """Main processing loop based on variant with consistent error handling"""
        if self.variant == 'router':
            await self._process_router()
        elif self.variant == 'terminator':
            await self._process_terminator()
        else:
            error_msg = f"Unknown variant: {self.variant}"
            self.logger.error(error_msg)
            await self.error_handler.handle_exception(
                ValueError(error_msg),
                context={"variant": self.variant, "available_variants": ["router", "terminator"]},
                operation="process_variant_validation"
            )
    
    async def _process_router(self) -> None:
        """Process router variant - route items to different outputs"""
        self.logger.info("Starting router control processing")
        
        async for item in self.receive_streams.get('input', []):
            try:
                self.logger.info(f"Router received item: {item}")
                
                # Determine output stream based on routing rules
                output_stream = self._determine_output_stream(item)
                
                self.logger.info(f"Routing item to output stream: {output_stream}")
                
                # Send to appropriate output stream
                if output_stream in self.send_streams:
                    await self.send_streams[output_stream].send(item)
                    self.logger.info(f"Item routed to '{output_stream}': {item}")
                else:
                    # Fallback to default output
                    if self.default_output in self.send_streams:
                        await self.send_streams[self.default_output].send(item)
                        self.logger.info(f"Item routed to default output '{self.default_output}': {item}")
                    else:
                        self.logger.warning(f"No valid output stream found for item: {item}")
                
                self.increment_processed()
            except Exception as e:
                await self.error_handler.handle_exception(
                    e,
                    context={"item": str(item), "output_stream": output_stream if 'output_stream' in locals() else "unknown"},
                    operation="router_item_processing"
                )
    
    def _determine_output_stream(self, item: Any) -> str:
        """Determine which output stream to route the item to"""
        # Simple routing based on item content
        if isinstance(item, dict):
            # Check for explicit routing key
            if 'route_to' in item:
                return item['route_to']
            
            # Check for category-based routing
            if 'category' in item:
                category = item['category']
                if category == 'high_priority':
                    return 'priority'
                elif category == 'low_priority':
                    return 'bulk'
                elif category == 'error':
                    return 'errors'
            
            # Check for value-based routing
            if 'value' in item:
                value = item.get('value', 0)
                if isinstance(value, (int, float)):
                    if value > 100:
                        return 'high_value'
                    elif value > 50:
                        return 'medium_value'
                    else:
                        return 'low_value'
            
            # Check for type-based routing
            if 'type' in item:
                item_type = item['type']
                return f"{item_type}_output"
        
        # Default routing
        return self.default_output
    
    async def _process_terminator(self) -> None:
        """Process terminator variant - control loop termination"""
        self.logger.info("Starting terminator control processing")
        
        async for item in self.receive_streams.get('input', []):
            try:
                self.items_processed += 1
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                self.logger.info(f"Terminator processed item {self.items_processed}: {item}")
                
                # Forward item to output if available
                if 'output' in self.send_streams:
                    await self.send_streams['output'].send(item)
                
                # Check termination conditions
                should_terminate = self._check_termination_conditions(elapsed_time)
                
                if should_terminate:
                    self.logger.info("Termination condition met")
                    break
                
                self.increment_processed()
            except Exception as e:
                await self.error_handler.handle_exception(
                    e,
                    context={"item": str(item), "items_processed": self.items_processed, "elapsed_time": elapsed_time if 'elapsed_time' in locals() else 0},
                    operation="terminator_item_processing"
                )
        
        # Log final termination
        self.logger.info("Termination condition met")
    
    def _check_termination_conditions(self, elapsed_time: float) -> bool:
        """Check if termination conditions are met"""
        # Check item count limit
        if self.items_processed >= self.max_items:
            self.logger.info(f"Item limit reached: {self.items_processed}/{self.max_items}")
            return True
        
        # Check timeout
        if elapsed_time >= self.timeout_seconds:
            self.logger.info(f"Timeout reached: {elapsed_time:.2f}s/{self.timeout_seconds}s")
            return True
        
        # Check for special termination item
        return False
    
    async def cleanup(self) -> None:
        """Cleanup Controller resources"""
        if self.variant == 'terminator':
            total_time = time.time() - self.start_time if self.start_time else 0
            self.logger.info(f"Terminator completed: {self.items_processed} items in {total_time:.2f}s")
        
        self.logger.info(f"Controller '{self.name}' cleanup completed")
        self._status.is_running = False