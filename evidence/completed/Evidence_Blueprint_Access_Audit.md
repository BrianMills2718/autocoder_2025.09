# Evidence: Blueprint Structure Migration - Complete Access Audit
Date: 2025-08-29
Task: Audit all blueprint access patterns in codebase

## Audit Results

### Total Violations Found: 219

### Top Files with Violations (by count):
1. **autocoder_cc/validation/context_builder.py** - 19 violations (PARTIALLY FIXED)
2. **tests/unit/test_system_generator.py** - 9 violations
3. **tests/unit/blueprint_generation/test_blueprint_generation_with_healing.py** - 7 violations
4. **tests/system/test_final_validation.py** - 7 violations
5. **tests/unit/reference_patterns/test_reference_integration.py** - 6 violations
6. **tests/integration/test_reference_integration.py** - 6 violations
7. **tests/fixtures/valid_blueprints.py** - 6 violations
8. **tests/fixtures/test_blueprints.py** - 6 violations
9. **autocoder_cc/validation/policy_engine.py** - 5 violations
10. **autocoder_cc/migration/blueprint_migrator.py** - 5 violations
11. **autocoder_cc/migration/blueprint_analyzer.py** - 5 violations
12. **autocoder_cc/blueprint_language/level3_real_integration_validator.py** - 5 violations
13. **autocoder_cc/blueprint_language/architectural_templates/template_selector.py** - 5 violations
14. **tests/validation/test_blueprint_structure_contract.py** - 4 violations
15. **tests/contracts/blueprint_structure_contract.py** - 4 violations (This is OK - it's the contract itself)
16. **autocoder_cc/core/schema_versioning.py** - 4 violations
17. **autocoder_cc/blueprint_language/system_generator.py** - 4 violations
18. **tests/unit/validation/test_pipeline_context.py** - 3 violations
19. **tests/unit/test_critical_paths.py** - 3 violations
20. **tests/integration/test_strict_validation.py** - 3 violations

### Critical Test Files Needing Migration (Priority Order):
1. tests/unit/validation/test_pipeline_context.py
2. tests/unit/test_system_generation.py (Note: file doesn't exist, likely test_system_generator.py)
3. tests/integration/test_strict_validation.py
4. tests/unit/blueprint_generation/test_blueprint_generation_with_healing.py
5. tests/system/test_final_validation.py
6. tests/unit/reference_patterns/test_reference_integration.py
7. tests/integration/test_reference_integration.py
8. tests/fixtures/valid_blueprints.py
9. tests/fixtures/test_blueprints.py
10. tests/unit/test_critical_paths.py

### Critical Production Files Needing Migration:
1. autocoder_cc/validation/context_builder.py (PARTIALLY FIXED - still has 19 violations)
2. autocoder_cc/validation/policy_engine.py (5 violations)
3. autocoder_cc/migration/blueprint_migrator.py (5 violations)
4. autocoder_cc/migration/blueprint_analyzer.py (5 violations)
5. autocoder_cc/blueprint_language/level3_real_integration_validator.py (5 violations)
6. autocoder_cc/blueprint_language/architectural_templates/template_selector.py (5 violations)
7. autocoder_cc/core/schema_versioning.py (4 violations)
8. autocoder_cc/blueprint_language/system_generator.py (4 violations)

## Migration Strategy

### Phase 1: Critical Test Files (Immediate)
- Start with the 3 priority test files mentioned in CLAUDE.md
- These are causing immediate test failures

### Phase 2: Test Fixtures
- Fix test fixtures to ensure all new tests use correct structure
- This prevents new violations from being introduced

### Phase 3: Production Code
- Fix production code starting with highest violation count
- context_builder.py needs completion of migration

### Phase 4: Remaining Tests
- Complete migration of all remaining test files

## Next Steps
1. Begin with tests/unit/validation/test_pipeline_context.py
2. Move to tests/unit/test_system_generator.py (or test_system_generation.py)
3. Complete tests/integration/test_strict_validation.py
4. Continue through the list systematically

## Verdict
❌ AUDIT COMPLETE: 219 violations found across 50+ files
🎯 READY TO MIGRATE: Priority list established, starting with critical test files