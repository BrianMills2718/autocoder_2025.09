{"timestamp": "2025-08-25T10:28:53.994050", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T10:28:53.994186", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T10:28:53.994271", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T10:28:53.994338", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T10:28:53.994402", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T10:28:53.994465", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T10:28:53.994525", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T10:28:53.994585", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T10:28:53.994644", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T10:28:53.994702", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T10:28:53.994760", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T10:28:53.994818", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T10:28:53.994887", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T10:28:53.994943", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T10:28:53.995001", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T10:29:03.815824", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T10:29:03.815925", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T10:29:03.817231", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:29:03.819199", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T10:29:03.819290", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T10:29:03.819344", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T10:29:03.819499", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T10:29:03.819575", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T10:29:03.819638", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:29:03.820182", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:29:03.822340", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T10:29:04.352787", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T10:29:04.355101", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
🤖 Translating natural language to blueprint...
LLM call attempt 1/6
   Fixed component type: 'APIEndpoint' → 'APIEndpoint'
   Fixed component type: 'Controller' → 'Controller'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: user_data_api_system
  description: A REST API system that handles user data storage and management.
  version: 1.0.0
  components:
  - name: user_api_endpoint...

🔧 Generating system components...
[32m10:29:19 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m10:29:19 - INFO - Session ID: autocoder_1756142959[0m
[32m10:29:19 - INFO - Log file: test_e2e_output/generation_verbose.log[0m
[32m10:29:19 - INFO - Structured log: test_e2e_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:29:19.017066", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:29:19.024148", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:29:19.024579", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T10:29:19.024662", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:29:19.025573", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:29:19.025745", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback DISABLED - will only use gemini_2_5_flash (fail fast on error)
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T10:29:19.032861", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T10:29:19.033045", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T10:29:19.039470", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T10:29:19.039643", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_e2e_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T10:29:19.039724", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T10:29:19.039813", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T10:29:19.040408", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_e2e_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-25T10:29:19.040813", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-25T10:29:19.048270", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T10:29:19.048396", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T10:29:19.048459", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T10:29:19.048594", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_api_endpoint.request → user_data_store.query"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_api_endpoint.request → user_data_store.query
{"timestamp": "2025-08-25T10:29:19.048667", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_data_store.response → user_api_endpoint.data"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_data_store.response → user_api_endpoint.data
{"timestamp": "2025-08-25T10:29:19.048742", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_api_endpoint.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_api_endpoint.control
{"timestamp": "2025-08-25T10:29:19.048811", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_data_store.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_data_store.control
{"timestamp": "2025-08-25T10:29:19.048876", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 4 missing bindings
{"timestamp": "2025-08-25T10:29:19.049018", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 4 missing bindings
{"timestamp": "2025-08-25T10:29:19.049246", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T10:29:19.049464", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T10:29:19.049595", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 3}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: user_data_api_system
WARNING:autocoder_cc.blueprint_language.architectural_validator:role_delta name=user_api_endpoint declared=SINK effective=TRANSFORMER reasons=['declared=SINK', 'outputs present (R1)']
INFO:autocoder_cc.blueprint_language.architectural_validator:Detected API-based architecture pattern - relaxed source validation
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
🔍 DEBUG VALIDATION - Component role analysis:
  user_api_endpoint: APIEndpoint → SINK → TRANSFORMER (in=2, out=2)
  user_controller: Controller → TRANSFORMER → TRANSFORMER (in=1, out=2)
  user_data_store: Store → SINK → SINK (in=2, out=1)
🔍 DEBUG VALIDATION - Sources: set()
🔍 DEBUG VALIDATION - Sinks: {'user_data_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=True
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
[32m10:29:19 - INFO - ▶️  Generate System: user_data_api_system[0m
INFO:VerboseAutocoder:▶️  Generate System: user_data_api_system
DEBUG:VerboseAutocoder:   📋 system_name: user_data_api_system
DEBUG:VerboseAutocoder:   📋 component_count: 3
DEBUG:VerboseAutocoder:   📋 binding_count: 6
[32m10:29:19 - INFO - 🚀 Generating system: user_data_api_system[0m
INFO:VerboseAutocoder:🚀 Generating system: user_data_api_system
[32m10:29:19 - INFO - 📋 Blueprint details:[0m
INFO:VerboseAutocoder:📋 Blueprint details:
[32m10:29:19 - INFO -    - Components: 3[0m
INFO:VerboseAutocoder:   - Components: 3
[32m10:29:19 - INFO -    - Bindings: 6[0m
INFO:VerboseAutocoder:   - Bindings: 6
[32m10:29:19 - INFO -    - Version: 1.0.0[0m
INFO:VerboseAutocoder:   - Version: 1.0.0
[32m10:29:19 - INFO -   ▶️  Pre-Generation Validation[0m
INFO:VerboseAutocoder:  ▶️  Pre-Generation Validation
{"timestamp": "2025-08-25T10:29:19.053015", "level": "INFO", "logger_name": "ValidationOrchestrator", "message": "✅ Pre-generation validation passed"}
INFO:ValidationOrchestrator:✅ Pre-generation validation passed
[32m10:29:19 - INFO -     ✅ pre_generation: PASSED[0m
INFO:VerboseAutocoder:    ✅ pre_generation: PASSED
DEBUG:VerboseAutocoder:       📊 success: True
[31m10:29:19 - ERROR -        🚨 Errors (0):[0m
ERROR:VerboseAutocoder:       🚨 Errors (0):
DEBUG:VerboseAutocoder:       📊 total_errors: 0
[32m10:29:19 - INFO -   ✅ Pre-Generation Validation (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Pre-Generation Validation (⏱️ 0.00s)
[32m10:29:19 - INFO -   ▶️  Allocate System Ports[0m
INFO:VerboseAutocoder:  ▶️  Allocate System Ports
{"timestamp": "2025-08-25T10:29:19.053633", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "PortRegistry initialized: range 8000-65535, reserved 10 ports"}
INFO:autocoder_cc.core.port_registry:PortRegistry initialized: range 8000-65535, reserved 10 ports
{"timestamp": "2025-08-25T10:29:19.053709", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Global PortRegistry instance created"}
INFO:autocoder_cc.core.port_registry:Global PortRegistry instance created
{"timestamp": "2025-08-25T10:29:19.053789", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Allocated port 8613 for user_api_endpoint (APIEndpoint)"}
INFO:autocoder_cc.core.port_registry:Allocated port 8613 for user_api_endpoint (APIEndpoint)
[32m10:29:19 - INFO - 🔌 Allocated port 8613 for user_api_endpoint[0m
INFO:VerboseAutocoder:🔌 Allocated port 8613 for user_api_endpoint
[32m10:29:19 - INFO - ✅ Allocated 1 ports successfully[0m
INFO:VerboseAutocoder:✅ Allocated 1 ports successfully
[32m10:29:19 - INFO -   ✅ Allocate System Ports (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Allocate System Ports (⏱️ 0.00s)
[32m10:29:19 - INFO -   ▶️  Generate System Scaffold[0m
INFO:VerboseAutocoder:  ▶️  Generate System Scaffold
{"timestamp": "2025-08-25T10:29:19.054260", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Component 'user_api_endpoint' already has port 8613"}
INFO:autocoder_cc.core.port_registry:Component 'user_api_endpoint' already has port 8613
{"timestamp": "2025-08-25T10:29:19.054354", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Allocated port 28205 for metrics (None)"}
INFO:autocoder_cc.core.port_registry:Allocated port 28205 for metrics (None)
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
[32m10:29:19 - INFO -     📄 Generated: main.py[0m
INFO:VerboseAutocoder:    📄 Generated: main.py
[32m10:29:19 - INFO -        📏 Size: 11214 chars, 280 lines[0m
INFO:VerboseAutocoder:       📏 Size: 11214 chars, 280 lines
DEBUG:VerboseAutocoder:       🏷️  component_count: 3
DEBUG:VerboseAutocoder:       🏷️  file_type: system_entry_point
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Generated main.py for user_data_api_system
DEBUG:VerboseAutocoder:            4: Using dynamic component loading - NO HARDCODED IMPORTS
DEBUG:VerboseAutocoder:            5: Following Enterprise Roadmap v3 requirements
DEBUG:VerboseAutocoder:            6: """
DEBUG:VerboseAutocoder:            7: import asyncio
DEBUG:VerboseAutocoder:            8: import logging
DEBUG:VerboseAutocoder:            9: from datetime import datetime
DEBUG:VerboseAutocoder:           10: from pathlib import Path
DEBUG:VerboseAutocoder:           11: from contextlib import asynccontextmanager
DEBUG:VerboseAutocoder:           12: from typing import Dict, Any, Optional
DEBUG:VerboseAutocoder:           13: import os
DEBUG:VerboseAutocoder:           14: import yaml
DEBUG:VerboseAutocoder:           15: import importlib.util
DEBUG:VerboseAutocoder:           16: 
DEBUG:VerboseAutocoder:           17: from fastapi import FastAPI, HTTPException, Request
DEBUG:VerboseAutocoder:           18: from pydantic import BaseModel
DEBUG:VerboseAutocoder:           19: import anyio
DEBUG:VerboseAutocoder:           20: 
DEBUG:VerboseAutocoder:          ... (261 more lines)
[32m10:29:19 - INFO -     📄 Generated: config/system_config.yaml[0m
INFO:VerboseAutocoder:    📄 Generated: config/system_config.yaml
[32m10:29:19 - INFO -        📏 Size: 1210 chars, 58 lines[0m
INFO:VerboseAutocoder:       📏 Size: 1210 chars, 58 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: system_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: system:
DEBUG:VerboseAutocoder:            2:   name: user_data_api_system
DEBUG:VerboseAutocoder:            3:   version: 1.0.0
DEBUG:VerboseAutocoder:            4:   environment: development
DEBUG:VerboseAutocoder:            5: database:
DEBUG:VerboseAutocoder:            6:   default:
DEBUG:VerboseAutocoder:            7:     database_type: postgresql
DEBUG:VerboseAutocoder:            8:     db_host: localhost
DEBUG:VerboseAutocoder:            9:     db_port: 5432
DEBUG:VerboseAutocoder:           10:     db_name: dev_db
DEBUG:VerboseAutocoder:           11:     db_user: dev_user
DEBUG:VerboseAutocoder:           12:     db_password: dev_password
DEBUG:VerboseAutocoder:           13:     min_connections: 1
DEBUG:VerboseAutocoder:           14:     max_connections: 10
DEBUG:VerboseAutocoder:           15:     connection_timeout: 30
DEBUG:VerboseAutocoder:           16:     ssl_mode: disable
DEBUG:VerboseAutocoder:           17:     charset: utf8mb4
DEBUG:VerboseAutocoder:           18:   environment: development
DEBUG:VerboseAutocoder:           19:   components:
DEBUG:VerboseAutocoder:           20:     user_data_store:
DEBUG:VerboseAutocoder:          ... (39 more lines)
[32m10:29:19 - INFO -     📄 Generated: requirements.txt[0m
INFO:VerboseAutocoder:    📄 Generated: requirements.txt
[32m10:29:19 - INFO -        📏 Size: 226 chars, 11 lines[0m
INFO:VerboseAutocoder:       📏 Size: 226 chars, 11 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: python_dependencies
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: anyio>=3.7.0
DEBUG:VerboseAutocoder:            2: asyncio-extras>=1.3.0
DEBUG:VerboseAutocoder:            3: asyncpg>=0.28.0
DEBUG:VerboseAutocoder:            4: databases>=0.7.0
DEBUG:VerboseAutocoder:            5: fastapi>=0.100.0
DEBUG:VerboseAutocoder:            6: httpx>=0.24.0
DEBUG:VerboseAutocoder:            7: prometheus-client>=0.17.0
DEBUG:VerboseAutocoder:            8: psycopg2-binary>=2.9.0
DEBUG:VerboseAutocoder:            9: pydantic-settings>=2.0.0
DEBUG:VerboseAutocoder:           10: pydantic>=2.0.0
DEBUG:VerboseAutocoder:           11: pyyaml>=6.0
DEBUG:VerboseAutocoder:           12: uvicorn[standard]>=0.22.0
[32m10:29:19 - INFO -     📄 Generated: Dockerfile[0m
INFO:VerboseAutocoder:    📄 Generated: Dockerfile
[32m10:29:19 - INFO -        📏 Size: 939 chars, 35 lines[0m
INFO:VerboseAutocoder:       📏 Size: 939 chars, 35 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: container_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: # Generated Production Dockerfile for user_data_api_system
DEBUG:VerboseAutocoder:            2: FROM python:3.11-slim
DEBUG:VerboseAutocoder:            3: 
DEBUG:VerboseAutocoder:            4: # Set working directory
DEBUG:VerboseAutocoder:            5: WORKDIR /app
DEBUG:VerboseAutocoder:            6: 
DEBUG:VerboseAutocoder:            7: # Install system dependencies for production
DEBUG:VerboseAutocoder:            8: RUN apt-get update && apt-get install -y \
DEBUG:VerboseAutocoder:            9:     curl \
DEBUG:VerboseAutocoder:           10:     && rm -rf /var/lib/apt/lists/*
DEBUG:VerboseAutocoder:           11: 
DEBUG:VerboseAutocoder:           12: # Copy requirements and install dependencies
DEBUG:VerboseAutocoder:           13: COPY requirements.txt .
DEBUG:VerboseAutocoder:           14: RUN pip install --no-cache-dir -r requirements.txt
DEBUG:VerboseAutocoder:           15: 
DEBUG:VerboseAutocoder:           16: # Copy application code
DEBUG:VerboseAutocoder:           17: COPY . .
DEBUG:VerboseAutocoder:           18: 
DEBUG:VerboseAutocoder:           19: # Create config and logs directories
DEBUG:VerboseAutocoder:           20: RUN mkdir -p config logs
DEBUG:VerboseAutocoder:          ... (16 more lines)
[32m10:29:19 - INFO -   ✅ Generate System Scaffold (⏱️ 0.01s)[0m
INFO:VerboseAutocoder:  ✅ Generate System Scaffold (⏱️ 0.01s)
[32m10:29:19 - INFO -   ▶️  Generate Database Schema Artifacts[0m
INFO:VerboseAutocoder:  ▶️  Generate Database Schema Artifacts
{"timestamp": "2025-08-25T10:29:19.066985", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Generated 2 database schema files"}
INFO:VersionedSchemaManager:✅ Generated 2 database schema files
[32m10:29:19 - INFO - ✅ Generated 2 schema artifacts[0m
INFO:VerboseAutocoder:✅ Generated 2 schema artifacts
[32m10:29:19 - INFO -     📄 Generated: database/schema_v1_0_0.sql[0m
INFO:VerboseAutocoder:    📄 Generated: database/schema_v1_0_0.sql
[32m10:29:19 - INFO -        📏 Size: 622 chars, 18 lines[0m
INFO:VerboseAutocoder:       📏 Size: 622 chars, 18 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: -- Generated Database Schema
DEBUG:VerboseAutocoder:            2: -- Schema Version: 1.0.0
DEBUG:VerboseAutocoder:            3: -- Generated: 2025-07-15
DEBUG:VerboseAutocoder:            4: 
DEBUG:VerboseAutocoder:            5: -- Enable UUID extension
DEBUG:VerboseAutocoder:            6: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DEBUG:VerboseAutocoder:            7: 
DEBUG:VerboseAutocoder:            8: -- Table for user_data_store component
DEBUG:VerboseAutocoder:            9: CREATE TABLE user_data_store_data (
DEBUG:VerboseAutocoder:           10:     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
DEBUG:VerboseAutocoder:           11:     data JSONB NOT NULL,
DEBUG:VerboseAutocoder:           12:     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
DEBUG:VerboseAutocoder:           13:     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
DEBUG:VerboseAutocoder:           14: );
DEBUG:VerboseAutocoder:           15: 
DEBUG:VerboseAutocoder:           16: -- Index for efficient querying
DEBUG:VerboseAutocoder:           17: CREATE INDEX idx_user_data_store_data_created_at ON user_data_store_data (created_at);
DEBUG:VerboseAutocoder:           18: CREATE INDEX idx_user_data_store_data_data_gin ON user_data_store_data USING gin(data);
DEBUG:VerboseAutocoder:           19: 
[32m10:29:19 - INFO -     📄 Generated: database/migration_metadata.json[0m
INFO:VerboseAutocoder:    📄 Generated: database/migration_metadata.json
[32m10:29:19 - INFO -        📏 Size: 163 chars, 7 lines[0m
INFO:VerboseAutocoder:       📏 Size: 163 chars, 7 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: {
DEBUG:VerboseAutocoder:            2:   "current_version": "1.0.0",
DEBUG:VerboseAutocoder:            3:   "generated_at": "2025-07-15T16:00:00Z",
DEBUG:VerboseAutocoder:            4:   "blueprint_hash": "ebb116715dd040a1",
DEBUG:VerboseAutocoder:            5:   "schema_files": [
DEBUG:VerboseAutocoder:            6:     "schema_v1_0_0.sql"
DEBUG:VerboseAutocoder:            7:   ]
DEBUG:VerboseAutocoder:            8: }
[32m10:29:19 - INFO -   ✅ Generate Database Schema Artifacts (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Database Schema Artifacts (⏱️ 0.00s)
[32m10:29:19 - INFO -   ▶️  Generate Service Communication Configuration[0m
INFO:VerboseAutocoder:  ▶️  Generate Service Communication Configuration
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 1: Trying gemini/gemini-2.5-flash
{"timestamp": "2025-08-25T10:29:19.069860", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)"}
INFO:autocoder_cc.core.timeout_manager:TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)
{"timestamp": "2025-08-25T10:29:19.069948", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "Global TimeoutManager instance created"}
INFO:autocoder_cc.core.timeout_manager:Global TimeoutManager instance created
[92m10:29:19 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:LiteLLM:
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
WARNING:autocoder_cc.llm_providers.unified_llm_provider:❌ Error with gemini/gemini-2.5-flash: LLM returned empty content (None) from gemini/gemini-2.5-flash
ERROR:autocoder_cc.llm_providers.unified_llm_provider:Primary model failed after 5.87s (fallback disabled)
{"timestamp": "2025-08-25T10:29:24.943256", "level": "ERROR", "logger_name": "system_generator", "message": "CRITICAL: LLM messaging selection failed: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.", "component": "SystemGenerator"}
ERROR:system_generator:CRITICAL: LLM messaging selection failed: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.
[31m10:29:24 - ERROR - ❌ Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.[0m
ERROR:VerboseAutocoder:❌ Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
[31m10:29:24 - ERROR -   ❌ Generate Service Communication Configuration FAILED (⏱️ 5.87s)[0m
ERROR:VerboseAutocoder:  ❌ Generate Service Communication Configuration FAILED (⏱️ 5.87s)
[31m10:29:24 - ERROR -      💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.[0m
ERROR:VerboseAutocoder:     💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
DEBUG:VerboseAutocoder:     📜 Stack trace:
DEBUG:VerboseAutocoder:        Traceback (most recent call last):
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 152, in _generate_with_llm
    response = future.result()
               ^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/concurrent/futures/_base.py", line 456, in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/usr/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/llm_providers/unified_llm_provider.py", line 245, in generate
    raise LLMProviderError(error_msg)
DEBUG:VerboseAutocoder:        autocoder_cc.llm_providers.base_provider.LLMProviderError: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.
DEBUG:VerboseAutocoder:        
The above exception was the direct cause of the following exception:
DEBUG:VerboseAutocoder:        Traceback (most recent call last):
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1657, in _determine_messaging_type
    response = self.component_generator._generate_with_llm(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 181, in _generate_with_llm
    raise RuntimeError(
DEBUG:VerboseAutocoder:        RuntimeError: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.
DEBUG:VerboseAutocoder:        
The above exception was the direct cause of the following exception:
DEBUG:VerboseAutocoder:        Traceback (most recent call last):
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 391, in _generate_system_with_logging
    messaging_config = self.generate_service_communication_config(system_blueprint)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1601, in generate_service_communication_config
    messaging_type = self._determine_messaging_type(system_blueprint)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1686, in _determine_messaging_type
    raise RuntimeError(
DEBUG:VerboseAutocoder:        RuntimeError: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
DEBUG:VerboseAutocoder:        
During handling of the above exception, another exception occurred:
DEBUG:VerboseAutocoder:        Traceback (most recent call last):
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 398, in _generate_system_with_logging
    raise RuntimeError(error_msg)
DEBUG:VerboseAutocoder:        RuntimeError: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
[31m10:29:24 - ERROR - ❌ Generate System: user_data_api_system FAILED (⏱️ 5.90s)[0m
ERROR:VerboseAutocoder:❌ Generate System: user_data_api_system FAILED (⏱️ 5.90s)
[31m10:29:24 - ERROR -    💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.[0m
ERROR:VerboseAutocoder:   💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
DEBUG:VerboseAutocoder:   📜 Stack trace:
DEBUG:VerboseAutocoder:      Traceback (most recent call last):
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 152, in _generate_with_llm
    response = future.result()
               ^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/concurrent/futures/_base.py", line 456, in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/usr/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/llm_providers/unified_llm_provider.py", line 245, in generate
    raise LLMProviderError(error_msg)
DEBUG:VerboseAutocoder:      autocoder_cc.llm_providers.base_provider.LLMProviderError: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.
DEBUG:VerboseAutocoder:      
The above exception was the direct cause of the following exception:
DEBUG:VerboseAutocoder:      Traceback (most recent call last):
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1657, in _determine_messaging_type
    response = self.component_generator._generate_with_llm(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 181, in _generate_with_llm
    raise RuntimeError(
DEBUG:VerboseAutocoder:      RuntimeError: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.
DEBUG:VerboseAutocoder:      
The above exception was the direct cause of the following exception:
DEBUG:VerboseAutocoder:      Traceback (most recent call last):
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 391, in _generate_system_with_logging
    messaging_config = self.generate_service_communication_config(system_blueprint)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1601, in generate_service_communication_config
    messaging_type = self._determine_messaging_type(system_blueprint)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1686, in _determine_messaging_type
    raise RuntimeError(
DEBUG:VerboseAutocoder:      RuntimeError: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
DEBUG:VerboseAutocoder:      
During handling of the above exception, another exception occurred:
DEBUG:VerboseAutocoder:      Traceback (most recent call last):
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 244, in _generate_system_from_blueprint
    result = await self._generate_system_with_logging(system_blueprint)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 398, in _generate_system_with_logging
    raise RuntimeError(error_msg)
DEBUG:VerboseAutocoder:      RuntimeError: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 152, in _generate_with_llm
    response = future.result()
               ^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/concurrent/futures/_base.py", line 456, in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
  File "/usr/lib/python3.12/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/llm_providers/unified_llm_provider.py", line 245, in generate
    raise LLMProviderError(error_msg)
autocoder_cc.llm_providers.base_provider.LLMProviderError: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1657, in _determine_messaging_type
    response = self.component_generator._generate_with_llm(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/component_logic_generator.py", line 181, in _generate_with_llm
    raise RuntimeError(
RuntimeError: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 391, in _generate_system_with_logging
    messaging_config = self.generate_service_communication_config(system_blueprint)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1601, in generate_service_communication_config
    messaging_type = self._determine_messaging_type(system_blueprint)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 1686, in _determine_messaging_type
    raise RuntimeError(
RuntimeError: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_e2e_generation.py", line 69, in <module>
    test_e2e_generation()
  File "/home/brian/projects/autocoder4_cc/test_e2e_generation.py", line 16, in test_e2e_generation
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
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 232, in generate_system_from_yaml
    return await self._generate_system_from_blueprint(system_blueprint)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 244, in _generate_system_from_blueprint
    result = await self._generate_system_with_logging(system_blueprint)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 398, in _generate_system_with_logging
    raise RuntimeError(error_msg)
RuntimeError: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
