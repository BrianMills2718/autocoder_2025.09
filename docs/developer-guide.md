# AutoCoder4_CC Developer Guide

**Purpose**: Complete guide for human developers contributing to the project. For AI agents, see [CLAUDE.md](../CLAUDE.md).

**Last Updated**: 2025-07-19

---

## 🚀 Quick Start for Developers

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- At least one LLM API key (OpenAI recommended)

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/your-org/autocoder4_cc
cd autocoder4_cc
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Verify setup
python -c "from autocoder_cc import SystemExecutionHarness; print('✅ Setup successful')"
```

## 🔧 Using the System Generator

### Programmatic System Generation

The `SystemGenerator` class provides methods for generating systems from blueprints:

```python
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
import asyncio

async def generate_example():
    generator = SystemGenerator()
    
    # Method 1: Generate from YAML string
    yaml_content = """
    schema_version: "1.0.0"
    system:
      name: "my_system"
      components:
        - name: "api"
          type: "APIEndpoint"
          config:
            port: 8080
      bindings: []
    """
    result = await generator.generate_system_from_yaml(yaml_content)
    
    # Method 2: Generate from file path
    from pathlib import Path
    blueprint_path = Path("my_blueprint.yaml")
    result = await generator.generate_system(blueprint_path)
    
    return result

# Run the async function
result = asyncio.run(generate_example())
```

**Important**: The correct method is `generate_system_from_yaml()` for YAML strings, not `generate_from_file()`.

## 📋 Contributing Guidelines

### Before You Start

1. **Check Current Status**: Review [roadmap-overview.md](roadmap-overview.md) for active development priorities
2. **Understand Architecture**: Read [architecture-overview.md](architecture-overview.md) for system design
3. **Review Guild Structure**: Current development is organized in parallel guilds:
   - 🏗️ **Infrastructure Guild**: Platform and deployment
   - 🔐 **Security Guild**: Advanced security features
   - 📊 **Observability Guild**: Monitoring and analytics  
   - 🧠 **AI/LLM Guild**: Generation capabilities

### Development Workflow

#### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/issue-description
```

#### 2. Follow Coding Standards

**Python Code Quality**:
```python
# Use type hints for all functions
def process_component(data: Dict[str, Any]) -> ComponentResult:
    """Process component with validation."""
    
# Follow PEP 8 and add docstrings
class ComponentProcessor:
    """Processes components with validation and error handling."""
    
    async def process(self, component: Component) -> ProcessResult:
        """
        Process a component asynchronously.
        
        Args:
            component: Component to process
            
        Returns:
            ProcessResult with success status and details
            
        Raises:
            ValidationError: If component validation fails
        """
```

**File Organization**:
- New modules go in appropriate subdirectories
- Follow existing import patterns
- Add `__init__.py` files for new packages
- Update `CLAUDE.md` files for AI agent guidance

#### 3. Testing Requirements

**Test Coverage Standards**:
- Unit tests: >90% line coverage for new code
- Integration tests for component interactions
- End-to-end tests for user workflows

**Test Structure**:
```bash
tests/
├── unit/           # Individual function/class tests
├── integration/    # Multi-component tests  
├── e2e/           # Complete workflow tests
├── performance/   # Load and benchmark tests
└── fixtures/      # Reusable test data
```

**Running Tests**:
```bash
# All tests
pytest tests/

# Specific test categories
pytest tests/unit/                  # Fast unit tests
pytest tests/integration/           # Integration tests
pytest tests/e2e/                  # End-to-end tests

# With coverage
pytest tests/ --cov=autocoder_cc --cov-report=html
```

#### 4. Documentation Updates

**Documentation Types**:
- **Code Documentation**: Docstrings and type hints
- **User Documentation**: Guides and tutorials
- **Architecture Documentation**: System design and decisions
- **API Documentation**: Generated from code annotations

**Status Tags**: Use appropriate status indicators:
- ✅ **IMPLEMENTED** - Code exists and is functional
- 🔗 **INTEGRATED** - Code exists and is wired into main pipeline
- 🚧 **IN_PROGRESS** - Partially implemented
- 📋 **PLANNED** - Design complete, not started
- ❌ **DEPRECATED** - No longer planned

### Code Review Process

