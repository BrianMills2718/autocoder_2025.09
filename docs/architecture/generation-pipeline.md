# Generation Pipeline

## Overview

The Autocoder system translates the dual `architecture.yaml` and `deployment.yaml` files into a fully deployed, verifiable software system. The pipeline is designed around the core principles of **quality assurance and functional correctness**, prioritizing working, secure, observable systems over perfect reproducibility.

## MVP Approach: Quality-Focused One-Shot Generation (Post-MVP: Build Context Sealing)

**Current MVP Priority**: Generate high-quality, functionally correct systems in one shot, optimizing for:
- **Functional correctness**: System works as intended
- **Security compliance**: All security requirements met  
- **Observability**: Complete monitoring and logging
- **Robust validation**: Comprehensive testing at every stage

**Post-MVP Enhancement**: Advanced build reproducibility features including:
- Build context sealing via `build.lock` files  
- Deterministic LLM completion freezing
- Cryptographic build provenance
- Bit-wise identical regeneration capabilities

> **Design Philosophy: Quality over Perfect Reproducibility**
> The MVP focuses on reliably generating working, secure, observable systems. Perfect reproducibility is valuable for enterprise workflows but secondary to functional correctness in initial implementation.

---

## Stage 1: Architectural Compilation

### Overview

This stage consumes natural language requirements and compiles them into a versioned, language-agnostic Intermediate Representation (IR) via structured blueprint generation.

### Input
*   Natural language system description
*   Optional context files and examples

### Process: Natural Language → Blueprint YAML

**Phase 1A: Requirements Analysis**
- Parse natural language using structured LLM prompts
- Extract system components, data flows, and quality requirements
- Identify security, scalability, and integration constraints
- Generate initial component topology graph

**Phase 1B: Blueprint Generation**  
- Map requirements to component types and port configurations
- Generate `architecture.yaml` with explicit component definitions
- Create `deployment.yaml` with environment-specific configurations
- Apply blueprint validation and schema conformance checks

**Phase 1C: IR Compilation**
- Parse and validate generated YAML against formal schemas
- Compile into versioned Intermediate Representation
- Perform semantic analysis and dependency resolution  
- Generate compilation metadata for validation traceability

### Validation & Quality Gates
- **Semantic Validation**: Ensure component connectivity makes logical sense
- **Completeness Check**: Verify all requirements are addressed in blueprint
- **Performance Estimation**: Validate against system capacity constraints
- **Security Analysis**: Check for security anti-patterns in component topology

### Output
*   `architecture.yaml` (generated system blueprint)
*   `deployment.yaml` (environment-specific configuration)
*   `generated/ir.v1.json` (versioned Intermediate Representation)
*   Compilation metadata for validation traceability

### Error Handling
- **Requirements Ambiguity**: Request clarification from user with specific questions
- **Impossible Topologies**: Fail fast with explanation of architectural constraints
- **Schema Violations**: Provide detailed fix suggestions with examples

---

## Stage 2: Code Generation

### Overview

The System Generator uses the IR and generates LLM completions to produce the complete source code.

### Input
*   `generated/ir.v1.json`
*   Compilation metadata and configuration

### Process
The generator iterates through the components defined in the IR. For each component, it selects the appropriate code template and generates business logic using **LLM completions tailored to the component requirements**. This stage focuses on producing functionally correct, secure, and observable component implementations.

### Output
*   Complete, generated source code in `generated/src/`.

---

## Stage 3: Validation & Hardening

### Overview
The generated code is subjected to a rigorous, multi-tier validation process. **This stage is strict by default**; any failure at any tier halts the build.

### Input
*   Generated source code from Stage 2.

### Process
1.  **Static Analysis**: The code is scanned for security vulnerabilities, anti-patterns, and compliance with style guides using tools like `bandit` and `ruff`.
2.  **Unit & Integration Testing**: A comprehensive suite of unit and integration tests is executed against the generated code.
3.  **Property-Based Testing**: For critical components, property-based tests are run to verify logical invariants and correctness across a wide range of inputs.
4.  **Architectural Policy Verification**: The system is checked against the constraints defined in the `policy` block of the `architecture.yaml`.
5.  **Performance Safeguards (ADR-021)**: Micro-benchmarks validate that capability performance stays within published budgets, with build failure if latency exceeds thresholds.
6.  **Performance Budget Framework (ADR-030)**: Static budget enforcement with benchmark comparison and runtime monitoring setup.

### Output
*   A set of test reports and validation artifacts. A successful exit code.

---

## Stage 4: Enterprise Deployment Generation

### Overview
The validated system is packaged with complete enterprise deployment artifacts, including Docker configurations, Kubernetes manifests, and operational tooling.

### Input
*   Validated source code from Stage 3.
*   System metadata and configuration
*   `deployment.yaml` (environment-specific configuration)

### Process
1.  **Docker Deployment Generation**:
    - Production-ready `Dockerfile` with multi-stage builds
    - `docker-compose.yml` for development environments  
    - `docker-compose.prod.yml` for production scaling
    - Environment-specific configuration management

2.  **Kubernetes Manifest Generation**:
    - `namespace.yaml` - Isolated environment setup
    - `deployment.yaml` - Application deployment with resource limits
    - `service.yaml` - Service discovery and load balancing
    - `ingress.yaml` - External traffic routing
    - `configmap.yaml` - Application configuration
    - `secrets.yaml` - Sealed secrets for sensitive data

3.  **Observability Integration**:
    - Prometheus metrics endpoints configured
    - Structured logging with OpenTelemetry integration
    - Health check endpoints for liveness/readiness probes
    - Performance monitoring and alerting setup

4.  **Security Configuration**:
    - RBAC manifests with least-privilege access
    - Network policies for traffic isolation
    - Security contexts and pod security standards
    - Input validation and sanitization middleware

5.  **Final Build Signing**: The complete deployment package is signed using `cosign` for integrity verification.

### Output
*   **Deployment Package**: Complete `deployments/` directory with:
    - Docker Compose configurations (development and production)
    - Kubernetes manifests (all required resources)
    - Environment configuration templates
    - Security and RBAC configurations
*   **Container Image**: Versioned, tagged, and signed container
*   **Build Provenance**: System metadata with generation audit trail (Post-MVP: Cryptographic signing) 