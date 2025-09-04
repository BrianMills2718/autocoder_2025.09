# Stream to Port Migration Strategy

## Executive Summary

This document outlines a **backward-compatible evolution strategy** from the current stream-based architecture to a future port-based model. Unlike a "big bang" migration, this approach ensures:

- ✅ **Zero breaking changes** at each phase
- ✅ **Gradual adoption** by teams and components  
- ✅ **Full reversibility** if issues arise
- ✅ **Immediate value** from each enhancement
- ✅ **Preservation of all original port-based goals**

## Core Philosophy: Evolution, Not Revolution

### Traditional Migration (High Risk)
```
Stream-Based → [BREAKING CHANGE] → Port-Based
```
- Forces system-wide rewrite
- Creates compatibility nightmares
- Risks project abandonment

### Our Approach (Low Risk)
```
Stream-Based → Enhanced Streams → Port Aliases → Hybrid Model → Optional Ports
```
- Each arrow represents a backward-compatible change
- Systems can stop at any phase and remain functional
- Old and new code coexist indefinitely

## Phase 1: Enhanced Streams with Optional Typing

### Goal
Add type safety to existing streams without modifying any current code.

### Implementation
```python
# NEW: Type wrapper (autocoder_cc/streams/typed.py)
from typing import AsyncIterator, Generic, TypeVar, Optional
import inspect

T = TypeVar('T')

class TypedStream(Generic[T]):
    """Backward-compatible typed wrapper for streams"""
    
    def __init__(self, stream, schema: Optional[Type[T]] = None):
        self._stream = stream
        self._schema = schema
    
    async def __aiter__(self) -> AsyncIterator[T]:
        async for item in self._stream:
            if self._schema and not isinstance(item, self._schema):
                # Optional runtime validation
                raise TypeError(f"Expected {self._schema}, got {type(item)}")
            yield item
    
    @classmethod
    def wrap(cls, stream_dict: dict, key: str, schema: Optional[Type[T]] = None):
        """Convenience wrapper for stream dictionaries"""
        return cls(stream_dict.get(key, []), schema)
```

### Usage Example
```python
# Existing code - still works!
async def process_legacy(self):
    async for item in self.receive_streams.get('input', []):
        result = await self.transform(item)
        await self.send_streams['output'].send(result)

# Enhanced code - type-safe!
from autocoder_cc.streams.typed import TypedStream
from .schemas import TodoItem, TodoResult

async def process_typed(self):
    input_stream = TypedStream.wrap(self.receive_streams, 'input', TodoItem)
    output_stream = self.send_streams.get('output')
    
    async for item in input_stream:  # item: TodoItem (IDE knows this!)
        result: TodoResult = await self.transform(item)
        await output_stream.send(result)
```

### Adoption Strategy
1. **Add TypedStream utility** to codebase
2. **Update examples** to show typed usage
3. **Gradually update components** as they're modified
4. **No forced migration** - both styles work forever

### Success Metrics
- IDE autocomplete starts working
- Type errors caught at development time
- Zero breaking changes to existing code
- Optional mypy type checking passes

## Phase 2: Port Aliases Over Streams

### Goal
Introduce a port-like interface while maintaining stream infrastructure.

### Implementation
```python
# NEW: Port abstraction (autocoder_cc/ports/aliases.py)
class PortAlias:
    """Port interface over existing streams"""
    
    def __init__(self, stream_dict: dict, port_name: str, 
                 schema: Optional[Type] = None, 
                 direction: str = 'input'):
        self._streams = stream_dict
        self._name = port_name
        self._schema = schema
        self._direction = direction
    
    async def __aiter__(self):
        """Allow async iteration for input ports"""
        if self._direction != 'input':
            raise TypeError(f"Cannot iterate over output port '{self._name}'")
        
        stream = self._streams.get(self._name, [])
        async for item in stream:
            if self._schema:
                # Optional validation
                self._validate(item)
            yield item
    
    async def send(self, item):
        """Send data through output port"""
        if self._direction != 'output':
            raise TypeError(f"Cannot send to input port '{self._name}'")
        
        if self._schema:
            self._validate(item)
        
        if self._name in self._streams:
            await self._streams[self._name].send(item)
    
    def _validate(self, item):
        """Optional schema validation"""
        if not isinstance(item, self._schema):
            raise TypeError(f"Port '{self._name}' expects {self._schema}")

# NEW: Component base enhancement
class EnhancedComponent(Component):
    """Component with automatic port creation"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._setup_ports()
    
    def _setup_ports(self):
        """Create port aliases from configuration"""
        # Automatic port creation based on component type
        if hasattr(self, 'PORT_DEFINITIONS'):
            for port_def in self.PORT_DEFINITIONS:
                port = PortAlias(
                    self.receive_streams if port_def['direction'] == 'input' else self.send_streams,
                    port_def['name'],
                    port_def.get('schema'),
                    port_def['direction']
                )
                setattr(self, f"{port_def['name']}_port", port)
        else:
            # Default ports for backward compatibility
            self.input_port = PortAlias(self.receive_streams, 'input', direction='input')
            self.output_port = PortAlias(self.send_streams, 'output', direction='output')
```

