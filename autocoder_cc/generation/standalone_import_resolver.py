from autocoder_cc.observability.structured_logging import get_logger
"""
Standalone Import Path Resolver
Generates imports for components that work without autocoder framework.
Part of Enterprise Roadmap v3 - make generated systems truly standalone.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path


class StandaloneImportResolver:
    """
    Resolves import paths for standalone component generation.
    Components can run without the autocoder framework.
    """
    
    def __init__(self, use_local_base: bool = True):
        """
        Args:
            use_local_base: If True, import from local component_base.py
                          If False, generate fully self-contained components
        """
        self.use_local_base = use_local_base
    
    def get_base_imports(self, component_type: str, from_test: bool = False) -> List[str]:
        """Get base imports for a component."""
        imports = []
        
        # Standard library imports
        imports.extend([
            "import asyncio",
            "import logging", 
            "from typing import Dict, Any, Optional, List",
            "from abc import ABC, abstractmethod",
            "from dataclasses import dataclass, field",
            "from datetime import datetime",
            ""
        ])
        
        # Component base class imports
        if self.use_local_base:
            # Import from local component_base.py
            if from_test:
                imports.append("from ..component_base import Component, ComponentStatus")
            else:
                imports.append("from .component_base import Component, ComponentStatus")
        else:
            # Component will be fully self-contained
            imports.append("# Component base class defined inline")
        
        return imports
    
    def get_component_specific_imports(self, component_type: str) -> List[str]:
        """Get imports specific to a component type."""
        imports = []
        
        type_import_map = {
            "APIEndpoint": [
                "from fastapi import FastAPI, HTTPException, Request, Response, Depends",
                "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials",
                "from pydantic import BaseModel, Field, validator",
                "import httpx",
                "import uvicorn",
            ],
            "Store": [
                "import asyncpg",
                "import aiomysql", 
                "import aiosqlite",
                "from sqlalchemy import create_engine, Column, String, Integer, DateTime",
                "from sqlalchemy.ext.declarative import declarative_base",
                "from sqlalchemy.orm import sessionmaker",
                "import json",
            ],
            "Transformer": [
                "import json",
                "import pandas as pd",
                "from datetime import datetime, timedelta",
            ],
            "Source": [
                "import aiofiles",
                "import json",
                "from pathlib import Path",
            ],
            "Sink": [
                "import aiofiles",
                "import json",
                "from pathlib import Path",
            ],
            "Controller": [
                "from enum import Enum",
                "import json",
            ],
            "MetricsEndpoint": [
                "from prometheus_client import Counter, Histogram, Gauge, generate_latest",
                "from fastapi import FastAPI, Response",
            ],
            "Accumulator": [
                "import redis.asyncio as redis",
                "import json",
                "from typing import Union",
            ],
            "MessageBusSource": [
                "import aio_pika",
                "import json",
            ],
            "MessageBusSink": [
                "import aio_pika", 
                "import json",
            ],
        }
        
        imports.extend(type_import_map.get(component_type, []))
        
        # Add anyio for all components (stream support)
        imports.append("import anyio")
        
        return imports
    
    def get_capability_imports(self, capabilities: List[str]) -> List[str]:
        """Get imports for capability classes."""
        imports = []
        
        capability_imports = {
            "retry": ["from tenacity import retry, stop_after_attempt, wait_exponential"],
            "circuit_breaker": ["from circuit_breaker import CircuitBreaker"],
            "rate_limit": ["from asyncio import Semaphore"],
            "cache": ["from functools import lru_cache"],
            "metrics": ["from prometheus_client import Counter, Histogram"],
        }
        
        for capability in capabilities:
            imports.extend(capability_imports.get(capability.lower(), []))
        
        return imports
    
    def generate_inline_base_class(self) -> str:
        """Generate inline Component base class for fully standalone operation."""
        return '''
class ComponentStatus:
    """Component status tracking."""
    def __init__(self):
        self.messages_processed = 0
        self.errors = 0
        self.is_running = False
        self.last_error = None
        self.last_processed = None


class Component(ABC):
    """
    Base component class for standalone operation.
    Provides core functionality without external dependencies.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Component.{self.name}")
        
        # Stream connections
        self.send_streams: Dict[str, Any] = {}
        self.receive_streams: Dict[str, Any] = {}
        
        # Status tracking
        self._status = ComponentStatus()
        
        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def setup(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Setup component before processing starts."""
        self.logger.info(f"Setting up component: {self.name}")
        self._status.is_running = True
    
    @abstractmethod
    async def process(self) -> None:
        """
        Main processing loop - must be implemented by subclasses.
        This method should run continuously until shutdown.
        """
        pass
    
    async def cleanup(self) -> None:
        """Cleanup component resources."""
        self.logger.info(f"Cleaning up component: {self.name}")
        self._status.is_running = False
        
        # Close all streams
        for stream in self.send_streams.values():
            if hasattr(stream, 'aclose'):
                await stream.aclose()
        for stream in self.receive_streams.values():
            if hasattr(stream, 'aclose'):
                await stream.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Return component health status."""
        return {
            "component": self.name,
            "status": "healthy" if self._status.is_running else "stopped",
            "messages_processed": self._status.messages_processed,
            "errors": self._status.errors,
            "last_error": str(self._status.last_error) if self._status.last_error else None,
            "last_processed": self._status.last_processed.isoformat() if self._status.last_processed else None
        }
    
    def increment_processed(self):
        """Increment processed message counter."""
        self._status.messages_processed += 1
        self._status.last_processed = datetime.utcnow()
    
    def increment_errors(self, error: Optional[Exception] = None):
        """Increment error counter."""
        self._status.errors += 1
        if error:
            self._status.last_error = error
'''
    
    def generate_stream_helpers(self) -> str:
        """Generate helper functions for stream handling."""
        return '''
async def create_memory_stream_pair(max_buffer_size: int = 1000):
    """Create a pair of connected memory streams."""
    send_stream, receive_stream = anyio.create_memory_object_stream(max_buffer_size)
    return send_stream, receive_stream


async def safe_send(stream, item):
    """Safely send item to stream with error handling."""
    try:
        await stream.send(item)
        return True
    except anyio.ClosedResourceError:
        logging.warning("Attempted to send to closed stream")
        return False
    except Exception as e:
        logging.error(f"Error sending to stream: {e}")
        return False


async def safe_receive(stream):
    """Safely receive from stream with error handling."""
    try:
        return await stream.receive()
    except anyio.EndOfStream:
        return None
    except anyio.ClosedResourceError:
        return None
    except Exception as e:
        logging.error(f"Error receiving from stream: {e}")
        return None
'''
    
    def resolve_imports(self, 
                       component_type: str,
                       capabilities: Optional[List[str]] = None,
                       from_test: bool = False,
                       inline_base: bool = False) -> List[str]:
        """
        Resolve all imports for a component.
        
        Args:
            component_type: Type of component (Store, Transformer, etc.)
            capabilities: List of capabilities the component uses
            from_test: Whether imports are for a test file
            inline_base: Whether to inline the base class instead of importing
            
        Returns:
            List of import statements
        """
        all_imports = []
        
        # Get base imports
        base_imports = self.get_base_imports(component_type, from_test)
        all_imports.extend(base_imports)
        
        # Get component-specific imports
        specific_imports = self.get_component_specific_imports(component_type)
        all_imports.extend(specific_imports)
        
        # Get capability imports
        if capabilities:
            cap_imports = self.get_capability_imports(capabilities)
            all_imports.extend(cap_imports)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_imports = []
        for imp in all_imports:
            if imp not in seen and imp.strip():
                seen.add(imp)
                unique_imports.append(imp)
        
        return unique_imports