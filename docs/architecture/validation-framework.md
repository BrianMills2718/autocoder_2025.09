# Validation Framework Architecture

## Overview

The Autocoder system implements a **Two-Layer Fail-Hard Architecture** that distinguishes between the AutoCoder system itself and the systems it generates:

### **Layer 1: AutoCoder System (Always Fail-Hard)**
The AutoCoder development, generation, and validation pipeline **always fails hard**:
- **Component Generation**: If LLM generation fails, build stops immediately
- **Blueprint Parsing**: Malformed YAML halts the entire process  
- **Validation Failures**: Any validation error stops the build completely
- **Capability Loading**: Missing kernel capabilities cause immediate system failure
- **Import Errors**: Module resolution failures halt the system

**Rationale**: AutoCoder must be deterministic and reliable. No partial systems, no "best effort" generation, no silent failures.

### **Layer 2: Generated Systems (Graceful Degradation with Fail-Hard Boundaries)**
Generated systems can implement **planned graceful degradation**, but when degradation itself fails, they must fail hard:

**Correct Pattern:**
```python
# Generated system - graceful degradation with fail-hard boundary
async def process_payment(self, payment_request):
    try:
        # Primary: Use payment service
        return await self.payment_service.process(payment_request)
    except PaymentServiceUnavailable:
        # Graceful degradation: Queue for later processing
        try:
            await self.payment_queue.enqueue(payment_request)
            return {"status": "queued", "message": "Payment queued for processing"}
        except QueueUnavailable:
            # Fail-hard when graceful degradation fails
            raise SystemError("Both payment service and queue unavailable - cannot proceed")
```

**Anti-Pattern:**
```python
# WRONG - unbounded degradation
async def process_payment(self, payment_request):
    try:
        return await self.payment_service.process(payment_request)
    except PaymentServiceUnavailable:
        try:
            await self.payment_queue.enqueue(payment_request)
        except QueueUnavailable:
            self.logger.warning("Payment failed, ignoring")  # WRONG - silent failure
            return {"status": "ignored"}  # WRONG - lies about system state
```

### **Capability Kernel: Fail-Hard at Both Layers**
The mandatory capability kernel (SchemaValidator, RateLimiter, MetricsCollector) is **fail-hard at both layers**:
- **AutoCoder Layer**: Cannot generate components without kernel capabilities
- **Generated System Layer**: Cannot operate without kernel capabilities - no graceful degradation allowed

**Rationale**: Kernel capabilities are fundamental to system integrity and cannot be gracefully degraded.

This document outlines the architecture of the **build-time validation framework** and the **graded failure policy** that distinguishes between validation failures and runtime failures.

## Legacy ↔️ Port Model Mapping ([ADR-031](adr/accepted/031-component-semantics.md))

| Old Term (pre-[ADR-031](adr/accepted/031-component-semantics.md)) | New Concept |
|------------------------|-------------|
| Source / Sink / Transformer Types | Roles derived from port topology |
| Type Validation Failures | Port Semantics Validation Failures |
| input/output streams | named ports with semantic_class + data_schema |

### Example Binding (port model)
```yaml
bindings:
  - from_component: public_user_api
    from_port: response
    to_component: user_validator
    to_port: request
```

## Guiding Principles

1.  **Fail-Hard at Build-Time:** Validation is not optional. Any failure to conform to the system's defined schemas, policies, or tests is a build-stopping event.
2.  **Verifiable Correctness by Default:** The system's correctness is not assumed. It is verified through a hierarchy of tests and static analysis. While formal proofs (e.g., TLA+) are a long-term goal, the current standard is rigorous, automated verification.
3.  **Layered Defense:** Validation occurs at multiple, distinct tiers, moving from simple syntax checks to complex semantic analysis.
4.  **Validation-Healing Coupling:** Every validation check MUST have a corresponding self-healing mechanism via LLM. No validation without remediation capability.
5.  **Explicit Configuration:** All required configuration must be explicitly provided. No smart defaults or guessing - missing configuration triggers LLM-guided generation.
6.  **Build-Time Completeness:** All issues that CAN be detected at build time MUST be detected at build time. Runtime surprises are validation failures.

---

## The Validation Hierarchy (Build-Time)

The framework is structured as a hierarchy of validation tiers, each with a specific responsibility. **Every validation check is coupled with a self-healing mechanism** that attempts to fix issues through LLM-guided remediation via the Semantic Healer (`autocoder_cc/healing/semantic_healer.py`).

### Tier 0: Configuration Completeness Validation (NEW)

*   **Responsibility:** To ensure all components have complete configuration before code generation begins.
*   **Checks Include:**
    *   **Required Configuration Detection:** Each component type declares required configuration via `get_required_config_fields()`.
    *   **Configuration Presence:** Validates all required configuration is present in the blueprint.
    *   **Configuration Validity:** Ensures configuration values meet type and constraint requirements.
    *   **Runtime Requirements:** Verifies runtime dependencies (e.g., "if output is file://, directory must exist").
*   **Self-Healing:**
    *   **LLM Configuration Generation:** When required config is missing, the semantic healer queries the LLM to provide appropriate values based on system context.
    *   **Requirement Inference:** LLM analyzes component relationships to infer missing configuration requirements.
    *   **No Defaults:** System explicitly rejects smart defaults in favor of LLM-provided explicit configuration.

### Tier 1: Blueprint Validation

