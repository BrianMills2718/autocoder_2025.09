"""Store component for walking skeleton."""
import anyio
import time
from typing import Dict, Any, List
from autocoder_cc.components.primitives.base import Sink
from autocoder_cc.ports.base import InputPort, OutputPort
from autocoder_cc.observability import get_logger

class Store(Sink):
    """Data store component."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.logger = get_logger(f"Store.{name}")
        self.input_port = InputPort(f"{name}.data_in")
        self.output_port = OutputPort(f"{name}.confirmations")
        
        self.storage_type = config.get('storage_type', 'memory')
        self.max_items = config.get('max_items', 10000)
        
        # In-memory storage
        self.data: List[Dict[str, Any]] = []
        self.stored_count = 0
        self.operation_counts = {'CREATE': 0, 'READ': 0, 'UPDATE': 0}
        self._task_group = None
        
    async def setup(self):
        """Setup the store."""
        self.logger.info(f"Setting up Store {self.name}")
        # Don't start task group here - will be handled by runner
    
    async def _process_loop(self):
        """Process messages from input port."""
        while True:
            try:
                message = await self.input_port.receive()
                if message:
                    await self.store_data(message)
                else:
                    await anyio.sleep(0.001)
            except Exception as e:
                self.logger.error(f"Process loop error: {e}")
                await anyio.sleep(0.01)
    
    async def store_data(self, message: Dict[str, Any]):
        """Store data and send confirmation."""
        # Store in memory
        if len(self.data) < self.max_items:
            self.data.append(message)
            self.stored_count += 1
            
            # Track operation type
            operation = message.get('operation', 'UNKNOWN')
            if operation in self.operation_counts:
                self.operation_counts[operation] += 1
            
            # Send confirmation
            confirmation = {
                'id': message.get('id', 'unknown'),
                'operation': operation,
                'stored': True,
                'store_index': self.stored_count - 1,
                'timestamp': time.time()
            }
            await self.output_port.send(confirmation)
        else:
            self.logger.warning(f"Store full, dropping message")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            'total_stored': self.stored_count,
            'current_items': len(self.data),
            'operation_counts': self.operation_counts,
            'storage_type': self.storage_type
        }
    
    async def consume(self, item: Dict[str, Any]) -> None:
        """Consume method required by Sink base class."""
        # This method is required by the abstract base class
        # Store the item
        if len(self.data) < self.max_items:
            self.data.append(item)
            self.stored_count += 1
            
            # Track operation type
            operation = item.get('operation', 'UNKNOWN')
            if operation in self.operation_counts:
                self.operation_counts[operation] += 1
    
    async def cleanup(self):
        """Cleanup the store."""
        # Task group cleanup removed - handled by runner
        self.input_port.disconnect()
        self.output_port.disconnect()
        
        # Log final stats
        stats = self.get_stats()
        self.logger.info(f"Store Statistics:")
        self.logger.info(f"  Total stored: {stats['total_stored']}")
        self.logger.info(f"  Operations: {stats['operation_counts']}")
        
        self.logger.info(f"Cleaned up Store {self.name}")