# Port vs Stream & Recipe System - Complete Design Document

*Created: 2025-08-10*
*Purpose: Definitive specification for ports, streams, and recipes*

## Executive Summary

This document provides the complete design for two critical architectural components:
1. **Ports vs Streams**: How typed interfaces wrap transport mechanisms
2. **Recipe System**: How 13 domain types become 5 mathematical primitives

## Part 1: Port vs Stream Architecture

### The Core Concept

**Stream**: The transport layer that moves data
**Port**: The contract layer that validates data

Think of it like networking:
- **Stream = TCP**: Just moves bytes, doesn't care what they mean
- **Port = HTTP**: Defines structure, headers, methods, validation

### Current State (What Exists)

```python
# In harness.py line 797 - THIS ALREADY EXISTS
send_stream, receive_stream = anyio.create_memory_object_stream(max_buffer_size=1000)

# Components already have these
class Component:
    def __init__(self):
        self.receive_streams = {}  # Dict of anyio streams
        self.send_streams = {}     # Dict of anyio streams
```

The streams ALREADY EXIST and WORK. We're just adding a typed wrapper.

### New Port Layer (What We're Adding)

```python
from typing import TypeVar, Generic, Type
from pydantic import BaseModel
import anyio

T = TypeVar('T', bound=BaseModel)

class Port(Generic[T]):
    """
    A PORT is a typed, validated interface to a stream.
    It enforces contracts that streams don't care about.
    """
    
    def __init__(self, 
                 name: str,
                 schema: Type[T],
                 stream: anyio.abc.ObjectStream = None):
        self.name = name
        self.schema = schema  # Pydantic model for validation
        self.stream = stream  # The underlying anyio stream
    
    async def send(self, data: T) -> None:
        """Send data with type validation"""
        # Validate against schema
        if not isinstance(data, self.schema):
            try:
                # Try to coerce to correct type
                data = self.schema(**data) if isinstance(data, dict) else self.schema(data)
            except Exception as e:
                raise PortValidationError(f"Port {self.name}: {e}")
        
        # Send through underlying stream
        await self.stream.send(data)
    
    async def receive(self) -> T:
        """Receive data with type guarantee"""
        # Get from stream
        raw_data = await self.stream.receive()
        
        # Validate and return typed data
        if not isinstance(raw_data, self.schema):
            raw_data = self.schema(**raw_data) if isinstance(raw_data, dict) else self.schema(raw_data)
        
        return raw_data
```

### Why Both Exist

**Streams handle:**
- Moving data between components
- Buffering (backpressure)
- Async communication
- Memory management

**Ports add:**
- Type safety (Pydantic schemas)
- Validation (data correctness)
- Contract enforcement (behavioral rules)
- Semantic meaning (what the data represents)

### Real Example

```python
# Define the data schema
class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False

# Without ports (current system) - NO VALIDATION
stream = anyio.create_memory_object_stream()
await stream[0].send({"id": "not_an_int", "title": 123})  # Wrong types, but works!

# With ports (new system) - ENFORCED VALIDATION
port = Port(name="todo_input", schema=TodoItem, stream=stream[0])
await port.send({"id": "not_an_int", "title": 123})  # FAILS! Type error caught

# The port ensures only valid TodoItems flow through
await port.send({"id": 1, "title": "Buy milk"})  # Success - valid schema
```

### Implementation Strategy

```python
class PortBasedComponent:
    """New base class using ports instead of raw streams"""
    
    def __init__(self):
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, Port] = {}
        
        # Under the hood, ports wrap streams
        # But components only interact with ports
    
    def add_input_port(self, name: str, schema: Type[BaseModel]):
        """Add typed input port"""
        stream = None  # Will be wired by harness
        self.input_ports[name] = Port(name, schema, stream)
    
    def add_output_port(self, name: str, schema: Type[BaseModel]):
        """Add typed output port"""
        stream = None  # Will be wired by harness
        self.output_ports[name] = Port(name, schema, stream)
    
    async def process(self):
        """Process using typed ports"""
        # Receive typed data
        data: TodoItem = await self.input_ports["main"].receive()
        
        # Process with type safety
        result = self.transform(data)
        
        # Send typed result
        await self.output_ports["main"].send(result)
```

