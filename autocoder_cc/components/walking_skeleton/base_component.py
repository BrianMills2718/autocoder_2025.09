"""Base class with proper anyio task group management."""
import anyio
from typing import Optional
from abc import ABC, abstractmethod

class WalkingSkeletonComponent(ABC):
    """Base class with proper anyio task group management."""
    
    def __init__(self, name: str):
        self.name = name
        self._cancel_scope: Optional[anyio.CancelScope] = None
        self._background_task: Optional[anyio.TaskStatus] = None
        
    async def setup(self):
        """Setup component and start background tasks."""
        # Create cancel scope for clean shutdown
        self._cancel_scope = anyio.CancelScope()
        
    async def run(self):
        """Run component with background tasks."""
        async with anyio.create_task_group() as tg:
            # Start background task with cancel scope
            tg.start_soon(self._run_with_cancel_scope)
            
    async def _run_with_cancel_scope(self):
        """Run background task with cancellation support."""
        with self._cancel_scope:
            await self._process_loop()
            
    @abstractmethod
    async def _process_loop(self):
        """Override this in subclasses."""
        pass
        
    async def cleanup(self):
        """Clean shutdown of background tasks."""
        if self._cancel_scope:
            self._cancel_scope.cancel()
            # Give tasks time to clean up
            await anyio.sleep(0.1)