*   **Responsibility:** To ensure the `architecture.yaml` and `deployment.yaml` files are well-formed, syntactically correct, and conform to their respective schemas.
*   **Checks Include:**
    *   YAML syntax correctness.
    *   Presence of all required sections and fields.
    *   Correct data types for all values.
    *   Component configuration completeness (calls Tier 0).
*   **Self-Healing:**
    *   **Schema Version Correction:** Automatically converts invalid version strings to semantic versions.
    *   **Missing Section Generation:** LLM generates required but missing blueprint sections.
    *   **Type Coercion:** Attempts to convert mistyped values to correct types via LLM reasoning.

### Tier 2: Architectural & Logical Validation

*   **Responsibility:** To enforce the fundamental rules of the Autocoder architecture. The `ComponentRegistry` is the primary agent for this tier.
*   **Checks Include:**
    *   **Implementation Existence:** Verifies that all `implementation` values correspond to known, registered components.
    *   **Port Compatibility:** Enforces that `bindings` connect compatible port types (e.g., `data_out` to `data_in`).
    *   **Binding Integrity:** Ensures that all `bindings` connect valid port names on existing components.
    *   **Configuration Contract Validation:** Validates component configurations against their declared contracts.
*   **Self-Healing:**
    *   **Port Generation:** Automatically generates missing ports based on binding requirements.
    *   **Binding Inference:** LLM infers and creates missing bindings based on component capabilities.
    *   **Schema Alignment:** Adjusts port schemas for compatibility when safe to do so.

### Tier 3: Pre-Runtime Simulation (CRITICAL)

*   **Responsibility:** To simulate component initialization and data flow without side effects before actual runtime. This tier catches configuration and dependency issues before code is even generated.
*   **Checks Include:**
    *   **Dry-Run Initialization:** Simulates component `__init__` and `setup()` methods without resource allocation.
    *   **Mock Data Flow:** Tests if synthetic data can flow through the pipeline based on port schemas.
    *   **Resource Availability:** Verifies required resources (files, databases, APIs) are accessible.
    *   **Configuration Usage:** Ensures all provided configuration is actually used by components.
    *   **Dependency Chain Validation:** Verifies each component receives required inputs from upstream components.
    *   **Runtime Prerequisites Check:** Validates all runtime prerequisites declared in component contracts.
*   **Self-Healing:**
    *   **Resource Creation:** Creates missing directories or files when safe.
    *   **Configuration Adjustment:** LLM adjusts configuration to match available resources.
    *   **Alternative Resource Suggestion:** When resources unavailable, LLM suggests alternatives.
    *   **Missing Dependency Resolution:** LLM adds required upstream components when missing.

### Tier 4: Static Code & Security Analysis

*   **Responsibility:** To analyze the generated source code for quality, correctness, and security vulnerabilities without executing it.
*   **Checks Include:**
    *   **Security Scanning:** Uses tools like `bandit` to detect common security issues.
    *   **Code Quality & Style:** Uses tools like `ruff` to enforce code quality and a consistent style.
    *   **Placeholder Detection:** Scans for `TODO`, `FIXME`, or `pass` statements in generated business logic.
    *   **Secret Scanning:** Scans for hard-coded secrets.
    *   **Import Validation:** Ensures all imports resolve correctly.
*   **Self-Healing:**
    *   **AST-Based Code Repair:** Automatically fixes syntax errors, missing imports, and structural issues.
    *   **Placeholder Replacement:** LLM generates actual implementation for placeholder code.
    *   **Security Issue Remediation:** LLM rewrites code to address security vulnerabilities.

### Tier 5: Semantic & Behavioral Validation (ENHANCED) 

*   **Responsibility:** To validate that components behave according to their intended purpose and user expectations using the semantic healer.
*   **Checks Include:**
    *   **Synthetic Input Generation:** Semantic healer's LLM generates domain-appropriate test inputs for each component.
    *   **Output Reasonableness:** Semantic healer's LLM examines component outputs to verify they match expected behavior.
    *   **Business Logic Validation:** Verifies transformations and processing logic are semantically correct.
    *   **Cross-Component Consistency:** Ensures data transformations maintain semantic meaning across pipeline.
*   **Self-Healing (via Semantic Healer):**
    *   **Logic Correction:** Semantic healer's LLM rewrites incorrect business logic based on intended behavior.
    *   **Transformation Enhancement:** Semantic healer improves data transformations to be more domain-appropriate.
    *   **Validation Injection:** Semantic healer adds output validation code where missing.
    *   **Reasonableness Checking:** Semantic healer ensures outputs make business sense given inputs.

### Tier 6: Compositional Validation (NEW)

*   **Responsibility:** To validate emergent behaviors and system-level properties when components are composed together.
*   **Checks Include:**
    *   **Emergent Behavior Detection:** Identifies unexpected behaviors from component combinations.
    *   **Interaction Invariants:** Validates properties that must hold across component boundaries.
    *   **Cascading Failure Analysis:** Simulates component failures and traces impact through system.
    *   **Data Flow Consistency:** Ensures data maintains integrity through entire pipeline.
    *   **System-Level Performance:** Validates aggregate performance meets requirements.
*   **Self-Healing:**
    *   **Component Reordering:** LLM adjusts component pipeline order for better behavior.
    *   **Buffer Injection:** Adds buffering components to handle timing issues.
    *   **Isolation Barriers:** Inserts error boundaries between components.
    *   **Coordination Logic:** Adds synchronization when needed.
