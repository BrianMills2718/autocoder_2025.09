"""Abstract base classes for port-based architecture primitives.

The 5 mathematical primitives that form the foundation of the port-based architecture:
- Source: 0→N message generator (abstract)
- Sink: N→0 message consumer (abstract)
- Transformer: 1→{0..1} message processor - may drop (abstract)
- Splitter: 1→N message distributor (abstract)
- Merger: N→1 message combiner (abstract)

IMPORTANT: These are ABSTRACT BASE CLASSES - not directly instantiable!
Recipe-expanded components will inherit from these and implement the abstract methods.
"""

from .base import Primitive
from .source import Source
from .sink import Sink
from .transformer import Transformer
from .splitter import Splitter
from .merger import Merger

__all__ = [
    'Primitive',
    'Source',
    'Sink',
    'Transformer',
    'Splitter',
    'Merger'
]

# Map primitive names to classes for recipe system
PRIMITIVE_REGISTRY = {
    'Source': Source,
    'Sink': Sink,
    'Transformer': Transformer,
    'Splitter': Splitter,
    'Merger': Merger
}

def get_primitive_class(primitive_type: str):
    """Get the primitive class for recipe expansion.
    
    This is used by the recipe system to determine which base class
    a recipe-expanded component should inherit from.
    
    Args:
        primitive_type: Type of primitive ('Source', 'Sink', etc.)
        
    Returns:
        The primitive class (not instantiated)
        
    Raises:
        ValueError: If primitive_type is not recognized
    """
    if primitive_type not in PRIMITIVE_REGISTRY:
        raise ValueError(
            f"Unknown primitive type: {primitive_type}. "
            f"Valid types: {list(PRIMITIVE_REGISTRY.keys())}"
        )
    
    return PRIMITIVE_REGISTRY[primitive_type]