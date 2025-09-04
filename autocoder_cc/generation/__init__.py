"""
Generation Module - Component and system generation utilities

This module contains extracted generation logic from the monolithic system_generator.py:
- ComponentGenerator: LLM-based component generation (~300 lines)
- TemplateEngine: Template rendering and assembly (~250 lines)
"""

from .component_generator import ComponentGenerator, GeneratedComponent
from .template_engine import TemplateEngine

__all__ = [
    'ComponentGenerator',
    'GeneratedComponent', 
    'TemplateEngine'
]