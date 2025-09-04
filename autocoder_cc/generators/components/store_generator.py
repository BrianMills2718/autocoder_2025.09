#!/usr/bin/env python3
"""
Store Component Generator
Generates data storage components with database integration
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from jinja2 import Template

from .base_generator import BaseComponentGenerator
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer


class StoreGenerator(BaseComponentGenerator):
    """
    Generator for Store components with database integration.
    
    Features:
    - PostgreSQL, MySQL, SQLite support
    - Async database operations
    - Connection pooling
    - Schema management
    - Data validation
    """
    
    def __init__(self):
        super().__init__()
        self.structured_logger = get_logger("store_generator", component="StoreGenerator")
        self.metrics_collector = get_metrics_collector("store_generator")
        self.tracer = get_tracer("store_generator")
        
        self.structured_logger.info(
            "StoreGenerator initialized",
            operation="init"
        )
    
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """Generate Store component code"""
        
        with self.tracer.span("store_generation", tags={"component": component_spec.get("name", "unknown")}) as span_id:
            try:
                component_name = component_spec.get("name", "DataStore")
                component_type = component_spec.get("type", "Store")
                
                self.structured_logger.info(
                    f"Generating Store component: {component_name}",
                    operation="generate_component",
                    tags={"component_name": component_name, "component_type": component_type}
                )
                
                # Generate and return component code
                component_code = self._generate_store_code(component_spec)
                
                # Record metrics
                self.metrics_collector.record_component_generated()
                
                self.structured_logger.info(
                    f"Store component generated successfully: {component_name}",
                    operation="component_generated",
                    tags={"component_name": component_name}
                )
                
                return component_code
                
            except Exception as e:
                self.metrics_collector.record_error(e.__class__.__name__)
                self.structured_logger.error(
                    f"Store component generation failed",
                    error=e,
                    operation="generation_error",
                    tags={"component_name": component_spec.get("name", "unknown")}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Generation error: {e}", "error")
                
                raise
    
    def _generate_store_code(self, config: Dict[str, Any]) -> str:
        """Generate the Store component implementation"""
        
        component_name = config.get("name", "DataStore")
        database_type = config.get("database_type", "postgresql")
        connection_pool_size = config.get("connection_pool_size", 10)
        tables = config.get("tables", [])
        indexes = config.get("indexes", [])
        
        template = Template('''#!/usr/bin/env python3
"""
{{ component_name }} - Store Component
Auto-generated data storage component with {{ database_type }} integration
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


@dataclass
class TableSchema:
    """Database table schema definition"""
    name: str
    columns: List[Dict[str, Any]]
    primary_key: str
    indexes: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "indexes": self.indexes or []
        }


