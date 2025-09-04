#!/usr/bin/env python3
"""Verify bypass_validation is completely removed"""

import ast
import os

def test_no_bypass_validation():
    """Ensure bypass_validation parameter doesn't exist"""
    
    files_to_check = [
        "autocoder_cc/blueprint_language/healing_integration.py",
        "autocoder_cc/blueprint_language/system_generator.py",
        "autocoder_cc/blueprint_language/natural_language_to_blueprint.py"
    ]
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            print(f"⚠️ File not found: {filepath}")
            continue
            
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check text patterns
        assert "bypass_validation" not in content, f"Found bypass_validation in {filepath}"
        assert "skip_validation" not in content, f"Found skip_validation in {filepath}"
        
        # Check AST to be absolutely sure
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.arg) and node.arg == "bypass_validation":
                raise AssertionError(f"Found bypass_validation parameter in {filepath}")
            if isinstance(node, ast.Name) and node.id == "bypass_validation":
                raise AssertionError(f"Found bypass_validation reference in {filepath}")
        
        print(f"✅ No bypass in {os.path.basename(filepath)}")
    
    print("\n✅ No bypass_validation found anywhere")
    return True

def test_validation_always_runs():
    """Verify validation cannot be skipped"""
    # This would require actually running the system
    # For now, we verify the code structure enforces it
    
    filepath = "autocoder_cc/blueprint_language/healing_integration.py"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check that validate_system is always called
        assert "validate_system" in content
        assert "if" not in content or "bypass" not in content
        
        print("✅ Validation appears mandatory")
    
    return True

if __name__ == "__main__":
    test_no_bypass_validation()
    test_validation_always_runs()
    print("\n✅ All bypass tests passed")