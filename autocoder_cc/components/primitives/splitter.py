"""Splitter primitive - abstract base class for message distributors."""
from typing import TypeVar, Generic, Dict
from abc import abstractmethod
from .base import Primitive

T = TypeVar('T')


class Splitter(Primitive, Generic[T]):
    """Splitter primitive: 1→N - abstract base for message distributors.
    
    Splitters distribute data from 1 input to N outputs.
    This is an ABSTRACT BASE CLASS - subclasses must implement split().
    
    Recipe-expanded components will inherit from this and implement
    the split() method to route domain-specific messages.
    """
    
    @abstractmethod
    async def split(self, item: T) -> Dict[str, T]:
        """Split an input item to multiple outputs.
        
        Must be implemented by subclasses to determine routing.
        
        Args:
            item: The input item of type T
            
        Returns:
            Dict mapping output port names to items to send
        """
        pass
