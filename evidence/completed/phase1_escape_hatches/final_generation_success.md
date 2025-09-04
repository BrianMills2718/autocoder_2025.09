{"timestamp": "2025-08-25T12:00:05.608314", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T12:00:05.608464", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T12:00:05.608525", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T12:00:05.608586", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T12:00:05.608647", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T12:00:05.608708", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T12:00:05.608771", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T12:00:05.608828", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T12:00:05.608910", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T12:00:05.608983", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T12:00:05.609040", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T12:00:05.609097", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T12:00:05.609154", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T12:00:05.609208", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T12:00:05.609264", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T12:00:12.446125", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T12:00:12.446223", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T12:00:12.447520", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:00:12.449655", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T12:00:12.449757", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T12:00:12.449811", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T12:00:12.449875", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T12:00:12.449919", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T12:00:12.449972", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:00:12.450499", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:00:12.452633", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T12:00:12.775843", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T12:00:12.780122", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
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
  description: A system that receives events from a source and stores them for further processing.
  version: 1.0.0
  components:
  - n...

🔧 Generating system components...
[32m12:00:21 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m12:00:21 - INFO - Session ID: autocoder_1756148421[0m
[32m12:00:21 - INFO - Log file: test_fixed_output/generation_verbose.log[0m
[32m12:00:21 - INFO - Structured log: test_fixed_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T12:00:21.177818", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:00:21.185076", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:00:21.185548", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T12:00:21.185632", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:00:21.186537", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:00:21.186705", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T12:00:21.193650", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T12:00:21.193829", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T12:00:21.199793", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T12:00:21.199944", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T12:00:21.200022", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T12:00:21.200085", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T12:00:21.201009", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_final_system_fixed.py", line 28, in test_final_system
    result = await generate_system_from_description(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/natural_language_to_blueprint.py", line 1178, in generate_system_from_description
    generated_system = asyncio.run(run_generation())
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 190, in run
    raise RuntimeError(
RuntimeError: asyncio.run() cannot be called from a running event loop
/home/brian/projects/autocoder4_cc/test_final_system_fixed.py:105: RuntimeWarning: coroutine 'generate_system_from_description.<locals>.run_generation' was never awaited
  return False
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found

❌ Generation error: asyncio.run() cannot be called from a running event loop
