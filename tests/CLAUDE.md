# Tests Directory Guide

**Purpose**: Comprehensive test suite for AutoCoder4_CC ensuring code quality, reliability, and regression prevention.

**LLM Assistant Usage**: Use this guide when writing tests, debugging failures, or understanding the testing architecture.

---

## 📁 Test Structure

### **Test Organization by Scope**

#### `unit/` - **Unit Tests**
**Purpose**: Test individual functions and classes in isolation
**Coverage**: Core components, utilities, and business logic
**Execution Time**: Fast (<10s for entire suite)
**Dependencies**: Minimal external dependencies

**Key Test Files**:
- `test_component_generation.py` - Component generation logic
- `test_aggregator_component.py` - Aggregator component functionality  
- `test_filter_component.py` - Filter component functionality
- `test_router_component.py` - Router component functionality
- `test_llm_connection.py` - LLM provider connectivity
- `test_validation_only.py` - Validation framework tests

#### `integration/` - **Integration Tests**
**Purpose**: Test component interactions and system integration points
**Coverage**: Multi-component workflows, pipeline integration
**Execution Time**: Medium (30s-2min)
**Dependencies**: Multiple components, may require external services

**Key Test Files**:
- `test_complete_pipeline.py` - End-to-end generation pipeline
- `test_localorchestrator_comprehensive.py` - Local orchestration system
- `test_phase2_integration.py` - Phase 2 development integration
- `test_service_communication_integration.py` - Inter-service communication
- `test_evidence_validation.py` - Evidence collection and validation

#### `e2e/` - **End-to-End Tests**
**Purpose**: Test complete user workflows and real-world scenarios
**Coverage**: Full system behavior, user experience validation
**Execution Time**: Slow (2-10min)
**Dependencies**: Full system stack, external services

**Key Test Files**:
- `test_end_to_end_system_validation.py` - Complete system validation
- `test_real_chaos_engineering.py` - Chaos engineering scenarios
- `test_github_workflows.py` - CI/CD workflow validation

#### `performance/` - **Performance Tests**
**Purpose**: Validate system performance and scalability
**Coverage**: Load testing, benchmark validation, resource usage
**Execution Time**: Variable (1-30min)
**Dependencies**: Performance monitoring tools

**Key Test Files**:
- `test_performance.py` - General performance benchmarks
- `test_service_communication_performance.py` - Communication performance
- `test_honest_performance_validation.py` - Statistical performance validation

### **Test Organization by Type**

#### `manual/` - **Manual Test Scripts**
**Purpose**: Scripts for manual testing and validation scenarios
**Usage**: One-off testing, debugging, experimental validation
**Execution**: Run individually as needed

**Key Scripts**:
- `test_crypto_policy_integration.py` - Cryptographic policy testing
- `test_fixed_generation.py` - Generation fix validation
- `test_p0_f6_comprehensive.py` - P0-F6 feature validation

#### `debugging/` - **Debug Test Scripts**
**Purpose**: Debug-specific tests for troubleshooting issues
**Usage**: Problem diagnosis, issue reproduction
**Execution**: Run when debugging specific problems

#### `validation/` - **Validation Tests**
**Purpose**: System validation and compliance checking
**Usage**: Ensure system meets requirements and standards

### **Supporting Infrastructure**

#### `fixtures/` - **Test Data and Fixtures**
**Purpose**: Reusable test data, mock objects, and test blueprints
**Contents**:
- `test_blueprints.py` - Standard test blueprints
- `architectural_test_cases.py` - Architecture test scenarios
- `store_component_blueprints.py` - Store component test data

#### `utils/` - **Test Utilities**
**Purpose**: Common testing utilities and helpers
**Contents**:
- `evidence_collector.py` - Evidence collection for validation
- `phase_test_runner.py` - Phase-based test execution

#### `outputs/` - **Test Output Files**
**Purpose**: Generated test outputs, temporary files, and build artifacts
**Organization**: Organized by test type and scenario
**Cleanup**: Automatically cleaned by test framework

---

## 🎯 LLM Assistant Testing Guidelines

### **Writing Tests**

#### **Test Naming Conventions**
```python
# Unit tests: test_{functionality}
def test_component_generation_creates_valid_output():
    pass

# Integration tests: test_{integration_scenario}
def test_pipeline_processes_blueprint_end_to_end():
    pass

# Performance tests: test_{performance_aspect}
def test_generation_performance_under_load():
    pass
```

#### **Test Structure Template**
```python
def test_feature_description():
    """Test description explaining what is being tested and why."""
    # Arrange: Set up test data and dependencies
    blueprint = create_test_blueprint()
    generator = ComponentGenerator()
    
    # Act: Execute the functionality being tested
    result = generator.generate(blueprint)
    
    # Assert: Verify expected behavior
    assert result.is_valid()
    assert len(result.components) > 0
    assert result.contains_required_elements()
```

