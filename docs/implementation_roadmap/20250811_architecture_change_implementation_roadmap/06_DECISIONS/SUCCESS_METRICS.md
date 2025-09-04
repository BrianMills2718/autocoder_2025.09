# Success Metrics Definition

*Date: 2025-08-12*
*Status: DEFINED - Clear measurable criteria*

## 📊 Primary Success Metric: Validation Success Rate

### Definition
**Validation Success Rate** = Percentage of components that pass integration testing in a generated system

### Formula
```
Success Rate = (Passed Components / Total Components) × 100%

Where:
- Total Components = All components generated for a system
- Passed Components = Components where ≥66.7% of test cases pass (2 out of 3)
```

### Current Implementation
From `integration_validation_gate.py`:
- Tests each component with 3 test cases
- Component passes if 2+ test cases succeed (66.7%)
- System passes if overall success rate ≥ target threshold

## 🎯 Target Thresholds

### Current State (Baseline)
- **27.8% validation success** 
- Measured on generated systems with wrong imports
- Most components fail to load due to import errors

### v1 Target (MVP)
- **80% validation success**
- 80% of components in generated systems must pass testing
- Example: 8 out of 10 components pass their tests

### v2 Target (Future)
- **95% validation success**
- Near-perfect generation quality
- Only edge cases fail

## 📈 Measurement Method

### 1. Generate System
```bash
python -m autocoder_cc.cli generate blueprint.yaml -o generated_systems/test_system/
```

### 2. Run Validation
```python
from autocoder_cc.blueprint_language.integration_validation_gate import IntegrationValidationGate

gate = IntegrationValidationGate()
result = await gate.validate_system(
    components_dir=Path("generated_systems/test_system/components"),
    system_name="test_system"
)

print(f"Success Rate: {result.success_rate}%")
print(f"Pass/Fail: {'PASS' if result.can_proceed else 'FAIL'}")
```

### 3. Validation Output
```
System: test_system
Total Components: 10
Passed Components: 8
Failed Components: 2
Success Rate: 80.0%
Can Proceed: True (meets v1 target)
```

## 🔍 What Gets Tested

### Per Component Tests (3 test cases each)
1. **Basic Functionality** - Can the component process basic input?
2. **Integration** - Can it communicate with other components?
3. **Error Handling** - Does it handle errors gracefully?

### Component Types and Test Data
```python
# Controller components
- Test: add_task action
- Test: get_all_tasks action  
- Test: error handling

# Store components
- Test: add_item action
- Test: list_items action
- Test: persistence check

# API Endpoint components
- Test: POST request handling
- Test: GET request handling
- Test: Error response

# Generic components
- Test: Basic data processing
- Test: Data transformation
- Test: Error conditions
```

## 📋 Transformer Drop Metrics (v1 Requirement)

### Required Metrics for Drop Tracking

**Messages Input Counter**:
- `messages_in_total{component_id, component_type}` 
- Increment for every message entering transform()

**Messages Dropped Counter**:
- `messages_dropped_total{component_id, component_type, reason}`
- Increment when transform() returns None
- Reason examples: "validation_failed", "deduplication", "rate_limit"
- **NOT** counted as errors_total

**Messages Output Counter**:
- `messages_out_total{component_id, component_type}`
- Increment for every non-None return from transform()

**Error Counter** (separate from drops):
- `errors_total{component_id, component_type, error_type}`
- Only increment when transform() raises exception
- Drops are NOT errors

### Drop Observability Requirements

1. **Log dropped messages** at INFO level with reason
2. **Sample dropped payloads** (first 10 per reason, PII-masked)
3. **require_output validation**: DropForbiddenError counts as error, not drop

## 📋 Secondary Success Metrics

### Performance Metrics (v2 and beyond - NOT v1)
| Metric | Current | v1 Target | v2 Target | Measurement |
|--------|---------|-----------|-----------|-------------|
| Throughput | Unknown | N/A (functional only) | 1000 msg/sec | Messages processed per second |
| p95 Latency | Unknown | N/A (functional only) | <50ms | 95th percentile response time |
| Memory Usage | Unknown | N/A (functional only) | <500MB | Peak RSS during load test |
| Startup Time | Unknown | N/A (functional only) | <5s | Time to ready state |

**Note**: v1 focuses on functional correctness only. Performance metrics are v2+ goals.

### Quality Metrics
| Metric | Current | v1 Target | v2 Target | Measurement |
|--------|---------|-----------|-----------|-------------|
| Import Errors | Many | 0 | 0 | Files with import failures |
| Type Errors | Unknown | <5 | 0 | mypy/pyright errors |
| Test Coverage | ~10% | 80% | 95% | pytest coverage report |
| Lint Score | Unknown | 8/10 | 10/10 | pylint/ruff score |

## 🏆 Pass/Fail Criteria

### v1 Release Criteria (MVP)
- [ ] Validation Success Rate ≥ 80%
- [ ] Throughput ≥ 1000 msg/sec
- [ ] p95 Latency < 50ms
- [ ] Zero import errors
- [ ] Test coverage ≥ 80%

### System Ready When
```python
def is_v1_ready(metrics):
    return all([
        metrics.validation_success_rate >= 80.0,
        metrics.throughput >= 1000,
        metrics.p95_latency_ms < 50,
        metrics.import_errors == 0,
        metrics.test_coverage >= 80.0
    ])
```

## 📊 Tracking Progress

### Daily Metrics Collection
```bash
# Run daily validation
./scripts/daily_validation.sh

# Output format
DATE: 2025-08-12
VALIDATION_RATE: 27.8%  # Current
TARGET: 80.0%           # v1 target
DELTA: -52.2%          # Gap to close
TREND: ↑ +5.2%         # Improvement from yesterday
```

### Validation Improvement Tracking
```
Day 0: 27.8% (baseline - import errors)
Day 1: 75.0% (after fixing imports)
Day 2: 78.0% (after fixing component issues)
Day 3: 82.0% (after optimization)
Day 4: 85.0% (exceeds v1 target!)
```

## 🚨 Failure Indicators

### Red Flags (Stop and Fix)
- Validation rate < 50% after import fixes
- Throughput < 100 msg/sec
- p95 latency > 500ms
- Memory leak detected
- System crashes during validation

### Yellow Flags (Monitor Closely)
- Validation rate 50-79%
- Throughput 100-999 msg/sec
- p95 latency 50-100ms
- Flaky tests (intermittent failures)
- High CPU usage (>80%)

## ✅ Evidence Required

For each metric claim, provide:
1. **Raw command output** showing the measurement
2. **Timestamp** when measured
3. **System configuration** during measurement
4. **Reproducible steps** to verify

Example Evidence:
```bash
$ date
2025-08-12 10:30:00 UTC

$ python validate_system.py generated_systems/test_system/
Loading system...
Testing todo_controller... PASS (3/3)
Testing todo_store... PASS (2/3)
Testing todo_api... PASS (3/3)
...
VALIDATION RATE: 83.3% (10/12 components)
STATUS: PASS (exceeds 80% threshold)

$ python benchmark.py
Throughput: 1,234 msg/sec
p95 Latency: 42.3ms
Memory: 423MB
STATUS: PASS (all metrics within targets)
```

---
*Success is measurable, reproducible, and evidence-based. No assumptions, only verified results.*