### Base Class Requirements & Inheritance Strategy

#### Current State Analysis
Multiple competing base class definitions exist:
1. `/orchestration/component.py` - The canonical base Component class
2. `/components/composed_base.py` - ComposedComponent that extends Component
3. Generated components import from `observability` (wrong path - causes failures)
4. Multiple conflicting implementations across codebase

#### The Core Requirements
**What components MUST implement to work with SystemExecutionHarness:**

```python
# Required methods for harness integration
class Component(ABC):
    @abstractmethod
    async def setup(self):
        """Initialize component resources"""
        pass
    
    @abstractmethod
    async def process(self):
        """Main processing logic"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass
```

#### Stream Connection Pattern
Streams are attached via harness injection:
```python
# Harness creates streams (line 797)
send_stream, receive_stream = anyio.create_memory_object_stream(max_buffer_size)

# Then connects to component
component.receive_streams[stream_name] = receive_stream
component.send_streams[stream_name] = send_stream
```

#### Inheritance Options Evaluated

**Option 1: Raw Component Base**
```python
from autocoder_cc.orchestration.component import Component

class MyComponent(Component):
    async def setup(self): pass
    async def process(self): pass
    async def cleanup(self): pass
```
- ✅ Simplest inheritance chain
- ❌ Missing observability features

**Option 2: ComposedComponent**
```python
from autocoder_cc.components.composed_base import ComposedComponent

class MyComponent(ComposedComponent):
    async def process_item(self, item): pass
```
- ✅ Built-in observability (metrics, tracing, logging)
- ❌ Extra abstraction layer, multiple conflicting definitions

**Option 3: New PortBasedComponent (CHOSEN)**
```python
from autocoder_cc.components.port_based import PortBasedComponent

class MyComponent(PortBasedComponent):
    def configure_ports(self):
        self.add_input_port("in", DataSchema)
        self.add_output_port("out", ResultSchema)
```
- ✅ Clean slate with port-based design
- ✅ Type safety built-in
- ✅ Future-proof architecture
- ✅ Designed-in observability

#### Configuration Pattern
Configuration passed via constructor and stored:
```python
class PortBasedComponent:
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.configure_ports()  # Subclasses define ports here
```

#### Critical Import Fix Required
```python
# WRONG (causes 100% failures):
from observability import ComposedComponent

# CORRECT:
from autocoder_cc.components.port_based import PortBasedComponent
```

#### Observability Integration
PortBasedComponent will include observability:
```python
class PortBasedComponent:
    def __init__(self, name, config):
        # ... port setup ...
        self.metrics = MetricsCollector(name)
        self.tracer = Tracer(name)
        self.logger = get_logger(name)
    
    async def process(self):
        with self.tracer.span("process"):
            self.metrics.increment("items_processed")
            # ... actual processing ...
```

## Part 2: Recipe System Design

### The Problem We're Solving

**Current**: 13 hardcoded component types (Store, Controller, APIEndpoint, Router, Filter, Aggregator, etc.)
**Goal**: 5 mathematical primitives that can express everything

### What Are Recipes?

**Recipes are NOT new component types.**
**Recipes are CONFIGURATIONS that tell the 5 base types how to behave.**

Think of it like this:
- A "car" isn't a fundamental thing
- It's wheels + engine + chassis configured a certain way
- A "truck" uses the same parts configured differently

Similarly:
- A "Store" isn't a fundamental component
- It's a Transformer + persistence configuration
- A "Controller" is a Transformer + orchestration configuration

### The 5 Fundamental Types (Mathematical Primitives)

