"""Controller component for walking skeleton."""
import anyio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from autocoder_cc.components.primitives.base import Transformer
from autocoder_cc.ports.base import InputPort, OutputPort
from autocoder_cc.observability import get_logger

class Controller(Transformer):
    """Business logic controller."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.logger = get_logger(f"Controller.{name}")
        self.input_port = InputPort(f"{name}.requests_in")
        self.output_port = OutputPort(f"{name}.processed_requests")
        
        self.processing_rules = config.get('processing_rules', {})
        self.processed_count = 0
        self._task_group = None
        
    async def setup(self):
        """Setup the controller."""
        self.logger.info(f"Setting up Controller {self.name}")
        # Don't start task group here - will be handled by runner
    
    async def _process_loop(self):
        """Process messages from input port."""
        while True:
            try:
                message = await self.input_port.receive()
                if message:
                    await self.process_request(message)
                else:
                    await anyio.sleep(0.001)
            except Exception as e:
                self.logger.error(f"Process loop error: {e}")
                await anyio.sleep(0.01)
    
    async def process_request(self, message: Dict[str, Any]):
        """Process a validated request."""
        operation = message.get('operation', 'UNKNOWN')
        
        # Apply processing rules based on operation
        if operation == 'CREATE':
            message = self.process_create(message)
        elif operation == 'READ':
            message = self.process_read(message)
        elif operation == 'UPDATE':
            message = self.process_update(message)
        
        # Add common metadata
        message['processed_by'] = self.name
        message['processed_at'] = datetime.now().isoformat()
        
        self.processed_count += 1
        await self.output_port.send(message)
    
    def process_create(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process CREATE operation."""
        message['id'] = str(uuid.uuid4())
        message['created_at'] = datetime.now().isoformat()
        message['version'] = 1
        return message
    
    def process_read(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process READ operation."""
        message['read_at'] = datetime.now().isoformat()
        message['permissions_checked'] = True
        return message
    
    def process_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process UPDATE operation."""
        message['updated_at'] = datetime.now().isoformat()
        message['version'] = message.get('version', 1) + 1
        message['audit_trail'] = message.get('audit_trail', [])
        message['audit_trail'].append({
            'action': 'UPDATE',
            'timestamp': datetime.now().isoformat(),
            'controller': self.name
        })
        return message
    
    async def transform(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform method required by Transformer base class."""
        # This method is required by the abstract base class
        # Process the request and return the transformed message
        operation = item.get('operation', 'UNKNOWN')
        
        # Apply processing rules based on operation
        if operation == 'CREATE':
            item = self.process_create(item)
        elif operation == 'READ':
            item = self.process_read(item)
        elif operation == 'UPDATE':
            item = self.process_update(item)
        
        # Add common metadata
        item['processed_by'] = self.name
        item['processed_at'] = datetime.now().isoformat()
        
        return item
    
    async def cleanup(self):
        """Cleanup the controller."""
        # Task group cleanup removed - handled by runner
        self.input_port.disconnect()
        self.output_port.disconnect()
        self.logger.info(f"Processed {self.processed_count} requests")
        self.logger.info(f"Cleaned up Controller {self.name}")