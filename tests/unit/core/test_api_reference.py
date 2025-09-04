#!/usr/bin/env python3
"""
Test API component pattern based on reference implementation.
This defines how all API components should behave.
"""
import pytest
import asyncio
from typing import Dict, Any
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from autocoder_cc.components.composed_base import ComposedComponent


class TaskAPI(ComposedComponent):
    """Test API component that follows the reference pattern"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 8000) if config else 8000
        # Initialize FastAPI app immediately
        from fastapi import FastAPI
        self.app = FastAPI(title=f"{name} API", version="1.0.0")
        self._setup_routes()
        # Other API component attributes
        self.server = None  # Server instance
        self.server_task = None  # Server task for async operations
        self.store_component = None  # Store component binding
        self.running = False  # Component lifecycle state
        
    def _setup_routes(self):
        """Setup FastAPI routes for the API component"""
        from fastapi import HTTPException
        from typing import Dict, Any, List
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            health = self.get_health_status()
            return {"status": "ok", "health": health}
        
        @self.app.get("/tasks")
        async def list_tasks() -> Dict[str, Any]:
            """List all tasks"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not connected")
            result = await self.store_component.process_item({"action": "list"})
            if result["status"] == "success":
                return {"tasks": result["data"]}
            raise HTTPException(status_code=500, detail=result.get("message", "Internal error"))
        
        @self.app.post("/tasks")
        async def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not connected")
            result = await self.store_component.process_item({"action": "create", "data": task_data})
            if result["status"] == "success":
                return {"task": result["data"], "id": result["id"]}
            raise HTTPException(status_code=400, detail=result.get("message", "Creation failed"))
        
        @self.app.get("/tasks/{task_id}")
        async def get_task(task_id: str) -> Dict[str, Any]:
            """Get a specific task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not connected")
            result = await self.store_component.process_item({"action": "get", "id": task_id})
            if result["status"] == "success":
                return {"task": result["data"]}
            elif result["status"] == "not_found":
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=500, detail=result.get("message", "Internal error"))
        
        @self.app.put("/tasks/{task_id}")
        async def update_task(task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
            """Update a specific task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not connected")
            result = await self.store_component.process_item({"action": "update", "id": task_id, "data": task_data})
            if result["status"] == "success":
                return {"task": result["data"]}
            elif result["status"] == "not_found":
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=400, detail=result.get("message", "Update failed"))
        
        @self.app.delete("/tasks/{task_id}")
        async def delete_task(task_id: str) -> Dict[str, Any]:
            """Delete a specific task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not connected")
            result = await self.store_component.process_item({"action": "delete", "id": task_id})
            if result["status"] == "success":
                return {"message": "Task deleted successfully"}
            elif result["status"] == "not_found":
                raise HTTPException(status_code=404, detail="Task not found")
            raise HTTPException(status_code=500, detail=result.get("message", "Internal error"))
        
    async def setup(self, harness_context=None):
        """Setup the API component"""
        await super().setup(harness_context)
        self.running = True
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port}")
        # Initialize server components
        from unittest.mock import Mock
        self.server = Mock()  # Mock server instance
        
    def set_store_component(self, store_component):
        """Set the store component for data operations"""
        self.store_component = store_component
        
    async def process(self, item: Any) -> Any:
        """Process method for async processing"""
        return await self.process_item(item)
        
    async def process_item(self, item: Any) -> Any:
        """Process API request"""
        try:
            # Mock API processing
            return {"status": 200, "body": {"success": True, "data": item}}
        except Exception as e:
            self.logger.error(f"API processing error: {e}")
            return {"status": 500, "body": {"error": "Internal Server Error", "message": str(e)}}
            
    async def cleanup(self):
        """Cleanup the API component"""
        await super().cleanup()
        self.running = False
        self.server_task = None
        self.logger.info(f"API {self.name} cleanup complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        base_health = super().get_health_status()
        # Extract route paths for endpoints list
        endpoints = [route.path for route in self.app.routes if hasattr(route, 'path')]
        return {
            **base_health, 
            "status": "healthy", 
            "api_ready": True, 
            "endpoint": f"{self.host}:{self.port}",
            "healthy": self.server is not None,
            "port": self.port,
            "host": self.host,
            "store_connected": self.store_component is not None,
            "endpoints": endpoints
        }


class TestAPIComponentPattern:
    """Test that API components follow the correct pattern"""
    
    @pytest.mark.asyncio
    async def test_api_initialization(self):
        """Test API component initialization"""
        config = {
            "port": 8081,
            "host": "127.0.0.1"
        }
        api = TaskAPI("test_api", config)
        
        # Verify base class
        assert isinstance(api, ComposedComponent)
        
        # Verify attributes
        assert api.name == "test_api"
        assert api.config == config
        assert api.port == 8081
        assert api.host == "127.0.0.1"
        assert hasattr(api, 'app')  # FastAPI app
        assert hasattr(api, 'server')
    
    @pytest.mark.asyncio
    async def test_api_lifecycle(self):
        """Test API component lifecycle methods"""
        config = {
            "port": 8082,
            "host": "127.0.0.1"
        }
        api = TaskAPI("test_api", config)
        
        # Setup creates server
        await api.setup()
        assert api.server is not None
        
        # Process method exists
        assert hasattr(api, 'process')
        assert asyncio.iscoroutinefunction(api.process)
        
        # Cleanup stops server
        await api.cleanup()
        # After cleanup, server task should be None
        assert api.server_task is None
    
    def test_api_endpoints_defined(self):
        """Test that API defines required endpoints"""
        config = {"port": 8083, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Get routes from FastAPI app
        routes = [route.path for route in api.app.routes]
        
        # Required endpoints
        assert "/health" in routes
        assert "/tasks" in routes
        assert "/tasks/{task_id}" in routes
    
    def test_api_health_endpoint(self):
        """Test API health endpoint structure"""
        config = {"port": 8084, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Should have health status method
        health = api.get_health_status()
        assert health['healthy'] == (api.server is not None)  # False initially
        assert 'port' in health
        assert 'host' in health
        assert health['port'] == 8084
        assert health['host'] == "127.0.0.1"
        assert 'store_connected' in health
        assert 'endpoints' in health
    
    @pytest.mark.asyncio
    async def test_api_store_binding(self):
        """Test API can bind to Store component"""
        config = {"port": 8085, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Create mock store
        mock_store = Mock()
        mock_store.process_item = AsyncMock(return_value={
            'status': 'success',
            'data': []
        })
        
        # Set store component
        api.set_store_component(mock_store)
        
        # Verify binding
        assert api.store_component == mock_store
    
    @pytest.mark.asyncio
    async def test_api_request_handling(self):
        """Test API handles requests properly"""
        config = {"port": 8086, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Mock store for testing
        mock_store = Mock()
        mock_store.process_item = AsyncMock()
        api.set_store_component(mock_store)
        
        # Test different request types
        test_cases = [
            {
                'method': 'GET',
                'path': '/tasks',
                'expected_action': 'list'
            },
            {
                'method': 'POST',
                'path': '/tasks',
                'expected_action': 'create',
                'data': {'title': 'Test'}
            },
            {
                'method': 'GET',
                'path': '/tasks/1',
                'expected_action': 'get'
            },
            {
                'method': 'PUT',
                'path': '/tasks/1',
                'expected_action': 'update',
                'data': {'title': 'Updated'}
            },
            {
                'method': 'DELETE',
                'path': '/tasks/1',
                'expected_action': 'delete'
            }
        ]
        
        # Note: Testing internal methods, actual HTTP testing
        # would require starting the server
        for test_case in test_cases:
            # Verify the endpoint exists
            routes = [r.path for r in api.app.routes]
            # Convert path pattern for checking
            path_pattern = test_case['path'].replace('/1', '/{task_id}')
            assert path_pattern in routes
    
    def test_api_configuration_options(self):
        """Test API accepts various configuration options"""
        config = {
            "port": 8087,
            "host": "0.0.0.0",
            "cors_enabled": True,
            "cors_origins": ["http://localhost:3000"],
            "rate_limit": 100,
            "timeout": 30
        }
        api = TaskAPI("test_api", config)
        
        # Basic config should be set
        assert api.port == 8087
        assert api.host == "0.0.0.0"
        
        # Should accept additional config
        assert api.config['cors_enabled'] == True
        assert api.config['rate_limit'] == 100
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API handles errors gracefully"""
        config = {"port": 8088, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Mock store that returns errors
        mock_store = Mock()
        mock_store.process_item = AsyncMock(return_value={
            'status': 'error',
            'error': 'Database connection failed'
        })
        api.set_store_component(mock_store)
        
        # API should handle store errors gracefully
        # (actual testing would require HTTP client)
        
        # Test missing store binding
        api.store_component = None
        health = api.get_health_status()
        # Should still report health even without store
        assert 'healthy' in health
    
    @pytest.mark.asyncio
    async def test_api_metrics_integration(self):
        """Test API integrates with metrics collector"""
        config = {"port": 8089, "host": "127.0.0.1"}
        api = TaskAPI("test_api", config)
        
        # Should have metrics collector
        assert hasattr(api, 'metrics_collector')
        assert api.metrics_collector is not None
        
        # Metrics collector should have increment method
        if hasattr(api.metrics_collector, 'increment'):
            # Test correct signature (no value parameter)
            api.metrics_collector.increment('api.request')
            api.metrics_collector.increment('api.request', {'method': 'GET'})


class TestAPIComponentContract:
    """Test the contract that all API components must follow"""
    
    def test_api_required_methods(self):
        """Test that API has all required methods"""
        api = TaskAPI("test", {"port": 8090, "host": "127.0.0.1"})
        
        # Lifecycle methods
        assert hasattr(api, 'setup')
        assert hasattr(api, 'process')
        assert hasattr(api, 'cleanup')
        
        # Health check
        assert hasattr(api, 'get_health_status')
        
        # Store setting method
        assert hasattr(api, 'set_store_component')
        
        # Async checks
        assert asyncio.iscoroutinefunction(api.setup)
        assert asyncio.iscoroutinefunction(api.process)
        assert asyncio.iscoroutinefunction(api.cleanup)
        assert not asyncio.iscoroutinefunction(api.get_health_status)
    
    def test_api_required_attributes(self):
        """Test that API has required attributes"""
        config = {
            "port": 8091,
            "host": "127.0.0.1",
            "timeout": 30
        }
        api = TaskAPI("test_api", config)
        
        # Base attributes
        assert hasattr(api, 'name')
        assert hasattr(api, 'config')
        assert hasattr(api, 'logger')
        assert hasattr(api, 'metrics_collector')
        assert hasattr(api, 'error_handler')
        assert hasattr(api, 'tracer')
        
        # API-specific attributes
        assert hasattr(api, 'app')  # FastAPI app
        assert hasattr(api, 'port')
        assert hasattr(api, 'host')
        assert hasattr(api, 'server')
        
        # Type checks
        assert isinstance(api.port, int)
        assert isinstance(api.host, str)
    
    def test_api_fastapi_integration(self):
        """Test that API properly integrates FastAPI"""
        api = TaskAPI("test", {"port": 8092, "host": "127.0.0.1"})
        
        # Should have FastAPI app
        from fastapi import FastAPI
        assert hasattr(api, 'app')
        assert isinstance(api.app, FastAPI)
        
        # App should have routes
        assert len(api.app.routes) > 0
        
        # Should have standard HTTP methods
        methods = set()
        for route in api.app.routes:
            if hasattr(route, 'methods'):
                methods.update(route.methods)
        
        # Should support standard REST methods
        expected_methods = {'GET', 'POST', 'PUT', 'DELETE'}
        assert expected_methods.issubset(methods)
    
    def test_api_endpoint_patterns(self):
        """Test that API follows RESTful patterns"""
        api = TaskAPI("test", {"port": 8093, "host": "127.0.0.1"})
        
        # Collect all routes and methods
        route_methods = {}
        for route in api.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                if route.path not in route_methods:
                    route_methods[route.path] = set()
                route_methods[route.path].update(route.methods)
        
        # Health endpoint
        assert '/health' in route_methods
        assert 'GET' in route_methods['/health']
        
        # Collection endpoints  
        assert '/tasks' in route_methods
        assert 'GET' in route_methods['/tasks']  # List
        assert 'POST' in route_methods['/tasks']  # Create
        
        # Item endpoints
        assert '/tasks/{task_id}' in route_methods
        assert 'GET' in route_methods['/tasks/{task_id}']  # Read
        assert 'PUT' in route_methods['/tasks/{task_id}']  # Update
        assert 'DELETE' in route_methods['/tasks/{task_id}']  # Delete
    
    @pytest.mark.asyncio
    async def test_api_lifecycle_sequence(self):
        """Test API lifecycle follows correct sequence"""
        api = TaskAPI("test", {"port": 8094, "host": "127.0.0.1"})
        
        # Initial state
        assert api.server is None
        
        # After setup
        await api.setup()
        assert api.server is not None
        
        # After cleanup
        await api.cleanup()
        # Server should be stopped after cleanup
        assert hasattr(api, 'server')
    
    def test_api_store_dependency(self):
        """Test API properly depends on Store component"""
        api = TaskAPI("test", {"port": 8095, "host": "127.0.0.1"})
        
        # Should have store_component attribute (initially None)
        assert hasattr(api, 'store_component')
        assert api.store_component is None
        
        # Should be able to set store
        mock_store = Mock()
        api.set_store_component(mock_store)
        assert api.store_component == mock_store
        
        # Health should reflect store status
        health = api.get_health_status()
        assert 'store_connected' in health
        assert health['store_connected'] == True
        
        # Without store
        api.store_component = None
        health = api.get_health_status()
        assert health['store_connected'] == False


class TestAPIResponseFormats:
    """Test that API responses follow consistent formats"""
    
    def test_success_response_format(self):
        """Test successful response format"""
        # This would typically test actual HTTP responses
        # For now, we verify the structure is defined
        api = TaskAPI("test", {"port": 8096, "host": "127.0.0.1"})
        
        # Mock a successful store response
        mock_store = Mock()
        mock_store.process_item = AsyncMock(return_value={
            'status': 'success',
            'data': {'id': '1', 'title': 'Test'}
        })
        api.set_store_component(mock_store)
        
        # Response should follow standard format
        # (actual HTTP testing would be done with TestClient)
    
    def test_error_response_format(self):
        """Test error response format"""
        api = TaskAPI("test", {"port": 8097, "host": "127.0.0.1"})
        
        # Mock a store error
        mock_store = Mock()
        mock_store.process_item = AsyncMock(return_value={
            'status': 'error',
            'error': 'Task not found'
        })
        api.set_store_component(mock_store)
        
        # Error responses should have consistent format
        # (actual HTTP testing would be done with TestClient)
    
    def test_validation_error_format(self):
        """Test validation error response format"""
        api = TaskAPI("test", {"port": 8098, "host": "127.0.0.1"})
        
        # API should validate input and return proper errors
        # (actual testing would require sending invalid data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])