```python
class Source:
    """Generates data: () → Stream[T]"""
    # No input ports, one or more output ports
    # Examples: API endpoint, file reader, timer, sensor

class Sink:
    """Consumes data: Stream[T] → ()"""
    # One or more input ports, no output ports
    # Examples: Database writer, file writer, API caller

class Transformer:
    """Transforms data: Stream[T] → Stream[U]"""
    # One input port, one output port
    # Examples: Parser, validator, enricher, calculator

class Splitter:
    """Splits data: Stream[T] → (Stream[T], Stream[T], ...)"""
    # One input port, multiple output ports
    # Examples: Router, broadcaster, load balancer

class Merger:
    """Merges data: (Stream[T], Stream[U], ...) → Stream[V]"""
    # Multiple input ports, one output port
    # Examples: Aggregator, combiner, multiplexer
```

### How Recipes Work

```python
# Recipe Definition
class Recipe:
    """A recipe is a reusable configuration pattern"""
    
    def __init__(self, 
                 base_type: str,           # Which of the 5 primitives
                 traits: Dict[str, Any],   # Behavioral modifications
                 contracts: List[str],     # Required guarantees
                 code_template: str):      # Code generation pattern
        self.base_type = base_type
        self.traits = traits
        self.contracts = contracts
        self.code_template = code_template

# Recipe Library (Replaces 13 Component Types)
RECIPE_LIBRARY = {
    "Store": Recipe(
        base_type="Transformer",  # A Store IS a Transformer
        traits={
            "persistent": True,    # It persists data
            "queryable": True,     # It can be queried
            "indexed": True        # It maintains indexes
        },
        contracts=[
            "idempotent",         # Same operation twice = same result
            "deterministic"       # Same input = same output
        ],
        code_template="""
        async def process(self, data):
            # Store pattern: persist then acknowledge
            key = await self.database.save(data)
            return {"status": "stored", "key": key}
        """
    ),
    
    "Controller": Recipe(
        base_type="Transformer",  # A Controller IS a Transformer
        traits={
            "orchestrator": True,  # It orchestrates other components
            "stateful": True,      # It maintains state
            "retryable": True      # It retries on failure
        },
        contracts=[
            "at_least_once",      # Guarantees delivery
            "timeout_ms:5000"     # Times out after 5 seconds
        ],
        code_template="""
        async def process(self, request):
            # Controller pattern: orchestrate multiple operations
            operations = self.plan_operations(request)
            results = await self.execute_parallel(operations)
            return self.aggregate_results(results)
        """
    ),
    
    "APIEndpoint": Recipe(
        base_type="Source",       # An API IS a Source
        traits={
            "http": True,          # It speaks HTTP
            "authenticated": True, # It requires auth
            "rate_limited": True   # It has rate limits
        },
        contracts=[
            "stateless",          # No state between requests
            "timeout_ms:30000"    # 30 second timeout
        ],
        code_template="""
        async def generate(self):
            # API pattern: receive HTTP, validate, emit
            while self.running:
                request = await self.http_server.receive()
                if self.validate_auth(request):
                    await self.output_port.send(request)
        """
    )
}
```

### How Recipes Generate Components

```python
def generate_component_from_recipe(recipe_name: str, instance_name: str, config: Dict) -> str:
    """Generate Python code for a component using a recipe"""
    
    recipe = RECIPE_LIBRARY[recipe_name]
    
    # Start with the base type
    code = f"""
from autocoder_cc.components.{recipe.base_type.lower()} import {recipe.base_type}

class {instance_name}({recipe.base_type}):
    '''Generated from {recipe_name} recipe'''
    
    def __init__(self, config):
        super().__init__(config)
        # Apply recipe traits
        {generate_trait_setup(recipe.traits)}
    
    {recipe.code_template}
"""
    return code

# EXAMPLE: Generate a Store component
store_code = generate_component_from_recipe(
    recipe_name="Store",
    instance_name="UserStore", 
    config={"database_url": "postgresql://..."}
)
# Result: A Transformer that acts like a Store
```

### Why This Is Better Than 13 Types

**Before (13 types):**
```python
# Validation needs to know about 13 different component types
# Each type has different rules
if isinstance(component, Store):
    validate_store_rules()
elif isinstance(component, Controller):
    validate_controller_rules()
elif isinstance(component, APIEndpoint):
    validate_api_rules()
# ... 10 more cases
```

