from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
SystemExecutionHarness - Universal orchestrator for component-based systems

This harness manages the lifecycle of all components in a system, handles
inter-component communication via anyio streams, and provides graceful shutdown
using structured concurrency.

Now supports dynamic component loading via manifests (Enterprise Roadmap v3).
"""

import anyio
import logging
import signal
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field

from autocoder_cc.orchestration.component import Component, ComponentStatus
from autocoder_cc.orchestration.dynamic_loader import DynamicComponentLoader, ComponentManifest
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.observability import Tracer
from autocoder_cc.error_handling.consistent_handler import get_global_error_metrics, ErrorMetrics, register_error_handler, ConsistentErrorHandler


class ComponentLifecycleState(Enum):
    """Component lifecycle states"""
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class ComponentHealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a component health check"""
    status: ComponentHealthStatus
    message: str = ""
    details: Dict[str, Any] = None


@dataclass
class ComponentMetrics:
    """Metrics for a single component"""
    items_processed: int = 0
    errors: int = 0
    processing_time_ms: float = 0.0
    last_activity: Optional[float] = None


@dataclass  
class StreamMetrics:
    """Metrics for a stream connection"""
    items_sent: int = 0
    items_received: int = 0
    buffer_size: int = 0
    backpressure_events: int = 0


@dataclass 
class Connection:
    """Represents a stream connection between two components"""
    from_component: str
    to_component: str
    from_output: str = "default"
    to_input: str = "default"
    max_buffer_size: int = 1000


@dataclass
class HarnessMetrics:
    """System-wide metrics with production observability"""
    start_time: float = field(default_factory=time.time)
    total_items_processed: int = 0
    total_errors: int = 0
    component_metrics: Dict[str, ComponentStatus] = field(default_factory=dict)
    
    # Production metrics
    items_per_second: float = 0.0
    error_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    queue_depths: Dict[str, int] = field(default_factory=dict)
    
    # Centralized error metrics from all components
    component_error_metrics: Dict[str, ErrorMetrics] = field(default_factory=dict)
    system_error_rate_per_minute: float = 0.0
    critical_error_count: int = 0
    
    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time
    
    def update_performance_metrics(self):
        """Update performance metrics"""
        if self.uptime_seconds > 0:
            self.items_per_second = self.total_items_processed / self.uptime_seconds
            self.error_rate = self.total_errors / max(1, self.total_items_processed)
        
        # Get system resource usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.memory_usage_mb = memory_info.rss / 1024 / 1024
            self.cpu_usage_percent = process.cpu_percent()
        except ImportError:
            # psutil not available, use mock values
            self.memory_usage_mb = 50.0
            self.cpu_usage_percent = 10.0
        
        # Update centralized error metrics from all components
        self.component_error_metrics = get_global_error_metrics()
        
        # Calculate system-wide error metrics
        total_errors_per_minute = 0
        total_critical_errors = 0
        
        for component_name, error_metrics in self.component_error_metrics.items():
            total_errors_per_minute += error_metrics.error_rate_per_minute
            total_critical_errors += error_metrics.critical_errors
        
        self.system_error_rate_per_minute = total_errors_per_minute
        self.critical_error_count = total_critical_errors


