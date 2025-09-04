# Evidence: Phase 1 - Blueprint Validation Analysis

**Date**: 2025-08-26  
**Task**: Analyze current validation logic that blocks simple blueprints

## Current Validation Rules Found

### Location: `autocoder_cc/blueprint_language/architectural_validator.py`

The validation logic is in the `_validate_legacy_node_terminalism` method starting at line 440:

```python
# Lines 440-476 show the core validation logic:

# Check for API-based pattern first (special case)
has_api_endpoint = any(comp.type == 'APIEndpoint' for comp in system_blueprint.system.components)
has_store_or_controller = any(comp.type in {'Store', 'Controller'} for comp in system_blueprint.system.components)

# API-based patterns are valid without traditional sources
if has_api_endpoint and has_store_or_controller:
    # API patterns can work without sources
    logger.info("Detected API-based architecture pattern - relaxed source validation")
else:
    # Traditional data flow pattern - need both sources and sinks
    if not sources:
        self.validation_errors.append(ArchitecturalValidationError(
            error_type="missing_sources",
            severity="error",
            message="No sources found after role inference",
            suggestion="Add at least one Source, EventSource, or component with no inputs"
        ))
```

### Key Findings:

1. **Source Requirement Logic**: Line 461-466
   - System REQUIRES sources unless it has both APIEndpoint AND (Store OR Controller)
   - Error type: "missing_sources" 
   - Severity: "error" (blocks generation)

2. **Role Inference**: Components are categorized by effective roles
   - Sources: Components with no inputs OR type='Source'/'EventSource'
   - Sinks: Components with no outputs OR type='Store'/'Sink'

3. **API Pattern Exception**: Lines 444-458
   - API patterns (APIEndpoint + Store/Controller) bypass source requirement
   - But simple "hello world" APIs with just APIEndpoint still fail

4. **Validation is Called From**: `system_blueprint_parser.py` line 185
   ```python
   self._validate_system_semantics(system_blueprint)
   ```

## Problem Analysis

The current validation is too strict for simple cases:

1. **Hello World API**: Just an APIEndpoint should be valid
2. **Simple Sink**: A data consumer without source should be valid 
3. **Pure Transformation**: Transform-only systems should be valid

## Solution Strategy

Need to add a `strict_mode` parameter that:
1. Defaults to False for development/simple systems
2. Can be enabled for production validation
3. Relaxes the source requirement for:
   - Systems with APIEndpoint only
   - Systems with Controller only  
   - Development/test systems

## Files to Modify

1. **architectural_validator.py**: Add strict_mode parameter
2. **system_blueprint_parser.py**: Pass strict_mode to validator
3. **smoke_test.py**: Use relaxed mode for simple test

## Raw Validation Test

```bash
# Current behavior - FAILS
python3 -c "
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
parser = SystemBlueprintParser()
test_yaml = '''
system:
  name: hello_api
  components:
    - name: api
      type: APIEndpoint
  bindings: []
'''
result = parser.parse_string(test_yaml)
print('Parsed successfully')
" 2>&1

# Output:
ERROR:autocoder_cc.architectural_validator:No sources found after role inference
ValueError: System blueprint validation failed after 4 attempts with 1 errors
  system: [missing_sources] No sources found after role inference
```

This confirms the "missing_sources" error is blocking simple API generation.