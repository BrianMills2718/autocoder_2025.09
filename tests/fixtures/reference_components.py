"""
Test fixtures based on the reference implementation.
These are known-good components we can use for testing.
"""
import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reference_implementation.components.task_store import TaskStore
from reference_implementation.components.task_api import TaskAPI


@pytest.fixture
async def reference_store():
    """Create a reference TaskStore for testing"""
    config = {"storage_type": "memory"}
    store = TaskStore("test_store", config)
    await store.setup()
    yield store
    await store.cleanup()


@pytest.fixture
async def reference_api():
    """Create a reference TaskAPI for testing"""
    config = {"port": 8082, "host": "127.0.0.1"}
    api = TaskAPI("test_api", config)
    await api.setup()
    yield api
    await api.cleanup()


@pytest.fixture
async def reference_store_with_data():
    """Create a TaskStore with some test data"""
    config = {"storage_type": "memory"}
    store = TaskStore("test_store", config)
    await store.setup()
    
    # Add some test data
    await store.process_item({
        'action': 'create',
        'data': {'title': 'Test Task 1', 'completed': False}
    })
    await store.process_item({
        'action': 'create',
        'data': {'title': 'Test Task 2', 'completed': True}
    })
    
    yield store
    await store.cleanup()


@pytest.fixture
def reference_store_config():
    """Standard configuration for a Store component"""
    return {
        "storage_type": "memory",
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db",
            "user": "test_user",
            "password": "test_pass"
        }
    }


@pytest.fixture
def reference_api_config():
    """Standard configuration for an API component"""
    return {
        "port": 8080,
        "host": "0.0.0.0",
        "endpoints": [
            {"path": "/tasks", "method": "GET"},
            {"path": "/tasks", "method": "POST"},
            {"path": "/tasks/{id}", "method": "GET"},
            {"path": "/tasks/{id}", "method": "PUT"},
            {"path": "/tasks/{id}", "method": "DELETE"},
            {"path": "/health", "method": "GET"}
        ]
    }


@pytest.fixture
def harness_context():
    """Standard harness context for component setup"""
    return {
        "components": {},
        "config": {
            "system": {
                "name": "test_system",
                "version": "1.0.0"
            }
        }
    }


class ReferenceComponentValidator:
    """Validator to check if a component matches reference implementation"""
    
    @staticmethod
    def validate_store_component(component):
        """Validate that a Store component matches reference implementation"""
        # Check base class
        from autocoder_cc.components.composed_base import ComposedComponent
        assert isinstance(component, ComposedComponent), \
            "Store must inherit from ComposedComponent"
        
        # Check required methods
        assert hasattr(component, 'setup')
        assert hasattr(component, 'process')
        assert hasattr(component, 'cleanup')
        assert hasattr(component, 'process_item')
        assert hasattr(component, 'get_health_status')
        
        # Check internal structure
        assert hasattr(component, 'tasks'), "Store must have 'tasks' attribute"
        assert hasattr(component, '_next_id'), "Store must have '_next_id' attribute"
        
        return True
    
    @staticmethod
    def validate_api_component(component):
        """Validate that an API component matches reference implementation"""
        from autocoder_cc.components.composed_base import ComposedComponent
        assert isinstance(component, ComposedComponent), \
            "API must inherit from ComposedComponent"
        
        # Check required methods
        assert hasattr(component, 'setup')
        assert hasattr(component, 'process')
        assert hasattr(component, 'cleanup')
        assert hasattr(component, 'get_health_status')
        
        # Check FastAPI integration
        assert hasattr(component, 'app'), "API must have FastAPI 'app' attribute"
        assert hasattr(component, 'port'), "API must have 'port' attribute"
        assert hasattr(component, 'host'), "API must have 'host' attribute"
        
        return True
    
    @staticmethod
    async def validate_store_behavior(store):
        """Validate that a Store behaves like reference implementation"""
        # Test CRUD operations
        
        # Create
        result = await store.process_item({
            'action': 'create',
            'data': {'title': 'Validation Test'}
        })
        assert result['status'] == 'success', "Create should succeed"
        assert 'id' in result, "Create should return ID"
        task_id = result['id']
        
        # Read
        result = await store.process_item({
            'action': 'get',
            'id': task_id
        })
        assert result['status'] == 'success', "Get should succeed"
        assert result['data']['data']['title'] == 'Validation Test'
        
        # Update
        result = await store.process_item({
            'action': 'update',
            'id': task_id,
            'data': {'title': 'Updated Test'}
        })
        assert result['status'] == 'success', "Update should succeed"
        
        # List
        result = await store.process_item({'action': 'list'})
        assert result['status'] == 'success', "List should succeed"
        assert len(result['data']) > 0, "Should have at least one task"
        
        # Delete
        result = await store.process_item({
            'action': 'delete',
            'id': task_id
        })
        assert result['status'] == 'success', "Delete should succeed"
        
        return True


# Export validator for use in tests
validator = ReferenceComponentValidator()