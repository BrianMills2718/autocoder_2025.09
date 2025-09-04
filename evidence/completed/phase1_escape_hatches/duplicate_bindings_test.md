{"timestamp": "2025-08-25T11:57:53.297311", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T11:57:53.297447", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T11:57:53.297508", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T11:57:53.297570", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T11:57:53.297616", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T11:57:53.297672", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T11:57:53.297714", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T11:57:53.297766", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T11:57:53.297823", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T11:57:53.297862", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T11:57:53.297912", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T11:57:53.297968", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T11:57:53.298008", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T11:57:53.298056", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T11:57:53.298110", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T11:57:59.957716", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T11:57:59.957809", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T11:57:59.959035", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:59.960888", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T11:57:59.960969", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T11:57:59.961020", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T11:57:59.961086", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T11:57:59.961126", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T11:57:59.961177", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:59.961660", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:59.963629", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:58:00.009063", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
{"timestamp": "2025-08-25T11:58:00.009194", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
{"timestamp": "2025-08-25T11:58:00.009284", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
{"timestamp": "2025-08-25T11:58:00.009353", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
{"timestamp": "2025-08-25T11:58:00.009454", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
{"timestamp": "2025-08-25T11:58:00.009518", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Added transformation to handle schema mismatch: common_object_schema -> ItemSchema"}
{"timestamp": "2025-08-25T11:58:00.009590", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
{"timestamp": "2025-08-25T11:58:00.009653", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Added transformation to handle schema mismatch: common_object_schema -> ItemSchema"}
{"timestamp": "2025-08-25T11:58:00.009711", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Applied 2 schema compatibility fixes"}
{"timestamp": "2025-08-25T11:58:00.009771", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 2 operations: Added missing policy block, Generated 1 missing bindings"}
Original bindings count: 1
  Binding 0: Original binding

Healed bindings count: 2
  Binding 0: Original binding | transformation: convert_common_object_schema_to_ItemSchema
  Binding 1: Auto-generated: event_source data flow to event_store | transformation: convert_common_object_schema_to_ItemSchema
