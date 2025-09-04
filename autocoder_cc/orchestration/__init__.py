"""
System Orchestration and Component Management
============================================

The orchestration package provides the core System-First Architecture implementation,
including the SystemExecutionHarness for managing distributed component lifecycles
and the Component framework for building pluggable, observable system components.

## Core Components

- **SystemExecutionHarness**: Central coordinator managing component lifecycle
- **Component**: Pluggable units with standardized interfaces  
- **Connection**: Inter-component communication channels
- **Health Monitoring**: Built-in health checks and metrics collection

## Quick Start

```python
from autocoder_cc.orchestration import SystemExecutionHarness, Component

# Create system harness
harness = SystemExecutionHarness("customer-analytics")

# Define and add components
api_component = Component(
    name="api-service",
    type="api_endpoint", 
    config={"port": 8000, "routes": ["/health", "/api/v1"]}
)
harness.add_component(api_component)

# Start and monitor
harness.start()
health = harness.get_system_health()
print(f"System health: {health.status}")
```

## Key Features

- **Lifecycle Management**: Automatic startup/shutdown sequences
- **Health Monitoring**: Real-time component health tracking
- **Error Recovery**: Circuit breakers and graceful degradation
- **Observability**: Built-in metrics, tracing, and logging
- **Testing Support**: Standardized test interfaces
- **Production Ready**: Zero-downtime updates, resource limits
"""

from .component import Component, ComponentStatus
from .harness import (
    SystemExecutionHarness, 
    Connection, 
    HarnessMetrics,
    ComponentLifecycleState,
    ComponentHealthStatus,
    HealthCheckResult,
    ComponentMetrics,
    StreamMetrics,
    HarnessComponent
)
from .pipeline_coordinator import PipelineCoordinator, GeneratedSystem
from .dependency_injection import DependencyContainer, SystemDependencyConfiguration

__all__ = [
    'Component',
    'ComponentStatus', 
    'SystemExecutionHarness',
    'Connection',
    'HarnessMetrics',
    'ComponentLifecycleState',
    'ComponentHealthStatus',
    'HealthCheckResult',
    'ComponentMetrics',
    'StreamMetrics',
    'HarnessComponent',
    'PipelineCoordinator',
    'GeneratedSystem',
    'DependencyContainer',
    'SystemDependencyConfiguration'
]