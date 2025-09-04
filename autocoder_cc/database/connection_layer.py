"""Database connection layer for port-based components."""
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from autocoder_cc.observability import get_logger

# Try to import database libraries if available
try:
    import asyncpg  # PostgreSQL
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    import aiosqlite  # SQLite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

try:
    from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB
    HAS_MOTOR = True
except ImportError:
    HAS_MOTOR = False

@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: str  # 'postgres', 'sqlite', 'mongodb'
    connection_string: str
    pool_size: int = 10
    timeout: int = 30

class DatabaseConnectionLayer:
    """Manages database connections for components."""
    
    def __init__(self):
        self.logger = get_logger("DatabaseConnectionLayer")
        self.connections: Dict[str, Any] = {}
        self.pools: Dict[str, Any] = {}
        
    async def connect(self, name: str, config: DatabaseConfig) -> Any:
        """Create database connection."""
        self.logger.info(f"Connecting to {config.db_type} database: {name}")
        
        if config.db_type == 'postgres':
            if not HAS_ASYNCPG:
                raise ImportError("asyncpg not installed. Install with: pip install asyncpg")
            pool = await asyncpg.create_pool(
                config.connection_string,
                min_size=1,
                max_size=config.pool_size,
                command_timeout=config.timeout
            )
            self.pools[name] = pool
            return pool
            
        elif config.db_type == 'sqlite':
            if not HAS_AIOSQLITE:
                raise ImportError("aiosqlite not installed. Install with: pip install aiosqlite")
            conn = await aiosqlite.connect(config.connection_string)
            self.connections[name] = conn
            return conn
            
        elif config.db_type == 'mongodb':
            if not HAS_MOTOR:
                raise ImportError("motor not installed. Install with: pip install motor")
            client = AsyncIOMotorClient(config.connection_string)
            self.connections[name] = client
            return client
            
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")
    
    async def disconnect(self, name: str):
        """Close database connection."""
        if name in self.pools:
            await self.pools[name].close()
            del self.pools[name]
            
        if name in self.connections:
            conn = self.connections[name]
            if hasattr(conn, 'close'):
                await conn.close()
            del self.connections[name]
        
        self.logger.info(f"Disconnected: {name}")
    
    async def execute(self, name: str, query: str, *args) -> Any:
        """Execute database query."""
        if name in self.pools:
            # PostgreSQL
            async with self.pools[name].acquire() as conn:
                return await conn.fetch(query, *args)
                
        elif name in self.connections:
            conn = self.connections[name]
            if HAS_AIOSQLITE and hasattr(conn, 'execute'):
                # SQLite
                cursor = await conn.execute(query, args)
                return await cursor.fetchall()
            else:
                # MongoDB - needs different approach
                raise NotImplementedError("Use MongoDB client directly")
        
        raise KeyError(f"No connection named: {name}")
    
    async def disconnect_all(self):
        """Close all connections."""
        for name in list(self.pools.keys()):
            await self.disconnect(name)
        for name in list(self.connections.keys()):
            await self.disconnect(name)