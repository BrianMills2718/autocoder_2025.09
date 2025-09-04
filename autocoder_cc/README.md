# Autocoder4_CC

**Status: [ACTIVE DEVELOPMENT]** - Core system operational, undergoing documentation and validation improvements

A comprehensive code generation and system orchestration framework with advanced validation, security, and observability capabilities.

> **Architecture Update**: ADR-031 has been accepted, establishing a **port-based component model** that replaces the rigid Source/Transformer/Sink trichotomy. Components now define their behavior through explicit, named ports with semantic types and schema validation.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run basic validation
python -m autocoder.validation.validation_framework

# Generate a system from blueprint
python -m autocoder.blueprint_language.system_generator --blueprint autocoder_cc/blueprint_language/examples/simple-api.yaml
```

## Core Features

- **Blueprint Language**: Declarative system specification with validation
- **Port-Based Components**: Explicit, named ports with semantic types and schema validation (ADR-031)
- **Component Generation**: Automated code generation for APIs, databases, message buses
- **Security Framework**: RBAC, input sanitization, secure execution
- **Observability**: Metrics, tracing, health checks, structured logging
- **Validation Pipeline**: Multi-level validation with CI integration
- **Production Ready**: Docker, Kubernetes, secrets management

## Documentation Status

### Automation Features

| Feature | Status | Implementation |
|---------|--------|----------------|
| Documentation Health Dashboard | [PLANNED] | Not yet implemented |
| Automated Status Tag Updates | [PLANNED] | Manual updates currently |
| Cross-Reference Validation | [PLANNED] | No automated checking |
| Link Integrity Checks | [PLANNED] | Manual verification |
| Documentation Coverage Metrics | [PLANNED] | No metrics collection |

### Current Documentation

- **[ACTIVE]** `README.md` - Main project overview and quick start
- **[ACTIVE]** `docs/architecture/` - System architecture documentation  
- **[ACTIVE]** `docs/quickstart.md` - Getting started guide
- **[ACTIVE]** `CLAUDE.md` - Development tasks and issues tracking
- **[DEPRECATED]** `DEVELOPMENT.md` - Replaced by CLAUDE.md and docs/
- **[DEPRECATED]** Various scattered README files - Consolidated to main README

## Architecture

The system follows a **port-based component architecture** (ADR-031) with:

- **Core Engine**: `autocoder/` - Main generation and orchestration logic
- **Blueprint Language**: `blueprint_language/` - System specification and validation
- **Components**: `autocoder/components/` - Reusable system components with explicit ports
- **Security**: `autocoder/security/` - RBAC, sanitization, secure execution
- **Observability**: `autocoder/observability/` - Metrics, tracing, health checks
- **Validation**: `autocoder/validation/` - Multi-level validation framework
- **Tools**: `tools/` - Development and validation utilities

### Component Model

Components use explicit port descriptors with semantic classes:
- `data_in` / `data_out` - Primary data flow
- `control_in` / `control_out` - Control plane signals  
- `metrics_out` / `metrics_in` - Observability data
- `error_out` / `error_in` - Error handling

Each port has a specific schema, and the ComponentRegistry enforces strict schema compatibility between connected ports.

## Development

See `CLAUDE.md` for current development tasks and issues.

For detailed development setup and contribution guidelines, see `docs/development.md`.

## License

[License information to be added]