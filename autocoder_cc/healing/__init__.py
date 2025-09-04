"""
Self-Healing System for Generated Code
=====================================

The healing package provides intelligent self-healing capabilities that automatically
detect and fix issues in generated code, ensuring systems are production-ready without
manual intervention.

## Core Components

- **AST Healer**: Fixes syntax errors, incomplete code, import issues, type errors
- **System Healer**: Resolves configuration, integration, deployment, and resource issues
- **Semantic Healer**: Corrects business logic, validation failures, security vulnerabilities

## Quick Start

```python
from autocoder_cc.healing import heal_component, heal_system_configuration

# Heal a component with issues
healed_code = heal_component(
    code=generated_code,
    issues=detected_issues,
    context=system_context
)

# Heal system configuration
healed_config = heal_system_configuration(
    config=system_config,
    errors=config_errors,
    environment=deployment_env
)
```

## Key Features

- **Multi-Level Healing**: AST, system, and semantic level fixes
- **Incremental Healing**: Progressive fixes with validation checkpoints
- **Intelligent Fix Selection**: Issue prioritization and dependency awareness
- **Multi-Model Healing**: LLM integration with fallback strategies
- **Error Recovery**: Graceful degradation and partial fixes
- **Learning System**: Pattern learning and fix history tracking
- **Custom Rules**: Project-specific healing rules and domain logic
- **Performance Optimized**: Incremental healing, caching, parallel processing
"""

from .ast_healer import ASTHealer, heal_component
from .system_healer import SystemHealer, heal_system_configuration
from .semantic_healer import SemanticHealer, heal_business_logic

__all__ = [
    'ASTHealer',
    'SystemHealer', 
    'SemanticHealer',
    'heal_component',
    'heal_system_configuration',
    'heal_business_logic'
]