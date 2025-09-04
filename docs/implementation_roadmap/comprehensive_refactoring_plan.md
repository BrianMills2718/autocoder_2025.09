# Comprehensive Refactoring and Testing Plan for autocoder4_cc

## Executive Summary

This document outlines a complete refactoring and testing strategy for the autocoder4_cc codebase, addressing critical system issues and implementing comprehensive improvements. **UPDATED** to include all identified gaps from deep system analysis. The plan spans 8 weeks:

**Phase 0: LLM Generation Architecture Fixes** - Fix fundamental issues causing 80% generation failure rate
**Phase 1: Critical System Fixes** - Fix import paths, dependencies, and system-breaking issues  
**Phase 2: Architectural Refactoring** - Break up god objects, implement DI, clean architecture
**Phase 3: Testing Framework** - Comprehensive test coverage with TDD and centralized configuration
**Phase 4: Security & Performance** - Security hardening and performance optimization
**Phase 5: Integration & Validation** - End-to-end validation and deployment pipeline
**Phase 6: Documentation & Alignment** - Fix documentation-code misalignment
**Phase 7: UI Automation & Final Validation** - Add UI generation with Puppeteer MCP

## ⚠️ CRITICAL UPDATE: LLM Generation Must Be Fixed First

**Discovery**: Investigation revealed the LLM generation system has fundamental architectural flaws causing 80% failure rate:
- LLM generates 6,614 characters but `has_business_logic: False`
- 150+ lines of boilerplate wasted in every prompt
- Blueprint business requirements lost during conversion
- Validation checks for infrastructure instead of business logic

**Impact**: All other phases depend on working component generation. Phase 0 must be completed first.

**Reference**: [Phase 0: LLM Generation Architecture Fixes](./phase_0_llm_generation_fixes.md)

## Phase 1: Prompt Management System

### 1.1 Prompt Directory Structure

```
autocoder_cc/
└── prompts/
    ├── __init__.py
    ├── blueprint_generation/
    │   ├── natural_language_to_blueprint.yaml
    │   ├── system_analysis.yaml
    │   └── blueprint_structure.yaml
    ├── component_generation/
    │   ├── base_component.yaml
    │   ├── api_endpoint.yaml
    │   ├── data_store.yaml
    │   ├── message_bus.yaml
    │   ├── router.yaml
    │   └── component_context.yaml
    ├── validation/
    │   ├── code_validation.yaml
    │   └── blueprint_validation.yaml
    └── deployment/
        ├── dockerfile_generation.yaml
        ├── k8s_manifests.yaml
        └── docker_compose.yaml
```

### 1.2 Prompt File Format

Each prompt file will use YAML format with:
- Metadata (version, description, author)
- Variables that can be injected
- The actual prompt template
- Example outputs for testing

```yaml
# prompts/component_generation/base_component.yaml
metadata:
  version: "1.0.0"
  description: "Generate base component implementation"
  author: "autocoder-team"
  
variables:
  - component_name: "Name of the component"
  - component_type: "Type of component (Store, Source, Sink, etc.)"
  - blueprint_context: "Full blueprint context for understanding system"
  - ports: "Component port configuration"
  - config: "Component configuration parameters"

prompt: |
  Generate a Python component implementation for the following specification:
  
  Component Name: {component_name}
  Component Type: {component_type}
  
  Blueprint Context:
  {blueprint_context}
  
  Port Configuration:
  {ports}
  
  Configuration Parameters:
  {config}
  
  Requirements:
  1. Import necessary dependencies at the top
  2. Implement the component class inheriting from appropriate base
  3. Include proper initialization with configuration
  4. Implement all required methods for the component type
  5. Add comprehensive error handling
  6. Include logging for debugging
  7. Follow Python best practices and PEP-8
  
  Generate ONLY the Python code, no explanations.

examples:
  - input:
      component_name: "CustomerDataStore"
      component_type: "Store"
      blueprint_context: "Customer analytics system..."
      ports: 
        input: ["data_in"]
        output: ["data_out"]
      config:
        database_url: "postgresql://..."
    output: |
      import asyncio
      from typing import Dict, Any, Optional
      from autocoder_cc.components.store import Store
      ...
```

