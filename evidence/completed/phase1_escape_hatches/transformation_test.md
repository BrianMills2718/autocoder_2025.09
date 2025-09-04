INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T11:01:51.818793", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T11:01:51.818884", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T11:01:51.818961", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 2/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
{"timestamp": "2025-08-25T11:01:51.819039", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 2"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
{"timestamp": "2025-08-25T11:01:51.819118", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
--
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T11:01:51.820015", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T11:01:51.820100", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T11:01:51.820186", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 3/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 3/4
{"timestamp": "2025-08-25T11:01:51.820265", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 3"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 3
{"timestamp": "2025-08-25T11:01:51.820341", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
--
INFO:port_auto_generator:Port auto-generation completed
INFO:autocoder_cc.blueprint_language.architectural_validator:Starting architectural validation for system: event_logger_system
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-25T11:01:51.821291", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-25T11:01:51.821359", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)
{"timestamp": "2025-08-25T11:01:51.821427", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 4/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 4/4
{"timestamp": "2025-08-25T11:01:51.821473", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 4
{"timestamp": "2025-08-25T11:01:51.821530", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
--
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True

❌ Generation error: System blueprint validation failed after 4 attempts with 1 errors
  binding.schema_compatibility: Schema mismatch without transformation: event_source.output (common_object_schema) → event_store.input (ItemSchema)

============================================================
❌ STUB PREVENTION TEST FAILED
============================================================
