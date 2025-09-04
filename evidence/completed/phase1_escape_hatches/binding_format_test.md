{"timestamp": "2025-08-25T11:57:13.260274", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T11:57:13.260517", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T11:57:13.260584", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T11:57:13.260653", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T11:57:13.260718", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T11:57:13.260764", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T11:57:13.260868", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T11:57:13.260945", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T11:57:13.261007", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T11:57:13.261067", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T11:57:13.261125", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T11:57:13.261184", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T11:57:13.261242", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T11:57:13.261297", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T11:57:13.261354", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T11:57:22.313333", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T11:57:22.313432", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T11:57:22.314977", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:22.317100", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T11:57:22.317197", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T11:57:22.317287", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T11:57:22.317354", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T11:57:22.317413", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T11:57:22.317479", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:22.317990", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:22.321018", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:57:22.405234", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
{"timestamp": "2025-08-25T11:57:22.405333", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
{"timestamp": "2025-08-25T11:57:22.405393", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
{"timestamp": "2025-08-25T11:57:22.405455", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
{"timestamp": "2025-08-25T11:57:22.405539", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
{"timestamp": "2025-08-25T11:57:22.405598", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Added transformation to handle schema mismatch: common_object_schema -> ItemSchema"}
{"timestamp": "2025-08-25T11:57:22.405653", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
{"timestamp": "2025-08-25T11:57:22.405712", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Added transformation to handle schema mismatch: common_object_schema -> ItemSchema"}
{"timestamp": "2025-08-25T11:57:22.405753", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Applied 2 schema compatibility fixes"}
{"timestamp": "2025-08-25T11:57:22.405816", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 2 operations: Added missing policy block, Generated 1 missing bindings"}
Original binding:
description: Test binding
from_component: event_source
from_port: output
to_components:
- event_store
to_ports:
- input


Healed binding:
_uses_alt_format: true
description: Test binding
from_component: event_source
from_port: output
to_components:
- event_store
to_ports:
- input
transformation: convert_common_object_schema_to_ItemSchema


✅ Transformation added: convert_common_object_schema_to_ItemSchema

Binding format uses:
  - from_component/to_components format
  - _uses_alt_format flag: True