### 1.3 Prompt Loader Implementation

```python
# autocoder_cc/prompts/prompt_manager.py
from pathlib import Path
import yaml
from typing import Dict, Any, Optional
import jinja2

class PromptManager:
    """Manages loading and rendering of prompts from files."""
    
    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.prompts_dir))
        )
    
    def load_prompt(self, prompt_path: str) -> Dict[str, Any]:
        """Load a prompt file and cache it."""
        if prompt_path in self._cache:
            return self._cache[prompt_path]
            
        full_path = self.prompts_dir / prompt_path
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")
            
        with open(full_path, 'r') as f:
            prompt_data = yaml.safe_load(f)
            
        self._cache[prompt_path] = prompt_data
        return prompt_data
    
    def render_prompt(self, prompt_path: str, variables: Dict[str, Any]) -> str:
        """Render a prompt with given variables."""
        prompt_data = self.load_prompt(prompt_path)
        
        # Validate required variables
        required_vars = {v['name'] for v in prompt_data.get('variables', [])}
        provided_vars = set(variables.keys())
        missing = required_vars - provided_vars
        
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Render the prompt
        template = self._jinja_env.from_string(prompt_data['prompt'])
        return template.render(**variables)
```

## Phase 2: Comprehensive Unit Testing Strategy

### 2.1 Test Structure for Code Generation Pipeline

```
tests/
├── unit/
│   ├── test_prompt_manager.py
│   ├── blueprint_generation/
│   │   ├── test_natural_language_parser.py
│   │   ├── test_blueprint_generator.py
│   │   └── test_blueprint_validator.py
│   ├── component_generation/
│   │   ├── test_base_component_generator.py
│   │   ├── test_api_endpoint_generator.py
│   │   ├── test_store_generator.py
│   │   ├── test_router_generator.py
│   │   └── test_message_bus_generator.py
│   ├── validation/
│   │   ├── test_ast_validator.py
│   │   ├── test_blueprint_validator.py
│   │   └── test_component_validator.py
│   └── healing/
│       ├── test_ast_healer.py
│       ├── test_blueprint_healer.py
│       └── test_component_healer.py
```

### 2.2 Unit Test Example for Component Generation

```python
# tests/unit/component_generation/test_store_generator.py
import pytest
from pathlib import Path
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
from autocoder_cc.prompts.prompt_manager import PromptManager

class TestStoreComponentGeneration:
    """Test Store component generation with real LLM calls."""
    
    @pytest.fixture
    def generator(self):
        """Create generator with test configuration."""
        return LLMComponentGenerator(
            prompt_manager=PromptManager(),
            model="gpt-4o-mini"  # Use correct model
        )
    
    def test_generate_simple_store(self, generator):
        """Test generating a basic Store component."""
        component_spec = {
            "name": "CustomerStore",
            "type": "Store",
            "ports": {
                "input": ["data_in"],
                "output": ["data_out"]
            },
            "config": {
                "database_url": "postgresql://test",
                "table_name": "customers"
            }
        }
        
        blueprint_context = """
        System: Customer Analytics
        Purpose: Store and retrieve customer data
        Components: CustomerStore, DataProcessor
        """
        
        # Generate the component
        generated_code = generator.generate_component(
            component_spec=component_spec,
            blueprint_context=blueprint_context
        )
        
        # Verify the generated code
        assert "class CustomerStore(Store):" in generated_code
        assert "import" in generated_code
        assert "async def store(" in generated_code
        assert "async def retrieve(" in generated_code
        
        # Verify it's valid Python
        compile(generated_code, "test.py", "exec")
        
    def test_generated_store_has_error_handling(self, generator):
        """Test that generated stores include proper error handling."""
        component_spec = {
            "name": "DataStore",
            "type": "Store",
            "ports": {"input": ["data_in"], "output": ["data_out"]},
            "config": {"database_url": "postgresql://test"}
        }
        
        generated_code = generator.generate_component(
            component_spec=component_spec,
            blueprint_context="Data storage system"
        )
        
        # Check for error handling patterns
        assert "try:" in generated_code
        assert "except" in generated_code
        assert "logger" in generated_code or "logging" in generated_code
        
    def test_store_includes_connection_management(self, generator):
        """Test that stores properly manage database connections."""
        component_spec = {
            "name": "PersistentStore",
            "type": "Store",
            "ports": {"input": ["data_in"], "output": ["data_out"]},
            "config": {"database_url": "postgresql://test"}
        }
        
        generated_code = generator.generate_component(
            component_spec=component_spec,
            blueprint_context="Persistent storage system"
        )
        
        # Check for connection lifecycle
        assert "async def initialize(" in generated_code
        assert "async def cleanup(" in generated_code
        assert "async with" in generated_code or "await self.connect" in generated_code
```

