{"timestamp": "2025-08-25T06:06:17.290461", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T06:06:17.290606", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T06:06:17.290772", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T06:06:17.290903", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T06:06:17.291016", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T06:06:17.291151", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T06:06:17.291307", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T06:06:17.291383", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T06:06:17.291449", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T06:06:17.291496", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T06:06:17.291553", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T06:06:17.291617", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T06:06:17.291681", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T06:06:17.291747", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T06:06:17.291811", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T06:06:24.190253", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T06:06:24.190350", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T06:06:24.191739", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:06:24.193735", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T06:06:24.193873", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T06:06:24.193928", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T06:06:24.194007", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T06:06:24.194051", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T06:06:24.194104", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:06:24.194610", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:06:24.196720", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:06:24.690934", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T06:06:24.695410", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}

Testing: Create a simple data processor
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
  ✅ Has terminal component
  ✅ Has 1 bindings

Testing: Build an API service
LLM call attempt 1/6
   Fixed component type: 'APIEndpoint' → 'APIEndpoint'
   Fixed component type: 'Controller' → 'Controller'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
  ✅ Has terminal component
  ✅ Has 2 bindings

Testing: Make a data pipeline
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Transformer' → 'Transformer'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
  ✅ Has terminal component
  ✅ Has 2 bindings
