# Observability Architecture

## Overview

The Autocoder system is built with a "glass box" philosophy. The architecture **mandates** deep, comprehensive, and out-of-the-box observability for every generated system. This is achieved through three core pillars: structured logging, hierarchical metrics, and distributed tracing. These features are not optional.

## Guiding Principles

1.  **Enabled by Default:** Core observability (logging, RED metrics) **is mandatory and non-bypassable**.
2.  **Deterministic:** All metrics and logs must include deterministic tags (component name, tier, etc.) for easy aggregation and filtering.
3.  **Tiered Insight:** The architecture provides insight into each layer of the system, from high-level component health down to individual capability performance.
4.  **Open Standards:** The system uses open standards like OpenTelemetry to ensure compatibility with a wide range of monitoring tools.

---

## Pillar 1: Structured Logging

The architecture provides a centralized, structured logging system.

### Requirements

*   **JSON Output:** All logs **must** be emitted as JSON objects to be easily parsed by modern log aggregation platforms (e.g., Datadog, Splunk, Elastic).
*   **Automatic Context:** Every log entry **is** automatically enriched with contextual information, including:
    *   `component_name`
    *   `trace_id` and `span_id` (when a trace is active)
*   **Resource Enrichment:** Error logs **are** enriched with system resource information (e.g., CPU, memory usage via `psutil`) to aid in diagnosing production issues.

---

## Pillar 2: Hierarchical Metrics

The architecture provides a powerful, multi-layered metrics system based on the four golden signals (Latency, Traffic, Errors, Saturation).

### Requirements

*   **RED Metrics by Default:** Every component **must** automatically expose Rate, Errors, and Duration (latency) metrics for its primary operations.
*   **Tiered Latency Histograms:** A `TierMetricsCollector` **must** measure and expose latency histograms for each individual capability in the processing chain to identify performance bottlenecks.
*   **Standardized Labels:** All metrics **must** be tagged with consistent labels (`component_name`, `capability_tier`, `status`) for aggregation.
*   **Secure Prometheus Exposition:** The system **must** expose metrics in the Prometheus text-exposition format via a standard `/metrics` endpoint. This endpoint **is secure by default** and requires authentication.

---

## Pillar 3: Distributed Tracing

The architecture provides end-to-end distributed tracing to follow requests as they flow through the system.

### Requirements

*   **OpenTelemetry SDK:** The system **uses** the OpenTelemetry SDK as its core tracing implementation.
*   **Automatic Context Propagation:** Trace context **is** automatically propagated across component boundaries, including through message buses.
*   **Traced Components:** A `TracedComponent` mixin or similar decorator **is** used to automatically start and end spans for the primary `process` method of each component.

*> **Note on Performance-Critical Paths:** For components with microsecond-level performance requirements, the standard OpenTelemetry SDK may introduce unacceptable overhead. The architecture acknowledges that a lower-overhead, binary logging format is a considered future optimization for these specific hot-path scenarios.*

---

## Pillar 4: Alerting

The architecture includes a built-in alerting pipeline.

### Requirements

*   **Threshold-Based Alerts:** The system **is** able to generate alerts when key metrics (e.g., error rate, latency p99) cross pre-defined thresholds.
*   **Integrations:** An `AlertIntegrator` **is** responsible for sending notifications to external systems like Slack and PagerDuty.

---

## Pillar 5: Visualization

The architecture requires that the system auto-generate baseline visualization assets.

### Requirements

*   **Grafana Dashboards:** The scaffolder **must** be capable of generating a default Grafana dashboard JSON file that visualizes the core RED metrics for every component in the generated system.

---

## Observability Economics

The architecture includes comprehensive cost management for observability data to prevent runaway costs while maintaining system visibility.

### Cost Management Philosophy

1. **Default Budgets:** Every environment has predefined observability budgets with automatic enforcement
2. **Tiered Sampling:** Different data types have different sampling rates based on operational value
3. **Intelligent Retention:** Retention policies balance compliance requirements with storage costs
4. **Cost Transparency:** Real-time cost monitoring with budget alerts and optimization recommendations

### Sampling Economics

The system implements environment-specific sampling policies to control ingestion costs:

#### Default Sampling Rates by Environment

| Data Type | Development | Staging | Production |
|-----------|-------------|---------|------------|
| Debug Logs | 25% | 5% | 1% |
| Info Logs | 25% | 5% | 1% |
| Error Logs | 100% | 100% | 100% |
| Security Events | 100% | 100% | 100% |
| Audit Logs | 100% | 100% | 100% |
| Performance Metrics | 10% | 5% | 1% |
| Distributed Traces | 10% | 5% | 1% |

#### Budget Enforcement

* **Development:** $20/month total observability budget
* **Staging:** $100/month total observability budget  
* **Production:** $500/month total observability budget

### Retention Economics

The system implements tiered storage with intelligent retention policies:

#### Storage Tiers

1. **Hot Storage:** Immediate access, highest cost ($0.023/GB/month)
2. **Warm Storage:** Quick access, medium cost ($0.0125/GB/month)
3. **Cold Storage:** Slower access, low cost ($0.004/GB/month)
4. **Archive Storage:** Rare access, lowest cost ($0.001/GB/month)

#### Default Retention Policies

| Data Type | Development | Staging | Production |
|-----------|-------------|---------|------------|
| Debug Logs | 12 hours (Hot) | 1 day (Warm) | 7 days (Cold) |
| Info Logs | 1 day (Hot) | 7 days (Warm) | 30 days (Cold) |
| Error Logs | 7 days (Hot) | 30 days (Warm) | 1 year (Warm) |
| Security Events | 30 days (Warm) | 90 days (Cold) | 7 years (Archive) |
| Audit Logs | 30 days (Warm) | 90 days (Cold) | 7 years (Archive) |
| Performance Metrics | 1 day (Hot) | 7 days (Warm) | 90 days (Cold) |
| Distributed Traces | 6 hours (Hot) | 1 day (Warm) | 7 days (Cold) |

### Budget Override Capability

The `deployment.yaml` schema supports environment-specific budget overrides:

```yaml
observability:
  budget_overrides:
    sampling_policy: "custom_high_volume"
    retention_policy: "extended_compliance"
    monthly_budget_limit: 1000.0
    alert_threshold: 0.75
```

### Cost Optimization

The system provides automatic optimization recommendations:

1. **Storage Tier Migration:** Automatically suggest moving data to cheaper storage tiers
2. **Retention Reduction:** Recommend shorter retention for non-compliance data
3. **Sampling Adjustment:** Suggest increased sampling rates for cost-sensitive environments
4. **Budget Reallocation:** Optimize budget allocation across data types

### Implementation Components

* **SamplingPolicyManager:** Manages sampling rates and budget enforcement
* **RetentionBudgetManager:** Handles retention policies and storage cost optimization
* **ObservabilityBudgetMonitor:** Real-time cost tracking and alerting
* **CostOptimizationEngine:** Automatic optimization recommendations

### Budget Enforcement Mechanisms

1. **Soft Limits:** Alerts at 80% of budget utilization
2. **Hard Limits:** Automatic sampling rate reduction when budget exceeded
3. **Emergency Throttling:** Temporary sampling reduction during cost spikes
4. **Compliance Protection:** Security/audit data never subject to cost-based reduction 