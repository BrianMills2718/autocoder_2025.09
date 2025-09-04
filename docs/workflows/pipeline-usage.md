# Pipeline Usage Guide

This guide provides step-by-step instructions for using the complete autocoder4_cc pipeline to generate production-ready systems from natural language descriptions.

## Quick Start

### 1. Generate a System

```bash
# Generate a simple API system
python generate_deployed_system.py "Create a todo API with user authentication"

# Generate a data processing system
python generate_deployed_system.py "Create a data pipeline that processes CSV files and generates reports"

# Generate a microservice
python generate_deployed_system.py "Create a user management microservice with CRUD operations"
```

### 2. Run the Generated System

```bash
# Navigate to generated system
cd generated_systems/your_system_name

# Start with default FastAPI server
python main.py

# Start in standalone mode (harness only)
python main.py --standalone
```

### 3. Test the System

```bash
# Run integration test
python test_generated_system_integration.py "Create a todo API"

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Detailed Usage

### System Generation

The pipeline supports two modes of operation:

#### HTTP Server Mode (Default)
Generated systems run with FastAPI and SystemExecutionHarness in the background:

```bash
python main.py
```

This provides:
- REST API endpoints at `http://localhost:8000`
- Health checks at `/health` and `/ready`
- Metrics at `/metrics`
- Auto-generated API documentation at `/docs`

#### Standalone Mode
Run only the SystemExecutionHarness without HTTP server:

```bash
python main.py --standalone
```

This provides:
- Pure stream-based processing
- Component-to-component communication
- Background data processing
- No HTTP endpoints

### System Architecture

Generated systems follow this architecture:

```
my_system/
├── main.py                 # Entry point using SystemExecutionHarness
├── blueprint.yaml          # System blueprint (auto-saved)
├── system_metadata.json    # Generation metadata
├── requirements.txt        # Python dependencies
├── components/             # Generated components
│   ├── __init__.py
│   ├── api_gateway.py
│   ├── data_processor.py
│   └── data_store.py
├── config/                 # Configuration files
│   └── system_config.yaml
└── tests/                  # Generated tests (optional)
    └── test_components.py
```

### Key Features

#### 1. Simplified Harness Integration
- No more bypasses or `simple_main.py` files
- Direct `SystemExecutionHarness.create_simple_harness()` usage
- Automatic component discovery from `components/` directory
- Automatic blueprint loading from `blueprint.yaml`

#### 2. Production-Ready Health Monitoring
All generated systems include:

- **Health Check** (`/health`): Overall system health
- **Readiness Check** (`/ready`): Service readiness for orchestration
- **Metrics Endpoint** (`/metrics`): Performance and operational metrics

#### 3. Component Architecture
All components use the ComposedComponent pattern:

```python
from autocoder.components.composed_base import ComposedComponent

class MyComponent(ComposedComponent):
    async def process_item(self, item: Any) -> Any:
        # Component logic here
        return processed_item
```

#### 4. CQRS Support
API components automatically include Command Query Responsibility Segregation:

- **Commands** (`POST /api/v1/system/commands`): Write operations
- **Queries** (`GET /api/v1/system/queries`): Read operations
- **Message Bus Integration**: RabbitMQ for command processing

## Configuration

### Environment Variables

```bash
# Core settings
export LOG_LEVEL=INFO
export DEBUG_MODE=false
export PORT_RANGE_START=8000

# Security
export JWT_SECRET_KEY=your-secret-key
export ENABLE_AUTH=true

# Performance
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_PERIOD=60

# Dependencies
export RABBITMQ_URL=amqp://localhost:5672
export REDIS_URL=redis://localhost:6379
```

### Blueprint Configuration

Generated systems include a `blueprint.yaml` file that defines the system:

```yaml
schema_version: "1.0.0"
system:
  name: my_todo_api
  description: "Todo API with user authentication"
  version: "1.0.0"
  
  components:
    - name: api_gateway
      type: APIEndpoint
      configuration:
        port: 8000
        auth_required: true
        
    - name: todo_controller
      type: Controller
      configuration:
        storage_type: memory
        
    - name: todo_store
      type: Store
      configuration:
        storage_type: file
        storage_path: ./data

  bindings:
    - from_component: api_gateway
      from_port: default
      to_components: [todo_controller]
      to_ports: [default]
```

## Development Workflow

### 1. Generate System
```bash
python generate_deployed_system.py "Your system description"
```

### 2. Review Generated Code
Check the generated system structure and components:

```bash
cd generated_systems/your_system
ls -la
cat main.py
cat blueprint.yaml
```

### 3. Test Integration
```bash
python test_generated_system_integration.py "Your system description"
```

