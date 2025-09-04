"""Abstract base classes for port-based architecture primitives.

These are NOT runnable components - they're bases for inheritance!
Generated components will inherit from these abstract classes.
"""
import anyio
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, Any, List
from autocoder_cc.observability import get_logger

# Type variables for generic primitives
T = TypeVar('T')
U = TypeVar('U')

class Primitive(ABC):
    """Abstract base class for all mathematical primitives.
    
    Primitives are the fundamental building blocks:
    - Source: 0→N (generates data)
    - Sink: N→0 (consumes data)
    - Transformer: 1→{0..1} (transforms data, may drop)
    - Splitter: 1→N (distributes data)
    - Merger: N→1 (combines data)
    
    THIS IS AN ABSTRACT BASE CLASS - NOT DIRECTLY INSTANTIABLE!
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize primitive.
        
        Args:
            name: Component name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.logger = get_logger(f"{self.__class__.__name__}.{name}")
    
    async def setup(self) -> None:
        """Initialize component resources. Can be overridden by subclasses."""
        self.logger.info(f"Setup complete for {self.name}")
    
    async def cleanup(self) -> None:
        """Clean up component resources. Can be overridden by subclasses."""
        self.logger.info(f"Cleanup complete for {self.name}")


class Source(Primitive, Generic[T]):
    """0→N: Generates data from nothing."""
    
    @abstractmethod
    async def generate(self):
        """Generate data items."""
        pass


class Sink(Primitive, Generic[T]):
    """N→0: Consumes data to nothing."""
    
    @abstractmethod
    async def consume(self, item: T) -> None:
        """Consume a data item."""
        pass


class Transformer(Primitive, Generic[T, U]):
    """1→{0..1}: Transforms data, may drop."""
    
    @abstractmethod
    async def transform(self, item: T) -> Optional[U]:
        """Transform an item. Return None to drop."""
        pass


class Splitter(Primitive, Generic[T]):
    """1→N: Distributes data to multiple outputs."""
    
    @abstractmethod
    async def split(self, item: T) -> Dict[str, T]:
        """Split input to multiple outputs.
        
        Returns dict mapping output port names to items.
        """
        pass


class Merger(Primitive, Generic[T]):
    """N→1: Combines multiple inputs into one output."""
    
    @abstractmethod
    async def merge(self, items: List[T]) -> T:
        """Merge multiple inputs into single output.
        
        Args:
            items: List of items from different input ports
            
        Returns:
            Merged output item
        """
        pass