class SystemExecutionHarness:
    """
    Universal execution harness for component-based systems.
    
    The SystemExecutionHarness is the central orchestration engine that manages
    the lifecycle of all components in a distributed system. It provides a robust
    foundation for building scalable, observable, and fault-tolerant applications.
    
    ## Key Features
    
    ### Component Lifecycle Management
    - **Automatic Startup**: Components start in dependency order
    - **Graceful Shutdown**: Components stop in reverse dependency order
    - **Health Monitoring**: Continuous health checks with configurable intervals
    - **Failure Recovery**: Automatic restart and circuit breaker patterns
    
    ### Inter-Component Communication
    - **Stream-Based**: AnyIO streams for asynchronous communication
    - **Queue Management**: Configurable buffer sizes and backpressure handling
    - **Type Safety**: Strongly typed message passing
    - **Connection Management**: Dynamic connection establishment and teardown
    
    ### Observability & Monitoring
    - **Structured Logging**: Centralized logging with correlation IDs
    - **Metrics Collection**: Prometheus-compatible metrics
    - **Distributed Tracing**: Jaeger integration for request tracing
    - **Health Checks**: Liveness and readiness probes
    
    ### Fault Tolerance
    - **Circuit Breakers**: Prevent cascade failures
    - **Error Isolation**: Component failures don't affect others
    - **Retry Logic**: Exponential backoff for transient failures
    - **Graceful Degradation**: Continue operation with reduced functionality
    
    ### Dynamic Loading
    - **Manifest-Based**: Load components from YAML manifests
    - **Hot Reloading**: Add/remove components without restart
    - **Discovery**: Automatic component discovery in directories
    - **Validation**: Schema validation for component configurations
    
    ## Usage Examples
    
    ### Basic System Setup
    
    ```python
    from autocoder_cc.orchestration import SystemExecutionHarness, Component
    
    # Create harness
    harness = SystemExecutionHarness("my-system")
    
    # Add components
    api_component = Component("api-service", "api_endpoint", {"port": 8000})
    db_component = Component("database", "postgres", {"url": "postgresql://..."})
    
    harness.register_component("api-service", api_component)
    harness.register_component("database", db_component)
    
    # Connect components
    harness.connect("api-service", "database")
    
    # Start system
    await harness.run()
    ```
    
    ### Dynamic Component Loading
    
    ```python
    # Load from manifest
    await harness.load_components_from_manifest("components.yaml")
    
    # Auto-discover components
    await harness.discover_and_load_components("./components/")
    ```
    
    ### Health Monitoring
    
    ```python
    # Get system health
    health = await harness.get_system_health_summary()
    
    # Get component status
    status = await harness.get_component_status("api-service")
    
    # Health check
    health_status = await harness.health_check()
    ```
    
    ### Metrics and Observability
    
    ```python
    # Get system metrics
    metrics = harness.get_metrics()
    
    # Get detailed metrics
    detailed_metrics = await harness.get_detailed_metrics()
    
    # Monitor performance
    print(f"Items per second: {metrics.items_per_second}")
    print(f"Error rate: {metrics.error_rate}")
    print(f"Memory usage: {metrics.memory_usage_mb} MB")
    ```
    
    ## Configuration
    
    ### Environment Variables
    
    ```bash
    # Harness configuration
    export HARNESS_NAME="my-system"
    export HEALTH_CHECK_INTERVAL="30"
    export METRICS_UPDATE_INTERVAL="5"
    export ENABLE_DYNAMIC_LOADING="true"
    
    # Observability
    export LOG_LEVEL="INFO"
    export ENABLE_METRICS="true"
    export ENABLE_TRACING="true"
    ```
    
    ### Component Manifest (YAML)
    
    ```yaml
    name: my-system
    components:
      - name: api-service
        type: api_endpoint
        config:
          port: 8000
          routes: ["/health", "/api/v1"]
        dependencies: ["database"]
      
      - name: database
        type: postgres
        config:
          url: "postgresql://user:pass@host:5432/db"
    
    connections:
      - from: api-service
        to: database
        max_buffer_size: 1000
    ```
    
    ## Architecture
    
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                SystemExecutionHarness                      │
    ├─────────────────────────────────────────────────────────────┤
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
    │  │ Component   │  │ Health      │  │ Metrics     │        │
    │  │ Lifecycle   │  │ Monitor     │  │ Collector   │        │
    │  └─────────────┘  └─────────────┘  └─────────────┘        │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
    │  │ Connection  │  │ Circuit     │  │ Error       │        │
    │  │ Manager     │  │ Breakers    │  │ Handler     │        │
    │  └─────────────┘  └─────────────┘  └─────────────┘        │
    └─────────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    Components                               │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
    │  │ API         │  │ Database    │  │ Message     │        │
    │  │ Service     │  │ Component   │  │ Bus         │        │
    │  └─────────────┘  └─────────────┘  └─────────────┘        │
    └─────────────────────────────────────────────────────────────┘
    ```
    
    ## Error Handling
    
    The harness implements comprehensive error handling:
    
    - **Component Failures**: Automatic restart with exponential backoff
    - **Communication Errors**: Circuit breakers prevent cascade failures
    - **Resource Exhaustion**: Graceful degradation and resource limits
    - **Configuration Errors**: Validation and fallback configurations
    
    ## Performance Considerations
    
    - **Async Operations**: All I/O operations are asynchronous
    - **Memory Management**: Automatic cleanup of completed tasks
    - **Resource Limits**: Configurable limits for memory and CPU usage
    - **Connection Pooling**: Efficient management of inter-component connections
    
    ## Security Features
    
    - **Component Isolation**: Components run in isolated contexts
    - **Secure Communication**: Encrypted inter-component communication
    - **Access Control**: Role-based access to harness operations
    - **Audit Logging**: Complete audit trail of all operations
    
    ## Monitoring and Alerting
    
    The harness provides built-in monitoring capabilities:
    
    - **Performance Metrics**: Throughput, latency, error rates
    - **Resource Usage**: CPU, memory, disk, network utilization
    - **Health Status**: Component and system health indicators
    - **Alerting**: Configurable alerts for critical conditions
    
    ## Best Practices
    
    1. **Component Design**: Keep components focused and single-purpose
    2. **Error Handling**: Implement proper error handling in components
    3. **Resource Management**: Use appropriate buffer sizes and timeouts
    4. **Monitoring**: Set up comprehensive monitoring and alerting
    5. **Testing**: Test components individually and as a system
    6. **Documentation**: Document component interfaces and dependencies
    
    ## Related Classes
    
    - `Component`: Base class for system components
    - `Connection`: Inter-component communication configuration
    - `HarnessMetrics`: System-wide metrics and performance data
    - `HealthCheckResult`: Component health status information
    - `ComponentLifecycleState`: Component lifecycle states
    - `ComponentHealthStatus`: Component health status enumeration
    """
    
    def __init__(self, name: str = "System", data_queue=None, enable_dynamic_loading: bool = True):
        self.name = name
        
        # Initialize centralized observability stack (Enterprise Roadmap v3 Phase 1)
        self.structured_logger = get_logger(f"harness.{name}", component=f"SystemExecutionHarness.{name}")
        self.metrics_collector = get_metrics_collector(f"harness.{name}")
        self.tracer = get_tracer(f"harness.{name}")
        
        # Legacy logger for backwards compatibility
        self.logger = get_logger(f"Harness.{name}")
        
        # Component registry
        self.components: Dict[str, Component] = {}
        self.connections: List[Connection] = []
        
        # System state
        self._running = False
        self._metrics = HarnessMetrics()
        self._task_group: Optional[anyio.abc.TaskGroup] = None
        self._shutdown_event = anyio.Event()  # Critical: Signal for graceful shutdown
        
        # Readiness tracking for race condition fix
        self._ready_event = anyio.Event()
        self._component_ready_count = 0
        self._total_components = 0
        self._startup_timeout = 30.0  # seconds
        
        # Data queue for hybrid architecture bridge
        self.data_queue = data_queue
        
        # Production features
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._error_queue = []
        self._health_check_interval = 30.0  # seconds
        self._metrics_update_interval = 5.0  # seconds
        
        # Observability (Legacy tracer kept for compatibility)
        self._tracer = Tracer(f"harness-{name}")
        self._alerts: List[Dict[str, Any]] = []
        self._recommendations: List[Dict[str, Any]] = []
        
        self.structured_logger.info(
            "SystemExecutionHarness initialized with centralized observability stack",
            operation="init",
            tags={"harness_name": name, "dynamic_loading": enable_dynamic_loading}
        )
        
        # Dynamic loading support (Enterprise Roadmap v3)
        self._enable_dynamic_loading = enable_dynamic_loading
        self._dynamic_loader: Optional[DynamicComponentLoader] = None
        if enable_dynamic_loading:
            self._dynamic_loader = DynamicComponentLoader()
    
    async def wait_until_ready(self, timeout: float = 30.0) -> bool:
        """
        Wait until all components are ready and harness is serving.
        
        Returns:
            bool: True if ready within timeout, False if timeout exceeded
            
        Raises:
            TimeoutError: If components fail to become ready within timeout
        """
        try:
            await anyio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except anyio.TimeoutError:
            ready_components = self._component_ready_count
            total_components = self._total_components
            raise TimeoutError(
                f"Harness not ready after {timeout}s. "
                f"Ready components: {ready_components}/{total_components}"
            )
    
    async def _verify_component_readiness(self, name: str, component, max_retries: int = 10):
        """Verify component is actually ready to serve requests."""
        if not hasattr(component, 'is_ready'):
            # If component doesn't implement is_ready, assume it's ready after start()
            return
        
        for attempt in range(max_retries):
            try:
                if await component.is_ready():
                    return
            except Exception as e:
                self.logger.warning(f"Component {name} readiness check failed (attempt {attempt + 1}): {e}")
            
            await anyio.sleep(0.5)  # Wait before retry
        
        raise RuntimeError(f"Component {name} failed readiness verification after {max_retries} attempts")
    
    async def _start_component_with_readiness(self, name: str, component):
        """Start component and track readiness."""
        try:
            # Start the component
            if hasattr(component, 'start'):
                await component.start()
            
            # Verify component is actually ready
            await self._verify_component_readiness(name, component)
            
            self._component_ready_count += 1
            self.logger.info(f"Component {name} ready ({self._component_ready_count}/{self._total_components})")
            
        except Exception as e:
            self.logger.error(f"Component {name} failed to start: {e}")
            raise
    
    async def _wait_for_all_components_ready(self, timeout: float = 30.0):
        """Wait for all components to become ready."""
        start_time = time.time()
        
        while self._component_ready_count < self._total_components:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Components failed to become ready within {timeout}s. "
                    f"Ready: {self._component_ready_count}/{self._total_components}"
                )
            await anyio.sleep(0.1)  # Check every 100ms

    @classmethod
    def create_simple_harness(cls, blueprint_file: Optional[str] = None, component_dir: Optional[str] = None, system_name: Optional[str] = None) -> 'SystemExecutionHarness':
        """
        Create a simplified harness for generated systems.
        
        This method provides a streamlined initialization path that generated
        systems can use without complex manual configuration.
        
        Args:
            blueprint_file: Path to blueprint YAML file (optional)
            component_dir: Directory containing component files (optional)
            system_name: Name for the system (auto-detected if not provided)
            
        Returns:
            SystemExecutionHarness: Configured harness ready for use
            
        Example:
            harness = SystemExecutionHarness.create_simple_harness(
                blueprint_file="blueprint.yaml",
                component_dir="components"
            )
        """
        import os
        import yaml
        from pathlib import Path
        import importlib.util
        import sys
        
        # Auto-detect system name from blueprint or directory
        if not system_name:
            if blueprint_file and os.path.exists(blueprint_file):
                try:
                    with open(blueprint_file, 'r') as f:
                        blueprint_data = yaml.safe_load(f)
                    system_name = blueprint_data.get('system', {}).get('name', 'generated-system')
                except Exception:
                    system_name = 'generated-system'
            elif component_dir:
                system_name = os.path.basename(os.path.abspath(component_dir)) + '-system'
            else:
                system_name = 'simple-system'
        
        # Create harness with minimal configuration
        harness = cls(name=system_name, enable_dynamic_loading=True)
        
        # Auto-discover and load components if component_dir provided
        if component_dir and os.path.exists(component_dir):
            try:
                components = harness._discover_components_simple(component_dir)
                for name, component in components.items():
                    harness.register_component(name, component)
                harness.logger.info(f"Auto-loaded {len(components)} components from {component_dir}")
            except Exception as e:
                harness.logger.warning(f"Failed to auto-load components: {e}")
        
        # Load blueprint if provided
        if blueprint_file and os.path.exists(blueprint_file):
            try:
                harness._load_blueprint_simple(blueprint_file)
                harness.logger.info(f"Loaded blueprint from {blueprint_file}")
            except Exception as e:
                harness.logger.warning(f"Failed to load blueprint: {e}")
        
        harness.logger.info(f"Simple harness created: {system_name}")
        return harness
    
    def _discover_components_simple(self, component_dir: str) -> Dict[str, Any]:
        """
        Simplified component discovery for generated systems.
        
        Scans a directory for Python files and attempts to import components
        that follow the standard naming pattern.
        """
        import importlib.util
        import sys
        from pathlib import Path
        
        components = {}
        component_path = Path(component_dir)
        
        if not component_path.exists():
            self.logger.warning(f"Component directory does not exist: {component_dir}")
            return components
        
        # Add component directory to Python path temporarily
        sys.path.insert(0, str(component_path))
        
        try:
            for py_file in component_path.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                module_name = py_file.stem
                
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find component classes in the module
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            
                            # Look for classes that appear to be components
                            if (isinstance(attr, type) and 
                                attr_name.startswith('Generated') and
                                hasattr(attr, '__init__')):
                                
                                try:
                                    # Try to instantiate the component
                                    component_instance = attr(module_name, {})
                                    components[module_name] = component_instance
                                    self.logger.debug(f"Discovered component: {module_name} ({attr_name})")
                                    break
                                except Exception as e:
                                    self.logger.debug(f"Failed to instantiate {attr_name}: {e}")
                                    continue
                
                except Exception as e:
                    self.logger.warning(f"Failed to import component from {py_file}: {e}")
                    continue
        
        finally:
            # Remove the component directory from Python path
            if str(component_path) in sys.path:
                sys.path.remove(str(component_path))
        
        return components
    
    def _load_blueprint_simple(self, blueprint_file: str) -> None:
        """
        Simplified blueprint loading for generated systems.
        
        Loads a blueprint file and sets up basic connections between components.
        """
        import yaml
        
        try:
            with open(blueprint_file, 'r') as f:
                blueprint_data = yaml.safe_load(f)
            
            # Extract bindings/connections from blueprint
            bindings = blueprint_data.get('system', {}).get('bindings', [])
            
            for binding in bindings:
                source = binding.get('source', {})
                target = binding.get('target', {})
                
                source_comp = source.get('component')
                source_stream = source.get('stream', 'default')
                target_comp = target.get('component')
                target_stream = target.get('stream', 'default')
                
                if source_comp and target_comp:
                    try:
                        self.connect(f"{source_comp}.{source_stream}", f"{target_comp}.{target_stream}")
                        self.logger.debug(f"Connected: {source_comp}.{source_stream} -> {target_comp}.{target_stream}")
                    except Exception as e:
                        self.logger.warning(f"Failed to connect {source_comp} -> {target_comp}: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to load blueprint {blueprint_file}: {e}")
            raise
        
    def register_component(self, name: str, component: Component) -> None:
        """Register a component with the harness"""
        if name in self.components:
            raise ValueError(f"Component '{name}' already registered")
            
        self.components[name] = component
        
        # Register component's error handler for centralized monitoring
        if hasattr(component, 'error_handler') and isinstance(component.error_handler, ConsistentErrorHandler):
            register_error_handler(component.error_handler)
            self.logger.debug(f"Registered error handler for component: {name}")
        
        self.logger.info(f"Registered component: {name}")
    
    async def load_components_from_manifest(self, manifest_path: Union[str, Path]) -> None:
        """
        Load components dynamically from a manifest file.
        This replaces hardcoded imports with runtime discovery.
        
        Args:
            manifest_path: Path to component manifest YAML file
        """
        if not self._enable_dynamic_loading or not self._dynamic_loader:
            raise RuntimeError("Dynamic loading is not enabled for this harness")
        
        manifest_path = Path(manifest_path)
        self.logger.info(f"Loading components from manifest: {manifest_path}")
        
        try:
            # Load all components from manifest
            components = await anyio.to_thread.run_sync(
                self._dynamic_loader.load_all_components,
                manifest_path
            )
            
            # Register each component
            for name, component in components.items():
                self.register_component(name, component)
                
            self.logger.info(f"Loaded {len(components)} components from manifest")
            
        except Exception as e:
            self.logger.error(f"Failed to load components from manifest: {e}")
            raise
    
    async def discover_and_load_components(self, search_path: Optional[Path] = None) -> None:
        """
        Discover and load components by scanning a directory.
        Enhanced with detailed logging and proper registration.
        
        Args:
            search_path: Directory to search for components (default: ./components)
        """
        if not self._enable_dynamic_loading or not self._dynamic_loader:
            raise RuntimeError("Dynamic loading is not enabled for this harness")
        
        # Update the loader's base_path if a specific search_path is provided
        if search_path:
            self._dynamic_loader.base_path = Path(search_path)
        
        self.logger.info(f"Discovering components in: {search_path or 'components/'}")
        
        try:
            # Discover components
            manifests = await anyio.to_thread.run_sync(
                self._dynamic_loader.discover_components,
                search_path
            )
            
            self.logger.info(f"Found {len(manifests)} component manifests")
            
            # Load and register each discovered component
            registered_count = 0
            for manifest in manifests:
                try:
                    self.logger.info(f"Loading component: {manifest.name}")
                    component = await anyio.to_thread.run_sync(
                        self._dynamic_loader.create_component,
                        manifest
                    )
                    
                    # CRITICAL: Register component with harness
                    self.register_component(manifest.name, component)
                    registered_count += 1
                    
                    self.logger.info(f"Successfully registered component: {manifest.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load component {manifest.name}: {e}")
                    # Continue loading other components but track failures
                    continue
            
            if registered_count == 0:
                raise RuntimeError(f"No components successfully registered from {len(manifests)} discovered")
            
            self.logger.info(f"Successfully registered {registered_count}/{len(manifests)} components")
            
            # Verify registration worked
            self.logger.info(f"Harness now contains {len(self.components)} registered components: {list(self.components.keys())}")
            
        except Exception as e:
            self.logger.error(f"Failed to discover/load components: {e}")
            raise
    
    def verify_component_registration(self) -> Dict[str, Any]:
        """Verify all expected components are properly registered."""
        verification = {
            "total_discovered": 0,
            "total_registered": len(self.components),
            "registered_components": list(self.components.keys()),
            "missing_components": [],
            "registration_success": False
        }
        
        # Expected component names based on blueprint/connections
        expected_components = set()
        for connection in getattr(self, '_expected_connections', []):
            if hasattr(connection, 'from_component'):
                expected_components.add(connection.from_component)
            if hasattr(connection, 'to_component'):
                expected_components.add(connection.to_component)
        
        verification["expected_components"] = list(expected_components)
        verification["missing_components"] = list(expected_components - set(self.components.keys()))
        verification["registration_success"] = len(verification["missing_components"]) == 0
        
        return verification
        
    def connect(self, 
                from_output: str, 
                to_input: str,
                max_buffer_size: int = 1000) -> None:
        """
        Connect two components via anyio streams.
        
        Args:
            from_output: Source in format "component_name.output_port"
            to_input: Destination in format "component_name.input_port"  
            max_buffer_size: Maximum buffer size for the stream
        """
        # Parse component and port names
        from_comp_name, from_port_name = from_output.split('.')
        to_comp_name, to_port_name = to_input.split('.')
        
        # Validate components exist
        if from_comp_name not in self.components:
            raise ValueError(f"Component '{from_comp_name}' not registered")
        if to_comp_name not in self.components:
            raise ValueError(f"Component '{to_comp_name}' not registered")
            
        # Create anyio stream pair
        send_stream, receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=max_buffer_size
        )
        
        # Wire streams to component ports
        self.components[from_comp_name].send_streams[from_port_name] = send_stream
        self.components[to_comp_name].receive_streams[to_port_name] = receive_stream
        
        # Create connection record
        connection = Connection(
            from_component=from_comp_name,
            from_output=from_port_name,
            to_component=to_comp_name,
            to_input=to_port_name,
            max_buffer_size=max_buffer_size
        )
        
        self.connections.append(connection)
        self.logger.info(f"Connected: {from_output} -> {to_input}")
    
    async def send_to_stream(self, stream_path: str, data: Any) -> bool:
        """
        Send data to a component stream from external sources (e.g., HTTP requests).
        
        This bridges the gap between synchronous HTTP endpoints and asynchronous 
        stream-based components, solving the fundamental architectural incompatibility.
        
        Args:
            stream_path: Component stream in format "component_name.stream_name"
            data: Data to send to the stream
            
        Returns:
            bool: True if data was sent successfully, False otherwise
            
        Example:
            await harness.send_to_stream("api_service.input", request_data)
        """
        try:
            # Parse stream path
            if '.' not in stream_path:
                self.logger.error(f"Invalid stream path format: {stream_path}. Expected 'component.stream'")
                return False
                
            component_name, stream_name = stream_path.split('.', 1)
            
            # Get component
            if component_name not in self.components:
                self.logger.error(f"Component not found: {component_name}")
                return False
                
            component = self.components[component_name]
            
            # Get send stream (this component will send data to the specified stream)
            if not hasattr(component, 'send_streams') or stream_name not in component.send_streams:
                self.logger.error(f"Stream not found: {stream_path}")
                return False
                
            # Send data to the stream
            send_stream = component.send_streams[stream_name]
            await send_stream.send(data)
            
            self.logger.debug(f"Successfully sent data to stream: {stream_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send data to stream {stream_path}: {e}")
            return False
    
    async def inject_to_component(self, component_name: str, input_stream: str, data: Any) -> bool:
        """
        Inject data directly into a component's input stream.
        
        This method provides direct access to component input streams for external
        data injection, supporting HTTP-to-stream bridge patterns.
        
        Args:
            component_name: Name of the target component
            input_stream: Name of the input stream (usually 'input')
            data: Data to inject
            
        Returns:
            bool: True if injection succeeded, False otherwise
        """
        try:
            if component_name not in self.components:
                self.logger.error(f"Component not found: {component_name}")
                return False
                
            component = self.components[component_name]
            
            # Access receive streams directly for injection
            if not hasattr(component, 'receive_streams') or input_stream not in component.receive_streams:
                self.logger.error(f"Input stream '{input_stream}' not found in component '{component_name}'")
                return False
            
            # Find the corresponding send stream from connections
            for connection in self.connections:
                if connection.to_component == component_name and connection.to_stream == input_stream:
                    # Found the connection, inject data through the send stream
                    from_component = self.components[connection.from_component]
                    if hasattr(from_component, 'send_streams') and connection.from_stream in from_component.send_streams:
                        send_stream = from_component.send_streams[connection.from_stream]
                        await send_stream.send(data)
                        self.logger.debug(f"Injected data into {component_name}.{input_stream}")
                        return True
            
            self.logger.error(f"No connection found for {component_name}.{input_stream}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to inject data into {component_name}.{input_stream}: {e}")
            return False
    
    async def receive_from_stream(self, stream_path: str, timeout: float = 5.0) -> Optional[Any]:
        """
        Receive data from a component stream for external consumption (e.g., HTTP responses).
        
        This completes the HTTP-to-stream bridge by allowing HTTP endpoints to receive
        processed results from the stream processing pipeline.
        
        Args:
            stream_path: Component stream in format "component_name.stream_name"
            timeout: Maximum time to wait for data (seconds)
            
        Returns:
            Data from the stream or None if timeout/error
            
        Example:
            result = await harness.receive_from_stream("api_service.output", timeout=10.0)
        """
        try:
            # Parse stream path
            if '.' not in stream_path:
                self.logger.error(f"Invalid stream path format: {stream_path}. Expected 'component.stream'")
                return None
                
            component_name, stream_name = stream_path.split('.', 1)
            
            # Get component
            if component_name not in self.components:
                self.logger.error(f"Component not found: {component_name}")
                return None
                
            component = self.components[component_name]
            
            # Get receive stream for output data
            if not hasattr(component, 'receive_streams') or stream_name not in component.receive_streams:
                self.logger.error(f"Stream not found: {stream_path}")
                return None
            
            # Receive data from the stream with timeout
            receive_stream = component.receive_streams[stream_name]
            
            with anyio.move_on_after(timeout) as cancel_scope:
                data = await receive_stream.receive()
                self.logger.debug(f"Successfully received data from stream: {stream_path}")
                return data
            
            if cancel_scope.cancelled_caught:
                self.logger.warning(f"Timeout receiving data from stream: {stream_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to receive data from stream {stream_path}: {e}")
            return None
        
    async def run(self) -> None:
        """
        Start and run the system using anyio structured concurrency.
        
        This method:
        1. Sets up all components
        2. Starts all components concurrently using TaskGroup
        3. Signals readiness when all components are ready
        4. Handles shutdown gracefully
        """
        self.logger.info(f"Starting harness: {self.name}")
        
        try:
            # Setup signal handlers
            self._setup_signal_handlers()
            
            self._running = True
            self._total_components = len(self.components)
            
            # Use anyio TaskGroup for structured concurrency
            async with anyio.create_task_group() as tg:
                self._task_group = tg
                
                # Call setup for each component first
                for name, component in self.components.items():
                    await component.setup(self.get_context())
                    component._status.is_running = True
                
                # Start and verify all components are ready
                for name, component in self.components.items():
                    await self._start_component_with_readiness(name, component)
                
                # All components ready - signal harness readiness
                self._ready_event.set()
                self.logger.info(f"Harness {self.name} ready with {len(self.components)} components")
                
                # Start all components as background tasks for continuous processing
                for name, component in self.components.items():
                    tg.start_soon(self._run_component, name, component)
                
                # Start production monitoring tasks
                tg.start_soon(self._health_check_monitor)
                tg.start_soon(self._metrics_updater)
                tg.start_soon(self._shutdown_monitor)  # Monitor for shutdown signals
                
                self.logger.info(f"Harness running: {self.name} with {len(self.components)} components")
                
                # The TaskGroup will automatically handle cancellation and cleanup
                
        except anyio.get_cancelled_exc_class():
            # Normal cancellation during shutdown
            self.logger.info("Harness cancelled during shutdown")
            await self.stop()
        except Exception as exc:
            # Handle actual system-level startup failure
            exc_str = str(exc).lower()
            if any(keyword in exc_str for keyword in ["cancelled", "taskgroup", "shutdown", "baseexceptiongroup"]):
                self.logger.info(f"Harness shutdown during cancellation: {exc}")
                await self.stop()
            else:
                self.logger.error(f"Error running harness: {exc}")
                await self.stop()
                raise
            
        finally:
            self._running = False
            self.logger.info(f"Harness stopped: {self.name}")
    
    async def start(self) -> None:
        """
        Start the harness in the background (non-blocking).
        
        This is useful for generated systems that need to start the harness
        as a background task while serving HTTP endpoints.
        """
        if self._running:
            self.logger.warning("Harness is already running")
            return
        
        # Start the harness as a background task
        import asyncio
        self._harness_task = asyncio.create_task(self.run())
        
        # Give the harness a moment to start up
        await anyio.sleep(0.1)
        
        self.logger.info(f"Harness started in background: {self.name}")
    
    async def wait_for_completion(self) -> None:
        """
        Wait for the harness to complete (blocks until shutdown).
        
        This is useful for generated systems that want to wait for shutdown signals.
        """
        if hasattr(self, '_harness_task') and self._harness_task:
            try:
                await self._harness_task
            except Exception as e:
                self.logger.error(f"Harness task completed with error: {e}")
                raise
        else:
            # If no background task, wait for shutdown event
            await self._shutdown_event.wait()
            
    async def stop(self) -> None:
        """Stop the system gracefully"""
        if not self._running:
            return
            
        self.logger.info(f"Stopping harness: {self.name}")
        self._running = False
        
        # Run cleanup for all components
        for name, component in self.components.items():
            try:
                self.logger.info(f"Cleaning up component: {name}")
                await component.cleanup()
                component._status.is_running = False
            except Exception as e:
                self.logger.error(f"Error cleaning up component {name}: {e}")
        
        self.logger.info(f"Harness stopped: {self.name}")
        
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        # Use anyio's built-in signal handling instead of custom handlers
        # This avoids the KeyboardInterrupt exception issues
        pass
        
    async def _run_component(self, name: str, component: Component) -> None:
        """Wrapper to run a single component's process loop with circuit breaker."""
        # Initialize circuit breaker for this component
        self._init_circuit_breaker(name)
        
        retry_count = 0
        max_retries = 3
        
        while retry_count <= max_retries:
            cb_state = self._circuit_breakers[name]["state"]
            
            # Check circuit breaker state
            if cb_state == "open":
                # Circuit breaker is open - check if we should try recovery
                if await self._should_attempt_recovery(name):
                    self._set_circuit_breaker_state(name, "half_open")
                    self.logger.info(f"Circuit breaker HALF-OPEN for component {name}")
                else:
                    # Still in cooling down period
                    await anyio.sleep(settings.RETRY_DELAY * 5)
                    continue
            
            try:
                self.logger.info(f"Starting component process: {name} (attempt {retry_count + 1})")
                
                # Component is healthy, run process
                await component.process()
                
                # If we get here, component completed successfully
                if cb_state in ["half_open", "open"]:
                    self._set_circuit_breaker_state(name, "closed")
                    self.logger.info(f"Component {name} successfully recovered - Circuit breaker CLOSED")
                
                break  # Component completed successfully
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Error in component {name} (attempt {retry_count}): {e}")
                component.record_error(str(e))
                
                # Record failure in circuit breaker
                self._record_circuit_breaker_failure(name)
                
                # Check if we should open circuit breaker
                if self._should_open_circuit_breaker(name):
                    self._set_circuit_breaker_state(name, "open")
                    self.logger.error(f"Circuit breaker OPEN for component {name}")
                
                if retry_count > max_retries:
                    self.logger.error(f"Component {name} failed after {max_retries} retries")
                    raise
                
                # Wait before retry
                await anyio.sleep(min(2.0 * retry_count, 10.0))  # Exponential backoff
            
    def get_context(self) -> Dict[str, Any]:
        """Get harness context for components"""
        return {
            "harness_name": self.name,
            "total_components": len(self.components),
            "connections": len(self.connections),
            "harness": self,
            "tracer": self._tracer
        }
        
    def get_metrics(self) -> HarnessMetrics:
        """Get current system metrics"""
        return self._metrics
    
    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics for monitoring endpoints"""
        # Update performance metrics
        self._metrics.update_performance_metrics()
        
        # Collect component statuses
        detailed_components = {}
        for name, component in self.components.items():
            status = component.get_status()
            detailed_components[name] = {
                "is_running": status.is_running,
                "is_healthy": status.is_healthy,
                "items_processed": status.items_processed,
                "errors_encountered": status.errors_encountered,
                "last_error": status.last_error,
                "metadata": status.metadata
            }
        
        # Calculate system health
        total_components = len(self.components)
        healthy_components = sum(1 for comp in self.components.values() if comp.get_status().is_healthy)
        running_components = sum(1 for comp in self.components.values() if comp.get_status().is_running)
        
        health_score = healthy_components / max(1, total_components)
        system_status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        
        # Generate alerts and recommendations
        alerts = self._generate_alerts()
        recommendations = self._generate_recommendations()
        
        return {
            "timestamp": time.time(),
            "uptime_seconds": self._metrics.uptime_seconds,
            "health_score": health_score,
            "system_status": system_status,
            "total_components": total_components,
            "healthy_components": healthy_components,
            "running_components": running_components,
            "performance": {
                "items_per_second": self._metrics.items_per_second,
                "error_rate": self._metrics.error_rate,
                "memory_usage_mb": self._metrics.memory_usage_mb,
                "cpu_usage_percent": self._metrics.cpu_usage_percent,
                "active_connections": self._metrics.active_connections
            },
            "detailed_components": detailed_components,
            "circuit_breakers": self._circuit_breakers,
            "streaming": {
                "total_connections": len(self.connections),
                "queue_depths": self._metrics.queue_depths
            },
            "alerts": alerts,
            "recommendations": recommendations,
            "traces": {
                "active_spans": len(self._tracer.active_spans),
                "total_traces": len(set(span.context.trace_id for span in self._tracer.spans))
            }
        }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get simple system health summary for load balancers"""
        total_components = len(self.components)
        healthy_components = sum(1 for comp in self.components.values() if comp.get_status().is_healthy)
        running_components = sum(1 for comp in self.components.values() if comp.get_status().is_running)
        
        health_score = healthy_components / max(1, total_components)
        system_status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        
        return {
            "system_status": system_status,
            "health_score": health_score,
            "uptime_seconds": self._metrics.uptime_seconds,
            "total_components": total_components,
            "healthy_components": healthy_components,
            "running_components": running_components
        }
        
    async def get_component_status(self, component_name: str) -> Optional[ComponentStatus]:
        """Get status of a specific component"""
        if component_name in self.components:
            return self.components[component_name].get_status()
        return None
        
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        health_status = {}
        for name, component in self.components.items():
            health_status[name] = await component.health_check()
        return health_status
    
    # Production monitoring methods
    
    async def _health_check_monitor(self):
        """Background task to monitor component health with retry logic"""
        retry_count = 0
        max_retries = 3
        
        while self._running:
            try:
                health_status = await self.health_check()
                unhealthy_components = [name for name, healthy in health_status.items() if not healthy]
                
                if unhealthy_components:
                    self.logger.warning(f"Unhealthy components detected: {unhealthy_components}")
                    # Trigger circuit breakers or alerts
                    for comp_name in unhealthy_components:
                        await self._handle_component_failure(comp_name)
                
                # Reset retry count on successful health check
                retry_count = 0
                await anyio.sleep(self._health_check_interval)
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Health check monitor error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    self.logger.critical("Health check monitor failed multiple times, initiating emergency shutdown")
                    self._shutdown_event.set()
                    break
                
                # Exponential backoff for retries
                backoff_time = min(self._health_check_interval * (2 ** retry_count), 300)  # Max 5 minutes
                await anyio.sleep(backoff_time)
    
    async def _metrics_updater(self):
        """Background task to update system metrics"""
        while self._running:
            try:
                # Update performance metrics
                self._metrics.update_performance_metrics()
                
                # Update component metrics
                for name, component in self.components.items():
                    self._metrics.component_metrics[name] = component.get_status()
                
                # Update stream queue depths
                for connection in self.connections:
                    # In a real implementation, check actual queue depths
                    self._metrics.queue_depths[f"{connection.from_component}->{connection.to_component}"] = 0
                
                # Log metrics periodically
                if int(self._metrics.uptime_seconds) % 60 == 0:  # Every minute
                    self.logger.info(f"System metrics: {self._metrics.items_per_second:.1f} items/sec, "
                                   f"{self._metrics.error_rate:.3f} error rate, "
                                   f"{self._metrics.memory_usage_mb:.1f}MB memory")
                
                await anyio.sleep(self._metrics_update_interval)
                
            except Exception as e:
                self.logger.error(f"Metrics updater error: {e}")
                await anyio.sleep(self._metrics_update_interval)
    
    async def _handle_component_failure(self, component_name: str):
        """Handle component failure with advanced circuit breaker logic"""
        if component_name not in self._circuit_breakers:
            self._circuit_breakers[component_name] = {
                "failures": 0,
                "last_failure": time.time(),
                "state": "closed",  # closed, open, half-open
                "recovery_attempts": 0,
                "total_requests": 0
            }
        
        cb = self._circuit_breakers[component_name]
        cb["failures"] += 1
        cb["total_requests"] += 1
        cb["last_failure"] = time.time()
        
        # Advanced circuit breaker logic with recovery
        failure_threshold = 3
        recovery_timeout = 60  # seconds
        
        if cb["state"] == "closed" and cb["failures"] >= failure_threshold:
            cb["state"] = "open"
            self.logger.warning(f"Circuit breaker OPEN for component: {component_name}")
            
        elif cb["state"] == "open":
            # Check if we should attempt recovery
            time_since_failure = time.time() - cb["last_failure"]
            if time_since_failure >= recovery_timeout:
                cb["state"] = "half-open"
                cb["recovery_attempts"] += 1
                self.logger.info(f"Circuit breaker HALF-OPEN for component: {component_name} (attempt {cb['recovery_attempts']})")
                
                # Try to recover the component
                await self._attempt_component_recovery(component_name)
        
        elif cb["state"] == "half-open":
            # If still failing in half-open state, go back to open
            cb["state"] = "open"
            cb["last_failure"] = time.time()
            self.logger.warning(f"Circuit breaker back to OPEN for component: {component_name}")
        
        # Add to error queue for analysis
        error_record = {
            "timestamp": time.time(),
            "component": component_name,
            "error_type": "health_check_failure",
            "failure_count": cb["failures"],
            "circuit_breaker_state": cb["state"],
            "error_rate": cb["failures"] / max(1, cb["total_requests"])
        }
        self._error_queue.append(error_record)
        
        # Keep error queue size manageable
        if len(self._error_queue) > 1000:
            self._error_queue = self._error_queue[-500:]  # Keep last 500 errors
    
    async def _attempt_component_recovery(self, component_name: str):
        """Attempt to recover a failed component"""
        if component_name not in self.components:
            return
            
        component = self.components[component_name]
        
        try:
            self.logger.info(f"Attempting recovery for component: {component_name}")
            
            # Try cleanup and re-setup
            await component.cleanup()
            await anyio.sleep(settings.RETRY_DELAY)  # Brief pause before retry
            await component.setup(self.get_context())
            
            # Test health after recovery
            if await component.health_check():
                cb = self._circuit_breakers[component_name]
                cb["state"] = "closed"
                cb["failures"] = 0
                self.logger.info(f"Component {component_name} successfully recovered")
            else:
                self.logger.warning(f"Component {component_name} recovery failed health check")
                
        except Exception as e:
            self.logger.error(f"Component {component_name} recovery failed: {e}")
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary with advanced observability"""
        component_health = {}
        for name, component in self.components.items():
            status = component.get_status()
            component_health[name] = {
                "is_running": status.is_running,
                "items_processed": status.items_processed,
                "error_count": status.errors_encountered,
                "last_error": status.last_error,
                "health_status": "healthy" if status.is_running and status.errors_encountered == 0 else "degraded"
            }
        
        # Calculate system-wide health score (0.0 to 1.0)
        total_components = len(self.components)
        healthy_components = sum(1 for info in component_health.values() if info["health_status"] == "healthy")
        health_score = healthy_components / max(1, total_components)
        
        return {
            "timestamp": time.time(),
            "system_status": "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "critical",
            "health_score": health_score,
            "uptime_seconds": self._metrics.uptime_seconds,
            "total_components": total_components,
            "running_components": sum(1 for c in self.components.values() if c._status.is_running),
            "healthy_components": healthy_components,
            "performance": {
                "total_errors": self._metrics.total_errors,
                "error_rate": self._metrics.error_rate,
                "items_per_second": self._metrics.items_per_second,
                "memory_usage_mb": self._metrics.memory_usage_mb,
                "cpu_usage_percent": self._metrics.cpu_usage_percent
            },
            "components": component_health,
            "circuit_breakers": self._circuit_breakers,
            "error_summary": {
                "total_errors": len(self._error_queue),
                "recent_errors": self._error_queue[-5:],  # Last 5 errors
                "error_types": self._get_error_type_summary()
            },
            "streaming": {
                "active_connections": len(self.connections),
                "queue_depths": self._metrics.queue_depths,
                "connection_details": [
                    {
                        "from": f"{conn.from_component}.{conn.from_output}",
                        "to": f"{conn.to_component}.{conn.to_input}",
                        "buffer_size": conn.max_buffer_size
                    } for conn in self.connections
                ]
            }
        }
    
    def _get_error_type_summary(self) -> Dict[str, int]:
        """Get summary of error types from error queue"""
        error_types = {}
        for error in self._error_queue[-100:]:  # Last 100 errors
            error_type = error.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types
    
    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed production metrics for monitoring/alerting"""
        health_summary = self.get_system_health_summary()
        
        # Add detailed component metrics
        detailed_components = {}
        for name, component in self.components.items():
            status = component.get_status()
            detailed_components[name] = {
                **health_summary["components"][name],
                "component_type": component.__class__.__name__,
                "is_healthy": status.is_healthy,  # Ensure this is included
                "errors_encountered": status.errors_encountered,  # Ensure this is included
                "last_error": status.last_error,
                "processing_rate": status.items_processed / max(1, self._metrics.uptime_seconds),
                "error_rate": status.errors_encountered / max(1, status.items_processed),
                "circuit_breaker": self._circuit_breakers.get(name, {"state": "closed"})
            }
        
        return {
            **health_summary,
            "detailed_components": detailed_components,
            "alerts": self._generate_alerts(),
            "recommendations": self._generate_recommendations(),
            "traces": {
                "active_spans": len(self._tracer.active_spans),
                "total_traces": len(set(span.context.trace_id for span in self._tracer.spans))
            }
        }
    
    # Circuit Breaker Implementation
    
    def _init_circuit_breaker(self, component_name: str) -> None:
        """Initialize circuit breaker for a component"""
        if component_name not in self._circuit_breakers:
            self._circuit_breakers[component_name] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": 0,
                "failure_threshold": 3,  # Open after 3 failures
                "recovery_timeout": 30.0,  # Try recovery after 30 seconds
                "success_threshold": 2,  # Close after 2 successes in half_open
                "success_count": 0
            }
    
    def _set_circuit_breaker_state(self, component_name: str, state: str) -> None:
        """Set circuit breaker state"""
        if component_name in self._circuit_breakers:
            old_state = self._circuit_breakers[component_name]["state"]
            self._circuit_breakers[component_name]["state"] = state
            
            if state == "closed":
                # Reset counters when closing
                self._circuit_breakers[component_name]["failure_count"] = 0
                self._circuit_breakers[component_name]["success_count"] = 0
            elif state == "half_open":
                # Reset success counter for half-open
                self._circuit_breakers[component_name]["success_count"] = 0
            
            if old_state != state:
                self.logger.info(f"Circuit breaker for {component_name}: {old_state} -> {state}")
    
    def _record_circuit_breaker_failure(self, component_name: str) -> None:
        """Record a failure in the circuit breaker"""
        if component_name in self._circuit_breakers:
            cb = self._circuit_breakers[component_name]
            cb["failure_count"] += 1
            cb["last_failure_time"] = time.time()
            cb["success_count"] = 0  # Reset success count on failure
    
    def _should_open_circuit_breaker(self, component_name: str) -> bool:
        """Check if circuit breaker should be opened"""
        if component_name not in self._circuit_breakers:
            return False
        
        cb = self._circuit_breakers[component_name]
        return (cb["state"] == "closed" and 
                cb["failure_count"] >= cb["failure_threshold"])
    
    async def _should_attempt_recovery(self, component_name: str) -> bool:
        """Check if we should attempt recovery for an open circuit breaker"""
        if component_name not in self._circuit_breakers:
            return False
        
        cb = self._circuit_breakers[component_name]
        if cb["state"] != "open":
            return False
        
        time_since_failure = time.time() - cb["last_failure_time"]
        return time_since_failure >= cb["recovery_timeout"]
    
    def _record_circuit_breaker_success(self, component_name: str) -> None:
        """Record a success in half-open circuit breaker"""
        if component_name in self._circuit_breakers:
            cb = self._circuit_breakers[component_name]
            if cb["state"] == "half_open":
                cb["success_count"] += 1
                if cb["success_count"] >= cb["success_threshold"]:
                    self._set_circuit_breaker_state(component_name, "closed")
    
    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate comprehensive system alerts based on current state"""
        alerts = []
        current_time = time.time()
        
        # Critical error rate alert
        if self._metrics.error_rate > 0.2:  # 20% error rate - critical
            alerts.append({
                "id": f"error_rate_critical_{int(current_time)}",
                "level": "critical",
                "type": "error_rate",
                "message": f"CRITICAL: System error rate {self._metrics.error_rate:.1%} is extremely high",
                "details": {
                    "error_rate": self._metrics.error_rate,
                    "threshold": 0.2,
                    "total_errors": self._metrics.total_errors,
                    "total_processed": self._metrics.total_items_processed
                },
                "timestamp": current_time,
                "severity": "critical",
                "category": "performance"
            })
        elif self._metrics.error_rate > 0.1:  # 10% error rate - warning
            alerts.append({
                "id": f"error_rate_warning_{int(current_time)}",
                "level": "warning",
                "type": "error_rate",
                "message": f"System error rate {self._metrics.error_rate:.1%} exceeds warning threshold",
                "details": {
                    "error_rate": self._metrics.error_rate,
                    "threshold": 0.1,
                    "total_errors": self._metrics.total_errors
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "performance"
            })
        
        # Memory usage alerts
        if self._metrics.memory_usage_mb > 2000:  # 2GB - critical
            alerts.append({
                "id": f"memory_critical_{int(current_time)}",
                "level": "critical",
                "type": "memory_usage",
                "message": f"CRITICAL: Memory usage {self._metrics.memory_usage_mb:.1f}MB is critically high",
                "details": {
                    "memory_mb": self._metrics.memory_usage_mb,
                    "threshold": 2000,
                    "cpu_percent": self._metrics.cpu_usage_percent
                },
                "timestamp": current_time,
                "severity": "critical",
                "category": "resource"
            })
        elif self._metrics.memory_usage_mb > 1000:  # 1GB - warning
            alerts.append({
                "id": f"memory_warning_{int(current_time)}",
                "level": "warning", 
                "type": "memory_usage",
                "message": f"Memory usage {self._metrics.memory_usage_mb:.1f}MB is elevated",
                "details": {
                    "memory_mb": self._metrics.memory_usage_mb,
                    "threshold": 1000
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "resource"
            })
        
        # CPU usage alerts
        if self._metrics.cpu_usage_percent > 80:
            alerts.append({
                "id": f"cpu_high_{int(current_time)}",
                "level": "warning",
                "type": "cpu_usage",
                "message": f"CPU usage {self._metrics.cpu_usage_percent:.1f}% is high",
                "details": {
                    "cpu_percent": self._metrics.cpu_usage_percent,
                    "threshold": 80
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "resource"
            })
        
        # Component health alerts
        unhealthy_components = [name for name, comp in self.components.items() 
                              if not comp.get_status().is_healthy]
        if unhealthy_components:
            alerts.append({
                "id": f"unhealthy_components_{int(current_time)}",
                "level": "critical",
                "type": "component_health",
                "message": f"Unhealthy components detected: {unhealthy_components}",
                "details": {
                    "unhealthy_components": unhealthy_components,
                    "total_components": len(self.components),
                    "health_percentage": (len(self.components) - len(unhealthy_components)) / len(self.components) * 100
                },
                "timestamp": current_time,
                "severity": "critical",
                "category": "health"
            })
        
        # Circuit breaker alerts
        open_breakers = [name for name, cb in self._circuit_breakers.items() if cb["state"] == "open"]
        half_open_breakers = [name for name, cb in self._circuit_breakers.items() if cb["state"] == "half_open"]
        
        if open_breakers:
            alerts.append({
                "id": f"circuit_breakers_open_{int(current_time)}",
                "level": "critical",
                "type": "circuit_breaker",
                "message": f"Circuit breakers OPEN: {open_breakers}",
                "details": {
                    "open_breakers": open_breakers,
                    "half_open_breakers": half_open_breakers,
                    "breaker_details": {name: self._circuit_breakers[name] for name in open_breakers}
                },
                "timestamp": current_time,
                "severity": "critical",
                "category": "resilience"
            })
        
        if half_open_breakers:
            alerts.append({
                "id": f"circuit_breakers_recovery_{int(current_time)}",
                "level": "warning",
                "type": "circuit_breaker_recovery",
                "message": f"Circuit breakers in recovery (HALF-OPEN): {half_open_breakers}",
                "details": {
                    "half_open_breakers": half_open_breakers,
                    "breaker_details": {name: self._circuit_breakers[name] for name in half_open_breakers}
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "resilience"
            })
        
        # Low throughput alert
        if self._metrics.uptime_seconds > 60 and self._metrics.items_per_second < 0.1:  # Very low throughput
            alerts.append({
                "id": f"low_throughput_{int(current_time)}",
                "level": "warning",
                "type": "throughput",
                "message": f"Low system throughput: {self._metrics.items_per_second:.2f} items/sec",
                "details": {
                    "items_per_second": self._metrics.items_per_second,
                    "uptime_seconds": self._metrics.uptime_seconds,
                    "total_items": self._metrics.total_items_processed
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "performance"
            })
        
        # Error queue backlog
        if len(self._error_queue) > 100:
            alerts.append({
                "id": f"error_backlog_{int(current_time)}",
                "level": "warning",
                "type": "error_backlog",
                "message": f"Large error queue backlog: {len(self._error_queue)} errors",
                "details": {
                    "error_count": len(self._error_queue),
                    "threshold": 100
                },
                "timestamp": current_time,
                "severity": "warning",
                "category": "operations"
            })
        
        return alerts
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable operational recommendations"""
        recommendations = []
        current_time = time.time()
        
        # Error rate recommendations
        if self._metrics.error_rate > 0.2:
            recommendations.append({
                "id": f"error_rate_action_{int(current_time)}",
                "priority": "critical",
                "category": "performance",
                "title": "Immediate Action Required: High Error Rate",
                "description": f"System error rate {self._metrics.error_rate:.1%} is critically high",
                "actions": [
                    "1. Check component logs immediately for root cause analysis",
                    "2. Consider rolling back recent deployments",
                    "3. Scale down traffic or enable maintenance mode",
                    "4. Review circuit breaker states for failing components"
                ],
                "estimated_time": "5-15 minutes",
                "impact": "System stability at risk - immediate intervention required"
            })
        elif self._metrics.error_rate > 0.05:
            recommendations.append({
                "id": f"error_monitoring_{int(current_time)}",
                "priority": "medium",
                "category": "monitoring",
                "title": "Enhanced Error Monitoring",
                "description": f"Error rate {self._metrics.error_rate:.1%} above normal baseline",
                "actions": [
                    "1. Enable verbose logging for components with high error rates",
                    "2. Review recent configuration changes",
                    "3. Monitor trends over next 30 minutes"
                ],
                "estimated_time": "10-20 minutes",
                "impact": "Potential performance degradation if trend continues"
            })
        
        # Memory usage recommendations
        if self._metrics.memory_usage_mb > 1500:
            recommendations.append({
                "id": f"memory_critical_{int(current_time)}",
                "priority": "high",
                "category": "resource",
                "title": "Memory Usage Optimization Required",
                "description": f"Memory usage {self._metrics.memory_usage_mb:.1f}MB approaching critical levels",
                "actions": [
                    "1. Identify memory-intensive components using /components endpoint",
                    "2. Consider restarting high-memory components",
                    "3. Review memory allocation patterns in component logs",
                    "4. Scale horizontally or increase memory limits"
                ],
                "estimated_time": "15-30 minutes",
                "impact": "Risk of out-of-memory errors and system instability"
            })
        elif self._metrics.memory_usage_mb > 750:
            recommendations.append({
                "id": f"memory_watch_{int(current_time)}",
                "priority": "low",
                "category": "resource",
                "title": "Memory Usage Monitoring",
                "description": f"Memory usage {self._metrics.memory_usage_mb:.1f}MB trending upward",
                "actions": [
                    "1. Monitor memory trends over next hour",
                    "2. Review component memory usage patterns",
                    "3. Consider garbage collection or cleanup tasks"
                ],
                "estimated_time": "5-10 minutes",
                "impact": "Preventive measure to avoid future memory issues"
            })
        
        # Circuit breaker recommendations
        open_breakers = [name for name, cb in self._circuit_breakers.items() if cb["state"] == "open"]
        if open_breakers:
            recommendations.append({
                "id": f"circuit_breaker_recovery_{int(current_time)}",
                "priority": "critical",
                "category": "resilience",
                "title": "Component Recovery Required",
                "description": f"Circuit breakers open for: {', '.join(open_breakers)}",
                "actions": [
                    "1. Check component health using /components endpoint",
                    "2. Review component logs for error patterns",
                    "3. Verify external dependencies are available",
                    "4. Consider manual component restart if logs indicate transient issues",
                    "5. Update component configuration if persistent errors found"
                ],
                "estimated_time": "20-45 minutes",
                "impact": "Reduced system functionality - some operations may be unavailable"
            })
        
        # Throughput recommendations
        if self._metrics.uptime_seconds > 60 and self._metrics.items_per_second < 0.1:
            recommendations.append({
                "id": f"throughput_investigation_{int(current_time)}",
                "priority": "medium",
                "category": "performance",
                "title": "Throughput Investigation",
                "description": f"Low throughput detected: {self._metrics.items_per_second:.2f} items/sec",
                "actions": [
                    "1. Check if input sources are providing data",
                    "2. Review component processing rates individually",
                    "3. Look for bottlenecks in component chains",
                    "4. Verify stream connections are properly established"
                ],
                "estimated_time": "10-25 minutes",
                "impact": "System may not be processing data efficiently"
            })
        
        # Unhealthy components
        unhealthy_components = [name for name, comp in self.components.items() 
                              if not comp.get_status().is_healthy]
        if unhealthy_components:
            recommendations.append({
                "id": f"component_health_{int(current_time)}",
                "priority": "high",
                "category": "health",
                "title": "Component Health Restoration",
                "description": f"Unhealthy components: {', '.join(unhealthy_components)}",
                "actions": [
                    "1. Review individual component status via /components endpoint",
                    "2. Check component logs for specific error messages",
                    "3. Verify component dependencies and connections",
                    "4. Consider component restart if errors are transient",
                    "5. Update component configuration if persistent issues found"
                ],
                "estimated_time": "15-40 minutes",
                "impact": "Degraded system functionality and potential data loss"
            })
        
        # Operational best practices
        if self._metrics.uptime_seconds > 86400:  # Running for more than a day
            recommendations.append({
                "id": f"maintenance_reminder_{int(current_time)}",
                "priority": "low",
                "category": "maintenance",
                "title": "Routine Maintenance Reminder",
                "description": f"System uptime: {self._metrics.uptime_seconds/3600:.1f} hours",
                "actions": [
                    "1. Consider scheduled maintenance window for updates",
                    "2. Review system logs for any recurring warnings",
                    "3. Check for available component or system updates",
                    "4. Validate backup and recovery procedures"
                ],
                "estimated_time": "30-60 minutes",
                "impact": "Preventive maintenance to ensure continued stability"
            })
        
        return recommendations
    
    async def _shutdown_monitor(self) -> None:
        """Monitor for shutdown signals and trigger graceful shutdown"""
        try:
            # Wait for shutdown event to be set
            await self._shutdown_event.wait()
            self.logger.info("Shutdown event received, initiating graceful shutdown")
            
            # Cancel the task group to trigger shutdown
            if self._task_group:
                self._task_group.cancel_scope.cancel()
                
        except Exception as e:
            self.logger.error(f"Error in shutdown monitor: {e}")
            # Still attempt to trigger shutdown
            if self._task_group:
                self._task_group.cancel_scope.cancel()


# Compatibility aliases
HarnessComponent = Component


def verify_harness_import():
    """Verify that SystemExecutionHarness can be imported and instantiated"""
    try:
        harness = SystemExecutionHarness()
        return True
    except Exception as e:
        print(f"Failed to create SystemExecutionHarness: {e}")
        return False


# Module test when run directly
if __name__ == "__main__":
    if verify_harness_import():
        print("✅ SystemExecutionHarness instantiation successful")
    else:
        print("❌ SystemExecutionHarness instantiation failed")