# Blueprint Examples for Port-Based Architecture

*Purpose: Complete working blueprint examples to validate the implementation*

## 1. Stateless Map Example

**File**: `examples/stateless_map.yaml`

```yaml
name: word_counter_system
version: 1.0.0
description: Stateless word counting system

components:
  - name: text_source
    recipe: Source
    config:
      source_type: file
      file_path: /tmp/input.txt
    outputs:
      - name: out_lines
        schema: TextLine
        
  - name: word_counter
    recipe: Transformer  # Stateless transformation
    config:
      stateless: true
    inputs:
      - name: in_lines
        schema: TextLine
    outputs:
      - name: out_counts
        schema: WordCount
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: result_sink
    recipe: Sink
    config:
      sink_type: console
    inputs:
      - name: in_counts
        schema: WordCount

connections:
  - from: text_source.out_lines
    to: word_counter.in_lines
  - from: word_counter.out_counts
    to: result_sink.in_counts

schemas:
  TextLine:
    type: object
    properties:
      line_number: integer
      text: string
      
  WordCount:
    type: object
    properties:
      line_number: integer
      word_count: integer
      unique_words: integer
```

## 2. Stateful Aggregation Example

**File**: `examples/stateful_aggregation.yaml`

```yaml
name: metrics_aggregator_system
version: 1.0.0
description: Aggregates metrics over time windows

components:
  - name: metrics_source
    recipe: Source
    config:
      source_type: http
      endpoint: /metrics
      poll_interval: 1
    outputs:
      - name: out_metrics
        schema: Metric
        
  - name: windowed_aggregator
    recipe: Aggregator  # Stateful - maintains window
    config:
      window_size: 60  # 1 minute windows
      aggregation_functions:
        - sum
        - avg
        - max
        - min
      stateful: true  # Maintains state across windows
    inputs:
      - name: in_metrics
        schema: Metric
    outputs:
      - name: out_aggregates
        schema: AggregatedMetric
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: metrics_store
    recipe: Store
    config:
      storage_backend: sqlite
      database: /var/lib/metrics.db
      checkpoint_enabled: true
    inputs:
      - name: in_aggregates
        schema: AggregatedMetric
    outputs:
      - name: out_responses
        schema: StoreResponse

connections:
  - from: metrics_source.out_metrics
    to: windowed_aggregator.in_metrics
  - from: windowed_aggregator.out_aggregates
    to: metrics_store.in_aggregates

schemas:
  Metric:
    type: object
    properties:
      timestamp: string  # ISO 8601
      name: string
      value: number
      tags:
        type: object
        
  AggregatedMetric:
    type: object
    properties:
      window_start: string
      window_end: string
      metric_name: string
      sum: number
      avg: number
      max: number
      min: number
      count: integer
      
  StoreResponse:
    type: object
    properties:
      success: boolean
      id: integer
      error: string
```

## 3. Idempotent Sink Example

**File**: `examples/idempotent_sink.yaml`

```yaml
name: payment_processor_system
version: 1.0.0
description: Idempotent payment processing

components:
  - name: payment_gateway
    recipe: APIEndpoint
    config:
      is_ingress: true  # Uses BLOCK_WITH_TIMEOUT
      endpoint: /payments
      method: POST
      rate_limit: 100
    outputs:
      - name: out_requests
        schema: PaymentRequest
        
  - name: idempotency_checker
    recipe: Transformer
    config:
      idempotent: true
      idempotency_key: transaction_id
      store_path: /var/lib/idempotency.db
    inputs:
      - name: in_requests
        schema: PaymentRequest
    outputs:
      - name: out_unique
        schema: PaymentRequest
      - name: out_duplicate
        schema: DuplicateResponse
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: payment_processor
    recipe: Transformer
    config:
      external_api: https://payment-provider.com
      timeout: 5000
    inputs:
      - name: in_payments
        schema: PaymentRequest
    outputs:
      - name: out_results
        schema: PaymentResult
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: result_store
    recipe: Sink  # Idempotent sink
    config:
      idempotent: true
      storage_backend: postgres
      connection_string: postgresql://user:pass@localhost/payments
      checkpoint_enabled: true
    inputs:
      - name: in_results
        schema: PaymentResult
      - name: in_duplicates
        schema: DuplicateResponse

connections:
  - from: payment_gateway.out_requests
    to: idempotency_checker.in_requests
  - from: idempotency_checker.out_unique
    to: payment_processor.in_payments
  - from: payment_processor.out_results
    to: result_store.in_results
  - from: idempotency_checker.out_duplicate
    to: result_store.in_duplicates

schemas:
  PaymentRequest:
    type: object
    required: [transaction_id, amount, currency]
    properties:
      transaction_id: string  # Idempotency key
      amount: number
      currency: string
      customer_id: string
      metadata: object
      
  PaymentResult:
    type: object
    properties:
      transaction_id: string
      status: string  # success|failed|pending
      provider_id: string
      processed_at: string
      
  DuplicateResponse:
    type: object
    properties:
      transaction_id: string
      original_result: object
      duplicate_count: integer
```

