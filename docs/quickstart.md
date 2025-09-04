# Autocoder4_CC Quick Start Guide

**Status: [ACTIVE]** - Current getting started guide for Autocoder4_CC v5.2

This guide will help you get started with Autocoder4_CC quickly using the current enterprise architecture. You can generate systems from natural language or YAML blueprints, run them locally with hot-reload, and deploy to production.

## Prerequisites

- Python 3.11+ (minimum 3.8+ supported)
- Docker (for containerized deployment)
- Git

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd autocoder4_cc
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Quick Start: Your First System

### Option 1: Natural Language Generation (Recommended)

The primary way to use Autocoder4_CC is through natural language system generation:

```bash
# Generate a complete system from description
python autocoder_cc/generate_deployed_system.py "Create a customer analytics dashboard with user authentication and data visualization"

# Alternative: Using the CLI module directly
python -m autocoder_cc.cli.main generate "Build a REST API for inventory management"
```

### Option 2: Blueprint-Based Generation

Create a YAML blueprint file for more precise control:

```yaml
# my-system.yaml
schema_version: "1.0.0"
system:
  name: "my-first-system"
  description: "A simple API with database storage"
  
  components:
    - name: "api_service"
      type: "FastAPICQRS"
      description: "REST API with CQRS pattern"
      config:
        port: 8000
        endpoints:
          - path: "/health"
            method: "GET"
            response: "OK"
    
    - name: "database"
      type: "Store"
      description: "Data persistence layer"
      config:
        type: "sqlite"
        path: "./data.db"
        
  bindings:
    - from_component: "api_service"
      to_components: ["database"]
      stream_name: "data_flow"
```

Generate the system:
```bash
# Generate from blueprint
python autocoder_cc/generate_deployed_system.py my-system.yaml

# Or use local orchestrator for immediate testing
python -m autocoder_cc.cli.local_orchestrator my-system.yaml
```

### Running Your Generated System

```bash
# Navigate to generated system
cd generated_systems/my-first-system

# Start the system
python main.py

# Or use the generated Docker Compose
docker-compose up
```

## CLI Commands Reference

### Core Commands

```bash
# Generate from natural language description
python autocoder_cc/generate_deployed_system.py "Create a microservices API with authentication"

# Generate from YAML blueprint
python autocoder_cc/generate_deployed_system.py <blueprint.yaml>

# Run system locally with hot reload (development)
python -m autocoder_cc.cli.local_orchestrator <blueprint.yaml> --watch --debug

# Validate a blueprint before generation
python -m autocoder_cc.blueprint_language.validation_framework <blueprint.yaml>

# Use CLI main module for advanced operations
python -m autocoder_cc.cli.main --help
```

### LocalOrchestrator Development Features

For development and testing, use the LocalOrchestrator with advanced capabilities:

```bash
# Basic local execution
python -m autocoder_cc.cli.local_orchestrator examples/customer_analytics_platform/config/system_config.yaml

# With hot-reload (automatically restarts when blueprint changes)
python -m autocoder_cc.cli.local_orchestrator examples/customer_analytics_platform/config/system_config.yaml --watch

# Debug mode with step-through execution
python -m autocoder_cc.cli.local_orchestrator examples/customer_analytics_platform/config/system_config.yaml --debug

# Full development mode with hot-reload and debugging
python -m autocoder_cc.cli.local_orchestrator examples/customer_analytics_platform/config/system_config.yaml --debug --watch

# Run with observability enabled
python -m autocoder_cc.cli.local_orchestrator <blueprint.yaml> --observability
```

### Advanced Generation Options

```bash
# Generate with specific configuration
python autocoder_cc/generate_deployed_system.py <blueprint.yaml>

# Generate with deployment artifacts (Docker, K8s, etc.)
python autocoder_cc/generate_deployed_system.py "Build a data pipeline"

# All systems include deployment artifacts by default
# Output directory is automatically created in generated_systems/
```

### System Migration and Versioning

Manage system schema versions and migrations:

```bash
# Schema management is handled through the validation framework
python -m autocoder_cc.core.schema_versioning --list

# Check schema validation
python -m autocoder_cc.blueprint_language.validation_framework --validate <blueprint.yaml>
```

## Working Examples

The following examples are fully functional and tested:

### Health Check API
```bash
# Generate a simple health check API
python autocoder_cc/generate_deployed_system.py examples/test_working_system/health_check_api/config/system_config.yaml

# Run locally for testing
python -m autocoder_cc.cli.local_orchestrator examples/test_working_system/health_check_api/config/system_config.yaml --watch
```

