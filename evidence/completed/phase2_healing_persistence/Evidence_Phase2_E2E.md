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
[32m19:17:02 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m19:17:02 - INFO - Session ID: autocoder_1756174622[0m
[32m19:17:02 - INFO - Log file: test_fixed_output/generation_verbose.log[0m
[32m19:17:02 - INFO - Structured log: test_fixed_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
INFO:system_generator:SystemGenerator initialized with observability stack
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: event_source.output → event_store.input
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
INFO:port_auto_generator:Starting port auto-generation
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
INFO:port_auto_generator:Starting port auto-generation
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 3/4
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 3
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 3 attempts
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
INFO:port_auto_generator:Starting port auto-generation
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 4/4
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 4
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 4 attempts
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
ERROR:autocoder_cc.healing.blueprint_healer:Maximum stagnation count reached - stopping healing to prevent infinite loops
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
INFO:port_auto_generator:Starting port auto-generation
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
