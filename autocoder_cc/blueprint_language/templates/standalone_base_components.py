#!/usr/bin/env python3
"""
Standalone Base Component Classes
Provides the base classes needed for generated systems without requiring the autocoder framework.
"""
import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class Component(ABC):
    """
    Base component class for standalone generated systems.
    
    This replaces autocoder.components.Component to make generated systems
    deployable without requiring the autocoder framework.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"{self.__class__.__name__}.{self.name}")
        self.created_at = time.time()
        
        # Component state
        self.is_running = False
        self.error_count = 0
        self.last_error = None
        
        self.logger.info(f"Component {self.name} initialized")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        return {
            'status': 'healthy' if self.error_count == 0 else 'degraded',
            'component': self.name,
            'type': self.__class__.__name__,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'uptime': time.time() - self.created_at
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Async health check for FastAPI integration"""
        return self.get_health_status()
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors"""
        self.error_count += 1
        self.last_error = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(f"Error in {self.name}: {self.last_error}")


class APIEndpoint(Component):
    """
    Base class for API endpoint components.
    
    This replaces autocoder.components.APIEndpoint to make generated systems
    deployable without requiring the autocoder framework.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # API-specific configuration
        self.port = self.config.get('port')
        self.host = self.config.get('host', '0.0.0.0')
        
        # Request tracking
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        
        # FastAPI router will be created by subclasses
        self.router = None
        
        self.logger.info(f"APIEndpoint {self.name} initialized on {self.host}:{self.port}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get API endpoint metrics"""
        return {
            'component': self.name,
            'total_requests': self._total_requests,
            'successful_requests': self._successful_requests,
            'failed_requests': self._failed_requests,
            'success_rate': (self._successful_requests / max(self._total_requests, 1)) * 100,
            'port': self.port,
            'host': self.host
        }
    
    def increment_request_count(self, success: bool = True):
        """Track request statistics"""
        self._total_requests += 1
        if success:
            self._successful_requests += 1
        else:
            self._failed_requests += 1
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health status for API endpoints"""
        base_health = await super().health_check()
        api_health = {
            'port': self.port,
            'host': self.host,
            'total_requests': self._total_requests,
            'success_rate': (self._successful_requests / max(self._total_requests, 1)) * 100
        }
        base_health.update(api_health)
        return base_health


class DataStore(Component):
    """
    Base class for data store components.
    
    This replaces parts of autocoder framework for data storage functionality.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # Store configuration
        self.connection_string = self.config.get('connection_string')
        self.database_type = self.config.get('database_type', 'sqlite')
        
        # Store state
        self.is_connected = False
        self.store_operations = 0
        self.query_operations = 0
        
        self.logger.info(f"DataStore {self.name} initialized for {self.database_type}")
    
    def sync_store(self, data: Any, table_name: str = None) -> Dict[str, Any]:
        """Synchronous store operation"""
        try:
            self.store_operations += 1
            # Basic implementation - would be overridden by V5EnhancedStore
            result = {
                'status': 'stored',
                'table_name': table_name or f'{self.name}_data',
                'timestamp': time.time(),
                'data_size': len(str(data)) if data else 0
            }
            self.logger.info(f"Stored data to {result['table_name']}")
            return result
        except Exception as e:
            self.handle_error(e, "sync_store")
            return {'status': 'error', 'error': str(e)}
    
    def sync_query(self, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronous query operation"""
        try:
            self.query_operations += 1
            # Basic implementation - would be overridden by V5EnhancedStore
            result = {
                'status': 'queried',
                'query': query,
                'parameters': parameters,
                'timestamp': time.time(),
                'rows_returned': 0  # Would be actual count in real implementation
            }
            self.logger.info(f"Executed query: {query}")
            return result
        except Exception as e:
            self.handle_error(e, "sync_query")
            return {'status': 'error', 'error': str(e)}
    
    def get_sync_health_status(self) -> Dict[str, Any]:
        """Enhanced health status for data stores"""
        base_health = super().get_sync_health_status()
        store_health = {
            'database_type': self.database_type,
            'is_connected': self.is_connected,
            'store_operations': self.store_operations,
            'query_operations': self.query_operations
        }
        base_health.update(store_health)
        return base_health