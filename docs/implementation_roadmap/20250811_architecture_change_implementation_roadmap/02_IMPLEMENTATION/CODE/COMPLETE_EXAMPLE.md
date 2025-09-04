# Complete End-to-End Example: Blueprint to Running System

## Overview
This document provides a complete walkthrough from blueprint definition to a running port-based system, demonstrating the entire AutoCoder4_CC pipeline with the new architecture.

## 1. Blueprint Definition

### Input: Todo Management System Blueprint
```yaml
# File: todo_system_blueprint.yaml
schema_version: "1.1.0"  # Updated for port-based architecture
system:
  name: todo_management_system
  description: Simple todo management system using port-based architecture
  version: "1.0.0"
  
  components:
    # Source component that generates todo items
    - name: todo_generator
      type: Source
      description: Generate todo items for testing
      configuration:
        generation_type: scheduled
        interval_seconds: 10
        max_items: 100
      
    # Transformer to validate and enrich todos
    - name: todo_validator
      type: Transformer  
      description: Validate and enrich todo items
      configuration:
        validation_rules:
          - field: title
            required: true
            max_length: 200
          - field: priority
            values: [low, medium, high]
        enrichment:
          add_timestamp: true
          generate_id: true
    
    # Splitter to route by priority
    - name: priority_router
      type: Splitter
      description: Route todos by priority
      configuration:
        split_criteria: priority
        outputs:
          high: high_priority_queue
          medium: medium_priority_queue  
          low: low_priority_queue
    
    # Merger to combine processed todos
    - name: todo_merger
      type: Merger
      description: Merge todos from different queues
      configuration:
        merge_strategy: round_robin
        buffer_size: 100
        
    # Sink to persist todos
    - name: todo_store
      type: Sink
      description: Persist todos to storage
      configuration:
        storage_type: postgresql
        connection_string: ${DB_CONNECTION_STRING}
        batch_size: 10
        
  # Port bindings defining data flow
  bindings:
    - from: todo_generator.output
      to: todo_validator.input
      
    - from: todo_validator.output  
      to: priority_router.input
      
    - from: priority_router.high_output
      to: todo_merger.input_1
      
    - from: priority_router.medium_output
      to: todo_merger.input_2
      
    - from: priority_router.low_output
      to: todo_merger.input_3
      
    - from: todo_merger.output
      to: todo_store.input

  # System-level configuration
  configuration:
    monitoring:
      enabled: true
      metrics_port: 9090
    health_check:
      enabled: true
      endpoint: /health
    resilience:
      circuit_breaker: true
      retry_policy:
        max_retries: 3
        backoff_ms: 1000
```

## 2. Generation Process

### Step 2.1: Natural Language to Blueprint (if needed)
```python
# If starting from natural language description:
from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToBlueprint

converter = NaturalLanguageToBlueprint()
blueprint = converter.convert("""
Create a todo management system that:
- Generates test todo items periodically
- Validates and enriches them with timestamps
- Routes by priority (high, medium, low)
- Merges them back together
- Stores in a database
""")
```

### Step 2.2: Blueprint Validation
```python
from autocoder_cc.blueprint_language.blueprint_validator import BlueprintValidator

validator = BlueprintValidator()
validation_result = validator.validate(blueprint_path="todo_system_blueprint.yaml")

if not validation_result.is_valid:
    print(f"Validation errors: {validation_result.errors}")
    sys.exit(1)
```

### Step 2.3: System Generation
```python
from autocoder_cc.blueprint_language.system_generator import SystemGenerator
from pathlib import Path

generator = SystemGenerator()
output_dir = Path("generated_systems/todo_system")

# Generate the system
result = generator.generate_system(
    blueprint_path="todo_system_blueprint.yaml",
    output_dir=output_dir,
    use_port_architecture=True  # Enable new architecture
)

print(f"Generated system at: {result.output_path}")
print(f"Components generated: {len(result.components)}")
```

## 3. Generated Code Structure

### Generated Directory Structure:
```
generated_systems/todo_system/
├── components/
│   ├── __init__.py
│   ├── todo_generator.py
│   ├── todo_validator.py
│   ├── priority_router.py
│   ├── todo_merger.py
│   └── todo_store.py
├── ports/
│   ├── __init__.py
│   ├── base.py
│   └── implementations.py
├── observability/
│   ├── __init__.py
│   └── metrics.py
├── config/
│   ├── system_config.yaml
│   └── .env.example
├── tests/
│   ├── test_todo_generator.py
│   ├── test_todo_validator.py
│   └── test_integration.py
├── docker-compose.yaml
├── requirements.txt
└── main.py
```

