# Component Model

## Overview

The entire Autocoder system is constructed from a single, unified building block: the `ComposedComponent`. This class serves as the foundation for all functional elements in a generated system. It is designed to be a lightweight container whose power is derived not from a complex inheritance tree, but from the discrete, explicit Capabilities it is assembled with.

> **Architecture Decision**: ADR-031 has been accepted, establishing a **port-based component model** that replaces the rigid Source/Transformer/Sink trichotomy. Components now define their behavior through explicit, named ports with semantic types and schema validation.

## The ComposedComponent Base Class

All components inherit from the `ComposedComponent` base class, which provides a universal set of features and contracts:

- **Unified Lifecycle**: Standard `setup()`, `process()`, and `cleanup()` methods.
- **Capability Hooks**: A consistent mechanism for injecting cross-cutting concerns like resilience, validation, and security. Capabilities implement a typed, async-first, three-phase hook interface (ADR-019).
- **Stream Communication**: anyio-based input/output streams for asynchronous data flow.
- **Integrated Observability**: Uniform logging, metrics, and tracing support out-of-the-box.
- **Consistent Error Handling**: Automatic wiring of the `ConsistentErrorHandler`.
- **Port-Based Semantics**: Explicit, named ports with schema validation and semantic typing.

Every component **always** ships with a minimal _Capability Kernel_.
This kernel is non-optional for the MVP release—there is **no switch** to turn it off.  
The kernel currently consists of:
* `SchemaValidator` — strict contract enforcement  
* `RateLimiter` — back-pressure & DoS protection  
* `MetricsCollector` — RED metrics for observability  

**Kernel Enforcement (ADR-029):** The ComponentRegistry validates that all components include the mandatory kernel capabilities. Builds fail if any kernel capability is missing. The kernel list is version-controlled and requires lead approval for changes.

**Two-Layer Fail-Hard Policy:**
- **AutoCoder Layer**: Missing kernel capabilities cause immediate build failure - no component can be generated without them
- **Generated System Layer**: Kernel capabilities are mandatory at runtime - no graceful degradation allowed for core capabilities like schema validation, rate limiting, or metrics collection

> Future roadmap (Post-MVP): an **audited bypass** mechanism may be introduced for edge-cases that genuinely cannot tolerate the kernel overhead.  That work will follow the "Option 2 – risk-ticket" design and will not break existing blueprints.

## Capability System

### Overview

A "Capability" is a self-contained, single-purpose class that provides a specific, cross-cutting concern. Instead of inheriting these features, every component is assembled with a stack of capabilities configured in the `architecture.yaml`.

### The Baseline Capability Set & Performance Budget

A subset of capabilities forms the **Baseline Capability Set**. This set provides foundational resilience and observability (e.g., `SchemaValidator`, `RateLimiter`, `MetricsCollector`). It is included by default in all components.

The kernel's inclusion is justified by a strict **Performance Budget**.  
Each kernel capability has a published `p95_latency_ms` and `max_memory_mb` budget committed in `capability_budgets.yaml`.  

• **Build-time guard** – a micro-benchmark in CI fails any pull-request that regresses beyond the budget.  
• **Runtime guard** – the same numbers feed Prometheus alert rules (`CapabilityLatencyHigh`, `CapabilityMemHigh`).  

These guards protect quality without removing validation or rate-limiting logic.  There is no bypass; a regression must be fixed or the budget formally updated with sign-off.

### Capability Hook Contract (ADR-019)

Capabilities implement a typed, async-first, three-phase hook interface:

```python
class Capability(Protocol):
    async def before_process(self, ctx: ProcessCtx) -> None: ...
    async def around_process(self, ctx: ProcessCtx, call_next: Callable) -> None: ...
    async def after_process(self, ctx: ProcessCtx, result: Any) -> None: ...
```

- `ProcessCtx` is a frozen dataclass containing trace-id, port information, and other context
- The contract is enforced with `typing.Protocol` for compile-time validation
- Hook signatures are frozen in `build.lock` to ensure reproducibility

### Capability Re-entrancy Policy (ADR-023)

Capability-to-capability re-entrant calls are **disallowed by default**. Capabilities that require re-entrancy must use an explicit decorator:

