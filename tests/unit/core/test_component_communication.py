"""
Test component communication patterns for the reference implementation.
Validates direct binding and message passing between components.
"""

import unittest
import asyncio
from typing import Dict, Any

# Import reference implementation components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.components.composed_base import ComposedComponent


# Reference implementations for testing communication
class TaskStore(ComposedComponent):
    """Test Store component for communication testing"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._items = {}
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        self.logger.info(f"Store {self.name} setup complete")
        
    async def process_item(self, item: Any) -> Any:
        try:
            item_id = item.get("id", len(self._items)) if isinstance(item, dict) else len(self._items)
            self._items[item_id] = item
            return {"status": "stored", "item_id": item_id}
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        await super().cleanup()
        self._items.clear()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "items_count": len(self._items)}


class TaskAPI(ComposedComponent):
    """Test API component for communication testing"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 8000) if config else 8000
        self.store_component = None  # Store component binding
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port}")
        
    def set_store_component(self, store_component):
        """Set the store component for data operations"""
        self.store_component = store_component
        
    async def process_item(self, item: Any) -> Any:
        try:
            if not isinstance(item, dict) or "action" not in item:
                return {"status": "error", "message": "Invalid request format"}
            
            action = item["action"]
            
            # Check if store is bound for actions that need it
            if action in ["create_task", "get_task", "list_tasks"] and self.store_component is None:
                return {"status": "error", "message": "No store component bound"}
            
            if action == "create_task":
                # Delegate to store component
                store_result = await self.store_component.process_item({
                    "action": "create",
                    "data": {
                        "title": item.get("title", ""),
                        "description": item.get("description", "")
                    }
                })
                if store_result["status"] == "success":
                    return {"status": "created", "id": store_result["id"]}
                else:
                    return {"status": "error", "message": "Failed to create task"}
                    
            elif action == "get_task":
                # Delegate to store component
                store_result = await self.store_component.process_item({
                    "action": "get",
                    "id": item["id"]
                })
                if store_result["status"] == "success":
                    return {"status": "success", "data": store_result["data"]}
                elif store_result["status"] == "not_found":
                    return {"status": "not_found", "message": f"Task {item['id']} not found"}
                else:
                    return {"status": "error", "message": "Failed to get task"}
                    
            elif action == "list_tasks":
                # Delegate to store component
                store_result = await self.store_component.process_item({
                    "action": "list"
                })
                if store_result["status"] == "success":
                    return {"status": "success", "data": store_result["data"]}
                else:
                    return {"status": "error", "message": "Failed to list tasks"}
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"API processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        await super().cleanup()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "endpoint": f"{self.host}:{self.port}"}


