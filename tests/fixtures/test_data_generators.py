"""
Test data generators for component testing.
Provides realistic test data for various component types.
"""

import random
import string
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid


class TestDataGenerator:
    """Generate test data for component testing."""
    
    @staticmethod
    def generate_task(
        title: str = None,
        description: str = None,
        status: str = None,
        priority: str = None
    ) -> Dict[str, Any]:
        """Generate a task object for Store testing."""
        return {
            'title': title or f"Task {random.randint(1, 1000)}",
            'description': description or f"Description for test task {uuid.uuid4().hex[:8]}",
            'status': status or random.choice(['pending', 'in_progress', 'completed']),
            'priority': priority or random.choice(['low', 'medium', 'high']),
            'created_at': datetime.now().isoformat(),
            'id': None  # Will be assigned by store
        }
    
    @staticmethod
    def generate_api_request(
        action: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate an API request for testing."""
        valid_actions = [
            'create_task', 'get_task', 'update_task', 
            'delete_task', 'list_tasks'
        ]
        
        action = action or random.choice(valid_actions)
        
        request = {'action': action}
        
        if action == 'create_task':
            request.update({
                'title': kwargs.get('title', f"API Task {random.randint(1, 100)}"),
                'description': kwargs.get('description', 'Created via API')
            })
        elif action == 'get_task':
            request['id'] = kwargs.get('id', f"task_{random.randint(1, 10)}")
        elif action == 'update_task':
            request['id'] = kwargs.get('id', f"task_{random.randint(1, 10)}")
            request['title'] = kwargs.get('title', 'Updated Title')
        elif action == 'delete_task':
            request['id'] = kwargs.get('id', f"task_{random.randint(1, 10)}")
            
        return request
    
    @staticmethod
    def generate_bulk_tasks(count: int = 10) -> List[Dict[str, Any]]:
        """Generate multiple tasks for bulk testing."""
        tasks = []
        for i in range(count):
            task = TestDataGenerator.generate_task(
                title=f"Bulk Task {i+1}",
                description=f"Part of bulk generation batch"
            )
            tasks.append(task)
        return tasks
    
    @staticmethod
    def generate_processing_item(
        data_type: str = None,
        size: str = 'medium'
    ) -> Dict[str, Any]:
        """Generate data for Processing component testing."""
        data_types = ['text', 'json', 'binary', 'structured']
        data_type = data_type or random.choice(data_types)
        
        sizes = {
            'small': 100,
            'medium': 1000,
            'large': 10000
        }
        
        if data_type == 'text':
            content = ''.join(random.choices(
                string.ascii_letters + string.digits + ' ',
                k=sizes.get(size, 1000)
            ))
        elif data_type == 'json':
            content = {
                'field1': random.randint(1, 100),
                'field2': ''.join(random.choices(string.ascii_letters, k=10)),
                'nested': {
                    'value': random.random()
                }
            }
        elif data_type == 'structured':
            content = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'metrics': [random.random() for _ in range(10)],
                'tags': [f"tag_{i}" for i in range(random.randint(1, 5))]
            }
        else:
            content = bytes(random.randint(0, 255) for _ in range(sizes.get(size, 1000)))
            
        return {
            'type': data_type,
            'content': content,
            'metadata': {
                'size': size,
                'generated_at': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def generate_config(
        component_type: str = 'Store'
    ) -> Dict[str, Any]:
        """Generate configuration for component initialization."""
        configs = {
            'Store': {
                'max_items': random.choice([100, 500, 1000]),
                'persistence': random.choice([True, False]),
                'cache_enabled': random.choice([True, False]),
                'cache_ttl': random.randint(60, 3600)
            },
            'API': {
                'port': random.choice([8080, 8081, 9090, 3000]),
                'timeout': random.randint(10, 60),
                'max_connections': random.choice([10, 50, 100]),
                'rate_limit': random.randint(10, 1000)
            },
            'Processing': {
                'batch_size': random.choice([10, 50, 100]),
                'parallel_workers': random.randint(1, 10),
                'timeout': random.randint(5, 30),
                'retry_count': random.randint(1, 5)
            },
            'Filter': {
                'criteria': random.choice(['include', 'exclude']),
                'patterns': [f"pattern_{i}" for i in range(random.randint(1, 5))],
                'case_sensitive': random.choice([True, False])
            },
            'Aggregator': {
                'window_size': random.choice([10, 60, 300]),
                'aggregation_type': random.choice(['sum', 'avg', 'min', 'max']),
                'flush_interval': random.randint(5, 60)
            }
        }
        
        return configs.get(component_type, {})
    
    @staticmethod
    def generate_message(
        source: str = None,
        destination: str = None,
        payload: Any = None
    ) -> Dict[str, Any]:
        """Generate inter-component message for communication testing."""
        return {
            'id': uuid.uuid4().hex,
            'source': source or f"component_{random.randint(1, 5)}",
            'destination': destination or f"component_{random.randint(6, 10)}",
            'timestamp': datetime.now().isoformat(),
            'payload': payload or {
                'action': random.choice(['process', 'store', 'retrieve']),
                'data': TestDataGenerator.generate_task()
            },
            'headers': {
                'content-type': 'application/json',
                'correlation-id': uuid.uuid4().hex
            }
        }
    
    @staticmethod
    def generate_error_scenario() -> Dict[str, Any]:
        """Generate error scenarios for testing error handling."""
        scenarios = [
            {
                'type': 'invalid_input',
                'data': None,
                'expected_error': 'Input cannot be None'
            },
            {
                'type': 'missing_required_field',
                'data': {'action': 'create_task'},  # Missing title
                'expected_error': 'Missing required field: title'
            },
            {
                'type': 'invalid_action',
                'data': {'action': 'unknown_action'},
                'expected_error': 'Unknown action: unknown_action'
            },
            {
                'type': 'resource_not_found',
                'data': {'action': 'get_task', 'id': 'non_existent'},
                'expected_error': 'Task not found'
            },
            {
                'type': 'validation_error',
                'data': {'action': 'create_task', 'title': ''},
                'expected_error': 'Title cannot be empty'
            }
        ]
        
        return random.choice(scenarios)
    
    @staticmethod
    def generate_performance_dataset(
        size: str = 'medium'
    ) -> List[Dict[str, Any]]:
        """Generate dataset for performance testing."""
        sizes = {
            'small': 100,
            'medium': 1000,
            'large': 10000,
            'xl': 100000
        }
        
        count = sizes.get(size, 1000)
        dataset = []
        
        for i in range(count):
            dataset.append({
                'id': i,
                'value': random.random() * 1000,
                'category': random.choice(['A', 'B', 'C', 'D']),
                'timestamp': (datetime.now() - timedelta(seconds=i)).isoformat()
            })
            
        return dataset
    
    @staticmethod
    def generate_blueprint_component(
        name: str = None,
        component_type: str = None
    ) -> Dict[str, Any]:
        """Generate blueprint component definition for testing."""
        types = ['Store', 'API', 'Processing', 'Filter', 'Aggregator']
        component_type = component_type or random.choice(types)
        
        component = {
            'name': name or f"Test{component_type}_{random.randint(1, 100)}",
            'type': component_type,
            'functions': []
        }
        
        # Add type-specific functions
        if component_type == 'Store':
            component['functions'] = [
                {
                    'name': 'store_item',
                    'inputs': ['item_data'],
                    'outputs': ['item_id'],
                    'business_logic': 'Store an item and return its ID'
                },
                {
                    'name': 'get_item',
                    'inputs': ['item_id'],
                    'outputs': ['item_data'],
                    'business_logic': 'Retrieve an item by ID'
                }
            ]
        elif component_type == 'API':
            component['functions'] = [
                {
                    'name': 'handle_request',
                    'inputs': ['request_data'],
                    'outputs': ['response_data'],
                    'business_logic': 'Process API request and return response'
                }
            ]
            component['bindings'] = [f"Store_{random.randint(1, 3)}"]
            
        return component
    
    @staticmethod
    def generate_health_status(
        status: str = None
    ) -> Dict[str, Any]:
        """Generate health status response for testing."""
        statuses = ['healthy', 'unhealthy', 'degraded']
        status = status or random.choice(statuses)
        
        health = {
            'status': status,
            'component': f"component_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'uptime': random.randint(0, 86400),
                'requests_processed': random.randint(0, 10000),
                'error_rate': random.random() * 0.1,
                'response_time_ms': random.randint(1, 1000)
            }
        }
        
        if status == 'unhealthy':
            health['error'] = 'Component experiencing issues'
            health['details'] = 'Connection timeout to backend service'
        elif status == 'degraded':
            health['warning'] = 'Performance degradation detected'
            health['details'] = 'High response times observed'
            
        return health


class MockDataStore:
    """Mock data store for testing."""
    
    def __init__(self):
        self.data = {}
        self.next_id = 1
        
    def store(self, item: Dict[str, Any]) -> str:
        """Store an item and return its ID."""
        item_id = f"item_{self.next_id}"
        self.next_id += 1
        self.data[item_id] = item
        return item_id
        
    def get(self, item_id: str) -> Dict[str, Any]:
        """Retrieve an item by ID."""
        return self.data.get(item_id)
        
    def update(self, item_id: str, item: Dict[str, Any]) -> bool:
        """Update an existing item."""
        if item_id in self.data:
            self.data[item_id] = item
            return True
        return False
        
    def delete(self, item_id: str) -> bool:
        """Delete an item."""
        if item_id in self.data:
            del self.data[item_id]
            return True
        return False
        
    def list_all(self) -> List[Dict[str, Any]]:
        """List all items."""
        return list(self.data.values())
        
    def clear(self):
        """Clear all data."""
        self.data.clear()
        self.next_id = 1


class ScenarioGenerator:
    """Generate complete test scenarios."""
    
    @staticmethod
    def generate_crud_scenario() -> List[Dict[str, Any]]:
        """Generate a complete CRUD operation scenario."""
        return [
            {
                'operation': 'create',
                'data': TestDataGenerator.generate_task(title="CRUD Test Task"),
                'expected': {'status': 'created'}
            },
            {
                'operation': 'read',
                'data': {'id': 'task_1'},
                'expected': {'status': 'found'}
            },
            {
                'operation': 'update',
                'data': {'id': 'task_1', 'title': 'Updated CRUD Task'},
                'expected': {'status': 'updated'}
            },
            {
                'operation': 'delete',
                'data': {'id': 'task_1'},
                'expected': {'status': 'deleted'}
            }
        ]
    
    @staticmethod
    def generate_load_test_scenario(
        operations: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate scenario for load testing."""
        scenario = []
        
        for i in range(operations):
            operation = random.choice(['create', 'read', 'update', 'delete'])
            
            if operation == 'create':
                scenario.append({
                    'operation': 'create',
                    'data': TestDataGenerator.generate_task(
                        title=f"Load Test Task {i}"
                    )
                })
            elif operation == 'read':
                scenario.append({
                    'operation': 'read',
                    'data': {'id': f"task_{random.randint(1, max(1, i))}"}
                })
            elif operation == 'update':
                scenario.append({
                    'operation': 'update',
                    'data': {
                        'id': f"task_{random.randint(1, max(1, i))}",
                        'title': f"Updated at {i}"
                    }
                })
            else:
                scenario.append({
                    'operation': 'delete',
                    'data': {'id': f"task_{random.randint(1, max(1, i))}"}
                })
                
        return scenario


if __name__ == "__main__":
    # Example usage
    print("Task:", TestDataGenerator.generate_task())
    print("API Request:", TestDataGenerator.generate_api_request())
    print("Config:", TestDataGenerator.generate_config('API'))
    print("Health:", TestDataGenerator.generate_health_status())