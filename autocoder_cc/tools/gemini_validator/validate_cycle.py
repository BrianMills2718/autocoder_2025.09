#!/usr/bin/env python3
"""
Cycle Validation Helper

Ensures proper validation process is followed for each development cycle.
Prevents validation suboptimality by enforcing structured validation claims.
"""

import sys
import os
from pathlib import Path
import argparse
import subprocess

def check_validation_claims_file(claims_file: Path) -> bool:
    """Check if validation claims file meets quality standards."""
    if not claims_file.exists():
        print(f"❌ Validation claims file not found: {claims_file}")
        return False
    
    content = claims_file.read_text()
    
    # Check for required sections
    required_sections = [
        "Files to examine",
        "Success criteria", 
        "Validation method",
        "VALIDATION COMMAND"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections: {missing_sections}")
        return False
    
    # Check for checkbox criteria
    if "- [ ]" not in content:
        print("❌ No checkbox success criteria found. Use '- [ ]' format.")
        return False
    
    # Check for specific file paths
    if ".py" not in content:
        print("❌ No specific file paths found. Include actual file paths to examine.")
        return False
    
    print("✅ Validation claims file meets quality standards")
    return True

def run_validation(claims_file: Path, target_dir: str) -> bool:
    """Run Gemini validation with structured prompt."""
    
    # Construct detailed validation prompt
    validation_prompt = (
        "Validate each claim systematically using the provided success criteria and validation methods. "
        "For each claim: "
        "1) Examine the specified files and line numbers "
        "2) Check each success criterion individually "
        "3) Report PASS/FAIL for each criterion with specific evidence "
        "4) Quote relevant code snippets as proof "
        "5) Identify any missing implementations "
        "Be thorough and specific - vague assessments are not acceptable."
    )
    
    cmd = [
        "python", "validation/gemini_cycle_review.py", target_dir,
        "--claims", str(claims_file),
        "--prompt", validation_prompt
    ]
    
    print(f"🤖 Running validation command:")
    print(f"   {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd="tools", capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Validation completed successfully")
            return True
        else:
            print(f"❌ Validation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return False

def create_cycle21_validation_claims() -> str:
    """Create validation claims content for Cycle 21 Evidence-Based Validation"""
    from datetime import datetime
    
    return f"""# Validation Claims - Cycle 21: Evidence-Based Validation

## Overview
This file specifies concrete validation claims for Cycle 21 implementation focused on evidence-based validation with automated scanning and concrete demonstrations.

## Success Criteria

### ✅ V.1: Complete Evidence-Based Validation
**Files to examine:**
- `tools/validation_scanner.py` (lines 1-800+)
- `tools/validation_pipeline.py` (lines 1-600+)

**Success criteria:**
- [ ] Automated hardcoded value scanning with regex patterns and AST analysis implemented
- [ ] Comprehensive validation report generation with file-by-file analysis
- [ ] CI/CD pipeline integration with exit codes and notifications
- [ ] Multiple export formats (JSON, HTML, CSV) working
- [ ] Performance baseline comparison functionality

**Validation method:**
Search for `class HardcodedValueDetector` and verify AST-based scanning
Search for `class ValidationPipeline` and verify CI/CD integration
Check for regex patterns in `self.patterns` dictionary
Verify report generation methods `export_report` with multiple formats

### ✅ V.2: Demonstrate OpenTelemetry Backend Integration  
**Files to examine:**
- `autocoder_cc/autocoder/observability/` directory
- Search for Jaeger and Prometheus integration code
- Look for concrete backend demonstration scripts

**Success criteria:**
- [ ] Local Jaeger and Prometheus instances setup documented
- [ ] Actual data export to backends demonstrated with screenshots/logs
- [ ] Health checks for backend connectivity implemented
- [ ] Setup instructions documented for integration testing

**Validation method:**
Search for `jaeger` and `prometheus` in observability modules
Look for health check implementations in observability code
Check for backend export configuration and connection testing

### ✅ V.3: Strengthen AST-Based Validation
**Files to examine:**
- `autocoder_cc/autocoder/validation/ast_analyzer.py` (enhanced version)
- Search for AST validation rule engine implementation

**Success criteria:**
- [ ] String-based validation replaced with comprehensive AST analysis
- [ ] AST validation rule engine for component pattern validation
- [ ] ComposedComponent compliance checking via AST
- [ ] Comprehensive AST visitor patterns implemented

**Validation method:**
Search for `ast.NodeVisitor` classes and validation rules
Verify removal of string matching in favor of AST parsing
Check for component pattern validation in AST analyzers

### ✅ V.4: Full LLM Generator Validation
**Files to examine:**
- `autocoder_cc/blueprint_language/llm_component_generator.py`
- Search for UnifiedComponent references throughout codebase

**Success criteria:**
- [ ] Comprehensive audit confirms no UnifiedComponent references remain
- [ ] Generated component examples demonstrate ComposedComponent compliance
- [ ] Regression tests for LLM prompt consistency implemented
- [ ] Automated UnifiedComponent reference detection

**Validation method:**
Search entire codebase for "UnifiedComponent" patterns
Check LLM generator prompts for ComposedComponent enforcement
Verify generated component examples use correct architecture

### ✅ V.5: Automated Hardcoded Value Detection
**Files to examine:**
- `tools/hardcode_scanner.py` (if separate from validation_scanner.py)
- Pre-commit hook configurations
- CI/CD pipeline validation integration

**Success criteria:**
- [ ] Comprehensive scanning for ports, URLs, paths, placeholder strings
- [ ] Whitelist management for acceptable hardcoded values
- [ ] Integration with pre-commit hooks and CI/CD pipeline
- [ ] Detailed reports with file locations and severity levels

**Validation method:**
Search for hardcoded value detection patterns and rules
Check for CI/CD integration scripts and configurations
Verify whitelist functionality and policy enforcement

## VALIDATION COMMAND

```bash
# Test validation scanner
python tools/validation_scanner.py autocoder_cc --output validation_test_report.json

# Test validation pipeline  
python tools/validation_pipeline.py --project-path autocoder_cc --fail-on-critical --score-threshold 90

# Search for UnifiedComponent references
rg -i "unifiedcomponent" autocoder_cc/

# Test AST analyzer enhancements
python -c "from autocoder_cc.autocoder.validation.ast_analyzer import *; print('AST analyzer imported successfully')"
```

Generated: {datetime.now().isoformat()}
"""

def create_validation_claims_template(cycle_num: int) -> Path:
    """Create a validation claims file from template."""
    claims_file = Path(f"validation_claims_cycle{cycle_num}.md")
    
    if cycle_num == 21:
        # Use Cycle 21 specific content
        claims_content = create_cycle21_validation_claims()
    else:
        # Try to use template
        template_path = Path("validation_claims_template.md")
        if not template_path.exists():
            print(f"❌ Template not found: {template_path}")
            sys.exit(1)
        
        # Copy template and update cycle number
        template_content = template_path.read_text()
        claims_content = template_content.replace("[N]", str(cycle_num))
    
    claims_file.write_text(claims_content)
    print(f"✅ Created validation claims file: {claims_file}")
    print(f"📝 Please edit {claims_file} with specific claims before validation")
    
    return claims_file

def main():
    parser = argparse.ArgumentParser(description="Cycle Validation Helper")
    parser.add_argument("cycle", type=int, help="Cycle number to validate")
    parser.add_argument("--target", default="autocoder_cc", help="Target directory to validate")
    parser.add_argument("--create-template", action="store_true", help="Create validation claims template")
    parser.add_argument("--check-only", action="store_true", help="Only check claims file quality")
    
    args = parser.parse_args()
    
    claims_file = Path(f"validation_claims_cycle{args.cycle}.md")
    
    if args.create_template:
        create_validation_claims_template(args.cycle)
        return
    
    # Check claims file quality
    if not check_validation_claims_file(claims_file):
        print("\n💡 To create a template:")
        print(f"   python validate_cycle.py {args.cycle} --create-template")
        sys.exit(1)
    
    if args.check_only:
        print("✅ Claims file check passed")
        return
    
    # Run validation
    success = run_validation(claims_file, args.target)
    
    if success:
        print("\n🎉 Cycle validation completed successfully!")
    else:
        print("\n❌ Cycle validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()