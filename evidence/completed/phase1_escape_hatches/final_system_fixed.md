{"timestamp": "2025-08-25T11:59:36.339416", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T11:59:36.339545", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T11:59:36.339623", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T11:59:36.339687", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T11:59:36.339734", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T11:59:36.339790", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T11:59:36.339848", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T11:59:36.339905", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T11:59:36.339946", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T11:59:36.339997", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T11:59:36.340037", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T11:59:36.340088", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T11:59:36.340129", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T11:59:36.340177", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T11:59:36.340241", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T11:59:43.251324", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T11:59:43.251434", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T11:59:43.252860", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:59:43.254883", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T11:59:43.254974", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T11:59:43.255027", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T11:59:43.255093", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T11:59:43.255152", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T11:59:43.255192", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:59:43.255750", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T11:59:43.257928", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_final_system_fixed.py", line 28, in test_final_system
    result = await generate_system_from_description(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: generate_system_from_description() got an unexpected keyword argument 'bypass_validation'
🔬 Testing complete system generation with healer fix...
------------------------------------------------------------

❌ Generation error: generate_system_from_description() got an unexpected keyword argument 'bypass_validation'
