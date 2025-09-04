"""Transformer primitive - abstract base class for message transformers."""
from typing import TypeVar, Generic, Optional
from abc import abstractmethod
from .base import Primitive

T = TypeVar('T')
U = TypeVar('U')

class Transformer(Primitive, Generic[T, U]):
    """Transformer primitive: 1→{0..1} - abstract base for message processors.
    
    Transformers transform data from 1 input to 0 or 1 output (may drop).
    This is an ABSTRACT BASE CLASS - subclasses must implement transform().
    
    Recipe-expanded components will inherit from this and implement
    the transform() method to process domain-specific messages.
    Can return None to drop messages (e.g., for validation/filtering).
    """
    
    @abstractmethod
    async def transform(self, item: T) -> Optional[U]:
        """Transform an input item.
        
        Must be implemented by subclasses to transform domain-specific data.
        Return None to drop the message.
        
        Args:
            item: The input item of type T
            
        Returns:
            Transformed item of type U, or None to drop
        """
        pass
    
    async def on_drop(self, item: T, reason: str) -> None:
        """Called when an item is dropped.
        
        Optional method for subclasses to override for drop handling.
        Default implementation logs the drop.
        
        Args:
            item: The dropped item
            reason: Reason for dropping
        """
        self.logger.debug(f"Dropped item: {reason}")