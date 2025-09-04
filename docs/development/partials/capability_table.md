| Capability | Tier | Status | Purpose |
|---|---|---|---|
| `SchemaValidator` | 10 | **Stable** | Strict data-contract enforcement using Pydantic. |
| `RateLimiter` | 20 | **Stub** | Controls throughput to downstream systems. |
| `StateCapability` | 30 | **Stub** | Provides pluggable, durable state (in-memory, Redis, etc.). |
| `RetryHandler` | 40 | **Stub** | Exponential-backoff retries for transient faults. |
| `CircuitBreaker` | 50 | **Stub** | Halts calls to unhealthy services. |
| `MetricsCollector` | 90 | **Stable** | Emits structured RED metrics for observability. | 