### Usage Example
```python
class TodoProcessor(EnhancedComponent):
    PORT_DEFINITIONS = [
        {'name': 'input', 'direction': 'input', 'schema': TodoItem},
        {'name': 'output', 'direction': 'output', 'schema': TodoResult},
        {'name': 'errors', 'direction': 'output', 'schema': ErrorEvent}
    ]
    
    async def process(self):
        # Can use EITHER syntax!
        
        # Stream syntax (still works)
        async for item in self.receive_streams.get('input', []):
            pass
        
        # Port syntax (also works)
        async for item in self.input_port:
            try:
                result = await self.transform(item)
                await self.output_port.send(result)
            except Exception as e:
                await self.errors_port.send(ErrorEvent(str(e)))
```

### Benefits
- Both syntaxes work simultaneously
- Gradual component migration
- Type safety through port schemas
- Better error messages

## Phase 3: Migration Tooling

### Goal
Provide automated assistance for component migration.

### Implementation
```python
# NEW: Migration assistant (autocoder_cc/tools/migration.py)
import ast
import inspect
from typing import List, Tuple

class MigrationAnalyzer:
    """Analyze components for migration readiness"""
    
    def analyze_component(self, component_class) -> dict:
        """Analyze a component for migration readiness"""
        source = inspect.getsource(component_class)
        tree = ast.parse(source)
        
        return {
            'uses_streams': self._uses_streams(tree),
            'uses_ports': self._uses_ports(tree),
            'stream_names': self._extract_stream_names(tree),
            'complexity': self._calculate_complexity(tree),
            'migration_effort': self._estimate_effort(tree),
            'recommendations': self._generate_recommendations(tree)
        }
    
    def migrate_component(self, component_class, target_phase: int = 2):
        """Automated migration with AST transformation"""
        source = inspect.getsource(component_class)
        tree = ast.parse(source)
        
        if target_phase >= 1:
            tree = self._add_type_hints(tree)
        
        if target_phase >= 2:
            tree = self._convert_to_ports(tree)
        
        return ast.unparse(tree)
    
    def _convert_to_ports(self, tree: ast.AST) -> ast.AST:
        """Convert stream access to port access"""
        class PortTransformer(ast.NodeTransformer):
            def visit_Attribute(self, node):
                # Transform: self.receive_streams.get('input', [])
                # To: self.input_port
                if (isinstance(node.value, ast.Attribute) and
                    node.value.attr == 'receive_streams' and
                    node.attr == 'get'):
                    # Extract port name from get() call
                    return ast.Attribute(
                        value=ast.Name(id='self'),
                        attr='input_port'
                    )
                return node
        
        return PortTransformer().visit(tree)
```

### Migration Process
```python
# CLI tool for migration
$ autocoder migrate-component TodoProcessor --phase 2

Analyzing TodoProcessor...
✓ Uses 3 input streams: ['input', 'control', 'config']
✓ Uses 2 output streams: ['output', 'metrics']
✓ Complexity: Low (42 lines)
✓ Migration effort: ~15 minutes

Recommendations:
1. Add type hints for 'input' stream (TodoItem schema detected)
2. Convert 'control' stream to control_port
3. Consider merging 'metrics' into observability capability

Proceed with migration? [y/N]: y

✓ Added TypedStream wrappers
✓ Created port definitions
✓ Updated process() method
✓ Backup saved to TodoProcessor.backup.py

Migration complete! Run tests to verify:
$ pytest tests/test_todo_processor.py
```

## Phase 4: Unified Port Model (Optional)

### Goal
Provide clean port-based architecture for new components while maintaining legacy support.

