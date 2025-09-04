{"timestamp": "2025-08-25T06:10:03.386461", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-25T06:10:03.386583", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-25T06:10:03.386668", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-25T06:10:03.386739", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-25T06:10:03.386805", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-25T06:10:03.386872", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-25T06:10:03.386934", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-25T06:10:03.386997", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-25T06:10:03.387058", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-25T06:10:03.387118", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-25T06:10:03.387187", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-25T06:10:03.387248", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-25T06:10:03.387309", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-25T06:10:03.387367", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-25T06:10:03.387427", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-25T06:10:05.267805", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-25T06:10:05.267906", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-25T06:10:05.269236", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:10:05.271240", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-25T06:10:05.271335", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-25T06:10:05.271407", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-25T06:10:05.271472", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-25T06:10:05.271515", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-25T06:10:05.271567", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:10:05.272129", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:10:05.274324", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-25T06:10:05.590887", "level": "INFO", "logger_name": "MetricsCollector.PrometheusServer", "message": "Production Prometheus server running on port 9090"}
{"timestamp": "2025-08-25T06:10:05.593397", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
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
[32m06:10:25 - INFO - 🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED[0m
[32m06:10:25 - INFO - Session ID: autocoder_1756127425[0m
[32m06:10:25 - INFO - Log file: test_e2e_output/generation_verbose.log[0m
[32m06:10:25 - INFO - Structured log: test_e2e_output/generation_verbose.json[0m
Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T06:10:25.439116", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T06:10:25.446610", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T06:10:25.447071", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
{"timestamp": "2025-08-25T06:10:25.447156", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T06:10:25.448083", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T06:10:25.448255", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
INFO:autocoder_cc.llm_providers.unified_llm_provider:Unified LLM Provider initialized with models: ['gemini_2_5_flash', 'openai_gpt4o_mini', 'claude_sonnet_4']
{"timestamp": "2025-08-25T06:10:25.455959", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator initialized - no more hanging!", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator initialized - no more hanging!
{"timestamp": "2025-08-25T06:10:25.456164", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.llm_component_generator", "message": "Unified LLM Component Generator ready - all modules loaded", "component": "llm_component_generator_unified"}
INFO:autocoder_cc.blueprint_language.llm_component_generator:Unified LLM Component Generator ready - all modules loaded
WARNING:opentelemetry.metrics._internal:Overriding of current MeterProvider is not allowed
{"timestamp": "2025-08-25T06:10:25.464077", "level": "INFO", "logger_name": "store_generator", "message": "StoreGenerator initialized", "component": "StoreGenerator", "operation": "init"}
INFO:store_generator:StoreGenerator initialized
INFO:autocoder_cc.blueprint_language.architectural_templates.template_selector:✅ TemplateSelector initialized with architectural templates
{"timestamp": "2025-08-25T06:10:25.464353", "level": "INFO", "logger_name": "component_logic_generator", "message": "ComponentLogicGenerator initialized with observability stack and architectural templates", "component": "ComponentLogicGenerator", "operation": "init", "tags": {"output_dir": "test_e2e_output/scaffolds"}}
INFO:component_logic_generator:ComponentLogicGenerator initialized with observability stack and architectural templates
{"timestamp": "2025-08-25T06:10:25.464463", "level": "INFO", "logger_name": "ComponentLogicGenerator", "message": "✅ ComponentLogicGenerator initialized with architectural templates"}
INFO:ComponentLogicGenerator:✅ ComponentLogicGenerator initialized with architectural templates
{"timestamp": "2025-08-25T06:10:25.464549", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
INFO:PropertyTestGenerator:✅ Property Test Generator initialized with fail-hard validation
{"timestamp": "2025-08-25T06:10:25.465547", "level": "INFO", "logger_name": "system_generator", "message": "SystemGenerator initialized with observability stack", "component": "SystemGenerator", "operation": "init", "tags": {"output_dir": "test_e2e_output", "verbose_logging": true, "timeout": null}}
INFO:system_generator:SystemGenerator initialized with observability stack
{"timestamp": "2025-08-25T06:10:25.465929", "level": "INFO", "logger_name": "port_auto_generator", "message": "ComponentPortAutoGenerator initialized", "component": "ComponentPortAutoGenerator", "operation": "init", "tags": {"template_count": 14}}
INFO:port_auto_generator:ComponentPortAutoGenerator initialized
{"timestamp": "2025-08-25T06:10:25.473955", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T06:10:25.474082", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T06:10:25.474145", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T06:10:25.474222", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_api_endpoint.request → user_store.query"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_api_endpoint.request → user_store.query
{"timestamp": "2025-08-25T06:10:25.474296", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_store.response → user_api_endpoint.data"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_store.response → user_api_endpoint.data
{"timestamp": "2025-08-25T06:10:25.474371", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_api_endpoint.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_api_endpoint.control
{"timestamp": "2025-08-25T06:10:25.474440", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_store.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_store.control
{"timestamp": "2025-08-25T06:10:25.474505", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 4 missing bindings
{"timestamp": "2025-08-25T06:10:25.474652", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 4 missing bindings
{"timestamp": "2025-08-25T06:10:25.474877", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T06:10:25.475068", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T06:10:25.475202", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 3}}
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
  user_store: Store → SINK → SINK (in=2, out=1)
🔍 DEBUG VALIDATION - Sources: set()
🔍 DEBUG VALIDATION - Sinks: {'user_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=True
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
[32m06:10:25 - INFO - ▶️  Generate System: user_data_api_system[0m
INFO:VerboseAutocoder:▶️  Generate System: user_data_api_system
DEBUG:VerboseAutocoder:   📋 system_name: user_data_api_system
DEBUG:VerboseAutocoder:   📋 component_count: 3
DEBUG:VerboseAutocoder:   📋 binding_count: 6
[32m06:10:25 - INFO - 🚀 Generating system: user_data_api_system[0m
INFO:VerboseAutocoder:🚀 Generating system: user_data_api_system
[32m06:10:25 - INFO - 📋 Blueprint details:[0m
INFO:VerboseAutocoder:📋 Blueprint details:
[32m06:10:25 - INFO -    - Components: 3[0m
INFO:VerboseAutocoder:   - Components: 3
[32m06:10:25 - INFO -    - Bindings: 6[0m
INFO:VerboseAutocoder:   - Bindings: 6
[32m06:10:25 - INFO -    - Version: 1.0.0[0m
INFO:VerboseAutocoder:   - Version: 1.0.0
[32m06:10:25 - INFO -   ▶️  Pre-Generation Validation[0m
INFO:VerboseAutocoder:  ▶️  Pre-Generation Validation
{"timestamp": "2025-08-25T06:10:25.478868", "level": "INFO", "logger_name": "ValidationOrchestrator", "message": "✅ Pre-generation validation passed"}
INFO:ValidationOrchestrator:✅ Pre-generation validation passed
[32m06:10:25 - INFO -     ✅ pre_generation: PASSED[0m
INFO:VerboseAutocoder:    ✅ pre_generation: PASSED
DEBUG:VerboseAutocoder:       📊 success: True
[31m06:10:25 - ERROR -        🚨 Errors (0):[0m
ERROR:VerboseAutocoder:       🚨 Errors (0):
DEBUG:VerboseAutocoder:       📊 total_errors: 0
[32m06:10:25 - INFO -   ✅ Pre-Generation Validation (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Pre-Generation Validation (⏱️ 0.00s)
[32m06:10:25 - INFO -   ▶️  Allocate System Ports[0m
INFO:VerboseAutocoder:  ▶️  Allocate System Ports
{"timestamp": "2025-08-25T06:10:25.479592", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "PortRegistry initialized: range 8000-65535, reserved 10 ports"}
INFO:autocoder_cc.core.port_registry:PortRegistry initialized: range 8000-65535, reserved 10 ports
{"timestamp": "2025-08-25T06:10:25.479674", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Global PortRegistry instance created"}
INFO:autocoder_cc.core.port_registry:Global PortRegistry instance created
{"timestamp": "2025-08-25T06:10:25.479756", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Allocated port 8466 for user_api_endpoint (APIEndpoint)"}
INFO:autocoder_cc.core.port_registry:Allocated port 8466 for user_api_endpoint (APIEndpoint)
[32m06:10:25 - INFO - 🔌 Allocated port 8466 for user_api_endpoint[0m
INFO:VerboseAutocoder:🔌 Allocated port 8466 for user_api_endpoint
[32m06:10:25 - INFO - ✅ Allocated 1 ports successfully[0m
INFO:VerboseAutocoder:✅ Allocated 1 ports successfully
[32m06:10:25 - INFO -   ✅ Allocate System Ports (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Allocate System Ports (⏱️ 0.00s)
[32m06:10:25 - INFO -   ▶️  Generate System Scaffold[0m
INFO:VerboseAutocoder:  ▶️  Generate System Scaffold
{"timestamp": "2025-08-25T06:10:25.480223", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Component 'user_api_endpoint' already has port 8466"}
INFO:autocoder_cc.core.port_registry:Component 'user_api_endpoint' already has port 8466
{"timestamp": "2025-08-25T06:10:25.480310", "level": "INFO", "logger_name": "autocoder_cc.core.port_registry", "message": "Allocated port 49906 for metrics (None)"}
INFO:autocoder_cc.core.port_registry:Allocated port 49906 for metrics (None)
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
WARNING:autocoder_cc.blueprint_language.database_config_manager:Removing legacy database field: storage_type
[32m06:10:25 - INFO -     📄 Generated: main.py[0m
INFO:VerboseAutocoder:    📄 Generated: main.py
[32m06:10:25 - INFO -        📏 Size: 11164 chars, 280 lines[0m
INFO:VerboseAutocoder:       📏 Size: 11164 chars, 280 lines
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
[32m06:10:25 - INFO -     📄 Generated: config/system_config.yaml[0m
INFO:VerboseAutocoder:    📄 Generated: config/system_config.yaml
[32m06:10:25 - INFO -        📏 Size: 1190 chars, 58 lines[0m
INFO:VerboseAutocoder:       📏 Size: 1190 chars, 58 lines
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
DEBUG:VerboseAutocoder:           20:     user_store:
DEBUG:VerboseAutocoder:          ... (39 more lines)
[32m06:10:25 - INFO -     📄 Generated: requirements.txt[0m
INFO:VerboseAutocoder:    📄 Generated: requirements.txt
[32m06:10:25 - INFO -        📏 Size: 226 chars, 11 lines[0m
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
[32m06:10:25 - INFO -     📄 Generated: Dockerfile[0m
INFO:VerboseAutocoder:    📄 Generated: Dockerfile
[32m06:10:25 - INFO -        📏 Size: 939 chars, 35 lines[0m
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
[32m06:10:25 - INFO -   ✅ Generate System Scaffold (⏱️ 0.01s)[0m
INFO:VerboseAutocoder:  ✅ Generate System Scaffold (⏱️ 0.01s)
[32m06:10:25 - INFO -   ▶️  Generate Database Schema Artifacts[0m
INFO:VerboseAutocoder:  ▶️  Generate Database Schema Artifacts
{"timestamp": "2025-08-25T06:10:25.494016", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Generated 2 database schema files"}
INFO:VersionedSchemaManager:✅ Generated 2 database schema files
[32m06:10:25 - INFO - ✅ Generated 2 schema artifacts[0m
INFO:VerboseAutocoder:✅ Generated 2 schema artifacts
[32m06:10:25 - INFO -     📄 Generated: database/schema_v1_0_0.sql[0m
INFO:VerboseAutocoder:    📄 Generated: database/schema_v1_0_0.sql
[32m06:10:25 - INFO -        📏 Size: 592 chars, 18 lines[0m
INFO:VerboseAutocoder:       📏 Size: 592 chars, 18 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: -- Generated Database Schema
DEBUG:VerboseAutocoder:            2: -- Schema Version: 1.0.0
DEBUG:VerboseAutocoder:            3: -- Generated: 2025-07-15
DEBUG:VerboseAutocoder:            4: 
DEBUG:VerboseAutocoder:            5: -- Enable UUID extension
DEBUG:VerboseAutocoder:            6: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DEBUG:VerboseAutocoder:            7: 
DEBUG:VerboseAutocoder:            8: -- Table for user_store component
DEBUG:VerboseAutocoder:            9: CREATE TABLE user_store_data (
DEBUG:VerboseAutocoder:           10:     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
DEBUG:VerboseAutocoder:           11:     data JSONB NOT NULL,
DEBUG:VerboseAutocoder:           12:     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
DEBUG:VerboseAutocoder:           13:     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
DEBUG:VerboseAutocoder:           14: );
DEBUG:VerboseAutocoder:           15: 
DEBUG:VerboseAutocoder:           16: -- Index for efficient querying
DEBUG:VerboseAutocoder:           17: CREATE INDEX idx_user_store_data_created_at ON user_store_data (created_at);
DEBUG:VerboseAutocoder:           18: CREATE INDEX idx_user_store_data_data_gin ON user_store_data USING gin(data);
DEBUG:VerboseAutocoder:           19: 
[32m06:10:25 - INFO -     📄 Generated: database/migration_metadata.json[0m
INFO:VerboseAutocoder:    📄 Generated: database/migration_metadata.json
[32m06:10:25 - INFO -        📏 Size: 163 chars, 7 lines[0m
INFO:VerboseAutocoder:       📏 Size: 163 chars, 7 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: database_schema
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: {
DEBUG:VerboseAutocoder:            2:   "current_version": "1.0.0",
DEBUG:VerboseAutocoder:            3:   "generated_at": "2025-07-15T16:00:00Z",
DEBUG:VerboseAutocoder:            4:   "blueprint_hash": "2ff458c9f64c0150",
DEBUG:VerboseAutocoder:            5:   "schema_files": [
DEBUG:VerboseAutocoder:            6:     "schema_v1_0_0.sql"
DEBUG:VerboseAutocoder:            7:   ]
DEBUG:VerboseAutocoder:            8: }
[32m06:10:25 - INFO -   ✅ Generate Database Schema Artifacts (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Database Schema Artifacts (⏱️ 0.00s)
[32m06:10:25 - INFO -   ▶️  Generate Service Communication Configuration[0m
INFO:VerboseAutocoder:  ▶️  Generate Service Communication Configuration
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 1: Trying gemini/gemini-2.5-flash
{"timestamp": "2025-08-25T06:10:25.497270", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)"}
INFO:autocoder_cc.core.timeout_manager:TimeoutManager initialized with config: TimeoutConfig(health_check=inf, llm_generation=inf, component_generation=inf, system_validation=inf, blueprint_processing=inf, resource_allocation=inf)
{"timestamp": "2025-08-25T06:10:25.497362", "level": "INFO", "logger_name": "autocoder_cc.core.timeout_manager", "message": "Global TimeoutManager instance created"}
INFO:autocoder_cc.core.timeout_manager:Global TimeoutManager instance created
[92m06:10:25 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
INFO:LiteLLM:
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
WARNING:autocoder_cc.llm_providers.unified_llm_provider:❌ Error with gemini/gemini-2.5-flash: LLM returned empty content (None) from gemini/gemini-2.5-flash
INFO:autocoder_cc.llm_providers.unified_llm_provider:Attempt 2: Trying gpt-4o-mini
[92m06:10:32 - LiteLLM:INFO[0m: utils.py:3260 - 
LiteLLM completion() model= gpt-4o-mini; provider = openai
INFO:LiteLLM:
LiteLLM completion() model= gpt-4o-mini; provider = openai
INFO:autocoder_cc.llm_providers.unified_llm_provider:✅ Success with gpt-4o-mini in 7.60s
{"timestamp": "2025-08-25T06:10:33.099822", "level": "INFO", "logger_name": "system_generator", "message": "Messaging type selected using LLM intelligence", "component": "SystemGenerator", "operation": "_determine_messaging_type", "tags": {"selected_type": "http", "component_count": 3, "method": "llm_intelligent"}}
INFO:system_generator:Messaging type selected using LLM intelligence
[32m06:10:33 - INFO - ✅ Generated service communication configuration[0m
INFO:VerboseAutocoder:✅ Generated service communication configuration
[32m06:10:33 - INFO -     📄 Generated: config/messaging_config.yaml[0m
INFO:VerboseAutocoder:    📄 Generated: config/messaging_config.yaml
[32m06:10:33 - INFO -        📏 Size: 2617 chars, 96 lines[0m
INFO:VerboseAutocoder:       📏 Size: 2617 chars, 96 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: messaging_configuration
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: messaging:
DEBUG:VerboseAutocoder:            2:   connection:
DEBUG:VerboseAutocoder:            3:     base_url: ${HTTP_BASE_URL:http://localhost:8080}
DEBUG:VerboseAutocoder:            4:     max_retries: ${HTTP_MAX_RETRIES:3}
DEBUG:VerboseAutocoder:            5:     timeout: ${HTTP_TIMEOUT:30}
DEBUG:VerboseAutocoder:            6:   queues:
DEBUG:VerboseAutocoder:            7:     user_api_endpoint_input:
DEBUG:VerboseAutocoder:            8:       auto_delete: false
DEBUG:VerboseAutocoder:            9:       durable: true
DEBUG:VerboseAutocoder:           10:       max_length: 10000
DEBUG:VerboseAutocoder:           11:       message_ttl: 3600000
DEBUG:VerboseAutocoder:           12:       routing_key: user_api_endpoint.input
DEBUG:VerboseAutocoder:           13:     user_api_endpoint_output:
DEBUG:VerboseAutocoder:           14:       auto_delete: false
DEBUG:VerboseAutocoder:           15:       durable: true
DEBUG:VerboseAutocoder:           16:       max_length: 10000
DEBUG:VerboseAutocoder:           17:       message_ttl: 3600000
DEBUG:VerboseAutocoder:           18:       routing_key: user_api_endpoint.output
DEBUG:VerboseAutocoder:           19:     user_controller_input:
DEBUG:VerboseAutocoder:           20:       auto_delete: false
DEBUG:VerboseAutocoder:          ... (77 more lines)
[32m06:10:33 - INFO -   ✅ Generate Service Communication Configuration (⏱️ 7.61s)[0m
INFO:VerboseAutocoder:  ✅ Generate Service Communication Configuration (⏱️ 7.61s)
[32m06:10:33 - INFO -   ▶️  Generate Shared Observability Module[0m
INFO:VerboseAutocoder:  ▶️  Generate Shared Observability Module
[32m06:10:33 - INFO -     📄 Generated: observability.py[0m
INFO:VerboseAutocoder:    📄 Generated: observability.py
[32m06:10:33 - INFO -        📏 Size: 14005 chars, 365 lines[0m
INFO:VerboseAutocoder:       📏 Size: 14005 chars, 365 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: shared_module
DEBUG:VerboseAutocoder:       🏷️  component_count: 3
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Shared Observability Module for user_data_api_system
DEBUG:VerboseAutocoder:            4: ============================================
DEBUG:VerboseAutocoder:            5: 
DEBUG:VerboseAutocoder:            6: Generated by ObservabilityGenerator on 2025-08-25 06:10:33
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
[32m06:10:33 - INFO - ✅ Generated shared observability module: test_e2e_output/scaffolds/user_data_api_system/components/observability.py[0m
INFO:VerboseAutocoder:✅ Generated shared observability module: test_e2e_output/scaffolds/user_data_api_system/components/observability.py
[32m06:10:33 - INFO - 📏 Observability module: 14005 chars, 365 lines[0m
INFO:VerboseAutocoder:📏 Observability module: 14005 chars, 365 lines
[32m06:10:33 - INFO -   ✅ Generate Shared Observability Module (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Shared Observability Module (⏱️ 0.00s)
[32m06:10:33 - INFO -   ▶️  Generate Communication Framework[0m
INFO:VerboseAutocoder:  ▶️  Generate Communication Framework
[32m06:10:33 - INFO -     📄 Generated: communication.py[0m
INFO:VerboseAutocoder:    📄 Generated: communication.py
[32m06:10:33 - INFO -        📏 Size: 14659 chars, 386 lines[0m
INFO:VerboseAutocoder:       📏 Size: 14659 chars, 386 lines
DEBUG:VerboseAutocoder:       🏷️  file_type: communication_framework
DEBUG:VerboseAutocoder:       🏷️  bindings_count: 6
DEBUG:VerboseAutocoder:       📝 Content:
DEBUG:VerboseAutocoder:            1: #!/usr/bin/env python3
DEBUG:VerboseAutocoder:            2: """
DEBUG:VerboseAutocoder:            3: Component Communication Framework for user_data_api_system
DEBUG:VerboseAutocoder:            4: ==================================================
DEBUG:VerboseAutocoder:            5: 
DEBUG:VerboseAutocoder:            6: Generated by ComponentCommunicationGenerator on 2025-08-25 06:10:33
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
[32m06:10:33 - INFO - ✅ Generated communication framework: test_e2e_output/scaffolds/user_data_api_system/components/communication.py[0m
INFO:VerboseAutocoder:✅ Generated communication framework: test_e2e_output/scaffolds/user_data_api_system/components/communication.py
[32m06:10:33 - INFO - 📏 Communication module: 14659 chars, 386 lines[0m
INFO:VerboseAutocoder:📏 Communication module: 14659 chars, 386 lines
[32m06:10:33 - INFO - 🔗 Configured 6 component bindings for runtime routing[0m
INFO:VerboseAutocoder:🔗 Configured 6 component bindings for runtime routing
[32m06:10:33 - INFO -   ✅ Generate Communication Framework (⏱️ 0.00s)[0m
INFO:VerboseAutocoder:  ✅ Generate Communication Framework (⏱️ 0.00s)
[32m06:10:33 - INFO -   ▶️  Generate Component Implementations with Self-Healing[0m
INFO:VerboseAutocoder:  ▶️  Generate Component Implementations with Self-Healing
{"timestamp": "2025-08-25T06:10:33.113536", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "🚀 Starting integrated system generation with healing"}
INFO:HealingIntegratedGenerator:🚀 Starting integrated system generation with healing
{"timestamp": "2025-08-25T06:10:33.113627", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "📋 Parsing system blueprint..."}
INFO:HealingIntegratedGenerator:📋 Parsing system blueprint...
{"timestamp": "2025-08-25T06:10:33.122086", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-25T06:10:33.122294", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-25T06:10:33.122384", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-25T06:10:33.122466", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_api_endpoint.request → user_store.query"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_api_endpoint.request → user_store.query
{"timestamp": "2025-08-25T06:10:33.122537", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_store.response → user_api_endpoint.data"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_store.response → user_api_endpoint.data
{"timestamp": "2025-08-25T06:10:33.122611", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_api_endpoint.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_api_endpoint.control
{"timestamp": "2025-08-25T06:10:33.122687", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: user_controller.control → user_store.control"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: user_controller.control → user_store.control
{"timestamp": "2025-08-25T06:10:33.122734", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 4 missing bindings
{"timestamp": "2025-08-25T06:10:33.122914", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 4 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 4 missing bindings
{"timestamp": "2025-08-25T06:10:33.122998", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T06:10:33.123164", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 3}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T06:10:33.123291", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 3}}
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: user_data_api_system
WARNING:autocoder_cc.blueprint_language.architectural_validator:role_delta name=user_api_endpoint declared=SINK effective=TRANSFORMER reasons=['declared=SINK', 'outputs present (R1)']
INFO:autocoder_cc.blueprint_language.architectural_validator:Detected API-based architecture pattern - relaxed source validation
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T06:10:33.125567", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   Blueprint parsed in 0.01s"}
INFO:HealingIntegratedGenerator:   Blueprint parsed in 0.01s
{"timestamp": "2025-08-25T06:10:33.125677", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "🔧 Starting component generation and validation loop..."}
INFO:HealingIntegratedGenerator:🔧 Starting component generation and validation loop...
{"timestamp": "2025-08-25T06:10:33.125778", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "\n🔄 Component validation attempt 1"}
INFO:HealingIntegratedGenerator:
🔄 Component validation attempt 1
{"timestamp": "2025-08-25T06:10:33.125854", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   🔧 Generating components..."}
INFO:HealingIntegratedGenerator:   🔧 Generating components...
{"timestamp": "2025-08-25T06:10:33.125909", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   Generating 3 components..."}
INFO:HealingIntegratedGenerator:   Generating 3 components...
{"timestamp": "2025-08-25T06:10:33.126001", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Using recipe 'APIEndpoint' for user_api_endpoint"}
INFO:HealingIntegratedGenerator:     Using recipe 'APIEndpoint' for user_api_endpoint
{"timestamp": "2025-08-25T06:10:33.126188", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     ✅ Generated user_api_endpoint from recipe"}
INFO:HealingIntegratedGenerator:     ✅ Generated user_api_endpoint from recipe
{"timestamp": "2025-08-25T06:10:33.126290", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Using recipe 'Controller' for user_controller"}
INFO:HealingIntegratedGenerator:     Using recipe 'Controller' for user_controller
{"timestamp": "2025-08-25T06:10:33.126460", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     ✅ Generated user_controller from recipe"}
INFO:HealingIntegratedGenerator:     ✅ Generated user_controller from recipe
{"timestamp": "2025-08-25T06:10:33.126559", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     Using recipe 'Store' for user_store"}
INFO:HealingIntegratedGenerator:     Using recipe 'Store' for user_store
{"timestamp": "2025-08-25T06:10:33.126712", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "     ✅ Generated user_store from recipe"}
INFO:HealingIntegratedGenerator:     ✅ Generated user_store from recipe
{"timestamp": "2025-08-25T06:10:33.126827", "level": "WARNING", "logger_name": "HealingIntegratedGenerator", "message": "Could not find system directory for creating __init__.py files"}
WARNING:HealingIntegratedGenerator:Could not find system directory for creating __init__.py files
{"timestamp": "2025-08-25T06:10:33.126897", "level": "INFO", "logger_name": "HealingIntegratedGenerator", "message": "   🚦 Running validation gate..."}
INFO:HealingIntegratedGenerator:   🚦 Running validation gate...
{"timestamp": "2025-08-25T06:10:33.126974", "level": "ERROR", "logger_name": "HealingIntegratedGenerator", "message": "💥 Pipeline failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'"}
ERROR:HealingIntegratedGenerator:💥 Pipeline failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
🔍 DEBUG VALIDATION - Component role analysis:
  user_api_endpoint: APIEndpoint → SINK → TRANSFORMER (in=2, out=2)
  user_controller: Controller → TRANSFORMER → TRANSFORMER (in=1, out=2)
  user_store: Store → SINK → SINK (in=2, out=1)
🔍 DEBUG VALIDATION - Sources: set()
🔍 DEBUG VALIDATION - Sinks: {'user_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=True
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True
[31m06:10:33 - ERROR - ❌ Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'[0m
ERROR:VerboseAutocoder:❌ Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
[31m06:10:33 - ERROR -   ❌ Generate Component Implementations with Self-Healing FAILED (⏱️ 0.02s)[0m
ERROR:VerboseAutocoder:  ❌ Generate Component Implementations with Self-Healing FAILED (⏱️ 0.02s)
[31m06:10:33 - ERROR -      💥 Error: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'[0m
ERROR:VerboseAutocoder:     💥 Error: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
DEBUG:VerboseAutocoder:     📜 Stack trace:
DEBUG:VerboseAutocoder:        Traceback (most recent call last):
DEBUG:VerboseAutocoder:          File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 509, in _generate_system_with_logging
    raise RuntimeError(error_msg)
DEBUG:VerboseAutocoder:        RuntimeError: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
[31m06:10:33 - ERROR - ❌ Generate System: user_data_api_system FAILED (⏱️ 7.65s)[0m
ERROR:VerboseAutocoder:❌ Generate System: user_data_api_system FAILED (⏱️ 7.65s)
[31m06:10:33 - ERROR -    💥 Error: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'[0m
ERROR:VerboseAutocoder:   💥 Error: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
DEBUG:VerboseAutocoder:   📜 Stack trace:
DEBUG:VerboseAutocoder:      Traceback (most recent call last):
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 244, in _generate_system_from_blueprint
    result = await self._generate_system_with_logging(system_blueprint)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DEBUG:VerboseAutocoder:        File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 509, in _generate_system_with_logging
    raise RuntimeError(error_msg)
DEBUG:VerboseAutocoder:      RuntimeError: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
Traceback (most recent call last):
  File "/home/brian/projects/autocoder4_cc/test_e2e_generation.py", line 55, in <module>
    test_e2e_generation()
  File "/home/brian/projects/autocoder4_cc/test_e2e_generation.py", line 16, in test_e2e_generation
    result = generate_system_from_description(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/natural_language_to_blueprint.py", line 1181, in generate_system_from_description
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
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/natural_language_to_blueprint.py", line 1179, in run_generation
    return await generator.generate_system_from_yaml(blueprint_yaml)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 232, in generate_system_from_yaml
    return await self._generate_system_from_blueprint(system_blueprint)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 244, in _generate_system_from_blueprint
    result = await self._generate_system_with_logging(system_blueprint)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brian/projects/autocoder4_cc/autocoder_cc/blueprint_language/system_generator.py", line 509, in _generate_system_with_logging
    raise RuntimeError(error_msg)
RuntimeError: Component generation with healing failed: 'IntegrationValidationGate' object has no attribute 'validate_components_for_system_generation'
