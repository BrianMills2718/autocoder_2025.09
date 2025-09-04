[1m=================================================== test session starts ===================================================[0m
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/brian/projects/autocoder4_cc
configfile: pytest.ini
plugins: cov-6.2.1, anyio-4.9.0, asyncio-1.1.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0m{"timestamp": "2025-08-24T21:59:34.329653", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-24T21:59:34.330004", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-24T21:59:34.330140", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-24T21:59:34.330256", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-24T21:59:34.330368", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-24T21:59:34.330479", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-24T21:59:34.330592", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-24T21:59:34.330819", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-24T21:59:34.330938", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-24T21:59:34.331050", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-24T21:59:34.331161", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-24T21:59:34.331276", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-24T21:59:34.331386", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-24T21:59:34.331492", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-24T21:59:34.331599", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-24T21:59:42.209825", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-24T21:59:42.209997", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-24T21:59:42.213715", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-24T21:59:42.217694", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-24T21:59:42.217844", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-24T21:59:42.217970", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-24T21:59:42.218087", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-24T21:59:42.218194", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-24T21:59:42.218299", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T21:59:42.219067", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T21:59:42.222310", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
collected 6 items

tests/test_connectivity_matrix_integrity.py::test_connectivity_matrix_symmetry [31mFAILED[0m

======================================================== FAILURES =========================================================
[31m[1m____________________________________________ test_connectivity_matrix_symmetry ____________________________________________[0m
[1m[31mtests/test_connectivity_matrix_integrity.py[0m:17: in test_connectivity_matrix_symmetry
    [0m[94massert[39;49;00m [95mnot[39;49;00m errors, [33mf[39;49;00m[33m"[39;49;00m[33mMatrix contradictions found:[39;49;00m[33m\n[39;49;00m[33m"[39;49;00m + [33m"[39;49;00m[33m\n[39;49;00m[33m"[39;49;00m.join(errors)[90m[39;49;00m
[1m[31mE   AssertionError: Matrix contradictions found:[0m
[1m[31mE     Filter → Transformer valid from Filter but Transformer doesn't accept from Filter[0m
[1m[31mE     Filter → Filter valid from Filter but Filter doesn't accept from Filter[0m
[1m[31mE     Filter → Router valid from Filter but Router doesn't accept from Filter[0m
[1m[31mE     Filter → Sink valid from Filter but Sink doesn't accept from Filter[0m
[1m[31mE     Filter → APIEndpoint valid from Filter but APIEndpoint doesn't accept from Filter[0m
[1m[31mE     Filter → Aggregator valid from Filter but Aggregator doesn't accept from Filter[0m
[1m[31mE     Router → Router valid from Router but Router doesn't accept from Router[0m
[1m[31mE     Router → APIEndpoint valid from Router but APIEndpoint doesn't accept from Router[0m
[1m[31mE     Aggregator → Transformer valid from Aggregator but Transformer doesn't accept from Aggregator[0m
[1m[31mE     Aggregator → Filter valid from Aggregator but Filter doesn't accept from Aggregator[0m
[1m[31mE     EventSource → Transformer valid from EventSource but Transformer doesn't accept from EventSource[0m
[1m[31mE     EventSource → Filter valid from EventSource but Filter doesn't accept from EventSource[0m
[1m[31mE     EventSource → Router valid from EventSource but Router doesn't accept from EventSource[0m
[1m[31mE     EventSource → Sink valid from EventSource but Sink doesn't accept from EventSource[0m
[1m[31mE     EventSource → Store valid from EventSource but Store doesn't accept from EventSource[0m
[1m[31mE   assert not ["Filter \u2192 Transformer valid from Filter but Transformer doesn't accept from Filter", "Filter \u2192 Filter valid from Filter but Filter doesn't accept from Filter", "Filter \u2192 Router valid from Filter but Router doesn't accept from Filter", "Filter \u2192 Sink valid from Filter but Sink doesn't accept from Filter", "Filter \u2192 APIEndpoint valid from Filter but APIEndpoint doesn't accept from Filter", "Filter \u2192 Aggregator valid from Filter but Aggregator doesn't accept from Filter", "Router \u2192 Router valid from Router but Router doesn't accept from Router", "Router \u2192 APIEndpoint valid from Router but APIEndpoint doesn't accept from Router", "Aggregator \u2192 Transformer valid from Aggregator but Transformer doesn't accept from Aggregator", "Aggregator \u2192 Filter valid from Aggregator but Filter doesn't accept from Aggregator", "EventSource \u2192 Transformer valid from EventSource but Transformer doesn't accept from EventSource", "EventSource \u2192 Filter valid from EventSource but Filter doesn't accept from EventSource", "EventSource \u2192 Router valid from EventSource but Router doesn't accept from EventSource", "EventSource \u2192 Sink valid from EventSource but Sink doesn't accept from EventSource", "EventSource \u2192 Store valid from EventSource but Store doesn't accept from EventSource"][0m
[36m[1m================================================= short test summary info =================================================[0m
[31mFAILED[0m tests/test_connectivity_matrix_integrity.py::[1mtest_connectivity_matrix_symmetry[0m - AssertionError: Matrix contradictions found:
  Filter → Transformer valid from Filter but Transformer doesn't accept from Filter
  Filter → Filter valid from Filter but Filter doesn't accept from Filter
  Filter → Router valid from Filter but Router doesn't accept from Filter
  Filter → Sink valid from Filter but Sink doesn't accept from Filter
  Filter → APIEndpoint valid from Filter but APIEndpoint doesn't accept from Filter
  Filter → Aggregator valid from Filter but Aggregator doesn't accept from Filter
  Router → Router valid from Router but Router doesn't accept from Router
  Router → APIEndpoint valid from Router but APIEndpoint doesn't accept from Router
  Aggregator → Transformer valid from Aggregator but Transformer doesn't accept from Aggregator
  Aggregator → Filter valid from Aggregator but Filter doesn't accept from Aggregator
  EventSource → Transformer valid from EventSource but Transformer doesn't accept from EventSource
  EventSource → Filter valid from EventSource but Filter doesn't accept from EventSource
  EventSource → Router valid from EventSource but Router doesn't accept from EventSource
  EventSource → Sink valid from EventSource but Sink doesn't accept from EventSource
  EventSource → Store valid from EventSource but Store doesn't accept from EventSource
assert not ["Filter \u2192 Transformer valid from Filter but Transformer doesn't accept from Filter", "Filter \u2192 Filter valid from Filter but Filter doesn't accept from Filter", "Filter \u2192 Router valid from Filter but Router doesn't accept from Filter", "Filter \u2192 Sink valid from Filter but Sink doesn't accept from Filter", "Filter \u2192 APIEndpoint valid from Filter but APIEndpoint doesn't accept from Filter", "Filter \u2192 Aggregator valid from Filter but Aggregator doesn't accept from Filter", "Router \u2192 Router valid from Router but Router doesn't accept from Router", "Router \u2192 APIEndpoint valid from Router but APIEndpoint doesn't accept from Router", "Aggregator \u2192 Transformer valid from Aggregator but Transformer doesn't accept from Aggregator", "Aggregator \u2192 Filter valid from Aggregator but Filter doesn't accept from Aggregator", "EventSource \u2192 Transformer valid from EventSource but Transformer doesn't accept from EventSource", "EventSource \u2192 Filter valid from EventSource but Filter doesn't accept from EventSource", "EventSource \u2192 Router valid from EventSource but Router doesn't accept from EventSource", "EventSource \u2192 Sink valid from EventSource but Sink doesn't accept from EventSource", "EventSource \u2192 Store valid from EventSource but Store doesn't accept from EventSource"]
[31m!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!![0m
[31m============================================= [31m[1m1 failed[0m, [33m56 warnings[0m[31m in 11.36s[0m[31m =============================================[0m
[1m=================================================== test session starts ===================================================[0m
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/brian/projects/autocoder4_cc
configfile: pytest.ini
plugins: cov-6.2.1, anyio-4.9.0, asyncio-1.1.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0m{"timestamp": "2025-08-24T22:00:38.481949", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Source"}
{"timestamp": "2025-08-24T22:00:38.482328", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Transformer"}
{"timestamp": "2025-08-24T22:00:38.482466", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: StreamProcessor"}
{"timestamp": "2025-08-24T22:00:38.482565", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Sink"}
{"timestamp": "2025-08-24T22:00:38.482677", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Store"}
{"timestamp": "2025-08-24T22:00:38.482790", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Controller"}
{"timestamp": "2025-08-24T22:00:38.482895", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: APIEndpoint"}
{"timestamp": "2025-08-24T22:00:38.483112", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Model"}
{"timestamp": "2025-08-24T22:00:38.483230", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Accumulator"}
{"timestamp": "2025-08-24T22:00:38.483344", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Router"}
{"timestamp": "2025-08-24T22:00:38.483456", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Aggregator"}
{"timestamp": "2025-08-24T22:00:38.483571", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: Filter"}
{"timestamp": "2025-08-24T22:00:38.483681", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Registered component class: WebSocket"}
{"timestamp": "2025-08-24T22:00:38.483788", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Built-in ComposedComponent types registered with capability-based composition"}
{"timestamp": "2025-08-24T22:00:38.483954", "level": "INFO", "logger_name": "ComponentRegistry", "message": "✅ Component Registry initialized with fail-hard validation and policy enforcement"}
{"timestamp": "2025-08-24T22:00:46.366694", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Registered 3 predefined templates"}
{"timestamp": "2025-08-24T22:00:46.366862", "level": "INFO", "logger_name": "SecureTemplateSystem", "message": "✅ Secure Template System initialized with AST-based fail-hard security validation"}
{"timestamp": "2025-08-24T22:00:46.370834", "level": "INFO", "logger_name": "NaturalLanguageParser", "message": "✅ Natural Language Parser initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:00:46.375270", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: ComponentData"}
{"timestamp": "2025-08-24T22:00:46.375503", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SourceData"}
{"timestamp": "2025-08-24T22:00:46.375645", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: TransformerData"}
{"timestamp": "2025-08-24T22:00:46.375768", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Registered schema: SinkData"}
{"timestamp": "2025-08-24T22:00:46.375880", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Built-in schemas registered"}
{"timestamp": "2025-08-24T22:00:46.375989", "level": "INFO", "logger_name": "SchemaValidator", "message": "✅ Schema Validator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:00:46.377072", "level": "INFO", "logger_name": "SchemaAwareComponentGenerator", "message": "✅ Schema-Aware Component Generator initialized with fail-hard validation"}
{"timestamp": "2025-08-24T22:00:46.379979", "level": "INFO", "logger_name": "PropertyTestGenerator", "message": "✅ Property Test Generator initialized with fail-hard validation"}
collected 1 item

tests/test_connectivity_matrix_integrity.py::test_connectivity_matrix_symmetry [32mPASSED[0m[31m[1m
ERROR: Coverage failure: total of 9 is less than fail-under=10
[0m

===================================================== tests coverage ======================================================
_____________________________________ coverage: platform linux, python 3.12.3-final-0 _____________________________________

Name                                                                                               Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------------------------------------------------------------
autocoder_cc/__init__.py                                                                               3      0   100%
autocoder_cc/analysis/__init__.py                                                                      4      0   100%
autocoder_cc/analysis/ast_parser.py                                                                  584    504    14%   236-242, 249-255, 260-264, 269-273, 278-359, 363-375, 379-404, 408-433, 437-449, 453-517, 521-550, 565-570, 583-604, 609-635, 641-656, 665-675, 680-707, 716-733, 738-764, 769-790, 805, 818-841, 845-862, 866-905, 909-923, 927-945, 950-967, 982, 995-1005, 1009-1024, 1028-1038, 1042-1052, 1056-1077, 1081-1102, 1106-1125, 1129-1157, 1161-1175, 1179-1197, 1216-1265, 1283-1291, 1304-1311, 1326-1342, 1352-1369
autocoder_cc/analysis/function_analyzer.py                                                            21     14    33%   12, 16-24, 28-36, 41-47
autocoder_cc/analysis/import_analyzer.py                                                              22     15    32%   12-13, 17-19, 23-25, 30-36
autocoder_cc/autocoder/security/__init__.py                                                            5      0   100%
autocoder_cc/autocoder/security/decorators.py                                                        114     91    20%   33-36, 40, 45-57, 69-125, 141-169, 181-209, 221-249, 267-280
autocoder_cc/autocoder/security/filesystem_manager.py                                                 63     42    33%   31, 36, 52-67, 71-74, 81-84, 96-126, 130-132
autocoder_cc/autocoder/security/models.py                                                             78     25    68%   33, 36, 48-62, 107, 111, 115-128
autocoder_cc/autocoder/security/process_executor.py                                                   43     23    47%   39, 55-82, 89-91, 100, 113-129
autocoder_cc/autocoder/security/rbac_generator.py                                                     50     39    22%   30-49, 53-84, 88-134, 138-171, 175
autocoder_cc/autocoder/security/sealed_secrets.py                                                    267    217    19%   70-88, 128-148, 163-182, 187-207, 211-222, 227-228, 250-283, 287-368, 372-396, 403-461, 468-503, 514-539, 543-569, 593-690, 707-785, 795-820, 839-886
autocoder_cc/blueprint_language/__init__.py                                                            8      0   100%
autocoder_cc/blueprint_language/adaptive_test_generator.py                                           130    130     0%   2-261
autocoder_cc/blueprint_language/architectural_templates/messaging/rabbitmq_component_template.py       9      3    67%   163, 167, 171
autocoder_cc/blueprint_language/architectural_templates/security/secure_compose_template.py           15     10    33%   160, 168, 176-195
autocoder_cc/blueprint_language/architectural_templates/template_selector.py                          68     55    19%   17-29, 33-62, 67-88, 92-94, 98-100, 104-107, 111-150
autocoder_cc/blueprint_language/architectural_validator.py                                           338    267    21%   173-193, 197-215, 220-256, 268-278, 283-374, 384-524, 540-572, 583-601, 611-633, 637-646, 650-658, 662-669, 673-680, 686, 691, 696, 701, 706-724, 734-761, 771-774, 778-781, 793-799
autocoder_cc/blueprint_language/architecture_blueprint_parser.py                                     339    262    23%   82-83, 87-112, 116-136, 142-188, 194-223, 233-274, 279-330, 336-398, 412-430, 435-445, 457-516, 528-559, 570-585, 591-621, 631-647, 657-677, 687-699, 704-729, 733-784, 787
autocoder_cc/blueprint_language/ast_self_healing.py                                                  703    627    11%   88-180, 185-206, 211-230, 234-385, 390-416, 421-448, 453-522, 529-550, 557-567, 573-597, 611-670, 675-692, 697-729, 734-764, 771-818, 823-831, 838, 846-982, 990, 1021-1076, 1081-1170, 1187-1205, 1222-1278, 1285-1348, 1355-1541, 1548-1594, 1600-1620, 1624-1625
autocoder_cc/blueprint_language/blueprint_compliance_engine.py                                       205    205     0%   6-441
autocoder_cc/blueprint_language/blueprint_parser.py                                                  330    248    25%   108-117, 121-137, 141-165, 169-182, 186-204, 208-261, 269-273, 278-366, 372-404, 408-418, 423-496, 502-532, 536-540, 546-575, 585-673, 677-700, 703
autocoder_cc/blueprint_language/component_introspector.py                                             87     87     0%   2-194
autocoder_cc/blueprint_language/component_logic_generator.py                                         845    791     6%   69-86, 96-126, 130-181, 189-225, 234-253, 259, 263-315, 321-385, 391-411, 416-474, 481-492, 503-569, 580-650, 659-694, 713-950, 955-1026, 1037-1169, 1192-1350, 1356-1388, 1393-1590, 1595-1620, 1625-1681, 1685-1700, 1704-1739, 1743-1753, 1757-1776, 1780-1802, 1806-1827, 1832-1928, 1932
autocoder_cc/blueprint_language/component_logic_generator_with_observability.py                       89     89     0%   11-260
autocoder_cc/blueprint_language/component_name_utils.py                                               67     59    12%   21-26, 37-43, 61-92, 105-133, 146-151, 157-180
autocoder_cc/blueprint_language/component_type_registry.py                                            79     79     0%   2-219
autocoder_cc/blueprint_language/database_config_manager.py                                           152    114    25%   44, 60-67, 79, 83, 87-100, 112-116, 161-186, 209-230, 236-257, 273-299, 311-335, 346-366, 371, 376-418
autocoder_cc/blueprint_language/deployment_blueprint_parser.py                                       236    169    28%   77-78, 82-107, 111-131, 137-163, 169-182, 193-248, 254-269, 274-307, 317-353, 363-391, 401-427, 437-468, 478-532, 541-629, 632
autocoder_cc/blueprint_language/documentation_generator.py                                           249    249     0%   15-770
autocoder_cc/blueprint_language/enhanced_system_generator.py                                         201    201     0%   7-500
autocoder_cc/blueprint_language/healing_integration.py                                               278    229    18%   93-123, 137-210, 225-330, 337-423, 428-515, 521-584, 590-655, 659-660
autocoder_cc/blueprint_language/import_auto_fixer.py                                                  65     65     0%   3-115
autocoder_cc/blueprint_language/integration_validation_gate.py                                        42     23    45%   28-29, 33-63, 75-94
autocoder_cc/blueprint_language/intermediate_format.py                                               108    108     0%   6-465
autocoder_cc/blueprint_language/intermediate_system_healer.py                                        387    387     0%   12-886
autocoder_cc/blueprint_language/intermediate_to_blueprint_translator.py                              151    151     0%   6-438
autocoder_cc/blueprint_language/level2_real_validator.py                                             146    146     0%   1-289
autocoder_cc/blueprint_language/level2_unit_validator.py                                             136    136     0%   12-514
autocoder_cc/blueprint_language/level3_integration_validator.py                                      194    194     0%   1-536
autocoder_cc/blueprint_language/level3_real_integration_validator.py                                 199    199     0%   5-466
autocoder_cc/blueprint_language/live_benchmark_collector.py                                          228    228     0%   7-483
autocoder_cc/blueprint_language/llm_component_generator.py                                           389    358     8%   50-81, 97-164, 171-307, 325-344, 363-388, 405-611, 619-715, 719-800, 806-834, 838-851
autocoder_cc/blueprint_language/llm_component_generator_backup.py                                    673    673     0%   6-2328
autocoder_cc/blueprint_language/llm_component_generator_original.py                                  204    204     0%   17-555
autocoder_cc/blueprint_language/llm_component_generator_unified.py                                   176    176     0%   7-449
autocoder_cc/blueprint_language/llm_generation/__init__.py                                             6      0   100%
autocoder_cc/blueprint_language/llm_generation/component_wrapper.py                                   99     96     3%   25, 50-122, 142-211
autocoder_cc/blueprint_language/llm_generation/context_builder.py                                    129    116    10%   31, 62-96, 111-160, 173-178, 191, 209, 235-294, 308-343, 358-365, 369-402
autocoder_cc/blueprint_language/llm_generation/o3_specialized_prompts.py                              25     14    44%   30, 34, 55-72, 87, 117, 136, 148-149, 165-170
autocoder_cc/blueprint_language/llm_generation/prompt_engine.py                                      106     92    13%   40-47, 51, 88-98, 109-150, 177-245, 250-280, 301-330, 348-349, 373-498, 511
autocoder_cc/blueprint_language/llm_generation/response_validator.py                                 185    163    12%   41-42, 46, 68, 82-104, 108-126, 130-143, 159-181, 204, 208-256, 268-317, 329-361, 375-413, 425-450
autocoder_cc/blueprint_language/llm_generation/retry_orchestrator.py                                 126     97    23%   42-52, 56-75, 90, 99-142, 159-231, 244-274, 287, 300, 316-323, 335-359
autocoder_cc/blueprint_language/natural_language_to_blueprint.py                                     508    508     0%   6-1176
autocoder_cc/blueprint_language/optimized_llm_generator.py                                           185    185     0%   7-386
autocoder_cc/blueprint_language/pattern_detector.py                                                   13     13     0%   2-28
autocoder_cc/blueprint_language/performance_optimization.py                                          332    332     0%   7-580
autocoder_cc/blueprint_language/port_auto_generator.py                                               121     99    18%   40-47, 56-220, 225-263, 268-285, 290-379, 384-402, 406, 410, 416-417, 422-423
autocoder_cc/blueprint_language/port_connection_validator.py                                         131    131     0%   2-285
autocoder_cc/blueprint_language/processors/__init__.py                                                 4      4     0%   6-10
autocoder_cc/blueprint_language/processors/blueprint_processor.py                                    180    180     0%   8-529
autocoder_cc/blueprint_language/processors/blueprint_validator.py                                    165    165     0%   7-412
autocoder_cc/blueprint_language/processors/schema_utils.py                                             7      7     0%   6-49
autocoder_cc/blueprint_language/production_deployment_generator.py                                   494    437    12%   51-72, 77-88, 96-155, 168-234, 239-319, 324-357, 362-401, 406-685, 690, 733-996, 1001-1004, 1161-1166, 1280-1327, 1332-1570, 1575-1588, 1592-1633, 1637-1640, 1648-1686, 1690-1762, 1768-1827, 1836-1844, 1849-1871, 1875-1911, 1916-1946, 1950-1958, 1971-2037, 2041-2059, 2063-2078, 2082-2097, 2101-2109, 2114-2122, 2127-2218, 2222
autocoder_cc/blueprint_language/prompt_loader.py                                                     146    120    18%   40-47, 51-52, 67-88, 101-123, 133-143, 156-168, 180-190, 199-224, 233-274, 283-301, 310-312, 322-345
autocoder_cc/blueprint_language/schema_aware_test_generator.py                                        75     75     0%   2-167
autocoder_cc/blueprint_language/schema_version_validator.py                                          204    204     0%   11-404
autocoder_cc/blueprint_language/semantic_validator.py                                                116    116     0%   12-389
autocoder_cc/blueprint_language/system_blueprint_parser.py                                           467    383    18%   90-101, 105-117, 121-169, 173-204, 210-340, 346-392, 399-460, 467-536, 542-595, 609-627, 632-642, 653-691, 702-748, 760-793, 799-860, 865-873, 879-898, 903-925, 930-937, 942-968, 972-1006, 1009
autocoder_cc/blueprint_language/system_communication_generator.py                                    104    104     0%   6-332
autocoder_cc/blueprint_language/system_file_manager.py                                               133    133     0%   6-436
autocoder_cc/blueprint_language/system_generation/__init__.py                                          2      0   100%
autocoder_cc/blueprint_language/system_generation/benchmark_collector.py                             240    212    12%   56-58, 63-99, 110-123, 132-166, 174-200, 209-213, 218-258, 265-286, 294-310, 318-319, 325-340, 346-388, 413-458, 484-529, 549-560, 565-597
autocoder_cc/blueprint_language/system_generation/decision_audit.py                                   25      6    76%   24, 27, 35-37, 40
autocoder_cc/blueprint_language/system_generation/messaging_analyzer.py                              128    106    17%   32-33, 39-50, 62-99, 105-134, 144-191, 202-247, 258-285, 296, 319-328, 332, 340, 346-361, 372-376, 385-388
autocoder_cc/blueprint_language/system_generation/schema_and_benchmarks.py                           168    108    36%   78-79, 162-165, 173-220, 230-251, 258-270, 277-327, 334-340, 344-358, 364-390
autocoder_cc/blueprint_language/system_generation/validation_orchestrator.py                          85     68    20%   22-23, 35-61, 77-103, 116-117, 128-142, 153-182
autocoder_cc/blueprint_language/system_generator.py                                                  907    829     9%   96-141, 153-174, 179-223, 229-232, 237-250, 255-713, 717-947, 966-1053, 1062-1150, 1154-1178, 1184-1193, 1205-1211, 1234-1378, 1387-1521, 1526-1577, 1587-1590, 1596-1621, 1627-1702, 1706-1731, 1735, 1743, 1747-1758, 1762-1773, 1777-1788, 1793-1799, 1804-1812, 1817-1831, 1835-1852, 1857-1875, 1879-1902, 1906-1930, 1934-1961, 1965-1979, 1983-2017, 2021-2087, 2094-2218, 2223-2224, 2228
autocoder_cc/blueprint_language/system_generator_patch.py                                             70     70     0%   7-148
autocoder_cc/blueprint_language/system_generator_refactored.py                                       156    156     0%   8-339
autocoder_cc/blueprint_language/system_health_analyzer.py                                            100    100     0%   3-156
autocoder_cc/blueprint_language/system_integration_tester.py                                         227    227     0%   16-579
autocoder_cc/blueprint_language/system_scaffold_generator.py                                         307    265    14%   45-47, 53-142, 152-156, 164-201, 205-230, 237-426, 433-496, 508-524, 529-547, 551-558, 563-572, 577-589, 594-602, 607-644, 649-756, 761-814, 819-882, 897-922, 929-937, 941-977, 981-993, 1000, 1095-1187, 1194
autocoder_cc/blueprint_language/system_validator.py                                                  170    170     0%   6-318
autocoder_cc/blueprint_language/ui_generator.py                                                      165    165     0%   10-830
autocoder_cc/blueprint_language/validation_framework.py                                               99     85    14%   15-16, 35-55, 67-80, 92-136, 148-180, 192-232, 243-270
autocoder_cc/blueprint_language/validation_result_types.py                                            45     19    58%   33-36, 41, 46, 51-56, 60-67
autocoder_cc/blueprint_language/validators/__init__.py                                                15     15     0%   15-32
autocoder_cc/blueprint_language/validators/component_validator.py                                    315    315     0%   18-639
autocoder_cc/blueprint_language/validators/integration_validator.py                                  347    347     0%   20-792
autocoder_cc/blueprint_language/validators/semantic_validator.py                                     342    342     0%   19-861
autocoder_cc/blueprint_language/verbose_logger.py                                                    243    196    19%   35-40, 58-71, 77-109, 113-127, 131-156, 160-184, 193-219, 231-260, 270-290, 298-315, 326-343, 354-358, 367-411, 415-423, 427-429, 445-446, 454-458, 461-462, 465-469, 474-512, 516
autocoder_cc/blueprint_validation/__init__.py                                                          7      0   100%
autocoder_cc/blueprint_validation/boundary_semantics.py                                              166    129    22%   45-47, 56-72, 79-88, 99-125, 132-156, 165-176, 182-201, 215-234, 241-248, 252, 259-297, 315-347, 352-358, 364-388, 396-420, 431-454, 458-460
autocoder_cc/blueprint_validation/migration_engine.py                                                307    238    22%   73-119, 130-146, 153-159, 163-179, 184-192, 196-211, 217, 221-256, 260-317, 321-333, 337-358, 362-386, 391-397, 402-424, 428-429, 433-455, 482-490, 496-510, 516-536, 542-555, 562-563, 569-577, 588, 597-610, 614-615, 619-622, 626-635, 644-647, 658-723
autocoder_cc/blueprint_validation/vr1_error_taxonomy.py                                              124     38    69%   92, 96, 107-130, 135, 139-157, 161-165, 174, 188, 208, 228, 248, 268, 287, 306, 327, 346
autocoder_cc/blueprint_validation/vr1_rollout.py                                                     125     99    21%   35-52, 56, 60-61, 65-72, 77-88, 111-162, 166-191, 196-211, 215-240
autocoder_cc/blueprint_validation/vr1_telemetry.py                                                   110     55    50%   18-19, 70-71, 92-110, 128-144, 149-165, 181-188, 201-202, 206-209, 225-230, 244-247, 260-273
autocoder_cc/blueprint_validation/vr1_validator.py                                                   184    143    22%   57-66, 76-164, 177-185, 195, 203-235, 252-282, 290-316, 324-372, 376, 381-388, 395-440, 444-445
autocoder_cc/capabilities/__init__.py                                                                  0      0   100%
autocoder_cc/capabilities/ast_security_validator.py                                                  143     90    37%   48-49, 173-202, 207-217, 221-222, 226-227, 231-240, 244-253, 257-259, 263-264, 268-285, 296-330, 341-348, 358-363, 368-384, 388-417, 434-435, 448-453
autocoder_cc/capabilities/circuit_breaker.py                                                          64     64     0%   4-94
autocoder_cc/capabilities/health_checker.py                                                          116    116     0%   1-231
autocoder_cc/capabilities/input_sanitizer.py                                                         184    128    30%   62-63, 80-128, 146-172, 177-194, 199-240, 244-255, 260-265, 269-284, 288-309, 314-322, 326-336, 340-351, 355-366, 373-395, 410-435, 439-468, 485-486, 502-511
autocoder_cc/capabilities/metrics_collector.py                                                        52     52     0%   9-111
autocoder_cc/capabilities/rate_limiter.py                                                             51     51     0%   4-81
autocoder_cc/capabilities/retry_handler.py                                                            50     50     0%   4-76
autocoder_cc/capabilities/schema_validator.py                                                         71     71     0%   9-121
autocoder_cc/chaos.py                                                                                635    635     0%   12-1500
autocoder_cc/checkpoint/__init__.py                                                                    0      0   100%
autocoder_cc/checkpoint/checkpoint_manager.py                                                         41     41     0%   2-69
autocoder_cc/cli/__init__.py                                                                           0      0   100%
autocoder_cc/cli/local_orchestrator.py                                                               263    263     0%   6-478
autocoder_cc/cli/lock_cli.py                                                                          33     33     0%   3-50
autocoder_cc/cli/main.py                                                                             190    190     0%   5-305
autocoder_cc/components/__init__.py                                                                   11      0   100%
autocoder_cc/components/accumulator.py                                                                93     79    15%   22-62, 72-73, 77-79, 83-111, 116-133, 144-208
autocoder_cc/components/aggregator.py                                                                206    206     0%   7-460
autocoder_cc/components/api_endpoint.py                                                              115     91    21%   28-41, 46-55, 60-70, 74, 78, 83-117, 121-136, 160, 178-201, 216-217, 230-232, 254-261, 268-274, 281-302
autocoder_cc/components/base.py                                                                       79     79     0%   11-248
autocoder_cc/components/component_categorization.py                                                   54     37    31%   47, 69-105, 123-134, 149-166
autocoder_cc/components/component_registry.py                                                        610    522    14%   40-44, 93, 125, 135-136, 162-207, 216-248, 257-281, 286-294, 298, 302, 307-317, 324-345, 349-353, 357-397, 402-466, 470-471, 475-536, 541-651, 655-673, 677-717, 721-752, 756-788, 792-800, 804-835, 853-881, 893-903, 908-913, 931-1010, 1029-1081, 1098-1181, 1193-1249, 1253-1273, 1277-1293, 1297-1323
autocoder_cc/components/composed_base.py                                                             250    200    20%   28-47, 53, 59-80, 84-86, 90-92, 96-98, 102-104, 108-110, 114-138, 152-247, 263, 268, 272, 276-279, 283-284, 288-291, 295-302, 306-311, 317-330, 340-341, 345-347, 351-355, 360-367, 372-379, 383-386, 391, 395, 399, 403, 407, 413, 418, 425, 432, 439, 446, 455-467, 471-480, 484-494, 498-504, 508-515
autocoder_cc/components/composition_interfaces.py                                                     20     20     0%   7-206
autocoder_cc/components/connection_manager.py                                                         62     62     0%   2-111
autocoder_cc/components/controller.py                                                                105     90    14%   23-38, 42-45, 50-57, 65-90, 99-131, 135-165, 170-180, 184-189
autocoder_cc/components/cqrs/__init__.py                                                               0      0   100%
autocoder_cc/components/cqrs/command_handler.py                                                       84     84     0%   1-189
autocoder_cc/components/cqrs/query_handler.py                                                        122    122     0%   1-256
autocoder_cc/components/database_component.py                                                         33     33     0%   2-61
autocoder_cc/components/enhanced_composition.py                                                      300    300     0%   11-505
autocoder_cc/components/fastapi_endpoint.py                                                          122    106    13%   15-30, 34-158, 162-168, 172, 176-181, 185-188
autocoder_cc/components/filter.py                                                                    231    231     0%   7-519
autocoder_cc/components/message_bus.py                                                               122    105    14%   32-57, 61-123, 127-162, 166-181, 185-206, 210-226, 230-258, 262
autocoder_cc/components/metrics_endpoint.py                                                          173    173     0%   1-328
autocoder_cc/components/model.py                                                                      85     69    19%   17-22, 27-37, 42-58, 62-70, 74-91, 100-109, 117-170
autocoder_cc/components/port_registry.py                                                              53     53     0%   2-81
autocoder_cc/components/ports.py                                                                     114    114     0%   8-322
autocoder_cc/components/primitives/__init__.py                                                        12     12     0%   14-60
autocoder_cc/components/primitives/base.py                                                            35     35     0%   6-100
autocoder_cc/components/primitives/merger.py                                                           8      8     0%   2-30
autocoder_cc/components/primitives/sink.py                                                             8      8     0%   2-27
autocoder_cc/components/primitives/source.py                                                           9      9     0%   2-28
autocoder_cc/components/primitives/splitter.py                                                         8      8     0%   2-31
autocoder_cc/components/primitives/transformer.py                                                     11     11     0%   2-45
autocoder_cc/components/router.py                                                                    147    147     0%   7-355
autocoder_cc/components/sink.py                                                                       67     67     0%   5-141
autocoder_cc/components/source.py                                                                     62     62     0%   5-137
autocoder_cc/components/store.py                                                                     169    144    15%   22-67, 72-85, 90-105, 109-147, 152-168, 172-180, 187-235, 244-294, 298-299, 311, 315, 319, 324, 328, 332-335, 339-340
autocoder_cc/components/stream_processor.py                                                          124    105    15%   25-44, 48-49, 54-63, 71-98, 106-128, 132-142, 150-162, 166-178, 182-196, 200-225, 234-238
autocoder_cc/components/transformer.py                                                                51     51     0%   5-128
autocoder_cc/components/type_safe_composition.py                                                     150    150     0%   7-284
autocoder_cc/components/type_safety.py                                                               246    246     0%   7-548
autocoder_cc/components/v5_enhanced_store.py                                                         386    295    24%   107-135, 143-189, 207-228, 232-254, 261-279, 286-319, 323-367, 374-410, 417, 421-458, 462-505, 509-525, 536-541, 545-608, 613-641, 650-664, 671-678, 693-696, 700-741, 751-763, 770-777, 781-787, 791-796, 801, 805-809, 816, 819, 822, 826, 830, 834, 844-847, 851-856, 860-869, 873, 883-897
autocoder_cc/components/walking_skeleton/__init__.py                                                   5      5     0%   2-7
autocoder_cc/components/walking_skeleton/api_source.py                                                43     43     0%   2-77
autocoder_cc/components/walking_skeleton/base_component.py                                            23     23     0%   2-40
autocoder_cc/components/walking_skeleton/controller.py                                                71     71     0%   2-111
autocoder_cc/components/walking_skeleton/store.py                                                     57     57     0%   2-103
autocoder_cc/components/walking_skeleton/validator.py                                                 66     66     0%   2-97
autocoder_cc/components/websocket.py                                                                 100    100     0%   5-172
autocoder_cc/core/__init__.py                                                                          0      0   100%
autocoder_cc/core/config.py                                                                          246     91    63%   329-330, 334, 339-348, 353-359, 364-390, 395-407, 411-432, 436-452, 456-460, 464-481, 485-489, 493-499, 503, 521-528, 534-551, 560-563
autocoder_cc/core/config_manager.py                                                                   23     23     0%   7-90
autocoder_cc/core/dependency_container.py                                                            285    223    22%   49-52, 56-59, 63, 67, 86-93, 97-117, 121-176, 184-185, 195-211, 235-271, 276-285, 295, 311, 327, 343-356, 367, 394-442, 449-465, 472, 479, 483, 491, 496-510, 514-516, 520-522, 531-537, 546-588, 592-629, 633-639, 652-703
autocoder_cc/core/dependency_graph.py                                                                237    237     0%   8-494
autocoder_cc/core/dependency_injection.py                                                             97     63    35%   43-49, 65-74, 84-86, 96, 111-141, 153-156, 160-164, 168, 172-185, 194-198, 213, 226, 236, 249-254
autocoder_cc/core/exceptions.py                                                                       34     34     0%   6-78
autocoder_cc/core/module_interfaces.py                                                               238     69    71%   91, 96, 101, 113, 121, 129, 138, 150, 158, 166, 171, 184, 193, 203, 208, 221, 230, 235, 240, 254, 263, 272, 280, 288, 301, 310, 319, 327, 340, 349, 357, 365, 378, 387, 395, 409, 417, 422, 435, 444, 452, 457, 471, 480, 490, 499, 512, 520, 525, 539, 544, 555, 560, 565, 570, 581-626
autocoder_cc/core/port_registry.py                                                                   154    121    21%   25-27, 53-65, 88-125, 137-158, 170-176, 188-201, 213-214, 226-227, 239-240, 252-253, 262-263, 275-285, 289-295, 308-335, 339-342, 360-366, 374-376
autocoder_cc/core/schema_versioning.py                                                                78     52    33%   36-37, 52-74, 90-96, 109-137, 143-163, 168-184, 188-190, 195-196, 200-201, 209
autocoder_cc/core/service_registry.py                                                                 46     46     0%   7-124
autocoder_cc/core/timeout_manager.py                                                                 156     97    38%   41, 56, 61, 67-69, 75-84, 105-115, 136-151, 163-172, 188-198, 207-208, 217-229, 252-271, 297-328, 337-351, 360-363, 367-368, 387-393, 401-403
autocoder_cc/database/__init__.py                                                                      0      0   100%
autocoder_cc/database/connection_layer.py                                                             77     77     0%   2-113
autocoder_cc/deployment/__init__.py                                                                    3      3     0%   9-12
autocoder_cc/deployment/deployment_manager.py                                                        257    257     0%   9-741
autocoder_cc/deployment/environment_provisioner.py                                                   147    147     0%   9-416
autocoder_cc/error_handling/__init__.py                                                                2      0   100%
autocoder_cc/error_handling/consistent_handler.py                                                    172    126    27%   90-97, 120-150, 159-216, 220-222, 226-244, 249-262, 272-282, 290-302, 306-330, 334, 347-349, 352, 355-358, 378-384, 393-417, 430, 435
autocoder_cc/exceptions.py                                                                           149     92    38%   43-51, 55-58, 62, 79, 86-89, 108-115, 127-130, 142-145, 164-171, 191-199, 218-225, 237, 251-258, 270-273, 292-299, 318-326, 338-339, 345-346, 350-360, 368, 372, 380-382, 392-433, 452-459, 470
autocoder_cc/fix_component_async_issues.py                                                            38     38     0%   5-66
autocoder_cc/focused_generation/__init__.py                                                            0      0   100%
autocoder_cc/focused_generation/blueprint_extractor.py                                               127    127     0%   9-301
autocoder_cc/focused_generation/business_logic_spec.py                                                42     42     0%   9-98
autocoder_cc/focused_generation/business_logic_validator.py                                          212    212     0%   9-357
autocoder_cc/focused_generation/component_assembler.py                                               103    103     0%   10-252
autocoder_cc/focused_generation/focused_prompt_engine.py                                              43     43     0%   9-103
autocoder_cc/generate_deployed_system.py                                                             525    525     0%   12-804
autocoder_cc/generation/__init__.py                                                                    3      0   100%
autocoder_cc/generation/blueprint_component_converter.py                                              82     65    21%   36-41, 66-99, 108-124, 128-134, 141-234, 238-267
autocoder_cc/generation/component_generator.py                                                       121     93    23%   70-88, 105-144, 156-168, 185-205, 209-241, 245-348, 352-368, 372-388, 392-428, 432-458, 462-485
autocoder_cc/generation/deployment/__init__.py                                                         0      0   100%
autocoder_cc/generation/deployment/config_manager.py                                                  57     57     0%   5-130
autocoder_cc/generation/deployment/environment_templates.py                                          102    102     0%   5-263
autocoder_cc/generation/import_path_resolver.py                                                       76     61    20%   25-30, 43-51, 68-77, 81, 93-112, 116-156, 167-207, 211-222, 239-255
autocoder_cc/generation/llm_schema_generator.py                                                      268    241    10%   44-133, 157-201, 216-284, 288-306, 310, 317-438, 450-550, 563-613
autocoder_cc/generation/nl_parser.py                                                                 218    171    22%   138-195, 203-235, 241-255, 264-286, 291-373, 378-404, 410-450, 455, 467-501
autocoder_cc/generation/phase2_integration.py                                                        228    228     0%   1-654
autocoder_cc/generation/property_test_generator.py                                                   324    261    19%   95-176, 184-239, 247-332, 338-367, 376-469, 474-483, 492-570, 575-642, 647-742, 748-792, 797, 802-850, 855-899, 904-911, 917, 921-934, 938-948, 952-960, 964-970, 974-980, 985-993, 997-999, 1043, 1053-1067, 1072-1075
autocoder_cc/generation/schema_generator.py                                                          306    263    14%   86-125, 133-161, 170-220, 226-274, 280-332, 338-400, 406-461, 470-518, 523-567, 571, 575, 580-594, 601-624
autocoder_cc/generation/secure_templates.py                                                          106     51    52%   376-407, 416-453, 458-466, 470, 476-500, 508-510
autocoder_cc/generation/standalone_import_resolver.py                                                 48     36    25%   23, 27-51, 55-117, 121-134, 138, 228, 278-301
autocoder_cc/generation/template_engine.py                                                           122     95    22%   33-50, 62-83, 87, 100-105, 115-116, 128-129, 133-135, 140-147, 152-157, 163-165, 170-171, 176-178, 183-206, 210-253, 258-276
autocoder_cc/generators/__init__.py                                                                    2      0   100%
autocoder_cc/generators/components/api_endpoint_generator.py                                          99     80    19%   14, 18-41, 49-88, 92, 132-235, 416-552, 556, 649-660, 664-680, 685-686, 692-702, 706, 710, 717-734, 742-743
autocoder_cc/generators/components/auth_endpoint_generator.py                                         13      7    46%   13, 17-25
autocoder_cc/generators/components/base_generator.py                                                  48     33    31%   25-27, 32, 40-55, 59-61, 65-67, 71-83, 92-149, 153
autocoder_cc/generators/components/data_transformer_generator.py                                      11      7    36%   14-24
autocoder_cc/generators/components/factory.py                                                         38     22    42%   47-52, 67-87, 99-101, 105, 109
autocoder_cc/generators/components/store_generator.py                                                 37     27    27%   29-34, 42-79, 84-689
autocoder_cc/generators/config.py                                                                     78     29    63%   32, 37, 46, 51, 56, 61, 66, 71, 76, 81, 86, 95, 100, 105, 114-115, 122-127, 131-136, 140, 144-145
autocoder_cc/generators/production_istio_validator.py                                                347    347     0%   8-1146
autocoder_cc/generators/scaffold/__init__.py                                                           2      0   100%
autocoder_cc/generators/scaffold/communication_generator.py                                           33     33     0%   14-503
autocoder_cc/generators/scaffold/docker_compose_generator.py                                          82     82     0%   5-310
autocoder_cc/generators/scaffold/dockerfile_generator.py                                              14     14     0%   5-87
autocoder_cc/generators/scaffold/env_file_generator.py                                                45     45     0%   5-146
autocoder_cc/generators/scaffold/k8s_generator.py                                                     39     39     0%   5-201
autocoder_cc/generators/scaffold/main_generator.py                                                    95     95     0%   6-384
autocoder_cc/generators/scaffold/main_generator_dynamic.py                                            63     63     0%   6-712
autocoder_cc/generators/scaffold/manifest_generator.py                                                36     36     0%   1-81
autocoder_cc/generators/scaffold/observability_generator.py                                           54     54     0%   13-538
autocoder_cc/generators/scaffold/orchestrator.py                                                      77     77     0%   5-156
autocoder_cc/generators/scaffold/requirements_generator.py                                            35     35     0%   5-128
autocoder_cc/generators/scaffold/shared_observability.py                                             117    117     0%   41-239
autocoder_cc/generators/scaffold/structure_generator.py                                               56     42    25%   21, 31-66, 71-85, 89-126, 130-188, 192-219, 223-278, 284-286
autocoder_cc/generators/service_deployment_generator.py                                              408    408     0%   9-2336
autocoder_cc/healing/__init__.py                                                                       4      0   100%
autocoder_cc/healing/ast_healer.py                                                                   320    266    17%   41, 53-125, 143-159, 177-193, 211-227, 246-274, 283-285, 289-311, 318, 322-336, 340-358, 365, 369-405, 412-413, 417-459, 466-470, 476-478, 481-486, 490-492, 496-498, 505-509, 513-516, 520-523, 527-530, 534-537, 541-544, 547-577, 581-613, 618-626, 630, 639-645, 659-693, 698-723
autocoder_cc/healing/ast_transformers/__init__.py                                                      3      3     0%   3-6
autocoder_cc/healing/ast_transformers/communication_method_transformer.py                             23     23     0%   2-60
autocoder_cc/healing/ast_transformers/message_envelope_transformer.py                                 21     21     0%   2-44
autocoder_cc/healing/blueprint_healer.py                                                             361    337     7%   18-24, 28-36, 42-58, 62-84, 96-172, 176-183, 187, 204-235, 253-418, 423-451, 456-493, 497-577, 581-590, 594-612, 616-649, 654-674, 679-687, 700-701
autocoder_cc/healing/reconcile_endpoints.py                                                          128    128     0%   6-256
autocoder_cc/healing/semantic_healer.py                                                              216    173    20%   24, 32-33, 37, 70-112, 116-118, 134-172, 194-225, 237-283, 296-353, 365-394, 407-430, 455-502, 513-539, 543-566, 589-620
autocoder_cc/healing/system_healer.py                                                                212    177    17%   54-56, 68-103, 115-142, 156-195, 209-237, 249-284, 296-328, 342-373, 387-405, 414-418, 432-472, 477-511
autocoder_cc/interfaces/__init__.py                                                                    0      0   100%
autocoder_cc/interfaces/components.py                                                                 21     21     0%   6-58
autocoder_cc/interfaces/config.py                                                                      2      0   100%
autocoder_cc/interfaces/generators.py                                                                 27     27     0%   6-85
autocoder_cc/llm_providers/__init__.py                                                                 4      0   100%
autocoder_cc/llm_providers/anthropic_provider.py                                                      48     48     0%   1-104
autocoder_cc/llm_providers/base_provider.py                                                           52     10    81%   47-51, 56, 61, 66, 71, 75
autocoder_cc/llm_providers/circuit_breaker.py                                                        103     72    30%   41-44, 48-51, 55, 59-64, 71-83, 91-104, 108-121, 125-142, 150-165, 173-182, 192-194
autocoder_cc/llm_providers/gemini_provider.py                                                        269    269     0%   1-468
autocoder_cc/llm_providers/model_registry.py                                                         119     63    47%   62-63, 69-252, 281-334, 338-340, 344-345, 349, 356, 363-372, 379-388, 395-436, 446-448
autocoder_cc/llm_providers/multi_provider_manager.py                                                 192    171    11%   17-46, 50-92, 97-160, 164-169, 173-187, 198, 203-232, 236-281, 286-358
autocoder_cc/llm_providers/openai_provider.py                                                         62     62     0%   1-143
autocoder_cc/llm_providers/provider_registry.py                                                       23     14    39%   9-10, 14-15, 19, 23, 27-34
autocoder_cc/llm_providers/structured_outputs.py                                                      61      0   100%
autocoder_cc/llm_providers/unified_llm_provider.py                                                   101     75    26%   44-69, 73, 96-101, 108-219, 227, 235-260, 266
autocoder_cc/lockfile.py                                                                              58     39    33%   29, 39-114, 122-125, 134-140, 148-149, 164-173
autocoder_cc/messaging/__init__.py                                                                     7      7     0%   8-15
autocoder_cc/messaging/bridges/__init__.py                                                             4      4     0%   7-11
autocoder_cc/messaging/bridges/anyio_http_bridge.py                                                  203    203     0%   7-364
autocoder_cc/messaging/bridges/anyio_kafka_bridge.py                                                 162    162     0%   7-297
autocoder_cc/messaging/bridges/anyio_rabbitmq_bridge.py                                              149    149     0%   7-274
autocoder_cc/messaging/connectors/__init__.py                                                          3      3     0%   7-10
autocoder_cc/messaging/connectors/message_bus_connector.py                                           180    180     0%   7-316
autocoder_cc/messaging/connectors/service_connector.py                                               337    337     0%   7-791
autocoder_cc/messaging/connectors/strict_service_connector.py                                        152    152     0%   6-447
autocoder_cc/messaging/connectors/zero_inference_consul_discovery.py                                 177    177     0%   7-432
autocoder_cc/messaging/exceptions.py                                                                  52     52     0%   8-180
autocoder_cc/messaging/protocols/__init__.py                                                           5      5     0%   7-12
autocoder_cc/messaging/protocols/http_protocol.py                                                    233    233     0%   7-384
autocoder_cc/messaging/protocols/kafka_protocol.py                                                   210    210     0%   7-371
autocoder_cc/messaging/protocols/message_format.py                                                    63     63     0%   7-125
autocoder_cc/messaging/protocols/rabbitmq_protocol.py                                                216    216     0%   7-342
autocoder_cc/migration/__init__.py                                                                     0      0   100%
autocoder_cc/migration/blueprint_analyzer.py                                                          77     77     0%   2-150
autocoder_cc/migration/blueprint_migrator.py                                                          85     85     0%   2-157
autocoder_cc/observability.py                                                                        261    261     0%   1-526
autocoder_cc/observability/__init__.py                                                                10      1    90%   16
autocoder_cc/observability/compliance_monitor.py                                                     233    233     0%   9-472
autocoder_cc/observability/cost_controls.py                                                          117     83    29%   33-35, 46-47, 51-56, 62-76, 80-106, 111-137, 147-180, 184-195, 199-205, 209, 260-266
autocoder_cc/observability/generation_logger.py                                                      156    156     0%   16-532
autocoder_cc/observability/health_checks.py                                                          259    259     0%   10-524
autocoder_cc/observability/metrics.py                                                                342    273    20%   37-45, 68-89, 93-113, 117-245, 252-260, 264-270, 274-280, 284-290, 294-305, 309-325, 329-340, 344, 348, 352, 357-358, 362-363, 367, 371, 375, 379, 383, 387-388, 393, 397, 401, 405, 410, 414, 418-429, 434-447, 451-460, 464-488, 500-518, 522-539, 543-576, 584-587, 590-591, 594-601, 611-614, 619-627, 632-638
autocoder_cc/observability/monitoring.py                                                             185    185     0%   10-607
autocoder_cc/observability/monitoring_alerts.py                                                      159     98    38%   45, 79-88, 92-103, 107-109, 115-134, 138-139, 143-148, 152-162, 166, 170-174, 178-194, 198-224, 234-255, 265-275, 285-287, 298-315, 319-330, 341-351
autocoder_cc/observability/otel_config.py                                                             11      8    27%   10-20
autocoder_cc/observability/pipeline_metrics.py                                                       102    102     0%   5-218
autocoder_cc/observability/real_world_integrations.py                                                237    237     0%   9-537
autocoder_cc/observability/retention_budget.py                                                       370    370     0%   9-854
autocoder_cc/observability/sampling_policy.py                                                        325    325     0%   9-670
autocoder_cc/observability/simple_generation_logger.py                                               173    173     0%   11-470
autocoder_cc/observability/structured_logging.py                                                     148     50    66%   81-82, 132-133, 139-144, 153-160, 188, 198, 202, 210, 215, 221, 226-236, 241-245, 258-262, 274, 283, 292-299, 312-316, 319-321, 324-342, 370-372
autocoder_cc/observability/tracing.py                                                                193    146    24%   33-35, 39, 56-65, 69-86, 90-123, 127, 131, 135, 139, 156-200, 212-253, 257-263, 268-280, 287-288, 292-293, 302-306, 322-333, 338-341, 346-353, 357-396, 406-444, 468-471, 476-481
autocoder_cc/observability/unified_economics.py                                                      149    149     0%   9-308
autocoder_cc/orchestration/__init__.py                                                                 5      0   100%
autocoder_cc/orchestration/component.py                                                              127     80    37%   43, 50, 60, 71, 161-175, 184-190, 210, 218, 235-255, 259, 266, 283-286, 290, 294-296, 302-304, 308-313, 317-322, 329-346, 350-372
autocoder_cc/orchestration/component_manifest.py                                                     115    115     0%   14-265
autocoder_cc/orchestration/dependency_injection.py                                                    97     75    23%   40-43, 55-75, 86-124, 133-150, 163-178, 191, 203, 212, 221-244, 258-259, 264-265, 274-283, 288-300, 304-305
autocoder_cc/orchestration/dynamic_loader.py                                                         179    140    22%   58-61, 65-95, 100-135, 139-218, 222-236, 241-254, 259-281, 288-325, 330-351
autocoder_cc/orchestration/harness.py                                                                731    613    16%   106, 110-138, 361-411, 423-429, 436-449, 453-466, 470-478, 502-544, 553-609, 617-644, 648-658, 668-689, 699-748, 752-772, 787-815, 834-863, 880-908, 927-961, 973-1029, 1038-1049, 1057-1065, 1069-1084, 1090, 1095-1145, 1149, 1159, 1164-1191, 1222-1229, 1240-1242, 1246-1249, 1255-1284, 1288-1312, 1316-1368, 1372-1395, 1399-1415, 1452-1456, 1460-1477, 1492-1493, 1505-1518, 1522-1526, 1530-1534, 1539-1547, 1551-1556, 1560-1730, 1734-1880, 1884-1897, 1906-1911, 1916-1919
autocoder_cc/orchestration/pipeline_coordinator.py                                                   120     95    21%   55-71, 84-157, 161-171, 175-204, 208-226, 230-249, 253-272, 276-300, 304-325
autocoder_cc/production/__init__.py                                                                    3      0   100%
autocoder_cc/production/environment_config.py                                                        142     89    37%   40, 83-85, 91-131, 152, 165-203, 215-239, 253-287, 301-332, 346-371, 376-401
autocoder_cc/production/secret_manager.py                                                             26     26     0%   9-92
autocoder_cc/production/secrets_manager.py                                                           149    112    25%   47-48, 88-108, 120-145, 163-195, 210-229, 241-274, 278-288, 293-306, 310-313, 318, 323, 327, 341-377, 388-414
autocoder_cc/prompts/__init__.py                                                                       2      2     0%   8-10
autocoder_cc/prompts/prompt_manager.py                                                               135    135     0%   11-335
autocoder_cc/recipes/__init__.py                                                                       3      0   100%
autocoder_cc/recipes/expander.py                                                                      76     69     9%   28-196, 208-213, 223-239, 251-252
autocoder_cc/recipes/registry.py                                                                       9      5    44%   370-373, 377
autocoder_cc/resource_orchestrator.py                                                                410    329    20%   92-95, 98-100, 104-118, 122-128, 132-170, 174-209, 227-246, 264-280, 293-302, 313-409, 413-430, 434-496, 509-519, 533-606, 615-621, 625-634, 638-651, 655-664, 668-689, 693-703, 707-717, 721-731, 739-779, 793-803, 817-832, 846-849, 856-859, 869, 875-900, 905-931, 935
autocoder_cc/resources.py                                                                             22     22     0%   6-46
autocoder_cc/runtime_defaults.py                                                                      24     24     0%   9-154
autocoder_cc/schemas.py                                                                              328    328     0%   87-762
autocoder_cc/security/__init__.py                                                                      6      6     0%   8-61
autocoder_cc/security/crypto_policy_enforcer.py                                                      165    165     0%   7-304
autocoder_cc/security/input_validator.py                                                             456    456     0%   8-942
autocoder_cc/security/secure_deployment.py                                                           384    384     0%   8-1123
autocoder_cc/security/security_auditor.py                                                            335    335     0%   8-856
autocoder_cc/setup.py                                                                                  2      2     0%   5-7
autocoder_cc/tdd/__init__.py                                                                           4      4     0%   22-46
autocoder_cc/tdd/file_hooks.py                                                                        75     75     0%   5-126
autocoder_cc/tdd/mutation_testing.py                                                                 249    249     0%   7-483
autocoder_cc/tdd/state_tracker.py                                                                    185    185     0%   6-341
autocoder_cc/tdd/test_runner.py                                                                      153    153     0%   5-302
autocoder_cc/testing/__init__.py                                                                       1      1     0%   12
autocoder_cc/testing/port_based_test_runner.py                                                       104    104     0%   2-170
autocoder_cc/tests/__init__.py                                                                         4      0   100%
autocoder_cc/tests/analysis/__init__.py                                                                4      0   100%
autocoder_cc/tests/analysis/test_ast_error_handling.py                                               190    166    13%   34-37, 41-42, 46-63, 68-95, 99-126, 130-145, 150-169, 174-191, 195-221, 225-248, 252-269, 274-292, 296-330, 335-354, 360-383, 388-411, 416-417
autocoder_cc/tests/analysis/test_placeholder_detection.py                                            147    121    18%   26-30, 34-45, 49-71, 82-85, 90-96, 100-116, 120-136, 140-149, 153-162, 166-174, 178-186, 190-207, 211-226, 230-255, 259-277, 281-292, 296-314, 318-332, 336-353, 357-390, 394-408, 412
autocoder_cc/tests/analysis/test_secret_detection.py                                                 141    117    17%   24, 28-46, 50-59, 63-71, 75-83, 87-103, 110-125, 132-142, 148-158, 162-177, 184-201, 207-217, 223-232, 238-259, 265-284, 289-306, 311-329, 333-347, 351-367, 371
autocoder_cc/tests/comprehensive/__init__.py                                                           0      0   100%
autocoder_cc/tests/comprehensive/test_comprehensive.py                                               181    181     0%   6-483
autocoder_cc/tests/comprehensive/test_hybrid_with_env.py                                              91     91     0%   6-153
autocoder_cc/tests/cqrs/__init__.py                                                                    0      0   100%
autocoder_cc/tests/cqrs/test_schema_versioning_standalone.py                                         160    160     0%   7-370
autocoder_cc/tests/e2e/__init__.py                                                                     0      0   100%
autocoder_cc/tests/e2e/test_comprehensive_e2e.py                                                     266    266     0%   7-458
autocoder_cc/tests/e2e/test_end_to_end_realistic.py                                                  213    213     0%   6-349
autocoder_cc/tests/e2e/test_hybrid_system.py                                                          65     65     0%   5-114
autocoder_cc/tests/e2e/test_real_chaos_engineering.py                                                571    571     0%   8-1353
autocoder_cc/tests/e2e/test_system_run.py                                                             27     27     0%   4-47
autocoder_cc/tests/integration/__init__.py                                                             0      0   100%
autocoder_cc/tests/integration/test_ast_integration_simple.py                                        117    117     0%   6-215
autocoder_cc/tests/integration/test_componentregistry_ast_integration.py                             117    117     0%   11-239
autocoder_cc/tests/integration/test_observability_integration.py                                     170    170     0%   7-383
autocoder_cc/tests/integration/test_system_generation_pipeline.py                                    237    237     0%   8-834
autocoder_cc/tests/observability/__init__.py                                                           0      0   100%
autocoder_cc/tests/observability/test_junit_xml_generation.py                                        114    114     0%   9-291
autocoder_cc/tests/observability/test_observability_standalone.py                                    236    236     0%   7-545
autocoder_cc/tests/performance/__init__.py                                                             0      0   100%
autocoder_cc/tests/performance/test_generation_performance.py                                        308    308     0%   8-619
autocoder_cc/tests/performance/test_pipeline_robustness.py                                           127    127     0%   11-335
autocoder_cc/tests/performance/test_validation_structure.py                                           40     40     0%   6-73
autocoder_cc/tests/test_service_communication_performance.py                                         379    379     0%   8-806
autocoder_cc/tests/tools/__init__.py                                                                   0      0   100%
autocoder_cc/tests/tools/component_analyzer.py                                                        71     60    15%   10, 14-46, 56-71, 78-96, 105-114, 118-127
autocoder_cc/tests/tools/component_loader.py                                                          44     44     0%   2-79
autocoder_cc/tests/tools/component_test_runner.py                                                    771    656    15%   26-27, 45-47, 56-133, 146-186, 197-199, 203, 207, 214-216, 219, 222, 225, 229, 232, 235, 239, 243-246, 314, 325, 330-341, 356-362, 374-388, 406-473, 477-496, 500-558, 562-591, 595-634, 639-658, 662-736, 741-770, 774-810, 815-852, 856-888, 893-941, 946-984, 989-1084, 1094-1103, 1107-1142, 1146-1237, 1241, 1260-1317, 1329-1569, 1586-1672, 1690-1696
autocoder_cc/tests/tools/concrete_components.py                                                      240    240     0%   2-383
autocoder_cc/tests/tools/integration_harness.py                                                       68     68     0%   2-122
autocoder_cc/tests/tools/integration_test_harness.py                                                 111     89    20%   18-19, 23-24, 28-38, 44-46, 50-112, 117-126, 130-148, 152-155, 159-173, 183-187, 193-194, 198, 202
autocoder_cc/tests/tools/message_bus.py                                                               33     33     0%   2-55
autocoder_cc/tests/tools/pipeline_test_runner.py                                                      53     53     0%   2-110
autocoder_cc/tests/tools/port_test_runner.py                                                          96     96     0%   2-169
autocoder_cc/tests/tools/real_component_test_runner.py                                               341    341     0%   6-712
autocoder_cc/tests/tools/test_data_generator.py                                                       39     39     0%   2-108
autocoder_cc/tests/tools/test_independent_verification.py                                             17     17     0%   4-27
autocoder_cc/tests/tools/test_production_validation.py                                                17     17     0%   4-27
autocoder_cc/tests/unit/__init__.py                                                                    0      0   100%
autocoder_cc/tests/unit/test_input_sanitization.py                                                   160    160     0%   9-368
autocoder_cc/tests/unit/test_llm_component_generator.py                                              221    221     0%   8-920
autocoder_cc/tests/unit/test_schema_versioning.py                                                    128    128     0%   7-318
autocoder_cc/tests/unit/test_todo_error.py                                                            30     30     0%   4-47
autocoder_cc/tests/unit/test_validation_framework.py                                                  73     73     0%   6-198
autocoder_cc/tests/validate_generation.py                                                             72     72     0%   4-119
autocoder_cc/utils/__init__.py                                                                         2      2     0%   7-13
autocoder_cc/utils/logging_config.py                                                                  52     52     0%   1-144
autocoder_cc/validate_all_systems.py                                                                  56     56     0%   5-97
autocoder_cc/validation.py                                                                           254    208    18%   35-41, 45, 49, 53, 71-79, 83, 95-97, 176-205, 218-242, 248-323, 332, 345-446, 450-464, 473-475, 491-526, 535-557, 565-582
autocoder_cc/validation/__init__.py                                                                    9      0   100%
autocoder_cc/validation/ast_analyzer.py                                                              594    494    17%   48-51, 56-103, 107-141, 156-161, 165-190, 201-219, 223-224, 228-236, 247-252, 258, 263-277, 282-285, 289-292, 296-310, 314-318, 322-327, 331-347, 357-358, 377-427, 455-478, 493-520, 532-566, 572-596, 604-607, 618-623, 627-632, 636-658, 662-685, 692-700, 705-749, 753-760, 764-791, 801-810, 814-825, 832-850, 866-867, 871-872, 876-879, 883-886, 891-897, 901-903, 907-909, 913-915, 920-978, 988-992, 997-1031, 1035-1039, 1043-1050, 1057-1065, 1069-1081, 1085-1086, 1090-1091, 1095-1101, 1105-1106, 1110-1117, 1165-1228, 1244-1279, 1290-1320, 1324-1328, 1332, 1341-1374, 1378-1415, 1421-1422, 1427-1428, 1433-1444
autocoder_cc/validation/graded_failure_handler.py                                                    204    204     0%   6-501
autocoder_cc/validation/integration_validator.py                                                     183    183     0%   6-290
autocoder_cc/validation/istio_configuration_validator.py                                             389    389     0%   8-1144
autocoder_cc/validation/mock_dependencies.py                                                          56     56     0%   3-78
autocoder_cc/validation/policy_engine.py                                                             153    153     0%   1-337
autocoder_cc/validation/resilience_patterns.py                                                       259    259     0%   6-435
autocoder_cc/validation/schema_framework.py                                                          126     72    43%   144, 157, 174-199, 208-234, 243-256, 261-276, 286, 291-343
autocoder_cc/validation/schema_validator.py                                                          179    179     0%   6-324
autocoder_cc/validation/sla_validator.py                                                             204    204     0%   6-508
autocoder_cc/validation/validation_failure_handler.py                                                130    130     0%   6-484
--------------------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                              54533  49418     9%
Coverage HTML written to dir htmlcov
[31m[1mFAIL Required test coverage of 10% not reached. Total coverage: 9.38%
[0m[33m============================================= [32m1 passed[0m, [33m[1m56 warnings[0m[33m in 18.64s[0m[33m =============================================[0m