### Data Pipeline with Observability
```bash
# Generate a data pipeline with Jaeger tracing
python autocoder_cc/generate_deployed_system.py examples/test_working_system/data_pipeline_jaeger/config/system_config.yaml

# Run with observability enabled
python -m autocoder_cc.cli.local_orchestrator examples/test_working_system/data_pipeline_jaeger/config/system_config.yaml --observability
```

### Customer Analytics Platform
```bash
# Generate customer analytics system from natural language
python autocoder_cc/generate_deployed_system.py "Create a customer analytics platform with user authentication, data collection, and dashboard visualization"

# Run locally with hot-reload for development
python -m autocoder_cc.cli.local_orchestrator examples/customer_analytics_platform/config/system_config.yaml --watch
```

## System Architecture

Autocoder4_CC generates systems using the **ComposedComponent** architecture:

### Component Types
- **APIEndpoint**: REST API endpoints with FastAPI
- **FastAPICQRS**: CQRS-based API endpoints with command/query separation
- **Store**: Data persistence components (SQLite, PostgreSQL)
- **Transformer**: Data processing and business logic
- **MessageBus**: Inter-component communication
- **Controller**: System coordination
- **StreamProcessor**: Stream processing components

> **Note**: ADR-031 has been accepted, establishing a port-based component model. Components now define their behavior through explicit, named ports with semantic types and schema validation, replacing the rigid Source/Transformer/Sink trichotomy.

### Implementation Status

#### ✅ Fully Implemented
- **Basic API Generation**: FastAPI endpoints with automatic routing
- **Database Integration**: SQLite and PostgreSQL support
- **Local Orchestration**: `python -m autocoder_cc.cli.local_orchestrator` with hot-reload
- **Blueprint Validation**: YAML schema validation
- **Basic Observability**: Health checks and metrics

#### 🔗 Partially Integrated
- **CQRS Generators**: Available but not default
- **Message Bus**: Available but requires manual setup
- **Security Decorators**: Available but not automatically applied

#### 🚧 In Progress
- **Advanced Observability**: Jaeger integration
- **Schema Versioning**: Basic implementation complete
- **Self-Healing**: AST-based healing available

#### 📋 Planned
- **Advanced Security**: RBAC, JWT, HTTPS enforcement
- **Performance Optimization**: LLM caching, parallel generation
- **Enterprise Features**: Multi-tenant, advanced validation

### Capabilities System
Components are composed with capabilities:
- **RetryHandler**: Automatic retry logic
- **CircuitBreaker**: Failure isolation
- **RateLimiter**: Throughput control
- **SchemaValidator**: Data validation
- **InputSanitizer**: Security validation
- **MetricsCollector**: Performance monitoring


## Development Workflow

### 1. System Generation
```bash
# Generate from natural language
autocoder generate "your system description"

# Review generated components
ls generated_system/components/
cat generated_system/config/system_config.yaml
```

### 2. Local Development
```bash
# Run with hot-reload for development
autocoder run-local generated_system/config/system_config.yaml --watch

# Debug mode for troubleshooting
autocoder run-local generated_system/config/system_config.yaml --debug
```

### 3. Validation and Testing
```bash
# Run validation pipeline
./tools/validation/run_cycle_validation.sh

# Run specific tests
python -m pytest tests/unit/
```

### 4. Deployment
```bash
# Generate deployment artifacts
autocoder generate "your system" --deploy

# Deploy to Kubernetes
kubectl apply -f generated_system/k8s/
```

## Configuration

### Environment Variables
Key environment variables in `.env`:
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Observability
OTEL_ENDPOINT=http://localhost:4317
PROMETHEUS_PORT=9090

# Development
DEBUG_MODE=true
LOG_LEVEL=INFO
```

### System Configuration
Systems are configured via YAML blueprints:
```yaml
schema_version: "1.0.0"
system:
  name: "My System"
  description: "System description"
  
  components:
    - name: "api_endpoint"
      type: "FastAPICQRS"
      description: "REST API with CQRS"
      
    - name: "data_store"
      type: "Store"
      description: "Data persistence"
      
  bindings:
    - from_component: "api_endpoint"
      to_components: ["data_store"]
      stream_name: "data_flow"
```

## Enterprise Deployment

### Production Docker Deployment

**🎯 TARGET ARCHITECTURE**: Generated systems will include production Docker configurations:

```bash
# Navigate to generated system
cd generated_systems/my-first-system