**After (5 types + recipes):**
```python
# Validation only needs to know 5 types
# Recipes are just configuration
if isinstance(component, Transformer):
    validate_transformer_rules()  # Works for Store, Controller, etc.
elif isinstance(component, Source):
    validate_source_rules()       # Works for APIEndpoint, Timer, etc.
# ... only 3 more cases

# The recipe's contracts are validated separately
validate_contracts(component.contracts)  # Same for all components
```

### How Recipes Are Applied

**Option 1: Compile-Time Expansion (RECOMMENDED)**
```python
# At blueprint parse time, expand recipes into base components
blueprint = parse_blueprint("system.yaml")
for component in blueprint.components:
    if component.type in RECIPE_LIBRARY:
        # It's a recipe, expand it
        recipe = RECIPE_LIBRARY[component.type]
        component.type = recipe.base_type  # Now it's a base type
        component.traits = recipe.traits
        component.contracts = recipe.contracts
        component.code_template = recipe.code_template
```

**Option 2: Runtime Composition (Alternative)**
```python
# At runtime, recipes modify behavior
class RecipeComponent(Transformer):
    def __init__(self, recipe_name: str):
        recipe = RECIPE_LIBRARY[recipe_name]
        self.apply_traits(recipe.traits)
        self.enforce_contracts(recipe.contracts)
```

## Part 3: Wiring - Why No Order?

You're absolutely right - there is NO order to wiring! I was confused.

### How Wiring Actually Works

```yaml
# Blueprint declares all connections simultaneously
bindings:
  - from: component_a.output
    to: component_b.input
  - from: component_b.output
    to: component_c.input
  - from: component_a.output2
    to: component_d.input
```

These are all wired **simultaneously** by the harness:

```python
class WiringHarness:
    def wire_components(self, bindings):
        """Wire all components according to blueprint"""
        # Create all connections at once
        for binding in bindings:
            # Create stream
            send_stream, receive_stream = anyio.create_memory_object_stream()
            
            # Get components
            from_component = self.get_component(binding.from_component)
            to_component = self.get_component(binding.to_component)
            
            # Connect ports through streams
            from_component.output_ports[binding.from_port].stream = send_stream
            to_component.input_ports[binding.to_port].stream = receive_stream
        
        # All wired simultaneously - no order!
```

### Why I Was Confused About Order

I mistakenly thought about the order of WRITING component code. But you're right:
1. Components are generated in isolation (could be parallel)
2. Blueprint declares all connections
3. Harness wires everything simultaneously
4. No order exists or matters

## Part 4: Integration Testing Philosophy

You're right - the goal is to make integration testing nearly redundant through complete blueprint specification.

### What Blueprint Should Specify (Making Integration Tests Redundant)

```yaml
components:
  user_store:
    type: Store  # Recipe name
    contracts:
      - idempotent
      - preserves_order
      - timeout_ms:1000
    ports:
      input:
        schema: UserData
        validation: strict
      output:
        schema: StorageResult
    
  user_controller:
    type: Controller
    contracts:
      - at_least_once
      - retry_count:3
    
bindings:
  - from: user_controller.output
    to: user_store.input
    contract: 
      - ordered        # Preserve order
      - no_loss       # No messages lost
      - backpressure  # Handle overload
```

With this level of specification, integration tests become trivial:

```python
async def integration_test(system):
    """Almost redundant - just verify blueprint was followed"""
    # Send one test message
    await system.input.send(test_data)
    
    # Did it come out?
    result = await system.output.receive(timeout=1)
    assert result is not None
    
    # That's it - blueprint guarantees everything else
```

## Summary

### Ports vs Streams
- **Streams**: Already exist, handle transport (anyio.MemoryObjectStream)
- **Ports**: New addition, handle contracts (type validation, schemas)
- **Relationship**: Port wraps Stream, adds validation layer

### Recipe System
- **Not new component types**: Just configuration patterns
- **5 base types only**: Source, Sink, Transformer, Splitter, Merger
- **Recipes**: Tell base types how to behave like domain components
- **Benefit**: Validation only needs to understand 5 types, not 13

### Wiring
- **No order**: Everything wired simultaneously from blueprint
- **Declarative**: Blueprint declares connections, harness implements
- **Parallel safe**: Components generated in isolation

