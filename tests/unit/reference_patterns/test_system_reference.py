"""
Test system-level orchestration with reference implementation patterns.
Validates component creation, binding, and lifecycle management.
"""

import unittest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Import reference implementations from component communication test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.components.composed_base import ComposedComponent


# Reference implementations for testing (from test_component_communication.py)
class TaskStore(ComposedComponent):
    """Test Store component for system testing"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._tasks = {}
        self._next_id = 1
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        self.logger.info(f"Store {self.name} setup complete")
        
    async def process_item(self, item: Any) -> Any:
        try:
            if item.get('action') == 'create_task':
                task_id = f"task_{self._next_id}"
                self._next_id += 1
                task_data = {
                    'id': task_id,
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'created_at': 'test_time'
                }
                self._tasks[task_id] = task_data
                return {'status': 'created', 'id': task_id}
            elif item.get('action') == 'get_task':
                task_id = item.get('id')
                if task_id in self._tasks:
                    return {'status': 'found', 'data': self._tasks[task_id]}
                else:
                    return {'status': 'not_found'}
            elif item.get('action') == 'list_tasks':
                return {'status': 'success', 'tasks': list(self._tasks.values())}
            elif item.get('action') == 'update_task':
                task_id = item.get('id')
                if task_id in self._tasks:
                    self._tasks[task_id]['title'] = item.get('title', self._tasks[task_id]['title'])
                    return {'status': 'updated'}
                else:
                    return {'status': 'not_found'}
            elif item.get('action') == 'delete_task':
                task_id = item.get('id')
                if task_id in self._tasks:
                    del self._tasks[task_id]
                    return {'status': 'deleted'}
                else:
                    return {'status': 'not_found'}
            else:
                return {'status': 'error', 'message': 'Unknown action'}
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {'status': 'error', 'message': str(e)}
            
    async def cleanup(self):
        await super().cleanup()
        self._tasks.clear()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "task_count": len(self._tasks)}


class TaskAPI(ComposedComponent):
    """Test API component for system testing"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 8000) if config else 8000
        self.store_component = None
        
    def set_store_component(self, store):
        self.store_component = store
        
    async def setup(self, harness_context=None):
        await super().setup(harness_context)
        self.logger.info(f"API {self.name} setup on {self.host}:{self.port}")
        
    async def process_item(self, item: Any) -> Any:
        try:
            if not self.store_component:
                return {'status': 'error', 'message': 'No store component bound'}
                
            # Forward requests to store component
            return await self.store_component.process_item(item)
        except Exception as e:
            self.logger.error(f"API processing error: {e}")
            return {'status': 'error', 'message': str(e)}
            
    async def cleanup(self):
        await super().cleanup()
        
    def get_health_status(self) -> Dict[str, Any]:
        base_health = super().get_health_status()
        return {**base_health, "status": "healthy", "endpoint": f"{self.host}:{self.port}"}


