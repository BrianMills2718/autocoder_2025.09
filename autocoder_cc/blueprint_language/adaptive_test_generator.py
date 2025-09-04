"""Adaptive test data generation based on component analysis"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from .component_introspector import ComponentIntrospector

class AdaptiveTestDataGenerator:
    """Generates test data based on component introspection"""
    
    def __init__(self):
        self.introspector = ComponentIntrospector()
        
        # Default values by field name patterns
        self.field_defaults = {
            'id': lambda: 'test-id-123',
            'task_id': lambda: 'task-456',
            'user_id': lambda: 'user-789',
            'title': lambda: 'Test Title',
            'name': lambda: 'Test Name',
            'description': lambda: 'Test Description',
            'action': lambda: 'create',
            'data': lambda: {'test': 'data'},
            'value': lambda: 42,
            'message': lambda: 'Test message',
            'status': lambda: 'active',
            'type': lambda: 'test_type'
        }
    
    def generate_test_data(self, component_file: Path, 
                          num_cases: int = 3) -> List[Dict[str, Any]]:
        """
        Generate test data based on component analysis.
        
        CRITICAL FIX: Ensure proper routing to specialized generators
        """
        # Analyze component
        analysis = self.introspector.analyze_component(component_file)
        
        # FIXED: Better type detection and routing
        component_type = analysis['component_type']
        
        # If type is generic but has controller patterns, treat as controller
        if component_type == 'Component' and (
            analysis.get('action_handlers') or 
            ('action' in analysis['expected_fields'] and 'payload' in analysis['expected_fields'])
        ):
            component_type = 'Controller'
        
        # Route to appropriate generator
        if component_type == 'Controller':
            return self._generate_controller_test_data(analysis, num_cases)
        elif component_type == 'Store':
            return self._generate_store_test_data(analysis, num_cases)
        elif component_type == 'APIEndpoint':
            return self._generate_api_test_data(analysis, num_cases)
        else:
            return self._generate_generic_test_data(analysis, num_cases)
    
    def _generate_controller_test_data(self, analysis: Dict, 
                                      num_cases: int) -> List[Dict[str, Any]]:
        """Generate Controller-specific test data with CORRECT structure"""
        test_cases = []
        
        # Check if controller uses payload pattern
        uses_payload = 'payload' in analysis['expected_fields'] or analysis.get('payload_fields')
        
        # If action handlers found, generate test for each
        if analysis['action_handlers']:
            for action_name, handler_info in analysis['action_handlers'].items():
                if uses_payload:
                    # Build payload with appropriate fields
                    payload = {}
                    
                    # Add fields from payload_fields analysis
                    for field in analysis.get('payload_fields', []):
                        payload[field] = self._get_field_value(field)
                    
                    # Add fields used by this specific action handler
                    for field in handler_info.get('fields', []):
                        if field not in payload:
                            payload[field] = self._get_field_value(field)
                    
                    # Ensure required fields for specific actions
                    if 'task' in action_name.lower():
                        if 'update' in action_name or 'delete' in action_name or 'get' in action_name:
                            if 'task_id' not in payload:
                                payload['task_id'] = 'task-123'
                        if 'add' in action_name or 'create' in action_name or 'update' in action_name:
                            if 'title' not in payload:
                                payload['title'] = 'Test Title'
                            if 'description' not in payload:
                                payload['description'] = 'Test Description'
                    
                    # CRITICAL: Only action and payload at top level
                    test_case = {
                        'action': action_name,  # Use ACTUAL action name
                        'payload': payload
                    }
                else:
                    # Non-payload pattern (direct fields)
                    test_case = {'action': action_name}
                    
                    # Add required fields directly
                    for field in handler_info.get('fields', []):
                        test_case[field] = self._get_field_value(field)
                
                test_cases.append(test_case)
                
                if len(test_cases) >= num_cases:
                    break
        
        # If not enough cases, generate based on analysis
        if not test_cases and uses_payload:
            # No action handlers found but uses payload pattern, generate common cases
            common_actions = ['add_task', 'get_task', 'update_task', 'delete_task', 'get_all_tasks']
            
            for action in common_actions[:num_cases]:
                payload = {}
                
                # Add all payload fields from analysis
                for field in analysis.get('payload_fields', []):
                    payload[field] = self._get_field_value(field)
                
                # Ensure required fields for specific actions
                if action in ['update_task', 'delete_task', 'get_task']:
                    if 'task_id' not in payload:
                        payload['task_id'] = 'task-123'
                if action in ['add_task', 'update_task']:
                    if 'title' not in payload:
                        payload['title'] = 'Test Title'
                    if 'description' not in payload:
                        payload['description'] = 'Test Description'
                
                test_case = {
                    'action': action,
                    'payload': payload
                }
                test_cases.append(test_case)
        
        # Fill remaining slots if needed
        while len(test_cases) < num_cases:
            # Generate a simple test case
            if uses_payload:
                test_case = {
                    'action': 'test_action',
                    'payload': {'test_data': f'test_{len(test_cases)}'}
                }
            else:
                test_case = {
                    'action': 'test_action',
                    'test_data': f'test_{len(test_cases)}'
                }
            test_cases.append(test_case)
        
        return test_cases[:num_cases]
    
    def _generate_store_test_data(self, analysis: Dict, 
                                 num_cases: int) -> List[Dict[str, Any]]:
        """Generate Store-specific test data"""
        test_cases = []
        
        # Common store operations
        store_actions = ['save', 'load', 'delete', 'query']
        
        for i, action in enumerate(store_actions[:num_cases]):
            test_case = {'operation': action}
            
            # Add required fields
            for field in analysis['required_fields']:
                test_case[field] = self._get_field_value(field)
            
            # Add operation-specific fields
            if action in ['save', 'update']:
                test_case['data'] = {'item': f'test-item-{i}'}
            elif action in ['load', 'delete']:
                test_case['id'] = f'item-id-{i}'
            elif action == 'query':
                test_case['filters'] = {'status': 'active'}
            
            test_cases.append(test_case)
        
        return test_cases[:num_cases]
    
    def _generate_api_test_data(self, analysis: Dict, 
                               num_cases: int) -> List[Dict[str, Any]]:
        """Generate APIEndpoint-specific test data"""
        test_cases = []
        
        # Common HTTP methods
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        
        for i, method in enumerate(methods[:num_cases]):
            test_case = {
                'method': method,
                'endpoint': f'/test/endpoint/{i}'
            }
            
            # Add required fields
            for field in analysis['required_fields']:
                test_case[field] = self._get_field_value(field)
            
            # Add method-specific fields
            if method in ['POST', 'PUT']:
                test_case['body'] = {'data': f'test-data-{i}'}
            elif method == 'GET':
                test_case['params'] = {'filter': 'all'}
            
            test_cases.append(test_case)
        
        return test_cases[:num_cases]
    
    def _generate_generic_test_data(self, analysis: Dict, 
                                   num_cases: int) -> List[Dict[str, Any]]:
        """Generate generic test data based on analysis"""
        test_cases = []
        
        for i in range(num_cases):
            test_case = {}
            
            # Add all required fields
            for field in analysis['required_fields']:
                test_case[field] = self._get_field_value(field)
            
            # Add some expected fields
            for field in list(analysis['expected_fields'])[:5]:
                if field not in test_case:
                    test_case[field] = self._get_field_value(field)
            
            # Add index for variety
            test_case['test_index'] = i
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _get_field_value(self, field_name: str) -> Any:
        """Get appropriate value for a field based on its name"""
        # Check exact match
        if field_name in self.field_defaults:
            return self.field_defaults[field_name]()
        
        # Check patterns
        field_lower = field_name.lower()
        
        if 'id' in field_lower:
            return f'{field_name}-123'
        elif 'name' in field_lower or 'title' in field_lower:
            return f'Test {field_name.title()}'
        elif 'description' in field_lower or 'desc' in field_lower:
            return f'Test description for {field_name}'
        elif 'action' in field_lower:
            return 'test_action'
        elif 'data' in field_lower or 'payload' in field_lower:
            return {'test': 'data'}
        elif 'count' in field_lower or 'number' in field_lower:
            return 42
        elif 'flag' in field_lower or 'is_' in field_name or 'has_' in field_name:
            return True
        elif 'status' in field_lower or 'state' in field_lower:
            return 'active'
        else:
            return f'test_{field_name}_value'