#### **Test Categories by Purpose**
1. **Functional Tests**: Verify features work as designed
2. **Regression Tests**: Prevent previously fixed bugs from returning
3. **Edge Case Tests**: Handle boundary conditions and error cases
4. **Performance Tests**: Ensure acceptable performance characteristics
5. **Integration Tests**: Verify component interactions

### **Running Tests**

#### **Test Execution Commands**
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/                  # Unit tests only
pytest tests/integration/           # Integration tests only
pytest tests/e2e/                  # End-to-end tests only

# Run specific test file
pytest tests/unit/test_component_generation.py

# Run with coverage
pytest tests/ --cov=autocoder_cc --cov-report=html

# Run performance tests
pytest tests/performance/ -v

# Run manual tests (one at a time)
python tests/manual/test_crypto_policy_integration.py
```

#### **Test Configuration**
- **Configuration File**: `pytest.ini` in project root
- **Coverage Settings**: Configured for HTML and terminal output
- **Test Discovery**: Automatic discovery of `test_*.py` files
- **Markers**: Use pytest markers for test categorization

### **Debugging Failed Tests**

#### **Debug Strategy**
1. **Read the failure message**: Understand what assertion failed
2. **Check test isolation**: Ensure tests don't depend on each other
3. **Verify test data**: Confirm fixtures and test data are valid
4. **Run with verbose output**: Use `-v` flag for detailed output
5. **Use debugging scripts**: Leverage `debugging/` directory scripts

#### **Common Failure Patterns**
```python
# Environment issues
AssertionError: API key not configured
# Solution: Check .env file configuration

# Data issues  
AssertionError: Expected component count 3, got 0
# Solution: Verify test blueprint is valid

# Timing issues
AssertionError: Component not ready after 30s
# Solution: Increase timeout or check async handling
```

### **Test Development Workflow**

#### **Adding New Tests**
1. **Identify test type**: Unit, integration, e2e, or performance
2. **Choose appropriate directory**: Based on test scope and purpose
3. **Write test following template**: Include arrange, act, assert pattern
4. **Add necessary fixtures**: Create reusable test data if needed
5. **Verify test isolation**: Ensure test can run independently
6. **Update test documentation**: Add to relevant test suites

#### **Test-Driven Development (TDD)**
1. **Write failing test**: Create test for desired functionality
2. **Implement minimal code**: Make the test pass
3. **Refactor**: Improve code while keeping tests passing
4. **Repeat**: Continue for next feature

---

## 🔧 Test Infrastructure

### **Test Dependencies**
- **pytest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution
- **unittest.mock**: Mocking and stubbing
- **asyncio**: Async test support

### **Test Data Management**
- **Fixtures**: Reusable test data in `fixtures/`
- **Mock Objects**: For external service simulation
- **Temporary Files**: Automatic cleanup in `outputs/`
- **Database**: In-memory SQLite for data tests

### **Continuous Integration**
- **GitHub Actions**: Automated test execution
- **Coverage Reporting**: Minimum 80% coverage requirement
- **Performance Regression**: Automated performance monitoring
- **Quality Gates**: Tests must pass before merge

---

## 📊 Test Metrics and Quality

### **Coverage Requirements**
- **Unit Tests**: >90% line coverage
- **Integration Tests**: >80% path coverage
- **E2E Tests**: >70% feature coverage
- **Overall**: >85% combined coverage

### **Performance Benchmarks**
- **Unit Test Suite**: <30 seconds total
- **Integration Suite**: <5 minutes total
- **E2E Suite**: <15 minutes total
- **Individual Tests**: <1 minute each

### **Quality Standards**
- **Test Reliability**: <1% flaky test rate
- **Test Maintenance**: Regular cleanup and updates
- **Documentation**: All test purposes clearly documented
- **Isolation**: No test dependencies on external state

---

## 🚨 Important Guidelines

### **Test Best Practices**
1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Minimal Setup**: Only create necessary test data
4. **Fast Execution**: Keep tests as fast as possible
5. **Readable Code**: Tests should be self-documenting

### **Avoiding Common Pitfalls**
- **Don't test implementation details**: Focus on behavior
- **Don't create brittle tests**: Avoid overly specific assertions
- **Don't ignore flaky tests**: Fix or remove unreliable tests
- **Don't skip cleanup**: Ensure proper test cleanup
- **Don't hardcode values**: Use constants and fixtures

### **Test Maintenance**
- **Regular Review**: Monthly review of test effectiveness
- **Refactoring**: Keep tests clean and maintainable
- **Updates**: Update tests when requirements change
- **Deprecation**: Remove obsolete tests promptly

This testing framework ensures AutoCoder4_CC maintains high quality and reliability across all development phases and deployment scenarios.