#!/usr/bin/env python3
"""
Claude Fixes Validation Script
==============================

This script runs a targeted Gemini review to validate all the specific claims
made about fixing the CLAUDE.md issues.
"""

import subprocess
import sys
from pathlib import Path

def run_gemini_validation():
    """Run Gemini review to validate all fixed issues"""
    
    # Custom prompt specifically for validating the fixes
    validation_prompt = """
    CRITICAL VALIDATION TASK: Assess whether ALL claimed fixes in the CLAUDE.md file have been properly implemented.

    Specifically validate these exact claims:

    **SECURITY FIXES CLAIMED:**
    1. Hardcoded credentials removed from autocoder/analysis/ast_parser.py:79 and tests/test_componentregistry_ast_integration.py:112
    2. Shell injection fixed in tests/test_ast_security_validation.py:86 by replacing subprocess.run(cmd, shell=True) with subprocess.run(cmd.split())
    3. Unsafe exec() replaced in tests/component_test_runner.py:269 with safe importlib.util mechanism

    **SCHEMA VERSION MANAGER FIXES CLAIMED:**
    4. Added detect_schema_version() method to SchemaVersionManager
    5. Added migration_registry property with MigrationRegistry class
    6. Added migrate_blueprint() method
    7. Added validate_blueprint_version() method

    **MOCK REMOVAL FIXES CLAIMED:**
    8. Removed MockSchemaValidator, MockMigrationManager, MockConnectionPool from v5_enhanced_store.py
    9. Replaced with real V5DatabaseSchemaValidator, V5MigrationManager, V5DatabaseConnectionPool implementations

    **API VERSIONING FIXES CLAIMED:**
    10. Added /api/v{version}/ prefixes to all generated API endpoints in APIEndpointGenerator
    11. Added /api/v{version}/auth/ prefixes to AuthEndpointGenerator routes
    12. Added /api/v{version}/commands/ and /api/v{version}/queries/ prefixes to FastAPICQRSGenerator

    **RESOURCE MANAGEMENT FIXES CLAIMED:**
    13. Added cleanup() method to MessageBusSource for RabbitMQ connections
    14. Added cleanup() method to MetricsCollector for OpenTelemetry resources
    15. Added cleanup() methods to RateLimiter and CircuitBreaker capability classes
    16. Enhanced V5EnhancedStore cleanup to handle connection pool resources

    FOR EACH CLAIM ABOVE:
    - Verify the exact file and line mentioned exists and contains the claimed fix
    - Check if the implementation is complete and functional (not just placeholder)
    - Identify any discrepancies between claims and actual implementation
    - Flag any remaining security vulnerabilities or missing implementations

    PROVIDE DETAILED VERIFICATION:
    - List each claim as VERIFIED, PARTIALLY VERIFIED, or NOT VERIFIED
    - For any issues, provide exact file locations and missing/incorrect code
    - Assess overall production readiness based on actual implementation vs claims
    """

    cmd = [
        sys.executable,
        "autocoder_cc/tools/documentation/gemini_doc_review.py",
        "--docs", "autocoder_cc/CLAUDE.md",
        "--code", 
        "autocoder_cc/autocoder/core/schema_versioning.py",
        "autocoder_cc/autocoder/components/v5_enhanced_store.py", 
        "autocoder_cc/autocoder/generators/components/",
        "autocoder_cc/autocoder/components/message_bus.py",
        "autocoder_cc/autocoder/observability/metrics.py",
        "autocoder_cc/autocoder/capabilities/",
        "autocoder_cc/autocoder/analysis/ast_parser.py",
        "autocoder_cc/tests/test_componentregistry_ast_integration.py",
        "autocoder_cc/tests/test_ast_security_validation.py",
        "autocoder_cc/tests/component_test_runner.py",
        "--prompt", validation_prompt,
        "--output", "claude_fixes_validation_report.md"
    ]
    
    print("🔍 Running Claude fixes validation with Gemini...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Validation failed: {result.stderr}")
        return False
    else:
        print("✅ Validation completed successfully")
        return True

def main():
    print("🚀 Starting Claude fixes validation...")
    
    if run_gemini_validation():
        print("\n📄 Reading validation report...")
        report_path = Path("claude_fixes_validation_report.md")
        if report_path.exists():
            print(f"\n{'='*60}")
            print("CLAUDE FIXES VALIDATION REPORT")
            print(f"{'='*60}")
            print(report_path.read_text())
        else:
            print("❌ Validation report not found")
    else:
        print("❌ Validation process failed")

if __name__ == "__main__":
    main()