# ADR-031 Component Semantics: A Proposal for a Unified, Flexible, and Validated Component Model

## 1. The Core Question: Defining a Component Model for the Future

Our current system is built on a component model that, while functional, has started to show its limitations. The rigid `Source/Transformer/Sink` trichotomy, while simple to understand, has led to architectural workarounds and inconsistencies as our system's complexity has grown.

The central architectural question we must answer is: **How do we evolve our component model to be more flexible, explicit, and robust, without sacrificing the simplicity and performance that have been key to our success?**

This document proposes **ADR-031**, a unified approach to component semantics that addresses this question through a combination of:

- **Port-Based Semantics**: Moving away from a rigid type system to a more flexible model where a component's role is defined by its named input and output ports.
- **Capability-Based Composition**: Embracing a "composition over inheritance" model where cross-cutting concerns (e.g., resilience, validation, security) are explicitly composed as capabilities.
- **Validation-Driven Architecture**: Enforcing architectural constraints and policies through a centralized `ComponentRegistry` that validates every aspect of a component's lifecycle.

This document serves as an aggregated resource for an external reviewer to understand the current state of our component model, the proposed changes, and the rationale behind them. It includes:

- The original ADR proposal for component semantics
- The complete `Component Model` documentation
- The full implementation of the `ComposedComponent` base class
- The implementation of the `port_auto_generator.py`
- The `architecture.schema.json` that defines the blueprint language
- Proposed ADRs for multi-port semantics, batched processing, and capability re-entrancy
- The full implementation of the `ComponentRegistry`

We believe this proposal represents a significant step forward in our system's architecture, and we look forward to a thorough review and discussion.

---

# Aggregate Architecture Document: Component Port Semantics (ADR-031)

**Purpose**: This document aggregates all relevant architecture information for evaluating ADR-031: Component Port Semantics. It includes current implementation, proposed changes, and the context needed for external evaluation.

**Date**: 2025-07-18  
**Scope**: Component model, port semantics, Source/Transformer/Sink evolution

---

## Table of Contents