### 2.3 Testing Each Generation Step

```python
# tests/unit/blueprint_generation/test_natural_language_parser.py
import pytest
from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToBlueprint

class TestNaturalLanguageConversion:
    """Test natural language to blueprint conversion."""
    
    @pytest.fixture
    def converter(self):
        return NaturalLanguageToBlueprint()
    
    def test_simple_system_description(self, converter):
        """Test converting a simple system description."""
        description = "Create a customer data processing system"
        
        blueprint_yaml = converter.convert(description)
        
        # Verify structure
        assert blueprint_yaml.startswith("schema_version:")
        assert "policy:" in blueprint_yaml
        assert "system:" in blueprint_yaml
        assert "components:" in blueprint_yaml
        
        # Verify it's valid YAML
        import yaml
        parsed = yaml.safe_load(blueprint_yaml)
        assert parsed["schema_version"] == "1.0.0"
        assert "policy" in parsed
        assert "system" in parsed
        
    def test_complex_system_with_requirements(self, converter):
        """Test converting complex system with specific requirements."""
        description = """
        Build an e-commerce order processing system with:
        - REST API for order submission
        - PostgreSQL for order storage
        - Redis for caching
        - Async processing queue
        - Email notifications
        """
        
        blueprint_yaml = converter.convert(description)
        parsed = yaml.safe_load(blueprint_yaml)
        
        # Verify components were identified
        components = parsed["system"]["components"]
        component_names = [c["name"] for c in components]
        
        assert any("api" in name.lower() for name in component_names)
        assert any("store" in name.lower() or "database" in name.lower() for name in component_names)
        assert any("cache" in name.lower() or "redis" in name.lower() for name in component_names)
        assert any("queue" in name.lower() or "processor" in name.lower() for name in component_names)
        
    def test_schema_version_placement(self, converter):
        """Test that schema_version is placed at root level."""
        description = "Simple test system"
        
        blueprint_yaml = converter.convert(description)
        lines = blueprint_yaml.split('\n')
        
        # First non-empty line should be schema_version
        first_line = next(line for line in lines if line.strip())
        assert first_line.startswith("schema_version:")
        
        # Parse and verify structure
        parsed = yaml.safe_load(blueprint_yaml)
        assert "schema_version" in parsed
        assert parsed["schema_version"] == "1.0.0"
        
        # Ensure schema_version is NOT inside system block
        assert "schema_version" not in parsed.get("system", {})
```

## Phase 3: Validation and Self-Healing Testing

### 3.1 Validation Test Structure

Every validator must have:
1. Tests for what it validates
2. Tests for its associated healer
3. Tests that healer fixes validator's issues

