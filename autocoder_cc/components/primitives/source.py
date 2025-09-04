"""Source primitive - abstract base class for message generators."""
from typing import TypeVar, Generic
from abc import abstractmethod
from .base import Primitive

T = TypeVar('T')

class Source(Primitive, Generic[T]):
    """Source primitive: 0→N - abstract base for message generators.
    
    Sources generate data from nothing (0 inputs) and send to N outputs.
    This is an ABSTRACT BASE CLASS - subclasses must implement generate().
    
    Recipe-expanded components will inherit from this and implement
    the generate() method to produce domain-specific messages.
    """
    
    @abstractmethod
    async def generate(self) -> T:
        """Generate the next message.
        
        Must be implemented by subclasses to produce domain-specific data.
        
        Returns:
            The generated message of type T
        """
        pass
        await super().cleanup()