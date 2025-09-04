# Runtime Orchestration Architecture

## Overview

The Autocoder runtime is built on a high-performance, asynchronous orchestration layer designed for correctness, resilience, and observability. Its sole responsibility is to manage the lifecycle and data flow of the instantiated components according to the blueprint's instructions. This document outlines the architectural principles of that runtime.

## Core Technology: `anyio`

The runtime is built entirely on `anyio`, a high-level structured concurrency library. This choice provides several key architectural benefits:
- **Async-Native:** The entire system runs in a native asynchronous event loop.
- **Structured Concurrency:** All components run as tasks within a single, top-level `anyio.TaskGroup`. This guarantees that all tasks are properly supervised and that the system can shut down cleanly without leaving orphaned processes.
- **Transport-Agnostic:** `anyio` supports both `asyncio` and `trio`, making the core runtime adaptable to different event loop backends.

## The SystemExecutionHarness

The `SystemExecutionHarness` is the conductor of the orchestra. It is the central entity that loads a validated `architecture.yaml` and its corresponding `deployment.yaml` to manage the runtime execution.

### The Three-Phase Lifecycle

The harness manages all components through a strict, three-phase lifecycle to ensure deterministic startup and shutdown:

1.  **Setup Phase (`setup()`):**
    *   The harness iterates through all components and calls their `setup()` method.
    *   This is where components acquire resources like database connections, load machine learning models, or initialize internal state.
    *   The capability chain is also set up during this phase.

2.  **Process Phase (`process()`):**
    *   Once all components are set up, the harness starts the `process()` method for each component within the main task group.
    *   This is the main operational loop where components receive data from their input streams, process it through their capability chain and business logic, and send results to their output streams.
    *   All components run concurrently.

3.  **Cleanup Phase (`cleanup()`):**
    *   Triggered by a graceful shutdown signal (e.g., `SIGINT`, `SIGTERM`).
    *   The harness cancels the main task group scope, which in turn cancels all running `process()` tasks.
    *   It then calls the `cleanup()` method on each component to release resources, flush buffers, and ensure a clean exit.

## Data Flow: Asynchronous Memory Streams

All data flows between components are architected as `anyio.MemoryObjectStream`.

-   **Decoupled Communication:** Components are fully decoupled. They do not have direct references to each other; they only know about their input and output streams. The harness is responsible for "wiring" the streams together according to the `bindings` in the blueprint.
-   **Backpressure by Design:** The streams are bounded (i.e., they have a maximum buffer size). If a downstream component processes data slower than an upstream component produces it, the stream buffer will fill up. This automatically exerts backpressure on the sending component, preventing out-of-memory errors and creating a self-regulating system.
-   **Configurable Buffers:** The architecture specifies that stream buffer sizes should be configurable to allow for performance tuning in different scenarios.

## Harness-Aggregated Batching (ADR-024)

The runtime supports harness-managed batch processing for improved throughput:

-   **Batch Formation:** The harness accumulates items until size (`max_items`) or time (`max_ms`) thresholds are met, then passes a `list[Event]` to the component.
-   **Vectorized Capabilities:** Capabilities can implement batch-aware hooks (`before_receive_batch`, `after_send_batch`) for performance optimization.
-   **Error Handling:** Configurable error modes (`fail_fast`, `per_item`) determine how batch failures are handled.
-   **Deterministic Metadata:** Each batch includes metadata (batch_id, size, timestamps) for observability and debugging.

## Performance & Scaling Model

## Scaling Architecture: Single-Process Design Choice

### **Current Design: Single-Process Optimization**

The current runtime, based on `anyio.MemoryObjectStream`, is **deliberately designed** for high-performance **single-process parallelism**. This architectural choice prioritizes:

**Advantages:**
- **Simplicity**: No network serialization, distributed consensus, or partition tolerance complexity
- **Performance**: Memory-speed communication between components (nanosecond latency)
- **Reliability**: No network failures, message loss, or distributed system failure modes
- **Development Velocity**: Easier debugging, testing, and development workflow
- **Resource Efficiency**: Lower memory overhead, no network protocol stack

**Trade-offs:**
- **Horizontal Scaling**: Limited to single-machine resources (CPU, memory)
- **GIL Constraints**: Python GIL limits true CPU parallelism for CPU-bound workloads
- **Fault Isolation**: Component failures can affect entire system process

### **Scaling Strategy: Start Simple, Scale When Needed**

This follows the architectural principle of **avoiding premature optimization**:

1. **Phase 1 (Current)**: Single-process for simplicity and development speed
2. **Phase 2 (Future)**: Pluggable transport layer for distributed scaling when required
3. **Migration Path**: Transport abstraction allows seamless upgrade without application changes

### **When to Scale Beyond Single-Process**

Consider distributed scaling when systems require:
- **Throughput**: >10,000 requests/second sustained load
- **Fault Isolation**: Component failures must not affect other components
- **Geographic Distribution**: Components must run in different data centers
- **Regulatory Compliance**: Data processing must be isolated by jurisdiction

### **Future Evolution: Distributed Transport**

Scaling beyond a single process is a **planned architectural evolution** requiring:
- **Transport Layer**: Redis Streams, NATS, or Kafka for inter-component communication
- **Service Discovery**: Component registry and health checking
- **Failure Handling**: Circuit breakers, retry policies, and partition tolerance
- **Deployment Complexity**: Container orchestration and distributed system operations

**Implementation Timeline**: Multi-node transport planned for P2 Enterprise Features phase.

## Capability Chain Execution

The harness ensures that for each item of data a component processes, the full chain of composed capabilities is executed in the **deterministic order loaded from the `build.lock`**. This guarantees that behaviors like rate limiting, retries, and schema validation occur in the same sequence for every build.

## Health, Metrics, and Alerting

The runtime architecture provides deep insight into a running system.

-   **Mandatory Health & Metrics API:** The harness **must** expose a detailed API for observing the system on a secure, authenticated endpoint. This includes granular metrics (e.g., per-capability status) and the ability to generate alerts based on system state. This is not optional.
-   **Error Enrichment:** The `ConsistentErrorHandler` enriches all error reports with system resource metrics (e.g., via `psutil`) to provide context for debugging.

## State Persistence & Recovery (ADR-028)

The runtime provides enterprise-grade state persistence for stateful components:

-   **Pluggable State Adapters:** Components can use `redis_snapshot` (default) or `inmem_ephemeral` adapters for state storage.
-   **Automatic Checkpointing:** State is automatically persisted at configurable intervals (`checkpoint_interval_s`).
-   **Graceful Degradation:** State persistence failures are handled with fail-soft semantics, allowing the system to continue operating.
-   **Recovery Support:** The harness can resume component state from the last successful checkpoint during restart.

## Local Development and Tooling

The runtime architecture must also support a high-velocity local development experience.

-   **LocalOrchestratorCLI:** The design includes a command-line tool for local orchestration that supports features like hot-reloading of components and resuming a system's state from a checkpoint to facilitate debugging and iterative development. 