```python
# tests/unit/validation/test_validation_healing_pairs.py
import pytest
from autocoder_cc.validation.blueprint_validator import BlueprintValidator
from autocoder_cc.healing.blueprint_healer import BlueprintHealer

class TestValidationHealingIntegration:
    """Test that every validator has working healing."""
    
    def test_blueprint_validation_healing_cycle(self):
        """Test blueprint validation and healing work together."""
        validator = BlueprintValidator()
        healer = BlueprintHealer()
        
        # Create intentionally broken blueprint
        broken_blueprint = {
            "system": {
                "schema_version": "1.0",  # Wrong location and format
                "name": "test_system",
                "components": []
            }
            # Missing policy block
        }
        
        # Validate - should fail
        validation_result = validator.validate(broken_blueprint)
        assert not validation_result.is_valid
        assert "schema_version" in str(validation_result.errors)
        assert "policy" in str(validation_result.errors)
        
        # Heal
        healed_blueprint = healer.heal(broken_blueprint)
        
        # Re-validate - should pass
        healed_result = validator.validate(healed_blueprint)
        assert healed_result.is_valid
        assert healed_blueprint["schema_version"] == "1.0.0"
        assert "policy" in healed_blueprint
        
    def test_component_validation_healing_cycle(self):
        """Test component validation and healing work together."""
        from autocoder_cc.validation.component_validator import ComponentValidator
        from autocoder_cc.healing.component_healer import ComponentHealer
        
        validator = ComponentValidator()
        healer = ComponentHealer()
        
        # Broken component code
        broken_code = """
import asyncio
# Missing base class import

class DataProcessor:  # Not inheriting from base
    def __init__(self):
        pass  # Missing super().__init__()
    
    # Missing required methods
"""
        
        # Validate - should fail
        validation_result = validator.validate(broken_code, component_type="Processor")
        assert not validation_result.is_valid
        
        # Heal
        healed_code = healer.heal(broken_code, component_type="Processor", validation_result)
        
        # Re-validate - should pass
        healed_result = validator.validate(healed_code, component_type="Processor")
        assert healed_result.is_valid
```

### 3.2 AST Validation and Healing Tests

```python
# tests/unit/validation/test_ast_validation_healing.py
import ast
import pytest
from autocoder_cc.validation.ast_validator import ASTValidator
from autocoder_cc.healing.ast_self_healing import ASTSelfHealing

class TestASTValidationHealing:
    """Test AST validation and healing."""
    
    def test_fix_missing_imports(self):
        """Test healing adds missing imports."""
        code = """
class MyComponent(Store):
    async def process(self):
        await asyncio.sleep(1)
        data = {"timestamp": datetime.now()}
        return json.dumps(data)
"""
        
        validator = ASTValidator()
        healer = ASTSelfHealing()
        
        # Validate - should detect missing imports
        validation = validator.validate(code)
        assert not validation.is_valid
        assert any("import" in str(e) for e in validation.errors)
        
        # Heal
        healed_code = healer.heal(code, validation)
        
        # Should have added imports
        assert "import asyncio" in healed_code
        assert "import json" in healed_code
        assert "from datetime import datetime" in healed_code
        assert "from autocoder_cc.components.store import Store" in healed_code
        
        # Re-validate
        healed_validation = validator.validate(healed_code)
        assert healed_validation.is_valid
        
    def test_fix_undefined_variables(self):
        """Test healing fixes undefined variables."""
        code = """
def process_data(data):
    result = transform(data)  # undefined function
    logger.info(f"Processed: {result}")  # undefined logger
    return result
"""
        
        validator = ASTValidator()
        healer = ASTSelfHealing()
        
        validation = validator.validate(code)
        healed_code = healer.heal(code, validation)
        
        # Should define missing elements
        assert "logger = logging.getLogger" in healed_code or "import logging" in healed_code
        assert "def transform(" in healed_code or "transform = " in healed_code
```

## Phase 4: TDD Philosophy - No Mocking

### 4.1 TDD Principles for autocoder4_cc

1. **Real Components Only**: Test with actual LLM calls, databases, etc.
2. **Fail-Fast Testing**: Tests should fail immediately on issues
3. **Evidence-Based**: Save all test outputs for verification
4. **No Stubs/Mocks**: Use real implementations or don't test
5. **Integration First**: Focus on end-to-end behavior

### 4.2 TDD Workflow Implementation