class TestSystemReference(unittest.TestCase):
    """Test system-level orchestration of reference components."""
    
    def test_component_creation(self):
        """Test creating components with correct initialization."""
        # Create Store component
        store = TaskStore("system_store", {"max_items": 1000})
        self.assertEqual(store.name, "system_store")
        self.assertEqual(store.config.get("max_items"), 1000)
        self.assertEqual(store._next_id, 1)
        self.assertEqual(len(store._tasks), 0)
        
        # Create API component
        api = TaskAPI("system_api", {"port": 9090})
        self.assertEqual(api.name, "system_api")
        self.assertEqual(api.port, 9090)
        self.assertIsNone(api.store_component)
        
    def test_binding_establishment(self):
        """Test establishing bindings between components."""
        store = TaskStore("store")
        api = TaskAPI("api", {"port": 8080})
        
        # Initially unbound
        self.assertIsNone(api.store_component)
        
        # Establish binding
        api.set_store_component(store)
        
        # Verify binding
        self.assertEqual(api.store_component, store)
        self.assertIsNotNone(api.store_component)
        
        # Test binding works
        async def test_binding():
            result = await api.process_item({
                'action': 'create_task',
                'title': 'Test binding'
            })
            return result
            
        result = asyncio.run(test_binding())
        self.assertEqual(result['status'], 'created')
        
    def test_graceful_shutdown(self):
        """Test graceful shutdown of system components."""
        # Track cleanup calls
        cleanup_log = []
        
        # Create components with tracked cleanup
        class TrackedStore(TaskStore):
            def cleanup(self):
                cleanup_log.append(f"cleanup_{self.name}")
                super().cleanup()
                
        class TrackedAPI(TaskAPI):
            def cleanup(self):
                cleanup_log.append(f"cleanup_{self.name}")
                super().cleanup()
                
        # Create system
        store = TrackedStore("store")
        api = TrackedAPI("api", {"port": 8080})
        api.set_store_component(store)
        
        # Add some data
        asyncio.run(api.process_item({
            'action': 'create_task',
            'title': 'Task 1'
        }))
        
        # Verify data exists
        self.assertEqual(len(store._tasks), 1)
        
        # Shutdown in correct order (API first, then Store)
        api.cleanup()
        store.cleanup()
        
        # Verify cleanup order
        self.assertEqual(cleanup_log, ["cleanup_api", "cleanup_store"])
        
        # Verify store was cleared
        self.assertEqual(len(store._tasks), 0)
        
    def test_health_monitoring(self):
        """Test health monitoring across system components."""
        store = TaskStore("store")
        api = TaskAPI("api", {"port": 8080})
        api.set_store_component(store)
        
        # Get initial health
        store_health = store.get_health_status()
        api_health = api.get_health_status()
        
        # Verify healthy status
        self.assertEqual(store_health['status'], 'healthy')
        self.assertEqual(api_health['status'], 'healthy')
        self.assertIn('component', store_health)
        self.assertIn('timestamp', store_health)
        
        # Simulate unhealthy state
        store._status = 'unhealthy'
        
        # Check health again
        store_health = store.get_health_status()
        self.assertEqual(store_health['status'], 'unhealthy')
        
        # API should still be healthy (independent health)
        api_health = api.get_health_status()
        self.assertEqual(api_health['status'], 'healthy')
        
    def test_full_system_lifecycle(self):
        """Test complete system lifecycle from startup to shutdown."""
        lifecycle_log = []
        
        class LifecycleStore(TaskStore):
            def setup(self):
                lifecycle_log.append(f"setup_{self.name}")
                super().setup()
                
            def cleanup(self):
                lifecycle_log.append(f"cleanup_{self.name}")
                super().cleanup()
                
        class LifecycleAPI(TaskAPI):
            def setup(self):
                lifecycle_log.append(f"setup_{self.name}")
                super().setup()
                
            def cleanup(self):
                lifecycle_log.append(f"cleanup_{self.name}")
                super().cleanup()
                
        # System initialization
        store = LifecycleStore("store")
        api = LifecycleAPI("api", {"port": 8080})
        
        # Startup sequence
        store.setup()
        api.setup()
        api.set_store_component(store)
        lifecycle_log.append("binding_established")
        
        # Verify startup order
        self.assertEqual(lifecycle_log[:3], [
            "setup_store",
            "setup_api",
            "binding_established"
        ])
        
        # Run operations
        async def run_operations():
            results = []
            
            # Create tasks
            for i in range(3):
                result = await api.process_item({
                    'action': 'create_task',
                    'title': f'Task {i+1}'
                })
                results.append(result)
                
            # List tasks
            list_result = await api.process_item({
                'action': 'list_tasks'
            })
            results.append(list_result)
            
            return results
            
        results = asyncio.run(run_operations())
        
        # Verify operations succeeded
        self.assertEqual(len(results), 4)
        for i in range(3):
            self.assertEqual(results[i]['status'], 'created')
        self.assertEqual(results[3]['status'], 'success')
        self.assertEqual(len(results[3]['tasks']), 3)
        
        # Shutdown sequence
        api.cleanup()
        store.cleanup()
        
        # Verify complete lifecycle
        self.assertEqual(lifecycle_log, [
            "setup_store",
            "setup_api",
            "binding_established",
            "cleanup_api",
            "cleanup_store"
        ])
        
    def test_concurrent_system_operations(self):
        """Test system behavior under concurrent operations."""
        store = TaskStore("store")
        api = TaskAPI("api", {"port": 8080})
        api.set_store_component(store)
        
        async def concurrent_test():
            # Create multiple tasks concurrently
            create_tasks = []
            for i in range(10):
                task = api.process_item({
                    'action': 'create_task',
                    'title': f'Concurrent {i}',
                    'description': f'Task {i}'
                })
                create_tasks.append(task)
                
            # Execute concurrently
            create_results = await asyncio.gather(*create_tasks)
            
            # Get all tasks
            list_result = await api.process_item({
                'action': 'list_tasks'
            })
            
            return create_results, list_result
            
        create_results, list_result = asyncio.run(concurrent_test())
        
        # Verify all tasks created
        self.assertEqual(len(create_results), 10)
        for result in create_results:
            self.assertEqual(result['status'], 'created')
            
        # Verify all tasks in store
        self.assertEqual(list_result['status'], 'success')
        self.assertEqual(len(list_result['tasks']), 10)
        
        # Verify unique IDs
        ids = [r['id'] for r in create_results]
        self.assertEqual(len(set(ids)), 10)  # All unique
        
    def test_error_recovery(self):
        """Test system error recovery mechanisms."""
        store = TaskStore("store")
        api = TaskAPI("api", {"port": 8080})
        api.set_store_component(store)
        
        async def test_errors():
            results = []
            
            # Try invalid action
            result = await api.process_item({
                'action': 'invalid_action'
            })
            results.append(result)
            
            # Try to get non-existent task
            result = await api.process_item({
                'action': 'get_task',
                'id': 'non_existent'
            })
            results.append(result)
            
            # Create valid task (recovery)
            result = await api.process_item({
                'action': 'create_task',
                'title': 'Recovery Task'
            })
            results.append(result)
            
            # Verify recovery worked
            result = await api.process_item({
                'action': 'get_task',
                'id': results[-1]['id']
            })
            results.append(result)
            
            return results
            
        results = asyncio.run(test_errors())
        
        # Verify error handling
        self.assertEqual(results[0]['status'], 'error')
        self.assertEqual(results[1]['status'], 'not_found')
        
        # Verify recovery
        self.assertEqual(results[2]['status'], 'created')
        self.assertEqual(results[3]['status'], 'found')
        
    def test_system_with_config(self):
        """Test system configuration propagation."""
        # Create config
        system_config = {
            'store': {
                'max_items': 100,
                'persistence': False
            },
            'api': {
                'port': 9090,
                'timeout': 30
            }
        }
        
        # Create components with config
        store = TaskStore("store", system_config['store'])
        api = TaskAPI("api", system_config['api'])
        
        # Verify config applied
        self.assertEqual(store.config['max_items'], 100)
        self.assertEqual(api.port, 9090)
        self.assertEqual(api.config['timeout'], 30)
        
    def test_multi_component_system(self):
        """Test system with multiple components of same type."""
        # Create multiple stores
        primary_store = TaskStore("primary_store")
        backup_store = TaskStore("backup_store")
        
        # Create API that can switch stores
        api = TaskAPI("api", {"port": 8080})
        
        # Use primary store
        api.set_store_component(primary_store)
        
        async def test_primary():
            result = await api.process_item({
                'action': 'create_task',
                'title': 'Primary Task'
            })
            return result
            
        result = asyncio.run(test_primary())
        self.assertEqual(result['status'], 'created')
        self.assertEqual(len(primary_store._tasks), 1)
        self.assertEqual(len(backup_store._tasks), 0)
        
        # Switch to backup store
        api.set_store_component(backup_store)
        
        async def test_backup():
            result = await api.process_item({
                'action': 'create_task',
                'title': 'Backup Task'
            })
            return result
            
        result = asyncio.run(test_backup())
        self.assertEqual(result['status'], 'created')
        self.assertEqual(len(primary_store._tasks), 1)
        self.assertEqual(len(backup_store._tasks), 1)


if __name__ == "__main__":
    unittest.main()