### Integration Testing
- **Goal**: Make it redundant through complete blueprint specification
- **Reality**: Keep minimal smoke test for "unknown unknowns"
- **Future**: As blueprint language improves, tests become more redundant

This is the complete design. The system is simpler than it seemed - just 5 types + configuration.

## Part 5: Recipe System Complexity Concerns

### Recipe Conflict Resolution

**Problem**: What if two recipes want different base types for similar functionality?

**Solution**: Recipes don't conflict because they're just templates. Each recipe has a unique name and clear purpose:
```python
# These are different recipes, not conflicts
RECIPE_LIBRARY = {
    "PersistentStore": Recipe(base_type="Transformer", ...),  # Uses Transformer
    "EventStore": Recipe(base_type="Sink", ...),              # Uses Sink
    "CacheStore": Recipe(base_type="Merger", ...)             # Uses Merger
}
# User chooses which recipe fits their needs
```

### Recipe Versioning and Evolution

**Strategy**: Semantic versioning with compatibility guarantees
```python
class Recipe:
    def __init__(self, version: str = "1.0.0", ...):
        self.version = version
        self.deprecated_in = None
        self.removed_in = None
        
RECIPE_LIBRARY = {
    "Store": Recipe(version="1.0.0", ...),
    "Store_v2": Recipe(version="2.0.0", ...),  # New version with different behavior
}

# Migration path
def migrate_recipe(old_recipe: str, new_recipe: str, config: Dict) -> Dict:
    """Migrate configuration from old recipe to new"""
    pass
```

### Recipe Validation Timing

**Blueprint-time validation** (Preferred):
```python
def validate_blueprint(blueprint):
    for component in blueprint.components:
        if component.type in RECIPE_LIBRARY:
            recipe = RECIPE_LIBRARY[component.type]
            # Validate recipe can be applied
            if recipe.base_type not in SUPPORTED_BASE_TYPES:
                raise ValidationError(f"Recipe {component.type} uses unsupported base")
            # Validate configuration matches recipe requirements
            validate_recipe_config(recipe, component.config)
```

**Runtime validation** (Fallback):
```python
class RecipeComponent:
    def __init__(self, recipe_name: str):
        if recipe_name not in RECIPE_LIBRARY:
            raise RuntimeError(f"Unknown recipe: {recipe_name}")
        # Apply recipe
```

### Performance Impact of Recipe Indirection

**Concern**: Does recipe indirection add overhead?

**Answer**: NO - recipes are expanded at generation time, not runtime
```python
# AT GENERATION TIME (no runtime overhead)
def generate_component(blueprint_component):
    if blueprint_component.type in RECIPE_LIBRARY:
        # Expand recipe into concrete code
        recipe = RECIPE_LIBRARY[blueprint_component.type]
        return generate_from_base_type(recipe.base_type, recipe.traits)
    
# GENERATED CODE (no recipe reference)
class UserStore(Transformer):  # Direct inheritance, no indirection
    def __init__(self):
        # Concrete implementation, no recipe lookup
        pass
```

## Part 6: Port Buffer Management

### Buffer Overflow Strategy

**Default**: Backpressure (sender blocks when buffer full)
```python
class Port:
    def __init__(self, buffer_size: int = 1000):
        self.stream = anyio.create_memory_object_stream(max_buffer_size=buffer_size)
    
    async def send(self, data):
        # Will block if buffer full (backpressure)
        await self.stream.send(data)
```

**Alternative**: Drop oldest (ring buffer)
```python
class RingBufferPort(Port):
    async def send(self, data):
        if self.stream.statistics().current_buffer_used >= self.max_buffer:
            # Drop oldest
            try:
                self.stream.receive_nowait()  # Remove one
            except anyio.WouldBlock:
                pass
        await self.stream.send(data)
```

### Slow Consumer Handling

**Options configured per port**:
```yaml
ports:
  high_priority:
    buffer_size: 100
    overflow_policy: block  # Backpressure (default)
  
  low_priority:
    buffer_size: 1000
    overflow_policy: drop_oldest  # Ring buffer
  
  critical:
    buffer_size: 10000
    overflow_policy: spill_to_disk  # Overflow to temp file
```