```python
# tests/tdd/test_new_component_type.py
import pytest
from autocoder_cc.tdd.tracker import TDDTracker

class TestNewComponentType:
    """TDD for implementing a new component type."""
    
    @pytest.fixture
    def tdd_tracker(self):
        """Track TDD state transitions."""
        return TDDTracker()
    
    def test_red_eventbus_component_generation(self, tdd_tracker):
        """RED: Test that EventBus component type doesn't exist yet."""
        tdd_tracker.start_red_phase("EventBus component generation")
        
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        
        generator = LLMComponentGenerator()
        
        # This should fail because EventBus isn't implemented
        with pytest.raises(ValueError, match="Unknown component type: EventBus"):
            generator.generate_component({
                "name": "SystemEventBus",
                "type": "EventBus",
                "config": {}
            })
        
        tdd_tracker.confirm_red_phase()
    
    def test_green_eventbus_component_generation(self, tdd_tracker):
        """GREEN: Implement EventBus component generation."""
        tdd_tracker.start_green_phase("EventBus component generation")
        
        # Add EventBus to component types
        from autocoder_cc.components.eventbus import EventBus  # Will need to create
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        
        generator = LLMComponentGenerator()
        
        # Now it should work
        generated_code = generator.generate_component({
            "name": "SystemEventBus",
            "type": "EventBus",
            "config": {
                "max_subscribers": 100,
                "async_delivery": True
            }
        })
        
        assert "class SystemEventBus(EventBus):" in generated_code
        assert "async def publish(" in generated_code
        assert "async def subscribe(" in generated_code
        
        # Verify it compiles
        compile(generated_code, "test.py", "exec")
        
        tdd_tracker.confirm_green_phase()
    
    def test_refactor_eventbus_prompt_extraction(self, tdd_tracker):
        """REFACTOR: Extract EventBus prompts to file."""
        tdd_tracker.start_refactor_phase("EventBus prompt extraction")
        
        # Create prompt file
        prompt_content = """
metadata:
  version: "1.0.0"
  description: "Generate EventBus component"

variables:
  - component_name: "Name of the EventBus"
  - config: "EventBus configuration"

prompt: |
  Generate an EventBus component named {component_name} with config: {config}
  
  Include:
  - publish method for sending events
  - subscribe method for registering handlers
  - unsubscribe method
  - proper async handling
  - thread-safe operations
"""
        
        # Save prompt file
        prompt_path = Path("prompts/component_generation/eventbus.yaml")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_content)
        
        # Update generator to use prompt file
        from autocoder_cc.prompts.prompt_manager import PromptManager
        prompt_manager = PromptManager()
        
        # Verify it still works
        generator = LLMComponentGenerator(prompt_manager=prompt_manager)
        generated_code = generator.generate_component({
            "name": "RefactoredEventBus",
            "type": "EventBus",
            "config": {}
        })
        
        assert "class RefactoredEventBus(EventBus):" in generated_code
        
        tdd_tracker.confirm_refactor_phase()
```

## Phase 5: Complete Test Coverage Requirements

### 5.1 Critical Path Tests

```python
# tests/e2e/test_critical_paths.py
import pytest
import tempfile
from pathlib import Path

class TestCriticalPaths:
    """Test the critical paths through the system."""
    
    @pytest.mark.critical
    async def test_natural_language_to_working_system(self):
        """Test complete pipeline from NL to deployed system."""
        from autocoder_cc.generate_deployed_system import (
            convert_to_blueprint,
            generate_system,
            validate_system_structure,
            deploy_and_test_system
        )
        
        # Natural language input
        description = "Create a simple REST API for user management"
        
        # Phase 1: NL → Blueprint
        blueprint_yaml = convert_to_blueprint(description)
        assert blueprint_yaml is not None
        assert "schema_version: \"1.0.0\"" in blueprint_yaml
        
        # Phase 2: Blueprint → System
        generated_system = await generate_system(blueprint_yaml)
        assert generated_system is not None
        assert generated_system.output_directory.exists()
        
        # Phase 3: Validate Structure
        valid = validate_system_structure(generated_system)
        assert valid is True
        
        # Phase 4: Deploy and Test
        deployed = deploy_and_test_system(generated_system)
        assert deployed is True
        
    @pytest.mark.critical  
    def test_every_component_type_generates_valid_code(self):
        """Test that each component type generates valid Python."""
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        
        generator = LLMComponentGenerator()
        
        component_types = [
            "Store", "Source", "Sink", "Processor",
            "APIEndpoint", "MessageBus", "Router"
        ]
        
        for comp_type in component_types:
            spec = {
                "name": f"Test{comp_type}",
                "type": comp_type,
                "config": {}
            }
            
            code = generator.generate_component(spec)
            
            # Should be valid Python
            compile(code, f"test_{comp_type}.py", "exec")
            
            # Should have correct class
            assert f"class Test{comp_type}(" in code
            
            # Should have required methods
            if comp_type == "Store":
                assert "async def store(" in code
                assert "async def retrieve(" in code
            elif comp_type == "APIEndpoint":
                assert "async def handle_request(" in code
```

