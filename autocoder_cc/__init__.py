"""
Autocoder V5.2 - Validation-Driven System Generation
===================================================

A comprehensive system generation framework that transforms high-level specifications
into fully functional, production-ready distributed systems with built-in validation,
observability, and self-healing capabilities.

## Architecture Overview

Autocoder4_CC implements a **System-First Architecture** with the following core principles:

- **Validation-Driven**: Every generated component undergoes semantic and integration validation
- **Observability-First**: Built-in metrics, tracing, and health monitoring
- **Self-Healing**: Automatic error detection and recovery mechanisms
- **Security-By-Design**: Zero hardcoded secrets, environment-based configuration
- **Enterprise-Ready**: Production-grade error handling, logging, and deployment

## Core Components

### System Execution Harness
The central orchestration engine that manages component lifecycle, health monitoring,
and inter-component communication.

### Component Framework
Base classes and interfaces for building pluggable, testable system components
with standardized lifecycle management.

### Generation Pipeline
Multi-stage generation process with validation checkpoints:
1. **Blueprint Parsing**: YAML specification to internal representation
2. **Component Generation**: AST-based code generation with placeholders
3. **Self-Healing**: Automatic placeholder resolution and code completion
4. **Validation**: Semantic and integration testing
5. **Deployment**: Docker, Kubernetes, and infrastructure generation

## Quick Start

```python
from autocoder import SystemExecutionHarness, Component

# Create a system harness
harness = SystemExecutionHarness("my-system")

# Define components
api_component = Component(
    name="api-service",
    type="api_endpoint",
    config={"port": 8000, "routes": ["/health", "/api/v1"]}
)

# Add to harness
harness.add_component(api_component)

# Start the system
harness.start()
```

## Key Features

- **Multi-LLM Support**: OpenAI o3, Anthropic Claude, Google Gemini
- **Blueprint Language**: Declarative YAML specifications
- **AST-Based Analysis**: Robust code parsing and manipulation
- **CQRS Generators**: Command/Query separation for scalable APIs
- **Security Scaffolding**: JWT, RBAC, rate limiting, input validation
- **Observability Stack**: Prometheus, Jaeger, structured logging
- **Production Deployment**: Docker, Kubernetes, Helm charts

## Configuration

All configuration is environment-based with no hardcoded values:

```bash
# Required environment variables
export OPENAI_API_KEY="your-key"
export JWT_SECRET_KEY="your-secret"
export POSTGRES_URL="postgresql://user:pass@host:5432/db"

# Optional overrides
export ENVIRONMENT="production"
export DEBUG_MODE="false"
export ENABLE_METRICS="true"
```

## Validation Pipeline

Every generated system undergoes comprehensive validation:

1. **Semantic Validation**: AST analysis for code quality and security
2. **Integration Validation**: Component interaction testing
3. **Security Validation**: Vulnerability scanning and best practices
4. **Performance Validation**: Load testing and resource analysis

## Examples

See `examples/` directory for complete working systems:
- Customer Analytics Platform
- Fraud Detection System
- Health Check API
- Data Pipeline with Observability

## API Reference

- **Core Classes**: `SystemExecutionHarness`, `Component`, `ComponentStatus`
- **Generation**: `BlueprintParser`, `ComponentGenerator`, `SelfHealer`
- **Validation**: `SemanticValidator`, `IntegrationValidator`
- **Observability**: `HealthChecker`, `MetricsCollector`, `Tracer`

For detailed API documentation, see the individual module docstrings.
"""

__version__ = "5.2.1"

# Export primary v4.3 System-First Architecture classes
from .orchestration import (
    SystemExecutionHarness, 
    Component, 
    ComponentStatus, 
    Connection, 
    HarnessMetrics,
    ComponentLifecycleState,
    ComponentHealthStatus,
    HealthCheckResult,
    ComponentMetrics,
    StreamMetrics,
    HarnessComponent
)

__all__ = [
    'SystemExecutionHarness',
    'Component', 
    'ComponentStatus',
    'Connection',
    'HarnessMetrics',
    'ComponentLifecycleState',
    'ComponentHealthStatus',
    'HealthCheckResult',
    'ComponentMetrics',
    'StreamMetrics',
    'HarnessComponent'
]