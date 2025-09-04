# Generator Integration Map

*Date: 2025-08-12*
*Status: CRITICAL - Must understand before port implementation*

⚠️ **CRITICAL DISCOVERY: Generator integration is impossible in current state**
- `system_generator.py` has ZERO recipe awareness (grep confirms no "recipe" mentions)
- Still generates 13 hardcoded RPC-based component types
- 37,933 lines of `llm_component_generator.py` still generates RPC patterns
- Integration with non-existent recipe system cannot proceed

## 🏗️ Current Generation Pipeline

### Primary Flow
```
blueprint.yaml 
    ↓
system_generator.py (orchestrator)
    ↓
llm_component_generator.py (code generation)
    ↓
ast_self_healing.py (fix/complete code)
    ↓
system_scaffold_generator.py (directory structure)
    ↓
Generated System (with wrong imports!)
```

## 📁 Key Files That Need Changes

### 1. ❌ ast_self_healing.py (CRITICAL)
**Current**: Hardcodes wrong imports
**Lines to Fix**:
- Line 223: Template with `from observability import`
- Line 305: Import mapping dictionary
- Lines 310-312: Observability imports
- Line 436: Direct import statement

**Required Changes**:
```python
# Line 305 - Fix import mappings
IMPORT_MAPPING = {
    'ComposedComponent': 'from autocoder_cc.components.composed_base import ComposedComponent',
    'StandaloneMetricsCollector': 'from autocoder_cc.observability import StandaloneMetricsCollector',
    'StandaloneTracer': 'from autocoder_cc.observability import StandaloneTracer',
    'get_logger': 'from autocoder_cc.observability import get_logger',
}
```

### 2. ⚠️ llm_component_generator.py
**Current**: Generates RPC-based components
**Size**: 37,933 lines (huge!)
**Required Changes**:
- Replace RPC patterns with port-based patterns
- Update component templates
- Change communication generation
- Update test generation

**Key Sections**:
```python
# Current RPC pattern (to remove)
async def call_service(self, service_name, method, **kwargs):
    return await self.rpc_client.call(service_name, method, kwargs)

# New port pattern (to add)  
async def process(self):
    async for message in self.input_ports["in_data"]:
        result = await self.transform(message)
        await self.output_ports["out_result"].send(result)
```

### 3. ⚠️ system_generator.py
**Current**: Main orchestrator for generation
**Size**: 2,199 lines (NOT 104K)
**Required Changes**:
- Update component type mappings
- Change from 13 types to 5 primitives + recipes
- Update validation logic
- Fix import generation

### 4. ⚠️ component_logic_generator.py
**Current**: Generates component business logic
**Size**: 93,258 lines
**Note**: Line 1492 is already correct!
**Required Changes**:
- Update to generate port-based logic
- Remove RPC communication patterns
- Add port configuration generation

### 5. ✅ Templates Directory
**Path**: `autocoder_cc/blueprint_language/templates/`
**Required New Templates**:
```
templates/
├── port_based/
│   ├── source.py.jinja2
│   ├── sink.py.jinja2
│   ├── transformer.py.jinja2
│   ├── splitter.py.jinja2
│   └── merger.py.jinja2
```

## 🔄 Integration Strategy

### Phase 1: Parallel Implementation
Create new port-based generation alongside existing:
```
blueprint_language/
├── generators/
│   ├── rpc/ (existing - keep for now)
│   │   ├── system_generator.py
│   │   └── llm_component_generator.py
│   └── port_based/ (new)
│       ├── port_system_generator.py
│       ├── port_component_generator.py
│       └── recipe_expander.py
```

