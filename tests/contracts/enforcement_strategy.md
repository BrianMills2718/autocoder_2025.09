# Blueprint Contract Enforcement Strategy

## Problem
Tests were testing the wrong blueprint structure because there was no enforced contract.

## Solution
Enforce a single blueprint structure contract across all code and tests.

## Implementation Steps

### 1. Immediate Actions
```python
# Replace all direct blueprint access:
# OLD (BAD):
components = blueprint["components"]  # Could be wrong!

# NEW (GOOD):
from tests.contracts.blueprint_structure_contract import BlueprintContract
components = BlueprintContract.get_components(blueprint)  # Always correct!
```

### 2. Test Migration Pattern
```python
# OLD TEST:
def test_something():
    blueprint = {
        "components": [...]  # Wrong structure!
    }
    
# NEW TEST:
from tests.contracts.blueprint_structure_contract import BlueprintTestFixture, enforce_contract_in_test

@enforce_contract_in_test
def test_something():
    blueprint = BlueprintTestFixture.create_pipeline()  # Guaranteed correct!
```

### 3. Production Code Migration
```python
# OLD CODE:
def process_blueprint(blueprint):
    for component in blueprint.get("components", []):  # Assumes flat!
        ...

# NEW CODE:
from tests.contracts.blueprint_structure_contract import BlueprintContract

def process_blueprint(blueprint):
    for component in BlueprintContract.get_components(blueprint):  # Works with any structure!
        ...
```

### 4. CI/CD Enforcement
```yaml
# .github/workflows/test.yml
- name: Validate Blueprint Contract
  run: |
    # Check no direct blueprint access
    ! grep -r 'blueprint\["components"\]' --include="*.py" .
    ! grep -r "blueprint\['components'\]" --include="*.py" .
    
    # Run contract tests
    pytest tests/contracts/ -v
```

### 5. Pre-commit Hook
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: blueprint-contract
      name: Check blueprint contract compliance
      entry: python tests/contracts/check_compliance.py
      language: python
      files: \.py$
```

## Monitoring

### Track Contract Violations
```python
# tests/contracts/check_compliance.py
import ast
import sys
from pathlib import Path

def check_file(file_path):
    """Check a Python file for blueprint contract violations"""
    violations = []
    
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        # Check for direct blueprint["components"] access
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == 'blueprint':
                if isinstance(node.slice, ast.Constant) and node.slice.value == 'components':
                    violations.append(f"{file_path}:{node.lineno}: Direct blueprint['components'] access")
    
    return violations

def main():
    violations = []
    for py_file in Path('.').rglob('*.py'):
        violations.extend(check_file(py_file))
    
    if violations:
        print("Blueprint contract violations found:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print("✅ No blueprint contract violations found")

if __name__ == "__main__":
    main()
```

## Benefits

1. **Single Source of Truth**: One place defines structure
2. **Automatic Detection**: Violations caught immediately
3. **Backward Compatibility**: Contract handles both structures
4. **Future Proof**: Easy to update contract if structure changes
5. **Test Confidence**: Tests guaranteed to match production

## Metrics

- Contract violations per week: Target 0
- Tests using BlueprintTestFixture: Target 100%
- Direct blueprint access in code: Target 0
- Blueprint structure bugs: Target 0

## Rollout Plan

Week 1:
- [ ] Update critical path tests
- [ ] Fix validation components
- [ ] Add CI checks

Week 2:
- [ ] Migrate all unit tests
- [ ] Update all blueprint consumers
- [ ] Add pre-commit hooks

Week 3:
- [ ] Full compliance audit
- [ ] Documentation update
- [ ] Team training

## Success Criteria

✅ Zero blueprint structure bugs in production
✅ All tests use contract-compliant fixtures
✅ No direct blueprint structure access in code
✅ CI/CD enforces contract automatically