### Dead Letter Queue

**Implementation**: Failed messages go to error port
```python
class PortWithDLQ(Port):
    def __init__(self, dlq_port: Port = None):
        super().__init__()
        self.dlq_port = dlq_port
        self.max_retries = 3
    
    async def send_with_retry(self, data):
        retries = 0
        while retries < self.max_retries:
            try:
                await self.send(data)
                return
            except Exception as e:
                retries += 1
                if retries >= self.max_retries and self.dlq_port:
                    # Send to dead letter queue
                    await self.dlq_port.send({
                        "original_data": data,
                        "error": str(e),
                        "timestamp": datetime.now()
                    })
                    return
```

### Dynamic Buffer Sizing

**Adaptive strategy based on flow rate**:
```python
class AdaptivePort(Port):
    async def auto_resize(self):
        """Monitor and adjust buffer size"""
        while True:
            stats = self.stream.statistics()
            utilization = stats.current_buffer_used / self.buffer_size
            
            if utilization > 0.9:  # 90% full
                # Increase buffer
                self.resize_buffer(self.buffer_size * 2)
            elif utilization < 0.1:  # 10% full
                # Decrease buffer
                self.resize_buffer(self.buffer_size // 2)
            
            await anyio.sleep(60)  # Check every minute
```

## Part 7: Error Propagation Strategy

### Error Port Design

**Separate error ports** (Recommended):
```python
class ComponentWithErrorHandling:
    def __init__(self):
        self.input_port = Port("input", DataSchema)
        self.output_port = Port("output", ResultSchema)
        self.error_port = Port("error", ErrorSchema)  # Dedicated error port
    
    async def process(self):
        try:
            data = await self.input_port.receive()
            result = self.transform(data)
            await self.output_port.send(result)
        except ValidationError as e:
            await self.error_port.send(ErrorSchema(
                error_type="validation",
                message=str(e),
                data=data
            ))
        except Exception as e:
            await self.error_port.send(ErrorSchema(
                error_type="processing",
                message=str(e),
                data=data
            ))
```

### Error Cascade Prevention

**Circuit breaker pattern**:
```python
class CircuitBreakerPort(Port):
    def __init__(self):
        super().__init__()
        self.failure_count = 0
        self.failure_threshold = 5
        self.is_open = False
        self.reset_timeout = 60  # seconds
    
    async def send(self, data):
        if self.is_open:
            raise CircuitOpenError("Circuit breaker is open")
        
        try:
            await super().send(data)
            self.failure_count = 0  # Reset on success
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                # Schedule reset
                asyncio.create_task(self.reset_after_timeout())
            raise
```

### Retry Logic Location

**Port-level retry** (for transport issues):
```python
class RetryPort(Port):
    async def send_with_retry(self, data, max_retries=3):
        for attempt in range(max_retries):
            try:
                await self.send(data)
                return
            except TransportError:
                if attempt == max_retries - 1:
                    raise
                await anyio.sleep(2 ** attempt)  # Exponential backoff
```

**Component-level retry** (for business logic):
```python
class Component:
    async def process_with_retry(self, data):
        for attempt in range(self.max_retries):
            try:
                return await self.business_logic(data)
            except BusinessError as e:
                if not e.is_retryable or attempt == self.max_retries - 1:
                    raise
                await anyio.sleep(self.retry_delay)
```

## Part 8: Component Lifecycle Coordination

### Startup Order Strategy

**Dependency graph resolution**:
```python
class LifecycleCoordinator:
    def __init__(self):
        self.dependency_graph = {}  # component -> [dependencies]
    
    def compute_startup_order(self) -> List[str]:
        """Topological sort of dependency graph"""
        visited = set()
        stack = []
        
        def visit(component):
            if component in visited:
                return
            visited.add(component)
            for dep in self.dependency_graph.get(component, []):
                visit(dep)
            stack.append(component)
        
        for component in self.dependency_graph:
            visit(component)
        
        return stack  # Correct startup order
    
    async def start_system(self):
        """Start components in dependency order"""
        startup_order = self.compute_startup_order()
        for component_name in startup_order:
            component = self.get_component(component_name)
            await component.setup()
            await self.wait_for_ready(component)
```