### Phase 2: Recipe Expansion
Implement recipe system to map old types to new:
```python
RECIPE_MAPPING = {
    # Old type → New primitive + configuration
    "Store": {
        "primitive": "Transformer",
        "ports": {
            "input": [{"name": "in_commands", "schema": "StoreCommand"}],
            "output": [{"name": "out_responses", "schema": "StoreResponse"}]
        },
        "traits": ["persistence", "idempotency"]
    },
    "Controller": {
        "primitive": "Transformer",
        "ports": {
            "input": [{"name": "in_requests", "schema": "Request"}],
            "output": [{"name": "out_commands", "schema": "Command"}]
        },
        "traits": ["validation", "rate_limiting"]
    },
    # ... 11 more mappings
}
```

### Phase 3: Generator Selection
Add logic to choose generator based on blueprint:
```python
def select_generator(blueprint):
    if blueprint.get("architecture") == "port_based":
        return PortSystemGenerator()
    else:
        return LegacySystemGenerator()  # existing RPC
```

## 📝 Files to Create

### 1. port_system_generator.py
```python
class PortSystemGenerator:
    """Generates port-based systems from blueprints"""
    
    def generate(self, blueprint):
        # 1. Parse blueprint
        # 2. Expand recipes to primitives
        # 3. Generate component code
        # 4. Create port connections
        # 5. Generate tests
        # 6. Create system scaffold
```

### 2. port_component_generator.py
```python
class PortComponentGenerator:
    """Generates individual port-based components"""
    
    def generate_source(self, name, config):
        # Generate Source primitive
        
    def generate_sink(self, name, config):
        # Generate Sink primitive
        
    def generate_transformer(self, name, config):
        # Generate Transformer primitive
```

### 3. recipe_expander.py
```python
class RecipeExpander:
    """Expands high-level recipes to primitive components"""
    
    def expand(self, recipe_name, component_name, config):
        recipe = RECIPES[recipe_name]
        primitive = recipe["primitive"]
        
        # Generate code based on primitive type
        # Add traits (persistence, validation, etc.)
        # Configure ports
        # Return generated code
```

## 🚫 Files to NOT Modify (Yet)

These files are too complex to modify directly:
- system_generator.py (104k lines)
- llm_component_generator.py (37k lines)
- llm_component_generator_backup.py (106k lines)

Instead, create parallel implementation.

## ✅ Validation Points

### After Each Change
1. **Import Validation**:
```bash
grep -r "from observability import" generated_systems/new_test/
# Should return nothing
```

2. **Component Structure**:
```bash
# Check for port definitions
grep -r "input_ports\|output_ports" generated_systems/new_test/
# Should find port configurations
```

3. **No RPC Patterns**:
```bash
grep -r "rpc_client\|call_service" generated_systems/new_test/
# Should return nothing
```

## 🎯 Success Criteria

### Immediate (Fix imports)
- [ ] ast_self_healing.py updated with correct imports
- [ ] New generation has correct imports
- [ ] Validation rate improves from 27.8%

### Short-term (Port implementation)
- [ ] Port-based generator creates valid components
- [ ] Components have input/output ports
- [ ] No RPC patterns in generated code

### Long-term (Full migration)
- [ ] All 13 component types map to 5 primitives
- [ ] Recipe expansion works
- [ ] 80% validation success achieved

## 🔧 Implementation Order

1. **Fix ast_self_healing.py** (immediate - fixes imports)
2. **Create recipe_expander.py** (enables mapping)
3. **Create port_component_generator.py** (generates components)
4. **Create port_system_generator.py** (orchestrates generation)
5. **Add generator selection logic** (enables parallel operation)
6. **Create port templates** (Jinja2 templates)
7. **Test with simple blueprint** (validate approach)
8. **Iterate until 80% validation** (refine generation)

## ⚠️ Risks and Mitigations

### Risk: Breaking existing generation
**Mitigation**: Keep parallel implementation, don't modify existing files

### Risk: Complexity of large files
**Mitigation**: Create new, focused implementations instead of modifying

### Risk: Recipe expansion complexity
**Mitigation**: Start with simple 1:1 mappings, enhance later

### Risk: Performance degradation
**Mitigation**: Benchmark before/after, optimize hot paths

---
*This is a complex integration. Start with import fixes for immediate improvement, then build port generation in parallel.*