# Evidence: Configuration Requirements Implementation
Date: 2025-08-28 13:00:00  
Component: Uncertainty #10 - Config Requirements Implementation

## Command
```bash
python3 investigations/validation_uncertainties/investigate_config_requirements.py
```

## Output
```
INVESTIGATION: Configuration Requirements Implementation
============================================================
Understanding how components should declare config requirements

============================================================
INVESTIGATION 1: Existing Implementations
============================================================

Sink:
  ✗ Inherits from ComposedComponent
    Returns: []
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

Source:
  ✗ Inherits from ComposedComponent
    Returns: []
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

Filter:
  ✓ Overrides get_required_config_fields
    Returns: ['filter_conditions']
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

Router:
  ✓ Overrides get_required_config_fields
    Returns: []
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

Store:
  ✗ Inherits from ComposedComponent
    Returns: []
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

APIEndpoint:
  ✗ Inherits from ComposedComponent
    Returns: []
  Config-related methods: ['get_required_config_fields', 'reconfigure_capability']

============================================================
INVESTIGATION 2: Override Pattern Test
============================================================
✓ Override successful!
  Returns 2 requirements

  Requirement: output_destination
    Type: str
    Required: True
    Description: Where to write output data

  Requirement: format
    Type: str
    Required: True
    Description: Output format

============================================================
INVESTIGATION 3: Config Usage Patterns
============================================================
Filter component config usage:
  Found 7 config access points
    1. self.filter_conditions = config.get("filter_conditions", [])...
    2. self.filter_action = config.get("filter_action", "pass")...
    3. self.transformation_rules = config.get("transformation_rules", [])...
    4. self.default_action = config.get("default_action", "pass")...
    5. self.condition_type = config.get("condition_type", "expression")...

  Config keys accessed: ['action', 'condition_type', 'custom_functions', 'default_action', 'filter_action', 'filter_conditions', 'transformation_rules']
```

## Key Findings

### ✅ RESOLVED: How should components declare configuration requirements?

**Answer**: Components can override `get_required_config_fields()` to return structured requirements.

### Current Implementation Status

1. **Method exists but underutilized**
   - Base method in ComposedComponent returns empty list
   - Only Filter overrides it (returns `['filter_conditions']`)
   - Router overrides but still returns empty list

2. **Override pattern works**
   - Successfully tested overriding in subclass
   - Can return structured requirement objects
   - All child components would use overridden version

3. **Config usage patterns identified**
   - Components access via `self.config.get(key, default)`
   - Filter uses 7 different config keys
   - Clear pattern of what configs each component needs

### Proposed ConfigRequirement Format

```python
@dataclass
class ConfigRequirement:
    name: str                          # Config field name
    type: str                          # Python type or semantic type
    description: str                   # Human-readable description
    required: bool = True              # Is this required?
    default: Optional[Any] = None      # Default value if not required
    validator: Optional[Callable] = None  # Custom validation function
    example: Optional[str] = None      # Example value for LLM
    semantic_type: Optional[str] = None  # 's3_url', 'db_connection', etc
    depends_on: Optional[Dict] = None  # Conditional requirements
    options: Optional[List] = None     # Valid options for enum-like fields
```

### Implementation Strategy

1. **Create ConfigRequirement dataclass** in validation module
2. **Update each component type** to override `get_required_config_fields()`
3. **Return list of ConfigRequirement** objects with full metadata
4. **Include semantic types** for LLM understanding
5. **Support conditional requirements** via `depends_on` field

## Example Implementation

```python
class DataSink(ComposedComponent):
    @classmethod
    def get_required_config_fields(cls):
        return [
            ConfigRequirement(
                name='output_destination',
                type='str',
                semantic_type='storage_url',
                description='Where to write output (S3, file, database URL)',
                required=True,
                example='s3://my-bucket/output/',
                validator=lambda x: x.startswith(('s3://', 'file://', 'postgres://'))
            ),
            ConfigRequirement(
                name='format',
                type='str',
                description='Output format',
                required=True,
                default='json',
                options=['json', 'parquet', 'csv']
            ),
            ConfigRequirement(
                name='schema',
                type='dict',
                description='Output schema for validation',
                required=False,
                depends_on={'format': 'parquet'}  # Only required for parquet
            )
        ]
```

## Impact on MVP Implementation

### Good News:
1. ✅ Infrastructure already in place
2. ✅ Override pattern confirmed working
3. ✅ Clear path to implementation

### Next Steps:
1. Create ConfigRequirement dataclass
2. Update component classes with requirements
3. Wire into validation framework
4. Test with LLM config generation

## Verdict
✅ PASS: Configuration requirements can be implemented via existing infrastructure