# Production deployment with scaling (TARGET)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale components individually (TARGET)
docker-compose up -d --scale api_service=3 --scale database=1
```

**⚠️ IMPLEMENTATION GAP**: 
- Docker generators exist (`autocoder_cc/generators/scaffold/docker_compose_generator.py`) but deployment files are not populated in `deployments/` directory
- Generated systems currently have empty `deployments/` folders
- **ROADMAP TASK**: Connect deployment generators to system generation pipeline

### Kubernetes Deployment

**🎯 TARGET ARCHITECTURE**: Generated systems will include Kubernetes manifests in the `k8s/` directory:

```bash
# Deploy to Kubernetes cluster (TARGET)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Monitor deployment (TARGET)
kubectl get pods -n autocoder-system
kubectl logs -f deployment/api-service -n autocoder-system
```

**⚠️ IMPLEMENTATION GAP**:
- K8s generator exists (`autocoder_cc/generators/scaffold/k8s_generator.py`) with deployment manifest generation
- K8s manifests are not currently generated in system output
- **ROADMAP TASK**: Integrate K8s generator into system generation pipeline

### Performance Characteristics

**🎯 TARGET PERFORMANCE SPECIFICATIONS**:

**Component Resource Requirements** (Design Targets):
- **APIEndpoint**: 100m CPU, 128Mi RAM (baseline)
- **Store** (memory): 50m CPU, 64Mi RAM 
- **Store** (database): 100m CPU, 256Mi RAM
- **StreamProcessor**: 200m CPU, 256Mi RAM
- **Controller**: 50m CPU, 128Mi RAM

**Scaling Guidelines** (Architectural Intent):
- API components: Scale horizontally (stateless)
- Store components: Vertical scaling for database, horizontal for memory
- Processing components: Scale based on throughput requirements

**Concurrent Request Handling** (Performance Goals):
- FastAPI endpoints: 1000+ concurrent requests per instance
- Database stores: Limited by connection pool (default: 20 connections)
- Memory stores: CPU-bound, scales with available cores

**⚠️ IMPLEMENTATION GAP**:
- Performance specifications not validated with actual benchmarks
- Resource requirements need empirical testing
- **ROADMAP TASK**: Create performance benchmarking suite to validate these targets

## Troubleshooting

### Common Issues

1. **Blueprint Not Found or Invalid**
   ```bash
   # Ensure you're in the correct directory
   pwd
   ls *.yaml
   
   # Validate blueprint syntax before generation
   autocoder validate <blueprint.yaml>
   ```

2. **Generation Failures**
   ```bash
   # Run with debug mode for detailed output
   autocoder runlocal <blueprint.yaml> --debug
   
   # Check component registry
   python -c "from autocoder.components.component_registry import component_registry; print(component_registry.list_components())"
   
   # Validate blueprint structure
   python -c "from blueprint_language.system_blueprint_parser import SystemBlueprintParser; parser = SystemBlueprintParser(); parser.parse_file('your_blueprint.yaml')"
   ```

3. **LLM API Connection Issues**
   ```bash
   # Check API keys are set
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   
   # Test LLM connectivity
   python -c "from autocoder.generation.llm_schema_generator import test_llm_connection; test_llm_connection()"
   ```

4. **Components Not Starting**
   ```bash
   # Check system logs
   tail -f logs/autocoder.log
   
   # Verify dependencies are installed
   pip list | grep autocoder
   
   # Run with debug mode for component startup details
   autocoder runlocal <blueprint.yaml> --debug
   ```

5. **Observability Issues**
   ```bash
   # Check observability backends
   python tools/ci/otel_backend_demo.py --health
   
   # Start observability stack
   python tools/ci/otel_backend_demo.py --setup
   
   # Run with observability enabled
   autocoder runlocal <blueprint.yaml> --observability
   ```

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
autocoder run-local your_system.yaml --debug
```

## Next Steps

1. **Explore Examples**: Try the working examples in `examples/test_working_system/`
2. **Read Architecture**: Understand the system design in `docs/architecture/`
3. **Customize Systems**: Modify blueprints to match your specific requirements
4. **Development Deep Dive**: See [contributing.md](contributing.md) for contribution guidelines
5. **Advanced Features**: Read the [Architecture Documentation](architecture-overview.md) for detailed system design
6. **Roadmap**: See [Implementation Roadmap](roadmap-overview.md) for development status and future plans

## Getting Help

- **Quick Reference**: Use `autocoder --help` for command-line help
- **Documentation**: 
  - Main overview: [README](../README.md)
  - Architecture details: [docs/reference/architecture/](architecture/)
  - Working examples: [examples/test_working_system/](../examples/test_working_system/)
- **Development Status**: Review [development-guide.md](development-guide.md) for known issues and current development status
- **Issues & Support**: 
  - Report bugs and feature requests via GitHub Issues
  - Ask architecture questions in GitHub Discussions
  - Check existing issues for known problems and solutions

---

**Note**: This quickstart reflects the current implementation status. For the full roadmap and planned features, see the architecture documentation and roadmap files. 