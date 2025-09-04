from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any, Optional
import asyncio
import logging
import asyncpg

class GeneratedStore_todo_store(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.storage_type = config.get("storage_type", "postgresql")
        self.connection = None

    async def initialize(self):
        try:
            self.connection = await asyncpg.connect(user='user', password='password', 
                                                    database='todo_db', host='127.0.0.1')
        except Exception as e:
            logging.error(f"Failed to connect to the database: {e}")
            raise

    async def store(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = "INSERT INTO todos(id, title, completed) VALUES($1, $2, $3) RETURNING id"
            item_id = await self.connection.fetchval(query, item['id'], item['title'], item['completed'])
            return {"status": "success", "id": item_id}
        except Exception as e:
            logging.error(f"Failed to store item: {e}")
            return {"status": "error", "message": str(e)}

    async def retrieve(self, item_id: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM todos WHERE id = $1"
            item = await self.connection.fetchrow(query, item_id)
            if item:
                return dict(item)
            return None
        except Exception as e:
            logging.error(f"Failed to retrieve item: {e}")
            return None

    async def process_item(self, item: Any) -> Any:
        if item is None:
            logging.error("No item provided for processing.")
            return {"status": "error", "message": "No item provided"}
        
        if 'action' not in item:
            logging.error("Invalid item structure.")
            return {"status": "error", "message": "Invalid item structure"}

        if item['action'] == 'store':
            return await self.store(item)
        elif item['action'] == 'retrieve':
            return await self.retrieve(item['id'])
        else:
            logging.error("Unsupported action.")
            return {"status": "error", "message": "Unsupported action"}

    async def close(self):
        if self.connection:
            await self.connection.close()