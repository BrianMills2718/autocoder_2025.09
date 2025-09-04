"""Base class for database-connected components."""
from typing import Dict, Any, Optional
from autocoder_cc.components.primitives.base import Sink, Source, Transformer
from autocoder_cc.database.connection_layer import DatabaseConnectionLayer, DatabaseConfig

class DatabaseSink(Sink):
    """Sink that writes to database."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.db_layer = DatabaseConnectionLayer()
        self.db_config = DatabaseConfig(
            db_type=config.get('db_type', 'sqlite'),
            connection_string=config.get('connection_string', ':memory:'),
            pool_size=config.get('pool_size', 10)
        )
        self.db_conn = None
        
    async def setup(self):
        """Initialize database connection."""
        await super().setup()
        self.db_conn = await self.db_layer.connect(self.name, self.db_config)
        
    async def cleanup(self):
        """Close database connection."""
        if self.db_conn:
            await self.db_layer.disconnect(self.name)
        await super().cleanup()
        
    async def consume(self, item: Dict[str, Any]):
        """Store item in database."""
        # Implement in subclasses
        raise NotImplementedError

class DatabaseSource(Source):
    """Source that reads from database."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.db_layer = DatabaseConnectionLayer()
        self.db_config = DatabaseConfig(
            db_type=config.get('db_type', 'sqlite'),
            connection_string=config.get('connection_string', ':memory:')
        )
        self.db_conn = None
        
    async def setup(self):
        """Initialize database connection."""
        await super().setup()
        self.db_conn = await self.db_layer.connect(self.name, self.db_config)
        
    async def cleanup(self):
        """Close database connection."""
        if self.db_conn:
            await self.db_layer.disconnect(self.name)
        await super().cleanup()
        
    async def generate(self):
        """Generate items from database."""
        # Implement in subclasses
        raise NotImplementedError