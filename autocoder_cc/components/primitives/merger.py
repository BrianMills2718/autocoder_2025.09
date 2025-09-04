"""Merger primitive - abstract base class for message combiners."""
from typing import TypeVar, Generic, List
from abc import abstractmethod
from .base import Primitive

T = TypeVar('T')

class Merger(Primitive, Generic[T]):
    """Merger primitive: N→1 - abstract base for message combiners.
    
    Mergers combine data from N inputs to 1 output.
    This is an ABSTRACT BASE CLASS - subclasses must implement merge().
    
    Recipe-expanded components will inherit from this and implement
    the merge() method to combine domain-specific messages.
    """
    
    @abstractmethod
    async def merge(self, items: List[T]) -> T:
        """Merge multiple input items into one.
        
        Must be implemented by subclasses to combine domain-specific data.
        
        Args:
            items: List of items of type T from different inputs
            
        Returns:
            Merged item of type T
        """
        pass