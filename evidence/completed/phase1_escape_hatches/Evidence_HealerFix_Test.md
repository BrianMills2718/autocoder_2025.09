[1m=================================================== test session starts ===================================================[0m
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/brian/projects/autocoder4_cc
configfile: pytest.ini
plugins: cov-6.2.1, anyio-4.9.0, asyncio-1.1.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0m{"timestamp": "2025-08-24T22:02:21.975194", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-24T22:02:21.975511", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-24T22:02:21.975657", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-24T22:02:21.975774", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-24T22:02:21.975886", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-24T22:02:21.976012", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-24T22:02:21.976123", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-24T22:02:21.976335", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-24T22:02:21.976456", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-24T22:02:21.976573", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-24T22:02:21.976682", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-24T22:02:21.976795", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-24T22:02:21.976928", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-24T22:02:21.977035", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-24T22:02:21.977143", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-24T22:02:29.851220", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-24T22:02:29.851383", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-24T22:02:29.855146", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:02:29.859044", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-24T22:02:29.859182", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-24T22:02:29.859299", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-24T22:02:29.859413", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-24T22:02:29.859516", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-24T22:02:29.859617", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:02:29.860350", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:02:29.863370", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
collected 6 items

tests/test_healer_matrix_compliance.py::test_healer_respects_matrix [32mPASSED[0m
tests/test_healer_matrix_compliance.py::test_healer_prevents_duplicates [32mPASSED[0m
tests/test_healer_matrix_compliance.py::test_healer_rejects_invalid_connections [32mPASSED[0m
tests/test_healer_matrix_compliance.py::test_healer_stagnation_detection {"timestamp": "2025-08-24T22:02:29.967023", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Healing stagnated after 2 attempts"}
{"timestamp": "2025-08-24T22:02:29.967223", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Detected healing loop - repeating same operations"}
{"timestamp": "2025-08-24T22:02:29.967357", "level": "WARNING", "logger_name": "autocoder_cc.healing.blueprint_healer", "message": "Detected healing loop - repeating same operations"}
[31mFAILED[0m

======================================================== FAILURES =========================================================
[31m[1m____________________________________________ test_healer_stagnation_detection _____________________________________________[0m
[1m[31mtests/test_healer_matrix_compliance.py[0m:71: in test_healer_stagnation_detection
    [0m[94massert[39;49;00m healer2._is_stagnating(ops) [95mis[39;49;00m [94mTrue[39;49;00m, [33m"[39;49;00m[33mThird identical operations should detect loop[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   AssertionError: Third identical operations should detect loop[0m
[1m[31mE   assert False is True[0m
[1m[31mE    +  where False = _is_stagnating(['Fixed schema_version', 'Added policy'])[0m
[1m[31mE    +    where _is_stagnating = <autocoder_cc.healing.blueprint_healer.BlueprintHealer object at 0x757a76ded820>._is_stagnating[0m
---------------------------------------------------- Captured log call ----------------------------------------------------
[33mWARNING [0m autocoder_cc.healing.blueprint_healer:structured_logging.py:194 Healing stagnated after 2 attempts
[33mWARNING [0m autocoder_cc.healing.blueprint_healer:structured_logging.py:194 Detected healing loop - repeating same operations
[33mWARNING [0m autocoder_cc.healing.blueprint_healer:structured_logging.py:194 Detected healing loop - repeating same operations
[36m[1m================================================= short test summary info =================================================[0m
[31mFAILED[0m tests/test_healer_matrix_compliance.py::[1mtest_healer_stagnation_detection[0m - AssertionError: Third identical operations should detect loop
assert False is True
 +  where False = _is_stagnating(['Fixed schema_version', 'Added policy'])
 +    where _is_stagnating = <autocoder_cc.healing.blueprint_healer.BlueprintHealer object at 0x757a76ded820>._is_stagnating
[31m!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!![0m
[31m======================================== [31m[1m1 failed[0m, [32m3 passed[0m, [33m56 warnings[0m[31m in 11.35s[0m[31m ========================================[0m
