from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Universal Component Base Class for System-First Architecture

This is the new base class that all components must inherit from to work
with the SystemExecutionHarness. It provides a standard lifecycle interface
and stream-based communication using anyio.
"""

import anyio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
import uuid
import time


@dataclass
class ComponentStatus:
    """Status information for a component"""
    is_running: bool = False
    is_healthy: bool = True
    items_processed: int = 0
    errors_encountered: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceContext:
    """OpenTelemetry-compatible trace context for distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1  # 1 = sampled
    baggage: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def create_new(cls) -> 'TraceContext':
        """Create a new root trace context"""
        return cls(
            trace_id=f"trace-{uuid.uuid4().hex[:16]}",
            span_id=f"span-{uuid.uuid4().hex[:8]}"
        )
    
    def create_child(self, operation_name: str = "child") -> 'TraceContext':
        """Create a child trace context"""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=f"span-{uuid.uuid4().hex[:8]}",
            parent_span_id=self.span_id,
            trace_flags=self.trace_flags,
            baggage=self.baggage.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'trace_flags': self.trace_flags,
            'baggage': self.baggage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceContext':
        """Create from dictionary"""
        return cls(
            trace_id=data.get('trace_id', f"trace-{uuid.uuid4().hex[:16]}"),
            span_id=data.get('span_id', f"span-{uuid.uuid4().hex[:8]}"),
            parent_span_id=data.get('parent_span_id'),
            trace_flags=data.get('trace_flags', 1),
            baggage=data.get('baggage', {})
        )