### Partial Startup Failure

**Rollback strategy**:
```python
class SafeStartup:
    async def start_with_rollback(self):
        started_components = []
        try:
            for component in self.startup_order:
                await component.setup()
                started_components.append(component)
                if not await component.health_check():
                    raise StartupError(f"{component.name} unhealthy")
        except Exception as e:
            # Rollback in reverse order
            for component in reversed(started_components):
                try:
                    await component.cleanup()
                except:
                    pass  # Best effort cleanup
            raise SystemStartupError(f"Startup failed: {e}")
```

### Graceful Degradation

**Feature flags and optional components**:
```python
class DegradableSystem:
    def __init__(self):
        self.required_components = ["core", "database"]
        self.optional_components = ["cache", "analytics", "monitoring"]
    
    async def start_with_degradation(self):
        # Start required components (fail if any fail)
        for name in self.required_components:
            component = self.get_component(name)
            if not await self.start_component(component):
                raise CriticalError(f"Required component {name} failed")
        
        # Start optional components (log but don't fail)
        degraded_features = []
        for name in self.optional_components:
            component = self.get_component(name)
            if not await self.start_component(component):
                self.logger.warning(f"Optional component {name} failed")
                degraded_features.append(name)
        
        if degraded_features:
            self.logger.info(f"System running in degraded mode without: {degraded_features}")
```

### Health Check Propagation

**Health aggregation through ports**:
```python
class HealthAggregator:
    async def check_system_health(self) -> Dict:
        """Aggregate health from all components"""
        health_status = {
            "healthy": True,
            "components": {},
            "timestamp": datetime.now()
        }
        
        for name, component in self.components.items():
            try:
                # Each component has health port
                health = await component.health_port.receive(timeout=1)
                health_status["components"][name] = health
                if not health.get("healthy", False):
                    health_status["healthy"] = False
            except TimeoutError:
                health_status["components"][name] = {
                    "healthy": False,
                    "error": "Health check timeout"
                }
                health_status["healthy"] = False
        
        return health_status

class ComponentWithHealth:
    def __init__(self):
        self.health_port = Port("health", HealthSchema)
    
    async def emit_health(self):
        """Periodically emit health status"""
        while True:
            health = await self.check_health()
            await self.health_port.send(health)
            await anyio.sleep(30)  # Every 30 seconds
```

## Summary

All complexity concerns have been addressed with concrete implementation strategies. The key insights:

1. **Recipe complexity** is managed through versioning and generation-time expansion
2. **Port buffers** use backpressure by default with configurable policies
3. **Errors** flow through dedicated error ports to prevent contamination
4. **Lifecycle** is managed through dependency graphs and graceful degradation

The system remains simple at its core (5 types + configuration) while providing sophisticated behavior through these patterns.

## Part 9: Additional Architecture Concerns

### Stream vs RPC Architecture - Deep Dive

**Current State Analysis:**
The system has a fundamental split personality:
- **Harness Layer**: Creates and manages anyio.MemoryObjectStream correctly
- **Component Layer**: Expected to use streams via receive_streams/send_streams
- **Generated Code**: Uses RPC-style ComponentCommunicator with method calls

**Critical Questions:**
1. **How deep is the RPC assumption?**
   - Generated communication.py implements full RPC routing
   - Components call `send_to_component()` expecting synchronous response
   - No async iteration over streams in generated code

2. **Migration complexity:**
   ```python
   # Current (RPC-style):
   response = await self.communicator.send_to_component("store", data)
   
   # Target (Stream-style):
   await self.output_ports["to_store"].send(data)
   # Response comes back via different port
   response = await self.input_ports["from_store"].receive()
   ```

3. **Behavioral differences:**
   - RPC: Request-response, synchronous-like, coupled
   - Streams: Fire-and-forget, async, decoupled
   - Ports: Typed streams with validation