1. [Current Component Model](#current-component-model)
2. [Component Registry Implementation](#component-registry-implementation)
3. [Port Auto-Generation System](#port-auto-generation-system)
4. [Schema Definitions](#schema-definitions)
5. [Current Limitations](#current-limitations)
6. [Proposed Solutions](#proposed-solutions)
7. [Related ADRs](#related-adrs)
8. [Implementation Examples](#implementation-examples)

---

## Current Component Model

### From: docs/reference/architecture/component-model.md

The entire Autocoder system is constructed from a single, unified building block: the `ComposedComponent`. This class serves as the foundation for all functional elements in a generated system. It is designed to be a lightweight container whose power is derived not from a complex inheritance tree, but from the discrete, explicit Capabilities it is assembled with.

#### The Three Fundamental Component Types

While all components are built from the same ComposedComponent base, they are categorized into one of three logical Types. The ComponentRegistry strictly enforces the rules associated with each type.

**Source**
- Purpose: To generate data and introduce it into the system.
- Rule: MUST NOT have any input streams. MUST have at least one output stream.

**Transformer**
- Purpose: To receive data, modify it in some way, and then pass it on.
- Rule: MUST have at least one input stream and at least one output stream.

**Sink**
- Purpose: To consume data and terminate a flow, often by sending it to an external system.
- Rule: MUST have at least one input stream. MUST NOT have any output streams.

#### Component Implementations

While there are only three fundamental Types (the "what"), there are many concrete Implementations (the "how"). An Implementation is a specific, pre-built version of a component type, engineered for a particular task.

The **System Generator service** selects the correct Implementation based on the user's request. This ensures that while the system has great flexibility, it still adheres to the strict rules of the three fundamental types.

Key Implementations include:

- **APIEndpoint** (Source, *Phase 0*): Exposes HTTP routes using FastAPI.
- **MessageBusSource** (Source, *Phase 2*): Consumes messages from a message-bus queue.
- **LocalOrchestrator** (Transformer, *Phase 1*): Coordinates a state-machine driven workflow.
- **Model** (Transformer, *Phase 2*): Executes an ML model.
- **Controller** (Transformer, *Phase 0*): Routes data based on content.
- **Store** (Sink, *Phase 0*): Persists data to a relational database using SQLAlchemy.
- **Accumulator** (Sink, *Phase 2*): Performs atomic aggregations in Redis.
- **MessageBusSink** (Sink, *Phase 2*): Publishes to a message-bus topic.
- **MetricsEndpoint** (Source, *Phase 0*): Auto-generated observability endpoint.

---

## Component Registry Implementation

### From: autocoder_cc/components/component_registry.py

```python
def _register_builtin_components(self) -> None:
    """Register built-in ComposedComponent types using composition over inheritance"""
    
    # Register ComposedComponent for all component types
    # Composition-based architecture - behavior determined by configuration and capabilities
    self.register_component_class("Source", ComposedComponent)
    self.register_component_class("Transformer", ComposedComponent)
    self.register_component_class("StreamProcessor", ComposedComponent)  # Real-time stream processing
    self.register_component_class("Sink", ComposedComponent)
    self.register_component_class("Store", ComposedComponent)
    self.register_component_class("Controller", ComposedComponent)  # System orchestration
    self.register_component_class("APIEndpoint", ComposedComponent)
    self.register_component_class("Model", ComposedComponent)
    self.register_component_class("Accumulator", ComposedComponent)  # Missing component type
    self.register_component_class("Router", ComposedComponent)  # Phase 2 component
    self.register_component_class("Aggregator", ComposedComponent)  # Phase 2 component
    self.register_component_class("Filter", ComposedComponent)  # Phase 2 component
```

**Note**: The registry actually supports 12 component types, but the documentation still teaches the "three fundamental types" model.

---

## Port Auto-Generation System

### From: autocoder_cc/blueprint_language/port_auto_generator.py

```python
#!/usr/bin/env python3
"""
Component Port Auto-Generator - Enterprise Roadmap v3 Phase 1
Auto-generates component port definitions based on component type and bindings
"""

from typing import Dict, Any, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import logging

from .blueprint_parser import ParsedComponent, ParsedPort
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer

# Import types only for type checking to avoid circular imports
if TYPE_CHECKING:
    from .system_blueprint_parser import ParsedBinding, ParsedSystemBlueprint


@dataclass
class ComponentTypeTemplate:
    """Template for component type port definitions"""
    default_inputs: List[ParsedPort]
    default_outputs: List[ParsedPort]
    required_inputs: Set[str]
    required_outputs: Set[str]


class ComponentPortAutoGenerator:
    """
    Auto-generates component port definitions based on type and connections.
    
    Features:
    - Component type-based default ports
    - Binding-driven port inference
    - Missing port detection and generation
    - Schema consistency validation
    """
    
    def __init__(self):
        self.structured_logger = get_logger("port_auto_generator", component="ComponentPortAutoGenerator")
        self.metrics_collector = get_metrics_collector("port_auto_generator")
        self.tracer = get_tracer("port_auto_generator")
        
        # Initialize component type templates
        self.type_templates = self._initialize_component_templates()
        
        self.structured_logger.info(
            "ComponentPortAutoGenerator initialized",
            operation="init",
            tags={"template_count": len(self.type_templates)}
        )
    
    def _initialize_component_templates(self) -> Dict[str, ComponentTypeTemplate]:
        """Initialize default port templates for component types"""
        
        templates = {}
        
        # Source components - only outputs, no inputs
        templates["Source"] = ComponentTypeTemplate(
            default_inputs=[],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Generated data items")
            ],
            required_inputs=set(),
            required_outputs={"output"}
        )
        
        # Transformer components - require both inputs and outputs
        templates["Transformer"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Input data items")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Transformed data items")
            ],
            required_inputs={"input"},
            required_outputs={"output"}
        )
        
        # Sink components - only inputs, no outputs
        templates["Sink"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Data items to process")
            ],
            default_outputs=[],
            required_inputs={"input"},
            required_outputs=set()
        )
        
        # Store components - inputs for storage, terminal component (no outputs)
        templates["Store"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="store", schema="ItemSchema", description="Items to store")
            ],
            default_outputs=[],  # No default outputs - terminal component
            required_inputs={"store"},
            required_outputs=set()  # No required outputs - terminal component
        )
        
        # APIEndpoint components - HTTP request/response
        templates["APIEndpoint"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="request", schema="APIRequestSchema", description="HTTP requests")
            ],
            default_outputs=[
                ParsedPort(name="response", schema="APIResponseSchema", description="HTTP responses")
            ],
            required_inputs={"request"},
            required_outputs={"response"}
        )
        
        # Accumulator components - multiple inputs to single output
        templates["Accumulator"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to accumulate")
            ],
            default_outputs=[
                ParsedPort(name="aggregate", schema="AggregateSchema", description="Aggregated results")
            ],
            required_inputs={"input"},
            required_outputs={"aggregate"}
        )
        
        # StreamProcessor components - stream processing
        templates["StreamProcessor"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="stream", schema="ItemSchema", description="Stream data items")
            ],
            default_outputs=[
                ParsedPort(name="processed", schema="ItemSchema", description="Processed stream items")
            ],
            required_inputs={"stream"},
            required_outputs={"processed"}
        )
        
        # Controller components - control signals
        templates["Controller"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="control", schema="SignalSchema", description="Control signals")
            ],
            default_outputs=[
                ParsedPort(name="command", schema="SignalSchema", description="Command signals")
            ],
            required_inputs={"control"},
            required_outputs={"command"}
        )
        
        # Router components - routing and dispatching
        templates["Router"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to route")
            ],
            default_outputs=[
                ParsedPort(name="output", schema="ItemSchema", description="Routed items")
            ],
            required_inputs={"input"},
            required_outputs={"output"}
        )
        
        # Model components - ML model inference
        templates["Model"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="features", schema="ItemSchema", description="Feature data for inference")
            ],
            default_outputs=[
                ParsedPort(name="predictions", schema="ItemSchema", description="Model predictions")
            ],
            required_inputs={"features"},
            required_outputs={"predictions"}
        )
        
        # FastAPICQRS components - CQRS pattern
        templates["FastAPICQRS"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="commands", schema="APIRequestSchema", description="Command requests"),
                ParsedPort(name="queries", schema="APIRequestSchema", description="Query requests")
            ],
            default_outputs=[
                ParsedPort(name="responses", schema="APIResponseSchema", description="API responses"),
                ParsedPort(name="events", schema="EventSchema", description="Domain events")
            ],
            required_inputs={"commands", "queries"},
            required_outputs={"responses", "events"}
        )
        
        # MessageBus components - message routing
        templates["MessageBus"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="messages", schema="EventSchema", description="Messages to route")
            ],
            default_outputs=[
                ParsedPort(name="routed", schema="EventSchema", description="Routed messages")
            ],
            required_inputs={"messages"},
            required_outputs={"routed"}
        )
        
        # Aggregator components - multiple inputs to single output
        templates["Aggregator"] = ComponentTypeTemplate(
            default_inputs=[
                ParsedPort(name="input", schema="ItemSchema", description="Items to aggregate")
            ],
            default_outputs=[
                ParsedPort(name="aggregate", schema="AggregateSchema", description="Aggregated results")
            ],
            required_inputs={"input"},
            required_outputs={"aggregate"}
        )
        
        return templates
```

### Key Features of Port Auto-Generator:

1. **Component Type Templates**: Pre-defined port configurations for each component type
2. **Binding Analysis**: Analyzes component bindings to infer required ports
3. **Missing Port Detection**: Identifies and generates missing ports based on connections
4. **Schema Consistency**: Ensures port schemas are compatible across connections
5. **Validation**: Validates that all required ports are present and properly configured

### Supported Component Types:

- **Source**: Generates data (outputs only)
- **Transformer**: Processes data (inputs and outputs)
- **Sink**: Consumes data (inputs only)
- **Store**: Persists data (inputs only, terminal)
- **APIEndpoint**: HTTP interface (request/response)
- **Accumulator**: Aggregates data (input to aggregate)
- **StreamProcessor**: Stream processing (stream to processed)
- **Controller**: Control signals (control to command)
- **Router**: Routes data (input to output)
- **Model**: ML inference (features to predictions)
- **FastAPICQRS**: CQRS pattern (commands/queries to responses/events)
- **MessageBus**: Message routing (messages to routed)
- **Aggregator**: Data aggregation (input to aggregate)

---

## Schema Definitions

### From: schemas/architecture.schema.json

```json
"type": {
  "type": "string",
  "enum": [
    "Source",
    "Transformer",
    "Accumulator",
    "Store",
    "Controller",
    "Sink",
    "StreamProcessor",
    "Model",
    "APIEndpoint",
    "Router"
  ],
  "description": "Component base type"
}
```

**Note**: The schema supports 10 component types, but the documentation still references only 3 fundamental types.

---

## Current Limitations

### Problem 1: Rigid Port Naming

The current system enforces rigid port naming:
- Sources: `output` (only)
- Transformers: `input` and `output` (only)
- Sinks: `input` (only)

This doesn't allow for semantically meaningful port names like:
- `data_in` and `control_in` for different input types
- `data_out` and `error_out` for different output types
- `metrics_out` for observability side-channels

### Problem 2: Complex Component Classification

Components that need multiple inputs or outputs are forced into the "Transformer" category, even when they have distinct semantic purposes:

```yaml
# Current approach - forced into Transformer
components:
  - name: data_enricher
    implementation: Transformer  # Generic classification
    config:
      input_schema: "schemas.data.RawEvent"
      output_schema: "schemas.data.EnrichedEvent"
```

### Problem 3: Documentation vs Implementation Gap

- **Documentation**: Teaches "three fundamental types" (Source/Transformer/Sink)
- **Implementation**: Supports 10-12 component types
- **Schema**: Validates 10 component types
- **Registry**: Registers 12 component types

This creates confusion about what the "real" component model is.

---

## Proposed Solutions

### Option A: Port-Based Semantic Model

Replace the rigid Source/Transformer/Sink model with flexible, named ports:

```yaml
# Proposed approach - semantic port names
components:
  - name: data_enricher
    implementation: EnrichmentTransformer
    ports:
      raw_events: data_in
      control_commands: control_in
      enriched_events: data_out
      error_events: data_out
      metrics: metrics_out
```

**Pros**:
- Maximum flexibility for complex components
- Semantic clarity in port names
- Future-proof for new port types

**Cons**:
- More complex blueprint authoring
- Requires significant refactoring
- May be overkill for simple components

### Option B: Keep Trichotomy, Add Compound Components

Keep the current Source/Transformer/Sink model but add wrapper components for complex cases:

```yaml
# Proposed approach - compound components
components:
  - name: data_enricher
    implementation: CompoundTransformer
    config:
      source_component: "DataProcessor"
      sink_component: "ErrorHandler"
      internal_binding: "source.errors -> sink.input"
```

**Pros**:
- Minimal change to existing architecture
- Keeps simple mental model
- Reuses existing component types

**Cons**:
- Wrapper explosion
- Harder debugging (nested components)
- Less intuitive for complex cases

### Option C: Define Additional Component Types

Keep the fundamental model but add more specific types:

```yaml
# Proposed approach - more specific types
components:
  - name: data_enricher
    implementation: EnrichmentProcessor  # New specific type
    config:
      primary_input: "raw_events"
      control_input: "control_commands"
      primary_output: "enriched_events"
      error_output: "error_events"
```

**Pros**:
- Explicit categories for common patterns
- Easier to reason about than fully free-form ports
- Maintains type-based validation

**Cons**:
- Type list will keep growing
- Eventually reinvents port semantics
- Less flexible than Option A

---

## Related ADRs

### ADR-022: Multi-Port Component Semantics (APPROVED)

**Context**: A component may have outputs that fit different logical types (e.g., a primary data output and a secondary metrics output). Our current `Source/Transformer/Sink` model is too simple to accurately describe these components, leading to ambiguity.

**Decision**: P1 Declarative Core with structured ports and explicit aggregation/distribution policies.

**Status**: **APPROVED** - Structured ports array with explicit aggregation/distribution enums and canonicalization step.

### ADR-024: Batched Processing Contracts (APPROVED)

**Context**: The current system is built exclusively around single-item processing, which limits throughput for high-volume scenarios.

**Decision**: Harness-aggregated batching with explicit configuration.

**Status**: **APPROVED** - Harness-managed batching contract with explicit blueprint fields and capability vectorization.

### ADR-028: Disaster Recovery and State Persistence (APPROVED)

**Context**: No mechanism for state persistence or disaster recovery, making the system unsuitable for production.

**Decision**: Pluggable state adapters with Redis snapshot as default.

**Status**: **APPROVED** - MVP-friendly pluggable state adapter solution with Redis snapshot adapter and pluggable SPI.

### ADR-027: LLM Provider Abstraction Layer (APPROVED)

**Context**: Components need unified access to LLM providers without vendor lock-in or complex dependency chains.

**Decision**: Remote-only MVP with thin SPI and provider registration via entry points.

**Status**: **APPROVED** - Thin provider SPI with standardized completion and embedding interfaces.

### ADR-030: Performance Budget Framework (APPROVED)

**Context**: Need systematic performance budget enforcement to prevent regressions and maintain system reliability.

**Decision**: Static budgets with build-time enforcement and runtime alerting.

**Status**: **APPROVED** - Static budget enforcement with benchmark comparison and runtime monitoring.

---

## Implementation Examples

### Current Implementation (Rigid)

```python
# Current ComposedComponent.process() method
async def process(self) -> None:
    # Get primary input stream (assumes single input)
    primary_stream_name = list(self.receive_streams.keys())[0]
    primary_stream = self.receive_streams[primary_stream_name]
    
    async for item in primary_stream:
        # Process single item
        result = await self.process_item(item)
        
        # Send to all output streams (no semantic distinction)
        if result is not None and self.send_streams:
            for output_name, output_stream in self.send_streams.items():
                await output_stream.send(result)
```

### Proposed Implementation (Flexible Ports)

```python
# Proposed approach with semantic ports
class Component:
    def __init__(self, ports: Dict[str, PortType]):
        self.ports = ports
        self.input_ports = {name: port for name, port in ports.items() 
                           if port.direction == PortDirection.INPUT}
        self.output_ports = {name: port for name, port in ports.items() 
                            if port.direction == PortDirection.OUTPUT}
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method to implement component logic"""
        raise NotImplementedError

class ComposedComponent(Component):
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Route inputs to appropriate capabilities
        # Apply capabilities in order
        # Route outputs to appropriate ports
        pass
```

---

## Key Questions for External Evaluation

1. **Architectural Simplicity vs Flexibility**: Should we prioritize the simple Source/Transformer/Sink model or embrace more complex port semantics?

2. **Migration Strategy**: How should we handle the transition from the current rigid model to a more flexible one?

3. **Component Type Proliferation**: Is it better to have a few fundamental types with many implementations, or many specific types?

4. **Port Naming Convention**: Should ports have semantic names (`data_in`, `control_in`) or generic names (`input`, `output`)?

5. **Backward Compatibility**: How important is it to maintain compatibility with existing blueprints?

6. **LLM Generation**: Which approach will be easier for LLMs to understand and generate correctly?

7. **Tooling Impact**: How will the choice affect monitoring, debugging, and visualization tools?

---

## Recommendation

Based on the analysis, **Option A (Port-Based Semantic Model)** provides the most flexibility and future-proofing, but requires significant refactoring. **Option C (Additional Component Types)** offers a good balance between flexibility and simplicity, while **Option B (Compound Components)** minimizes architectural changes.

The choice depends on:
- How much complexity the team is willing to accept
- Whether the current limitations are blocking real use cases
- The timeline and resources available for refactoring
- The importance of maintaining the simple mental model

**Next Steps**: 
1. Validate the proposed solutions against real-world component requirements
2. Assess the impact on LLM generation capabilities
3. Evaluate the migration effort and backward compatibility requirements
4. Consider the tooling and monitoring implications 

---

## APPENDIX A: COMPLETE COMPONENT MODEL DOCUMENTATION

### From: docs/reference/architecture/component-model.md

# Component Model

## Overview

The entire Autocoder system is constructed from a single, unified building block: the `ComposedComponent`. This class serves as the foundation for all functional elements in a generated system. It is designed to be a lightweight container whose power is derived not from a complex inheritance tree, but from the discrete, explicit Capabilities it is assembled with.

## The ComposedComponent Base Class

All components inherit from the `ComposedComponent` base class, which provides a universal set of features and contracts:

- **Unified Lifecycle**: Standard `setup()`, `process()`, and `cleanup()` methods.
- **Capability Hooks**: A consistent mechanism for injecting cross-cutting concerns like resilience, validation, and security.
- **Stream Communication**: anyio-based input/output streams for asynchronous data flow.
- **Integrated Observability**: Uniform logging, metrics, and tracing support out-of-the-box.
- **Consistent Error Handling**: Automatic wiring of the `ConsistentErrorHandler`.

Every component **always** ships with a minimal _Capability Kernel_.
This kernel is non-optional for the MVP release—there is **no switch** to turn it off.  
The kernel currently consists of:
* `SchemaValidator` — strict contract enforcement  
* `RateLimiter` — back-pressure & DoS protection  
* `MetricsCollector` — RED metrics for observability  

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

**Purpose**: Provides pluggable, durable state (in-memory, Redis, etc.).

**Features**:
- Pluggable storage backends (in-memory, Redis, future adapters)
- Used by LocalOrchestrator for workflow state persistence
- Supports state recovery and resumption

**Configuration**:
```yaml
capabilities:
  state:
    backend: "redis"  # or "memory"
    redis_url: "${REDIS_URL}"
    ttl: 3600  # seconds
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

## Component Types (Port-Based Semantics)

### Overview

The rigid `Source/Transformer/Sink` trichotomy has been deprecated in favor of a more flexible, port-based semantic model (see ADR-022). A component's role is now defined by the types of its named ports, which are explicitly declared in the `architecture.yaml`. This allows a single component to have multiple, logically distinct inputs and outputs (e.g., a data input, a control-plane input, a primary data output, and a metrics side-channel output).

### Port Types

The following standard port types are defined:
*   `data_in`: Primary data input.
*   `data_out`: Primary data output.
*   `control_in`: Input for control-plane commands (e.g., "flush cache").
*   `metrics_out`: Output for specialized, component-specific metrics.

The `ComponentRegistry` validates that all connections in the blueprint link compatible port types.

### Example Blueprint

```yaml
components:
  - name: data_enricher
    implementation: EnrichmentTransformer
    ports:
      raw_events: data_in
      control_commands: control_in
      enriched_events: data_out
      error_events: data_out
```

## Component Implementations

### Overview

While there are only three fundamental Types (the "what"), there are many concrete Implementations (the "how"). An Implementation is a specific, pre-built version of a component type, engineered for a particular task.

The **System Generator service** selects the correct Implementation based on the user's request. This ensures that while the system has great flexibility, it still adheres to the strict rules of the three fundamental types.

### Interface & API Implementations

#### APIEndpoint

**Fundamental Type**: Source

**Purpose**: To expose a web-based API that receives external client requests and introduces them into the system as data events.

**Technology**: 
- MUST use FastAPI for high performance and native asyncio support
- Served by uvicorn.Server instance in a separate thread for proper server isolation
- Uses threading.Thread with daemon=True for non-blocking server startup

**Execution Pattern**: The FastAPI application is served in a separate thread to ensure proper server isolation and prevent blocking the main anyio task group. The server thread is managed as a daemon thread for automatic cleanup.

**Blueprint Configuration**:
```yaml
components:
  - name: user_api
    implementation: APIEndpoint
    config:
      port: 8000
      routes:
        - path: "/users"
          method: "POST"
          output_stream: "new_users"
          output_schema: "schemas.user.NewUserEvent"
```

#### MetricsEndpoint

**Fundamental Type**: Source

**Purpose**: To provide production-grade observability into the health and performance of the running system.

**Technology**: FastAPI and Uvicorn

**Execution Pattern**: Same as APIEndpoint; runs as a native anyio task

**Details**: This component is non-configurable and exposes standard endpoints:
- `/health`: Simple 200 OK endpoint for load balancers
- `/metrics/json`: Comprehensive JSON payload with performance metrics
- `/metrics/prometheus`: Industry-standard Prometheus text-exposition format

### Persistence & Storage Implementations

#### Store

**Fundamental Type**: Sink

**Purpose**: To provide a robust, production-grade interface for persisting data to a relational database.

**Technology**: 
- Uses async database connections with connection pooling
- All database interactions through structured query methods
- Strictly forbidden to use raw SQL strings in component logic

**Architectural Pattern**: Uses structured database access methods with connection pooling for efficient data operations.

**Schema Management**: Database schema managed through structured configuration. Application code MUST NOT contain any CREATE TABLE or ALTER TABLE statements.

**Blueprint Configuration**:
```yaml
components:
  - name: user_database
    implementation: Store
    config:
      repository: "UserRepository"
      db_connection_env_var: "POSTGRES_DSN"
```

#### Accumulator

**Fundamental Type**: Sink

**Purpose**: To perform high-performance, atomic numerical aggregations and state management.

**Technology**: Redis with modern, asynchronous Redis client like redis-py

**Details**: Purpose-built for operations like counting events, summing values, or maintaining real-time leaderboards. Uses Redis commands like INCRBYFLOAT or Lua scripts for atomic read-modify-write operations.

**Blueprint Configuration**:
```yaml
components:
  - name: user_counter
    implementation: Accumulator
    config:
      redis_connection_env_var: "REDIS_URL"
      aggregation_type: "count"
      key_pattern: "users:count"
```

### AI & ML Implementations

#### Model

**Fundamental Type**: Transformer

**Purpose**: To execute a pre-trained machine learning model for inference, embedding it as a seamless part of the data flow.

**Details**: Specialized Transformer that loads serialized model files (e.g., .pkl from scikit-learn, .pt from PyTorch, or Hugging Face Transformers directory) and performs inference on incoming data.

**Blueprint Configuration**:
```yaml
components:
  - name: fraud_detector
    implementation: Model
    config:
      model_path: "/models/fraud_detector.pkl"
      input_schema: "schemas.transaction.TransactionEvent"
      output_schema: "schemas.fraud.FraudScore"
```

### Workflow Implementations

#### LocalOrchestrator

**Fundamental Type**: Transformer

**Purpose**: Owns a declarative state-machine that coordinates multiple downstream Transformers as a single unit of work (a mini-saga).

**Capabilities**: Always composes a StateCapability (tier 30) enabling pluggable durability.

**Behavior**: Exposes a simple `resume(saga_id)` API that re-hydrates state from the chosen StateCapability backend and continues processing where it left off.

**Blueprint Configuration**:
```yaml
components:
  - name: order_processor
    implementation: LocalOrchestrator
    config:
      workflow_definition: "workflows/order_processing.yaml"
      state_backend: "redis"
    capabilities:
      state:
        backend: "redis"
        redis_url: "${REDIS_URL}"
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
        self.register("Source", Source)
        self.register("Transformer", Transformer)
        self.register("Sink", Sink)
        self.register("Store", Store)
        self.register("Controller", Controller)
        self.register("APIEndpoint", APIEndpoint)
        self.register("Model", Model)
        self.register("Accumulator", Accumulator)
        self.register("Router", Router)
        self.register("StreamProcessor", StreamProcessor)
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

### Fail-Hard Philosophy

Components follow a fail-hard philosophy:
- No lazy fallbacks or graceful degradation
- Immediate errors for missing configurations or dependencies
- Strict validation at every stage

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

## P99 Latency Cost Table

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
| schema_validation | 113.18ms | Slow | p99 < 1000.0ms | Validate data against JSON schemas (avg: 96.12ms, 10 ops/sec) |

### Performance Tiers

- **Ultra Fast**: < 1.0ms - Critical path operations
- **Fast**: 1.0-10.0ms - High-frequency operations
- **Standard**: 10.0-100.0ms - Normal operations
- **Slow**: 100.0-1000.0ms - Background operations
- **Very Slow**: > 1000.0ms - Infrequent operations 

---

## APPENDIX B: COMPLETE COMPOSEDCOMPONENT IMPLEMENTATION

### From: autocoder_cc/components/composed_base.py

```python
#!/usr/bin/env python3
"""
ComposedComponent Architecture - Enterprise Roadmap v3 Phase 0
Pure composition over inheritance with capability-based design
"""
import time
from typing import Dict, Any, Optional, List, Type
from autocoder_cc.orchestration.component import Component
from autocoder_cc.error_handling.consistent_handler import handle_errors, ConsistentErrorHandler
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer


class ComposedComponent(Component):
    """
    Single unified component base using pure composition over inheritance.
    
    Replaces complex inheritance hierarchies with capability-based composition:
    - RetryHandler capability for resilience
    - CircuitBreaker capability for failure isolation  
    - SchemaValidator capability for data validation
    - RateLimiter capability for throughput control
    - MetricsCollector capability for observability
    
    All capabilities are composed dynamically based on configuration.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = config.get('type', 'Unknown') if config else 'Unknown'
        
        # Initialize consistent error handler
        self.error_handler = ConsistentErrorHandler(self.name)
        
        # Initialize observability stack - Enterprise Roadmap v3 Phase 1
        self.structured_logger = get_logger(f"component.{self.name}", component=self.name)
        self.metrics_collector = get_metrics_collector(self.name)
        self.tracer = get_tracer(self.name)
        
        # Composed capabilities - initialized based on config
        self.capabilities: Dict[str, Any] = {}
        
        # Phase 2: Service communication capabilities
        self.messaging_config = config.get("messaging", {}) if config else {}
        self.message_bridge = None
        
        # Setup all capabilities based on configuration
        self._compose_capabilities()
    
    def _setup_logging(self):
        """Setup component-specific logging - for compatibility with generated code"""
        # Logging is already set up in __init__ via observability stack
        # This method exists for compatibility with LLM-generated components
        pass
    
    def _compose_capabilities(self):
        """Compose capabilities based on configuration - pure composition pattern"""
        
        # Retry capability
        if self.config.get('retry_enabled', True):
            self.capabilities['retry'] = self._create_retry_capability()
        
        # Circuit breaker capability  
        if self.config.get('circuit_breaker_enabled', False):
            self.capabilities['circuit_breaker'] = self._create_circuit_breaker_capability()
        
        # Rate limiter capability
        if self.config.get('rate_limiter_enabled', False):
            self.capabilities['rate_limiter'] = self._create_rate_limiter_capability()
        
        # Schema validator capability
        if self.config.get('schema_validation_enabled', True):
            self.capabilities['schema_validator'] = self._create_schema_validator_capability()
        
        # Metrics collector capability
        if self.config.get('metrics_enabled', True):
            self.capabilities['metrics'] = self._create_metrics_capability()
        
        # Messaging capability (Phase 2)
        if self.messaging_config:
            self.capabilities['messaging'] = self._create_messaging_capability()
    
    def _create_retry_capability(self):
        """Create retry handler capability"""
        try:
            from autocoder_cc.capabilities.retry_handler import RetryHandler
            return RetryHandler(**self.config.get('retry', {}))
        except ImportError:
            # Graceful degradation if capability not available
            return None
    
    def _create_circuit_breaker_capability(self):
        """Create circuit breaker capability"""
        try:
            from autocoder_cc.capabilities.circuit_breaker import CircuitBreaker
            return CircuitBreaker(**self.config.get('circuit_breaker', {}))
        except ImportError:
            return None
    
    def _create_rate_limiter_capability(self):
        """Create rate limiter capability"""
        try:
            from autocoder_cc.capabilities.rate_limiter import RateLimiter
            return RateLimiter(**self.config.get('rate_limiter', {}))
        except ImportError:
            return None
    
    def _create_schema_validator_capability(self):
        """Create schema validator capability"""
        try:
            from autocoder_cc.capabilities.schema_validator import SchemaValidator
            return SchemaValidator(**self.config.get('schema_validation', {}))
        except ImportError:
            return None
    
    def _create_metrics_capability(self):
        """Create metrics collector capability"""
        try:
            from autocoder_cc.capabilities.metrics_collector import MetricsCollector
            return MetricsCollector(self.name)
        except ImportError:
            return None
    
    def _create_messaging_capability(self):
        """Create messaging capability for service communication"""
        try:
            bridge_type = self.messaging_config.get("bridge_type", "anyio_rabbitmq")
            
            if bridge_type == "anyio_rabbitmq":
                from autocoder_cc.messaging.bridges.anyio_rabbitmq_bridge import AnyIORabbitMQBridge
                rabbitmq_url = self.messaging_config.get("rabbitmq_url", "amqp://localhost")
                queue_name = self.messaging_config.get("queue_name", f"{self.name}_queue")
                return AnyIORabbitMQBridge(rabbitmq_url, self.name, queue_name)
                
            elif bridge_type == "anyio_kafka":
                from autocoder_cc.messaging.bridges.anyio_kafka_bridge import AnyIOKafkaBridge
                bootstrap_servers = self.messaging_config.get("bootstrap_servers", "localhost:9092")
                topic_name = self.messaging_config.get("topic_name", f"{self.name}_topic")
                return AnyIOKafkaBridge(bootstrap_servers, self.name, topic_name)
                
            elif bridge_type == "anyio_http":
                from autocoder_cc.messaging.bridges.anyio_http_bridge import AnyIOHTTPBridge
                host = self.messaging_config.get("host", "localhost")
                port = self.messaging_config.get("port", 8080)
                return AnyIOHTTPBridge(self.name, host, port)
                
            else:
                self.structured_logger.warning(f"Unknown bridge type: {bridge_type}")
                return None
                
        except ImportError as e:
            self.structured_logger.warning(f"Messaging capability not available: {e}")
            return None
    
    @handle_errors("ComposedComponent")
    async def process(self) -> None:
        """
        Main processing loop with Enterprise Roadmap v3 observability integration.
        
        Features:
        - Structured logging with trace correlation
        - Metrics collection for performance monitoring
        - Distributed tracing for component communication
        - Capability composition (retry, circuit breaking, etc.)
        """
        # Start processing trace
        with self.tracer.span("component.process", tags={'component_type': self.component_type}) as span_id:
            
            self.structured_logger.info(
                "Starting component processing",
                operation="process_start",
                tags={'component_type': self.component_type}
            )
            
            # Record component start metrics
            self.metrics_collector.record_component_start()
            
            if not self.receive_streams:
                self.structured_logger.warning(
                    "Component has no input streams configured",
                    operation="process_validation"
                )
                return
            
            # Get primary input stream
            primary_stream_name = list(self.receive_streams.keys())[0]
            primary_stream = self.receive_streams[primary_stream_name]
            
            self.structured_logger.debug(
                f"Processing items from stream: {primary_stream_name}",
                operation="stream_processing",
                tags={'stream_name': primary_stream_name}
            )
            
            async for item in primary_stream:
                try:
                    # Start item processing span  
                    with self.tracer.span("item.process") as item_span_id:
                        start_time = time.time()
                        
                        # Apply rate limiting capability if enabled
                        if 'rate_limiter' in self.capabilities and self.capabilities['rate_limiter']:
                            await self.capabilities['rate_limiter'].acquire()
                        
                        # Validate input schema if capability enabled
                        if 'schema_validator' in self.capabilities and self.capabilities['schema_validator']:
                            item = self.capabilities['schema_validator'].validate_input(item)
                        
                        # Process item with retry capability if enabled
                        if 'retry' in self.capabilities and self.capabilities['retry']:
                            result = await self.capabilities['retry'].execute(self.process_item, item)
                        elif 'circuit_breaker' in self.capabilities and self.capabilities['circuit_breaker']:
                            result = await self.capabilities['circuit_breaker'].execute(self.process_item, item)
                        else:
                            result = await self.process_item(item)
                        
                        # Validate output schema if capability enabled
                        if result is not None and 'schema_validator' in self.capabilities and self.capabilities['schema_validator']:
                            result = self.capabilities['schema_validator'].validate_output(result)
                        
                        # Send result to output streams
                        if result is not None and self.send_streams:
                            for output_name, output_stream in self.send_streams.items():
                                await output_stream.send(result)
                        
                        # Record successful processing metrics
                        processing_time = (time.time() - start_time) * 1000
                        self.metrics_collector.record_items_processed()
                        self.metrics_collector.record_processing_time(processing_time)
                        
                        self.structured_logger.debug(
                            f"Processed item successfully",
                            operation="item_processed",
                            metrics={'processing_time_ms': processing_time}
                        )
                        
                        self.increment_processed()
                        
                except Exception as e:
                    # Record error metrics
                    self.metrics_collector.record_error(e.__class__.__name__)
                    
                    self.structured_logger.error(
                        f"Item processing failed",
                        error=e,
                        operation="item_processing_error",
                        tags={'error_type': e.__class__.__name__}
                    )
                    
                    # Add error to current span
                    if item_span_id:
                        self.tracer.add_span_log(item_span_id, f"Processing error: {e}", "error")
                    
                    await self.error_handler.handle_exception(
                        e, 
                        context={"item": str(item), "component_type": self.component_type},
                        operation="process_item"
                    )
                finally:
                    # Release rate limiter if capability enabled
                    if 'rate_limiter' in self.capabilities and self.capabilities['rate_limiter']:
                        self.capabilities['rate_limiter'].release()
    
    async def process_item(self, item: Any) -> Any:
        """
        Process a single item - implement in subclasses for component-specific logic.
        
        This method should contain the core business logic for the component.
        Capabilities (retry, circuit breaking, etc.) are handled transparently.
        
        Args:
            item: The item to process
            
        Returns:
            The processed result or None to filter out the item
        """
        # Default implementation - pass through
        return item
    
    # Capability accessor methods for clean API
    def has_capability(self, capability_name: str) -> bool:
        """Check if component has a specific capability"""
        return capability_name in self.capabilities and self.capabilities[capability_name] is not None
    
    def get_capability(self, capability_name: str) -> Optional[Any]:
        """Get a specific capability instance"""
        return self.capabilities.get(capability_name)
    
    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry capability if available"""
        if self.has_capability('retry'):
            return await self.capabilities['retry'].execute(operation, *args, **kwargs)
        else:
            return await operation(*args, **kwargs)
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record metric using metrics capability if available"""
        if self.has_capability('metrics'):
            self.capabilities['metrics'].record(metric_name, value, tags or {})
    
    async def execute_with_circuit_breaker(self, operation, *args, **kwargs):
        """Execute operation with circuit breaker if available"""
        if self.has_capability('circuit_breaker'):
            return await self.capabilities['circuit_breaker'].execute(operation, *args, **kwargs)
        else:
            return await operation(*args, **kwargs)
    
    async def execute_with_rate_limit(self, operation, *args, **kwargs):
        """Execute operation with rate limiting if available"""
        if self.has_capability('rate_limiter'):
            await self.capabilities['rate_limiter'].acquire()
            try:
                return await operation(*args, **kwargs)
            finally:
                self.capabilities['rate_limiter'].release()
        else:
            return await operation(*args, **kwargs)
    
    def validate_data(self, data: Any, schema_type: str = 'input') -> Any:
        """Validate data using schema validator capability if available"""
        if self.has_capability('schema_validator'):
            if schema_type == 'input':
                return self.capabilities['schema_validator'].validate_input(data)
            elif schema_type == 'output':
                return self.capabilities['schema_validator'].validate_output(data)
        return data
    
    # Enhanced health check with capability status
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status including all capability statuses"""
        base_health = super().get_health_status()
        
        # Add capability health status
        capability_health = {}
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'get_status'):
                capability_health[cap_name] = capability.get_status()
            else:
                capability_health[cap_name] = {'status': 'disabled' if capability is None else 'active'}
        
        return {
            **base_health,
            'component_type': self.component_type,
            'capabilities': capability_health,
            'composition_model': 'capability_based'
        }
    
    # Dynamic capability management
    def add_capability(self, capability_name: str, capability_instance: Any):
        """Dynamically add a capability at runtime"""
        self.capabilities[capability_name] = capability_instance
        self.logger.info(f"Added capability '{capability_name}' to component {self.name}")
    
    def remove_capability(self, capability_name: str):
        """Dynamically remove a capability at runtime"""
        if capability_name in self.capabilities:
            del self.capabilities[capability_name]
            self.logger.info(f"Removed capability '{capability_name}' from component {self.name}")
    
    def reconfigure_capability(self, capability_name: str, new_config: Dict[str, Any]):
        """Reconfigure a specific capability"""
        if self.has_capability(capability_name):
            capability = self.capabilities[capability_name]
            if hasattr(capability, 'reconfigure'):
                capability.reconfigure(new_config)
                self.logger.info(f"Reconfigured capability '{capability_name}' for component {self.name}")
    
    # Component lifecycle with capability management
    async def _start_component(self):
        """Start all capabilities during component startup"""
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'start'):
                await capability.start()
                self.logger.debug(f"Started capability '{cap_name}' for component {self.name}")
        
        # Initialize messaging bridge if configured
        if self.has_capability('messaging'):
            await self.setup_messaging()
    
    async def _stop_component(self):
        """Stop all capabilities during component shutdown"""
        # Stop messaging bridge first
        if self.message_bridge:
            await self.message_bridge.stop()
            self.message_bridge = None
        
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'stop'):
                await capability.stop()
                self.logger.debug(f"Stopped capability '{cap_name}' for component {self.name}")
    
    def _cleanup_component(self):
        """Cleanup all capabilities during component cleanup"""
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'cleanup'):
                capability.cleanup()
                self.logger.debug(f"Cleaned up capability '{cap_name}' for component {self.name}")
    
    # Type checking helpers for backwards compatibility
    def is_source(self) -> bool:
        """Check if component is a source type"""
        return self.component_type.lower() in ['source', 'apiendpoint', 'metricsendpoint']
    
    def is_transformer(self) -> bool:
        """Check if component is a transformer type"""
        return self.component_type.lower() in ['transformer', 'controller', 'model', 'streamprocessor']
    
    def is_sink(self) -> bool:
        """Check if component is a sink type"""
        return self.component_type.lower() in ['sink', 'store', 'accumulator']
    
    def is_store(self) -> bool:
        """Check if component is a store type"""
        return self.component_type.lower() == 'store'
    
    def is_api_endpoint(self) -> bool:
        """Check if component is an API endpoint"""
        return self.component_type.lower() == 'apiendpoint'
    
    # Abstract method implementations
    @classmethod
    def get_required_config_fields(cls) -> List[str]:
        """Get required configuration fields for this component type"""
        return []
    
    @classmethod
    def get_required_dependencies(cls) -> List[str]:
        """Get required dependencies for this component type"""
        return []
    
    # Component readiness and health
    async def is_ready(self) -> bool:
        """Check if component is ready to process"""
        # Check all capabilities are ready
        for capability in self.capabilities.values():
            if capability and hasattr(capability, 'is_ready'):
                if not await capability.is_ready():
                    return False
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = self.get_health_status()
        
        # Add capability-specific health checks
        capability_health = {}
        for cap_name, capability in self.capabilities.items():
            if capability and hasattr(capability, 'health_check'):
                capability_health[cap_name] = await capability.health_check()
        
        health_status['capability_health'] = capability_health
        return health_status
    
    # Messaging capability integration
    async def setup_messaging(self):
        """Setup messaging bridge if messaging capability is available"""
        if self.has_capability('messaging'):
            try:
                self.message_bridge = self.capabilities['messaging']
                await self.message_bridge.start()
                self.structured_logger.info(
                    "Messaging bridge started",
                    operation="messaging_setup",
                    tags={'bridge_type': self.messaging_config.get('bridge_type', 'unknown')}
                )
            except Exception as e:
                self.structured_logger.error(
                    f"Failed to setup messaging bridge: {e}",
                    operation="messaging_setup_error"
                )
                raise
    
    async def send_message(self, message: Any) -> None:
        """Send message through messaging bridge if available"""
        if self.message_bridge:
            await self.message_bridge.send(message)
        else:
            self.structured_logger.warning(
                "No messaging bridge available for sending message",
                operation="send_message_no_bridge"
            )
    
    async def receive_message(self) -> Any:
        """Receive message from messaging bridge if available"""
        if self.message_bridge:
            return await self.message_bridge.receive()
        else:
            self.structured_logger.warning(
                "No messaging bridge available for receiving message",
                operation="receive_message_no_bridge"
            )
            return None
    
    async def get_messaging_health(self) -> Dict[str, Any]:
        """Get messaging bridge health status"""
        if self.message_bridge and hasattr(self.message_bridge, 'health_check'):
            return await self.message_bridge.health_check()
        return {'status': 'no_messaging_bridge'}
    
    def get_messaging_channels(self) -> Optional[Dict[str, Any]]:
        """Get messaging channel information"""
        if self.message_bridge and hasattr(self.message_bridge, 'get_channels'):
            return self.message_bridge.get_channels()
        return None
``` 

---

## APPENDIX D: ARCHITECTURE SCHEMA DEFINITIONS

### From: schemas/architecture.schema.json

#### Component Type Definitions

The architecture schema defines the following component types:

```json
{
  "type": {
    "type": "string",
    "enum": [
      "Source",
      "Transformer",
      "Accumulator",
      "Store",
      "Controller",
      "Sink",
      "StreamProcessor",
      "Model",
      "APIEndpoint",
      "Router"
    ],
    "description": "Component base type"
  }
}
```

#### Component Port Schema

```json
{
  "ComponentPort": {
    "type": "object",
    "required": ["name", "schema"],
    "properties": {
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_]*$",
        "description": "Port name"
      },
      "schema": {
        "type": "string",
        "description": "Reference to schema definition"
      },
      "required": {
        "type": "boolean",
        "default": true,
        "description": "Whether this port is required"
      },
      "description": {
        "type": "string",
        "description": "Port description"
      },
      "flow_type": {
        "type": "string",
        "enum": ["push", "pull", "request_response"],
        "default": "push",
        "description": "How data flows through this port"
      },
      "capabilities": {
        "$ref": "#/definitions/PortCapabilities",
        "description": "Required capabilities for this port"
      }
    },
    "additionalProperties": false
  }
}
```

#### Component Binding Schema

```json
{
  "ComponentBinding": {
    "type": "object",
    "required": ["from_component", "from_port", "to_component", "to_port"],
    "properties": {
      "from_component": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_]*$",
        "description": "Source component name"
      },
      "from_port": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_]*$",
        "description": "Source port name"
      },
      "to_component": {
        "oneOf": [
          {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Target component name"
          },
          {
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_]*$"
            },
            "description": "Multiple target components for fan-out"
          }
        ]
      },
      "to_port": {
        "oneOf": [
          {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Target port name"
          },
          {
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_]*$"
            },
            "description": "Multiple target ports for fan-out"
          }
        ]
      },
      "transformation": {
        "type": "string",
        "description": "Data transformation specification"
      },
      "condition": {
        "type": "string",
        "description": "Conditional routing expression"
      },
      "qos_requirements": {
        "$ref": "#/definitions/QoSRequirements",
        "description": "Quality of service requirements"
      }
    },
    "additionalProperties": false
  }
}
```

#### Architectural Component Schema

```json
{
  "ArchitecturalComponent": {
    "type": "object",
    "required": ["name", "type", "processing_mode"],
    "properties": {
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_]*$",
        "description": "Component name in snake_case"
      },
      "type": {
        "type": "string",
        "enum": [
          "Source",
          "Transformer",
          "Accumulator",
          "Store",
          "Controller",
          "Sink",
          "StreamProcessor",
          "Model",
          "APIEndpoint",
          "Router"
        ],
        "description": "Component base type"
      },
      "description": {
        "type": "string",
        "description": "Component description"
      },
      "processing_mode": {
        "type": "string",
        "enum": ["batch", "stream", "hybrid"],
        "description": "Data processing approach"
      },
      "inputs": {
        "type": "array",
        "items": {
          "$ref": "#/definitions/ComponentPort"
        },
        "description": "Component input ports"
      },
      "outputs": {
        "type": "array",
        "items": {
          "$ref": "#/definitions/ComponentPort"
        },
        "description": "Component output ports"
      },
      "properties": {
        "type": "array",
        "items": {
          "$ref": "#/definitions/PropertyConstraint"
        },
        "description": "Output property validation rules"
      },
      "contracts": {
        "type": "array",
        "items": {
          "$ref": "#/definitions/ContractConstraint"
        },
        "description": "Input/output contract validation rules"
      },
      "resource_requirements": {
        "$ref": "#/definitions/ArchitecturalResourceRequirements",
        "description": "Abstract resource requirements"
      },
      "architectural_config": {
        "$ref": "#/definitions/ArchitecturalComponentConfig",
        "description": "Architecture-level component configuration"
      },
      "dependencies": {
        "type": "array",
        "items": {
          "$ref": "#/definitions/ServiceDependency"
        },
        "description": "External service dependencies"
      },
      "implementation": {
        "$ref": "#/definitions/ComponentImplementation",
        "description": "Code generation specifications"
      },
      "security": {
        "$ref": "#/definitions/ComponentSecurity",
        "description": "Security requirements and authentication"
      },
      "quality_attributes": {
        "$ref": "#/definitions/QualityAttributes",
        "description": "Non-functional requirements"
      }
    },
    "additionalProperties": false
  }
}
```

### Key Schema Features:

1. **Port Flow Types**: Support for push, pull, and request_response patterns
2. **Fan-out Support**: Components can connect to multiple targets
3. **Conditional Routing**: Support for conditional data flow
4. **QoS Requirements**: Quality of service specifications
5. **Processing Modes**: Batch, stream, and hybrid processing
6. **Security Integration**: Built-in security requirements
7. **Quality Attributes**: Non-functional requirement specifications 

---

## APPENDIX E: PROPOSED ADR DOCUMENTS

### From: docs/reference/architecture/adr/proposed/022-multi-port-component-semantics.md

# ADR-022: Multi-Port Component Semantics

## Status
Proposed

## Context
The current component model uses a rigid Source/Transformer/Sink trichotomy that limits component flexibility. Components often need multiple, logically distinct inputs and outputs (e.g., a data input, a control-plane input, a primary data output, and a metrics side-channel output).

## Decision
Replace the rigid trichotomy with a flexible, port-based semantic model where a component's role is defined by the types of its named ports, explicitly declared in the architecture.yaml.

## Consequences

### Positive
- **Flexibility**: Components can have multiple, semantically distinct ports
- **Clarity**: Port purposes are explicit in the blueprint
- **Extensibility**: New port types can be added without breaking existing components
- **Validation**: ComponentRegistry can validate port type compatibility

### Negative
- **Complexity**: More complex blueprint validation
- **Learning Curve**: Developers need to understand port semantics
- **Migration**: Existing blueprints need updates

### Neutral
- **Performance**: No significant impact
- **Tooling**: Requires updates to code generation and validation tools

## Implementation

### Port Types
Define standard port types:
- `data_in`: Primary data input
- `data_out`: Primary data output  
- `control_in`: Control-plane commands
- `metrics_out`: Component-specific metrics

### Blueprint Syntax
```yaml
components:
  - name: data_enricher
    implementation: EnrichmentTransformer
    ports:
      raw_events: data_in
      control_commands: control_in
      enriched_events: data_out
      error_events: data_out
```

### Validation Rules
- ComponentRegistry validates port type compatibility
- Connections must link compatible port types
- Required ports must be connected

---

### From: docs/reference/architecture/adr/proposed/024-batched-processing-contracts.md

# ADR-024: Batched Processing Contracts

## Status
Proposed

## Context
Current components process items one at a time, which is inefficient for high-throughput scenarios. Many operations (database writes, API calls, ML inference) are more efficient when batched.

## Decision
Introduce batched processing contracts that allow components to process multiple items at once, with configurable batch sizes and processing strategies.

## Consequences

### Positive
- **Performance**: Significant throughput improvements for batch-friendly operations
- **Efficiency**: Reduced overhead for database and API operations
- **Flexibility**: Configurable batch sizes and strategies
- **Backward Compatibility**: Existing single-item processing still works

### Negative
- **Complexity**: More complex component implementations
- **Latency**: Potential increased latency for small batches
- **Memory**: Higher memory usage for large batches
- **Error Handling**: More complex error handling for partial batch failures

### Neutral
- **Tooling**: Requires updates to code generation
- **Testing**: More complex test scenarios needed

## Implementation

### Batch Configuration
```yaml
components:
  - name: batch_processor
    implementation: BatchTransformer
    config:
      batch_size: 100
      batch_timeout: 1.0  # seconds
      strategy: "size_or_timeout"  # or "size_only", "timeout_only"
```

### Processing Contracts
```python
async def process_batch(self, items: List[Any]) -> List[Any]:
    """Process multiple items at once"""
    # Batch processing logic
    return processed_items

async def process_item(self, item: Any) -> Any:
    """Process single item (for backward compatibility)"""
    return (await self.process_batch([item]))[0]
```

### Error Handling
- Partial batch failures return failed items
- Circuit breaker integration for batch failures
- Configurable retry strategies for failed batches

---

### From: docs/reference/architecture/adr/proposed/023-capability-re-entrancy-policy.md

# ADR-023: Capability Re-Entrancy Policy

## Status
Proposed

## Context
Capabilities can be called recursively when components are nested or when capabilities call other capabilities. This can lead to deadlocks, infinite loops, or unexpected behavior.

## Decision
Define a clear re-entrancy policy for capabilities that prevents deadlocks while maintaining flexibility.

## Consequences

### Positive
- **Safety**: Prevents deadlocks and infinite loops
- **Predictability**: Clear behavior for nested capability calls
- **Debugging**: Easier to debug capability interactions
- **Performance**: Avoids redundant capability execution

### Negative
- **Complexity**: More complex capability implementations
- **Overhead**: Additional tracking and validation
- **Restrictions**: Some capability combinations may be forbidden

### Neutral
- **Tooling**: Requires capability framework updates
- **Testing**: More complex test scenarios

## Implementation

### Re-Entrancy Rules
1. **Same Capability**: Prevent re-entry of the same capability type
2. **Capability Order**: Respect capability tier ordering
3. **Nested Calls**: Allow nested calls to different capability types
4. **Timeout Protection**: Prevent infinite capability chains

### Capability Context
```python
class CapabilityContext:
    def __init__(self):
        self.active_capabilities: Set[str] = set()
        self.capability_stack: List[str] = []
    
    def enter_capability(self, capability_name: str) -> bool:
        """Enter capability, return False if re-entry detected"""
        if capability_name in self.active_capabilities:
            return False
        self.active_capabilities.add(capability_name)
        self.capability_stack.append(capability_name)
        return True
    
    def exit_capability(self, capability_name: str):
        """Exit capability"""
        self.active_capabilities.discard(capability_name)
        if self.capability_stack and self.capability_stack[-1] == capability_name:
            self.capability_stack.pop()
```

### Validation
- Build-time validation of capability combinations
- Runtime detection of re-entrancy violations
- Automatic capability ordering based on tiers 

---

## APPENDIX F: COMPLETE COMPONENT REGISTRY IMPLEMENTATION

### From: autocoder_cc/components/component_registry.py

```python
#!/usr/bin/env python3
"""
Component Registry for V5.0 Validation-Driven Architecture
Implements centralized component discovery and validation with fail-hard principles
"""

from typing import Dict, Type, List, Any, Optional
import logging
import subprocess
import socket
import requests
from datetime import datetime
from .composed_base import ComposedComponent
from ..validation import ConstraintValidator, ValidationResult, ValidationError
from ..exceptions import SignatureMismatch
from pathlib import Path


class ComponentRegistryError(Exception):
    """Raised when component registry operations fail - no fallbacks available"""
    pass


class ComponentRegistry:
    """
    Enterprise Roadmap v3 Phase 0: Registry-Driven Generation Pipeline
    
    Central authority for component validation and instantiation using ComposedComponent architecture.
    Implements multi-stage validation lifecycle with fail-hard enforcement.
    """
    
    def __init__(self, *, lockfile_path: str | None = None):
        # Verify build.lock signature unless SKIP_SIGCHECK
        from autocoder_cc.lockfile import LockVerifier
        import os
        if os.getenv("SKIP_SIGCHECK") != "1":
            candidate = Path(lockfile_path or "build.lock.json")
            if candidate.exists():
                try:
                    LockVerifier.verify(candidate)
                    get_logger("ComponentRegistry").info("✅ build.lock signature verified")
                except (FileNotFoundError, subprocess.CalledProcessError, SignatureMismatch) as e:
                    raise ComponentRegistryError(f"Lockfile verification failed: {e}") from e

        # proceed with normal init
        
        self.logger = get_logger("ComponentRegistry")
        
        # Registry of component classes (ComposedComponent-based)
        self._component_classes: Dict[str, Type[ComposedComponent]] = {}
        
        # Registry of component instances
        self._component_instances: Dict[str, ComposedComponent] = {}
        
        # Component validation rules
        self._validation_rules: Dict[str, Dict[str, Any]] = {}
        
        # Policy constraints for components
        self._policy_constraints: Dict[str, List[Dict[str, Any]]] = {}
        
        # External service dependencies tracking
        self._external_dependencies: Dict[str, List[Dict[str, Any]]] = {}
        
        # Constraint validator for policy evaluation
        self._constraint_validator = ConstraintValidator()
        
        # AST validation rule engine for comprehensive code analysis
        from ..validation.ast_analyzer import ASTValidationRuleEngine
        self._ast_validator = ASTValidationRuleEngine({
            'rules_enabled': {
                'placeholder_detection': True,
                'component_pattern_validation': True,
                'hardcoded_value_detection': True,
                'code_quality_analysis': True
            },
            'severity_thresholds': {
                'critical': 0,  # Fail on any critical issues
                'high': 2,      # Allow up to 2 high severity issues  
                'medium': 5,    # Allow up to 5 medium severity issues
                'low': 10       # Allow up to 10 low severity issues
            }
        })
        
        # Register built-in component types
        self._register_builtin_components()
        
        self.logger.info("✅ Component Registry initialized with fail-hard validation and policy enforcement")
    
    def _register_builtin_components(self) -> None:
        """Register built-in ComposedComponent types using composition over inheritance"""
        
        # Register ComposedComponent for all component types
        # Composition-based architecture - behavior determined by configuration and capabilities
        self.register_component_class("Source", ComposedComponent)
        self.register_component_class("Transformer", ComposedComponent)
        self.register_component_class("StreamProcessor", ComposedComponent)  # Real-time stream processing
        self.register_component_class("Sink", ComposedComponent)
        self.register_component_class("Store", ComposedComponent)
        self.register_component_class("Controller", ComposedComponent)  # System orchestration
        self.register_component_class("APIEndpoint", ComposedComponent)
        self.register_component_class("Model", ComposedComponent)
        self.register_component_class("Accumulator", ComposedComponent)  # Missing component type
        self.register_component_class("Router", ComposedComponent)  # Phase 2 component
        self.register_component_class("Aggregator", ComposedComponent)  # Phase 2 component
        self.register_component_class("Filter", ComposedComponent)  # Phase 2 component
        
        self.logger.info("✅ Built-in ComposedComponent types registered with capability-based composition")
    
    def register_component_class(
        self, 
        component_type: str, 
        component_class: Type[ComposedComponent]
    ) -> None:
        """Register a component class with multi-stage validation"""
        
        # Implementation Validation: Validate component class inheritance
        if not issubclass(component_class, ComposedComponent):
            raise ComponentRegistryError(
                f"Component class '{component_class.__name__}' must inherit from ComposedComponent. "
                f"Enterprise Roadmap v3 Phase 0 requires composition over inheritance - no complex hierarchies allowed."
            )
        
        # Check for abstract methods implementation
        try:
            # Try to get required methods
            component_class.get_required_config_fields
            component_class.get_required_dependencies
        except AttributeError:
            raise ComponentRegistryError(
                f"Component class '{component_class.__name__}' must implement required abstract methods. "
                f"V5.0 requires complete component implementation - no partial implementations allowed."
            )
        
        # Register the component class
        self._component_classes[component_type] = component_class
        
        # Initialize validation rules for this component type
        self._validation_rules[component_type] = {
            'required_config_fields': [],
            'required_dependencies': [],
            'schema_requirements': {}
        }
        
        self.logger.info(f"✅ Registered component class: {component_type}")
    
    def create_component(
        self, 
        component_type: str, 
        name: str, 
        config: Dict[str, Any]
    ) -> ComposedComponent:
        """Create and validate a component instance"""
        
        # Validate component type is registered
        if component_type not in self._component_classes:
            available_types = list(self._component_classes.keys())
            raise ComponentRegistryError(
                f"Unknown component type '{component_type}'. "
                f"Available types: {available_types}. "
                f"V5.0 requires explicit component registration - no dynamic type inference."
            )
        
        # Validate component name uniqueness
        if name in self._component_instances:
            raise ComponentRegistryError(
                f"Component name '{name}' already exists. "
                f"V5.0 requires unique component names - no name conflicts allowed."
            )
        
        # Get component class
        component_class = self._component_classes[component_type]
        
        # Pre-validate configuration requirements
        self._validate_component_config(component_type, config)
        
        # Validate policy constraints
        self._validate_policy_constraints(component_type, name, config)
        
        # Validate external dependencies
        self._validate_external_dependencies(name, config)
        
        try:
            # Create component instance (this will trigger validation)
            component_instance = component_class(name, config)
            
            # Set component_type for component instances
            if hasattr(component_instance, 'component_type'):
                component_instance.component_type = component_type
            
            # Final fail-hard check - prevent instantiation with missing dependencies
            self._enforce_fail_hard_behavior(component_instance)
            
            # Register the instance
            self._component_instances[name] = component_instance
            
            self.logger.info(f"✅ Created and registered component: {name} ({component_type})")
            return component_instance
            
        except Exception as e:
            raise ComponentRegistryError(
                f"Failed to create component '{name}' of type '{component_type}': {e}. "
                f"V5.0 components must initialize successfully - no partial initialization allowed."
            )
    
    def _validate_component_config(self, component_type: str, config: Dict[str, Any]) -> None:
        """Validate component configuration against type requirements"""
        
        # Get component class for validation
        component_class = self._component_classes[component_type]
        
        # Create temporary instance to get requirements (without full initialization)
        try:
            temp_instance = object.__new__(component_class)
            temp_instance.config = config
            temp_instance.name = "temp_validation"
            
            # Get required fields
            required_fields = temp_instance.get_required_config_fields()
            required_dependencies = temp_instance.get_required_dependencies()
            
        except (AttributeError, TypeError, ValueError) as e:
            raise ComponentRegistryError(
                f"Failed to validate component type '{component_type}' requirements: {e}"
            )
        
        # Validate required configuration fields
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            raise ComponentRegistryError(
                f"Missing required configuration fields for {component_type}: {missing_fields}. "
                f"V5.0 requires all configuration fields - no defaults or fallbacks available."
            )
        
        # Validate component logic based on type
        self._validate_component_logic(component_type, config)
        
        self.logger.debug(f"✅ Configuration validated for {component_type}")
    
    def _validate_component_logic(self, component_type: str, config: Dict[str, Any]) -> None:
        """Validate component logic based on type-specific rules"""
        
        # CRITICAL FIX: Port auto-generation puts ports in component.inputs/outputs, not config
        # We need to validate the actual component structure, not just the config
        # For now, skip port validation since it's handled by port auto-generator
        
        # Validate source component logic
        if component_type == "Source" and (config.get('inputs') or not config.get('outputs')):
            raise ComponentRegistryError(
                "Source components must have outputs and no inputs. "
                "V5.0 requires strict component semantics - no mixed-mode components."
            )
        
        # Validate sink component logic
        if component_type == "Sink" and (not config.get('inputs') or config.get('outputs')):
            raise ComponentRegistryError(
                "Sink components must have inputs and no outputs. "
                "V5.0 requires strict component semantics - no mixed-mode components."
            )
        
        # Validate transformer component logic
        if component_type == "Transformer" and (not config.get('inputs') or not config.get('outputs')):
            raise ComponentRegistryError(
                "Transformer components must have both inputs and outputs. "
                "V5.0 requires strict component semantics - no mixed-mode components."
            )
        
        self.logger.debug(f"✅ Component logic validated for {component_type}")
    
    def get_component(self, name: str) -> ComposedComponent:
        """Get a component instance by name with fail-hard checks"""
        if name not in self._component_instances:
            raise ComponentRegistryError(
                f"Component '{name}' not found in registry. "
                f"V5.0 requires all components to be registered - no dynamic creation."
            )
        return self._component_instances[name]
    
    def list_component_types(self) -> List[str]:
        """List all registered component types"""
        return list(self._component_classes.keys())
    
    def list_component_instances(self) -> List[str]:
        """List all instantiated component names"""
        return list(self._component_instances.keys())
    
    def validate_component_dependencies(self, name: str) -> bool:
        """Validate dependencies for a specific component"""
        if name not in self._component_instances:
            raise ComponentRegistryError(f"Component '{name}' not found for dependency validation.")
        
        component = self._component_instances[name]
        required_dependencies = component.get_required_dependencies()
        
        for dep in required_dependencies:
            if dep not in self._component_instances:
                raise ComponentRegistryError(
                    f"Missing dependency '{dep}' for component '{name}'. "
                    f"V5.0 requires all dependencies to be explicitly defined and available."
                )
        
        return True
    
    def validate_all_components(self) -> Dict[str, bool]:
        """Validate dependencies for all components"""
        
        # Fail-hard check for circular dependencies
        from ..validation.dependency_analyzer import DependencyAnalyzer
        
        dependency_graph = {}
        for name, component in self._component_instances.items():
            dependency_graph[name] = component.get_required_dependencies()
            
        analyzer = DependencyAnalyzer(dependency_graph)
        circular_dependencies = analyzer.find_circular_dependencies()
        
        if circular_dependencies:
            raise ComponentRegistryError(
                f"Circular dependencies detected: {circular_dependencies}. "
                f"V5.0 architecture prohibits circular dependencies - must be resolved."
            )
        
        # Validate dependencies for each component
        validation_results = {}
        for name in self._component_instances:
            try:
                validation_results[name] = self.validate_component_dependencies(name)
            except ComponentRegistryError as e:
                self.logger.error(f"Dependency validation failed for '{name}': {e}")
                validation_results[name] = False
                
        return validation_results
    
    # Policy and constraint management
    def register_policy_constraints(self, component_type: str, constraints: List[Dict[str, Any]]) -> None:
        """Register policy constraints for a component type"""
        if component_type not in self._policy_constraints:
            self._policy_constraints[component_type] = []
        self._policy_constraints[component_type].extend(constraints)
        self.logger.info(f"✅ Registered {len(constraints)} policy constraints for {component_type}")
    
    def _validate_policy_constraints(self, component_type: str, component_name: str, config: Dict[str, Any]) -> None:
        """Validate a component's configuration against registered policy constraints"""
        
        # Validate against component-specific policies
        if component_type in self._policy_constraints:
            component_policies = self._policy_constraints[component_type]
            
            for policy in component_policies:
                validation_result = self._constraint_validator.validate(config, policy)
                
                if not validation_result.is_valid:
                    raise ComponentRegistryError(
                        f"Policy violation in component '{component_name}' of type '{component_type}': "
                        f"{validation_result.errors}. "
                        f"V5.0 requires all components to adhere to policy constraints."
                    )
        
        # Validate against global blueprint policy if set
        if hasattr(self, '_blueprint_policy'):
            self._validate_blueprint_policy_constraints(
                component_name, component_type, config, self._blueprint_policy
            )
        
        self.logger.debug(f"✅ Policy constraints validated for {component_name} ({component_type})")
    
    def _validate_blueprint_policy_constraints(self, component_name: str, component_type: str, 
                                             config: Dict[str, Any], blueprint_policy: Dict[str, Any]) -> None:
        """Validate component configuration against blueprint-level policy constraints"""
        
        if not blueprint_policy:
            return
        
        # Global constraints for all components
        global_constraints = blueprint_policy.get('global_constraints', [])
        for constraint in global_constraints:
            result = self._constraint_validator.validate(config, constraint)
            if not result.is_valid:
                raise ComponentRegistryError(
                    f"Global policy violation in component '{component_name}': {result.errors}"
                )
        
        # Per-component-type constraints
        type_constraints = blueprint_policy.get('component_constraints', {}).get(component_type, [])
        for constraint in type_constraints:
            result = self._constraint_validator.validate(config, constraint)
            if not result.is_valid:
                raise ComponentRegistryError(
                    f"Component-type policy violation in component '{component_name}': {result.errors}"
                )
        
        # Security constraints
        security_constraints = blueprint_policy.get('security_constraints', {})
        component_security_config = config.get('security', {})
        
        # Validate authentication requirements
        auth_required = security_constraints.get('authentication_required', True)
        if auth_required and 'authentication' not in component_security_config:
            raise ComponentRegistryError(f"Missing required authentication configuration for '{component_name}'")
        
        # Validate authorization requirements
        authz_required = security_constraints.get('authorization_required', True)
        if authz_required and 'authorization' not in component_security_config:
            raise ComponentRegistryError(f"Missing required authorization configuration for '{component_name}'")
        
        # Validate encryption requirements
        encryption_constraints = security_constraints.get('encryption', {})
        if encryption_constraints.get('data_in_transit', True):
            if not component_security_config.get('tls_enabled', True):
                raise ComponentRegistryError(f"TLS must be enabled for '{component_name}'")
        
        # Validate logging requirements
        logging_constraints = blueprint_policy.get('logging_constraints', {})
        log_level_required = logging_constraints.get('minimum_log_level', 'INFO')
        component_log_level = config.get('logging', {}).get('level', 'INFO')
        
        log_levels = {'DEBUG': 1, 'INFO': 2, 'WARNING': 3, 'ERROR': 4, 'CRITICAL': 5}
        if log_levels.get(component_log_level, 0) < log_levels.get(log_level_required, 2):
            raise ComponentRegistryError(
                f"Log level for '{component_name}' is too low. Required: {log_level_required}"
            )
        
        # Validate resource limits
        resource_constraints = blueprint_policy.get('resource_constraints', {})
        component_resources = config.get('resources', {})
        
        max_cpu = resource_constraints.get('max_cpu')
        if max_cpu and component_resources.get('cpu_limit', 0) > max_cpu:
            raise ComponentRegistryError(f"CPU limit for '{component_name}' exceeds policy limit")
        
        max_memory_mb = resource_constraints.get('max_memory_mb')
        if max_memory_mb and component_resources.get('memory_limit_mb', 0) > max_memory_mb:
            raise ComponentRegistryError(f"Memory limit for '{component_name}' exceeds policy limit")
        
        self.logger.debug(f"✅ Blueprint policy constraints validated for {component_name}")
    
    def set_blueprint_policy(self, blueprint_policy: Dict[str, Any]) -> None:
        """Set blueprint-level policy constraints"""
        self._blueprint_policy = blueprint_policy
        self.logger.info("✅ Blueprint policy set successfully")
    
    def validate_system_against_blueprint_policy(self, system_blueprint_data: Dict[str, Any]) -> None:
        """Validate a full system blueprint against the policy"""
        
        if not hasattr(self, '_blueprint_policy'):
            self.logger.warning("No blueprint policy set, skipping validation")
            return
        
        components = system_blueprint_data.get('components', [])
        
        # Validate each component against policy
        for component_config in components:
            component_type = component_config.get('type')
            component_name = component_config.get('name')
            
            if not component_type or not component_name:
                raise ComponentRegistryError("Component type and name are required in blueprint")
            
            self._validate_policy_constraints(component_type, component_name, component_config)
        
        # Validate bindings against policy
        bindings = system_blueprint_data.get('bindings', [])
        allowed_bindings = self._blueprint_policy.get('allowed_bindings', {})
        
        if allowed_bindings:
            for binding in bindings:
                from_component_type = self._get_component_type_by_name(binding['from_component'])
                to_component_type = self._get_component_type_by_name(binding['to_component'])
                
                if from_component_type not in allowed_bindings:
                    raise ComponentRegistryError(
                        f"Binding from '{from_component_type}' is not allowed by policy"
                    )
                
                allowed_targets = allowed_bindings[from_component_type]
                if to_component_type not in allowed_targets:
                    raise ComponentRegistryError(
                        f"Binding from '{from_component_type}' to '{to_component_type}' is not allowed by policy"
                    )
        
        # Validate external service usage
        allowed_external_services = self._blueprint_policy.get('allowed_external_services')
        if allowed_external_services:
            for component_config in components:
                dependencies = component_config.get('dependencies', [])
                for dep in dependencies:
                    if dep['type'] not in allowed_external_services:
                        raise ComponentRegistryError(
                            f"External service '{dep['type']}' is not allowed by policy"
                        )
        
        self.logger.info("✅ System blueprint validated against policy successfully")
    
    def _get_component_type_by_name(self, component_name: str) -> str:
        """Get component type from instance name"""
        component = self.get_component(component_name)
        if hasattr(component, 'component_type'):
            return component.component_type
        raise ComponentRegistryError(f"Could not determine type for component '{component_name}'")
    
    # External dependency validation
    def _validate_external_dependencies(self, component_name: str, config: Dict[str, Any]) -> None:
        """Validate external dependencies for a component"""
        
        # Skip validation if env var is set
        import os
        if os.getenv("SKIP_DEPENDENCY_VALIDATION") == "1":
            self.logger.warning("Skipping external dependency validation due to environment variable")
            return
        
        dependencies = config.get('dependencies', [])
        
        if not dependencies:
            self.logger.debug(f"No external dependencies to validate for {component_name}")
            return
        
        # Validate each dependency
        for dependency in dependencies:
            if not self._check_dependency_availability(dependency):
                raise ComponentRegistryError(
                    f"External dependency '{dependency.get('name')}' for component '{component_name}' is not available. "
                    f"V5.0 requires all external dependencies to be reachable at startup."
                )
        
        self.logger.info(f"✅ External dependencies validated for {component_name}")
    
    # Fail-hard behavior for dependency checks
    def _check_dependency_availability(self, dependency: Dict[str, Any]) -> bool:
        """Check availability of an external dependency"""
        
        dep_type = dependency.get('type')
        
        if dep_type == 'database':
            return self._check_database_availability(dependency)
        elif dep_type == 'message_queue':
            return self._check_message_queue_availability(dependency)
        elif dep_type == 'external_service':
            return self._check_external_service_availability(dependency)
        else:
            self.logger.warning(f"Unknown dependency type: {dep_type}")
            return False
    
    def _check_database_availability(self, dependency: Dict[str, Any]) -> bool:
        """Check database connection availability"""
        
        import os
        db_url = os.getenv(dependency.get('connection_env_var'))
        if not db_url:
            self.logger.error(f"Database connection environment variable not set: {dependency.get('connection_env_var')}")
            return False
        
        db_type = dependency.get('db_type', 'postgresql')
        
        try:
            if db_type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(db_url)
                conn.close()
            elif db_type == 'mysql':
                import mysql.connector
                conn = mysql.connector.connect(db_url)
                conn.close()
            elif db_type == 'redis':
                import redis
                r = redis.from_url(db_url)
                r.ping()
            else:
                self.logger.warning(f"Unsupported database type: {db_type}")
                return False
                
            self.logger.info(f"✅ Database connection successful: {dependency.get('name')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection failed for '{dependency.get('name')}': {e}")
            return False
    
    def _check_message_queue_availability(self, dependency: Dict[str, Any]) -> bool:
        """Check message queue connection availability"""
        
        import os
        mq_url = os.getenv(dependency.get('connection_env_var'))
        if not mq_url:
            self.logger.error(f"Message queue connection environment variable not set: {dependency.get('connection_env_var')}")
            return False
        
        mq_type = dependency.get('mq_type', 'rabbitmq')
        
        try:
            if mq_type == 'rabbitmq':
                import pika
                connection = pika.BlockingConnection(pika.URLParameters(mq_url))
                connection.close()
            elif mq_type == 'kafka':
                from kafka import KafkaProducer
                producer = KafkaProducer(bootstrap_servers=mq_url)
                producer.close()
            else:
                self.logger.warning(f"Unsupported message queue type: {mq_type}")
                return False
                
            self.logger.info(f"✅ Message queue connection successful: {dependency.get('name')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Message queue connection failed for '{dependency.get('name')}': {e}")
            return False
    
    def _check_external_service_availability(self, dependency: Dict[str, Any]) -> bool:
        """Check external service availability"""
        
        service_url = dependency.get('url')
        health_endpoint = dependency.get('health_endpoint', '/health')
        
        if not service_url:
            self.logger.error("External service URL is not defined")
            return False
        
        full_url = f"{service_url.rstrip('/')}/{health_endpoint.lstrip('/')}"
        
        try:
            response = requests.get(full_url, timeout=5)
            response.raise_for_status()
            
            self.logger.info(f"✅ External service is healthy: {full_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"External service health check failed for '{full_url}': {e}")
            return False
    
    def _check_tcp_connectivity(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Check TCP connectivity to a host and port"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error) as e:
            self.logger.error(f"TCP connectivity check failed for {host}:{port} - {e}")
            return False
    
    def _enforce_fail_hard_behavior(self, component_instance: ComposedComponent) -> None:
        """Enforce fail-hard behavior by checking for placeholder logic"""
        
        # Analyze component code for placeholders
        from ..validation.ast_analyzer import analyze_code_for_placeholders
        
        # This requires getting the source code of the component class
        import inspect
        try:
            source_code = inspect.getsource(component_instance.__class__)
            analysis_result = analyze_code_for_placeholders(source_code)
            
            if analysis_result['placeholders_found']:
                raise ComponentRegistryError(
                    f"Placeholder logic detected in component '{component_instance.name}'. "
                    f"V5.0 prohibits placeholder implementations - component must be fully implemented."
                    f"Details: {analysis_result['details']}"
                )
            
            # Validate against hardcoded values
            hardcoded_values = self._ast_validator.analyze_code(
                source_code, rules_to_run=['hardcoded_value_detection']
            )
            if hardcoded_values['hardcoded_values']:
                raise ComponentRegistryError(
                    f"Hardcoded values detected in component '{component_instance.name}': "
                    f"{hardcoded_values['hardcoded_values']}. "
                    f"V5.0 requires configuration-driven components - no hardcoded values allowed."
                )
            
            # Code quality validation
            code_quality_issues = self._ast_validator.analyze_code(
                source_code, rules_to_run=['code_quality_analysis']
            )
            if code_quality_issues['issues']:
                raise ComponentRegistryError(
                    f"Code quality issues detected in component '{component_instance.name}': "
                    f"{code_quality_issues['issues']}. "
                    f"V5.0 requires high code quality - issues must be resolved."
                )
            
        except (TypeError, OSError):
            # This can happen for dynamically generated classes
            self.logger.warning(f"Could not get source code for component '{component_instance.name}'")
    
    def create_component_from_blueprint(self, component_config: Dict[str, Any]) -> ComposedComponent:
        """Create a component instance from a blueprint configuration"""
        
        # Validate required fields
        if 'name' not in component_config or 'type' not in component_config:
            raise ComponentRegistryError(
                "Component name and type are required in blueprint configuration. "
                "V5.0 requires explicit component definition - no implicit creation."
            )
        
        component_name = component_config['name']
        component_type = component_config['type']
        
        # Add 'implementation' to config if not present for compatibility
        if 'implementation' not in component_config:
            component_config['implementation'] = {'language': 'python'}
        
        # Create the component
        return self.create_component(
            component_type=component_type,
            name=component_name,
            config=component_config
        )
    
    def create_system_components(self, blueprint_data: Dict[str, Any]) -> Dict[str, ComposedComponent]:
        """Create all components defined in a system blueprint"""
        
        components_config = blueprint_data.get('components', [])
        
        # Validate component names are unique
        component_names = [c['name'] for c in components_config]
        if len(component_names) != len(set(component_names)):
            raise ComponentRegistryError(
                "Duplicate component names detected in blueprint. "
                "V5.0 requires unique component names across the system."
            )
        
        # Create all components
        for component_config in components_config:
            self.create_component_from_blueprint(component_config)
            
        return self._component_instances
    
    def clear_registry(self) -> None:
        """Clear all registered component classes and instances"""
        self._component_classes.clear()
        self._component_instances.clear()
        self._validation_rules.clear()
        self._policy_constraints.clear()
        self._external_dependencies.clear()
        self._register_builtin_components()  # Re-register built-ins
        self.logger.info("✅ Component registry cleared")
    
    # Comprehensive component file validation
    def validate_component_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a component file using AST analysis for comprehensive checks.
        
        This method performs a deep analysis of the component's source code,
        checking for:
        - Placeholder logic (e.g., pass, NotImplementedError)
        - Hardcoded sensitive values (e.g., passwords, API keys)
        - Adherence to component design patterns
        - Code quality metrics (e.g., cyclomatic complexity)
        - Security vulnerabilities (e.g., use of insecure functions)
        """
        
        self.logger.info(f"🔬 Starting AST validation for component file: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                source_code = f.read()
        except FileNotFoundError:
            raise ComponentRegistryError(f"Component file not found: {file_path}")
        except Exception as e:
            raise ComponentRegistryError(f"Failed to read component file '{file_path}': {e}")
        
        # Initialize validation result
        validation_report = {
            'file_path': file_path,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'analysis': {}
        }
        
        # Run all AST validation rules
        try:
            ast_analysis = self._ast_validator.analyze_code(source_code)
            
            validation_report['analysis'] = ast_analysis
            
            # Check for critical issues that should fail validation
            if ast_analysis.get('severity', {}).get('critical', 0) > 0:
                validation_report['status'] = 'failed'
                validation_report['errors'].append("Critical severity issues detected")
                
            if ast_analysis.get('placeholders_found'):
                validation_report['status'] = 'failed'
                validation_report['errors'].append("Placeholder implementation detected")
            
            # Check for hardcoded secrets
            hardcoded_secrets = ast_analysis.get('hardcoded_values', {}).get('secrets', [])
            if hardcoded_secrets:
                validation_report['status'] = 'failed'
                validation_report['errors'].append(f"Hardcoded secrets found: {hardcoded_secrets}")
            
            # Add warnings for other issues
            if ast_analysis.get('severity', {}).get('high', 0) > 0:
                validation_report['warnings'].append("High severity issues detected")
            
            if not validation_report['errors']:
                self.logger.info(f"✅ AST validation passed for: {file_path}")
            else:
                self.logger.error(f"❌ AST validation failed for: {file_path}")
                
        except Exception as e:
            validation_report['status'] = 'failed'
            validation_report['errors'].append(f"AST validation engine failed: {e}")
            self.logger.error(f"AST validation engine failed for '{file_path}': {e}")
        
        return validation_report
    
    def validate_component_code(self, component_name: str, component_code: str) -> Dict[str, Any]:
        """Validate a string of component code using AST analysis"""
        
        self.logger.info(f"🔬 Starting AST validation for component code: {component_name}")
        
        # Initialize validation result
        validation_report = {
            'component_name': component_name,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'analysis': {}
        }
        
        # Run all AST validation rules
        try:
            ast_analysis = self._ast_validator.analyze_code(component_code)
            
            validation_report['analysis'] = ast_analysis
            
            # Check for critical issues that should fail validation
            if ast_analysis.get('severity', {}).get('critical', 0) > 0:
                validation_report['status'] = 'failed'
                validation_report['errors'].append("Critical severity issues detected")
                
            if ast_analysis.get('placeholders_found'):
                validation_report['status'] = 'failed'
                validation_report['errors'].append("Placeholder implementation detected")
            
            # Check for hardcoded secrets
            hardcoded_secrets = ast_analysis.get('hardcoded_values', {}).get('secrets', [])
            if hardcoded_secrets:
                validation_report['status'] = 'failed'
                validation_report['errors'].append(f"Hardcoded secrets found: {hardcoded_secrets}")
            
            # Add warnings for other issues
            if ast_analysis.get('severity', {}).get('high', 0) > 0:
                validation_report['warnings'].append("High severity issues detected")
            
            if not validation_report['errors']:
                self.logger.info(f"✅ AST validation passed for code: {component_name}")
            else:
                self.logger.error(f"❌ AST validation failed for code: {component_name}")
                
        except Exception as e:
            validation_report['status'] = 'failed'
            validation_report['errors'].append(f"AST validation engine failed: {e}")
            self.logger.error(f"AST validation engine failed for code '{component_name}': {e}")
        
        return validation_report
    
    def validate_all_component_files(self, component_directory: str) -> Dict[str, Any]:
        """Validate all component files in a directory"""
        
        all_results = {}
        component_files = list(Path(component_directory).glob('*.py'))
        
        if not component_files:
            self.logger.warning(f"No component files found in directory: {component_directory}")
            return {}
        
        for file_path in component_files:
            if file_path.name == '__init__.py':
                continue
            
            report = self.validate_component_file(str(file_path))
            all_results[file_path.name] = report
            
        # Summary report
        total_files = len(all_results)
        passed_files = sum(1 for report in all_results.values() if report['status'] == 'passed')
        failed_files = total_files - passed_files
        
        summary = {
            'total_files': total_files,
            'passed': passed_files,
            'failed': failed_files,
            'results': all_results
        }
        
        self.logger.info(f"Component validation summary: {passed_files}/{total_files} passed.")
        return summary
