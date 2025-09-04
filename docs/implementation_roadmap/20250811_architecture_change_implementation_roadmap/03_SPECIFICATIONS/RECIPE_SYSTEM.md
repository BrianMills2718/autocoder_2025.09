# Recipe System Specification

✅ **CURRENT STATUS: RECIPE SYSTEM EXISTS BUT NOT INTEGRATED**
- **RecipeExpander class EXISTS** at `autocoder_cc/recipes/expander.py` (231 lines)
- **Recipe registry EXISTS** at `autocoder_cc/recipes/registry.py` (376 lines)
- **13 recipes defined and working**
- **❌ NOT integrated with system_generator.py** (needs ~30-50 LOC change)

*Consolidated from: RECIPE_SYSTEM.md and RECIPE_EXPANSION.md*
*Status: BUILT BUT NOT INTEGRATED - Needs Phase 2 integration*

## The Vision (Not Reality)

The recipe system would convert 13 domain component types into configurations of 5 mathematical primitives. Instead of maintaining 13 separate component classes (~10,000 lines), we would have 5 primitives (~1,000 lines) plus 13 recipes (configuration).

## The 5 Mathematical Primitives (DON'T EXIST YET)

```python
# These classes need to be created in autocoder_cc/components/primitives/
class Source(PortBasedComponent):      # 0→N ports: generates data
class Sink(PortBasedComponent):        # N→0 ports: consumes data  
class Transformer(PortBasedComponent): # 1→{0..1} ports: transforms data (may drop)
class Splitter(PortBasedComponent):    # 1→N ports: distributes data
class Merger(PortBasedComponent):      # N→1 ports: combines data
```

### Transformer Drop Semantics (1→{0..1})

**Decision**: Transformers can drop messages by returning None, with strict guardrails:

```python
class Transformer(PortBasedComponent):
    def __init__(self, require_output: bool = False):
        self.require_output = require_output
    
    async def transform(self, item: T) -> Optional[U]:
        """Transform input item. Return None to drop."""
        # Implementation must handle Optional return type
        pass
    
    async def on_drop(self, item: T, reason: str):
        """Called when item is dropped. Log for observability."""
        pass

# Guardrails:
# - Type system enforces Optional[U] return type
# - Metrics separate messages_dropped_total from errors_total  
# - require_output=True raises DropForbiddenError on None
# - Drop reasons logged for debugging
```

**Recipe Defaults**:
- Validators/Filters: require_output=False (can drop)
- Business Transformers: require_output=True (must output)

## Recipe Registry (EXISTS - Reference Implementation)

The recipe registry exists at `autocoder_cc/recipes/registry.py` (376 lines). Here's the reference structure:

```python
# REFERENCE: This shows the registry structure from autocoder_cc/recipes/registry.py
RECIPE_REGISTRY = {
    "Store": {
        "base_primitive": "Transformer",
        "description": "Persistent storage component",
        "ports": {
            "input": {"name": "in_commands", "type": "StoreCommand"},
            "output": {"name": "out_responses", "type": "StoreResponse"}
        },
        "config": {
            "storage_backend": "sqlite",
            "persistent": True,  # Capability flag, not trait
            "idempotent": True,  # Capability flag, not trait
            "checkpoint_enabled": True,
            "require_output": True  # Business transformer - must output
        },
        "transform_method": '''
async def transform(self, command):
    """Store transformation logic."""
    if self.config.get("idempotency_check"):
        if await self.is_duplicate(command.id):
            return None
    
    result = await self.persist(command)
    return {
        "id": command.id,
        "status": "success",
        "result": result
    }
'''
    },
    
    "Controller": {
        "base_primitive": "Splitter",
        "description": "Request routing controller",
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
            "route_by_action": True
        },
        "split_method": '''
async def split(self, request):
    """Route requests to appropriate outputs."""
    if request.action in ["create", "update", "delete"]:
        return {"out_to_store": {"action": request.action, "payload": request.payload}}
    elif request.action == "validate":
        return {"out_to_validator": request.payload}
    else:
        return {"out_responses": {"status": "error", "message": "Unknown action"}}
'''
    },
    
    "APIEndpoint": {
        "base_primitive": "Source",
        "ports": {"output": {"name": "out_requests", "type": "HTTPRequest"}},
        "config": {"port": 8080, "rate_limit": 100}
    },
    
    "MessageQueue": {
        "base_primitive": "Transformer",
        "config": {"buffer_size": 10000, "ordering": "FIFO"}
    },
    
    "Aggregator": {
        "base_primitive": "Merger",
        "config": {"window_size": 60, "aggregation_function": "sum"}
    },
    
    "Filter": {
        "base_primitive": "Transformer",
        "config": {"filter_conditions": [], "transformation_rules": []}
    },
    
    "Router": {
        "base_primitive": "Splitter",
        "config": {"routing_rules": [], "default_route": "error"}
    },
    
    "Cache": {
        "base_primitive": "Transformer",
        "config": {"ttl": 3600, "max_size": 1000}
    },
    
    "Validator": {
        "base_primitive": "Transformer",
        "description": "Input validation with drop capability",
        "ports": {
            "input": {"name": "in_data", "type": "Any"},
            "output": {"name": "out_validated", "type": "Any"}
        },
        "config": {
            "validation_schema": {},
            "strict_mode": True,
            "require_output": False  # Can drop invalid messages
        },
        "transform_method": '''
async def transform(self, item):
    """Validate input. Return None to drop invalid items."""
    if not self.validate(item):
        await self.on_drop(item, "validation_failed")
        return None  # Drop invalid message
    return item  # Pass through valid message
'''
    },
    
    "Logger": {
        "base_primitive": "Sink",
        "config": {"log_level": "INFO", "output": "stdout"}
    },
    
    "MetricsCollector": {
        "base_primitive": "Sink",
        "config": {"collection_interval": 60, "export_format": "prometheus"}
    },
    
    "WebSocket": {
        "base_primitive": "Source",
        "config": {"port": 8081, "heartbeat_interval": 30}
    },
    
    "StreamProcessor": {
        "base_primitive": "Transformer",
        "config": {"batch_size": 100, "processing_interval": 1000}
    }
}
```

