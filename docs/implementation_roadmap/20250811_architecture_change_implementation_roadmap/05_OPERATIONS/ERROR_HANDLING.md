# Error Handling and StandardErrorEnvelope

*Purpose: Complete error handling strategy with standard envelope format*

## StandardErrorEnvelope Definition

```python
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel

class StandardErrorEnvelope(BaseModel):
    """Decision #50: Standard error format for all error ports"""
    ts: datetime                    # Timestamp of error
    system: str                      # System name (e.g., "todo_system")
    component: str                   # Component name (e.g., "todo_store")
    port: str                        # Port where error occurred (e.g., "in_commands")
    input_offset: int               # Message number that caused error
    category: str                   # Error category: validation|runtime|io
    message: str                    # Human-readable error message
    payload: Dict[str, Any] = {}   # Original data that caused error
    trace_id: Optional[str] = None  # Correlation ID for tracing
```

## Usage Pattern

### In Components

```python
from autocoder_cc.errors import StandardErrorEnvelope
from datetime import datetime

class TodoStore(Transformer):
    def configure_ports(self):
        self.add_input_port("in_commands", TodoCommand)
        self.add_output_port("out_responses", TodoResponse)
        self.add_output_port("err_errors", StandardErrorEnvelope)  # Error port
    
    async def transform(self, command: TodoCommand) -> TodoResponse:
        try:
            # Normal processing
            result = await self.process_command(command)
            return result
        except ValidationError as e:
            # Send to error port
            error = StandardErrorEnvelope(
                ts=datetime.utcnow(),
                system=self.config.get("system", "unknown"),
                component=self.name,
                port="in_commands",
                input_offset=self.input_ports["in_commands"].metrics.messages_in_total,
                category="validation",
                message=str(e),
                payload={"command": command.model_dump()},
                trace_id=self.config.get("trace_id")
            )
            await self.output_ports["err_errors"].send(error)
            # Return error response
            return TodoResponse(success=False, error=str(e))
```

### Error Categories

```python
# Validation errors - bad input data
category="validation"

# Runtime errors - processing failures
category="runtime"  

# IO errors - database, network, file system
category="io"
```

## Error Port Naming Convention

All error ports MUST start with `err_`:

```python
self.add_output_port("err_errors", StandardErrorEnvelope)
self.add_output_port("err_validation", StandardErrorEnvelope)
self.add_output_port("err_timeout", StandardErrorEnvelope)
```

## Error Aggregation Pattern

```python
class ErrorCollector(Sink):
    """Collects all errors from system"""
    
    def configure_ports(self):
        self.add_input_port("in_errors", StandardErrorEnvelope)
    
    async def consume(self, port_name: str, error: StandardErrorEnvelope):
        # Log error
        logger.error(f"[{error.category}] {error.component}:{error.port} - {error.message}")
        
        # Store in database
        await self.store_error(error)
        
        # Alert if critical
        if error.category == "runtime":
            await self.send_alert(error)
```

## Error Recovery Patterns

### Retry with Backoff
```python
class RetryingTransformer(Transformer):
    async def transform(self, item):
        for attempt in range(3):
            try:
                return await self.process(item)
            except Exception as e:
                if attempt == 2:  # Last attempt
                    await self.send_error(e, item)
                    raise
                await anyio.sleep(2 ** attempt)  # Exponential backoff
```

### Circuit Breaker
```python
class CircuitBreakerComponent(PortBasedComponent):
    def __init__(self):
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = None
    
    async def process(self):
        if self.circuit_open:
            if time.monotonic() - self.last_failure_time > 60:  # Try after 1 minute
                self.circuit_open = False
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await self.do_work()
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if self.failure_count >= 5:
                self.circuit_open = True
            raise
```

## Testing Error Handling

```python
@pytest.mark.asyncio
async def test_error_port():
    """Test that errors go to error port"""
    from autocoder_cc.components.ports import create_connected_ports
    
    # Create component with error port
    component = TodoStore()
    
    # Connect error port
    err_out, err_in = create_connected_ports("err_errors", "in_test", StandardErrorEnvelope)
    component.output_ports["err_errors"] = err_out
    
    # Send invalid command
    invalid_command = TodoCommand(action="invalid_action")
    
    # Process should generate error
    async with anyio.create_task_group() as tg:
        tg.start_soon(component.process)
        
        # Check error port
        error = await err_in.receive()
        assert error.category == "validation"
        assert error.component == "TodoStore"
        assert "invalid_action" in error.message
```

## Monitoring Errors

```python
def get_error_metrics():
    """Aggregate error metrics from all components"""
    metrics = {
        "total_errors": 0,
        "by_category": {"validation": 0, "runtime": 0, "io": 0},
        "by_component": {},
        "error_rate": 0.0
    }
    
    for component in all_components:
        for port_name, port in component.output_ports.items():
            if port_name.startswith("err_"):
                metrics["total_errors"] += port.metrics.messages_out_total
                # Further categorization...
    
    return metrics
```

## Error Port Implementation

```python
# File: autocoder_cc/errors/envelope.py

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class StandardErrorEnvelope(BaseModel):
    """Standard error format for all error ports"""
    ts: datetime = Field(default_factory=datetime.utcnow)
    system: str
    component: str
    port: str
    input_offset: int
    category: str = Field(regex="^(validation|runtime|io)$")
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---
*Consistent error handling enables debugging, monitoring, and recovery across the system.*