*   **Value/Difficulty Rating:** ⭐⭐⭐⭐⭐ Value / 🔧🔧🔧🔧 Difficulty
    *   High value: Catches integration issues that component-level testing misses
    *   High difficulty: Requires modeling component interactions and emergent behaviors

### Tier 7: Temporal & Stateful Validation (NEW)

*   **Responsibility:** To validate system behavior over time and across state transitions.
*   **Checks Include:**
    *   **Temporal Properties:** Validates "eventually consistent", "always responds within X", "never deadlocks".
    *   **State Machine Validation:** Ensures valid state transitions and no illegal states.
    *   **Memory Leak Detection:** Monitors resource usage over extended runtime.
    *   **Long-Running Stability:** Tests system behavior over hours/days of operation.
    *   **State Recovery:** Validates system can recover state after restart.
*   **Self-Healing:**
    *   **State Machine Repair:** LLM fixes invalid state transitions.
    *   **Resource Cleanup Addition:** Adds proper cleanup code for resources.
    *   **Timeout Configuration:** Sets appropriate timeouts to prevent hangs.
    *   **State Persistence:** Adds checkpointing for state recovery.
*   **Value/Difficulty Rating:** ⭐⭐⭐⭐ Value / 🔧🔧🔧🔧🔧 Difficulty
    *   High value: Catches entire class of time-based and state-related bugs
    *   Very high difficulty: Requires temporal logic and state space exploration

### Tier 8: Degradation Path Validation (NEW)

*   **Responsibility:** To validate system behavior under failure conditions and recovery mechanisms.
*   **Checks Include:**
    *   **Graceful Degradation Testing:** Verifies fallback paths work correctly.
    *   **Circuit Breaker Validation:** Ensures protection mechanisms engage at right thresholds.
    *   **Recovery Path Testing:** System recovers correctly after component restoration.
    *   **Cascading Failure Prevention:** No single failure brings down entire system.
    *   **Partial Availability Testing:** System remains partially functional during failures.
*   **Self-Healing:**
    *   **Fallback Implementation:** LLM adds missing degradation paths.
    *   **Circuit Breaker Tuning:** Adjusts thresholds based on system behavior.
    *   **Recovery Logic Addition:** Implements proper recovery sequences.
    *   **Bulkhead Isolation:** Adds isolation between components to prevent cascade.
*   **Value/Difficulty Rating:** ⭐⭐⭐⭐⭐ Value / 🔧🔧🔧 Difficulty
    *   Very high value: Critical for production resilience
    *   Medium difficulty: Well-understood resilience patterns

### Tier 9: Adversarial Validation (NEW)

*   **Responsibility:** To validate system security and robustness against hostile inputs.
*   **Checks Include:**
    *   **Intelligent Fuzzing:** LLM generates adversarial inputs to find weaknesses.
    *   **Resource Exhaustion Testing:** Deliberately attempts to exhaust system resources.
    *   **Security Attack Simulation:** Tests against OWASP top 10 and common attacks.
    *   **Byzantine Failure Testing:** Components sending malformed/malicious data.
    *   **Input Validation Testing:** Ensures all inputs properly sanitized and validated.
*   **Self-Healing:**
    *   **Input Sanitization:** LLM adds proper input validation and sanitization.
    *   **Rate Limiting:** Adds rate limiters to prevent resource exhaustion.
    *   **Security Headers:** Adds security headers and configurations.
    *   **Error Message Sanitization:** Prevents information leakage in errors.
*   **Value/Difficulty Rating:** ⭐⭐⭐⭐ Value / 🔧🔧🔧🔧 Difficulty
    *   High value: Critical for security and robustness
    *   High difficulty: Requires security expertise and adversarial thinking

### Tier 10: Multi-Environment Validation (NEW)

*   **Responsibility:** To ensure system works correctly across different deployment environments.
*   **Checks Include:**
    *   **Development vs Production:** Different configurations for different environments.
    *   **Platform Compatibility:** Works on Linux, Mac, Windows, Docker, K8s.
    *   **Scaling Validation:** Works at different scales (1 user vs 10000 users).
    *   **Dependency Version Testing:** Works with different versions of dependencies.
    *   **Network Condition Testing:** Works under various network conditions.
*   **Self-Healing:**
    *   **Environment Detection:** Adds code to detect and adapt to environment.
    *   **Compatibility Shims:** LLM adds compatibility layers for different platforms.
    *   **Configuration Templates:** Creates environment-specific configurations.
    *   **Dependency Resolution:** Finds compatible dependency versions.
*   **Value/Difficulty Rating:** ⭐⭐⭐ Value / 🔧🔧 Difficulty
    *   Medium value: Important for real-world deployment
    *   Low difficulty: Mostly configuration and testing

### Tier 11: Dynamic & Property-Based Testing

*   **Responsibility:** To validate the runtime behavior of the generated system **within the build pipeline**.
*   **Checks Include:**
    *   **Unit & Integration Testing:** Executes a comprehensive suite of generated unit and integration tests.
    *   **Property-Based Testing:** Executes property-based tests for critical components to verify logical invariants and correctness across a wide range of inputs.
    *   **Architectural Policy Verification:** Verifies the system against the machine-verifiable proofs defined in the `policy` block of the `architecture.yaml`.
    *   **Component Interaction Testing:** Tests actual data flow between components with realistic payloads.
