LLM call attempt 1/6
LLM call attempt 1/6
{"timestamp": "2025-08-24T22:04:30.836624", "level": "INFO", "logger_name": "SelfHealingSystem", "message": "LLM component generator initialized for healing"}
INFO:SelfHealingSystem:LLM component generator initialized for healing
{"timestamp": "2025-08-24T22:04:30.859202", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 1/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 1/4
{"timestamp": "2025-08-24T22:04:30.859358", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-24T22:04:30.859459", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-24T22:04:30.859589", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated binding: monitoring_service.output → alert_handler.input"}
INFO:autocoder_cc.healing.blueprint_healer:Generated binding: monitoring_service.output → alert_handler.input
{"timestamp": "2025-08-24T22:04:30.859687", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 1 missing bindings
{"timestamp": "2025-08-24T22:04:30.859826", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed with 1 operations: Generated 1 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Blueprint healing completed with 1 operations: Generated 1 missing bindings
INFO:autocoder_cc.blueprint_language.architectural_validator:Architectural validation completed: 0 errors, 0 warnings
{"timestamp": "2025-08-24T22:04:30.861499", "level": "WARNING", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint validation failed with 1 errors, attempting healing:"}
WARNING:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint validation failed with 1 errors, attempting healing:
{"timestamp": "2025-08-24T22:04:30.861693", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Blueprint parsing attempt 2/4"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Blueprint parsing attempt 2/4
{"timestamp": "2025-08-24T22:04:30.861779", "level": "INFO", "logger_name": "autocoder_cc.blueprint_language.system_blueprint_parser", "message": "Applying healing for attempt 2"}
INFO:autocoder_cc.blueprint_language.system_blueprint_parser:Applying healing for attempt 2
{"timestamp": "2025-08-24T22:04:30.861864", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Starting blueprint healing process"}
INFO:autocoder_cc.healing.blueprint_healer:Starting blueprint healing process
{"timestamp": "2025-08-24T22:04:30.861949", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Analyzing 3 components for missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Analyzing 3 components for missing bindings
{"timestamp": "2025-08-24T22:04:30.862037", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Generated 0 missing bindings"}
INFO:autocoder_cc.healing.blueprint_healer:Generated 0 missing bindings
{"timestamp": "2025-08-24T22:04:30.862157", "level": "INFO", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Blueprint healing completed - no issues found"}
