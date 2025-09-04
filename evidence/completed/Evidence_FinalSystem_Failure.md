{"timestamp": "2025-08-26T12:38:34.650200", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-26T12:38:34.650345", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-26T12:38:34.650426", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-26T12:38:34.650492", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-26T12:38:34.650557", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-26T12:38:34.650620", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-26T12:38:34.650681", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-26T12:38:34.650740", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-26T12:38:34.650799", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-26T12:38:34.650856", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-26T12:38:34.650914", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-26T12:38:34.650972", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-26T12:38:34.651030", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-26T12:38:34.651086", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-26T12:38:34.651143", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-26T12:38:36.502805", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-26T12:38:36.502905", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-26T12:38:36.504363", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-26T12:38:36.506604", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-26T12:38:36.506699", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-26T12:38:36.506795", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-26T12:38:36.506892", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-26T12:38:36.506964", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-26T12:38:36.507027", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-26T12:38:36.507587", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-26T12:38:36.509676", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-26T12:38:36.602452", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-26T12:38:36.604764", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
[92m12:38:36 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
[92m12:38:45 - LiteLLM:INFO[0m: utils.py:1262 - Wrapper: Completed Call, calling success_handler
[92m12:38:45 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
[92m12:38:48 - LiteLLM:INFO[0m: utils.py:1262 - Wrapper: Completed Call, calling success_handler
🔬 Testing complete system generation with healer fix...
------------------------------------------------------------
🤖 Translating natural language to blueprint...
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: event_processing_system
  description: A system designed to receive events from a source and persist them in a dedicated store.
  version: 1.0.0
  components:
...

🔧 Generating system components...
[32m12:38:48 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m12:38:48 - INFO - Session ID: autocoder_1756237128[0m
[32m12:38:48 - INFO - Log file: test_fixed_output/generation_verbose.log[0m
[32m12:38:48 - INFO - Structured log: test_fixed_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-26T12:38:48.102077", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback ENABLED - will try multiple models on failure
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T12:38:48.114252", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T12:38:48.114752", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-26T12:38:48.114869", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback ENABLED - will try multiple models on failure
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T12:38:48.115803", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T12:38:48.115990", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback ENABLED - will try multiple models on failure
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T12:38:48.127198", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T12:38:48.127380", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-26T12:38:48.133785", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-26T12:38:48.133949", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-26T12:38:48.134043", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-26T12:38:48.134125", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-26T12:38:48.134978", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_fixed_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-26T12:38:48.135279", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-26T12:38:48.141986", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-26T12:38:48.142147", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process (phase: structural)"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process (phase: structural)
{"timestamp": "2025-08-26T12:38:48.142224", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-26T12:38:48.142325", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: event_source.output → event_store.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: event_source.output → event_store.input
{"timestamp": "2025-08-26T12:38:48.142396", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-26T12:38:48.142488", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
{"timestamp": "2025-08-26T12:38:48.142663", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-26T12:38:48.142839", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-26T12:38:48.142942", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 2}}
INFO:port_auto_generator:Port auto-generation completed
{"timestamp": "2025-08-26T12:38:48.143103", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying schema healing for attempt 1"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying schema healing for attempt 1
{"timestamp": "2025-08-26T12:38:48.143275", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process (phase: schema)"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process (phase: schema)
{"timestamp": "2025-08-26T12:38:48.143373", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
INFO:autocoder_cc.healing.blueprint_healer:Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)
{"timestamp": "2025-08-26T12:38:48.143443", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Added transformation to handle schema mismatch: common_object_schema -> ItemSchema"}
INFO:autocoder_cc.healing.blueprint_healer:Added transformation to handle schema mismatch: common_object_schema -> ItemSchema
{"timestamp": "2025-08-26T12:38:48.143508", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Applied 1 schema compatibility fixes"}
INFO:autocoder_cc.healing.blueprint_healer:Applied 1 schema compatibility fixes
{"timestamp": "2025-08-26T12:38:48.143573", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Connectivity validation complete: 0 orphaned components found
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
[32m12:38:48 - INFO - ▶️  Generate System: event_processing_system[0m
INFO:VerboseAutocoder:▶️  Generate System: event_processing_system
DEBUG:VerboseAutocoder:   📋 system_name: event_processing_system
DEBUG:VerboseAutocoder:   📋 component_count: 2
DEBUG:VerboseAutocoder:   📋 binding_count: 2
[32m12:38:48 - INFO - 🚀 Generating system: event_processing_system[0m
INFO:VerboseAutocoder:🚀 Generating system: event_processing_system
[32m12:38:48 - INFO - 📋 Blueprint details:[0m
INFO:VerboseAutocoder:📋 Blueprint details:
[32m12:38:48 - INFO -    - Components: 2[0m
INFO:VerboseAutocoder:   - Components: 2
[32m12:38:48 - INFO -    - Bindings: 2[0m
INFO:VerboseAutocoder:   - Bindings: 2
[32m12:38:48 - INFO -    - Version: 1.0.0[0m
INFO:VerboseAutocoder:   - Version: 1.0.0
[32m12:38:48 - INFO -   ▶️  Pre-Generation Validation[0m
INFO:VerboseAutocoder:  ▶️  Pre-Generation Validation
{"timestamp": "2025-08-26T12:38:48.144655", "level": "INFO", "logger_name": "ValidationOrchestrator", "message": "✅ Pre-generation validation passed"}
INFO:ValidationOrchestrator:✅ Pre-generation validation passed
[32m12:38:48 - INFO -     ✅ pre_generation: PASSED[0m
INFO:VerboseAutocoder:    ✅ pre_generation: PASSED
DEBUG:VerboseAutocoder:       📊 success: True
[31m12:38:48 - ERROR -        🚨 Errors (0):[0m
ERROR:VerboseAutocoder:       🚨 Errors (0):
DEBUG:VerboseAutocoder:       📊 total_errors: 0
[32m12:38:48 - INFO -   ✅ Pre-Generation Validation (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Pre-Generation Validation (⏱️ 0.00s)
[32m12:38:48 - INFO -   ▶️  Allocate System Ports[0m
INFO:VerboseAutocoder:  ▶️  Allocate System Ports
[32m12:38:48 - INFO - ✅ Allocated 0 ports successfully[0m
INFO:VerboseAutocoder:✅ Allocated 0 ports successfully
[32m12:38:48 - INFO -   ✅ Allocate System Ports (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Allocate System Ports (⏱️ 0.00s)
[32m12:38:48 - INFO -   ▶️  Generate System Scaffold[0m
INFO:VerboseAutocoder:  ▶️  Generate System Scaffold
{"timestamp": "2025-08-26T12:38:48.145911", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "PortRegistry initialized: range 8000-65535, reserved 10 ports"}
INFO:autocoder_cc.core.port_registry:PortRegistry initialized: range 8000-65535, reserved 10 ports
{"timestamp": "2025-08-26T12:38:48.145989", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Global PortRegistry instance created"}
INFO:autocoder_cc.core.port_registry:Global PortRegistry instance created
{"timestamp": "2025-08-26T12:38:48.146074", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Allocated port 21878 for metrics (None)"}
INFO:autocoder_cc.core.port_registry:Allocated port 21878 for metrics (None)
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
[32m12:38:48 - INFO -     📄 Generated: main.py[0m
INFO:VerboseAutocoder:    📄 Generated: main.py
[32m12:38:48 - INFO -        📏 Size: 9619 chars, 253 lines[0m
INFO:VerboseAutocoder:       📏 Size: 9619 chars, 253 lines
DEBUG:VerboseAutocoder:       🏷️  component_count: 2
DEBUG:VerboseAutocoder:       🏷️  file_type: system_entry_point
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Generated main.py for event_processing_system
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
DEBUG:VerboseAutocoder:          ... (234 more lines)
[32m12:38:48 - INFO -     📄 Generated: config/system_config.yaml[0m
INFO:VerboseAutocoder:    📄 Generated: config/system_config.yaml
[32m12:38:48 - INFO -        📏 Size: 1125 chars, 54 lines[0m
INFO:VerboseAutocoder:       📏 Size: 1125 chars, 54 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: system_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: system:
DEBUG:VerboseAutocoder:            2:   name: event_processing_system
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
DEBUG:VerboseAutocoder:           20:     event_store:
DEBUG:VerboseAutocoder:          ... (35 more lines)
[32m12:38:48 - INFO -     📄 Generated: requirements.txt[0m
INFO:VerboseAutocoder:    📄 Generated: requirements.txt
[32m12:38:48 - INFO -        📏 Size: 226 chars, 11 lines[0m
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
[32m12:38:48 - INFO -     📄 Generated: Dockerfile[0m
INFO:VerboseAutocoder:    📄 Generated: Dockerfile
[32m12:38:48 - INFO -        📏 Size: 930 chars, 34 lines[0m
INFO:VerboseAutocoder:       📏 Size: 930 chars, 34 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: container_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: # Generated Production Dockerfile for event_processing_system
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
DEBUG:VerboseAutocoder:          ... (15 more lines)
[32m12:38:48 - INFO -   ✅ Generate System Scaffold (⏱️ 0.01s)[0m
INFO:VerboseAutocoder:  ✅ Generate System Scaffold (⏱️ 0.01s)
[32m12:38:48 - INFO -   ▶️  Generate Database Schema Artifacts[0m
INFO:VerboseAutocoder:  ▶️  Generate Database Schema Artifacts
{"timestamp": "2025-08-26T12:38:48.158502", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Generated 2 database schema files"}
INFO:VersionedSchemaManager:✅ Generated 2 database schema files
[32m12:38:48 - INFO - ✅ Generated 2 schema artifacts[0m
INFO:VerboseAutocoder:✅ Generated 2 schema artifacts
[32m12:38:48 - INFO -     📄 Generated: database/schema_v1_0_0.sql[0m
INFO:VerboseAutocoder:    📄 Generated: database/schema_v1_0_0.sql
[32m12:38:48 - INFO -        📏 Size: 598 chars, 18 lines[0m
INFO:VerboseAutocoder:       📏 Size: 598 chars, 18 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: -- Generated Database Schema
DEBUG:VerboseAutocoder:            2: -- Schema Version: 1.0.0
DEBUG:VerboseAutocoder:            3: -- Generated: 2025-07-15
DEBUG:VerboseAutocoder:            4: 
DEBUG:VerboseAutocoder:            5: -- Enable UUID extension
DEBUG:VerboseAutocoder:            6: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DEBUG:VerboseAutocoder:            7: 
DEBUG:VerboseAutocoder:            8: -- Table for event_store component
DEBUG:VerboseAutocoder:            9: CREATE TABLE event_store_data (
DEBUG:VerboseAutocoder:           10:     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
DEBUG:VerboseAutocoder:           11:     data JSONB NOT NULL,
DEBUG:VerboseAutocoder:           12:     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
DEBUG:VerboseAutocoder:           13:     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
DEBUG:VerboseAutocoder:           14: );
DEBUG:VerboseAutocoder:           15: 
DEBUG:VerboseAutocoder:           16: -- Index for efficient querying
DEBUG:VerboseAutocoder:           17: CREATE INDEX idx_event_store_data_created_at ON event_store_data (created_at);
DEBUG:VerboseAutocoder:           18: CREATE INDEX idx_event_store_data_data_gin ON event_store_data USING gin(data);
DEBUG:VerboseAutocoder:           19: 
[32m12:38:48 - INFO -     📄 Generated: database/migration_metadata.json[0m
INFO:VerboseAutocoder:    📄 Generated: database/migration_metadata.json
[32m12:38:48 - INFO -        📏 Size: 163 chars, 7 lines[0m
INFO:VerboseAutocoder:       📏 Size: 163 chars, 7 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: {
DEBUG:VerboseAutocoder:            2:   "current_version": "1.0.0",
DEBUG:VerboseAutocoder:            3:   "generated_at": "2025-07-15T16:00:00Z",
DEBUG:VerboseAutocoder:            4:   "blueprint_hash": "0186c7e22f68c4fb",
DEBUG:VerboseAutocoder:            5:   "schema_files": [
DEBUG:VerboseAutocoder:            6:     "schema_v1_0_0.sql"
DEBUG:VerboseAutocoder:            7:   ]
DEBUG:VerboseAutocoder:            8: }
[32m12:38:48 - INFO -   ✅ Generate Database Schema Artifacts (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Database Schema Artifacts (⏱️ 0.00s)
[32m12:38:48 - INFO -   ▶️  Generate Service Communication Configuration[0m
INFO:VerboseAutocoder:  ▶️  Generate Service Communication Configuration
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 1: Trying gemini/gemini-2.5-flash
{"timestamp": "2025-08-26T12:38:48.162076", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)"}
INFO:autocoder_cc.core.timeout_manager:TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)
{"timestamp": "2025-08-26T12:38:48.162166", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "Global TimeoutManager instance created"}
INFO:autocoder_cc.core.timeout_manager:Global TimeoutManager instance created
[92m12:38:48 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:LiteLLM:
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
WARNING:autocoder_cc.llm_providers.unified_llm_provider:❌ Error with gemini/gemini-2.5-flash: LLM returned empty content (None) from gemini/gemini-2.5-flash
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 2: Trying gpt-4o-mini
[92m12:38:55 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gpt-4o-mini; provider = openai
INFO:LiteLLM:
LiteLLM completion() model= gpt-4o-mini; provider = openai
INFO:autocoder_cc.llm_providers.unified_llm_provider:✅ Success with gpt-4o-mini in 8.11s
{"timestamp": "2025-08-26T12:38:56.271920", "level": "INFO", "logger_name": "system_generator", "message": "Messaging type selected using LLM intelligence", "component": "SystemGenerator", "operation": "_determine_messaging_type", "tags": {"selected_type": "kafka", "component_count": 2, "method": "llm_intelligent"}}
INFO:system_generator:Messaging type selected using LLM intelligence
[32m12:38:56 - INFO - ✅ Generated service communication configuration[0m
INFO:VerboseAutocoder:✅ Generated service communication configuration
[32m12:38:56 - INFO -     📄 Generated: config/messaging_config.yaml[0m
INFO:VerboseAutocoder:    📄 Generated: config/messaging_config.yaml
[32m12:38:56 - INFO -        📏 Size: 1846 chars, 68 lines[0m
INFO:VerboseAutocoder:       📏 Size: 1846 chars, 68 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: messaging_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: messaging:
DEBUG:VerboseAutocoder:            2:   connection:
DEBUG:VerboseAutocoder:            3:     bootstrap_servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
DEBUG:VerboseAutocoder:            4:     client_id: ${KAFKA_CLIENT_ID:autocoder_cc}
DEBUG:VerboseAutocoder:            5:     security_protocol: ${KAFKA_SECURITY_PROTOCOL:PLAINTEXT}
DEBUG:VerboseAutocoder:            6:   queues:
DEBUG:VerboseAutocoder:            7:     event_source_input:
DEBUG:VerboseAutocoder:            8:       auto_delete: false
DEBUG:VerboseAutocoder:            9:       durable: true
DEBUG:VerboseAutocoder:           10:       max_length: 10000
DEBUG:VerboseAutocoder:           11:       message_ttl: 3600000
DEBUG:VerboseAutocoder:           12:       routing_key: event_source.input
DEBUG:VerboseAutocoder:           13:     event_source_output:
DEBUG:VerboseAutocoder:           14:       auto_delete: false
DEBUG:VerboseAutocoder:           15:       durable: true
DEBUG:VerboseAutocoder:           16:       max_length: 10000
DEBUG:VerboseAutocoder:           17:       message_ttl: 3600000
DEBUG:VerboseAutocoder:           18:       routing_key: event_source.output
DEBUG:VerboseAutocoder:           19:     event_store_input:
DEBUG:VerboseAutocoder:           20:       auto_delete: false
DEBUG:VerboseAutocoder:          ... (49 more lines)
[32m12:38:56 - INFO -   ✅ Generate Service Communication Configuration (⏱️ 8.11s)[0m
INFO:VerboseAutocoder:  ✅ Generate Service Communication Configuration (⏱️ 8.11s)
[32m12:38:56 - INFO -   ▶️  Generate Shared Observability Module[0m
INFO:VerboseAutocoder:  ▶️  Generate Shared Observability Module
[32m12:38:56 - INFO -     📄 Generated: observability.py[0m
INFO:VerboseAutocoder:    📄 Generated: observability.py
[32m12:38:56 - INFO -        📏 Size: 14008 chars, 365 lines[0m
INFO:VerboseAutocoder:       📏 Size: 14008 chars, 365 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: shared_module
DEBUG:VerboseAutocoder:       🏷️  component_count: 2
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Shared Observability Module for event_processing_system
DEBUG:VerboseAutocoder:            4: ============================================
DEBUG:VerboseAutocoder:            5: 
DEBUG:VerboseAutocoder:            6: Generated by ObservabilityGenerator on 2025-08-26 12:38:56
DEBUG:VerboseAutocoder:            7: 
DEBUG:VerboseAutocoder:            8: This module contains all observability infrastructure shared across components:
DEBUG:VerboseAutocoder:            9: - StandaloneMetricsCollector: Metrics collection and reporting
DEBUG:VerboseAutocoder:           10: - StandaloneTracer: Distributed tracing support  
DEBUG:VerboseAutocoder:           11: - StandaloneSpan: Span implementation for tracing
DEBUG:VerboseAutocoder:           12: - ComponentStatus: Component state tracking
DEBUG:VerboseAutocoder:           13: - ComposedComponent: Base class for all components
DEBUG:VerboseAutocoder:           14: - SpanStatus: OpenTelemetry-compatible span status codes
DEBUG:VerboseAutocoder:           15: 
DEBUG:VerboseAutocoder:           16: Usage:
DEBUG:VerboseAutocoder:           17:     from observability import ComposedComponent, SpanStatus
DEBUG:VerboseAutocoder:           18:     
DEBUG:VerboseAutocoder:           19:     class MyComponent(ComposedComponent):
DEBUG:VerboseAutocoder:           20:         def __init__(self, name: str, config: Dict[str, Any] = None):
DEBUG:VerboseAutocoder:          ... (346 more lines)
[32m12:38:56 - INFO - ✅ Generated shared observability module: test_fixed_output/scaffolds/event_processing_system/components/observability.py[0m
INFO:VerboseAutocoder:✅ Generated shared observability module: test_fixed_output/scaffolds/event_processing_system/components/observability.py
[32m12:38:56 - INFO - 📏 Observability module: 14008 chars, 365 lines[0m
INFO:VerboseAutocoder:📏 Observability module: 14008 chars, 365 lines
[32m12:38:56 - INFO -   ✅ Generate Shared Observability Module (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Shared Observability Module (⏱️ 0.00s)
[32m12:38:56 - INFO -   ▶️  Generate Communication Framework[0m
INFO:VerboseAutocoder:  ▶️  Generate Communication Framework
[32m12:38:56 - INFO -     📄 Generated: communication.py[0m
INFO:VerboseAutocoder:    📄 Generated: communication.py
[32m12:38:56 - INFO -        📏 Size: 14668 chars, 386 lines[0m
INFO:VerboseAutocoder:       📏 Size: 14668 chars, 386 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: communication_framework
DEBUG:VerboseAutocoder:       🏷️  bindings_count: 2
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Component Communication Framework for event_processing_system
DEBUG:VerboseAutocoder:            4: ==================================================
DEBUG:VerboseAutocoder:            5: 
DEBUG:VerboseAutocoder:            6: Generated by ComponentCommunicationGenerator on 2025-08-26 12:38:56
DEBUG:VerboseAutocoder:            7: 
DEBUG:VerboseAutocoder:            8: This module provides the communication infrastructure for real inter-component
DEBUG:VerboseAutocoder:            9: message passing based on blueprint bindings.
DEBUG:VerboseAutocoder:           10: 
DEBUG:VerboseAutocoder:           11: Classes:
DEBUG:VerboseAutocoder:           12: - ComponentRegistry: Component discovery and registration
DEBUG:VerboseAutocoder:           13: - ComponentCommunicator: Message routing and delivery  
DEBUG:VerboseAutocoder:           14: - CommunicationConfig: Routing configuration from blueprint
DEBUG:VerboseAutocoder:           15: - MessageEnvelope: Structured message wrapper
DEBUG:VerboseAutocoder:           16: 
DEBUG:VerboseAutocoder:           17: Usage:
DEBUG:VerboseAutocoder:           18:     from communication import ComponentRegistry, ComponentCommunicator
DEBUG:VerboseAutocoder:           19:     
DEBUG:VerboseAutocoder:           20:     # In component initialization
DEBUG:VerboseAutocoder:          ... (367 more lines)
[32m12:38:56 - INFO - ✅ Generated communication framework: test_fixed_output/scaffolds/event_processing_system/components/communication.py[0m
INFO:VerboseAutocoder:✅ Generated communication framework: test_fixed_output/scaffolds/event_processing_system/components/communication.py
[32m12:38:56 - INFO - 📏 Communication module: 14668 chars, 386 lines[0m
INFO:VerboseAutocoder:📏 Communication module: 14668 chars, 386 lines
[32m12:38:56 - INFO - 🔗 Configured 2 component bindings for runtime routing[0m
INFO:VerboseAutocoder:🔗 Configured 2 component bindings for runtime routing
[32m12:38:56 - INFO -   ✅ Generate Communication Framework (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Communication Framework (⏱️ 0.00s)
[32m12:38:56 - INFO -   ▶️  Generate Component Implementations with Self-Healing[0m
INFO:VerboseAutocoder:  ▶️  Generate Component Implementations with Self-Healing
{"timestamp": "2025-08-26T12:38:56.283323", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "🚀 Starting integrated system generation with healing"}
INFO:HealingIntegratedGenerator:🚀 Starting integrated system generation with healing
{"timestamp": "2025-08-26T12:38:56.283454", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "📋 Parsing system blueprint..."}
INFO:HealingIntegratedGenerator:📋 Parsing system blueprint...
{"timestamp": "2025-08-26T12:38:56.343860", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-26T12:38:56.344047", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process (phase: structural)"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process (phase: structural)
{"timestamp": "2025-08-26T12:38:56.344129", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 2 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 2 components for missing bindings
{"timestamp": "2025-08-26T12:38:56.344213", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-26T12:38:56.344300", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-26T12:38:56.344381", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-26T12:38:56.344535", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-26T12:38:56.344620", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 0}}
INFO:port_auto_generator:Port auto-generation completed
{"timestamp": "2025-08-26T12:38:56.344783", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying schema healing for attempt 1"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying schema healing for attempt 1
{"timestamp": "2025-08-26T12:38:56.344932", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process (phase: schema)"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process (phase: schema)
{"timestamp": "2025-08-26T12:38:56.345025", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)"}
INFO:autocoder_cc.healing.blueprint_healer:Schema mismatch detected: event_source.output (common_object_schema) -> event_store.input (ItemSchema)
{"timestamp": "2025-08-26T12:38:56.345109", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 2 attempts"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing stagnated after 2 attempts
{"timestamp": "2025-08-26T12:38:56.345176", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing may be stagnating - limited operations performed"}
WARNING:autocoder_cc.healing.blueprint_healer:Healing may be stagnating - limited operations performed
{"timestamp": "2025-08-26T12:38:56.345239", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_processing_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Connectivity validation complete: 0 orphaned components found
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-26T12:38:56.345565", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   Blueprint parsed in 0.06s"}
INFO:HealingIntegratedGenerator:   Blueprint parsed in 0.06s
{"timestamp": "2025-08-26T12:38:56.345691", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "🔧 Starting component generation and validation loop..."}
INFO:HealingIntegratedGenerator:🔧 Starting component generation and validation loop...
{"timestamp": "2025-08-26T12:38:56.345802", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "\n🔄 Component validation attempt 1"}
INFO:HealingIntegratedGenerator:
🔄 Component validation attempt 1
{"timestamp": "2025-08-26T12:38:56.345874", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   🔧 Generating components..."}
INFO:HealingIntegratedGenerator:   🔧 Generating components...
{"timestamp": "2025-08-26T12:38:56.345941", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   Generating 2 components..."}
INFO:HealingIntegratedGenerator:   Generating 2 components...
{"timestamp": "2025-08-26T12:38:56.346061", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Generating event_source with LLM..."}
INFO:HealingIntegratedGenerator:     Generating event_source with LLM...
{"timestamp": "2025-08-26T12:38:56.346320", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "llm_generation_start", "component": "llm_component_generator_unified", "operation": {"generation_id": "event_source_1756237136", "component_type": "Source", "component_name": "event_source", "class_name": "Eventsource", "provider": "unified_llm_provider", "model": "automatic_fallback"}}
INFO:autocoder_cc.blueprint_language.llm_component_generator:llm_generation_start
{"timestamp": "2025-08-26T12:38:56.346408", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "llm_generation_attempt", "component": "llm_component_generator_unified", "operation": {"generation_id": "event_source_1756237136", "attempt": 1, "max_attempts": 6, "has_validation_feedback": false, "prompt_length": 7528}}
INFO:autocoder_cc.blueprint_language.llm_component_generator:llm_generation_attempt
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 1: Trying gemini/gemini-2.5-flash
[92m12:38:56 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:LiteLLM:
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:autocoder_cc.llm_providers.unified_llm_provider:✅ Success with gemini/gemini-2.5-flash in 22.03s
INFO:autocoder_cc.llm_providers.unified_llm_provider:Fallback ENABLED - will try multiple models on failure
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-26T12:39:18.379185", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-26T12:39:18.379371", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-26T12:39:18.379462", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-26T12:39:18.379558", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "/tmp"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-26T12:39:18.379628", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-26T12:39:18.417243", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "llm_generation_complete", "component": "llm_component_generator_unified", "operation": {"generation_id": "event_source_1756237136", "total_attempts": 1, "success": true, "provider": "gemini_2_5_flash", "model": "gemini/gemini-2.5-flash"}}
INFO:autocoder_cc.blueprint_language.llm_component_generator:llm_generation_complete
{"timestamp": "2025-08-26T12:39:18.417605", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Generated: event_source"}
INFO:HealingIntegratedGenerator:     Generated: event_source
{"timestamp": "2025-08-26T12:39:18.417737", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Using recipe 'Store' structure with LLM implementation for event_store"}
INFO:HealingIntegratedGenerator:     Using recipe 'Store' structure with LLM implementation for event_store
{"timestamp": "2025-08-26T12:39:18.417813", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Recipe provides structure, LLM will generate implementation..."}
INFO:HealingIntegratedGenerator:     Recipe provides structure, LLM will generate implementation...
{"timestamp": "2025-08-26T12:39:18.417894", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Generating event_store with LLM..."}
INFO:HealingIntegratedGenerator:     Generating event_store with LLM...
{"timestamp": "2025-08-26T12:39:18.418134", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "llm_generation_start", "component": "llm_component_generator_unified", "operation": {"generation_id": "event_store_1756237158", "component_type": "Store", "component_name": "event_store", "class_name": "Eventstore", "provider": "unified_llm_provider", "model": "automatic_fallback"}}
INFO:autocoder_cc.blueprint_language.llm_component_generator:llm_generation_start
{"timestamp": "2025-08-26T12:39:18.418218", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "llm_generation_attempt", "component": "llm_component_generator_unified", "operation": {"generation_id": "event_store_1756237158", "attempt": 1, "max_attempts": 6, "has_validation_feedback": false, "prompt_length": 9340}}
INFO:autocoder_cc.blueprint_language.llm_component_generator:llm_generation_attempt
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 1: Trying gemini/gemini-2.5-flash
[92m12:39:18 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:LiteLLM:
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
