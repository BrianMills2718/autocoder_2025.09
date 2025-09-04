#!/usr/bin/env python3
"""
Test suite for the reference implementation.
These tests verify that our GOLDEN STANDARD actually works.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reference_implementation.components.task_store import TaskStore
from reference_implementation.components.task_api import TaskAPI
from reference_implementation.main import TodoSystem


@pytest.mark.asyncio
class TestTaskStore:
    """Test the TaskStore component"""
    
    async def test_store_initialization(self):
        """Test that store can be initialized"""
        config = {'storage_type': 'memory'}
        store = TaskStore('test_store', config)
        
        assert store.name == 'test_store'
        assert store.storage_type == 'memory'
        assert store.tasks == {}
        assert store._next_id == 1
    
    async def test_store_setup(self):
        """Test store setup method"""
        store = TaskStore('test_store', {'storage_type': 'memory'})
        await store.setup()
        
        assert store.running == True
        assert store.tasks == {}
        
        await store.cleanup()
    
    async def test_store_crud_operations(self):
        """Test CRUD operations"""
        store = TaskStore('test_store', {'storage_type': 'memory'})
        await store.setup()
        
        # Create
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Test Task', 'completed': False}
        })
        assert result['status'] == 'success'
        assert result['action'] == 'created'
        assert 'id' in result
        task_id = result['id']
        
        # Get
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert result['status'] == 'success'
        assert result['data']['data']['title'] == 'Test Task'
        
        # Update
        result = await store.process_item({
            'action': 'update',
            'id': task_id,
            'data': {'completed': True}
        })
        assert result['status'] == 'success'
        assert result['data']['data']['completed'] == True
        
        # List
        result = await store.process_item({
            'action': 'list'
        })
        assert result['status'] == 'success'
        assert len(result['data']) == 1
        
        # Delete
        result = await store.process_item({
            'action': 'delete',
            'id': task_id
        })
        assert result['status'] == 'success'
        
        # Verify deleted
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert result['status'] == 'not_found'
        
        await store.cleanup()
    
    async def test_store_health_status(self):
        """Test health status reporting"""
        store = TaskStore('test_store', {'storage_type': 'memory'})
        await store.setup()
        
        health = store.get_health_status()
        assert health['healthy'] == True
        assert health['task_count'] == 0
        assert health['storage_type'] == 'memory'
        
        await store.cleanup()


@pytest.mark.asyncio
class TestTaskAPI:
    """Test the TaskAPI component"""
    
    async def test_api_initialization(self):
        """Test that API can be initialized"""
        config = {'port': 8081, 'host': '127.0.0.1'}
        api = TaskAPI('test_api', config)
        
        assert api.name == 'test_api'
        assert api.port == 8081
        assert api.host == '127.0.0.1'
        assert api.store_component is None
    
    async def test_api_setup(self):
        """Test API setup method"""
        api = TaskAPI('test_api', {'port': 8081})
        
        # Create mock store
        mock_store = Mock()
        mock_store.name = 'mock_store'
        
        # Setup with context containing store
        await api.setup({
            'components': {
                'task_store': mock_store
            }
        })
        
        assert api.store_component == mock_store
        assert api.server is not None
        
        await api.cleanup()
    
    async def test_api_store_binding(self):
        """Test API can be bound to store"""
        api = TaskAPI('test_api', {'port': 8081})
        store = TaskStore('test_store', {'storage_type': 'memory'})
        
        api.set_store_component(store)
        assert api.store_component == store
        
        health = api.get_health_status()
        assert health['store_connected'] == True


@pytest.mark.asyncio
class TestTodoSystem:
    """Test the complete system orchestration"""
    
    async def test_system_initialization(self):
        """Test system can be initialized"""
        system = TodoSystem()
        
        assert system.config['system']['name'] == 'todo_system'
        assert 'task_store' in system.config['components']
        assert 'task_api' in system.config['components']
        assert len(system.components) == 0
    
    async def test_system_component_creation(self):
        """Test system creates components"""
        system = TodoSystem()
        await system.initialize()
        
        assert 'task_store' in system.components
        assert 'task_api' in system.components
        assert isinstance(system.components['task_store'], TaskStore)
        assert isinstance(system.components['task_api'], TaskAPI)
        
        # Check binding
        api = system.components['task_api']
        store = system.components['task_store']
        assert api.store_component == store
        
        await system.shutdown()
    
    async def test_system_lifecycle(self):
        """Test complete system lifecycle"""
        system = TodoSystem()
        
        # Initialize
        await system.initialize()
        assert system.running == True
        
        # Create a task to run the system briefly
        async def run_briefly():
            await asyncio.sleep(0.1)
            system.running = False
        
        run_task = asyncio.create_task(run_briefly())
        await system.run()
        await run_task
        
        # Shutdown
        await system.shutdown()
        assert system.running == False
    
    async def test_system_health_check(self):
        """Test system health checking"""
        system = TodoSystem()
        await system.initialize()
        
        # Check health
        await system.check_health()
        
        # Verify components are healthy
        for name, component in system.components.items():
            health = component.get_health_status()
            assert health['healthy'] == True
        
        await system.shutdown()


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete system"""
    
    async def test_end_to_end_data_flow(self):
        """Test data flows correctly through the system"""
        # Create components
        store = TaskStore('store', {'storage_type': 'memory'})
        api = TaskAPI('api', {'port': 8082})
        
        # Setup components
        await store.setup()
        api.set_store_component(store)
        await api.setup({'components': {'store': store}})
        
        # Test data flow through API to store
        # Simulate API creating a task
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Integration Test Task'}
        })
        
        assert result['status'] == 'success'
        task_id = result['id']
        
        # Verify task exists
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert result['status'] == 'success'
        assert result['data']['data']['title'] == 'Integration Test Task'
        
        # Cleanup
        await store.cleanup()
        await api.cleanup()
    
    async def test_component_communication(self):
        """Test components can communicate correctly"""
        system = TodoSystem()
        await system.initialize()
        
        # Get components
        store = system.components['task_store']
        api = system.components['task_api']
        
        # Verify API can talk to store
        assert api.store_component == store
        
        # Create task through store
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Communication Test'}
        })
        assert result['status'] == 'success'
        
        # Verify task exists
        result = await store.process_item({'action': 'list'})
        assert len(result['data']) == 1
        
        await system.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])