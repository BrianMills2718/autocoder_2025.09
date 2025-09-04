
import uuid
from datetime import datetime, timezone

# Essential imports for all components - use sys.path to ensure imports work
import sys
import os
# Add the components directory to sys.path for imports
if __name__ != '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
from observability import ComposedComponent, SpanStatus
# Standard library imports - MUST include all typing types used
from typing import Dict, Any, Optional, List, Tuple, Union, Set

import uuid
from datetime import datetime, timezone
import re
import time

class GeneratedStore_Datapersister(ComposedComponent):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.items = {}
        self.storage_type = config.get("storage_type", "in-memory")
        self.logger.info(f"Datapersister component initialized with storage type: {self.storage_type}")

    async def process_item(self, item):
        """Route actions to appropriate handlers for data persistence."""
        action = item.get("action")
        
        try:
            if action == "add_item":
                title = item.get("title")
                description = item.get("description")
                if not title or not description:
                    return {"status": "error", "message": "Missing 'title' or 'description' for add_item action."}
                return await self.add_item(title, description)
            elif action == "get_item":
                item_id = item.get("item_id")
                if not item_id:
                    return {"status": "error", "message": "Missing 'item_id' for get_item action."}
                return await self.get_item(item_id)
            elif action == "update_item":
                item_id = item.get("item_id")
                update_data = item.get("update_data")
                if not item_id or not update_data:
                    return {"status": "error", "message": "Missing 'item_id' or 'update_data' for update_item action."}
                return await self.update_item(item_id, update_data)
            elif action == "delete_item":
                item_id = item.get("item_id")
                if not item_id:
                    return {"status": "error", "message": "Missing 'item_id' for delete_item action."}
                return await self.delete_item(item_id)
            elif action == "list_items":
                return await self.list_items()
            else:
                self.logger.warning(f"Unknown action received: {action}")
                return {"status": "error", "message": f"Unknown action: {action}"}
        except Exception as e:
            self.handle_error(e, context=f"Error processing action '{action}'")
            return {"status": "error", "message": f"An internal error occurred while processing action '{action}'."}

    async def add_item(self, title: str, description: str) -> Dict[str, Any]:
        """Add a new item to the store."""
        import uuid
        from datetime import datetime
        
        item_id = str(uuid.uuid4())
        item_data = {
            "id": item_id,
            "title": title,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.items[item_id] = item_data
        self.logger.info(f"Item '{item_id}' added successfully.")
        self.metrics_collector.increment_counter("items_added_total")
        
        return {
            "status": "success",
            "message": "Item added successfully",
            "data": item_data
        }
    
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific item by ID."""
        if item_id in self.items:
            self.logger.debug(f"Item '{item_id}' retrieved.")
            self.metrics_collector.increment_counter("items_retrieved_total")
            return {
                "status": "success",
                "message": "Item retrieved",
                "data": self.items[item_id]
            }
        else:
            self.logger.warning(f"Attempted to retrieve non-existent item: {item_id}")
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
    
    async def update_item(self, item_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item."""
        from datetime import datetime
        
        if item_id not in self.items:
            self.logger.warning(f"Attempted to update non-existent item: {item_id}")
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        # Update fields from update_data
        for key, value in update_data.items():
            if key not in ["id", "created_at"]:  # Don't allow updating these fields
                self.items[item_id][key] = value
        
        self.items[item_id]["updated_at"] = datetime.utcnow().isoformat()
        self.logger.info(f"Item '{item_id}' updated successfully.")
        self.metrics_collector.increment_counter("items_updated_total")
        
        return {
            "status": "success",
            "message": "Item updated successfully",
            "data": self.items[item_id]
        }
    
    async def delete_item(self, item_id: str) -> Dict[str, Any]:
        """Delete an item by ID."""
        if item_id not in self.items:
            self.logger.warning(f"Attempted to delete non-existent item: {item_id}")
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        deleted_item = self.items.pop(item_id)
        self.logger.info(f"Item '{item_id}' deleted successfully.")
        self.metrics_collector.increment_counter("items_deleted_total")
        
        return {
            "status": "success",
            "message": "Item deleted successfully",
            "data": deleted_item
        }
    
    async def list_items(self) -> Dict[str, Any]:
        """List all items in the store."""
        items_list = list(self.items.values())
        self.logger.debug(f"Retrieved {len(items_list)} items from store.")
        self.metrics_collector.set_gauge("current_items_count", len(items_list))
        
        return {
            "status": "success",
            "message": f"Retrieved {len(items_list)} items",
            "data": items_list
        }

    async def setup(self):
        """Initialize component resources."""
        pass

    async def cleanup(self):
        """Clean up component resources."""
        pass

    def get_health_status(self) -> Dict[str, Any]:
        """Return component health status."""
        return {
            "healthy": True,
            "component": self.name,
            "status": "operational"
        }