### 5.2 Observability and Metrics Tests

```python
# tests/unit/observability/test_pipeline_metrics.py
import pytest
from autocoder_cc.observability.pipeline_metrics import PipelineMetrics, PipelineStage

class TestPipelineMetrics:
    """Test pipeline observability."""
    
    def test_stage_tracking(self):
        """Test that pipeline stages are tracked correctly."""
        metrics = PipelineMetrics()
        
        # Start a stage
        metrics.start_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION)
        
        # Verify it's tracked as in progress
        assert metrics.is_stage_in_progress(PipelineStage.NATURAL_LANGUAGE_CONVERSION)
        
        # End successfully
        metrics.end_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION, success=True)
        
        # Verify metrics
        summary = metrics.get_summary()
        assert summary["stages_completed"] == 1
        assert summary["stages_failed"] == 0
        
    def test_critical_error_detection(self):
        """Test that critical errors are properly flagged."""
        metrics = PipelineMetrics()
        
        # Record a critical error
        error = ValueError("Blueprint validation failed: schema_version missing")
        metrics.record_critical_error(PipelineStage.BLUEPRINT_PARSING, error)
        
        # Verify it's flagged as critical
        summary = metrics.get_summary()
        assert summary["has_critical_errors"] is True
        assert "blueprint" in summary["critical_errors"][0].lower()
```

## Phase 6: Refactoring Roadmap

### 6.1 God Object Decomposition

Break down `system_generator.py` (2000+ lines) into:

```python
# autocoder_cc/generation/
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py          # Main pipeline orchestration (200 lines)
│   ├── stage_manager.py         # Pipeline stage management (150 lines)
│   └── error_handler.py         # Pipeline error handling (100 lines)
├── blueprint/
│   ├── __init__.py
│   ├── parser.py                # Blueprint parsing (300 lines)
│   ├── validator.py             # Blueprint validation (200 lines)
│   ├── healer.py                # Blueprint healing (200 lines)
│   └── converter.py             # NL to blueprint conversion (250 lines)
├── component/
│   ├── __init__.py
│   ├── generator.py             # Component generation (300 lines)
│   ├── validator.py             # Component validation (200 lines)
│   ├── healer.py                # Component healing (200 lines)
│   └── templates.py             # Component templates (150 lines)
└── deployment/
    ├── __init__.py
    ├── docker_generator.py       # Docker artifact generation (200 lines)
    ├── k8s_generator.py          # K8s manifest generation (250 lines)
    └── test_generator.py         # Test generation (200 lines)
```

### 6.2 Dependency Injection Refactoring

