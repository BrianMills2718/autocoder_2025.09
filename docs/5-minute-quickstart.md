# 5-Minute AutoCoder Quickstart

**Goal**: Generate your first working system in under 5 minutes.

## Prerequisites

- Python 3.11+
- At least one LLM API key (OpenAI, Anthropic, or Gemini)

## Step 1: Setup (1 minute)

```bash
# Clone and install
git clone https://github.com/your-org/autocoder4_cc
cd autocoder4_cc
pip install -e .

# Set API key (choose one)
export OPENAI_API_KEY="your-openai-key"        # Recommended
export ANTHROPIC_API_KEY="your-anthropic-key"  # Alternative
export GEMINI_API_KEY="your-gemini-key"        # Alternative
```

## Step 2: Generate Your First System (3 minutes)

```bash
# Generate a complete system from natural language
python autocoder_cc/generate_deployed_system.py "Create a simple task tracker API"
```

**What happens**:
- 🧠 **Phase 1**: Converts your description to system blueprint (30 seconds)
- ⚙️ **Phase 2**: Generates all components and code (2 minutes)  
- 🐳 **Phase 3**: Creates Docker containers and deployment files (30 seconds)
- 🚀 **Phase 4**: Deploys complete working system

## Step 3: Test Your System (1 minute)

```bash
# Navigate to generated system
cd generated_systems/system_$(date +%Y%m%d_*)

# Start the system
docker-compose up -d

# Test the API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/tasks -d '{"title":"My first task","description":"Testing AutoCoder"}'
curl http://localhost:8000/tasks
```

## ✅ Success!

You now have:
- ✅ **Working REST API** with database persistence
- ✅ **Complete system** with monitoring and observability
- ✅ **Production-ready** Docker deployment
- ✅ **Scalable architecture** with message queues and caching

## What You Get

Every generated system includes:

### **API Features**
- RESTful endpoints with proper HTTP methods
- Request/response validation  
- Error handling and logging
- Authentication ready (configurable)

### **Infrastructure**
- PostgreSQL database with migrations
- RabbitMQ message queue
- Redis caching layer
- Prometheus monitoring
- Docker containerization

### **Code Quality**
- Type hints and validation
- Comprehensive error handling
- Structured logging
- Unit and integration tests
- Production configuration

## Next Steps

### **Customize Your System**
```bash
# Generate different system types
python autocoder_cc/generate_deployed_system.py "Build an e-commerce API with products and orders"
python autocoder_cc/generate_deployed_system.py "Create a social media API with posts and comments"
python autocoder_cc/generate_deployed_system.py "Build a file processing system with webhooks"
```

### **Production Deployment**
```bash
# Deploy to Kubernetes (if available)
kubectl apply -f k8s/

# Or run in production mode
ENVIRONMENT=production docker-compose up -d
```

### **Monitor System Health**
```bash
# Check system status
python -c "
from autocoder_cc.llm_providers.multi_provider_manager import MultiProviderManager
manager = MultiProviderManager({'environment': 'development'})
print(manager.get_system_health_status())
"
```

## Troubleshooting

### **API Key Issues**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test provider connection
python -c "
from autocoder_cc.llm_providers.openai_provider import OpenAIProvider
provider = OpenAIProvider({'api_key': '$OPENAI_API_KEY'})
print('API key working' if provider.health_check() else 'API key invalid')
"
```

### **Generation Fails**
```bash
# Check logs
tail -f generated_systems/*/generation_verbose.log

# Try simpler description
python autocoder_cc/generate_deployed_system.py "Create a simple API"
```

### **System Won't Start**
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs

# Reset and retry
docker-compose down && docker-compose up -d
```

## Cost Information

**Typical generation costs**:
- Simple API: $0.001 - $0.003 (1-3 cents)
- Complex system: $0.01 - $0.05 (1-5 cents)  
- Enterprise system: $0.10 - $0.50 (10-50 cents)

**Cost controls are built-in**:
- Daily limits: $10 (configurable)
- Per-request limits: $0.01 (configurable)
- Real-time monitoring and alerts

## Common Examples

### **E-commerce System**
```bash
python autocoder_cc/generate_deployed_system.py "Build an e-commerce platform with products, shopping cart, orders, and payment processing"
```

### **Content Management**
```bash
python autocoder_cc/generate_deployed_system.py "Create a blog platform with posts, comments, user authentication, and admin dashboard"
```

### **IoT Data Pipeline**
```bash
python autocoder_cc/generate_deployed_system.py "Build an IoT data collection system with sensor readings, real-time processing, and alerting"
```

### **Analytics Dashboard**
```bash
python autocoder_cc/generate_deployed_system.py "Create an analytics system with data ingestion, processing, and dashboard visualization"
```

## Learn More

- **📋 [Full Documentation](README.md)** - Complete guide and reference
- **🏗️ [Architecture Overview](docs/architecture-overview.md)** - System design and principles  
- **📊 [Project Status](docs/roadmap-overview.md)** - Current progress and roadmap
- **🤝 [Contributing](docs/contributing.md)** - How to contribute to the project

## Need Help?

- **GitHub Issues**: [Report problems or ask questions](https://github.com/your-org/autocoder4_cc/issues)
- **Discussions**: [Community discussions and examples](https://github.com/your-org/autocoder4_cc/discussions)
- **Documentation**: [Complete documentation hub](docs/README.md)

---

**That's it!** You've generated a complete, production-ready system in 5 minutes. AutoCoder transforms natural language descriptions into working software with enterprise-grade quality and observability built-in.