{"timestamp": "2025-08-25T11:03:17.608360", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T11:03:17.608495", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T11:03:17.608581", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T11:03:17.608652", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T11:03:17.608700", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T11:03:17.608760", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T11:03:17.608805", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T11:03:17.608859", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T11:03:17.608902", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T11:03:17.608955", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T11:03:17.608998", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T11:03:17.609051", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T11:03:17.609095", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T11:03:17.609146", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T11:03:17.609189", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T11:03:24.364732", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T11:03:24.364830", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T11:03:24.366226", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:03:24.368179", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T11:03:24.368265", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T11:03:24.368337", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T11:03:24.368407", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T11:03:24.368468", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T11:03:24.368527", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:03:24.369032", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:03:24.371087", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:03:24.419299", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T11:03:24.419418", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T11:03:24.419488", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: event_source.output → event_store.input
{"timestamp": "2025-08-25T11:03:24.419560", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-25T11:03:24.419651", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
INFO:autocoder_cc.healing.blueprint_healer:Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)
{"timestamp": "2025-08-25T11:03:24.419728", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Auto-fixed schema: event_store.input changed to any"}
INFO:autocoder_cc.healing.blueprint_healer:Auto-fixed schema: event_store.input changed to any
{"timestamp": "2025-08-25T11:03:24.419789", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Applied 1 schema compatibility fixes"}
INFO:autocoder_cc.healing.blueprint_healer:Applied 1 schema compatibility fixes
{"timestamp": "2025-08-25T11:03:24.419861", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 2 operations: Added missing policy block, Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 2 operations: Added missing policy block, Generated 1 missing bindings
Testing blueprint healer with schema mismatch...
Original binding: {'from_component': 'event_source', 'from_port': 'output', 'to_components': ['event_store'], 'to_ports': ['input'], 'description': 'Auto-generated: event_source data flow to event_store'}
Healed binding: {'from_component': 'event_source', 'from_port': 'output', 'to_components': ['event_store'], 'to_ports': ['input'], 'description': 'Auto-generated: event_source data flow to event_store', '_uses_alt_format': True}
❌ FAILED: No transformation added for schema mismatch
DEBUG:asyncio:Using selector: EpollSelector
