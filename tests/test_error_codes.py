#!/usr/bin/env python3
"""Test error code system works properly"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autocoder_cc.errors.error_codes import (
    AutocoderError, RecipeError, 
    ValidationError, ComponentGenerationError, ErrorCode
)

def test_error_codes_exist():
    """Test that all required error codes exist"""
    
    # Recipe errors
    assert ErrorCode.RECIPE_NOT_FOUND.value == 1001
    assert ErrorCode.RECIPE_NO_IMPLEMENTATION.value == 1003
    
    # Validation errors  
    assert ErrorCode.VALIDATION_FAILED.value == 2001
    assert ErrorCode.VALIDATION_BYPASSED_ILLEGALLY.value == 2004
    
    # LLM errors
    assert ErrorCode.LLM_FALLBACK_DISABLED.value == 5003
    
    print("✅ All required error codes exist")
    return True

def test_error_creation():
    """Test creating errors with codes"""
    
    # Test creating errors with codes
    error = RecipeError(
        code=ErrorCode.RECIPE_NOT_FOUND,
        message="Test recipe not found",
        details={"recipe": "TestRecipe"}
    )
    
    assert error.code == ErrorCode.RECIPE_NOT_FOUND
    assert "Test recipe not found" in str(error)
    assert error.details["recipe"] == "TestRecipe"
    
    # Test error message format includes code
    assert f"[ERROR {ErrorCode.RECIPE_NOT_FOUND.value}]" in str(error)
    
    print("✅ Error creation works correctly")
    return True

def test_different_error_types():
    """Test different error types"""
    
    # Component Generation Error
    comp_error = ComponentGenerationError(
        code=ErrorCode.COMPONENT_GENERATION_FAILED,
        message="Generation failed",
        details={"component": "test"}
    )
    assert comp_error.code == ErrorCode.COMPONENT_GENERATION_FAILED
    
    # Validation Error
    val_error = ValidationError(
        code=ErrorCode.VALIDATION_FAILED,
        message="Validation failed",
        details={"component": "test"}
    )
    assert val_error.code == ErrorCode.VALIDATION_FAILED
    
    print("✅ Different error types work")
    return True

if __name__ == "__main__":
    test_error_codes_exist()
    test_error_creation()
    test_different_error_types()
    print("\n✅ All error code tests passed")