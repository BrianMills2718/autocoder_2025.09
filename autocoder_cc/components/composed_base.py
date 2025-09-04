#!/usr/bin/env python3
"""
ComposedComponent Architecture - Enterprise Roadmap v3 Phase 0
Pure composition over inheritance with capability-based design
"""
import time
from typing import Dict, Any, Optional, List, Type
from autocoder_cc.orchestration.component import Component
from autocoder_cc.error_handling.consistent_handler import handle_errors, ConsistentErrorHandler
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.validation.config_requirement import ConfigRequirement


class ComposedComponent(Component):
    """
    Single unified component base using pure composition over inheritance.
    
    Replaces complex inheritance hierarchies with capability-based composition:
    - RetryHandler capability for resilience
    - CircuitBreaker capability for failure isolation  
    - SchemaValidator capability for data validation
    - RateLimiter capability for throughput control
    - MetricsCollector capability for observability
    
    All capabilities are composed dynamically based on configuration.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = config.get('type', 'Unknown') if config else 'Unknown'
        
        # Initialize consistent error handler
        self.error_handler = ConsistentErrorHandler(self.name)
        
        # Initialize observability stack - Enterprise Roadmap v3 Phase 1
        self.structured_logger = get_logger(f"component.{self.name}", component=self.name)
        self.metrics_collector = get_metrics_collector(self.name)
        self.tracer = get_tracer(self.name)
        
        # Composed capabilities - initialized based on config
        self.capabilities: Dict[str, Any] = {}
        
        # Phase 2: Service communication capabilities
        self.messaging_config = config.get("messaging", {}) if config else {}
        self.message_bridge = None
        
        # Setup all capabilities based on configuration
        self._compose_capabilities()
    
    def _setup_logging(self):
        """Setup component-specific logging - for compatibility with generated code"""
        # Logging is already set up in __init__ via observability stack
        # This method exists for compatibility with LLM-generated components
        pass
    
    def _compose_capabilities(self):
        """Compose capabilities based on configuration - pure composition pattern"""
        
        # Retry capability
        if self.config.get('retry_enabled', True):
            self.capabilities['retry'] = self._create_retry_capability()
        
        # Circuit breaker capability  
        if self.config.get('circuit_breaker_enabled', False):
            self.capabilities['circuit_breaker'] = self._create_circuit_breaker_capability()
        
        # Rate limiter capability
        if self.config.get('rate_limiter_enabled', False):
            self.capabilities['rate_limiter'] = self._create_rate_limiter_capability()
        
        # Schema validator capability
        if self.config.get('schema_validation_enabled', True):
            self.capabilities['schema_validator'] = self._create_schema_validator_capability()
        
        # Metrics collector capability
        if self.config.get('metrics_enabled', True):
            self.capabilities['metrics'] = self._create_metrics_capability()
        
        # Messaging capability (Phase 2)
        if self.messaging_config:
            self.capabilities['messaging'] = self._create_messaging_capability()
    
    def _create_retry_capability(self):
        """Create retry handler capability"""
        from autocoder_cc.capabilities.retry_handler import RetryHandler
        # FAIL-FAST: Required capability must be available
        return RetryHandler(**self.config.get('retry', {}))
    
    def _create_circuit_breaker_capability(self):
        """Create circuit breaker capability"""
        from autocoder_cc.capabilities.circuit_breaker import CircuitBreaker
        # FAIL-FAST: Required capability must be available
        return CircuitBreaker(**self.config.get('circuit_breaker', {}))
    
    def _create_rate_limiter_capability(self):
        """Create rate limiter capability"""
        from autocoder_cc.capabilities.rate_limiter import RateLimiter
        # FAIL-FAST: Required capability must be available
        return RateLimiter(**self.config.get('rate_limiter', {}))
    
    def _create_schema_validator_capability(self):
        """Create schema validator capability"""
        from autocoder_cc.capabilities.schema_validator import SchemaValidator
        # FAIL-FAST: Required capability must be available
        return SchemaValidator(**self.config.get('schema_validation', {}))
    
    def _create_metrics_capability(self):
        """Create metrics collector capability"""
        from autocoder_cc.capabilities.metrics_collector import MetricsCollector
        # FAIL-FAST: Required capability must be available
        return MetricsCollector(self.name)
    
    def _create_messaging_capability(self):
        """Create messaging capability for service communication - FAIL-FAST implementation"""
        bridge_type = self.messaging_config.get("bridge_type", "anyio_rabbitmq")
        
        # FAIL-FAST: Validate bridge type is supported before attempting import
        valid_bridge_types = ["anyio_rabbitmq", "anyio_kafka", "anyio_http"]
        if bridge_type not in valid_bridge_types:
            raise ValueError(f"Unsupported bridge type: {bridge_type}. Must be one of: {valid_bridge_types}")
        
        # FAIL-FAST: Import the required bridge module - let ImportError propagate
        if bridge_type == "anyio_rabbitmq":
            from autocoder_cc.messaging.bridges.anyio_rabbitmq_bridge import AnyIORabbitMQBridge
            rabbitmq_url = self.messaging_config.get("rabbitmq_url", "amqp://localhost")
            queue_name = self.messaging_config.get("queue_name", f"{self.name}_queue")
            return AnyIORabbitMQBridge(rabbitmq_url, self.name, queue_name)
            
        elif bridge_type == "anyio_kafka":
            from autocoder_cc.messaging.bridges.anyio_kafka_bridge import AnyIOKafkaBridge
            bootstrap_servers = self.messaging_config.get("bootstrap_servers", "localhost:9092")
            topic_name = self.messaging_config.get("topic_name", f"{self.name}_topic")
            return AnyIOKafkaBridge(bootstrap_servers, self.name, topic_name)
            
        elif bridge_type == "anyio_http":
            from autocoder_cc.messaging.bridges.anyio_http_bridge import AnyIOHTTPBridge
            host = self.messaging_config.get("host", "localhost")
            port = self.messaging_config.get("port", 8080)
            return AnyIOHTTPBridge(self.name, host, port)
    
    @handle_errors("ComposedComponent")
    async def process(self) -> None:
        """
        Main processing loop with Enterprise Roadmap v3 observability integration.
        
        Features:
        - Structured logging with trace correlation
        - Metrics collection for performance monitoring
        - Distributed tracing for component communication
        - Capability composition (retry, circuit breaking, etc.)
        """
        # Start processing trace
        with self.tracer.span("component.process", tags={'component_type': self.component_type}) as span_id:
            
            self.structured_logger.info(
                "Starting component processing",
                operation="process_start",
                tags={'component_type': self.component_type}
            )
            
            # Record component start metrics
            self.metrics_collector.record_component_start()
            
            if not self.receive_streams:
                self.structured_logger.warning(
                    "Component has no input streams configured",
                    operation="process_validation"
                )
                return
            
            # Get primary input stream
            primary_stream_name = list(self.receive_streams.keys())[0]
            primary_stream = self.receive_streams[primary_stream_name]
            
            self.structured_logger.debug(
                f"Processing items from stream: {primary_stream_name}",
                operation="stream_processing",
                tags={'stream_name': primary_stream_name}
            )
            
            async for item in primary_stream:
                try:
                    # Start item processing span  
                    with self.tracer.span("item.process") as item_span_id:
                        start_time = time.time()
                        
                        # Apply rate limiting capability if enabled
                        if 'rate_limiter' in self.capabilities and self.capabilities['rate_limiter']:
                            await self.capabilities['rate_limiter'].acquire()
                        
                        # Validate input schema if capability enabled
                        if 'schema_validator' in self.capabilities and self.capabilities['schema_validator']:
                            item = self.capabilities['schema_validator'].validate_input(item)
                        
                        # Process item with retry capability if enabled
                        if 'retry' in self.capabilities and self.capabilities['retry']:
                            result = await self.capabilities['retry'].execute(self.process_item, item)
                        elif 'circuit_breaker' in self.capabilities and self.capabilities['circuit_breaker']:
                            result = await self.capabilities['circuit_breaker'].execute(self.process_item, item)
                        else:
                            result = await self.process_item(item)
                        
                        # Validate output schema if capability enabled
                        if result is not None and 'schema_validator' in self.capabilities and self.capabilities['schema_validator']:
                            result = self.capabilities['schema_validator'].validate_output(result)
                        
                        # Send result to output streams
                        if result is not None and self.send_streams:
                            for output_name, output_stream in self.send_streams.items():
                                await output_stream.send(result)
                        
                        # Record successful processing metrics
                        processing_time = (time.time() - start_time) * 1000
                        self.metrics_collector.record_items_processed()
                        self.metrics_collector.record_processing_time(processing_time)
                        
                        self.structured_logger.debug(
                            f"Processed item successfully",
                            operation="item_processed",
                            metrics={'processing_time_ms': processing_time}
                        )
                        
                        self.increment_processed()
                        
                except Exception as e:
                    # Record error metrics
                    self.metrics_collector.record_error(e.__class__.__name__)
                    
                    self.structured_logger.error(
                        f"Item processing failed",
                        error=e,
                        operation="item_processing_error",
                        tags={'error_type': e.__class__.__name__}
                    )
                    
                    # Add error to current span
                    if item_span_id:
                        self.tracer.add_span_log(item_span_id, f"Processing error: {e}", "error")
                    
                    await self.error_handler.handle_exception(
                        e, 
                        context={"item": str(item), "component_type": self.component_type},
                        operation="process_item"
                    )
                finally:
                    # Release rate limiter if capability enabled
                    if 'rate_limiter' in self.capabilities and self.capabilities['rate_limiter']:
                        self.capabilities['rate_limiter'].release()
    
    async def process_item(self, item: Any) -> Any:
        """
        Process a single item - implement in subclasses for component-specific logic.
        
        This method should contain the core business logic for the component.
        Capabilities (retry, circuit breaking, etc.) are handled transparently.
        
        Args:
            item: The item to process
            
        Returns:
            The processed result or None to filter out the item
        """
        # Default implementation - pass through
        return item
    
    # Capability accessor methods for clean API
    def has_capability(self, capability_name: str) -> bool:
        """Check if component has a specific capability"""
        return capability_name in self.capabilities and self.capabilities[capability_name] is not None
    
    def get_capability(self, capability_name: str) -> Optional[Any]:
        """Get a specific capability instance"""
        return self.capabilities.get(capability_name)
    
    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry capability if available"""
        if self.has_capability('retry'):
            return await self.capabilities['retry'].execute(operation, *args, **kwargs)
        else:
            return await operation(*args, **kwargs)
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record metric using metrics capability if available"""
        if self.has_capability('metrics'):
            self.capabilities['metrics'].record(metric_name, value, tags or {})
    
    async def execute_with_circuit_breaker(self, operation, *args, **kwargs):
        """Execute operation with circuit breaker if available"""
        if self.has_capability('circuit_breaker'):
            return await self.capabilities['circuit_breaker'].execute(operation, *args, **kwargs)
        else:
            return await operation(*args, **kwargs)
    
    async def execute_with_rate_limit(self, operation, *args, **kwargs):
        """Execute operation with rate limiting if available"""
        if self.has_capability('rate_limiter'):
            await self.capabilities['rate_limiter'].acquire()
            try:
                return await operation(*args, **kwargs)
            finally:
                self.capabilities['rate_limiter'].release()
        else:
            return await operation(*args, **kwargs)
    
    def validate_data(self, data: Any, schema_type: str = 'input') -> Any:
        """Validate data using schema validator capability if available"""
        if self.has_capability('schema_validator'):
            if schema_type == 'input':
                return self.capabilities['schema_validator'].validate_input(data)
            elif schema_type == 'output':
                return self.capabilities['schema_validator'].validate_output(data)
        return data
    
    # Enhanced health check with capability status
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status including all capability statuses"""
        # Base health information (since Component doesn't have get_health_status)
        base_health = {
            'name': self.name,
            'healthy': True,  # Basic assumption - can be overridden by capabilities
        }
        
        # Add capability health status
        capability_health = {}
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'get_status'):
                capability_health[cap_name] = capability.get_status()
            else:
                capability_health[cap_name] = {'status': 'disabled' if capability is None else 'active'}
        
        return {
            **base_health,
            'component_type': self.component_type,
            'capabilities': capability_health,
            'composition_model': 'capability_based'
        }
    
    # Dynamic capability management
    def add_capability(self, capability_name: str, capability_instance: Any):
        """Dynamically add a capability at runtime"""
        self.capabilities[capability_name] = capability_instance
        self.logger.info(f"Added capability '{capability_name}' to component {self.name}")
    
    def remove_capability(self, capability_name: str):
        """Dynamically remove a capability at runtime"""
        if capability_name in self.capabilities:
            del self.capabilities[capability_name]
            self.logger.info(f"Removed capability '{capability_name}' from component {self.name}")
    
    def reconfigure_capability(self, capability_name: str, new_config: Dict[str, Any]):
        """Reconfigure a specific capability"""
        if self.has_capability(capability_name):
            capability = self.capabilities[capability_name]
            if hasattr(capability, 'reconfigure'):
                capability.reconfigure(new_config)
                self.logger.info(f"Reconfigured capability '{capability_name}' for component {self.name}")
    
    # Component lifecycle with capability management
    async def _start_component(self):
        """Start all capabilities during component startup"""
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'start'):
                await capability.start()
                self.logger.debug(f"Started capability '{cap_name}' for component {self.name}")
        
        # Initialize messaging bridge if configured
        if self.has_capability('messaging'):
            await self.setup_messaging()
    
    async def _stop_component(self):
        """Stop all capabilities during component shutdown"""
        # Stop messaging bridge first
        if self.message_bridge:
            await self.message_bridge.stop()
            self.message_bridge = None
        
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'stop'):
                await capability.stop()
                self.logger.debug(f"Stopped capability '{cap_name}' for component {self.name}")
    
    def _cleanup_component(self):
        """Cleanup all capabilities during component cleanup"""
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'cleanup'):
                capability.cleanup()
                self.logger.debug(f"Cleaned up capability '{cap_name}' for component {self.name}")
    
    # Type checking helpers for backwards compatibility
    def is_source(self) -> bool:
        """Check if this is a source component"""
        return self.component_type.lower() in ['source', 'generated_source']
    
    def is_transformer(self) -> bool:
        """Check if this is a transformer component"""
        return self.component_type.lower() in ['transformer', 'generated_transformer']
    
    def is_sink(self) -> bool:
        """Check if this is a sink component"""
        return self.component_type.lower() in ['sink', 'generated_sink']
    
    def is_store(self) -> bool:
        """Check if this is a store component"""
        return self.component_type.lower() in ['store', 'generated_store']
    
    def is_api_endpoint(self) -> bool:
        """Check if this is an API endpoint component"""
        return self.component_type.lower() in ['apiendpoint', 'api_endpoint', 'generated_apiendpoint']
    
    # Required methods for component registry
    @classmethod
    def get_required_config_fields(cls) -> List[str]:
        """Get list of required configuration fields for this component"""
        return []  # ComposedComponent has no required config fields by default
    
    @classmethod
    def get_required_dependencies(cls) -> List[str]:
        """Get list of required dependencies for this component"""
        return []  # ComposedComponent has no required dependencies by default
    
    async def start(self) -> None:
        """
        Start the component. Calls setup() from base Component class.
        Override in subclasses for component-specific startup logic.
        """
        await self.setup()
    
    async def stop(self) -> None:
        """
        Stop the component. Calls cleanup() from base Component class.
        Override in subclasses for component-specific shutdown logic.
        """
        await self.cleanup()
    
    async def is_ready(self) -> bool:
        """
        Check if component is ready to serve requests.
        Override in subclasses for component-specific readiness checks.
        """
        return True  # Default implementation
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Component health check.
        Override in subclasses for component-specific health checks.
        """
        return {
            "status": "healthy",
            "component": self.__class__.__name__,
            "name": getattr(self, 'name', 'unknown')
        }
    
    # Phase 2: Service communication methods
    async def setup_messaging(self):
        """Setup messaging bridge for component communication - FAIL-FAST"""
        if not self.has_capability('messaging'):
            raise RuntimeError("Messaging capability is required but not available (fail-fast principle)")
        
        try:
            self.message_bridge = self.capabilities['messaging']
            await self.message_bridge.initialize()
            await self.message_bridge.start()
            
            self.structured_logger.info(f"Messaging bridge initialized for component {self.name}")
            
        except Exception as e:
            self.structured_logger.error(f"Failed to setup messaging: {e}")
            raise RuntimeError(f"Failed to setup messaging: {e}")
    
    async def send_message(self, message: Any) -> None:
        """Send a message through the messaging bridge - FAIL-FAST"""
        if not self.message_bridge:
            raise RuntimeError("No messaging bridge available - component not properly initialized (fail-fast principle)")
        
        try:
            await self.message_bridge.send_message(message)
            self.structured_logger.debug(f"Sent message through bridge: {type(message).__name__}")
            
        except Exception as e:
            self.structured_logger.error(f"Failed to send message: {e}")
            raise RuntimeError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Any:
        """Receive a message through the messaging bridge - FAIL-FAST"""
        if not self.message_bridge:
            raise RuntimeError("No messaging bridge available - component not properly initialized (fail-fast principle)")
        
        try:
            message = await self.message_bridge.receive_message()
            self.structured_logger.debug(f"Received message through bridge: {type(message).__name__}")
            return message
            
        except Exception as e:
            self.structured_logger.error(f"Failed to receive message: {e}")
            raise RuntimeError(f"Failed to receive message: {e}")
    
    async def get_messaging_health(self) -> Dict[str, Any]:
        """Get messaging bridge health status"""
        if not self.message_bridge:
            return {"status": "disabled", "bridge": None}
        
        try:
            return await self.message_bridge.health_check()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_messaging_channels(self) -> Optional[Dict[str, Any]]:
        """Get AnyIO channels for direct integration"""
        if not self.message_bridge:
            return None
        
        try:
            return self.message_bridge.get_anyio_channels()
        except Exception as e:
            self.structured_logger.error(f"Failed to get messaging channels: {e}")
            return None    
    @classmethod
    def get_config_requirements(cls, component_type: str = None) -> List[ConfigRequirement]:
        """
        Get configuration requirements for this component type.
        
        This method provides component-specific configuration requirements
        based on the component type. It's used by the validation pipeline
        to ensure configurations are complete and valid before generation.
        
        Args:
            component_type: The type of component (Source, Transformer, etc.)
                          If not provided, attempts to determine from class name
        
        Returns:
            List of ConfigRequirement objects defining required/optional fields
        """
        # If component_type not provided, try to determine from class name
        if not component_type:
            component_type = cls.__name__.replace("ComposedComponent", "").strip()
        
        # Define requirements based on component type
        requirements_map = {
            "Source": [
                ConfigRequirement(
                    name="data_source",
                    type="str",
                    required=True,
                    description="Data source URL or path",
                    example="file://data.json",
                    semantic_type="url"
                ),
                ConfigRequirement(
                    name="auth_token",
                    type="str",
                    required=True,
                    description="Authentication token for secure sources",
                    # No example or default - this will require LLM or user input
                    semantic_type="secret"
                ),
                ConfigRequirement(
                    name="poll_interval",
                    type="int",
                    required=False,
                    default=60,
                    description="Polling interval in seconds"
                )
            ],
            "Transformer": [
                ConfigRequirement(
                    name="transformation_type",
                    type="str",
                    required=False,
                    default="passthrough",
                    description="Type of transformation to apply"
                )
            ],
            "Sink": [
                ConfigRequirement(
                    name="destination",
                    type="str",
                    required=True,
                    description="Destination for data output",
                    example="file://output.json"
                )
            ],
            "Filter": [
                ConfigRequirement(
                    name="filter_conditions",
                    type="list",
                    required=False,
                    default=[],
                    description="List of filter conditions"
                )
            ],
            "Store": [
                ConfigRequirement(
                    name="database_url",
                    type="str",
                    required=True,
                    description="Database connection URL",
                    example="postgresql://localhost/db"
                ),
                ConfigRequirement(
                    name="table_name",
                    type="str",
                    required=False,
                    default="data",
                    description="Table name for storage"
                )
            ],
            "Controller": [
                ConfigRequirement(
                    name="control_logic",
                    type="str",
                    required=False,
                    default="sequential",
                    description="Control flow logic type"
                )
            ],
            "APIEndpoint": [
                ConfigRequirement(
                    name="port",
                    type="int",
                    required=False,
                    default=8080,
                    description="Port to listen on"
                ),
                ConfigRequirement(
                    name="host",
                    type="str",
                    required=False,
                    default="0.0.0.0",
                    description="Host to bind to"
                )
            ],
            "Model": [
                ConfigRequirement(
                    name="model_path",
                    type="str",
                    required=False,
                    default="./model.pkl",
                    description="Path to model file"
                )
            ],
            "Accumulator": [
                ConfigRequirement(
                    name="batch_size",
                    type="int",
                    required=False,
                    default=100,
                    description="Batch size for accumulation"
                ),
                ConfigRequirement(
                    name="timeout",
                    type="int",
                    required=False,
                    default=60,
                    description="Timeout in seconds"
                )
            ],
            "Router": [
                ConfigRequirement(
                    name="routing_rules",
                    type="list",
                    required=False,
                    default=[],
                    description="List of routing rules"
                )
            ],
            "Aggregator": [
                ConfigRequirement(
                    name="aggregation_function",
                    type="str",
                    required=False,
                    default="sum",
                    description="Aggregation function to apply"
                ),
                ConfigRequirement(
                    name="window_size",
                    type="int",
                    required=False,
                    default=10,
                    description="Window size for aggregation"
                )
            ],
            "StreamProcessor": [
                ConfigRequirement(
                    name="stream_config",
                    type="dict",
                    required=False,
                    default={},
                    description="Stream processing configuration"
                )
            ],
            "WebSocket": [
                ConfigRequirement(
                    name="websocket_url",
                    type="str",
                    required=False,
                    default="ws://localhost:8080",
                    description="WebSocket server URL"
                ),
                ConfigRequirement(
                    name="reconnect_interval",
                    type="int",
                    required=False,
                    default=5,
                    description="Reconnection interval in seconds"
                )
            ]
        }
        
        # Return requirements for this component type, or empty list if unknown
        return requirements_map.get(component_type, [])