class Component(ABC):
    """
    Universal base class for all harness-compatible components.
    
    The Component class provides a standardized interface for building pluggable,
    observable, and testable system components. It implements the System-First
    Architecture pattern with stream-based communication and comprehensive
    lifecycle management.
    
    ## Key Features
    
    ### Lifecycle Management
    - **Setup Phase**: Component initialization and resource allocation
    - **Processing Phase**: Main business logic execution  
    - **Cleanup Phase**: Resource cleanup and graceful shutdown
    - **Health Monitoring**: Continuous health checks and status reporting
    
    ### Stream-Based Communication
    - **AnyIO Streams**: Structured concurrency with MemoryObjectStreams
    - **Type Safety**: Strongly typed message passing
    - **Backpressure Handling**: Automatic flow control and buffering
    - **Error Isolation**: Component failures don't affect others
    
    ### Observability Integration
    - **Structured Logging**: Centralized logging with correlation IDs
    - **Distributed Tracing**: OpenTelemetry-compatible trace context
    - **Metrics Collection**: Built-in performance and error metrics
    - **Health Checks**: Liveness and readiness probe support
    
    ### Error Handling
    - **Graceful Degradation**: Continue operation with reduced functionality
    - **Error Recovery**: Automatic retry and circuit breaker patterns
    - **Error Reporting**: Comprehensive error tracking and reporting
    - **Resource Cleanup**: Automatic cleanup on failures
    
    ## Usage
    
    Components communicate through AnyIO streams:
    
    ```python
    # Receiving data
    async for data in self.receive_streams['input_stream']:
        # Process data
        result = process(data)
        
        # Send to output streams
        await self.send_streams['output_stream'].send(result)
    ```
    
    ## Configuration
    
    Components can be configured through the config dictionary:
    
    ```python
    config = {
        'max_retries': 3,
        'timeout': 30.0,
        'buffer_size': 1000,
        'health_check_interval': 30
    }
    
    component = MyComponent("my-component", config)
    ```
    
    ## Best Practices
    
    1. **Single Responsibility**: Each component should have a single, well-defined purpose
    2. **Error Handling**: Implement proper error handling and recovery
    3. **Resource Management**: Clean up resources in the cleanup method
    4. **Observability**: Use structured logging and tracing
    5. **Testing**: Write unit tests for component logic
    
    ## Related Classes
    
    - `ComponentStatus`: Component status and metrics
    - `TraceContext`: Distributed tracing context
    - `SystemExecutionHarness`: Component orchestration
    - `Connection`: Inter-component communication configuration
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Component.{name}")
        
        # Stream-based communication (anyio) - this is the ONLY communication method
        self.receive_streams: Dict[str, anyio.abc.ReceiveStream] = {}
        self.send_streams: Dict[str, anyio.abc.SendStream] = {}
        
        # Component state
        self._status = ComponentStatus()
        self._shutdown_event = None  # Will be set by harness during setup
        
        # Tracing support
        self._tracer = None  # Will be set by harness during setup
        self._current_trace_context: Optional[TraceContext] = None
        
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the component.
        Called once when the component starts.
        Override this method to add component-specific setup logic.
        """
        # Initialize tracing if available
        if harness_context and 'tracer' in harness_context:
            self._tracer = harness_context['tracer']
            self.logger.info(f"Tracing enabled for component {self.name}")
        
        # Mark component as running after successful setup
        self._status.is_running = True
        self.logger.info(f"Component {self.name} setup completed")
    
    @abstractmethod
    async def process(self) -> None:
        """
        Main processing loop using anyio stream patterns.
        
        The idiomatic pattern for stream consumption is:
        ```python
        async for item in self.receive_streams['input_name']:
            result = self.transform(item)
            await self.send_streams['output_name'].send(result)
        ```
        
        This method should:
        1. Use async for loops to consume from self.receive_streams
        2. Process the data 
        3. Send results via self.send_streams
        4. Handle graceful shutdown when streams are closed
        """
        pass
    
    async def cleanup(self) -> None:
        """
        Cleanup resources.
        Called once when the component shuts down.
        Override this method to add component-specific cleanup logic.
        """
        pass
    
    async def _process_stream_with_handler(self, stream_name: str, stream, handler: Callable) -> None:
        """
        Generic stream processing with custom handler function.
        
        This method abstracts the common pattern of:
        1. Iterating over stream data
        2. Processing each item with a custom handler
        3. Sending results to output streams
        4. Error handling and logging
        
        Args:
            stream_name: Name of the input stream for logging
            stream: The anyio stream to process
            handler: Async function that processes each data item
        """
        try:
            async for data in stream:
                try:
                    # Process the data with the provided handler
                    result = await handler(data)
                    
                    # Send to all output streams if result is not None
                    if result is not None and self.send_streams:
                        for out_stream_name, out_stream in self.send_streams.items():
                            await out_stream.send(result)
                        self.increment_processed()
                        
                except Exception as e:
                    self.logger.error(f"Error processing data in stream {stream_name}: {e}")
                    self.record_error(str(e))
                    # Continue processing other items
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error processing stream {stream_name}: {e}")
            self.record_error(str(e))
    
    def get_status(self) -> ComponentStatus:
        """Get current component status"""
        return self._status
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Component health check.
        Override in subclasses for component-specific health checks.
        """
        return {
            "status": "healthy" if (self._status.is_running and self._status.is_healthy) else "unhealthy",
            "component": self.__class__.__name__,
            "name": self.name,
            "is_running": self._status.is_running,
            "is_healthy": self._status.is_healthy,
            "items_processed": self._status.items_processed,
            "errors_encountered": self._status.errors_encountered,
            "last_error": self._status.last_error
        }
    
    async def is_ready(self) -> bool:
        """
        Check if component is ready to serve requests.
        Override in subclasses for component-specific readiness checks.
        """
        # For API components, check if server is listening
        if hasattr(self, '_server') and self._server:
            return not self._server.should_exit
        # For other components, check if initialization is complete
        return hasattr(self, '_initialized') and self._initialized or self._status.is_running
    
    def increment_processed(self) -> None:
        """Increment the processed items counter"""
        self._status.items_processed += 1
    
    def record_error(self, error: str) -> None:
        """Record an error in component status"""
        self._status.errors_encountered += 1
        self._status.last_error = error
        self._status.is_healthy = False
    
    # Tracing Helper Methods
    
    def create_trace_context(self, operation_name: str = "process") -> TraceContext:
        """Create a new trace context for this component"""
        if self._current_trace_context:
            return self._current_trace_context.create_child(operation_name)
        return TraceContext.create_new()
    
    def extract_trace_context(self, item: Any) -> Optional[TraceContext]:
        """Extract trace context from an item if present"""
        if isinstance(item, dict) and '_trace_context' in item:
            try:
                return TraceContext.from_dict(item['_trace_context'])
            except Exception:
                pass
        return None
    
    def inject_trace_context(self, item: Any, trace_context: TraceContext) -> Any:
        """Inject trace context into an item for propagation"""
        if isinstance(item, dict):
            item['_trace_context'] = trace_context.to_dict()
            return item
        else:
            # Wrap non-dict items in a dict with trace context
            return {
                'data': item,
                '_trace_context': trace_context.to_dict()
            }
    
    async def send_with_trace(self, stream_name: str, item: Any, operation_name: str = None) -> None:
        """Send an item with trace context propagation"""
        if stream_name not in self.send_streams:
            self.logger.warning(f"Stream '{stream_name}' not found in send_streams")
            return
        
        # Create or propagate trace context
        if self._current_trace_context:
            trace_context = self._current_trace_context.create_child(operation_name or f"{self.name}_send")
        else:
            trace_context = self.create_trace_context(operation_name or f"{self.name}_send")
        
        # Inject trace context and send
        traced_item = self.inject_trace_context(item, trace_context)
        
        # Log trace propagation
        if self._tracer:
            self.logger.info(f"Sending item with trace_id={trace_context.trace_id}, span_id={trace_context.span_id}")
        
        await self.send_streams[stream_name].send(traced_item)
    
    async def receive_with_trace(self, stream_name: str):
        """Async iterator that receives items and extracts trace context"""
        if stream_name not in self.receive_streams:
            raise ValueError(f"Stream '{stream_name}' not found in receive_streams")
        
        # Receive items
        async for item in self.receive_streams[stream_name]:
            # Extract trace context
            trace_context = self.extract_trace_context(item)
            
            if trace_context:
                self._current_trace_context = trace_context
                # Log trace propagation
                if self._tracer:
                    self.logger.info(f"Received item with trace_id={trace_context.trace_id}, span_id={trace_context.span_id}")
                
                # Extract original data if wrapped
                if isinstance(item, dict) and 'data' in item and '_trace_context' in item:
                    yield item['data'], trace_context
                else:
                    # Remove trace context from dict item
                    clean_item = {k: v for k, v in item.items() if k != '_trace_context'} if isinstance(item, dict) else item
                    yield clean_item, trace_context
            else:
                yield item, None