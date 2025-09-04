{"timestamp": "2025-08-25T10:58:29.530822", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T10:58:29.530944", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T10:58:29.531020", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T10:58:29.531084", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T10:58:29.531145", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T10:58:29.531206", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T10:58:29.531263", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T10:58:29.531319", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T10:58:29.531376", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T10:58:29.531438", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T10:58:29.531494", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T10:58:29.531551", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T10:58:29.531607", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T10:58:29.531661", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T10:58:29.531716", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T10:58:36.363765", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T10:58:36.363855", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T10:58:36.365186", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:58:36.367030", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T10:58:36.367121", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T10:58:36.367190", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T10:58:36.367254", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T10:58:36.367311", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T10:58:36.367366", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:58:36.367828", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:58:36.369810", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:58:36.676779", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T10:58:36.678385", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
============================================================
TESTING SIMPLE SYSTEM GENERATION - STUB PREVENTION
============================================================

1. Generating system: 'Create a simple event logger that receives events and stores them'
🤖 Translating natural language to blueprint...
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: event_logger_system
  description: A simple event logger that receives events and stores them.
  version: 1.0.0
  components:
  - name: event_source
    type: ...

🔧 Generating system components...
[32m10:58:43 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m10:58:43 - INFO - Session ID: autocoder_1756144723[0m
[32m10:58:43 - INFO - Log file: test_simple_output/generation_verbose.log[0m
[32m10:58:43 - INFO - Structured log: test_simple_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:58:43.749871", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:58:43.756737", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:58:43.757143", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T10:58:43.757236", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:58:43.758191", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:58:43.758381", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:58:43.765066", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:58:43.765224", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:58:43.771000", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T10:58:43.771158", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_simple_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T10:58:43.771242", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T10:58:43.771324", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T10:58:43.772157", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_simple_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-25T10:58:43.772446", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-25T10:58:43.777649", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T10:58:43.777730", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:58:43.777800", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T10:58:43.777874", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: event_source.output → event_store.input
{"timestamp": "2025-08-25T10:58:43.777947", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-25T10:58:43.778064", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
{"timestamp": "2025-08-25T10:58:43.778229", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:58:43.778377", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:58:43.778488", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:58:43.779207", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:58:43.779294", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:58:43.779382", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 2/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
{"timestamp": "2025-08-25T10:58:43.779466", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 2"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
{"timestamp": "2025-08-25T10:58:43.779543", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:58:43.779621", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T10:58:43.779700", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:58:43.779797", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:58:43.779887", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:58:43.780022", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:58:43.780123", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:58:43.780378", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:58:43.780466", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:58:43.780548", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 3/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 3/4
{"timestamp": "2025-08-25T10:58:43.780622", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 3"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 3
{"timestamp": "2025-08-25T10:58:43.780695", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:58:43.780770", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T10:58:43.780846", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:58:43.780950", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 3 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 3 attempts
{"timestamp": "2025-08-25T10:58:43.781023", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T10:58:43.781095", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:58:43.781173", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:58:43.781293", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:58:43.781395", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T10:58:43.781649", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T10:58:43.781728", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T10:58:43.781807", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 4/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 4/4
{"timestamp": "2025-08-25T10:58:43.781880", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 4
{"timestamp": "2025-08-25T10:58:43.781951", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:58:43.782027", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-25T10:58:43.782103", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-25T10:58:43.782205", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 4 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 4 attempts
{"timestamp": "2025-08-25T10:58:43.782284", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-25T10:58:43.782360", "level": "ERROR", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Maximum stagnation count reached - stopping healing to prevent infinite loops"}
ERROR:autocoder_cc.healing.blueprint_healer:Maximum stagnation count reached - stopping healing to prevent infinite loops
{"timestamp": "2025-08-25T10:58:43.782432", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T10:58:43.782511", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:58:43.782626", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:58:43.782720", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
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

============================================================
❌ STUB PREVENTION TEST FAILED
============================================================
