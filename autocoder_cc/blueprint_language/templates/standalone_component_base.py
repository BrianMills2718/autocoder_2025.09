#!/usr/bin/env python3
"""
Standalone Component Base - Auto-Generated
This file provides component functionality without requiring autocoder framework
"""

import time
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ComponentStatus:
    """Status information for a component"""
    is_running: bool = False
    is_healthy: bool = True
    items_processed: int = 0
    errors_encountered: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Component(ABC):
    """
    Standalone base class for all components.
    Simplified version without framework dependencies.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Component.{name}")
        self.created_at = time.time()
        
        # Component state
        self._status = ComponentStatus()
        
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the component"""
        self._status.is_running = True
        self.logger.info(f"Component {self.name} setup completed")
    
    @abstractmethod
    async def process(self) -> None:
        """Main processing loop - must be implemented by generated components"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info(f"Component {self.name} cleanup completed")
    
    def get_status(self) -> ComponentStatus:
        """Get current component status"""
        return self._status
    
    async def health_check(self) -> bool:
        """Check if component is healthy"""
        return self._status.is_running and self._status.is_healthy
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        return {
            'status': 'healthy' if self._status.errors_encountered == 0 else 'degraded',
            'component': self.name,
            'type': self.__class__.__name__,
            'error_count': self._status.errors_encountered,
            'uptime': time.time() - self.created_at,
            'items_processed': self._status.items_processed
        }
    
    def increment_processed(self) -> None:
        """Increment the processed items counter"""
        self._status.items_processed += 1
    
    def record_error(self, error: str) -> None:
        """Record an error in component status"""
        self._status.errors_encountered += 1
        self._status.last_error = error
        self._status.is_healthy = False
        self.logger.error(f"Component error: {error}")