## 4. Complex Todo System Example

**File**: `examples/todo_system.yaml`

```yaml
name: todo_api_system
version: 1.0.0
description: Complete TODO API with port-based architecture

components:
  - name: api_gateway
    recipe: APIEndpoint
    config:
      is_ingress: true
      port: 8080
      endpoints:
        - path: /todos
          methods: [GET, POST, PUT, DELETE]
    outputs:
      - name: out_requests
        schema: HTTPRequest
        
  - name: request_validator
    recipe: Validator
    config:
      validation_rules:
        - required_fields: [title]
        - max_length: {title: 200, description: 1000}
    inputs:
      - name: in_requests
        schema: HTTPRequest
    outputs:
      - name: out_valid
        schema: TodoCommand
      - name: out_invalid
        schema: ValidationError
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: todo_controller
    recipe: Controller
    config:
      route_by: action
    inputs:
      - name: in_commands
        schema: TodoCommand
    outputs:
      - name: out_to_store
        schema: StoreCommand
      - name: out_to_cache
        schema: CacheCommand
      - name: out_responses
        schema: TodoResponse
        
  - name: todo_store
    recipe: Store
    config:
      storage_backend: sqlite
      database: /var/lib/todos.db
      checkpoint_enabled: true
      idempotent: true
    inputs:
      - name: in_commands
        schema: StoreCommand
    outputs:
      - name: out_results
        schema: StoreResult
      - name: err_errors
        schema: StandardErrorEnvelope
        
  - name: todo_cache
    recipe: Cache
    config:
      cache_type: memory
      ttl: 300  # 5 minutes
      max_size: 1000
    inputs:
      - name: in_commands
        schema: CacheCommand
    outputs:
      - name: out_data
        schema: CachedData
        
  - name: response_formatter
    recipe: Transformer
    config:
      format: json
    inputs:
      - name: in_responses
        schema: TodoResponse
      - name: in_errors
        schema: ValidationError
    outputs:
      - name: out_http
        schema: HTTPResponse

connections:
  - from: api_gateway.out_requests
    to: request_validator.in_requests
  - from: request_validator.out_valid
    to: todo_controller.in_commands
  - from: todo_controller.out_to_store
    to: todo_store.in_commands
  - from: todo_controller.out_to_cache
    to: todo_cache.in_commands
  - from: todo_store.out_results
    to: todo_controller.in_store_results
  - from: todo_cache.out_data
    to: todo_controller.in_cache_data
  - from: todo_controller.out_responses
    to: response_formatter.in_responses
  - from: request_validator.out_invalid
    to: response_formatter.in_errors
```

## Running the Examples

```bash
# Validate blueprint
python -m autocoder_cc.cli validate examples/stateless_map.yaml

# Generate components
python -m autocoder_cc.cli generate examples/stateless_map.yaml

# Run the system
python -m autocoder_cc.cli run examples/stateless_map.yaml

# Monitor metrics
python -m autocoder_cc.cli monitor examples/stateless_map.yaml

# Create checkpoint
python -m autocoder_cc.cli checkpoint stateless_map_system

# Restore from checkpoint
python -m autocoder_cc.cli restore stateless_map_system --checkpoint-id 123
```

## Testing Blueprint Components

```python
import pytest
from autocoder_cc.blueprint import BlueprintLoader
from autocoder_cc.generator import ComponentGenerator

@pytest.mark.asyncio
async def test_stateless_map_generation():
    """Test that stateless map blueprint generates valid components"""
    # Load blueprint
    blueprint = BlueprintLoader.load("examples/stateless_map.yaml")
    
    # Generate components
    generator = ComponentGenerator()
    components = await generator.generate(blueprint)
    
    # Verify each component
    assert len(components) == 3
    
    # Check word_counter is stateless
    word_counter = components["word_counter"]
    assert word_counter.config["stateless"] == True
    assert "in_lines" in word_counter.input_ports
    assert "out_counts" in word_counter.output_ports
    assert "err_errors" in word_counter.output_ports
```

---
*These blueprints demonstrate stateless, stateful, and idempotent patterns in the port-based architecture.*