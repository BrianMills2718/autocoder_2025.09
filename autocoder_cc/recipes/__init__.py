"""Recipe system for configuring primitives as domain components.

The recipe system allows us to define 13 domain-specific component types
using just 5 mathematical primitives as the foundation.
"""
from .registry import RECIPE_REGISTRY, get_recipe
from .expander import RecipeExpander

__all__ = ['RECIPE_REGISTRY', 'get_recipe', 'RecipeExpander']