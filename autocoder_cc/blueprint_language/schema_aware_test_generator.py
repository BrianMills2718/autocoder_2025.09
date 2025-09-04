"""Schema-aware test data generator for validation."""
import json
import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from autocoder_cc.observability import get_logger

class SchemaAwareTestGenerator:
    """Generate test data matching component schemas."""
    
    def __init__(self):
        self.logger = get_logger("SchemaAwareTestGenerator")
        self.generated_count = 0
    
    def generate_test_data(self, component_type: str, port_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate test data for a component.
        
        Args:
            component_type: Type of component
            port_schema: Optional JSON schema for the port
            
        Returns:
            Generated test data
        """
        if port_schema:
            return self._generate_from_schema(port_schema)
        else:
            return self._generate_default_for_type(component_type)
    
    def _generate_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data matching a JSON schema."""
        if schema.get('type') == 'object':
            result = {}
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            # Generate required fields
            for field in required:
                if field in properties:
                    result[field] = self._generate_field(properties[field])
            
            # Generate optional fields (50% chance)
            for field, field_schema in properties.items():
                if field not in result and random.random() > 0.5:
                    result[field] = self._generate_field(field_schema)
            
            return result
        elif schema.get('type') == 'array':
            item_schema = schema.get('items', {})
            length = random.randint(1, 5)
            return [self._generate_from_schema(item_schema) for _ in range(length)]
        else:
            return self._generate_field(schema)
    
    def _generate_field(self, field_schema: Dict[str, Any]) -> Any:
        """Generate a single field value."""
        field_type = field_schema.get('type', 'string')
        
        if field_type == 'string':
            if 'enum' in field_schema:
                return random.choice(field_schema['enum'])
            elif 'format' in field_schema:
                return self._generate_formatted_string(field_schema['format'])
            else:
                return self._generate_random_string()
        
        elif field_type == 'number' or field_type == 'integer':
            min_val = field_schema.get('minimum', 0)
            max_val = field_schema.get('maximum', 1000)
            if field_type == 'integer':
                return random.randint(int(min_val), int(max_val))
            else:
                return random.uniform(min_val, max_val)
        
        elif field_type == 'boolean':
            return random.choice([True, False])
        
        elif field_type == 'array':
            item_schema = field_schema.get('items', {'type': 'string'})
            length = random.randint(1, 5)
            return [self._generate_field(item_schema) for _ in range(length)]
        
        elif field_type == 'object':
            return self._generate_from_schema(field_schema)
        
        else:
            return None
    
    def _generate_formatted_string(self, format_type: str) -> str:
        """Generate string with specific format."""
        if format_type == 'date-time':
            return datetime.now().isoformat()
        elif format_type == 'date':
            return datetime.now().date().isoformat()
        elif format_type == 'email':
            return f"test_{self.generated_count}@example.com"
        elif format_type == 'uuid':
            import uuid
            return str(uuid.uuid4())
        elif format_type == 'uri':
            return f"https://example.com/resource/{self.generated_count}"
        else:
            return self._generate_random_string()
    
    def _generate_random_string(self, length: int = 10) -> str:
        """Generate random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _generate_default_for_type(self, component_type: str) -> Dict[str, Any]:
        """Generate default test data for component type."""
        self.generated_count += 1
        
        defaults = {
            'Source': {
                'id': f'source_{self.generated_count}',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'value': random.randint(1, 100),
                    'type': 'generated'
                }
            },
            'Sink': {
                'id': f'sink_{self.generated_count}',
                'operation': 'store',
                'payload': {'test': True}
            },
            'Transformer': {
                'id': f'transform_{self.generated_count}',
                'input': random.randint(1, 100),
                'operation': 'multiply',
                'factor': 2
            },
            'Filter': {
                'id': f'filter_{self.generated_count}',
                'value': random.randint(1, 100),
                'threshold': 50
            },
            'Router': {
                'id': f'route_{self.generated_count}',
                'destination': random.choice(['service_a', 'service_b', 'service_c']),
                'priority': random.randint(1, 10)
            },
            'Store': {
                'id': f'store_{self.generated_count}',
                'operation': random.choice(['CREATE', 'READ', 'UPDATE', 'DELETE']),
                'entity': {
                    'name': f'entity_{self.generated_count}',
                    'value': random.randint(1, 1000)
                }
            },
            'Controller': {
                'id': f'control_{self.generated_count}',
                'command': random.choice(['start', 'stop', 'pause', 'resume']),
                'target': f'component_{random.randint(1, 10)}'
            }
        }
        
        return defaults.get(component_type, {
            'id': f'test_{self.generated_count}',
            'type': component_type,
            'data': {'test': True}
        })
    
    def generate_batch(self, component_type: str, count: int, schema: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Generate batch of test data."""
        return [
            self.generate_test_data(component_type, schema)
            for _ in range(count)
        ]