*   **Self-Healing:**
    *   **Test Generation:** LLM generates missing test cases based on component contracts.
    *   **Assertion Correction:** Fixes incorrect test assertions based on actual behavior.
    *   **Mock Generation:** Creates appropriate test doubles when external dependencies unavailable.
*   **Value/Difficulty Rating:** ⭐⭐⭐ Value / 🔧🔧 Difficulty
    *   Medium value: Standard testing practice but essential
    *   Low difficulty: Well-understood testing patterns

### Tier 5: Performance Safeguards (ADR-021)

*   **Responsibility:** To enforce performance budgets and prevent regressions that could impact system reliability.
*   **Checks Include:**
    *   **Build-Time Micro-Benchmarks:** Automated performance tests that gate PRs if capability latency exceeds published budgets.
    *   **Runtime Self-Profiling:** Continuous monitoring of capability performance with automatic alerts at 80% of budget and circuit breaks at 120%.
    *   **Memory Usage Validation:** Ensures components stay within allocated memory budgets.

### Tier 6: Performance Budget Framework (ADR-030)

*   **Responsibility:** To enforce static performance budgets with build-time validation and runtime alerting.
*   **Checks Include:**
    *   **Static Budget Enforcement:** Fails PR if any capability exceeds latency or memory budget by >10%.
    *   **Benchmark Comparison:** Compares against main branch benchmarks using pytest-benchmark.
    *   **Runtime Budget Monitoring:** Prometheus alerts at 80% and 120% of published budgets.

---

## Context-Aware Healing (NEW)

The Semantic Healer operates with full system context, not in isolation:

### Contextual Information Provided to Healer

1. **Pipeline Context:** Full upstream and downstream component information
2. **Historical Context:** Previous similar systems and their successful configurations
3. **Dependency Context:** How changes affect other components
4. **Performance Context:** Current system performance characteristics
5. **Environment Context:** Deployment environment and constraints

### Context-Aware Healing Process

```python
def heal_with_context(component_issue: Issue, 
                      pipeline_context: PipelineContext,
                      historical_context: HistoricalContext) -> HealingResult:
    """Heal component issues with full system awareness"""
    
    # Consider downstream expectations
    downstream_requirements = pipeline_context.get_downstream_requirements()
    
    # Learn from similar systems
    similar_solutions = historical_context.find_similar_solutions()
    
    # Apply healing that considers whole system
    return semantic_healer.heal(
        issue=component_issue,
        constraints=downstream_requirements,
        known_good_patterns=similar_solutions
    )
```

### Benefits
- **Smarter Fixes:** Considers impact on entire system
- **Pattern Reuse:** Leverages successful previous solutions
- **Consistency:** Maintains system-wide invariants

**Value/Difficulty Rating:** ⭐⭐⭐⭐⭐ Value / 🔧🔧🔧 Difficulty
- Very high value: Dramatically improves fix quality
- Medium difficulty: Requires context gathering and management

---

## Validation Provenance & Audit Trail (NEW)

Complete tracking of all validation decisions and healing actions:

### Provenance Information Captured

1. **Decision History:** Why LLM chose specific configurations
2. **Healing Actions Log:** What was changed, when, and why
3. **Validation Rule Triggers:** Which rules fired and their results
4. **Configuration Lineage:** How configuration evolved through stages
5. **Performance Metrics:** Time taken for each validation/healing cycle

### Audit Trail Structure

```yaml
validation_audit:
  timestamp: "2024-01-15T10:30:00Z"
  stage: "Configuration Validation"
  component: "DataSink"
  
  validation_trigger:
    rule: "required_config_check"
    result: "FAILED"
    reason: "Missing required field: output_destination"
  
  healing_action:
    healer: "SemanticHealer"
    llm_model: "gpt-4"
    prompt_tokens: 1250
    completion_tokens: 340
    
    decision_reasoning: |
      Component type DataSink requires output destination.
      Based on system context (data pipeline for logs),
      choosing file output to /var/log/processed/
    
    changes_made:
      - field: "output_destination"
        old_value: null
        new_value: "file:///var/log/processed/"
        justification: "Standard log processing location"
  
  validation_retry:
    result: "PASSED"
    duration_ms: 2340
```

### Benefits
- **Debugging:** Complete history of what happened and why
- **Trust:** Users can understand LLM decisions
- **Learning:** Identify patterns in failures and fixes
- **Compliance:** Full audit trail for regulated environments

**Value/Difficulty Rating:** ⭐⭐⭐⭐⭐ Value / 🔧🔧 Difficulty
- Very high value: Essential for debugging and trust
- Low difficulty: Mostly logging and structured data

---

## Cross-System Pattern Learning (NEW)

Leverage knowledge from previously generated systems:

### Pattern Categories

1. **Configuration Templates:** Common configurations that work well
2. **Component Combinations:** Known good component pairings
3. **Anti-Patterns:** Combinations known to cause issues
4. **Performance Profiles:** Expected performance for similar systems
5. **Scaling Patterns:** How similar systems scale

### Pattern Learning Process

```python
class PatternLearner:
    def extract_patterns(self, successful_systems: List[System]) -> PatternLibrary:
        """Extract reusable patterns from successful systems"""
        return {
            "config_templates": self.extract_config_patterns(),
            "component_graphs": self.extract_component_patterns(),
            "anti_patterns": self.identify_failure_patterns(),
            "performance_baselines": self.extract_performance_patterns()
        }
    
    def apply_patterns(self, new_system: System) -> System:
        """Apply learned patterns to new system generation"""
        similar_systems = self.find_similar_systems(new_system)
        patterns = self.get_applicable_patterns(similar_systems)
        return self.enhance_with_patterns(new_system, patterns)
```

