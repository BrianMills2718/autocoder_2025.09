"""
Known-good component implementations for deterministic testing.
These components are hand-crafted and verified to be correct.
"""

KNOWN_GOOD_STORE = '''#!/usr/bin/env python3
"""
Generated Store component for task_store
"""
from typing import Dict, Any, Optional
import asyncio
import json
from pathlib import Path
from autocoder_cc.components.composed_base import ComposedComponent


class GeneratedStore_task_store(ComposedComponent):
    """Task storage component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tasks = {}
        self.next_id = 1
        
    async def setup(self) -> None:
        """Initialize the store"""
        self.logger.info(f"TaskStore initialized with config: {self.config}")
        # Initialize in-memory storage
        self.tasks = {}
        self.next_id = 1
        
    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Store or retrieve tasks"""
        try:
            action = item.get('action', 'get')
            
            if action == 'create':
                task_data = item.get('data', {})
                task_id = str(self.next_id)
                self.next_id += 1
                self.tasks[task_id] = {
                    'id': task_id,
                    'data': task_data,
                    'created_at': item.get('timestamp', 'now')
                }
                return {
                    'status': 'success',
                    'action': 'created',
                    'id': task_id,
                    'data': self.tasks[task_id]
                }
                
            elif action == 'get':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    return {
                        'status': 'success',
                        'action': 'retrieved',
                        'data': self.tasks[task_id]
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'get',
                        'id': task_id
                    }
                    
            elif action == 'update':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    task_data = item.get('data', {})
                    self.tasks[task_id]['data'].update(task_data)
                    return {
                        'status': 'success',
                        'action': 'updated',
                        'id': task_id,
                        'data': self.tasks[task_id]
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'update',
                        'id': task_id
                    }
                    
            elif action == 'delete':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    deleted = self.tasks.pop(task_id)
                    return {
                        'status': 'success',
                        'action': 'deleted',
                        'id': task_id,
                        'data': deleted
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'delete',
                        'id': task_id
                    }
                    
            elif action == 'list':
                return {
                    'status': 'success',
                    'action': 'list',
                    'data': list(self.tasks.values())
                }
                
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing item: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def teardown(self) -> None:
        """Cleanup"""
        self.tasks.clear()
        self.logger.info("TaskStore shutdown complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            'healthy': True,
            'task_count': len(self.tasks),
            'next_id': self.next_id
        }
'''

KNOWN_GOOD_API_ENDPOINT = '''#!/usr/bin/env python3
"""
Generated APIEndpoint component for task_api
"""
from typing import Dict, Any, Optional
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from autocoder_cc.components.composed_base import ComposedComponent


class TaskModel(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class GeneratedAPIEndpoint_task_api(ComposedComponent):
    """Task API endpoint component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app = FastAPI(title="Task API")
        self.port = config.get('port', 8080)
        self.store_component = None
        
    async def setup(self) -> None:
        """Initialize the API endpoint"""
        self.logger.info(f"Task API initialized on port {self.port}")
        
        # Setup routes
        @self.app.get("/tasks")
        async def get_tasks():
            """Get all tasks"""
            if self.store_component:
                result = await self.store_component.process_item({
                    'action': 'list'
                })
                return result.get('data', [])
            return []
        
        @self.app.post("/tasks")
        async def create_task(task: TaskModel):
            """Create a new task"""
            if self.store_component:
                result = await self.store_component.process_item({
                    'action': 'create',
                    'data': task.dict()
                })
                if result['status'] == 'success':
                    return result['data']
                else:
                    raise HTTPException(status_code=500, detail=result.get('message'))
            raise HTTPException(status_code=503, detail="Store not available")
        
        @self.app.get("/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get a specific task"""
            if self.store_component:
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
            raise HTTPException(status_code=503, detail="Store not available")
        
        @self.app.put("/tasks/{task_id}")
        async def update_task(task_id: str, task: TaskModel):
            """Update a task"""
            if self.store_component:
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
            raise HTTPException(status_code=503, detail="Store not available")
        
        @self.app.delete("/tasks/{task_id}")
        async def delete_task(task_id: str):
            """Delete a task"""
            if self.store_component:
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
            raise HTTPException(status_code=503, detail="Store not available")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return self.get_health_status()
    
    def set_store_component(self, store):
        """Set reference to store component"""
        self.store_component = store
        
    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process API requests - mainly for internal communication"""
        # This is used when other components need to interact with the API
        action = item.get('action', 'status')
        
        if action == 'status':
            return {'status': 'running', 'port': self.port}
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
    
    async def teardown(self) -> None:
        """Cleanup"""
        self.logger.info("Task API shutdown complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            'healthy': True,
            'port': self.port,
            'store_connected': self.store_component is not None
        }
'''

