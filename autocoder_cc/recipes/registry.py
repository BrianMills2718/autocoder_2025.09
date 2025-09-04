"""Registry of all component recipes.

Each recipe defines how to configure a primitive to act as a domain component.
"""
from typing import Dict, Any

RECIPE_REGISTRY = {
    "Store": {
        "base_primitive": "Transformer",
        "description": "Persistent storage component with CRUD operations",
        "ports": {
            "input": {"name": "in_commands", "type": "StoreCommand"},
            "output": {"name": "out_responses", "type": "StoreResponse"}
        },
        "config": {
            "storage_backend": "sqlite",
            "checkpoint_enabled": True,
            "idempotency_check": True
        },
        "imports": [
            "from datetime import datetime",
            "import sqlite3",
            "from typing import Dict, Any, Optional"
        ],
        "methods": {
            "transform": '''async def transform(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Store transformation logic."""
        # Check idempotency if enabled
        if self.config.get("idempotency_check") and "id" in command:
            if await self._is_duplicate(command["id"]):
                return None  # Drop duplicate
        
        # Process based on action
        action = command.get("action", "")
        if action == "add_item":
            result = await self._add_item(command)
        elif action == "get_item":
            result = await self._get_item(command)
        elif action == "list_items":
            result = await self._list_items(command)
        elif action == "delete_item":
            result = await self._delete_item(command)
        else:
            result = {"status": "error", "message": f"Unknown action: {action}"}
        
        # Return response
        return {
            "id": command.get("id"),
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }'''
        }
    },
    
    "Controller": {
        "base_primitive": "Splitter",
        "description": "Request routing controller that orchestrates operations",
        "ports": {
            "input": {"name": "in_requests", "type": "Request"},
            "outputs": {
                "out_to_store": {"type": "StoreCommand"},
                "out_to_validator": {"type": "ValidationRequest"},
                "out_responses": {"type": "Response"}
            }
        },
        "config": {
            "validate_input": True,
            "route_by_action": True,
            "max_retries": 3
        },
        "methods": {
            "split": '''async def split(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route requests to appropriate outputs."""
        outputs = {}
        
        # Validate if configured
        if self.config.get("validate_input"):
            if not self._validate_request(request):
                outputs["out_responses"] = {
                    "status": "error",
                    "message": "Invalid request format"
                }
                return outputs
        
        # Route by action
        action = request.get("action", "")
        if action in ["create", "update", "delete", "add_task", "add_item"]:
            outputs["out_to_store"] = {
                "action": action,
                "payload": request.get("payload", {}),
                "id": request.get("id")
            }
        elif action == "validate":
            outputs["out_to_validator"] = request.get("payload", {})
        elif action in ["get", "list", "get_all_tasks", "list_items"]:
            outputs["out_to_store"] = {
                "action": action,
                "payload": request.get("payload", {})
            }
        else:
            outputs["out_responses"] = {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
        
        return outputs'''
        }
    },
    
    "APIEndpoint": {
        "base_primitive": "Source",
        "description": "HTTP/REST API endpoint that generates requests from external sources",
        "ports": {
            "outputs": {
                "out_requests": {"type": "Request"},
                "out_errors": {"type": "Error"}
            }
        },
        "config": {
            "host": "localhost",
            "port": 8080,
            "auth_required": False,
            "rate_limit": 1000
        },
        "methods": {
            "generate": '''async def generate(self):
        """Generate requests from HTTP endpoints."""
        async for request in self._http_server():
            # Transform HTTP request to internal format
            internal_request = {
                "method": request.method,
                "path": request.path,
                "body": request.body,
                "headers": request.headers,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Route based on path and method
            if request.path.startswith("/todos"):
                if request.method == "POST":
                    yield {"action": "add_task", "payload": request.body}
                elif request.method == "GET":
                    yield {"action": "get_all_tasks", "payload": {}}
                elif request.method == "DELETE":
                    task_id = request.path.split("/")[-1]
                    yield {"action": "delete_task", "payload": {"id": task_id}}
            else:
                yield {"error": f"Unknown endpoint: {request.path}"}'''
        }
    },
    
    "Filter": {
        "base_primitive": "Transformer",
        "description": "Filters messages based on conditions",
        "ports": {
            "input": {"name": "in_messages", "type": "Message"},
            "output": {"name": "out_filtered", "type": "Message"}
        },
        "config": {
            "filter_conditions": [],
            "transformation_rules": [],
            "drop_on_error": False
        },
        "methods": {
            "transform": '''async def transform(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and optionally transform messages."""
        # Evaluate filter conditions
        for condition in self.config.get("filter_conditions", []):
            if not self._evaluate_condition(condition, message):
                return None  # Drop message
        
        # Apply transformations
        transformed = message.copy()
        for rule in self.config.get("transformation_rules", []):
            transformed = self._apply_transformation(rule, transformed)
        
        return transformed'''
        }
    },
    
    "Router": {
        "base_primitive": "Splitter", 
        "description": "Routes messages to different paths based on rules",
        "ports": {
            "input": {"name": "in_messages", "type": "Message"},
            "outputs": {
                "route_a": {"type": "Message"},
                "route_b": {"type": "Message"},
                "default": {"type": "Message"}
            }
        },
        "config": {
            "routing_rules": [],
            "default_route": "default"
        },
        "methods": {
            "split": '''async def split(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route message based on rules."""
        outputs = {}
        
        # Evaluate routing rules
        for rule in self.config.get("routing_rules", []):
            if self._matches_rule(rule, message):
                route = rule.get("route", "default")
                outputs[route] = message
                return outputs
        
        # Default route
        default = self.config.get("default_route", "default")
        outputs[default] = message
        return outputs'''
        }
    },
    
    "Aggregator": {
        "base_primitive": "Merger",
        "description": "Combines multiple inputs into single output",
        "ports": {
            "inputs": {
                "in_stream_1": {"type": "Data"},
                "in_stream_2": {"type": "Data"},
                "in_stream_3": {"type": "Data"}
            },
            "output": {"name": "out_aggregated", "type": "AggregatedData"}
        },
        "config": {
            "aggregation_strategy": "combine",  # combine, average, sum, etc.
            "buffer_size": 10,
            "timeout_ms": 1000
        },
        "methods": {
            "merge": '''async def merge(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple items based on strategy."""
        strategy = self.config.get("aggregation_strategy", "combine")
        
        if strategy == "combine":
            # Combine all items into one
            result = {}
            for item in items:
                result.update(item)
            return result
        elif strategy == "average":
            # Average numeric values
            return self._average_items(items)
        elif strategy == "sum":
            # Sum numeric values
            return self._sum_items(items)
        else:
            # Default: return last item
            return items[-1] if items else {}'''
        }
    },
    
    "WebSocket": {
        "base_primitive": "Source",
        "description": "WebSocket connection handler for bidirectional streaming",
        "ports": {
            "outputs": {
                "out_messages": {"type": "WSMessage"},
                "out_events": {"type": "WSEvent"}
            }
        },
        "config": {
            "url": "ws://localhost:8080/ws",
            "reconnect": True,
            "heartbeat_interval": 30
        }
    },
    
    "MessageBus": {
        "base_primitive": "Splitter",
        "description": "Pub/sub message bus for event distribution",
        "ports": {
            "input": {"name": "in_events", "type": "Event"},
            "outputs": {
                # Dynamic outputs based on subscriptions
            }
        },
        "config": {
            "topics": [],
            "persistent": False,
            "max_queue_size": 1000
        }
    },
    
    "Accumulator": {
        "base_primitive": "Transformer",
        "description": "Stateful aggregation of data over time windows",
        "ports": {
            "input": {"name": "in_data", "type": "Data"},
            "output": {"name": "out_accumulated", "type": "AccumulatedData"}
        },
        "config": {
            "window_size": 100,
            "window_type": "count",  # count, time, sliding
            "aggregation": "sum"
        }
    },
    
    "StreamProcessor": {
        "base_primitive": "Transformer",
        "description": "Processes streaming data with stateful operations",
        "ports": {
            "input": {"name": "in_stream", "type": "StreamData"},
            "output": {"name": "out_processed", "type": "ProcessedData"}
        },
        "config": {
            "batch_size": 100,
            "processing_mode": "micro-batch",  # micro-batch, continuous
            "checkpoint_interval": 60
        }
    },
    
    "CommandHandler": {
        "base_primitive": "Transformer",
        "description": "CQRS command processing component",
        "ports": {
            "input": {"name": "in_commands", "type": "Command"},
            "output": {"name": "out_events", "type": "Event"}
        },
        "config": {
            "command_types": [],
            "validation_strict": True,
            "event_sourcing": False
        }
    },
    
    "QueryHandler": {
        "base_primitive": "Transformer",
        "description": "CQRS query processing component",
        "ports": {
            "input": {"name": "in_queries", "type": "Query"},
            "output": {"name": "out_results", "type": "QueryResult"}
        },
        "config": {
            "query_types": [],
            "cache_enabled": True,
            "cache_ttl": 300
        }
    },
    
    "Model": {
        "base_primitive": "Transformer",
        "description": "Business logic and data processing model",
        "ports": {
            "input": {"name": "in_data", "type": "ModelInput"},
            "output": {"name": "out_result", "type": "ModelOutput"}
        },
        "config": {
            "model_type": "business_logic",
            "validation_rules": [],
            "processing_rules": []
        }
    }
}

def get_recipe(name: str) -> Dict[str, Any]:
    """Get a recipe by name.
    
    Args:
        name: Recipe name (e.g., "Store", "Controller")
        
    Returns:
        Recipe dictionary
        
    Raises:
        ValueError: If recipe not found
    """
    if name not in RECIPE_REGISTRY:
        available = ", ".join(RECIPE_REGISTRY.keys())
        raise ValueError(f"Unknown recipe: {name}. Available: {available}")
    return RECIPE_REGISTRY[name]

def list_recipes() -> list[str]:
    """List all available recipe names."""
    return list(RECIPE_REGISTRY.keys())