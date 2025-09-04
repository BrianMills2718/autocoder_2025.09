"""Sink primitive - abstract base class for message consumers."""
from typing import TypeVar, Generic
from abc import abstractmethod
from .base import Primitive

T = TypeVar('T')

class Sink(Primitive, Generic[T]):
    """Sink primitive: N→0 - abstract base for message consumers.
    
    Sinks consume data from N inputs and produce nothing (0 outputs).
    This is an ABSTRACT BASE CLASS - subclasses must implement consume().
    
    Recipe-expanded components will inherit from this and implement
    the consume() method to handle domain-specific messages.
    """
    
    @abstractmethod
    async def consume(self, item: T) -> None:
        """Consume an incoming message.
        
        Must be implemented by subclasses to handle domain-specific data.
        
        Args:
            item: The message to consume of type T
        """
        pass