### Benefits
- **Faster Generation:** Reuse successful configurations
- **Higher Quality:** Avoid known problems
- **Consistency:** Similar systems behave similarly

**Value/Difficulty Rating:** ⭐⭐⭐⭐ Value / 🔧🔧🔧🔧 Difficulty
- High value: Improves quality and speed over time
- High difficulty: Requires pattern extraction and matching

---

## Incremental Re-validation (NEW)

Smart validation that only re-validates what changed:

### Dependency Graph Based Validation

1. **Change Detection:** Identify what components/configs changed
2. **Impact Analysis:** Determine affected downstream components
3. **Selective Re-validation:** Only validate affected parts
4. **Cache Management:** Reuse validation results for unchanged parts

### Implementation

```python
class IncrementalValidator:
    def __init__(self):
        self.validation_cache = {}
        self.dependency_graph = {}
    
    def validate_incremental(self, system: System, changes: List[Change]) -> ValidationResult:
        """Only validate parts affected by changes"""
        
        # Identify affected components
        affected = self.trace_dependencies(changes)
        
        # Reuse cached results for unaffected parts
        results = {}
        for component in system.components:
            if component.id in affected:
                results[component.id] = self.validate_component(component)
                self.validation_cache[component.id] = results[component.id]
            else:
                results[component.id] = self.validation_cache.get(component.id)
        
        return self.aggregate_results(results)
```

### Benefits
- **Faster Validation:** Don't re-validate everything
- **Resource Efficient:** Less LLM calls for unchanged parts
- **Interactive Development:** Quick feedback on changes

**Value/Difficulty Rating:** ⭐⭐⭐ Value / 🔧🔧🔧 Difficulty
- Medium value: Improves development speed
- Medium difficulty: Requires dependency tracking

---

## Constraint Solver Integration (NEW)

Use formal constraint solvers for configuration problems:

### Constraint Types

1. **Configuration Constraints:** Valid ranges, dependencies
2. **Resource Constraints:** Memory, CPU, network limits
3. **Compatibility Constraints:** Version compatibility requirements
4. **Business Constraints:** Cost, compliance requirements

### Solver Integration

```python
class ConstraintSolver:
    def solve_configuration(self, 
                           requirements: List[Requirement],
                           constraints: List[Constraint]) -> Configuration:
        """Use SMT solver to find valid configuration"""
        
        # Convert to SMT formula
        formula = self.requirements_to_smt(requirements)
        formula.add(self.constraints_to_smt(constraints))
        
        # Solve
        solver = Z3Solver()
        if solver.check(formula) == sat:
            return self.extract_configuration(solver.model())
        else:
            # Relax constraints and retry
            return self.solve_with_relaxation(requirements, constraints)
    
    def optimize_configuration(self, 
                              constraints: List[Constraint],
                              objective: Objective) -> Configuration:
        """Find optimal configuration within constraints"""
        optimizer = Z3Optimizer()
        optimizer.add(constraints)
        optimizer.maximize(objective)
        return optimizer.check()
```

### Benefits
- **Guaranteed Solutions:** Find configs that satisfy all constraints
- **Optimization:** Find best config, not just valid one
- **Conflict Resolution:** Identify and resolve conflicting requirements

**Value/Difficulty Rating:** ⭐⭐⭐⭐ Value / 🔧🔧🔧🔧🔧 Difficulty
- High value: Solves complex configuration problems
- Very high difficulty: Requires formal methods expertise

---

## Component Capability Contracts (ENHANCED)

Every component type MUST declare its full capabilities, requirements, and contracts through formal specifications. This enables comprehensive validation at all stages of generation.

### Full Contract Declaration

Components declare their complete contracts via multiple methods:

```python
class DataSink(ComposedComponent):
    @classmethod
    def get_component_contract(cls) -> ComponentContract:
        """Full component contract including capabilities, requirements, and guarantees"""
        return ComponentContract(
            capabilities=["data_writing", "format_conversion", "buffering"],
            semantic_type="data_output",
            requires={
                "input": DataSchema(
                    semantic_type="processable_data",
                    structure="Dict[str, Any]"
                ),
                "config": {
                    "output_destination": ConfigRequirement(
                        type="string",
                        semantic_type="uri",
                        description="Where to write data (stdout, file://path, s3://bucket)",
                        validator=lambda x: x.startswith(("stdout", "file://", "s3://", "http://")),
                        examples=["stdout", "file:///tmp/output.json", "s3://my-bucket/data/"]
                    ),
                    "format": ConfigRequirement(
                        type="string",
                        semantic_type="data_format",
                        required=False,
                        options=["json", "csv", "parquet", "avro"]
                    )
                }
            },
            provides={
                "output": DataSchema(
                    semantic_type="write_confirmation",
                    structure={"bytes_written": "int", "location": "string", "timestamp": "datetime"}
                ),
                "metrics": MetricsSchema(
                    counters=["records_written", "bytes_written", "errors"],
                    gauges=["buffer_size", "write_latency_ms"]
                )
            },
            runtime_prerequisites=[
                "If output_destination is file://, directory must exist and be writable",
                "If output_destination is s3://, AWS credentials must be configured",
                "If format is parquet, pyarrow library must be installed"
            ],
            invariants=[
                "All data received on input port must be written or explicitly rejected",
                "Write confirmations must include actual bytes written",
                "Errors must be logged with full context"
            ],
            performance_expectations={
                "latency_p99_ms": 100,
                "throughput_records_per_sec": 10000,
                "memory_usage_mb": 512
            }
        )
    
    @classmethod
    def get_required_config_fields(cls) -> List[ConfigRequirement]:
        """Legacy method - delegates to contract"""
        return cls.get_component_contract().requires["config"]
    
    @classmethod
    def get_runtime_requirements(cls) -> List[RuntimeRequirement]:
        """Legacy method - delegates to contract"""
        return cls.get_component_contract().runtime_prerequisites
```

