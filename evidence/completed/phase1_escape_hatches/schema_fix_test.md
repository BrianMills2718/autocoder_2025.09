{"timestamp": "2025-08-25T11:00:52.511964", "level": "ERROR", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Maximum stagnation count reached - stopping healing to prevent infinite loops"}
ERROR:autocoder_cc.healing.blueprint_healer:Maximum stagnation count reached - stopping healing to prevent infinite loops
{"timestamp": "2025-08-25T11:00:52.512053", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed - no issues found
{"timestamp": "2025-08-25T11:00:52.512133", "level": "INFO", "logger_name": "VersionedSchemaManager", "message": "✅ Schema version validation passed: 1.0.0"}
INFO:VersionedSchemaManager:✅ Schema version validation passed: 1.0.0
{"timestamp": "2025-08-25T11:00:52.512252", "level": "INFO", "logger_name": "port_auto_generator", "message": "Starting port auto-generation", "component": "ComponentPortAutoGenerator", "operation": "auto_generate_ports", "tags": {"component_count": 2}}
INFO:port_auto_generator:Starting port auto-generation
{"timestamp": "2025-08-25T11:00:52.512348", "level": "INFO", "logger_name": "port_auto_generator", "message": "Port auto-generation completed", "component": "ComponentPortAutoGenerator", "operation": "ports_generated", "tags": {"components_modified": 1}}
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
