import logging
import time
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


def get_logger(name: str) -> logging.Logger:
    """Create a standalone logger with proper formatting"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class StandaloneMetricsCollector:
    """Standalone metrics collector for observability"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.metrics = {}
        self.logger = get_logger(f"metrics.{component_name}")
    
    def counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Record a counter metric"""
        key = f"{self.component_name}.{name}"
        self.metrics[key] = self.metrics.get(key, 0) + value
        self.logger.debug(f"Counter {key}: {self.metrics[key]}")
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a gauge metric"""
        key = f"{self.component_name}.{name}"
        self.metrics[key] = value
        self.logger.debug(f"Gauge {key}: {value}")
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric"""
        key = f"{self.component_name}.{name}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(value)
        self.logger.debug(f"Histogram {key}: {value}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics"""
        return self.metrics.copy()


class StandaloneTracer:
    """Standalone tracer for observability"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = get_logger(f"tracer.{component_name}")
    
    def start_span(self, name: str, tags: Dict[str, str] = None):
        """Start a new span"""
        return StandaloneSpan(name, self.logger, tags)


class StandaloneSpan:
    """Standalone span implementation"""
    
    def __init__(self, name: str, logger: logging.Logger, tags: Dict[str, str] = None):
        self.name = name
        self.logger = logger
        self.tags = tags or {}
        self.start_time = time.time()
    
    def __enter__(self):
        self.logger.debug(f"Starting span: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.logger.debug(f"Completed span: {self.name} ({duration:.3f}s)")
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.tags[key] = str(value)
    
    def set_tag(self, key: str, value: str):
        """Set span tag"""
        self.tags[key] = value


@dataclass
class ComponentStatus:
    """Status information for a component"""
    is_running: bool = False
    is_healthy: bool = True
    items_processed: int = 0
    errors_encountered: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StandaloneComponentBase:
    """
    Standalone base class for all components.
    Provides all functionality without requiring autocoder_cc imports.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Component.{name}")
        self.metrics_collector = StandaloneMetricsCollector(name)
        self.tracer = StandaloneTracer(name)
        self.created_at = time.time()
        
        # Component state
        self._status = ComponentStatus()
        
        self.logger.info(f"Component {self.name} initialized")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        return {
            'status': 'healthy' if self._status.errors_encountered == 0 else 'degraded',
            'component': self.name,
            'type': self.__class__.__name__,
            'error_count': self._status.errors_encountered,
            'last_error': self._status.last_error,
            'uptime': time.time() - self.created_at,
            'items_processed': self._status.items_processed,
            'is_running': self._status.is_running,
            'is_healthy': self._status.is_healthy
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Async health check"""
        return self.get_health_status()
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors"""
        self._status.errors_encountered += 1
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self._status.last_error = error_msg
        self._status.is_healthy = False
        self.logger.error(f"Error in {self.name}: {error_msg}")
        self.metrics_collector.counter("errors", 1)
    
    def increment_processed(self):
        """Increment processed items counter"""
        self._status.items_processed += 1
        self.metrics_collector.counter("items_processed", 1)
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None):
        """Initialize the component"""
        self._status.is_running = True
        self.logger.info(f"Component {self.name} setup completed")
    
    async def cleanup(self):
        """Cleanup resources"""
        self._status.is_running = False
        self.logger.info(f"Component {self.name} cleanup completed")



from typing import Dict, Any, Optional

class GeneratedAPIEndpoint_hello_world_endpoint(StandaloneComponentBase):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.port = config.get("port", 8080)
        self.host = config.get("host", "0.0.0.0")
        self.greeting_message = config.get("message", "Hello, World!")
        self.logger.info(f"Initialized Hello World API Endpoint '{self.name}' to listen on {self.host}:{self.port} with message: '{self.greeting_message}'")

    async def process_item(self, item: Any = None) -> Any:
        """
        Processes an incoming HTTP request for the Hello World endpoint.
        The 'item' parameter typically represents the incoming request object.
        """
        try:
            # For a simple Hello World, we don't need to inspect the 'item' (request body/params)
            # but we acknowledge its presence.
            
            # Simulate a very quick operation, e.g., fetching a static message
            # A real API might involve database queries, external API calls, etc.
            
            response_data = {
                "status": "success",
                "message": self.greeting_message,
                "timestamp": time.time(), # time.time() is a built-in function, no import needed
                "endpoint_name": self.name,
                "service_host": self.host,
                "service_port": self.port
            }
            
            self.logger.info(f"API request processed successfully. Responding with: '{response_data['message']}'")
            self.increment_processed() # Increment metric for processed requests
            
            return response_data
        except Exception as e:
            # Handle any unexpected errors during processing
            self.handle_error(e, "Failed to process Hello World API request")
            
            # Return an error response to the client
            return {
                "status": "error",
                "message": f"An internal error occurred: {str(e)}",
                "timestamp": time.time(),
                "endpoint_name": self.name
            }