### Sample Generated Component: todo_validator.py
```python
#!/usr/bin/env python3
"""
Todo Validator - Transformer Component
Generated by AutoCoder4_CC
"""
import anyio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from autocoder_cc.observability import get_logger
from ports.base import Transformer, Port, Message

class TodoItem(BaseModel):
    """Todo item data model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: str = Field(..., pattern="^(low|medium|high)$")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class TodoValidator(Transformer[Dict[str, Any], TodoItem]):
    """Validates and enriches todo items"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.logger = get_logger(name)
        self.validation_rules = config.get("validation_rules", [])
        self.enrichment = config.get("enrichment", {})
        
    async def setup(self):
        """Initialize the validator"""
        await super().setup()
        self.logger.info(f"TodoValidator '{self.name}' initialized")
        
    async def transform(self, message: Message[Dict[str, Any]]) -> Optional[Message[TodoItem]]:
        """Validate and enrich a todo item"""
        try:
            # Extract data
            data = message.data
            
            # Apply validation rules
            for rule in self.validation_rules:
                field = rule.get("field")
                if rule.get("required") and field not in data:
                    self.logger.warning(f"Required field '{field}' missing")
                    return None  # Drop invalid message
                    
                if field in data and "max_length" in rule:
                    if len(str(data[field])) > rule["max_length"]:
                        self.logger.warning(f"Field '{field}' exceeds max length")
                        return None
                        
                if field in data and "values" in rule:
                    if data[field] not in rule["values"]:
                        self.logger.warning(f"Field '{field}' has invalid value")
                        return None
            
            # Apply enrichment
            if self.enrichment.get("add_timestamp") and "created_at" not in data:
                data["created_at"] = datetime.utcnow().isoformat()
                
            if self.enrichment.get("generate_id") and "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            # Create validated model
            todo_item = TodoItem.model_validate(data)
            
            # Return transformed message
            return Message(
                data=todo_item,
                metadata={
                    **message.metadata,
                    "validated_at": datetime.utcnow().isoformat(),
                    "validator": self.name
                }
            )
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            await self.metrics.increment("validation_errors")
            return None  # Drop on error
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get component health status"""
        return {
            "healthy": True,
            "component": self.name,
            "type": "Transformer",
            "metrics": await self.metrics.get_snapshot()
        }
```

### Sample Generated Port Implementation: ports/base.py
```python
#!/usr/bin/env python3
"""
Port-based Architecture Base Classes
Generated by AutoCoder4_CC
"""
import anyio
from typing import TypeVar, Generic, Optional, Dict, Any, AsyncIterator
from pydantic import BaseModel, Field
from datetime import datetime
import time

T = TypeVar('T')
U = TypeVar('U')

class Message(BaseModel, Generic[T]):
    """Message wrapper for port communication"""
    data: T
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True

class Port(Generic[T]):
    """Typed port for component communication"""
    
    def __init__(self, capacity: int = 100):
        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=capacity,
            item_type=Message[T]
        )
        self.metrics = PortMetrics()
        
    async def send(self, message: Message[T]):
        """Send a message through the port"""
        start_time = time.monotonic()
        await self.send_stream.send(message)
        duration_ms = (time.monotonic() - start_time) * 1000
        await self.metrics.record_send(duration_ms)
        
    async def receive(self) -> Message[T]:
        """Receive a message from the port"""
        start_time = time.monotonic()
        message = await self.receive_stream.receive()
        duration_ms = (time.monotonic() - start_time) * 1000
        await self.metrics.record_receive(duration_ms, message.timestamp)
        return message
        
    async def close(self):
        """Close the port"""
        await self.send_stream.aclose()
        await self.receive_stream.aclose()

class PortMetrics:
    """Metrics collection for ports"""
    
    def __init__(self):
        self.sends = 0
        self.receives = 0
        self.send_duration_ms = []
        self.receive_duration_ms = []
        self.message_age_ms = []
        
    async def record_send(self, duration_ms: float):
        self.sends += 1
        self.send_duration_ms.append(duration_ms)
        
    async def record_receive(self, duration_ms: float, message_timestamp: datetime):
        self.receives += 1
        self.receive_duration_ms.append(duration_ms)
        age_ms = (datetime.utcnow() - message_timestamp).total_seconds() * 1000
        self.message_age_ms.append(age_ms)
        
    async def get_snapshot(self) -> Dict[str, Any]:
        return {
            "sends": self.sends,
            "receives": self.receives,
            "avg_send_duration_ms": sum(self.send_duration_ms) / len(self.send_duration_ms) if self.send_duration_ms else 0,
            "avg_receive_duration_ms": sum(self.receive_duration_ms) / len(self.receive_duration_ms) if self.receive_duration_ms else 0,
            "avg_message_age_ms": sum(self.message_age_ms) / len(self.message_age_ms) if self.message_age_ms else 0
        }
```