### 4. Customize (Optional)
Edit generated components in the `components/` directory:

```python
# components/my_component.py
class MyComponent(ComposedComponent):
    async def process_item(self, item: Any) -> Any:
        # Add your custom logic here
        return self.custom_processing(item)
    
    def custom_processing(self, item):
        # Your business logic
        pass
```

### 5. Deploy
Generated systems are self-contained and ready for deployment:

```bash
# Docker
docker build -t my-system .
docker run -p 8000:8000 my-system

# Direct deployment
pip install -r requirements.txt
python main.py
```

## API Usage

### Health Endpoints

```bash
# Check system health
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-07-16T12:00:00Z",
  "version": "1.0.0",
  "service": "todo_api",
  "components": {
    "command_handler": true,
    "query_handler": true,
    "api_ready": true
  },
  "uptime_seconds": 3600
}

# Check readiness
curl http://localhost:8000/ready

# Response:
{
  "status": "ready",
  "timestamp": "2025-07-16T12:00:00Z",
  "service": "todo_api",
  "dependencies": "ok"
}
```

### CQRS Endpoints

```bash
# Execute command (write operation)
curl -X POST http://localhost:8000/api/v1/todo/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "create_todo",
    "data": {
      "title": "Learn autocoder4_cc",
      "description": "Study the pipeline architecture"
    }
  }'

# Execute query (read operation)
curl "http://localhost:8000/api/v1/todo/queries?query_type=list_todos&limit=10"
```

## Troubleshooting

### Common Issues

#### 1. System Won't Start
```bash
# Check logs
python main.py 2>&1 | tee system.log

# Verify components
ls components/
python -c "from components import *"
```

#### 2. Health Checks Fail
```bash
# Check individual components
curl http://localhost:8000/health -v

# Check dependencies
curl http://localhost:8000/ready -v
```

#### 3. Components Not Loading
```bash
# Verify blueprint
cat blueprint.yaml

# Check component directory
ls -la components/
python -c "import sys; sys.path.append('.'); from components.my_component import MyComponent"
```

#### 4. Generation Fails
```bash
# Check generation logs
python generate_deployed_system.py "test system" --verbose

# Verify configuration
env | grep -E "(LOG_LEVEL|DEBUG_MODE|OPENAI_API_KEY)"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
python main.py
```

### Integration Test Debugging

```bash
# Run with verbose output
python test_generated_system_integration.py "test system" --verbose

# Check specific endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/ready
```

## Performance Tuning

### Optimal Settings

```bash
# Production settings
export LOG_LEVEL=WARNING
export DEBUG_MODE=false
export RATE_LIMIT_REQUESTS=1000
export RATE_LIMIT_PERIOD=60

# Resource limits
export MAX_WORKERS=4
export MAX_MEMORY_MB=512
export TIMEOUT_SECONDS=30
```

### Monitoring

Monitor system performance:

```bash
# Get metrics
curl http://localhost:8000/metrics

# Monitor logs
tail -f system.log

# System resources
htop
```

## Advanced Usage

### Custom Components

Create custom components that integrate with the harness:

```python
from autocoder.components.composed_base import ComposedComponent

class CustomAnalyzer(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.analysis_model = self.load_model()
    
    async def process_item(self, item: Any) -> Any:
        # Custom analysis logic
        result = await self.analyze(item)
        return result
    
    def load_model(self):
        # Load your ML model
        pass
    
    async def analyze(self, item):
        # Run analysis
        pass
```

### Multiple Systems

Run multiple generated systems:

```bash
# Generate different systems
python generate_deployed_system.py "Create a user API" --port 8001
python generate_deployed_system.py "Create a order API" --port 8002

# Start both systems
cd generated_systems/user_api && python main.py &
cd generated_systems/order_api && python main.py &
```

### Integration with External Services

Generated systems can integrate with external services:

```python
# In component configuration
{
    "external_apis": {
        "payment_service": "https://api.payment.com",
        "notification_service": "https://api.notify.com"
    },
    "database": {
        "type": "postgresql",
        "url": "postgresql://user:pass@localhost:5432/db"
    }
}
```

## Next Steps

1. **Explore Examples**: Check `examples/` directory for sample systems
2. **Read Architecture**: Review `docs/architecture.md` for deep dive
3. **Contribute**: See `CONTRIBUTING.md` for development guidelines
4. **Deploy**: Use `docs/deployment.md` for production deployment

## Support

- **Documentation**: `/docs/` directory
- **Examples**: `/examples/` directory  
- **Issues**: GitHub Issues
- **Integration Test**: `python test_generated_system_integration.py`