```python
# autocoder_cc/core/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Prompt management
    prompt_manager = providers.Singleton(
        PromptManager,
        prompts_dir=config.prompts_dir
    )
    
    # LLM providers
    llm_provider = providers.Selector(
        config.llm_provider,
        openai=providers.Singleton(OpenAIProvider, config=config.openai),
        anthropic=providers.Singleton(AnthropicProvider, config=config.anthropic),
        gemini=providers.Singleton(GeminiProvider, config=config.gemini)
    )
    
    # Validators and healers
    blueprint_validator = providers.Factory(BlueprintValidator)
    blueprint_healer = providers.Factory(BlueprintHealer)
    
    component_validator = providers.Factory(ComponentValidator)
    component_healer = providers.Factory(ComponentHealer)
    
    # Generators
    blueprint_generator = providers.Factory(
        BlueprintGenerator,
        prompt_manager=prompt_manager,
        llm_provider=llm_provider,
        validator=blueprint_validator,
        healer=blueprint_healer
    )
    
    component_generator = providers.Factory(
        ComponentGenerator,
        prompt_manager=prompt_manager,
        llm_provider=llm_provider,
        validator=component_validator,
        healer=component_healer
    )
    
    # Pipeline orchestrator
    pipeline_orchestrator = providers.Singleton(
        PipelineOrchestrator,
        blueprint_generator=blueprint_generator,
        component_generator=component_generator,
        metrics=providers.Singleton(PipelineMetrics)
    )
```

### 6.3 Error Handling Improvements

```python
# autocoder_cc/error_handling/pipeline_errors.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"     # System cannot continue
    ERROR = "error"           # Component failed but system continues  
    WARNING = "warning"       # Issue but not blocking
    INFO = "info"            # Informational

@dataclass
class PipelineError:
    """Rich error information for pipeline failures."""
    stage: PipelineStage
    severity: ErrorSeverity
    error_type: str
    message: str
    context: Dict[str, Any]
    original_exception: Optional[Exception] = None
    suggested_fix: Optional[str] = None
    
    def is_critical(self) -> bool:
        """Check if this error is critical."""
        return self.severity == ErrorSeverity.CRITICAL
    
    def format_for_user(self) -> str:
        """Format error for user display."""
        lines = [
            f"{'🚨' if self.is_critical() else '⚠️'} {self.severity.value.upper()}: {self.message}",
            f"   Stage: {self.stage.value}",
            f"   Type: {self.error_type}"
        ]
        
        if self.suggested_fix:
            lines.append(f"   💡 Suggested Fix: {self.suggested_fix}")
            
        if self.context:
            lines.append("   Context:")
            for key, value in self.context.items():
                lines.append(f"     - {key}: {value}")
                
        return "\n".join(lines)
```

## Phase 7: Implementation Priority

### 7.1 Critical Path First (Week 1)

1. **Fix Blueprint Generation** (Day 1-2)
   - Fix schema_version placement
   - Add policy block generation
   - Create blueprint healer
   - Add comprehensive tests

2. **Fix Component Generation** (Day 3-4)
   - Update model configuration
   - Create prompt files for each component type
   - Test each component type generates valid code
   - Add component healing

3. **Add Pipeline Observability** (Day 5)
   - Implement pipeline metrics
   - Add critical error detection
   - Create stage tracking
   - Surface errors prominently

### 7.2 Refactoring Phase (Week 2)

1. **Break Up God Object** (Day 1-3)
   - Extract pipeline orchestration
   - Extract blueprint handling
   - Extract component generation
   - Extract deployment generation

2. **Implement Dependency Injection** (Day 4)
   - Create DI container
   - Wire up all components
   - Remove circular dependencies

3. **Improve Error Handling** (Day 5)
   - Implement rich error types
   - Add error context preservation
   - Create user-friendly error messages

### 7.3 Testing Phase (Week 3)

1. **Unit Tests** (Day 1-2)
   - Test each generation step
   - Test all validators and healers
   - Test prompt rendering

2. **Integration Tests** (Day 3-4)
   - Test pipeline stages
   - Test component interactions
   - Test error propagation

3. **End-to-End Tests** (Day 5)
   - Test complete system generation
   - Test various system types
   - Test error recovery

## Conclusion

This comprehensive plan addresses:

1. **Prompt Management**: Externalizing prompts for easy iteration
2. **Testing Strategy**: Real tests for every component without mocking
3. **Validation & Healing**: Every validator paired with working healer
4. **TDD Approach**: Clear RED-GREEN-REFACTOR cycles
5. **Refactoring**: Breaking down god objects and improving architecture

The key is to start with fixing the critical path (blueprint generation → component generation → deployment) with comprehensive tests, then refactor the architecture while maintaining the working system.