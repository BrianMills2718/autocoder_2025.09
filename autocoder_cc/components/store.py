#!/usr/bin/env python3
"""
Store component for Autocoder Production Architecture
"""
import anyio
import json
from typing import Dict, Any, Optional, List
from .composed_base import ComposedComponent
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Store(ComposedComponent):
    """
    Store components for data persistence using direct database connections.
    
    This component connects directly to databases (PostgreSQL, MySQL, etc.) 
    based on blueprint configuration for true production readiness.
    Implements CRUD operations pattern from reference implementation.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "Store"
        self.db_client = None
        self.database_type = None
        self.connection_url = None
        
        # Add CRUD operations attributes from reference pattern
        self.storage_type = config.get("storage_type", "memory") if config else "memory"
        self._items = {}
        self.tasks = {}  # Task storage for TaskStore functionality
        self._next_id = 1  # Next ID for task/item generation
        self.running = False  # Component lifecycle state
        
        # Note: ConsistentErrorHandler already initialized in ComposedComponent
        
        # Parse database configuration from blueprint
        if config:
            self.database_type = config.get('database_type', 'postgresql')
            self.table_name = config.get('table_name', 'data_store')
            
            # Only configure database connection if not using memory storage
            if self.storage_type != "memory" and self.database_type != "memory":
                # Use database_url from configuration (lowercase standard)
                self.connection_url = config.get('database_url')
                if not self.connection_url:
                    # Build connection URL from individual components (fallback)
                    try:
                        from autocoder_cc.generators.config import generator_settings
                        host = config.get('host', getattr(generator_settings, 'postgres_host', 'localhost'))
                        port = config.get('port', 5432 if self.database_type == 'postgresql' else 3306)
                        database = config.get('database', getattr(generator_settings, 'postgres_db', 'autocoder'))
                        user = config.get('user', getattr(generator_settings, 'postgres_user', 'postgres'))
                        password = config.get('password', getattr(generator_settings, 'postgres_password', 'password'))
                        
                        if self.database_type == 'postgresql':
                            self.connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                        elif self.database_type == 'mysql':
                            self.connection_url = f"mysql://{user}:{password}@{host}:{port}/{database}"
                    except ImportError:
                        # Fallback to memory storage if database config not available
                        self.storage_type = "memory"
                        self.database_type = "memory"
        else:
            # Default memory configuration for compatibility
            self.storage_type = "memory"
            self.database_type = "memory"

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Store component"""
        return [
            ConfigRequirement(
                name="database_url",
                type="str",
                description="Database connection URL",
                required=True,
                semantic_type=ConfigType.DATABASE_URL,
                example="postgresql://user:pass@localhost/db"
            ),
            ConfigRequirement(
                name="table_name",
                type="str",
                description="Name of the database table",
                required=True,
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="connection_pool_size",
                type="int",
                description="Size of database connection pool",
                required=False,
                default=10,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: 1 <= x <= 100
            )
        ]

    
    @handle_errors(component_name="Store", operation="setup")
    async def setup(self, harness_context=None):
        """Setup store - connect to real database or initialize memory storage"""
        try:
            await super().setup(harness_context)
            self.running = True
            if self.storage_type == "memory":
                self.logger.info(f"Store {self.name} setup with {self.storage_type} storage")
            else:
                await self._connect_storage()
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "database_setup"},
                operation="setup"
            )
            raise
    
    @handle_errors(component_name="Store", operation="cleanup")
    async def cleanup(self):
        """Cleanup store - disconnect from database or clear memory storage"""
        try:
            if self.db_client:
                await self.db_client.disconnect()
            await super().cleanup()
            self.running = False
            self._items.clear()
            self.tasks.clear()
            self.logger.info(f"Store {self.name} cleanup complete")
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "database_cleanup"},
                operation="cleanup"
            )
            # Don't re-raise during cleanup to avoid masking original errors
            self.logger.error(f"Cleanup error (ignored): {e}")
    
    async def _connect_storage(self):
        """Initialize real database client based on configuration"""
        try:
            import databases
            
            self.db_client = databases.Database(self.connection_url)
            await self.db_client.connect()
            
            # Create table if it doesn't exist
            if self.database_type == 'postgresql':
                await self.db_client.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(255) UNIQUE NOT NULL,
                        value JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            elif self.database_type == 'mysql':
                await self.db_client.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        key VARCHAR(255) UNIQUE NOT NULL,
                        value JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")
                
            self.logger.info(f"Connected to {self.database_type} database using URL: {self.connection_url.split('@')[0]}@***")
            
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "database_type": self.database_type, "connection_url": self.connection_url},
                operation="database_connection"
            )
            raise
    
    @handle_errors(component_name="Store", operation="process")
    async def process(self) -> None:
        """Process data from input streams using direct database operations."""
        try:
            # Process all available input streams (not just 'input')
            if self.receive_streams:
                async with anyio.create_task_group() as tg:
                    for stream_name, stream in self.receive_streams.items():
                        tg.start_soon(self._process_stream, stream_name, stream)
            else:
                self.logger.warning("No input stream configured")
                
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "main_process_loop"},
                operation="process"
            )
            self.record_error(str(e))
            raise
    
    async def _process_stream(self, stream_name: str, stream):
        """Process a single input stream using the shared base class method"""
        try:
            await self._process_stream_with_handler(stream_name, stream, self._store_data)
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "stream": stream_name, "operation": "process_stream"},
                operation="stream_processing"
            )
            raise
    
    async def _store_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store data using direct database operations.
        This performs real INSERT/UPDATE operations for production readiness.
        """
        try:
            if not self.db_client:
                raise RuntimeError("Database client not connected")
            
            # Extract key and value from input data
            key = data.get('key', f"auto_key_{self._status.items_processed}")
            value = data.get('value', data)
            
            # Convert value to JSON string for storage
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            # Perform INSERT or UPDATE based on database type
            if self.database_type == 'postgresql':
                # Use PostgreSQL UPSERT (INSERT ... ON CONFLICT)
                query = f"""
                    INSERT INTO {self.table_name} (key, value, updated_at) 
                    VALUES (:key, :value, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) 
                    DO UPDATE SET value = :value, updated_at = CURRENT_TIMESTAMP
                """
                await self.db_client.execute(query, {"key": key, "value": value_json})
                
            elif self.database_type == 'mysql':
                # Use MySQL ON DUPLICATE KEY UPDATE
                query = f"""
                    INSERT INTO {self.table_name} (key, value, updated_at) 
                    VALUES (:key, :value, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE value = :value, updated_at = CURRENT_TIMESTAMP
                """
                await self.db_client.execute(query, {"key": key, "value": value_json})
            
            self.logger.info(f"Successfully stored data with key: {key}")
            
            return {
                "operation": "store",
                "key": key,
                "success": True,
                "database_type": self.database_type,
                "table_name": self.table_name,
                "original_data": data
            }
            
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "database_store", "data": data},
                operation="store_data"
            )
            return {
                "operation": "store",
                "success": False,
                "error": str(e),
                "original_data": data
            }
    
    async def process_item(self, item: Any) -> Any:
        """Process CRUD operations on tasks (from reference pattern)"""
        try:
            if not isinstance(item, dict) or "action" not in item:
                return {"status": "error", "message": "Invalid request format"}
            
            action = item["action"]
            
            if action == "create":
                task_id = str(self._next_id)
                task_data = {
                    "id": task_id,
                    "data": item["data"]
                }
                self.tasks[task_id] = task_data
                self._next_id += 1
                return {"status": "success", "id": task_id, "data": task_data}
            
            elif action == "get":
                task_id = item["id"]
                if task_id in self.tasks:
                    return {"status": "success", "data": self.tasks[task_id]}
                else:
                    return {"status": "not_found", "action": "get", "id": task_id}
            
            elif action == "update":
                task_id = item["id"]
                if task_id in self.tasks:
                    # Update task data while preserving id
                    updated_data = {**self.tasks[task_id]["data"], **item["data"]}
                    self.tasks[task_id]["data"] = updated_data
                    return {"status": "success", "data": self.tasks[task_id]}
                else:
                    return {"status": "not_found", "action": "update", "id": task_id}
            
            elif action == "delete":
                task_id = item["id"]
                if task_id in self.tasks:
                    del self.tasks[task_id]
                    return {"status": "success"}
                else:
                    return {"status": "not_found", "action": "delete", "id": task_id}
            
            elif action == "list":
                task_list = list(self.tasks.values())
                return {"status": "success", "data": task_list}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Store processing error: {e}")
            return {"status": "error", "message": str(e)}
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status (from reference pattern)"""
        base_health = super().get_health_status()
        return {
            **base_health, 
            "status": "healthy", 
            "items_count": len(self._items), 
            "storage_type": self.storage_type,
            "healthy": True,
            "task_count": len(self.tasks),
            "next_id": self._next_id
        }
    
    def get(self, item_id):
        """Get an item by ID (from reference pattern)"""
        return self._items.get(item_id)
    
    def list_items(self):
        """List all stored items (from reference pattern)"""
        return list(self._items.values())
    
    def count(self):
        """Get count of stored items (from reference pattern)"""
        return len(self._items)
    
    # CRUD Methods for smoke test compatibility
    def create(self, key: str, value: Any) -> None:
        """Create a new item in the store"""
        self._items[key] = value
    
    def read(self, key: str) -> Any:
        """Read an item from the store"""
        return self._items.get(key)
    
    def update(self, key: str, value: Any) -> None:
        """Update an existing item in the store"""
        if key in self._items:
            self._items[key] = value
        else:
            raise KeyError(f"Key '{key}' not found in store")
    
    def delete(self, key: str) -> None:
        """Delete an item from the store"""
        if key in self._items:
            del self._items[key]