**Resolution Strategy:**
- **Option A**: Fix generation to use existing streams (simpler, faster)
- **Option B**: Wrap RPC in port interface (compatibility layer)
- **Option C**: Full rewrite to stream-based (clean but expensive)

### Port Implementation Complexity - Unresolved Issues

**1. Stream-Port Impedance Mismatch**
```python
# Streams are untyped
stream: anyio.MemoryObjectStream  # Accepts any object

# Ports are typed
port: Port[TodoItem]  # Only accepts TodoItem

# How to handle mismatches?
# Option 1: Runtime errors
# Option 2: Coercion
# Option 3: Separate error port
```

**2. Port Discovery and Wiring**
```python
# How do components declare ports?
class Component:
    def declare_ports(self):
        # Option A: Declarative
        return {
            "input": Port[DataIn],
            "output": Port[DataOut]
        }
    
    # Option B: Programmatic
    def __init__(self):
        self.add_input_port("input", DataIn)
        self.add_output_port("output", DataOut)
    
    # Option C: Convention
    # Ports discovered by introspection
```

**3. Backpressure Propagation**
```python
# When output port is full, what happens?
async def process(self):
    data = await self.input_port.receive()
    result = transform(data)
    
    # This might block if output is full
    await self.output_port.send(result)
    # Should we:
    # 1. Block input (natural backpressure)
    # 2. Buffer internally (memory risk)
    # 3. Drop messages (data loss)
    # 4. Spill to disk (complexity)
```

**4. Error Port Topology**
```python
# Where do error ports connect?
# Option A: Dedicated error collector
all_errors -> ErrorCollector

# Option B: Source component
component.error -> source_component.error_input

# Option C: Supervisor
component.error -> supervisor.handle_error

# Option D: Dead letter queue
component.error -> dlq.store
```

**5. Port Lifecycle Management**
```python
# When are ports created/destroyed?
class PortLifecycle:
    async def startup(self):
        # Create ports before or after component init?
        self.create_ports()
        await self.component.setup()
        self.wire_ports()
    
    async def shutdown(self):
        # Drain ports before shutdown?
        await self.drain_all_ports()
        await self.component.cleanup()
        self.destroy_ports()
```

**6. Type Evolution and Compatibility**
```python
# What happens when types change?
# V1: Port[TodoItemV1]
# V2: Port[TodoItemV2] with new required field

# Options:
# 1. Version negotiation at wire time
# 2. Adapter ports for migration
# 3. Dual-port period
# 4. Big-bang migration
```

### Unresolved Architectural Decisions

1. **Sync vs Async Port Operations**
   - Should port.send() always be async?
   - What about receive_nowait() for polling?
   - How to handle timeout semantics?

2. **Port Composition Patterns**
   ```python
   # Can ports be composed?
   class MultiplexPort(Port):
       def __init__(self, ports: List[Port]):
           self.ports = ports
       
       async def send(self, data):
           # Send to all? Round-robin? Hash-based?
   ```

3. **Port Observability**
   - Should ports emit metrics automatically?
   - How to trace data flow through ports?
   - Where to log port operations?

4. **Port Testing Strategy**
   ```python
   # How to test components with ports?
   class TestPort(Port):
       def __init__(self):
           self.sent_items = []
           self.receive_items = Queue()
       
       async def send(self, data):
           self.sent_items.append(data)
   ```

### Recommendation: Incremental Port Adoption

**Phase 1: Facade Pattern**
```python
# Wrap existing streams with port interface
class PortFacade:
    def __init__(self, stream):
        self.stream = stream
    
    async def send(self, data):
        # Add validation later
        await self.stream.send(data)
```

**Phase 2: Type Validation**
```python
# Add schema validation
class ValidatedPort(PortFacade):
    def __init__(self, stream, schema):
        super().__init__(stream)
        self.schema = schema
    
    async def send(self, data):
        validated = self.schema.validate(data)
        await self.stream.send(validated)
```

**Phase 3: Full Port Implementation**
```python
# Complete port with all features
class Port(ValidatedPort):
    # Metrics, tracing, error handling, etc.
```

This incremental approach reduces risk while providing immediate value.