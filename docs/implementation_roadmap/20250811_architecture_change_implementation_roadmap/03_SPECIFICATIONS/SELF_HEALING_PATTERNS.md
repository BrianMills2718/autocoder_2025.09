# Self-Healing Patterns for Port-Based Architecture

*Purpose: Patterns and strategies for achieving 100% validation through self-healing*

## Core Principle

**"Generated code doesn't need to be perfect, but self-healing MUST make it perfect"**

## Transactional Healing Approach

```python
class TransactionalHealer:
    MAX_PASSES = 3  # Bounded attempts per layer
    
    async def heal(self, code):
        checkpoint = code.copy()  # Save current state
        
        for pass_num in range(self.MAX_PASSES):
            healed_code = await self.apply_healing_patterns(code)
            
            if self.is_valid(healed_code):
                return healed_code  # Success!
            elif self.is_worse_than(healed_code, checkpoint):
                # Rollback - healing made it worse
                return await self.escalate(checkpoint)
            else:
                # Made progress, continue
                code = healed_code
                checkpoint = code.copy()  # New checkpoint
        
        # Couldn't fix at this level, escalate
        return await self.escalate(checkpoint)
```

## Port-Specific Healing Patterns

### AST-Level Patterns

```python
# Pattern 1: Missing async iteration
BROKEN:  for item in self.input_ports["in_data"]:
FIXED:   async for item in self.input_ports["in_data"]:

# Pattern 2: Wrong port access
BROKEN:  self.ports["input"]
FIXED:   self.input_ports["in_input"]

# Pattern 3: Missing await on send
BROKEN:  self.output_ports["out_data"].send(data)
FIXED:   await self.output_ports["out_data"].send(data)

# Pattern 4: Direct stream access instead of port
BROKEN:  self.receive_streams["data"]
FIXED:   self.input_ports["in_data"]

# Pattern 5: Wrong port naming
BROKEN:  self.add_input_port("data", Schema)
FIXED:   self.add_input_port("in_data", Schema)

# Pattern 6: Missing port prefix
BROKEN:  self.add_output_port("result", Schema)
FIXED:   self.add_output_port("out_result", Schema)
```

### Type-Level Patterns

```python
# Pattern 1: Schema mismatch
DETECT:  Output port sends Dict, input expects TodoItem
FIX:     Wrap dict in TodoItem() constructor

# Pattern 2: Missing schema import
DETECT:  Uses TodoItem but not imported
FIX:     Add: from schemas import TodoItem

# Pattern 3: Incompatible port connection
DETECT:  OutputPort[DataA] -> InputPort[DataB]
FIX:     Add transformer or coercion

# Pattern 4: Missing Pydantic BaseModel
DETECT:  class Schema: (not inheriting BaseModel)
FIX:     class Schema(BaseModel):
```

### Component-Level Patterns

```python
# Pattern 1: Missing configure_ports
DETECT:  PortBasedComponent without configure_ports
FIX:     Add empty configure_ports method

# Pattern 2: Missing process method
DETECT:  Component without process()
FIX:     Add process() that reads from inputs and writes to outputs

# Pattern 3: Wrong base class
DETECT:  class Component(ComposedComponent)
FIX:     class Component(PortBasedComponent)

# Pattern 4: Missing async on process
DETECT:  def process(self):
FIX:     async def process(self):
```

## Healing Priority Order

1. **Fix imports** (most common issue)
2. **Fix async/await** (second most common)
3. **Fix port naming** (in_, out_, err_ prefixes)
4. **Fix port access** (input_ports vs output_ports)
5. **Fix schema validation** (add missing types)
6. **Fix component structure** (missing methods)

## Implementation Strategy

### BasicHealer (v1 - 80% target)
```python
class BasicHealer:
    def __init__(self):
        self.patterns = [
            FixImportsPattern(),
            FixAsyncPattern(),
            FixPortNamingPattern(),
            FixPortAccessPattern()
        ]
    
    async def heal(self, code):
        for pattern in self.patterns:
            code = await pattern.apply(code)
        return code
```

### AdvancedHealer (v2 - 100% target)
```python
class AdvancedHealer:
    def __init__(self):
        self.ast_healer = ASTHealer()
        self.type_healer = TypeHealer()
        self.component_healer = ComponentHealer()
        self.llm_healer = LLMHealer()  # Fallback
    
    async def heal(self, code):
        # Try each healer in order
        code = await self.ast_healer.heal(code)
        if not self.is_valid(code):
            code = await self.type_healer.heal(code)
        if not self.is_valid(code):
            code = await self.component_healer.heal(code)
        if not self.is_valid(code):
            code = await self.llm_healer.heal(code)
        return code
```

## Validation After Healing

```python
async def validate_healed_component(component_code):
    """Ensure component works after healing"""
    # 1. Parse AST
    tree = ast.parse(component_code)
    
    # 2. Check structure
    assert has_configure_ports(tree)
    assert has_process_method(tree)
    assert uses_correct_base_class(tree)
    
    # 3. Import and instantiate
    module = import_string_as_module(component_code)
    component = module.Component()
    
    # 4. Test with mock data
    test_data = generate_test_data(component)
    results = await run_component_tests(component, test_data)
    
    return results.success_rate >= 0.8  # v1 target
```

## Success Metrics

### v1 (BasicHealer)
- Fix 80% of generation issues automatically
- Handle all common patterns
- Fall back to manual fix for complex issues

### v2 (AdvancedHealer)
- Fix 100% of generation issues
- Use LLM as final fallback
- Never fail validation

---
*These patterns ensure generated code always works through systematic healing.*