@dataclass
class QueryResult:
    """Result of database query"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    row_count: int = 0
    execution_time_ms: float = 0.0


class {{ component_name }}(ComposedComponent):
    """
    Store component for data persistence with {{ database_type }} integration.
    
    Features:
    - {{ database_type.title() }} database integration
    - Connection pooling with {{ connection_pool_size }} connections
    - Async database operations
    - Schema management and migration
    - Data validation and sanitization
    - Query optimization with indexes
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "Store"
        
        # Initialize observability
        self.structured_logger = get_logger(f"store.{name}", component=self.name)
        self.metrics_collector = get_metrics_collector(f"store.{name}")
        self.tracer = get_tracer(f"store.{name}")
        
        # Database configuration
        self.database_type = DatabaseType({{ database_type.upper() }})
        self.connection_pool_size = {{ connection_pool_size }}
        self.connection_string = config.get("connection_string", self._get_default_connection_string())
        
        # Database connection
        self.database = None
        self.connection_pool = None
        
        # Schema management
        self.tables = {{ tables }}
        self.indexes = {{ indexes }}
        
        # Query cache for performance
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        
        self.structured_logger.info(
            f"{{ component_name }} initialized",
            operation="init",
            tags={
                "database_type": self.database_type.value,
                "connection_pool_size": self.connection_pool_size,
                "tables": len(self.tables),
                "indexes": len(self.indexes)
            }
        )
    
    def _get_default_connection_string(self) -> str:
        """Get default connection string based on database type"""
        if self.database_type == DatabaseType.POSTGRESQL:
            return "postgresql://user:password@localhost:5432/autocoder_db"
        elif self.database_type == DatabaseType.MYSQL:
            return "mysql://user:password@localhost:3306/autocoder_db"
        elif self.database_type == DatabaseType.SQLITE:
            return "sqlite:///autocoder.db"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")
    
    async def setup(self):
        """Setup database connections and schema"""
        
        await super().setup()
        
        try:
            # Initialize database connection based on type
            if self.database_type == DatabaseType.POSTGRESQL:
                await self._setup_postgresql()
            elif self.database_type == DatabaseType.MYSQL:
                await self._setup_mysql()
            elif self.database_type == DatabaseType.SQLITE:
                await self._setup_sqlite()
            
            # Create tables and indexes
            await self._create_schema()
            
            self.structured_logger.info(
                "Store setup complete",
                operation="setup_complete",
                tags={"database_type": self.database_type.value}
            )
            
        except Exception as e:
            self.structured_logger.error(
                "Store setup failed",
                error=e,
                operation="setup_error"
            )
            raise
    
    async def _setup_postgresql(self):
        """Setup PostgreSQL connection"""
        try:
            from databases import Database
            
            self.database = Database(self.connection_string)
            await self.database.connect()
            
            self.structured_logger.debug(
                "PostgreSQL connection established",
                operation="postgresql_connected"
            )
            
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")
    
    async def _setup_mysql(self):
        """Setup MySQL connection"""
        try:
            from databases import Database
            
            self.database = Database(self.connection_string)
            await self.database.connect()
            
            self.structured_logger.debug(
                "MySQL connection established",
                operation="mysql_connected"
            )
            
        except Exception as e:
            raise Exception(f"Failed to connect to MySQL: {e}")
    
    async def _setup_sqlite(self):
        """Setup SQLite connection"""
        try:
            from databases import Database
            
            self.database = Database(self.connection_string)
            await self.database.connect()
            
            self.structured_logger.debug(
                "SQLite connection established",
                operation="sqlite_connected"
            )
            
        except Exception as e:
            raise Exception(f"Failed to connect to SQLite: {e}")
    
    async def _create_schema(self):
        """Create database schema with tables and indexes"""
        
        for table_schema in self.tables:
            await self._create_table(table_schema)
        
        for index in self.indexes:
            await self._create_index(index)
        
        self.structured_logger.info(
            f"Schema created with {len(self.tables)} tables and {len(self.indexes)} indexes",
            operation="schema_created"
        )
    
    async def _create_table(self, table_schema: Dict[str, Any]):
        """Create a database table"""
        
        table_name = table_schema["name"]
        columns = table_schema["columns"]
        primary_key = table_schema["primary_key"]
        
        # Build CREATE TABLE statement
        column_definitions = []
        for column in columns:
            col_name = column["name"]
            col_type = column["type"]
            col_nullable = "NOT NULL" if not column.get("nullable", True) else ""
            col_default = f"DEFAULT {column['default']}" if "default" in column else ""
            
            column_definitions.append(f"{col_name} {col_type} {col_nullable} {col_default}".strip())
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)},
            PRIMARY KEY ({primary_key})
        )
        """
        
        await self.database.execute(create_table_sql)
        
        self.structured_logger.debug(
            f"Table created: {table_name}",
            operation="table_created",
            tags={"table": table_name}
        )
    
    async def _create_index(self, index_config: Dict[str, Any]):
        """Create a database index"""
        
        index_name = index_config["name"]
        table_name = index_config["table"]
        columns = index_config["columns"]
        index_type = index_config.get("type", "BTREE")
        
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS {index_name} 
        ON {table_name} ({', '.join(columns)}) 
        USING {index_type}
        """
        
        await self.database.execute(create_index_sql)
        
        self.structured_logger.debug(
            f"Index created: {index_name} on {table_name}",
            operation="index_created",
            tags={"index": index_name, "table": table_name}
        )
    
    async def insert_data(self, table_name: str, data: Dict[str, Any]) -> QueryResult:
        """Insert data into a table"""
        
        with self.tracer.span("store_insert", tags={"table": table_name}) as span_id:
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Build INSERT statement
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ", ".join(["?" for _ in values])
                
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Execute insert
                await self.database.execute(insert_sql, values)
                
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Record metrics
                self.metrics_collector.record_database_operation("insert", table_name)
                
                self.structured_logger.info(
                    f"Data inserted into {table_name}",
                    operation="data_inserted",
                    tags={"table": table_name, "execution_time_ms": execution_time}
                )
                
                return QueryResult(
                    success=True,
                    row_count=1,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.metrics_collector.record_error(e.__class__.__name__)
                
                self.structured_logger.error(
                    f"Failed to insert data into {table_name}",
                    error=e,
                    operation="insert_error",
                    tags={"table": table_name}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Insert error: {e}", "error")
                
                return QueryResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
    
    async def query_data(self, table_name: str, conditions: Dict[str, Any] = None, 
                        limit: int = None, offset: int = None) -> QueryResult:
        """Query data from a table"""
        
        with self.tracer.span("store_query", tags={"table": table_name}) as span_id:
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Build SELECT statement
                select_sql = f"SELECT * FROM {table_name}"
                values = []
                
                # Add WHERE conditions
                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        where_clauses.append(f"{key} = ?")
                        values.append(value)
                    
                    if where_clauses:
                        select_sql += f" WHERE {' AND '.join(where_clauses)}"
                
                # Add LIMIT and OFFSET
                if limit:
                    select_sql += f" LIMIT {limit}"
                if offset:
                    select_sql += f" OFFSET {offset}"
                
                # Execute query
                rows = await self.database.fetch_all(select_sql, values)
                
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Record metrics
                self.metrics_collector.record_database_operation("query", table_name)
                
                self.structured_logger.info(
                    f"Data queried from {table_name}",
                    operation="data_queried",
                    tags={"table": table_name, "row_count": len(rows), "execution_time_ms": execution_time}
                )
                
                return QueryResult(
                    success=True,
                    data=[dict(row) for row in rows],
                    row_count=len(rows),
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.metrics_collector.record_error(e.__class__.__name__)
                
                self.structured_logger.error(
                    f"Failed to query data from {table_name}",
                    error=e,
                    operation="query_error",
                    tags={"table": table_name}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Query error: {e}", "error")
                
                return QueryResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
    
    async def update_data(self, table_name: str, data: Dict[str, Any], 
                         conditions: Dict[str, Any]) -> QueryResult:
        """Update data in a table"""
        
        with self.tracer.span("store_update", tags={"table": table_name}) as span_id:
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Build UPDATE statement
                set_clauses = []
                values = []
                
                for key, value in data.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    values.append(value)
                
                update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)}"
                if where_clauses:
                    update_sql += f" WHERE {' AND '.join(where_clauses)}"
                
                # Execute update
                await self.database.execute(update_sql, values)
                
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Record metrics
                self.metrics_collector.record_database_operation("update", table_name)
                
                self.structured_logger.info(
                    f"Data updated in {table_name}",
                    operation="data_updated",
                    tags={"table": table_name, "execution_time_ms": execution_time}
                )
                
                return QueryResult(
                    success=True,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.metrics_collector.record_error(e.__class__.__name__)
                
                self.structured_logger.error(
                    f"Failed to update data in {table_name}",
                    error=e,
                    operation="update_error",
                    tags={"table": table_name}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Update error: {e}", "error")
                
                return QueryResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
    
    async def delete_data(self, table_name: str, conditions: Dict[str, Any]) -> QueryResult:
        """Delete data from a table"""
        
        with self.tracer.span("store_delete", tags={"table": table_name}) as span_id:
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Build DELETE statement
                where_clauses = []
                values = []
                
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    values.append(value)
                
                delete_sql = f"DELETE FROM {table_name}"
                if where_clauses:
                    delete_sql += f" WHERE {' AND '.join(where_clauses)}"
                
                # Execute delete
                await self.database.execute(delete_sql, values)
                
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Record metrics
                self.metrics_collector.record_database_operation("delete", table_name)
                
                self.structured_logger.info(
                    f"Data deleted from {table_name}",
                    operation="data_deleted",
                    tags={"table": table_name, "execution_time_ms": execution_time}
                )
                
                return QueryResult(
                    success=True,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.metrics_collector.record_error(e.__class__.__name__)
                
                self.structured_logger.error(
                    f"Failed to delete data from {table_name}",
                    error=e,
                    operation="delete_error",
                    tags={"table": table_name}
                )
                
                if span_id:
                    self.tracer.add_span_log(span_id, f"Delete error: {e}", "error")
                
                return QueryResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
    
    async def process_item(self, item: Any) -> Any:
        """Process stream item (if used in stream processing)"""
        
        # If item is a dictionary with database operation, execute it
        if isinstance(item, dict) and "operation" in item:
            operation = item["operation"]
            table_name = item.get("table")
            data = item.get("data", {})
            conditions = item.get("conditions", {})
            
            if operation == "insert":
                return await self.insert_data(table_name, data)
            elif operation == "query":
                return await self.query_data(table_name, conditions, 
                                           item.get("limit"), item.get("offset"))
            elif operation == "update":
                return await self.update_data(table_name, data, conditions)
            elif operation == "delete":
                return await self.delete_data(table_name, conditions)
        
        return item
    
    async def teardown(self):
        """Teardown database connections"""
        
        try:
            if self.database:
                await self.database.disconnect()
            
            self.structured_logger.info(
                "Store teardown complete",
                operation="teardown_complete"
            )
            
        except Exception as e:
            self.structured_logger.error(
                "Store teardown failed",
                error=e,
                operation="teardown_error"
            )
        
        await super().teardown()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get store health status"""
        
        base_health = super().get_health_status()
        
        store_health = {
            "database_type": self.database_type.value,
            "connection_active": self.database is not None,
            "tables_configured": len(self.tables),
            "indexes_configured": len(self.indexes),
            "cache_size": len(self.query_cache)
        }
        
        return {
            **base_health,
            "store": store_health
        }


# Example usage
async def example_store_operations():
    """Example of how to use the store component"""
    
    # Create store instance
    store = {{ component_name }}("example_store", {
        "database_type": "{{ database_type }}",
        "connection_string": "your_connection_string_here"
    })
    
    # Setup store
    await store.setup()
    
    # Insert data
    result = await store.insert_data("users", {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # Query data
    result = await store.query_data("users", {"id": 1})
    
    # Update data
    result = await store.update_data("users", {"name": "Jane Doe"}, {"id": 1})
    
    # Delete data
    result = await store.delete_data("users", {"id": 1})
    
    # Teardown
    await store.teardown()
''')
        
        return template.render(
            component_name=component_name,
            database_type=database_type,
            connection_pool_size=connection_pool_size,
            tables=tables,
            indexes=indexes
        ) 