## Recipe Expander (EXISTS - Needs Integration)

The RecipeExpander exists at `autocoder_cc/recipes/expander.py` (231 lines) but needs integration with system_generator.py:

```python
# REFERENCE: From autocoder_cc/recipes/expander.py
class RecipeExpander:
    """Expands recipes into full component implementations."""
    
    def expand_recipe(self, recipe_name: str, component_name: str, config: Dict[str, Any]) -> str:
        """
        Expand a recipe into full component code.
        
        This method must:
        1. Load recipe from registry
        2. Merge provided config with recipe defaults
        3. Generate appropriate imports
        4. Create class inheriting from base primitive
        5. Add port configuration
        6. Include method implementations
        7. Return complete Python code as string
        """
        # Implementation needed
        pass
```

## Generator Integration (REQUIRED CHANGES)

The system_generator.py needs modification (currently has ZERO recipe awareness):

```python
# In autocoder_cc/blueprint_language/system_generator.py
# ADD these changes:

from autocoder_cc.recipes import RecipeExpander  # After creating recipes module

class SystemGenerator:
    def __init__(self):
        self.recipe_expander = RecipeExpander()  # ADD THIS
        # ... existing init code
    
    def generate_component(self, spec):
        # ADD THIS CHECK:
        if "recipe" in spec:
            return self.recipe_expander.expand_recipe(
                spec["recipe"],
                spec["name"],
                spec.get("config", {})
            )
        
        # ... existing generation logic for non-recipe components
```

## Blueprint Usage (AFTER IMPLEMENTATION)

Once implemented, blueprints could use recipes like:

```yaml
schema_version: "2.0.0"
system:
  name: "todo_system"
  components:
    - name: "todo_store"
      recipe: "Store"  # Uses Store recipe
      config:
        storage_backend: "postgresql"
        
    - name: "todo_controller"
      recipe: "Controller"  # Uses Controller recipe
      config:
        validate_input: true
        
    - name: "todo_api"
      recipe: "APIEndpoint"  # Uses APIEndpoint recipe
      config:
        port: 8080
```

## Implementation Requirements

### What Must Be Built:
1. **Primitives** (~/1000 lines)
   - Create `autocoder_cc/components/primitives/` directory
   - Implement Source, Sink, Transformer, Splitter, Merger

2. **Recipe System** (~500 lines)
   - Create `autocoder_cc/recipes/` directory
   - Implement RECIPE_REGISTRY with all 13 recipes
   - Implement RecipeExpander class

3. **Generator Integration** (~50 lines)
   - Modify system_generator.py
   - Add recipe awareness
   - Test recipe-based generation

4. **Templates** (~500 lines)
   - Create expansion templates
   - Port configuration templates
   - Method implementation templates

## Benefits (IF IMPLEMENTED)

1. **Code Reduction**: 10,000 lines → 2,000 lines (80% reduction)
2. **Maintenance**: Update 5 primitives instead of 13 components
3. **Testing**: Test 5 primitives thoroughly vs 13 components
4. **Flexibility**: Change behavior through configuration
5. **Consistency**: All components follow same patterns

## Current Reality Check

- **Documentation**: 1000+ lines ✅
- **Implementation**: 0 lines ❌
- **Integration**: 0% ❌
- **Testing**: 0% ❌
- **Usability**: 0% ❌

## Summary

The recipe system is a well-designed architectural pattern that would provide significant benefits. However, it currently exists only in documentation. Before the port-based architecture can work, this entire system must be built from scratch, including primitives, recipe registry, expander, and generator integration.

**Time Estimate**: 3-5 days to implement completely
**Priority**: CRITICAL - Cannot proceed without this
**Complexity**: Medium - Clear design, straightforward implementation

---
> **📊 Status Note**: Status facts in this document are **non-authoritative**. See [06_DECISIONS/STATUS_SOT.md](06_DECISIONS/STATUS_SOT.md) for the single source of truth.
