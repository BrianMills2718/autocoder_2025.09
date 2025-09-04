"""
Production Validators Package

This package contains production-grade validation implementations for the 4-tier validation hierarchy.
These validators were extracted from the evidence directory to create a self-contained validation framework.

Validation Levels:
- Level 1: Framework validation (built into ValidationDrivenOrchestrator)
- Level 2: Component logic validation (component_validator.py)
- Level 3: Integration validation (integration_validator.py)  
- Level 4: Semantic validation (semantic_validator.py)
"""

# Import production validators for easy access
try:
    from .component_validator import Level2ComponentValidator
except ImportError:
    Level2ComponentValidator = None

try:
    from .integration_validator import Level3SystemValidator
    Level3IntegrationValidator = Level3SystemValidator  # Alias for compatibility
except ImportError:
    Level3SystemValidator = None
    Level3IntegrationValidator = None

try:
    from .semantic_validator import Level4SemanticValidator
except ImportError:
    Level4SemanticValidator = None

__all__ = [
    'Level2ComponentValidator',
    'Level3IntegrationValidator', 
    'Level4SemanticValidator'
]