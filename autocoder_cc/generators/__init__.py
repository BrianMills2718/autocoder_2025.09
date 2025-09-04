#!/usr/bin/env python3
"""
Component Generation System
==========================

The generators package provides the core code generation capabilities for transforming
blueprint specifications into fully functional system components with production-ready
features including security, observability, and deployment configurations.

## Core Generators

- **API Endpoint Generator**: RESTful APIs with CQRS, security, validation
- **Database Generator**: ORM integration, migrations, connection pooling
- **Message Bus Generator**: Event-driven components with routing and monitoring
- **Observability Generator**: Metrics, tracing, health checks, alerting

## Quick Start

```python
from autocoder_cc.generators import create_project_structure
from autocoder_cc.blueprint_language import BlueprintParser

# Parse and generate
parser = BlueprintParser()
blueprint = parser.parse("system.yaml")
generator = ComponentGenerator()
components = generator.generate(blueprint)

# Create project structure
create_project_structure(components, output_dir="./generated_system")
```

## Key Features

- **Multi-stage Pipeline**: Parse → Generate → Validate → Deploy
- **Template System**: Jinja2-based code generation
- **Security Scaffolding**: JWT, RBAC, rate limiting, validation
- **Observability**: Prometheus metrics, Jaeger tracing, health checks
- **Deployment Ready**: Docker, Kubernetes, Helm charts
- **Validation**: Semantic, integration, and performance testing
"""

from .scaffold import create_project_structure

__all__ = [
    'create_project_structure'
] 