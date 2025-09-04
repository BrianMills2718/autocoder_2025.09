# Blueprint Language

## Overview

The Autocoder system is defined by two declarative YAML files: `architecture.yaml` and `deployment.yaml`. This separation of concerns is a core principle: the architecture is a pure, environment-agnostic definition of a system, while the deployment file provides the concrete, environment-specific configuration.

## Schema & Validation

Both blueprint files are formally defined by and validated against a strict JSON Schema. This provides compile-time guarantees of correctness and eliminates schema drift. Ad-hoc linting is forbidden.
*   **Architecture Schema:** [`schemas/architecture.schema.json`](./schemas/architecture.schema.json)
*   **Deployment Schema:** [`schemas/deployment.schema.json`](./schemas/deployment.schema.json)

### Schema Version Requirements

The blueprint parser requires semantic versioning in x.y.z format for schema versions:
- ✅ **Valid**: `"1.0.0"`, `"2.1.3"`, `"1.0.0-beta"`
- ❌ **Invalid**: `"1.0"`, `"1"`, `"v1.0.0"`

The system includes auto-healing that will attempt to convert invalid versions (e.g., `"1.0"` → `"1.0.0"`).

## Auto-Healing Features

The blueprint parser includes auto-healing that can **automatically correct** common blueprint issues. 

### **Why Auto-Healing is Compatible with Radical Explicitness**

**Key Insight**: Users interact with the system exclusively through a **conversational chatbot interface**, not by directly editing YAML blueprints. Therefore:

- **Users never write blueprints directly** - the system generates them from natural language
- **Auto-healing applies to system-generated artifacts**, not user-created content
- **All auto-healing actions are logged and auditable**, maintaining full transparency
- **The chatbot explains what it's building**, so users understand the final system

**This is architectural explicitness** (no hidden configs, implicit behaviors) **not user interface explicitness** (showing every internal step to users).

### **Auto-Healing Maintains Explicitness By:**

- **Logging** all auto-healing actions for audit trails  
- **Preserving** original blueprints with corrections marked as metadata
- **Failing fast** when auto-healing cannot resolve issues
- **Transparency**: Chatbot can explain what was auto-corrected if users ask

Common auto-healing capabilities:

### 1. Schema Version Auto-Healing
Automatically converts non-semantic version strings to valid semantic versions:
```yaml
# Input (invalid)
schema_version: "1.0"

# Auto-healed to
schema_version: "1.0.0"
```

### 2. Missing Bindings Detection
Automatically adds missing bindings between components based on port compatibility:
```yaml
# If components have compatible ports but no explicit binding,
# the system will auto-generate appropriate bindings
components:
  - name: api_endpoint
    type: APIEndpoint
    ports:
      outputs:
        - name: requests
  - name: processor
    type: StreamProcessor
    ports:
      inputs:
        - name: data_in

# Auto-generates binding:
# bindings:
#   - from_component: api_endpoint
#     from_port: requests
#     to_component: processor
#     to_port: data_in
```

### 3. Policy Block Auto-Generation
If required policy blocks are missing, the system automatically adds them with sensible defaults:
```yaml
# Missing policy block auto-generated with:
policy:
  resource_limits:
    cpu: "1000m"
    memory: "512Mi"
  security:
    require_https: false
  observability:
    log_retention_days: 7
```

### 4. Component Configuration Defaults
Components missing required configuration receive appropriate defaults:
```yaml
# Input
components:
  - name: store
    type: Store
    # Missing config

# Auto-healed to
components:
  - name: store
    type: Store
    config:
      storage_type: "memory"
```

---

## `architecture.yaml`: The Architectural Contract

This file is the single source of truth for a system's **design**. It defines the default, structurally-integral configuration of all components.

### Top-Level Structure

```yaml
schema_version: "1.0.0"
system:
  name: user_processing_service
  version: 1.0.1
  description: "Processes user registrations"

components:
  - name: public_user_api
    implementation: APIEndpoint
    ports:
      outputs:
        - name: new_users
          semantic_class: data_out
          data_schema:
            id: schemas.user.NewUserEvent
            version: 2
    config:
      # Defines default schema paths and capability settings.
      # These can be overridden in deployment.yaml for specific environments.
      routes:
        - path: "/users"
          method: "POST"
          output_stream: "new_users"
    capabilities:
      rate_limit:
        # Default rate limit - can be tuned per-environment.
        rate: 100
        period: 1.0
    batching:
      enabled: true
      max_items: 64
      max_ms: 5
      error_mode: per_item

bindings:
  - from_component: public_user_api
    from_port: new_users
    to_component: user_validator
    to_port: input_events

policy:
  resource_limits:
    cpu: "500m"
    memory: "256Mi"
```

### Sections

#### `components`
Defines component instances and their **default configuration**. This acknowledges that some configuration (like a schema path) is tightly coupled to the architecture, while allowing for operational overrides.

#### `bindings`
Defines data flow connections between components. Bindings support both single and multiple target configurations:

**Single Target Binding:**
```yaml
bindings:
  - from_component: public_user_api
    from_port: new_users
    to_component: user_validator
    to_port: input_events
```

**Multiple Target Binding (Array Format):**
```yaml
bindings:
  - from_component: api_gateway
    from_port: requests
    to_components: ["auth_service", "rate_limiter", "logger"]
    to_ports: ["input", "check", "events"]
```

Bindings can include optional metadata for advanced routing:
```yaml
bindings:
  - from_component: data_source
    from_port: output
    to_components: ["processor_1", "processor_2"]
    to_ports: ["input", "input"]
    transformation: "json_to_dict"
    condition: "item.priority == 'high'"
```

---

## `deployment.yaml`: The Operational Contract

This file provides the environment-specific **overrides and operational parameters** required to run the system.

### Top-Level Structure
```yaml
schema_version: "1.0.0"
environment: production

replicas:
  default: 10
  public_user_api: 20

component_overrides:
  - component: public_user_api
    config:
      # Overrides the default schema for a legacy v1 environment.
      output_schema: "schemas.user.NewUserEvent_v1"
    capabilities:
      rate_limit:
        # Increase rate limit for the high-traffic production environment.
        rate: 1000
        period: 1.0

env_vars:
  - name: LOG_LEVEL
    value: "INFO"
  - name: POSTGRES_DSN
    valueFrom:
      secretKeyRef:
        name: postgres-credentials
        key: dsn

policy:
  security:
    require_https: true
    jwt_algorithm: "RS256"
  observability:
    log_retention_days: 30
    metrics_sampling_rate: 0.05
```

### Sections

#### `component_overrides`
Provides environment-specific **overrides** for component configurations defined in `architecture.yaml`. This is the designated mechanism for tuning settings like schema versions, rate limits, or feature flags for a specific environment (e.g., `development`, `production`).

#### `env_vars`
A list of environment variables. It supports direct values or referencing production-safe Kubernetes secrets.

#### `policy`
Defines **operational** policies for the environment, such as security controls and observability budgets. 