### Configuration Validation Flow

1. **Detection Phase**: Component registry collects all required configuration from component types
2. **Validation Phase**: Blueprint validator checks all required fields are present
3. **Healing Phase**: If missing, semantic healer queries LLM with:
   - Component type and purpose
   - Available system context
   - Configuration requirements and examples
   - Related component configurations
4. **Verification Phase**: Validates LLM-provided configuration meets requirements
5. **Runtime Check**: Pre-runtime simulation verifies runtime requirements are met

### Configuration Requirement Types

*   **Required Fields**: Must be present, no defaults allowed
*   **Optional Fields**: May be omitted, but if needed, LLM must provide
*   **Constrained Fields**: Must meet validation criteria
*   **Dependent Fields**: Required based on other field values
*   **Runtime Dependencies**: External resources that must exist

---

## Multi-Stage Generation Validation (NEW)

Instead of validating only at the end, the system validates and heals at each stage of generation:

### Stage-by-Stage Validation

#### Stage 1: Requirements Validation
*   **Check:** Is the natural language requirement complete and unambiguous?
*   **Self-Healing:** LLM clarifies ambiguities and fills missing details
*   **Output:** Complete, validated requirements specification

#### Stage 2: Blueprint Validation
*   **Check:** Does the blueprint fully implement the requirements?
*   **Self-Healing:** LLM adds missing components or configurations
*   **Output:** Complete, validated blueprint

#### Stage 3: Configuration Validation
*   **Check:** Do all components have required configuration?
*   **Self-Healing:** LLM provides missing configuration values
*   **Output:** Fully configured component specifications

#### Stage 4: Code Generation Validation
*   **Check:** Is generated code complete and correct?
*   **Self-Healing:** Semantic healer fixes logic and implementation issues
*   **Output:** Working, validated code

#### Stage 5: Behavioral Validation
*   **Check:** Does the system behavior match requirements?
*   **Self-Healing:** LLM adjusts logic to match intended behavior
*   **Output:** System that meets original requirements

### Benefits
- **Early Detection:** Problems caught at the stage where they occur
- **Targeted Healing:** Each stage has specialized self-healing
- **No Cascade Failures:** Issues fixed before propagating to next stage
- **Complete Validation:** Every transformation is validated

---

## Semantic Type System (NEW)

Beyond structural validation, components use semantic types to ensure business logic correctness:

### Semantic Type Declaration

```yaml
# In blueprint or component contract
transaction_amount:
  type: float
  semantic_type: currency_usd
  constraints:
    min: 0.01
    max: 1000000.00
    precision: 2
  business_meaning: "Transaction amount in USD"
  validation_rules:
    - "Must be positive"
    - "Must not exceed customer's daily limit"
    - "Must be less than account balance"
```

### Semantic Validation

