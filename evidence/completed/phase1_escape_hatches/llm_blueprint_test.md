{"timestamp": "2025-08-25T12:03:08.699941", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T12:03:08.700074", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T12:03:08.700153", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T12:03:08.700217", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T12:03:08.700279", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T12:03:08.700341", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T12:03:08.700399", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T12:03:08.700465", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T12:03:08.700522", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T12:03:08.700578", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T12:03:08.700634", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T12:03:08.700691", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T12:03:08.700747", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T12:03:08.700802", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T12:03:08.700857", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T12:03:15.304456", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T12:03:15.304550", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T12:03:15.305793", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:03:15.307612", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T12:03:15.307696", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T12:03:15.307755", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T12:03:15.307821", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T12:03:15.307862", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T12:03:15.307912", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:03:15.308368", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:03:15.310340", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:03:15.614277", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T12:03:15.616372", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
=== LLM GENERATED BLUEPRINT ===
schema_version: "1.0.0"

system:
  name: event_processing_system
  description: A system that receives events from a source and stores them for further processing.
  version: 1.0.0
  components:
  - name: event_source
    type: Source
    description: Generates events for processing.
    processing_mode: stream
    inputs: []
    outputs:
    - name: output
      schema: common_object_schema
      required: true
      description: The event data output.
      flow_type: push
      batch_size: 1
    properties: []
    contracts: []
    configuration: {}
    dependencies: []
    implementation:
      language: python
      methods: {}
  - name: event_store
    type: Store
    description: Stores the received events.
    processing_mode: batch
    inputs:
    - name: data
      schema: common_object_schema
      required: true
      description: Input for storing event data.
      flow_type: push
      batch_size: 1
    outputs: []
    properties: []
    contracts: []
    configuration:
 

=== BINDINGS IN LLM OUTPUT ===
Number of bindings: 1

Binding 0:
  from: event_source.output
  to: event_store.data
  transformation: NONE
  description: none

=== COMPONENT SCHEMAS ===

event_source (Source):
  output 'output': common_object_schema

event_store (Store):
  input 'data': common_object_schema
