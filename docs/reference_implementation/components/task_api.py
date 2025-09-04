#!/usr/bin/env python3
"""
Reference implementation of an APIEndpoint component.
This is the GOLDEN STANDARD for API components.
"""
from typing import Dict, Any, Optional, List
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from autocoder_cc.components.composed_base import ComposedComponent


class TaskModel(BaseModel):
    """Data model for tasks"""
    title: str
    description: Optional[str] = None
    completed: bool = False


class TaskAPI(ComposedComponent):
    """
    Minimal API endpoint component that follows the actual expected interface.
    
    Key points:
    - Inherits from ComposedComponent
    - Implements setup(), process(), and cleanup() methods
    - Integrates with FastAPI for REST endpoints
    """
    
    def __init__(self, name: str = "task_api", config: Dict[str, Any] = None):
        """Initialize the API component"""
        # Call parent constructor
        super().__init__(name, config or {})
        
        # Create FastAPI app
        self.app = FastAPI(title="Task API", version="1.0.0")
        
        # Configuration
        self.port = self.config.get('port', 8080)
        self.host = self.config.get('host', '0.0.0.0')
        
        # Component references (will be set by harness)
        self.store_component = None
        
        # Server instance
        self.server = None
        self.server_task = None
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info(f"TaskAPI initialized on port {self.port}")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return self.get_health_status()
        
        @self.app.get("/tasks")
        async def get_tasks():
            """Get all tasks"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not available")
            
            result = await self.store_component.process_item({
                'action': 'list'
            })
            
            if result['status'] == 'success':
                return result.get('data', [])
            else:
                raise HTTPException(status_code=500, detail=result.get('message'))
        
        @self.app.post("/tasks")
        async def create_task(task: TaskModel):
            """Create a new task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not available")
            
            result = await self.store_component.process_item({
                'action': 'create',
                'data': task.dict()
            })
            
            if result['status'] == 'success':
                return result['data']
            else:
                raise HTTPException(status_code=500, detail=result.get('message'))
        
        @self.app.get("/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get a specific task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not available")
            
            result = await self.store_component.process_item({
                'action': 'get',
                'id': task_id
            })
            
            if result['status'] == 'success':
                return result['data']
            elif result['status'] == 'not_found':
                raise HTTPException(status_code=404, detail="Task not found")
            else:
                raise HTTPException(status_code=500, detail=result.get('message'))
        
        @self.app.put("/tasks/{task_id}")
        async def update_task(task_id: str, task: TaskModel):
            """Update a task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not available")
            
            result = await self.store_component.process_item({
                'action': 'update',
                'id': task_id,
                'data': task.dict()
            })
            
            if result['status'] == 'success':
                return result['data']
            elif result['status'] == 'not_found':
                raise HTTPException(status_code=404, detail="Task not found")
            else:
                raise HTTPException(status_code=500, detail=result.get('message'))
        
        @self.app.delete("/tasks/{task_id}")
        async def delete_task(task_id: str):
            """Delete a task"""
            if not self.store_component:
                raise HTTPException(status_code=503, detail="Store not available")
            
            result = await self.store_component.process_item({
                'action': 'delete',
                'id': task_id
            })
            
            if result['status'] == 'success':
                return {"message": "Task deleted", "data": result['data']}
            elif result['status'] == 'not_found':
                raise HTTPException(status_code=404, detail="Task not found")
            else:
                raise HTTPException(status_code=500, detail=result.get('message'))
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Setup the component. Called by the harness during initialization.
        
        Args:
            harness_context: Optional context from the harness, may contain component references
        """
        self.logger.info(f"Setting up TaskAPI with context: {harness_context}")
        
        # Get reference to store component from harness context
        if harness_context and 'components' in harness_context:
            components = harness_context['components']
            # Look for store component
            for comp_name, comp_instance in components.items():
                if 'store' in comp_name.lower() or isinstance(comp_instance, type(comp_instance)) and 'Store' in comp_instance.__class__.__name__:
                    self.store_component = comp_instance
                    self.logger.info(f"Connected to store component: {comp_name}")
                    break
        
        # Create server configuration
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False  # We use our own logging
        )
        
        # Create server
        self.server = uvicorn.Server(config)
        
        self.logger.info("TaskAPI setup complete")
    
    async def process(self) -> None:
        """
        Main processing loop. Starts the FastAPI server.
        """
        self.logger.info(f"Starting TaskAPI server on {self.host}:{self.port}")
        
        # Run the server in the background
        try:
            await self.server.serve()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            if self.error_handler:
                self.error_handler.handle(e, {"component": self.name})
    
    async def cleanup(self) -> None:
        """
        Cleanup the component. Stops the FastAPI server.
        """
        self.logger.info("TaskAPI cleanup started")
        
        if self.server:
            self.logger.info("Shutting down API server...")
            self.server.should_exit = True
            # Give server time to shutdown gracefully
            await asyncio.sleep(0.5)
        
        self.logger.info("TaskAPI cleanup complete")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Return health status of the component.
        """
        return {
            'healthy': self.server is not None,
            'port': self.port,
            'host': self.host,
            'store_connected': self.store_component is not None,
            'endpoints': [
                '/health',
                '/tasks (GET, POST)',
                '/tasks/{id} (GET, PUT, DELETE)'
            ]
        }
    
    def set_store_component(self, store):
        """
        Set reference to store component.
        Used for manual binding in simple setups.
        """
        self.store_component = store
        self.logger.info(f"Store component set: {store.name if hasattr(store, 'name') else store}")