The semantic healer validates that:
- Data transformations preserve semantic meaning
- Type conversions are semantically valid (e.g., can't convert distance to currency)
- Business rules are enforced across the pipeline
- Output semantics match input semantics plus intended transformation

---

## Test Oracle Generation (NEW)

The LLM generates comprehensive test oracles, not just test inputs:

### Oracle Components

1. **Input-Output Pairs:** For each test input, the expected output
2. **Invariants:** Properties that must always hold
3. **Performance Expectations:** Expected latency, throughput, resource usage
4. **Edge Case Behaviors:** How system should handle boundary conditions
5. **Error Scenarios:** Expected behavior for invalid inputs

### Oracle Generation Process

```python
def generate_test_oracle(component_contract: ComponentContract, 
                         requirements: str) -> TestOracle:
    """LLM generates complete test oracle from contract and requirements"""
    return TestOracle(
        test_cases=[
            TestCase(
                input={"amount": 100.50, "currency": "USD"},
                expected_output={"converted": 85.43, "currency": "EUR"},
                invariants=["output.converted > 0", "output.currency == 'EUR'"],
                max_latency_ms=50
            )
        ],
        global_invariants=[
            "No data loss in pipeline",
            "All errors logged with context",
            "Memory usage < 1GB"
        ],
        performance_expectations={
            "p50_latency_ms": 10,
            "p99_latency_ms": 100,
            "throughput_rps": 1000
        }
    )
```

---

## Bidirectional Validation (NEW)

Validation forms a complete circle from requirements back to requirements:

### Validation Flow

1. **Requirements → Blueprint:** Does blueprint implement all requirements?
2. **Blueprint → Code:** Does code correctly implement blueprint?
3. **Code → Behavior:** Does code produce expected behavior?
4. **Behavior → Requirements:** Does behavior satisfy original requirements?

### Implementation

Each transition is validated by the semantic healer:
- **Forward Validation:** Each stage output matches its specification
- **Backward Validation:** Final behavior traces back to requirements
- **Circular Validation:** System behavior matches user intent

### Benefits
- **Complete Correctness:** Every transformation validated both ways
- **Intent Preservation:** Original requirements always satisfied
- **No Specification Drift:** Implementation stays true to requirements

---

## Testing and Mocking Policy

The validation framework's philosophy extends to testing.

*   **Mock Usage:** The use of traditional mocking libraries (`pytest-mock`) is strongly discouraged in favor of tests that use real component interactions against test doubles or in-memory backends. The build will fail if mock usage is detected unless explicitly approved via a documented risk acceptance.
*   **Synthetic Data Generation:** LLM generates realistic test data for each component based on its declared purpose and configuration.
*   **Behavioral Testing:** Every component's output is validated by LLM for reasonableness and correctness relative to its intended behavior.

---

## Graded Failure Policy

The system implements a **graded failure policy** that distinguishes between different types of failures and applies appropriate handling strategies. This policy ensures that validation failures always fail hard (immediate system termination) while runtime failures fail soft (graceful degradation with resilience patterns).

### Failure Classification

#### Validation Failures (Fail-Hard)
These failures indicate fundamental issues with system correctness and **always result in immediate system termination**:

*   **Schema Validation Failures**: Data does not conform to expected schemas
*   **Port Semantics Validation Failures**: Port compatibility or schema mismatches in component interactions
*   **Constraint Validation Failures**: Business rule violations or constraint violations
*   **Security Validation Failures**: Security policy violations or unauthorized access attempts
*   **Configuration Validation Failures**: Invalid configuration values or missing required settings
*   **Blueprint Validation Failures**: Malformed or invalid architecture/deployment blueprints
*   **Component Validation Failures**: Component implementation or integration issues
*   **Integration Validation Failures**: Component compatibility or binding issues

#### Runtime Failures (Fail-Soft)
These failures indicate operational issues that can be handled gracefully with **resilience patterns**:

*   **Connection Failures**: Network timeouts, database connection issues
*   **Service Unavailability**: Downstream service outages or capacity issues
*   **Resource Exhaustion**: Memory pressure, disk space issues (within limits)
*   **Transient Errors**: Temporary operational issues that may resolve automatically

#### Infrastructure Failures (Retry with Circuit Breaker)
These failures may be transient and are handled with **retry mechanisms**:

*   **Network Timeouts**: Connection timeouts that may be temporary
*   **Database Lock Conflicts**: Temporary database contention
*   **Rate Limit Exceeded**: API rate limiting that may reset
*   **Resource Temporarily Unavailable**: Temporary resource constraints

### Failure Handling Strategies

#### Fail-Hard Implementation
For validation failures:
1. **Immediate Termination**: System exits with non-zero code (exit code 2 for validation failures)
2. **Detailed Logging**: Complete failure context logged at CRITICAL level
3. **Failure Report Generation**: Comprehensive failure report saved to disk
4. **No Recovery**: No attempt to continue operation
5. **Alert Generation**: Critical alerts sent to monitoring systems

#### Fail-Soft Implementation
For runtime failures:
1. **Graceful Degradation**: System continues with reduced functionality
2. **Circuit Breaker Protection**: Prevents cascading failures
3. **Fallback Mechanisms**: Alternative execution paths when available
4. **Monitoring & Alerting**: Warnings logged and alerts sent
5. **Automatic Recovery**: Attempts to recover when conditions improve

#### Retry with Resilience Patterns
For infrastructure failures:
1. **Exponential Backoff**: Increasing delays between retry attempts
2. **Jitter**: Random delay variation to prevent thundering herd
3. **Maximum Retry Limits**: Fail-soft after exhausting retry attempts
4. **Circuit Breaker Integration**: Open circuit after repeated failures
5. **Bulkhead Isolation**: Separate resource pools to prevent total failure

### Resilience Patterns

#### Circuit Breaker Pattern
*   **States**: Closed (normal), Open (failing), Half-Open (testing recovery)
*   **Failure Threshold**: Number of consecutive failures before opening
*   **Recovery Timeout**: Time to wait before testing recovery
*   **Monitoring**: Circuit state changes logged and monitored

#### Retry Pattern
*   **Exponential Backoff**: Delay = initial_delay * (multiplier ^ attempt)
*   **Jitter**: Random variation to prevent synchronized retries
*   **Maximum Attempts**: Hard limit on retry attempts
*   **Retryable Exceptions**: Only specific exception types trigger retries

#### Timeout Pattern
*   **Operation Timeouts**: Maximum time allowed for operations
*   **Cascading Timeouts**: Shorter timeouts for nested operations
*   **Timeout Monitoring**: Timeout events logged and monitored

#### Bulkhead Pattern
*   **Resource Isolation**: Separate resource pools for different operations
*   **Concurrent Limits**: Maximum concurrent operations per resource pool
*   **Queue Management**: Bounded queues with overflow handling

### Policy Configuration

The graded failure policy is configurable through failure policies that define:
*   **Failure Classification**: Which exceptions map to which failure types
*   **Handling Strategy**: Fail-hard, fail-soft, or retry behavior
*   **Retry Configuration**: Maximum attempts, backoff parameters, timeouts
*   **Circuit Breaker Settings**: Thresholds, recovery timeouts, monitoring
*   **Monitoring Requirements**: Metrics, alerting, and logging levels

### Implementation Components

#### GradedFailureHandler
*   **Purpose**: Orchestrates failure handling based on failure type
*   **Location**: `autocoder_cc/validation/graded_failure_handler.py`
*   **Responsibilities**: Failure classification, policy application, termination

#### ValidationFailureHandler
*   **Purpose**: Implements fail-hard behavior for validation failures
*   **Location**: `autocoder_cc/validation/validation_failure_handler.py`
*   **Responsibilities**: Immediate termination, failure reporting, alerting

#### ResiliencePatterns
*   **Purpose**: Implements fail-soft resilience patterns for runtime failures
*   **Location**: `autocoder_cc/validation/resilience_patterns.py`
*   **Responsibilities**: Circuit breakers, retries, timeouts, bulkheads

### Monitoring and Observability

#### Failure Metrics
*   **Failure Counts**: By type, component, and severity
*   **Failure Rates**: Failures per unit time
*   **Circuit Breaker States**: Open/closed/half-open statistics
*   **Retry Attempts**: Success/failure rates for retry operations

#### Alerting
*   **Critical Alerts**: All validation failures (fail-hard)
*   **Warning Alerts**: Runtime failures and degraded operation
*   **Information Alerts**: Circuit breaker state changes, retry exhaustion

#### Logging
*   **Structured Logging**: All failures logged with complete context
*   **Failure Reports**: Detailed reports saved for validation failures
*   **Trace Correlation**: Failure events correlated with request traces

### Long-Term Vision: Formal Methods Integration

While the current implementation uses heuristic-based failure detection and handling, the long-term vision includes formal methods integration:

#### Formal Verification Goals
*   **TLA+ Specifications**: Critical system invariants specified in TLA+
*   **Property-Based Testing**: Automated property verification
*   **Theorem Proving**: Mathematical proofs of correctness properties
*   **Model Checking**: Exhaustive state space exploration

#### Migration Path
1. **Current State**: Comprehensive heuristic validation and resilience patterns
2. **Intermediate**: Property-based testing with formal specifications
3. **Advanced**: TLA+ specifications for critical system properties
4. **Ultimate**: Full formal verification of system correctness

The graded failure policy provides a solid foundation for this evolution, ensuring that validation failures are never ignored while runtime failures are handled with appropriate resilience patterns.

---

## Summary of Enhanced Validation Framework

This enhanced validation framework ensures maximum robustness, quality, and flexibility through:

### Robustness Improvements
- **Pre-Runtime Simulation (Tier 3):** Catches configuration and dependency issues before runtime
- **Component Capability Contracts:** Formal specification of all requirements and guarantees
- **Multi-Stage Validation:** Problems caught and fixed at each generation stage
- **Bidirectional Validation:** Complete verification from requirements to behavior and back

### Quality Improvements
- **Semantic Type System:** Business logic correctness enforced through semantic types
- **Test Oracle Generation:** Comprehensive test expectations, not just inputs
- **Invariant Checking:** Properties that must always hold are continuously validated
- **Performance Expectations:** Built-in performance validation against contracts

### Flexibility Improvements
- **Component Contracts:** Any component type can declare its full capabilities and needs
- **Semantic Types:** Support for domain-specific types and validation rules
- **Stage-by-Stage Healing:** Each stage has specialized self-healing mechanisms
- **Extensible Validation:** New validation tiers and checks can be added without breaking existing ones

The framework ensures that every potential failure point has a validation check, and every validation check is coupled with LLM-based self-healing through the Semantic Healer, creating a robust, self-correcting system that generates high-quality code aligned with user intent.

---

## Implementation Priority Guide

Based on value/difficulty ratings, recommended implementation order:

### Phase 1: High Value, Low-Medium Difficulty (Immediate Impact)
1. **Validation Provenance & Audit Trail** (⭐⭐⭐⭐⭐/🔧🔧) - Essential for debugging
2. **Degradation Path Validation** (⭐⭐⭐⭐⭐/🔧🔧🔧) - Critical for production
3. **Context-Aware Healing** (⭐⭐⭐⭐⭐/🔧🔧🔧) - Dramatically improves fixes

### Phase 2: High Value, Higher Difficulty (Strategic Investment)
4. **Compositional Validation** (⭐⭐⭐⭐⭐/🔧🔧🔧🔧) - Catches integration issues
5. **Adversarial Validation** (⭐⭐⭐⭐/🔧🔧🔧🔧) - Security and robustness
6. **Cross-System Pattern Learning** (⭐⭐⭐⭐/🔧🔧🔧🔧) - Long-term quality improvement

### Phase 3: Specialized Value (As Needed)
7. **Temporal & Stateful Validation** (⭐⭐⭐⭐/🔧🔧🔧🔧🔧) - For stateful systems
8. **Constraint Solver Integration** (⭐⭐⭐⭐/🔧🔧🔧🔧🔧) - For complex configs
9. **Multi-Environment Validation** (⭐⭐⭐/🔧🔧) - For production deployment
10. **Incremental Re-validation** (⭐⭐⭐/🔧🔧🔧) - For development speed

### Quick Wins (Start Today)
- Add logging for validation decisions (toward Provenance)
- Implement basic fallback paths (toward Degradation)
- Pass pipeline context to semantic healer (toward Context-Aware) 