### Implementation
```python
# NEW: First-class ports (autocoder_cc/ports/core.py)
class Port(Generic[T]):
    """First-class port with full type safety and validation"""
    
    def __init__(self, name: str, schema: Type[T], 
                 direction: str = 'input',
                 validators: List[Callable] = None):
        self.name = name
        self.schema = schema
        self.direction = direction
        self.validators = validators or []
        self._channel = None  # Underlying stream/channel
    
    async def connect(self, channel):
        """Connect port to underlying transport"""
        self._channel = channel
    
    async def __aiter__(self) -> AsyncIterator[T]:
        """Type-safe iteration"""
        if self.direction != 'input':
            raise PortError(f"Cannot read from output port '{self.name}'")
        
        async for item in self._channel:
            validated = await self._validate(item)
            yield validated
    
    async def send(self, item: T) -> None:
        """Type-safe sending"""
        if self.direction != 'output':
            raise PortError(f"Cannot write to input port '{self.name}'")
        
        validated = await self._validate(item)
        await self._channel.send(validated)
    
    async def _validate(self, item: T) -> T:
        """Run all validators"""
        for validator in self.validators:
            item = await validator(item)
        return item

# Component with first-class ports
class ModernComponent:
    """Pure port-based component"""
    
    # Port declarations
    input: Port[TodoItem]
    output: Port[TodoResult]
    errors: Port[ErrorEvent]
    
    def __init__(self, name: str, config: dict):
        self.input = Port('input', TodoItem, 'input')
        self.output = Port('output', TodoResult, 'output')
        self.errors = Port('errors', ErrorEvent, 'output')
    
    async def process(self):
        async for item in self.input:  # Full type safety!
            try:
                result = await self.transform(item)
                await self.output.send(result)  # Schema validated!
            except Exception as e:
                await self.errors.send(ErrorEvent.from_exception(e))
```

### Compatibility Layer
```python
class CompatibilityAdapter:
    """Allows modern components to work in legacy systems"""
    
    @staticmethod
    def adapt_to_streams(component: ModernComponent) -> Component:
        """Wrap modern component for stream-based system"""
        # Create stream dictionaries
        component.receive_streams = {}
        component.send_streams = {}
        
        # Connect ports to streams
        for attr_name in dir(component):
            attr = getattr(component, attr_name)
            if isinstance(attr, Port):
                if attr.direction == 'input':
                    stream = AsyncIterableStream()
                    component.receive_streams[attr.name] = stream
                    attr.connect(stream)
                else:
                    stream = AsyncSendableStream()
                    component.send_streams[attr.name] = stream
                    attr.connect(stream)
        
        return component
```

## Implementation Timeline

### Phase Rollout Strategy
- **No fixed dates** - progress based on readiness
- **Parallel development** - phases can overlap
- **Early adopter program** - volunteer teams test first
- **Gradual rollout** - start with non-critical components
- **Continuous validation** - extensive testing at each phase

### Success Criteria Per Phase

#### Phase 1 Success:
- [ ] TypedStream utility merged and documented
- [ ] 3+ components using typed streams in production
- [ ] Developer feedback positive
- [ ] No performance regression

#### Phase 2 Success:
- [ ] Port aliases working in test environment
- [ ] 5+ components migrated successfully
- [ ] Both syntaxes proven to coexist
- [ ] Migration guide published

#### Phase 3 Success:
- [ ] Migration tool handles 80% of components automatically
- [ ] Manual migration time reduced by 50%
- [ ] Rollback mechanism tested
- [ ] Component library 30% migrated

#### Phase 4 Success:
- [ ] Modern components demonstrate clear benefits
- [ ] Performance meets or exceeds streams
- [ ] Type safety catches real bugs
- [ ] New development prefers ports

## Risk Mitigation

### Technical Risks
1. **Performance degradation**: Benchmark at each phase
2. **Complexity increase**: Simplify where possible
3. **Breaking changes**: Extensive compatibility testing
4. **Type system limitations**: Gradual typing adoption

### Organizational Risks
1. **Developer resistance**: Optional adoption, clear benefits
2. **Migration fatigue**: Pauseable at any phase
3. **Support burden**: Both systems supported long-term
4. **Documentation lag**: Update docs before code

## Conclusion

This migration strategy provides a **safe, gradual path** from streams to ports that:

- **Preserves all existing functionality**
- **Adds value at each phase**
- **Allows stopping at any point**
- **Achieves the full port-based vision**
- **Minimizes risk and disruption**

The key insight: By treating ports as an **enhancement** rather than a **replacement**, we can evolve the architecture without forcing painful migrations.

---
**Last Updated**: 2025-08-03  
**Status**: Strategy defined, Phase 1 ready to begin  
**Next Step**: Implement TypedStream utility and test with volunteer component