#### 1. Self-Review Checklist
```bash
# Before submitting PR
pytest tests/                      # All tests pass
black autocoder_cc/                # Code formatting
mypy autocoder_cc/                 # Type checking
flake8 autocoder_cc/               # Linting

# Check imports work
python -c "import autocoder_cc; print('✅ Imports working')"
```

#### 2. Pull Request Guidelines

**PR Title Format**:
- `feat: add component generation optimization`
- `fix: resolve async bug in LLM provider`
- `docs: update architecture decision records`
- `test: add integration tests for multi-provider`

**PR Description Template**:
```markdown
## Summary
Brief description of changes and motivation.

## Changes Made
- [ ] Code changes
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Breaking changes (if any)

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

#### 3. Review and Merge
- **Approval Required**: All PRs require review and approval
- **CI Must Pass**: All automated checks must pass
- **No Direct Main**: Never push directly to main branch

## 🏗️ Development Environments

### Local Development

**Environment Configuration**:
```python
# Development settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
KAFKA_BROKERS=localhost:9092

# API Keys (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key  
GEMINI_API_KEY=your-gemini-key
```

**Cost Controls** (Development):
```python
# Automatic cost limits for development
MAX_COST_PER_REQUEST=0.01     # $0.01 per generation
MAX_DAILY_COST=5.00           # $5 per day
MAX_MONTHLY_COST=50.00        # $50 per month
```

### Testing Environment

**Staging Setup**:
```bash
ENVIRONMENT=staging
# Higher limits for testing
MAX_DAILY_COST=25.00
MAX_MONTHLY_COST=200.00
```

### Production Environment

**Production Configuration**:
```bash
ENVIRONMENT=production
# Production limits
MAX_DAILY_COST=100.00
MAX_MONTHLY_COST=1000.00

# Required: Real secrets management
# - Use HashiCorp Vault or AWS Secrets Manager
# - No hardcoded API keys
# - Proper key rotation
```

## 🧪 Testing Strategy

### Unit Testing

**Test Individual Components**:
```python
# Example: test_component_validator.py
import pytest
from autocoder_cc.validation import ComponentValidator

def test_component_validation_success():
    validator = ComponentValidator()
    result = validator.validate_component(valid_component_code, "TestComponent")
    assert result["success"] is True
    assert result["quality_percentage"] >= 80

def test_component_validation_failure():
    validator = ComponentValidator() 
    result = validator.validate_component(invalid_component_code, "TestComponent")
    assert result["success"] is False
    assert "missing_patterns" in result
```

### Integration Testing

**Test Component Interactions**:
```python
# Example: test_generation_pipeline.py
async def test_complete_generation_pipeline():
    # Test natural language -> blueprint -> components -> deployment
    description = "Create a simple task tracker"
    
    # Phase 1: Natural language to blueprint
    blueprint = await generator.natural_language_to_blueprint(description)
    assert blueprint is not None
    
    # Phase 2: Blueprint to components  
    components = await generator.blueprint_to_components(blueprint)
    assert len(components) > 0
    
    # Phase 3: Components to deployment
    deployment = await generator.components_to_deployment(components)
    assert deployment["success"] is True
