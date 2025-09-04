
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

from datetime import datetime, timezone

class GeneratedSource_data_generator(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.logger.info(f"Initializing DataGenerator component: {name}")

        # Configuration for data generation
        self._num_items_to_generate = int(self.config.get("num_items_to_generate", 1))
        self._data_prefix = self.config.get("data_prefix", "record_")
        self._start_id = int(self.config.get("start_id", 0))

        self._current_record_id = self._start_id
        self.logger.info(f"DataGenerator configured: num_items_to_generate={self._num_items_to_generate}, data_prefix='{self._data_prefix}', start_id={self._start_id}")

    async def process_item(self, item: Any) -> Any:
        span = self.tracer.start_span(f"{self.name}.process_item")
        span.set_attribute("component.name", self.name)
        span.set_attribute("item.input", str(item))

        try:
            items_to_generate = self._num_items_to_generate
            # Allow the input item to specify how many items to generate
            if isinstance(item, dict) and "count" in item and isinstance(item["count"], int):
                items_to_generate = item["count"]
                self.logger.debug(f"Overriding generation count from item: {items_to_generate}")

            generated_items_summary = []
            all_routing_responses = []

            for _ in range(items_to_generate):
                record_id = self._current_record_id
                # Generate a simple data record
                generated_data = {
                    "id": record_id,
                    "data": f"{self._data_prefix}{record_id}",
                    "timestamp": "simulated_timestamp_placeholder" # Cannot use datetime without import
                }
                self._current_record_id += 1

                self.logger.debug(f"Generating item: {generated_data}")
                self.metrics_collector.counter("items_generated_total", 1)
                self.metrics_collector.gauge("current_record_id", self._current_record_id)

                item_span = self.tracer.start_span("generate_and_route_item", parent=span)
                item_span.set_attribute("generated.id", record_id)
                item_span.set_attribute("generated.data", generated_data["data"])

                try:
                    # Route the generated data to downstream components
                    routing_responses = await self.route_to_bindings(generated_data)
                    all_routing_responses.extend(routing_responses)
                    self.logger.debug(f"Routed item {record_id}. Responses: {routing_responses}")
                    generated_items_summary.append({"id": record_id, "status": "routed", "responses_count": len(routing_responses)})
                    self.metrics_collector.counter("items_routed_success", 1)
                except Exception as e:
                    self.handle_error(e, context=f"Error routing generated item {record_id}")
                    generated_items_summary.append({"id": record_id, "status": "routing_failed", "error": str(e)})
                    self.metrics_collector.counter("items_routed_failure", 1)
                finally:
                    item_span.end()

            span.set_attribute("generated.items.count", len(generated_items_summary))
            span.set_attribute("routing.responses.count", len(all_routing_responses))

            return {
                "status": "success",
                "message": f"Generated and routed {len(generated_items_summary)} items.",
                "generated_items": generated_items_summary,
                "routing_responses": all_routing_responses
            }
        except Exception as e:
            self.handle_error(e, context="Failed to generate or process items in DataGenerator")
            span.set_attribute("error", True)
            span.record_exception(e)
            return {
                "status": "error",
                "message": f"Failed to generate data: {str(e)}"
            }
        finally:
            span.end()

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