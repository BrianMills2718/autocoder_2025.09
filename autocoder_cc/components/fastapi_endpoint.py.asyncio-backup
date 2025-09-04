#!/usr/bin/env python3
"""FastAPIEndpoint component base – provides FastAPI + uvicorn server startup for generated APIEndpoint components."""
from typing import Dict, Any, Optional
import anyio
import threading
import uvicorn
from fastapi import FastAPI
from .api_endpoint import APIEndpoint
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors

class FastAPIEndpoint(APIEndpoint):
    """Concrete APIEndpoint implementation that spins up a FastAPI application via uvicorn."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self.app: Optional[FastAPI] = None
        self._uvicorn_server: Optional[uvicorn.Server] = None
        self._server_thread: Optional[threading.Thread] = None
        
        # Add FastAPI-specific attributes from reference pattern
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 8000) if config else 8000
        self.server = None  # Server instance
        self.server_task = None  # Server task for async operations
        self.store_component = None  # Store component binding
        self.running = False  # Component lifecycle state
        
        # Setup consistent error handling (inherits from APIEndpoint which already has error_handler)
        # But we override with FastAPIEndpoint-specific handler
        self.error_handler = ConsistentErrorHandler(f"FastAPIEndpoint.{name}")

    @handle_errors(component_name="FastAPIEndpoint", operation="start_server")
    async def _start_server(self):
        if self.app is None:
            # Generate a working FastAPI app if not provided
            self.logger.info(f"Generated component {self.__class__.__name__} creating default FastAPI app")
            
            from fastapi import FastAPI, HTTPException
            
            self.app = FastAPI(
                title=f"{self.name} API",
                description="Generated FastAPI endpoint",
                version="1.0.0"
            )
            
            # Add health endpoint (from reference pattern)
            @self.app.get("/health")
            async def health_check():
                """Health check endpoint"""
                health = self.get_health_status()
                return {"status": "ok", "health": health}
            
            # Add task endpoints (from reference pattern)
            @self.app.get("/tasks")
            async def list_tasks():
                """List all tasks"""
                if not self.store_component:
                    raise HTTPException(status_code=503, detail="Store not connected")
                result = await self.store_component.process_item({"action": "list"})
                if result["status"] == "success":
                    return {"tasks": result["data"]}
                raise HTTPException(status_code=500, detail=result.get("message", "Internal error"))
            
            @self.app.post("/tasks")
            async def create_task(task_data: Dict[str, Any]):
                """Create a new task"""
                if not self.store_component:
                    raise HTTPException(status_code=503, detail="Store not connected")
                result = await self.store_component.process_item({"action": "create", "data": task_data})
                if result["status"] == "success":
                    return {"task": result["data"], "id": result["id"]}
                raise HTTPException(status_code=400, detail=result.get("message", "Creation failed"))
            
            @self.app.get("/tasks/{task_id}")
            async def get_task(task_id: str):
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
            async def update_task(task_id: str, task_data: Dict[str, Any]):
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
            async def delete_task(task_id: str):
                """Delete a specific task"""
                if not self.store_component:
                    raise HTTPException(status_code=503, detail="Store not connected")
                result = await self.store_component.process_item({"action": "delete", "id": task_id})
                if result["status"] == "success":
                    return {"message": "Task deleted successfully"}
                elif result["status"] == "not_found":
                    raise HTTPException(status_code=404, detail="Task not found")
                raise HTTPException(status_code=500, detail=result.get("message", "Internal error"))
            
            # Add legacy data endpoint for backward compatibility
            @self.app.post(f"/api/{self.name}")
            async def handle_data(data: dict):
                """Handle POST requests with comprehensive input validation"""
                try:
                    # Validate and sanitize input data
                    sanitized_data = self.validate_request_data(data)
                    return {
                        "received": sanitized_data, 
                        "component": self.name, 
                        "status": "processed",
                        "timestamp": __import__('time').time()
                    }
                except Exception as e:
                    await self.error_handler.handle_exception(
                        e,
                        context={"endpoint": f"/api/{self.name}", "input_data": str(data)[:200]},
                        operation="request_validation"
                    )
                    return {
                        "error": "Invalid input data", 
                        "component": self.name, 
                        "status": "error",
                        "details": str(e)
                    }
            
            self.logger.info(f"FastAPI app created for {self.name} with task endpoints and input validation")

        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        self._uvicorn_server = uvicorn.Server(config=config)

        def _run():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._uvicorn_server.serve())

        self._server_thread = threading.Thread(target=_run, daemon=True)
        self._server_thread.start()
        self.running = True
        self.server = self._uvicorn_server  # Store server reference for compatibility

        # Wait until server is started or timeout
        for _ in range(20):
            if self._uvicorn_server.started:
                break
            await anyio.sleep(0.1)
        
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port}")

    @handle_errors(component_name="FastAPIEndpoint", operation="stop_server")
    async def _stop_server(self):
        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True
        if self._server_thread is not None:
            self._server_thread.join(timeout=5)
        self.running = False
        self.server_task = None
        self.logger.info(f"API {self.name} cleanup complete")
    
    def set_store_component(self, store_component):
        """Set the store component for data operations (from reference pattern)"""
        self.store_component = store_component
        
    async def process_item(self, item: Any) -> Any:
        """Process API request (from reference pattern)"""
        try:
            # Mock API processing
            return {"status": 200, "body": {"success": True, "data": item}}
        except Exception as e:
            self.logger.error(f"API processing error: {e}")
            return {"status": 500, "body": {"error": "Internal Server Error", "message": str(e)}}
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status (from reference pattern)"""
        base_health = super().get_health_status() if hasattr(super(), 'get_health_status') else {}
        # Extract route paths for endpoints list
        endpoints = [route.path for route in self.app.routes if hasattr(route, 'path')] if self.app else []
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