{"timestamp": "2025-08-25T12:01:05.816798", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T12:01:05.816940", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T12:01:05.817024", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T12:01:05.817134", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T12:01:05.817224", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T12:01:05.817307", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T12:01:05.817376", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T12:01:05.817441", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T12:01:05.817503", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T12:01:05.817565", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T12:01:05.817636", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T12:01:05.817697", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T12:01:05.817792", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T12:01:05.817861", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T12:01:05.817924", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T12:01:12.715051", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T12:01:12.715153", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T12:01:12.716456", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:01:12.718434", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T12:01:12.718531", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T12:01:12.718601", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T12:01:12.718675", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T12:01:12.718733", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T12:01:12.718790", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:01:12.719298", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:01:12.721467", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:01:13.032642", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T12:01:13.035420", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
🔬 Testing complete system generation with healer fix...
------------------------------------------------------------
🤖 Translating natural language to blueprint...
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: event_processing_system
  description: A system that receives events from a source and stores them in a data store.
  version: 1.0.0
  components:
  - name: ev...

🔧 Generating system components...
[32m12:01:21 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m12:01:21 - INFO - Session ID: autocoder_1756148481[0m
[32m12:01:21 - INFO - Log file: test_fixed_output/generation_verbose.log[0m
[32m12:01:21 - INFO - Structured log: test_fixed_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T12:01:21.572796", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:01:21.580264", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:01:21.580729", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T12:01:21.580816", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:01:21.581712", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:01:21.581879", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:01:21.589287", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:01:21.589503", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T12:01:21.595920", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T12:01:21.596094", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T12:01:21.596174", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T12:01:21.596238", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T12:01:21.597080", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-25T12:01:21.597402", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-25T12:01:21.602798", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T12:01:21.602923", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T12:01:21.603005", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T12:01:21.603089", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: event_source.output → event_store.input
{"timestamp": "2025-08-25T12:01:21.603165", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-25T12:01:21.603280", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
{"timestamp": "2025-08-25T12:01:21.603535", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T12:01:21.603736", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T12:01:21.603841", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T12:01:21.604630", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T12:01:21.604709", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T12:01:21.604785", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 2/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
{"timestamp": "2025-08-25T12:01:21.604864", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 2"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
{"timestamp": "2025-08-25T12:01:21.604936", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T12:01:21.605004", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T12:01:21.605075", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T12:01:21.605176", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T12:01:21.605253", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T12:01:21.605375", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T12:01:21.605466", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T12:01:21.605711", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T12:01:21.605790", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T12:01:21.605861", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 3/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 3/4
{"timestamp": "2025-08-25T12:01:21.605925", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 3"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 3
{"timestamp": "2025-08-25T12:01:21.605987", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T12:01:21.606052", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T12:01:21.606123", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T12:01:21.606201", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 3 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 3 attempts
{"timestamp": "2025-08-25T12:01:21.606261", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T12:01:21.606323", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T12:01:21.606394", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T12:01:21.606506", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T12:01:21.606590", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T12:01:21.606828", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T12:01:21.606898", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T12:01:21.606967", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 4/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 4/4
{"timestamp": "2025-08-25T12:01:21.607038", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 4
{"timestamp": "2025-08-25T12:01:21.607101", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T12:01:21.607172", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T12:01:21.607241", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T12:01:21.607348", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 4 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 4 attempts
{"timestamp": "2025-08-25T12:01:21.607412", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T12:01:21.607477", "level": "ERROR", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Maximum stagnation count reached - stopping healing to prevent infinite loops"}
ERROR:autocoder_cc.healing.blueprint_healer:Maximum stagnation count reached - stopping healing to prevent infinite loops
{"timestamp": "2025-08-25T12:01:21.607540", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T12:01:21.607608", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T12:01:21.607727", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T12:01:21.607810", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_final_system_fixed.py", line 27, in test_final_system
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
  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
🔍 DEBUG VALIDATION - Component role analysis:
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'event_source'}
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'event_source'}
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'event_source'}
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
🔍 DEBUG VALIDATION - Component role analysis:
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'event_source'}
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True

❌ Generation error: System blueprint validation failed after 4 attempts with 1 errors
  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
