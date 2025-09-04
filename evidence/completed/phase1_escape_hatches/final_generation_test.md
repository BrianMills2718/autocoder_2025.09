{"timestamp": "2025-08-25T10:54:10.146789", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T10:54:10.146935", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T10:54:10.147002", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T10:54:10.147066", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T10:54:10.147132", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T10:54:10.147215", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T10:54:10.147278", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T10:54:10.147322", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T10:54:10.147376", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T10:54:10.147418", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T10:54:10.147472", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T10:54:10.147514", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T10:54:10.147569", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T10:54:10.147609", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T10:54:10.147662", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T10:54:21.972716", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T10:54:21.972814", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T10:54:21.974163", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:54:21.978295", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T10:54:21.978373", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T10:54:21.978440", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T10:54:21.978504", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T10:54:21.978561", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T10:54:21.978615", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:54:21.979124", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:54:21.981080", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:54:22.296313", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
{"timestamp": "2025-08-25T10:54:22.296700", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
============================================================
TESTING COMPLETE SYSTEM GENERATION WITH ALL FIXES
============================================================

1. Generating system from natural language...
   Description: 'Create a data processing pipeline that reads data from a source, transforms it, and stores it'
🤖 Translating natural language to blueprint...
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Transformer' → 'Transformer'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: data_processing_pipeline
  description: A data processing pipeline that reads data from a source, transforms it, and stores it.
  version: 1.0.0
  components:
...

🔧 Generating system components...
[32m10:54:32 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m10:54:32 - INFO - Session ID: autocoder_1756144472[0m
[32m10:54:32 - INFO - Log file: test_final_system/generation_verbose.log[0m
[32m10:54:32 - INFO - Structured log: test_final_system/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:54:32.327462", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:54:32.334836", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:54:32.335303", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T10:54:32.335386", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:54:32.336300", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:54:32.336464", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:54:32.343561", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:54:32.343741", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:54:32.350248", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T10:54:32.350466", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_final_system/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T10:54:32.350548", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T10:54:32.350645", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T10:54:32.351504", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_final_system", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-25T10:54:32.351833", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-25T10:54:32.358692", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T10:54:32.358822", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:54:32.358909", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T10:54:32.359009", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: data_transformer.output → data_store.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: data_transformer.output → data_store.input
{"timestamp": "2025-08-25T10:54:32.359085", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-25T10:54:32.359220", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
{"timestamp": "2025-08-25T10:54:32.359457", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:54:32.359648", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:54:32.359760", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: data_processing_pipeline
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:54:32.360663", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:54:32.360745", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:54:32.360830", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 2/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
{"timestamp": "2025-08-25T10:54:32.360899", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 2"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
{"timestamp": "2025-08-25T10:54:32.360992", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:54:32.361068", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T10:54:32.361140", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:54:32.361237", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:54:32.361316", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:54:32.361465", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:54:32.361563", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: data_processing_pipeline
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:54:32.361844", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:54:32.361947", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:54:32.362020", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 3/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 3/4
{"timestamp": "2025-08-25T10:54:32.362085", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 3"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 3
{"timestamp": "2025-08-25T10:54:32.362148", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:54:32.362213", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T10:54:32.362281", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:54:32.362387", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 3 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 3 attempts
{"timestamp": "2025-08-25T10:54:32.362450", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T10:54:32.362512", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:54:32.362581", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:54:32.362702", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:54:32.362790", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: data_processing_pipeline
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:54:32.363054", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:54:32.363126", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:54:32.363195", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 4/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 4/4
{"timestamp": "2025-08-25T10:54:32.363258", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 4
{"timestamp": "2025-08-25T10:54:32.363321", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:54:32.363385", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T10:54:32.363452", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:54:32.363554", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 4 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 4 attempts
{"timestamp": "2025-08-25T10:54:32.363617", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T10:54:32.363682", "level": "ERROR", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Maximum stagnation count reached - stopping healing to prevent infinite loops"}
ERROR:autocoder_cc.healing.blueprint_healer:Maximum stagnation count reached - stopping healing to prevent infinite loops
{"timestamp": "2025-08-25T10:54:32.363743", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:54:32.363823", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:54:32.363942", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:54:32.364030", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: data_processing_pipeline
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_final_generation.py", line 26, in test_system_generation
    result = generate_system_from_description(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/natural_language_to_blueprint.py", line 1178, in generate_system_from_description
    generated_system = asyncio.run(run_generation())
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/natural_language_to_blueprint.py", line 1176, in run_generation
    return await generator.generate_system_from_yaml(blueprint_yaml)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 230, in generate_system_from_yaml
    system_blueprint = parser.parse_string(blueprint_yaml)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_blueprint_parser.py", line 169, in parse_string
    raise ValueError(error_summary)
ValueError: System blueprint validation failed after 4 attempts with 1 errors
  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
🔍 DEBUG VALIDATION - Component role analysis:
  data_source: Source → SOURCE → SOURCE (in=0, out=1)
  data_transformer: Transformer → TRANSFORMER → TRANSFORMER (in=1, out=1)
  data_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'data_source'}
🔍 DEBUG VALIDATION - Sinks: {'data_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  data_source: Source → SOURCE → SOURCE (in=0, out=1)
  data_transformer: Transformer → TRANSFORMER → TRANSFORMER (in=1, out=1)
  data_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'data_source'}
🔍 DEBUG VALIDATION - Sinks: {'data_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  data_source: Source → SOURCE → SOURCE (in=0, out=1)
  data_transformer: Transformer → TRANSFORMER → TRANSFORMER (in=1, out=1)
  data_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'data_source'}
🔍 DEBUG VALIDATION - Sinks: {'data_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  data_source: Source → SOURCE → SOURCE (in=0, out=1)
  data_transformer: Transformer → TRANSFORMER → TRANSFORMER (in=1, out=1)
  data_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'data_source'}
🔍 DEBUG VALIDATION - Sinks: {'data_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True

❌ Generation failed: System blueprint validation failed after 4 attempts with 1 errors
  binding.schema_compatibility: Schema mismatch without transformation: data_transformer.output (common_object_schema) → data_store.input (ItemSchema)

============================================================
❌ TEST FAILED: Issues found in generated system
============================================================
