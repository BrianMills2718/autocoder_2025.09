# Autocoder4_CC Test Suite

This directory contains the comprehensive test suite for Autocoder4 organized by test type and functionality.

## 📁 Test Organization

### **Unit Tests** (`unit/`)
Tests for individual components and functions:
- `test_validation_framework.py` - Validation framework unit tests
- `test_input_sanitization.py` - Input sanitization tests
- `test_schema_versioning.py` - Schema versioning tests
- `test_todo_error.py` - Error handling tests

### **Integration Tests** (`integration/`)
Tests for component interactions and integration:
- `test_ast_integration_simple.py` - AST integration tests
- `test_componentregistry_ast_integration.py` - Component registry integration
- `test_observability_integration.py` - Observability integration
- `test_fastapi_cqrs_architecture.py` - CQRS architecture integration

### **End-to-End Tests** (`e2e/`)
Complete system workflow tests:
- `test_comprehensive_e2e.py` - Comprehensive end-to-end tests
- `test_end_to_end_realistic.py` - Realistic scenario tests
- `test_system_run.py` - System execution tests
- `test_hybrid_system.py` - Hybrid system tests

### **Performance Tests** (`performance/`)
Performance and robustness tests:
- `test_pipeline_robustness.py` - Pipeline robustness tests
- `test_validation_structure.py` - Validation performance tests

### **Security Tests** (`security/`)
Security and compliance tests:
- `test_lockfile.py` - Lockfile security tests
- `test_ast_security_validation.py` - AST security validation
- `test_production_secret_management.py` - Secret management tests
- `test_constraint_engine_placeholder.py` - Constraint engine tests

### **Analysis Tests** (`analysis/`)
Code analysis and AST tests:
- `test_ast_error_handling.py` - AST error handling
- `test_placeholder_detection.py` - Placeholder detection
- `test_secret_detection.py` - Secret detection

### **Observability Tests** (`observability/`)
Observability and monitoring tests:
- `test_observability_standalone.py` - Standalone observability tests
- `test_junit_xml_generation.py` - JUnit XML generation tests

### **CQRS Tests** (`cqrs/`)
Command Query Responsibility Segregation tests:
- `test_fastapi_cqrs_standalone.py` - CQRS standalone tests
- `test_schema_versioning_standalone.py` - Schema versioning tests

### **Comprehensive Tests** (`comprehensive/`)
Large-scale comprehensive test suites:
- `test_comprehensive.py` - Comprehensive test suite
- `test_hybrid_with_env.py` - Environment-aware hybrid tests

### **Test Tools** (`tools/`)
Test utilities and runners:
- `component_test_runner.py` - Component test runner
- `component_test_runner.py.bak` - Backup test runner

### **Fixtures** (`fixtures/`)
Test data and fixtures:
- `ast_validation_demo.json` - AST validation demo data
- `ast_validation_test.json` - AST validation test data

### **Artifacts** (`artifacts/`)
Test output and artifacts:
- `test_results.json` - Test results data

## 🚀 Running Tests

### Run All Tests
```bash
pytest autocoder_cc/tests/
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest autocoder_cc/tests/unit/

# Integration tests only
pytest autocoder_cc/tests/integration/

# End-to-end tests only
pytest autocoder_cc/tests/e2e/

# Security tests only
pytest autocoder_cc/tests/security/
```

### Run Specific Test Files
```bash
# Run a specific test file
pytest autocoder_cc/tests/unit/test_validation_framework.py

# Run with verbose output
pytest autocoder_cc/tests/unit/test_validation_framework.py -v
```

### Run Tests with Coverage
```bash
pytest autocoder_cc/tests/ --cov=autocoder_cc --cov-report=html
```

## 📊 Test Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Unit** | Test individual functions/classes | Validation, sanitization, schema tests |
| **Integration** | Test component interactions | AST integration, registry tests |
| **E2E** | Test complete workflows | System generation, realistic scenarios |
| **Performance** | Test performance characteristics | Pipeline robustness, validation speed |
| **Security** | Test security features | Secret management, AST security |
| **Analysis** | Test code analysis features | Placeholder detection, error handling |
| **Observability** | Test monitoring features | JUnit XML, observability integration |
| **CQRS** | Test CQRS architecture | FastAPI CQRS, schema versioning |
| **Comprehensive** | Large-scale test suites | Full system validation |

## 🔧 Test Guidelines

### Writing New Tests
1. **Choose the right category** - Place tests in the appropriate directory
2. **naming conventions** - Use descriptive test names
3. **Include proper assertions** - Test both success and failure cases
4. **Add docstrings** - Document test purpose and expected behavior
5. **Use fixtures** - Reuse test data from `fixtures/` directory

### Test Quality Standards
- **Coverage**: Aim for >80code coverage
- **Speed**: Tests should run quickly (<30s for full suite)
- **Isolation**: Tests should not depend on each other
- **Clarity**: Test names and assertions should be clear and descriptive

### Continuous Integration
- All tests must pass before merging
- Coverage reports are generated automatically
- Performance tests are run on every build
- Security tests are mandatory for all changes

## 📈 Test Metrics

### Coverage Targets
- **Overall Coverage**: >80%
- **Critical Paths**: >95%
- **New Features**: 100% coverage required

### Performance Targets
- **Unit Tests**: <5s total
- **Integration Tests**: <30s total
- **E2E Tests**: <2min total
- **Full Suite**: <5min total

### Quality Metrics
- **Test Reliability**: >99pass rate
- **Test Maintenance**: <5% flaky tests
- **Documentation**: 100% of test categories documented

---

**Last Updated**:2025716**Test Count**: 30+ test files across 10 categories
**Coverage**: Comprehensive coverage of core functionality 