```

### End-to-End Testing

**Test Complete User Workflows**:
```python
# Example: test_system_generation.py
def test_complete_system_generation():
    # Test the entire generate_deployed_system.py workflow
    result = subprocess.run([
        "python", "autocoder_cc/generate_deployed_system.py",
        "Create a simple API"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Phase 1 Complete" in result.stdout
    assert "System generation successful" in result.stdout
```

## 🔧 Architecture and Design

### System Architecture

**Key Components**:
```
autocoder_cc/
├── llm_providers/          # Multi-provider LLM system
├── blueprint_language/     # System specification and generation
├── components/            # Base component implementations  
├── observability/         # Monitoring and cost controls
├── security/             # Security framework
└── validation/           # Quality assurance
```

**Design Principles**:
1. **Multi-Provider**: Never depend on single LLM provider
2. **Cost-Conscious**: Built-in cost monitoring and circuit breakers
3. **Production-Ready**: Enterprise-grade observability and security
4. **Template Injection**: LLM focuses on business logic, templates handle architecture

### Template Injection Architecture

**Why Template Injection**:
- **Token Efficiency**: 60% reduction in boilerplate token usage
- **Consistency**: 100% architectural compliance (vs. 50% with pure LLM)
- **Maintainability**: Single point of control for architectural patterns

**How It Works**:
1. LLM generates business logic only
2. Template injection adds architectural boilerplate
3. Unified validation ensures complete components work correctly

**Implementation**:
```python
# LLM generates this
async def process_item(self, item: Any) -> Any:
    # Business logic here
    return processed_result

# Template injection adds this
class ComponentName(StandaloneComponentBase):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # Standard initialization
    
    # LLM business logic injected here
```

## 📊 Monitoring and Observability

### Cost Monitoring

**Built-in Cost Controls**:
```python
# Cost circuit breakers automatically prevent overruns
from autocoder_cc.observability.cost_controls import create_cost_circuit_breaker

breaker = create_cost_circuit_breaker("development")
allowed, reason = breaker.check_request_allowed(estimated_cost, "openai")
```

### Performance Monitoring

**Production Monitoring**:
```python
# Real-time system health monitoring
from autocoder_cc.observability.monitoring_alerts import create_production_monitor

monitor = create_production_monitor()
monitor.check_provider_health(provider_stats)
monitor.check_cost_thresholds(cost_usage)
```

### Alerting

**Alert Configuration**:
```python
# Configurable alert thresholds
monitor_config = {
    'max_response_time': 30.0,      # 30 seconds
    'min_success_rate': 0.95,       # 95% success rate
    'max_error_rate': 0.05,         # 5% error rate
    'alert_channels': ['log', 'console', 'webhook']
}
```

## 🚀 Guild Development

### Current Guild Structure

**🏗️ Infrastructure Guild**:
- **Focus**: Kubernetes operators, deployment automation
- **Status**: Ready to start (P0.6 foundation complete)
- **Contact**: Infrastructure team lead

**🔐 Security Guild**:  
- **Focus**: RBAC, compliance, secrets management
- **Status**: Ready to start (crypto policies complete)
- **Contact**: Security team lead

**📊 Observability Guild**:
- **Focus**: Real-world integrations, cost optimization
- **Status**: Ready to start (cost tracking complete) 
- **Contact**: Observability team lead

**🧠 AI/LLM Guild**:
- **Focus**: Advanced generation, multi-provider optimization
- **Status**: Ready for advanced features (P0.6 foundation complete)
- **Contact**: AI/LLM team lead

### Guild Coordination

**Weekly Sync**: Tuesdays 3:00 PM UTC  
**Monthly Review**: First Friday of each month  
**Cross-Guild Dependencies**: Tracked in shared project board  

## 📚 Additional Resources

### Documentation Structure
```
docs/
├── README.md                    # Documentation hub
├── 5-minute-quickstart.md      # New user quick start
├── developer-guide.md          # This file (developers)  
├── architecture-overview.md     # System architecture
├── roadmap-overview.md         # Current status (single source of truth)
├── architecture/               # Detailed architecture docs
├── implementation_roadmap/     # Development planning
└── workflows/                  # Process guides
```

### Key Files for Developers
- **[CLAUDE.md](../CLAUDE.md)** - AI agent development guide
- **[Architecture Overview](architecture-overview.md)** - System design
- **[Roadmap](roadmap-overview.md)** - Current development status
- **[Test Guide](../tests/CLAUDE.md)** - Testing framework details

### External Resources
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Community Q&A and examples
- **CI/CD Pipeline**: Automated testing and deployment
- **Performance Benchmarks**: System performance tracking

## 🤝 Getting Help

### Development Questions
1. **Check Documentation**: Start with this guide and architecture docs
2. **Search Issues**: Look for existing GitHub issues and discussions
3. **Ask the Community**: Use GitHub Discussions for questions
4. **Contact Guild Leads**: For guild-specific development questions

### Bug Reports
1. **Check Known Issues**: Review open GitHub issues first
2. **Reproduce Issue**: Include minimal reproduction steps
3. **Include Environment**: Python version, OS, API keys used
4. **Attach Logs**: Include relevant error messages and stack traces

### Feature Requests
1. **Check Roadmap**: Review current development priorities
2. **Describe Use Case**: Explain the problem you're trying to solve
3. **Propose Solution**: Suggest implementation approach if possible
4. **Consider Guild**: Identify which guild would handle the feature

---

**Welcome to the AutoCoder4_CC development community!** This project transforms natural language into production-ready systems, and we're excited to have you contribute to making that vision a reality.