## 4. Running the System

### Main Entry Point: main.py
```python
#!/usr/bin/env python3
"""
Todo Management System - Main Entry Point
Generated by AutoCoder4_CC
"""
import anyio
import signal
from pathlib import Path

from components import (
    TodoGenerator,
    TodoValidator,
    PriorityRouter,
    TodoMerger,
    TodoStore
)
from ports.base import Port
from observability import setup_monitoring, get_logger

logger = get_logger("main")

class TodoSystem:
    """Main system orchestrator"""
    
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.components = {}
        self.ports = {}
        self.running = False
        
    def _load_config(self, path: Path) -> Dict[str, Any]:
        """Load system configuration"""
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
            
    async def setup(self):
        """Initialize all components and ports"""
        logger.info("Setting up Todo Management System")
        
        # Create ports
        self.ports = {
            "gen_to_val": Port(),
            "val_to_router": Port(),
            "router_to_merger_high": Port(),
            "router_to_merger_medium": Port(),
            "router_to_merger_low": Port(),
            "merger_to_store": Port()
        }
        
        # Create components
        self.components["generator"] = TodoGenerator(
            name="todo_generator",
            config=self.config["components"]["todo_generator"],
            output_port=self.ports["gen_to_val"]
        )
        
        self.components["validator"] = TodoValidator(
            name="todo_validator",
            config=self.config["components"]["todo_validator"],
            input_port=self.ports["gen_to_val"],
            output_port=self.ports["val_to_router"]
        )
        
        self.components["router"] = PriorityRouter(
            name="priority_router",
            config=self.config["components"]["priority_router"],
            input_port=self.ports["val_to_router"],
            output_ports={
                "high": self.ports["router_to_merger_high"],
                "medium": self.ports["router_to_merger_medium"],
                "low": self.ports["router_to_merger_low"]
            }
        )
        
        self.components["merger"] = TodoMerger(
            name="todo_merger",
            config=self.config["components"]["todo_merger"],
            input_ports=[
                self.ports["router_to_merger_high"],
                self.ports["router_to_merger_medium"],
                self.ports["router_to_merger_low"]
            ],
            output_port=self.ports["merger_to_store"]
        )
        
        self.components["store"] = TodoStore(
            name="todo_store",
            config=self.config["components"]["todo_store"],
            input_port=self.ports["merger_to_store"]
        )
        
        # Initialize all components
        for component in self.components.values():
            await component.setup()
            
        logger.info("System setup complete")
        
    async def run(self):
        """Run the system"""
        self.running = True
        logger.info("Starting Todo Management System")
        
        # Setup monitoring
        if self.config.get("monitoring", {}).get("enabled"):
            await setup_monitoring(self.config["monitoring"])
        
        # Start all components
        async with anyio.create_task_group() as tg:
            for name, component in self.components.items():
                tg.start_soon(self._run_component, name, component)
                
            # Handle shutdown signal
            tg.start_soon(self._handle_shutdown)
            
    async def _run_component(self, name: str, component):
        """Run a single component"""
        logger.info(f"Starting component: {name}")
        try:
            await component.run()
        except Exception as e:
            logger.error(f"Component {name} failed: {e}")
            await self.shutdown()
            
    async def _handle_shutdown(self):
        """Handle graceful shutdown"""
        with anyio.open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
            async for sig in signals:
                logger.info(f"Received signal {sig}, shutting down...")
                await self.shutdown()
                break
                
    async def shutdown(self):
        """Shutdown the system"""
        if not self.running:
            return
            
        self.running = False
        logger.info("Shutting down Todo Management System")
        
        # Stop all components
        for name, component in self.components.items():
            logger.info(f"Stopping component: {name}")
            await component.stop()
            
        # Close all ports
        for name, port in self.ports.items():
            await port.close()
            
        logger.info("Shutdown complete")

async def main():
    """Main entry point"""
    config_path = Path("config/system_config.yaml")
    system = TodoSystem(config_path)
    
    try:
        await system.setup()
        await system.run()
    except Exception as e:
        logger.error(f"System error: {e}")
        await system.shutdown()
        raise

if __name__ == "__main__":
    anyio.run(main)
```