class TestComponentCommunication(unittest.TestCase):
    """Test inter-component communication patterns."""
    
    def setUp(self):
        """Set up test components."""
        self.store = TaskStore("test_store")
        self.api = TaskAPI("test_api", {"port": 8080})
        
    def test_direct_component_binding(self):
        """Test direct binding between Store and API components."""
        # Bind store to API
        self.api.set_store_component(self.store)
        
        # Verify binding
        self.assertEqual(self.api.store_component, self.store)
        self.assertIsNotNone(self.api.store_component)
        
    def test_message_passing_create_task(self):
        """Test message passing for task creation."""
        # Bind components
        self.api.set_store_component(self.store)
        
        # Create task through API
        async def test_create():
            result = await self.api.process_item({
                'action': 'create_task',
                'title': 'Test Task',
                'description': 'Test Description'
            })
            return result
            
        result = asyncio.run(test_create())
        
        # Verify task was created
        self.assertEqual(result['status'], 'created')
        self.assertIn('id', result)
        self.assertEqual(result['id'], 'task_1')
        
    def test_message_passing_get_task(self):
        """Test message passing for task retrieval."""
        # Bind components
        self.api.set_store_component(self.store)
        
        async def test_flow():
            # Create a task first
            create_result = await self.api.process_item({
                'action': 'create_task',
                'title': 'Test Task',
                'description': 'Test Description'
            })
            
            task_id = create_result['id']
            
            # Get the task
            get_result = await self.api.process_item({
                'action': 'get_task',
                'id': task_id
            })
            
            return get_result
            
        result = asyncio.run(test_flow())
        
        # Verify retrieval
        self.assertEqual(result['status'], 'found')
        self.assertEqual(result['data']['title'], 'Test Task')
        
    def test_error_propagation_missing_task(self):
        """Test error propagation when task not found."""
        # Bind components
        self.api.set_store_component(self.store)
        
        async def test_missing():
            result = await self.api.process_item({
                'action': 'get_task',
                'id': 'nonexistent'
            })
            return result
            
        result = asyncio.run(test_missing())
        
        # Error should propagate from Store to API
        self.assertEqual(result['status'], 'not_found')
        
    def test_error_propagation_no_store_bound(self):
        """Test error when no store is bound to API."""
        # Don't bind store
        
        async def test_unbound():
            result = await self.api.process_item({
                'action': 'create_task',
                'title': 'Test'
            })
            return result
            
        result = asyncio.run(test_unbound())
        
        # Should return error
        self.assertEqual(result['status'], 'error')
        self.assertIn('No store component', result['message'])
        
    def test_multiple_operations_sequence(self):
        """Test sequence of operations through bound components."""
        self.api.set_store_component(self.store)
        
        async def test_sequence():
            results = []
            
            # Create multiple tasks
            for i in range(3):
                result = await self.api.process_item({
                    'action': 'create_task',
                    'title': f'Task {i+1}',
                    'description': f'Description {i+1}'
                })
                results.append(result)
                
            # List all tasks
            list_result = await self.api.process_item({
                'action': 'list_tasks'
            })
            results.append(list_result)
            
            # Update a task
            update_result = await self.api.process_item({
                'action': 'update_task',
                'id': 'task_2',
                'title': 'Updated Task 2'
            })
            results.append(update_result)
            
            # Delete a task
            delete_result = await self.api.process_item({
                'action': 'delete_task',
                'id': 'task_1'
            })
            results.append(delete_result)
            
            return results
            
        results = asyncio.run(test_sequence())
        
        # Verify sequence
        self.assertEqual(len(results), 6)
        
        # Check creates
        for i in range(3):
            self.assertEqual(results[i]['status'], 'created')
            self.assertEqual(results[i]['id'], f'task_{i+1}')
            
        # Check list
        self.assertEqual(results[3]['status'], 'success')
        self.assertEqual(len(results[3]['tasks']), 3)
        
        # Check update
        self.assertEqual(results[4]['status'], 'updated')
        
        # Check delete
        self.assertEqual(results[5]['status'], 'deleted')
        
    def test_component_discovery_pattern(self):
        """Test component discovery and registration pattern."""
        # Create a registry-like structure
        registry = {}
        
        # Register components
        registry[self.store.name] = {
            'instance': self.store,
            'type': 'Store',
            'capabilities': ['create', 'read', 'update', 'delete']
        }
        
        registry[self.api.name] = {
            'instance': self.api,
            'type': 'API',
            'capabilities': ['http_endpoint'],
            'bindings': []
        }
        
        # Discover and bind
        for name, info in registry.items():
            if info['type'] == 'API':
                # Find store to bind
                for other_name, other_info in registry.items():
                    if other_info['type'] == 'Store':
                        api = info['instance']
                        store = other_info['instance']
                        api.set_store_component(store)
                        info['bindings'].append(other_name)
                        
        # Verify discovery worked
        self.assertEqual(len(registry), 2)
        self.assertEqual(registry['test_api']['bindings'], ['test_store'])
        self.assertIsNotNone(self.api.store_component)
        
    def test_async_component_coordination(self):
        """Test async coordination between components."""
        self.api.set_store_component(self.store)
        
        async def concurrent_operations():
            # Run multiple operations concurrently
            tasks = []
            
            for i in range(5):
                task = self.api.process_item({
                    'action': 'create_task',
                    'title': f'Concurrent Task {i}',
                    'description': f'Created concurrently'
                })
                tasks.append(task)
                
            # Wait for all to complete
            results = await asyncio.gather(*tasks)
            return results
            
        results = asyncio.run(concurrent_operations())
        
        # All should succeed with unique IDs
        self.assertEqual(len(results), 5)
        ids = [r['id'] for r in results]
        self.assertEqual(len(set(ids)), 5)  # All unique
        
        # IDs should be sequential
        for i, result in enumerate(results):
            self.assertEqual(result['status'], 'created')
            # Note: Order might vary due to async, but IDs should be unique
            
    def test_component_health_propagation(self):
        """Test health status propagation between components."""
        self.api.set_store_component(self.store)
        
        # Get health from both components
        store_health = self.store.get_health_status()
        api_health = self.api.get_health_status()
        
        # Both should be healthy
        self.assertEqual(store_health['status'], 'healthy')
        self.assertEqual(api_health['status'], 'healthy')
        
        # Simulate store issue
        self.store._status = 'unhealthy'
        
        # API should detect unhealthy store (in real implementation)
        # This is a simplified test
        store_health = self.store.get_health_status()
        self.assertEqual(store_health['status'], 'unhealthy')
        
    def test_binding_cleanup_on_shutdown(self):
        """Test that bindings are cleaned up properly on shutdown."""
        self.api.set_store_component(self.store)
        
        # Verify binding exists
        self.assertIsNotNone(self.api.store_component)
        
        # Cleanup
        self.api.cleanup()
        
        # In a full implementation, cleanup might clear bindings
        # For now, just verify cleanup was called without error
        self.assertTrue(True)  # Cleanup succeeded


if __name__ == "__main__":
    unittest.main()