KNOWN_GOOD_MAIN = '''#!/usr/bin/env python3
"""
Generated main.py for test_todo_system
"""
import asyncio
import logging
from pathlib import Path
import sys
import yaml

# Add components directory to path
sys.path.insert(0, str(Path(__file__).parent))

from components.task_store import GeneratedStore_task_store
from components.task_api import GeneratedAPIEndpoint_task_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TodoSystem:
    """Main system orchestrator"""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.components = {}
        
    def load_config(self, config_path: str = None) -> dict:
        """Load system configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                'system': {
                    'name': 'test_todo_system',
                    'version': '1.0.0'
                },
                'components': {
                    'task_store': {
                        'type': 'Store',
                        'config': {
                            'database_type': 'memory'
                        }
                    },
                    'task_api': {
                        'type': 'APIEndpoint',
                        'config': {
                            'port': 8080
                        }
                    }
                }
            }
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Todo System...")
        
        # Create store component
        store_config = self.config['components']['task_store']['config']
        self.components['task_store'] = GeneratedStore_task_store(store_config)
        await self.components['task_store'].setup()
        
        # Create API component
        api_config = self.config['components']['task_api']['config']
        self.components['task_api'] = GeneratedAPIEndpoint_task_api(api_config)
        
        # Connect components (binding)
        self.components['task_api'].set_store_component(self.components['task_store'])
        
        await self.components['task_api'].setup()
        
        logger.info("Todo System initialized successfully")
    
    async def run(self):
        """Run the system"""
        logger.info("Todo System running...")
        
        try:
            # Keep system running
            while True:
                await asyncio.sleep(1)
                
                # Check component health
                for name, component in self.components.items():
                    health = component.get_health_status()
                    if not health.get('healthy', False):
                        logger.warning(f"Component {name} is unhealthy: {health}")
                        
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down Todo System...")
        
        for name, component in self.components.items():
            logger.info(f"Shutting down {name}...")
            await component.teardown()
            
        logger.info("Todo System shutdown complete")


async def main():
    """Main entry point"""
    system = TodoSystem()
    await system.initialize()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
'''

# Component metadata for validation
COMPONENT_METADATA = {
    'task_store': {
        'type': 'Store',
        'class_name': 'GeneratedStore_task_store',
        'file_name': 'task_store.py',
        'imports': [
            'from typing import Dict, Any, Optional',
            'import asyncio',
            'import json',
            'from pathlib import Path',
            'from autocoder_cc.components.composed_base import ComposedComponent'
        ],
        'methods': ['setup', 'process_item', 'teardown', 'get_health_status']
    },
    'task_api': {
        'type': 'APIEndpoint',
        'class_name': 'GeneratedAPIEndpoint_task_api',
        'file_name': 'task_api.py',
        'imports': [
            'from typing import Dict, Any, Optional',
            'import asyncio',
            'from fastapi import FastAPI, HTTPException, Request',
            'from pydantic import BaseModel',
            'from autocoder_cc.components.composed_base import ComposedComponent'
        ],
        'methods': ['setup', 'process_item', 'teardown', 'get_health_status', 'set_store_component']
    }
}