## 5. Running and Testing

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_CONNECTION_STRING="postgresql://user:pass@localhost/todos"

# Run the system
python main.py

# In another terminal, check health
curl http://localhost:8080/health

# View metrics
curl http://localhost:9090/metrics
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up --build

# Scale specific components
docker-compose up --scale todo_validator=3

# View logs
docker-compose logs -f todo_validator
```

### Integration Testing
```python
# tests/test_integration.py
import anyio
import pytest
from pathlib import Path

from main import TodoSystem

@pytest.mark.anyio
async def test_todo_flow():
    """Test complete todo flow through the system"""
    # Setup
    config_path = Path("config/test_config.yaml")
    system = TodoSystem(config_path)
    await system.setup()
    
    # Run system for a short time
    async with anyio.create_task_group() as tg:
        tg.start_soon(system.run)
        
        # Wait for some processing
        await anyio.sleep(5)
        
        # Check that todos were processed
        store = system.components["store"]
        stored_count = await store.get_stored_count()
        assert stored_count > 0
        
        # Shutdown
        await system.shutdown()
        tg.cancel_scope.cancel()
```

## 6. Validation Gate Check

### Running Validation
```python
from autocoder_cc.blueprint_language.validation_gate import ValidationGate

gate = ValidationGate()
result = await gate.validate_system(
    system_path=Path("generated_systems/todo_system"),
    test_data_path=Path("tests/test_data.json")
)

print(f"Validation Success Rate: {result.success_rate}%")
print(f"Can Deploy: {result.can_proceed}")

# Expected output:
# Validation Success Rate: 85.3%
# Can Deploy: True
```

## 7. Monitoring and Observability

### Metrics Dashboard
```yaml
# Grafana dashboard showing:
- Component throughput (messages/sec)
- Port buffer utilization
- Message latency (p50, p95, p99)
- Error rates by component
- System health status
```

### Sample Metrics Output
```json
{
  "system": "todo_management_system",
  "timestamp": "2025-08-11T10:30:00Z",
  "components": {
    "todo_generator": {
      "messages_sent": 1000,
      "rate": 10.5,
      "errors": 0
    },
    "todo_validator": {
      "messages_processed": 980,
      "validation_failures": 20,
      "avg_latency_ms": 5.2
    },
    "priority_router": {
      "messages_routed": {
        "high": 196,
        "medium": 490,
        "low": 294
      }
    },
    "todo_merger": {
      "messages_merged": 980,
      "buffer_utilization": 0.45
    },
    "todo_store": {
      "messages_stored": 980,
      "batch_writes": 98,
      "storage_latency_ms": 15.3
    }
  },
  "ports": {
    "gen_to_val": {
      "buffer_depth": 5,
      "capacity": 100,
      "utilization": 0.05
    }
  }
}
```

## Summary

This complete example demonstrates:
1. **Blueprint Definition**: Clear YAML specification using 5 mathematical primitives
2. **Code Generation**: Automatic generation of type-safe, port-based components
3. **Port Architecture**: Components connected via typed anyio ports
4. **Observability**: Built-in metrics and health checking
5. **Testing**: Integration testing of the complete system
6. **Validation**: 80%+ success rate enabling deployment
7. **Monitoring**: Real-time metrics and observability

The generated system:
- Uses **anyio** exclusively for async operations
- Implements **Pydantic v2** for data validation
- Uses **monotonic time** for duration measurements
- Provides **atomic checkpointing** capability
- Tracks **buffer utilization** and **message age**
- Supports **Transformer arity 1→{0..1}** (can drop messages)

This represents a complete, production-ready system generated from a simple blueprint specification.