```python
@allow_reentrant("MetricsCollector")
class RetryHandler(Capability): ...
```

- Detection is via context-var "capability_stack" depth
- Fail-hard if illegal recursion is detected
- This prevents infinite loops and metrics explosions

### Capability Tier System

Capabilities are executed in a deterministic order based on their tier. This order is calculated during the build's "freeze" step and stored in the `build.lock` to ensure true reproducibility.

{{#include ../../_partials/capability_table.md}}

> **Implementation Note**  
> The helper `no_capabilities()` and the undocumented `unsafe_ignore_capabilities` switch have been **removed for MVP**.  All components instantiate the kernel unconditionally; tuning is achieved only via parameters (e.g., setting `rate_limit.rate` very high).

### Core Capabilities

#### SchemaValidator (Tier 10) **[KERNEL]**

**Purpose**: Strict data-contract enforcement using Pydantic schemas.

**Features**:
- Validates all incoming and outgoing data against Pydantic schemas
- Supports schema versioning with automatic upgrades
- Enforces fail-hard validation - any schema violation raises an exception

**Configuration**:
```yaml
capabilities:
  schema_validator:
    enabled: true
    strict_mode: true  # Reject unknown fields
```

#### RateLimiter (Tier 20) **[KERNEL]**

**Purpose**: Controls throughput to downstream systems and provides backpressure.

**Features**:
- Token bucket algorithm for rate limiting
- Configurable rate and burst limits
- Automatic backpressure when limits are exceeded

**Configuration**:
```yaml
capabilities:
  rate_limit:
    rate: 100  # requests per second
    burst: 200  # maximum burst size
```

#### StateCapability (Tier 30)

**Purpose**: Provides pluggable, durable state with enterprise-grade persistence (ADR-028).

**Features**:
- Pluggable state adapters (Redis snapshot, in-memory ephemeral, future event-log)
- Automatic checkpointing with configurable intervals
- Graceful degradation with fail-soft error handling

**Configuration**:
```yaml
state:
  adapter: redis_snapshot        # or inmem_ephemeral
  checkpoint_interval_s: 60      # default 60s
  rpo_hint_s: 60                 # declarative hint for RPO
```

#### BatchedProcessingCapability (Tier 25)

**Purpose**: Enables harness-aggregated batch processing for improved throughput (ADR-024).

**Features**:
- Harness-managed batching with explicit size/time triggers
- Vectorized capability hooks for performance optimization
- Configurable error handling modes (fail_fast, per_item)

**Configuration**:
```yaml
batching:
  enabled: true
  max_items: 64
  max_ms: 5
  min_items: 1
  forming_buffer_limit: 2
  error_mode: per_item  # or fail_fast
  ordering: relaxed     # or strict
```

#### LLMProviderCapability (Tier 35)

**Purpose**: Provides unified access to LLM providers through a thin abstraction layer (ADR-027).

**Features**:
- Remote-only MVP with provider registration via entry points
- Standardized completion and embedding interfaces
- Provider-specific configuration isolation

**Configuration**:
```yaml
llm:
  provider: openai
  openai:
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}
```

#### RetryHandler (Tier 40)

**Purpose**: Exponential-backoff retries for transient faults.

**Features**:
- Exponential backoff with jitter
- Configurable retry attempts and backoff parameters
- Circuit breaker integration for persistent failures

**Configuration**:
```yaml
capabilities:
  retry:
    max_attempts: 3
    initial_delay: 1.0  # seconds
    max_delay: 60.0  # seconds
    backoff_factor: 2.0
```

#### CircuitBreaker (Tier 50)

**Purpose**: Halts calls to unhealthy services.

**Features**:
- Three states: Closed, Open, Half-Open
- Configurable failure thresholds and timeouts
- Automatic recovery and health monitoring

**Configuration**:
```yaml
capabilities:
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 60  # seconds
    expected_exception: "ConnectionError"
```

#### MetricsCollector (Tier 90) **[KERNEL]**

**Purpose**: Emits structured RED (Rate, Errors, Duration) metrics for observability.

**Features**:
- OpenTelemetry-compatible metrics
- Per-capability tier latency breakdown
- Automatic metric collection for all components

**Configuration**:
```yaml
capabilities:
  metrics:
    enabled: true
    endpoint: "/metrics/prometheus"
```

## Component Port Semantics (ADR-031)

### Overview

**ADR-031 has been accepted**, establishing a **port-based component model** that replaces the rigid Source/Transformer/Sink trichotomy. A component's role now emerges from its port topology rather than being declared as a static type.

### Key Principles

1. **Explicit over Implicit**: All component connectivity semantics must be declared explicitly—no inference from naming heuristics.
2. **Derive Role, Don't Declare Type**: Operational roles (source, sink, transformer) emerge from port topology, not static strings.
3. **Schema-Driven Connectivity**: Every port has a specific schema, and outputs can only connect to inputs with matching/compatible schemas.
4. **Selective Emission**: Components return a mapping of port → payload(s), not broadcast to all outputs.

### **Migration Impact: Minimal Due to Chatbot Interface**

**Critical Insight**: The transition from Source/Transformer/Sink to port-based semantics has **minimal end-user impact** because:

**Users Never Directly Specify Component Types**:
- Users interact via conversational AI: "Build me a todo API"
- The chatbot internally selects appropriate component types
- Blueprint generation handles component model evolution transparently
- No user training required on new component taxonomy

**Internal Migration Strategy**:
- **Legacy Support**: Source/Transformer/Sink types maintained for compatibility
- **Gradual Transition**: Chatbot gradually migrates to port-based components
- **Transparent Upgrade**: Users experience improved capabilities without migration work
- **Backward Compatibility**: Existing generated systems continue to work

**Migration Complexity** primarily affects:
- **AutoCoder developers** updating generation logic
- **Internal blueprints** and validation schemas
- **Component registry** supporting both models during transition

**End-user migration complexity**: **Near zero** due to conversational abstraction.

### Port Descriptors (ADR-022)

Each component declares explicit, named ports using the structured array format. The legacy delimited alias syntax (`success|error`) is deprecated.

```yaml
ports:
  inputs:
    - name: primary_input
      semantic_class: data_in
      direction: input
      data_schema:
        id: schemas.user.NewUserEvent
        version: 1
      required: true
      description: "Primary data input for user events"
  
  outputs:
    - name: enriched_output
      semantic_class: data_out
      direction: output
      data_schema:
        id: schemas.user.EnrichedUserEvent
        version: 2
      required: true
      description: "Enriched user events with additional data"
    
    - name: error_output
      semantic_class: error_out
      direction: output
      data_schema:
        id: schemas.common.ErrorEvent
        version: 1
      required: false
      description: "Error events for failed processing"
```

### Multi-Port Aggregation and Distribution (ADR-022)

For components with multiple ports of the same semantic class, explicit aggregation and distribution policies must be declared:

```yaml
ports:
  outputs:
    - name: success
      semantic_class: data_out
      distribution:
        mode: broadcast  # or partition_hash, conditional
        key: user_id     # required for partition_hash
    - name: errors
      semantic_class: error_out
      distribution:
        mode: broadcast
```

**Aggregation Modes** (for fan-in scenarios):
- `merge`: Interleave events as they arrive
- `priority`: Always prefer specified upstream order
- `first_wins`: Close other streams after first event
- `concatenate`: Process upstreams sequentially

**Distribution Modes** (for fan-out scenarios):
- `broadcast`: Send to all downstream components
- `partition_hash`: Consistent hashing based on key
- `conditional`: Predicate-based routing (future)
- `weighted`: Probabilistic distribution (future)

### Semantic Classes

The following standard semantic classes are defined:
*   `data_in`: Primary data input
*   `data_out`: Primary data output  
*   `control_in`: Input for control-plane commands (e.g., "flush cache")
*   `control_out`: Output for control signals
*   `metrics_out`: Output for component-specific metrics
*   `metrics_in`: Input for metrics collection
*   `error_out`: Output for error events
*   `error_in`: Input for error handling

### Role Derivation

Component roles are automatically derived from port topology:
- **Source-like**: Only output ports (no inputs)
- **Sink-like**: Only input ports (no outputs)  
- **Transformer-like**: Both input and output ports

### Schema Compatibility

The ComponentRegistry enforces strict schema compatibility:
- `data_out` → `data_in` connections must have matching schema IDs
- Producer version must be ≥ consumer's minimum required version
- Semantic class pairs must be allowed by the compatibility matrix

### Example Blueprint

```yaml
components:
  - name: data_enricher
    implementation: EnrichmentTransformer
    component_semantics_version: 2
    ports:
      raw_events:
        semantic_class: data_in
        direction: input
        data_schema:
          id: schemas.events.RawEvent
          version: 1
        required: true
      control_commands:
        semantic_class: control_in
        direction: input
        data_schema:
          id: schemas.control.Command
          version: 1
        required: false
      enriched_events:
        semantic_class: data_out
        direction: output
        data_schema:
          id: schemas.events.EnrichedEvent
          version: 2
        required: true
      error_events:
        semantic_class: error_out
        direction: output
        data_schema:
          id: schemas.common.ErrorEvent
          version: 1
        required: false
```

## Component Implementations

### Overview

Components are implemented using the `ComposedComponent` base class with capability-based composition. The **System Generator service** selects the appropriate implementation based on the user's request and port requirements.

### Implementation Patterns

#### APIEndpoint

**Purpose**: To expose a web-based API that receives external client requests and introduces them into the system as data events.

**Technology**: 
- MUST use FastAPI for high performance and native asyncio support
- Served by uvicorn.Server instance in a separate thread for proper server isolation
- Uses threading.Thread with daemon=True for non-blocking server startup

**Port Configuration**:
```yaml
ports:
  request:
    semantic_class: data_in
    direction: input
    data_schema:
      id: schemas.api.APIRequest
      version: 1
  response:
    semantic_class: data_out
    direction: output
    data_schema:
      id: schemas.api.APIResponse
      version: 1
```

#### Store

**Purpose**: To provide a robust, production-grade interface for persisting data to a relational database.

**Technology**: 
- Uses async database connections with connection pooling
- All database interactions through structured query methods
- Strictly forbidden to use raw SQL strings in component logic

**Port Configuration**:
```yaml
ports:
  store:
    semantic_class: data_in
    direction: input
    data_schema:
      id: schemas.persistence.StoreRequest
      version: 1
    required: true
```

#### Model

**Purpose**: To execute a pre-trained machine learning model for inference, embedding it as a seamless part of the data flow.

**Port Configuration**:
```yaml
ports:
  features:
    semantic_class: data_in
    direction: input
    data_schema:
      id: schemas.ml.FeatureVector
      version: 1
    required: true
  predictions:
    semantic_class: data_out
    direction: output
    data_schema:
      id: schemas.ml.Prediction
      version: 1
    required: true
```

## Component Registry

### Overview

The ComponentRegistry is the central authority for component validation and instantiation. It maintains the definitive catalog of all available component implementations and enforces the architectural rules.

### Registration Process

```python
class ComponentRegistry:
    def __init__(self):
        self._components = {}
        self._register_builtin_components()
    
    def _register_builtin_components(self):
        """Register all built-in component implementations."""
        # Legacy types maintained for backward compatibility during ADR-031 migration
        # NOTE: Migration impact is minimal due to chatbot interface - users don't directly reference component types
        self.register("Source", Source)
        self.register("Transformer", Transformer)
        self.register("Sink", Sink)
        # Port-based component types (ADR-031)
        self.register("Store", Store)
        self.register("Controller", Controller)
        self.register("APIEndpoint", APIEndpoint)
        self.register("Model", Model)
        self.register("Accumulator", Accumulator)
        self.register("Router", Router)
        self.register("StreamProcessor", StreamProcessor)
        self.register("WebSocket", WebSocket)
        self.register("MessageQueue", MessageQueue)
        self.register("EventBus", EventBus)
        self.register("TimerTrigger", TimerTrigger)
        self.register("FileWatcher", FileWatcher)
        self.register("DatabaseConnector", DatabaseConnector)
```

### Validation Methods

The ComponentRegistry provides specific validation methods:

- `validate_component_dependencies()`: Checks component dependencies
- `validate_all_components()`: Validates entire blueprint
- `validate_component_file()`: Validates individual component files
- `validate_component_code()`: Validates generated component code

### Integration with Validation Framework

The ComponentRegistry is tightly integrated with:
- `LockVerifier`: Ensures build integrity
- `ASTValidationRuleEngine`: Performs code quality analysis
- `PolicyEngine`: Enforces constraint-as-code policies

## Component Lifecycle

### Setup Phase

During setup, components prepare for operation:

```python
async def setup(self) -> None:
    """Prepare component for operation."""
    # Initialize capabilities
    for capability in self.capabilities:
        await capability.setup()
    
    # Component-specific setup
    await self._setup_component()
```

### Process Phase

During processing, components execute their main logic:

```python
async def process(self) -> None:
    """Main processing loop."""
    try:
        while True:
            # Process data through capability chain
            data = await self._receive_data()
            processed_data = await self._process_through_capabilities(data)
            await self._send_data(processed_data)
    except Exception as e:
        await self._handle_error(e)
```

### Cleanup Phase

During cleanup, components release resources:

```python
async def cleanup(self) -> None:
    """Clean up resources."""
    # Component-specific cleanup
    await self._cleanup_component()
    
    # Cleanup capabilities
    for capability in reversed(self.capabilities):
        await capability.cleanup()
```

## Data Flow Between Components

### Stream-Based Communication

Components communicate through anyio.MemoryObjectStream instances:

```python
# Source component sends data
await output_stream.send(data)

# Destination component receives data
data = await input_stream.receive()
```

### Binding Configuration

Data flows are explicitly defined in the blueprint:

```yaml
bindings:
  - from: user_api
    on: new_users
    to: user_validator
    as: input
  - from: user_validator
    on: output
    to: user_database
    as: input
```

### Backpressure Handling

Streams inherently provide backpressure. If a downstream component cannot keep up, the stream fills up and the sending component naturally pauses until there is capacity.

## Error Handling

### Two-Layer Fail-Hard Philosophy

The error handling strategy differs between AutoCoder system components and generated system components:

#### **AutoCoder System Components (Always Fail-Hard)**
AutoCoder internal components always fail hard:
- No lazy fallbacks or graceful degradation
- Immediate errors for missing configurations or dependencies  
- Strict validation at every stage
- Missing imports cause immediate system halt
- Failed component generation stops the entire build

#### **Generated System Components (Graceful Degradation with Fail-Hard Boundaries)**
Generated components can implement planned graceful degradation, but must fail hard when degradation itself fails:
- **Circuit Breakers**: Graceful degradation when services are unavailable, fail-hard when circuit breaker mechanism fails
- **Fallback Queues**: Graceful degradation to queue processing, fail-hard when both primary service and queue fail
- **Capability Kernel**: Always fail-hard - no graceful degradation for schema validation, rate limiting, or metrics collection
- **Configuration Errors**: Always fail-hard - malformed configuration must never be silently ignored

### Consistent Error Handling

All components use the ConsistentErrorHandler which:
- Automatically adds system resource metrics to logged errors
- Provides rich context for debugging
- Integrates with the self-healing framework

### Circuit Breaker Integration

Components with CircuitBreaker capability automatically handle persistent failures by:
- Opening the circuit after failure threshold is reached
- Preventing calls to unhealthy services
- Automatically attempting recovery after timeout

## Testing Support

### Component Isolation

Every component is fully decoupled, enabling precise unit testing:

```python
# Test a single transformer component
async def test_user_validator():
    validator = UserValidator(config, capabilities)
    await validator.setup()
    
    # Send test data
    test_data = NewUserEvent(username="test", email="test@example.com")
    result = await validator.process_data(test_data)
    
    # Assert on results
    assert result.is_valid == True
```

### LLM-Generated Test Scenarios

The system leverages LLM understanding to generate:
- Realistic integration tests
- Edge case coverage
- Security-focused tests
- End-to-end test scenarios 

## P99 Latency Cost Table ⚠️ ARCHITECTURAL PERFORMANCE GOALS

**CRITICAL DISCLAIMER**: These are **performance goals and design targets**, NOT guaranteed performance or empirically validated measurements. These represent what we aim to achieve, not what has been proven possible.

**Status**: All values are **aspirational targets** pending:
- Empirical benchmarking implementation  
- Real-world workload validation
- Hardware configuration optimization
- Performance regression testing

**Methodology**: Targets derived from complexity analysis, similar system benchmarks, and performance engineering best practices. **All values subject to significant revision** based on actual measurements.

**Risk**: These targets may prove unattainable and require architectural changes if performance constraints cannot be met.

| Capability | P99 Latency | Cost Tier | SLA Requirement | Description |
|------------|-------------|-----------|-----------------|-------------|
| circuit_breaker | 0.06ms | Ultra Fast | p99 < 1.0ms | Execute circuit breaker pattern for resilience (avg: 0.04ms, 23923 ops/sec) |
| metrics_collection | 0.07ms | Ultra Fast | p99 < 1.0ms | Collect and record performance metrics (avg: 0.04ms, 23698 ops/sec) |
| event_processing | 0.07ms | Ultra Fast | p99 < 1.0ms | Process and route events (avg: 0.05ms, 21765 ops/sec) |
| api_endpoint | 0.07ms | Ultra Fast | p99 < 1.0ms | Handle API endpoint requests (avg: 0.04ms, 22843 ops/sec) |
| retry_mechanism | 0.07ms | Ultra Fast | p99 < 1.0ms | Execute retry logic with backoff (avg: 0.04ms, 22457 ops/sec) |
| resource_allocation | 0.07ms | Ultra Fast | p99 < 1.0ms | Allocate system resources (CPU, memory, disk) (avg: 0.04ms, 23816 ops/sec) |
| rate_limiting | 0.07ms | Ultra Fast | p99 < 1.0ms | Enforce rate limiting policies (avg: 0.04ms, 23646 ops/sec) |
| caching | 0.08ms | Ultra Fast | p99 < 1.0ms | Store and retrieve cached data (avg: 0.04ms, 22746 ops/sec) |
| error_handling | 0.08ms | Ultra Fast | p99 < 1.0ms | Handle and process errors with context (avg: 0.05ms, 21564 ops/sec) |
| database_operation | 0.09ms | Ultra Fast | p99 < 1.0ms | Execute database queries and updates (avg: 0.04ms, 22279 ops/sec) |
| data_transformation | 0.10ms | Ultra Fast | p99 < 1.0ms | Transform data between different formats (avg: 0.05ms, 20071 ops/sec) |
| component_initialization | 0.11ms | Ultra Fast | p99 < 1.0ms | Initialize component instances with configuration (avg: 0.05ms, 21081 ops/sec) |
| component_loading | 0.11ms | Ultra Fast | p99 < 1.0ms | Load component classes from registry (avg: 0.05ms, 22004 ops/sec) |
| port_validation | 0.12ms | Ultra Fast | p99 < 1.0ms | Validate component port definitions and connections (avg: 0.05ms, 20913 ops/sec) |
| security_validation | 0.13ms | Ultra Fast | p99 < 1.0ms | Validate security constraints and permissions (avg: 0.04ms, 23061 ops/sec) |
| health_checks | 0.13ms | Ultra Fast | p99 < 1.0ms | Execute health check validations (avg: 0.04ms, 23140 ops/sec) |
| logging | 0.36ms | Ultra Fast | p99 < 1.0ms | Write structured log messages (avg: 0.20ms, 4995 ops/sec) |
| file_system | 0.59ms | Ultra Fast | p99 < 1.0ms | Read and write file system operations (avg: 0.19ms, 5363 ops/sec) |
| async_processing | 1.50ms | Fast | p99 < 10.0ms | Process asynchronous operations (avg: 1.40ms, 717 ops/sec) |
| configuration_loading | 4.89ms | Fast | p99 < 10.0ms | Load and parse configuration settings (avg: 4.29ms, 233 ops/sec) |
| schema_validation | TBD | TBD | TBD | Validate data against JSON schemas (performance pending empirical benchmarks) |

### Performance Tiers

- **Ultra Fast**: < 1.0ms - Critical path operations
- **Fast**: 1.0-10.0ms - High-frequency operations
- **Standard**: 10.0-100.0ms - Normal operations
- **Slow**: 100.0-1000.0ms - Background operations
- **Very Slow**: > 1000.0ms - Infrequent operations