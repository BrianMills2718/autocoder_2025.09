{"timestamp": "2025-08-26T08:09:44.657926", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-26T08:09:44.658076", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-26T08:09:44.658163", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-26T08:09:44.658232", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-26T08:09:44.658308", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-26T08:09:44.658379", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-26T08:09:44.658442", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-26T08:09:44.658514", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-26T08:09:44.658559", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-26T08:09:44.658614", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-26T08:09:44.658680", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-26T08:09:44.658741", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-26T08:09:44.658802", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-26T08:09:44.658859", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-26T08:09:44.658919", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-26T08:09:51.478335", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-26T08:09:51.478444", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-26T08:09:51.479885", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-26T08:09:51.481989", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-26T08:09:51.482091", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-26T08:09:51.482167", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-26T08:09:51.482237", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-26T08:09:51.482299", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-26T08:09:51.482359", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-26T08:09:51.482937", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-26T08:09:51.485158", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
============================================================
INTEGRATION TEST: Full System Escape Hatch Verification
============================================================

Running: Generated systems have no stubs
[32m08:09:51 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m08:09:51 - INFO - Session ID: autocoder_1756220991[0m
[32m08:09:51 - INFO - Log file: /tmp/tmpvk0a4web/generated_system/generation_verbose.log[0m
[32m08:09:51 - INFO - Structured log: /tmp/tmpvk0a4web/generated_system/generation_verbose.json[0m
{"timestamp": "2025-08-26T08:09:51.580603", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-26T08:09:51.593551", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.603265", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.604401", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-26T08:09:51.604517", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.605582", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.605763", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.613186", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.613381", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-26T08:09:51.620181", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-26T08:09:51.620359", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "/tmp/tmpvk0a4web/generated_system/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-26T08:09:51.620450", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-26T08:09:51.620536", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-26T08:09:51.621339", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "/tmp/tmpvk0a4web/generated_system", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
❌ FAILED: Generated systems have no stubs
   Error: 'SystemGenerator' object has no attribute 'generate_from_blueprint'

Running: Validation cannot be bypassed
[32m08:09:51 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
INFO:VerboseAutocoder:🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED
[32m08:09:51 - INFO - Session ID: autocoder_1756220991[0m
INFO:VerboseAutocoder:Session ID: autocoder_1756220991
[32m08:09:51 - INFO - Log file: /tmp/tmpqcvldtjx/generated_system/generation_verbose.log[0m
INFO:VerboseAutocoder:Log file: /tmp/tmpqcvldtjx/generated_system/generation_verbose.log
[32m08:09:51 - INFO - Structured log: /tmp/tmpqcvldtjx/generated_system/generation_verbose.json[0m
INFO:VerboseAutocoder:Structured log: /tmp/tmpqcvldtjx/generated_system/generation_verbose.json
{"timestamp": "2025-08-26T08:09:51.623321", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.624370", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.624544", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-26T08:09:51.624623", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.625568", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.625734", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T08:09:51.626700", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T08:09:51.626863", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-26T08:09:51.626951", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-26T08:09:51.627059", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "/tmp/tmpqcvldtjx/generated_system/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-26T08:09:51.627134", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-26T08:09:51.627220", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-26T08:09:51.627599", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "/tmp/tmpqcvldtjx/generated_system", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
❌ FAILED: Validation cannot be bypassed
   Error: SystemGenerator should have healing_system

Running: Circuit breakers not active
❌ FAILED: Circuit breakers not active
   Error: 'PosixPath' object has no attribute 'get'

Running: Error codes properly used
✅ Proper error codes used for failures

Running: No mock dependencies in production
✅ Mock dependencies properly isolated in tests/mocks/
✅ No mock dependencies in production code

Running: LLM fallback disabled
✅ LLM fallback disabled by default

Running: Recipes force implementation
✅ Recipe 'Store' correctly forces LLM implementation

Running: Async validation always runs
❌ FAILED: Async validation always runs
   Error: SelfHealingSystem.__init__() got an unexpected keyword argument 'output_dir'

============================================================
INTEGRATION TEST RESULTS
============================================================
✅ Passed: 4/8
❌ Failed: 4/8

Failed tests:
  - Generated systems have no stubs: 'SystemGenerator' object has no attribute 'generate_from_blueprint'
  - Validation cannot be bypassed: SystemGenerator should have healing_system
  - Circuit breakers not active: 'PosixPath' object has no attribute 'get'
  - Async validation always runs: SelfHealingSystem.__init__() got an unexpected keyword argument 'output_dir'
