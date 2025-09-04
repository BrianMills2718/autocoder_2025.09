#!/usr/bin/env python3
"""
Test Store component pattern based on reference implementation.
This defines how all Store components should behave.
"""
import pytest
import asyncio
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from autocoder_cc.components.composed_base import ComposedComponent


class TaskStore(ComposedComponent):
    """Test Store component that follows the reference pattern"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.storage_type = config.get("storage_type", "memory") if config else "memory"
        self._items = {}
        self.tasks = {}  # Task storage for TaskStore functionality
        self._next_id = 1  # Next ID for task/item generation
        self.running = False  # Component lifecycle state
        
    async def setup(self, harness_context=None):
        """Setup the Store component"""
        await super().setup(harness_context)
        self.running = True
        self.logger.info(f"Store {self.name} setup with {self.storage_type} storage")
        
    async def process_item(self, item: Any) -> Any:
        """Process CRUD operations on tasks"""
        try:
            if not isinstance(item, dict) or "action" not in item:
                return {"status": "error", "message": "Invalid request format"}
            
            action = item["action"]
            
            if action == "create":
                task_id = str(self._next_id)
                task_data = {
                    "id": task_id,
                    "data": item["data"]
                }
                self.tasks[task_id] = task_data
                self._next_id += 1
                return {"status": "success", "id": task_id, "data": task_data}
            
            elif action == "get":
                task_id = item["id"]
                if task_id in self.tasks:
                    return {"status": "success", "data": self.tasks[task_id]}
                else:
                    return {"status": "not_found", "action": "get", "id": task_id}
            
            elif action == "update":
                task_id = item["id"]
                if task_id in self.tasks:
                    # Update task data while preserving id
                    updated_data = {**self.tasks[task_id]["data"], **item["data"]}
                    self.tasks[task_id]["data"] = updated_data
                    return {"status": "success", "data": self.tasks[task_id]}
                else:
                    return {"status": "not_found", "action": "update", "id": task_id}
            
            elif action == "delete":
                task_id = item["id"]
                if task_id in self.tasks:
                    del self.tasks[task_id]
                    return {"status": "success"}
                else:
                    return {"status": "not_found", "action": "delete", "id": task_id}
            
            elif action == "list":
                task_list = list(self.tasks.values())
                return {"status": "success", "data": task_list}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self):
        """Cleanup the Store component"""
        await super().cleanup()
        self.running = False
        self._items.clear()
        self.tasks.clear()
        self.logger.info(f"Store {self.name} cleanup complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        base_health = super().get_health_status()
        return {
            **base_health, 
            "status": "healthy", 
            "items_count": len(self._items), 
            "storage_type": self.storage_type,
            "healthy": True,
            "task_count": len(self.tasks),
            "next_id": self._next_id
        }
    
    def get(self, item_id):
        """Get an item by ID"""
        return self._items.get(item_id)
    
    def list_items(self):
        """List all stored items"""
        return list(self._items.values())
    
    def count(self):
        """Get count of stored items"""
        return len(self._items)


class TestStoreComponentPattern:
    """Test that Store components follow the correct pattern"""
    
    @pytest.mark.asyncio
    async def test_store_initialization(self):
        """Test Store component initialization"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        
        # Verify base class
        assert isinstance(store, ComposedComponent)
        
        # Verify attributes
        assert store.name == "test_store"
        assert store.config == config
        assert hasattr(store, 'tasks')
        assert hasattr(store, '_next_id')
        assert store._next_id == 1
    
    @pytest.mark.asyncio
    async def test_store_lifecycle(self):
        """Test Store component lifecycle methods"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        
        # Setup
        await store.setup()
        assert store.running == True
        assert store.tasks == {}
        
        # Process (main loop would be running)
        # Not testing the actual loop, just that method exists
        assert hasattr(store, 'process')
        assert asyncio.iscoroutinefunction(store.process)
        
        # Cleanup
        await store.cleanup()
        assert store.running == False
    
    @pytest.mark.asyncio
    async def test_store_crud_operations(self):
        """Test Store CRUD operations"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # CREATE
        result = await store.process_item({
            'action': 'create',
            'data': {
                'title': 'Test Task',
                'description': 'A test task',
                'completed': False
            }
        })
        assert result['status'] == 'success'
        assert 'id' in result
        task_id = result['id']
        assert task_id == "1"
        
        # READ (single)
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert result['status'] == 'success'
        assert result['data']['data']['title'] == 'Test Task'
        
        # UPDATE
        result = await store.process_item({
            'action': 'update',
            'id': task_id,
            'data': {
                'title': 'Updated Task',
                'completed': True
            }
        })
        assert result['status'] == 'success'
        assert result['data']['data']['title'] == 'Updated Task'
        assert result['data']['data']['completed'] == True
        
        # LIST (all)
        result = await store.process_item({
            'action': 'list'
        })
        assert result['status'] == 'success'
        assert len(result['data']) == 1
        assert result['data'][0]['id'] == task_id
        
        # DELETE
        result = await store.process_item({
            'action': 'delete',
            'id': task_id
        })
        assert result['status'] == 'success'
        
        # Verify deletion
        result = await store.process_item({
            'action': 'list'
        })
        assert result['status'] == 'success'
        assert len(result['data']) == 0
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_error_handling(self):
        """Test Store error handling"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # Get non-existent task
        result = await store.process_item({
            'action': 'get',
            'id': '999'
        })
        assert result['status'] == 'not_found'
        assert result['action'] == 'get'
        assert result['id'] == '999'
        
        # Update non-existent task
        result = await store.process_item({
            'action': 'update',
            'id': '999',
            'data': {'title': 'Should Fail'}
        })
        assert result['status'] == 'not_found'
        assert result['action'] == 'update'
        assert result['id'] == '999'
        
        # Delete non-existent task
        result = await store.process_item({
            'action': 'delete',
            'id': '999'
        })
        assert result['status'] == 'not_found'
        assert result['action'] == 'delete'
        assert result['id'] == '999'
        
        # Invalid action
        result = await store.process_item({
            'action': 'invalid_action'
        })
        assert result['status'] == 'error'
        assert 'unknown action' in result['message'].lower()
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_id_generation(self):
        """Test Store ID generation is sequential"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        ids = []
        for i in range(5):
            result = await store.process_item({
                'action': 'create',
                'data': {'title': f'Task {i}'}
            })
            ids.append(result['id'])
        
        # Verify sequential IDs
        assert ids == ["1", "2", "3", "4", "5"]
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_health_status(self):
        """Test Store health status reporting"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # Check health status
        health = store.get_health_status()
        assert health['healthy'] == True
        assert 'task_count' in health
        assert health['task_count'] == 0
        assert health['next_id'] == 1
        assert health['storage_type'] == 'memory'
        
        # Add some tasks
        for i in range(3):
            await store.process_item({
                'action': 'create',
                'data': {'title': f'Task {i}'}
            })
        
        # Check health again
        health = store.get_health_status()
        assert health['task_count'] == 3
        assert health['next_id'] == 4  # Next ID after creating 3 tasks
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_data_persistence(self):
        """Test that Store maintains data across operations"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            result = await store.process_item({
                'action': 'create',
                'data': {
                    'title': f'Task {i}',
                    'priority': i
                }
            })
            task_ids.append(result['id'])
        
        # Verify all tasks exist
        result = await store.process_item({'action': 'list'})
        assert len(result['data']) == 3
        
        # Update one task
        await store.process_item({
            'action': 'update',
            'id': task_ids[1],
            'data': {'title': 'Modified Task'}
        })
        
        # Verify update didn't affect others
        result = await store.process_item({'action': 'list'})
        assert len(result['data']) == 3
        titles = [task['data']['title'] for task in result['data']]
        assert 'Task 0' in titles
        assert 'Modified Task' in titles
        assert 'Task 2' in titles
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_empty_operations(self):
        """Test Store operations on empty store"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # List empty store
        result = await store.process_item({'action': 'list'})
        assert result['status'] == 'success'
        assert result['data'] == []
        
        # Health check on empty store
        health = store.get_health_status()
        assert health['healthy'] == True
        assert health['task_count'] == 0
        
        await store.cleanup()
    
    @pytest.mark.asyncio 
    async def test_store_data_integrity(self):
        """Test Store maintains data integrity"""
        config = {"storage_type": "memory"}
        store = TaskStore("test_store", config)
        await store.setup()
        
        # Create task with all fields
        original_data = {
            'title': 'Complete Task',
            'description': 'This is a complete task',
            'completed': False,
            'priority': 'high',
            'tags': ['test', 'important']
        }
        
        result = await store.process_item({
            'action': 'create',
            'data': original_data
        })
        task_id = result['id']
        
        # Retrieve and verify all fields preserved
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        
        stored_data = result['data']['data']
        for key, value in original_data.items():
            assert stored_data[key] == value, f"Field {key} not preserved"
        
        # Partial update should preserve other fields
        await store.process_item({
            'action': 'update',
            'id': task_id,
            'data': {'completed': True}
        })
        
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        
        updated_data = result['data']['data']
        assert updated_data['completed'] == True
        assert updated_data['title'] == original_data['title']
        assert updated_data['description'] == original_data['description']
        assert updated_data['priority'] == original_data['priority']
        assert updated_data['tags'] == original_data['tags']
        
        await store.cleanup()


class TestStoreComponentContract:
    """Test the contract that all Store components must follow"""
    
    def test_store_required_methods(self):
        """Test that Store has all required methods"""
        store = TaskStore("test", {})
        
        # Lifecycle methods
        assert hasattr(store, 'setup')
        assert hasattr(store, 'process')
        assert hasattr(store, 'cleanup')
        
        # Data operation method
        assert hasattr(store, 'process_item')
        
        # Health check
        assert hasattr(store, 'get_health_status')
        
        # All should be async except get_health_status
        assert asyncio.iscoroutinefunction(store.setup)
        assert asyncio.iscoroutinefunction(store.process)
        assert asyncio.iscoroutinefunction(store.cleanup)
        assert asyncio.iscoroutinefunction(store.process_item)
        assert not asyncio.iscoroutinefunction(store.get_health_status)
    
    def test_store_required_attributes(self):
        """Test that Store has required attributes"""
        config = {"storage_type": "memory", "db_path": "/tmp/test.db"}
        store = TaskStore("test_store", config)
        
        # Base attributes
        assert hasattr(store, 'name')
        assert hasattr(store, 'config')
        assert hasattr(store, 'logger')
        assert hasattr(store, 'metrics_collector')
        assert hasattr(store, 'error_handler')
        assert hasattr(store, 'tracer')
        
        # Store-specific attributes
        assert hasattr(store, 'tasks')
        assert hasattr(store, '_next_id')
        
        # Type checks
        assert isinstance(store.tasks, dict)
        assert isinstance(store._next_id, int)
    
    @pytest.mark.asyncio
    async def test_store_action_contract(self):
        """Test that Store handles all required actions"""
        store = TaskStore("test", {})
        await store.setup()
        
        required_actions = ['create', 'get', 'update', 'delete', 'list']
        
        for action in required_actions:
            # Build appropriate request
            request = {'action': action}
            if action in ['get', 'update', 'delete']:
                request['id'] = '1'
            if action in ['create', 'update']:
                request['data'] = {'title': 'Test'}
            
            # Should not raise exception (might return error status)
            result = await store.process_item(request)
            assert 'status' in result
            assert result['status'] in ['success', 'error']
        
        await store.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_response_format(self):
        """Test that Store responses follow consistent format"""
        store = TaskStore("test", {})
        await store.setup()
        
        # Success response format
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Test'}
        })
        assert 'status' in result
        assert result['status'] == 'success'
        assert 'id' in result or 'data' in result
        
        # Not found response format
        result = await store.process_item({
            'action': 'get',
            'id': '999'
        })
        assert 'status' in result
        assert result['status'] == 'not_found'
        assert 'action' in result
        assert 'id' in result
        
        # Error response format (invalid action)
        result = await store.process_item({
            'action': 'invalid'
        })
        assert 'status' in result
        assert result['status'] == 'error'
        assert 'message' in result
        
        await store.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])