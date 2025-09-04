#!/usr/bin/env python3
"""
Autocoder V5.2 System-First Architecture Components Package
"""
# UnifiedComponent removed - use ComposedComponent instead
from .api_endpoint import APIEndpoint
from .model import Model
from .store import Store
from .v5_enhanced_store import V5EnhancedStore
from .accumulator import Accumulator
from .controller import Controller
from .stream_processor import StreamProcessor
from .fastapi_endpoint import FastAPIEndpoint
from .message_bus import MessageBusSource
from .composed_base import ComposedComponent
# NO queue_source import - Enterprise Roadmap v2 forbids queue bridges

__all__ = [
    # PREFERRED: Composed Component Architecture (Enterprise Roadmap v3 Phase 0)
    'ComposedComponent',
    
    # Current components (enterprise-ready)
    'APIEndpoint',
    'Model',
    'Store',
    'V5EnhancedStore',
    'Accumulator',
    'Controller',
    'StreamProcessor',
    'FastAPIEndpoint',
    'MessageBusSource',
]