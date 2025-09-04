
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



class GeneratedTransformer_data_processor(ComposedComponent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.transformation_rule = config.get("transformation_rule", "default_rule")

    async def process_item(self, item: Any) -> Any:
        try:
            self.logger.info(f"Processing item: {item}")
            transformed_item = self.apply_transformation(item)
            self.metrics_collector.counter("items_processed", 1)
            response = await self.send_to_component("next_component", transformed_item)
            if response.get("status") == "error":
                self.handle_error(Exception(response["message"]), "Failed to send transformed item")
                return {"status": "error", "message": "Failed to process item"}
            return response.get("result")
        except Exception as e:
            self.handle_error(e, "Error processing item")
            return {"status": "error", "message": str(e)}

    def apply_transformation(self, item: Any) -> Any:
        # Example transformation logic based on the rule
        if self.transformation_rule == "default_rule":
            return {k: v.upper() for k, v in item.items()}  # Transform values to uppercase
        # Additional transformation rules can be added here
        return item  # Fallback to original item if no rule matches

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