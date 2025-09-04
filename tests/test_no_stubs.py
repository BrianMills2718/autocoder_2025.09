#!/usr/bin/env python3
"""Verify recipe expander has no stub implementations"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autocoder_cc.recipes.expander import RecipeExpander
from autocoder_cc.errors.error_codes import RecipeError, ErrorCode

def test_recipe_has_no_stubs():
    """Recipe should only provide structure, not implementations"""
    expander = RecipeExpander()
    
    # Generate code from recipe
    code = expander.expand_recipe("Store", "test_store", {})
    
    # Check for stub patterns that should NOT exist
    forbidden_patterns = [
        'return {"items": []}',
        'return {"data": {}}', 
        'return True  # Simplified',
        'return False  # Simplified',
        '# Simplified',
        'pass  # TODO',
        'def _add_item',  # Should not have implementations
        'def _get_item',   # Should not have implementations
        'def _is_duplicate',
        'def _evaluate_condition',
    ]
    
    for pattern in forbidden_patterns:
        assert pattern not in code, f"Found stub pattern: {pattern}"
    
    # Should have NotImplementedError to force LLM generation
    assert "NotImplementedError" in code
    assert "LLM must" in code or "LLM MUST" in code
    assert str(ErrorCode.RECIPE_NO_IMPLEMENTATION.value) in code
    
    print("✅ Recipe expander has no stubs")
    return True

def test_recipe_forces_implementation():
    """Verify recipe forces real implementation"""
    expander = RecipeExpander()
    
    # Test each recipe type (use available recipes)
    for recipe_name in ["Store", "Controller", "APIEndpoint"]:
        code = expander.expand_recipe(recipe_name, f"test_{recipe_name.lower()}", {})
        
        # Must raise NotImplementedError
        assert "NotImplementedError" in code
        assert "1003" in code  # ErrorCode.RECIPE_NO_IMPLEMENTATION
        
        print(f"✅ {recipe_name} recipe forces implementation")
    
    return True

if __name__ == "__main__":
    test_recipe_has_no_stubs()
    test_recipe_forces_implementation()
    print("\n✅ All recipe tests passed")