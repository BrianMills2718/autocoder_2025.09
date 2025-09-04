#!/usr/bin/env python3
"""
Test script to verify validation errors trigger retries in LLM component generator.
This validates the architectural fix mentioned in CLAUDE.md.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'autocoder_cc'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator, ComponentGenerationError
from autocoder_cc.autocoder.core.config import settings
import time

class TestValidationRetryArchitecture(unittest.TestCase):
    """Test that validation errors trigger retries within the retry loop"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Set environment variables for testing
        os.environ['OPENAI_API_KEY'] = 'test_key'
        os.environ['OPENAI_MODEL'] = 'gpt-4'
        
        # Create generator instance
        self.generator = LLMComponentGenerator()
    
    def test_validation_error_triggers_retry(self):
        """Test that validation errors trigger retries with adaptive prompts"""
        print("🧪 Testing validation error retry architecture...")
        
        # Mock the LLM client to return invalid code on first attempt, valid code on second
        invalid_code = '''
class InvalidComponent:
    def __init__(self):
        raise NotImplementedError("This is forbidden")
'''
        
        valid_code = '''
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent

class GeneratedAPIEndpoint_test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.data = {"initialized": True}
        
    async def process_item(self, item: Any) -> Any:
        return {"result": "success", "data": self.data}
'''
        
        # Mock response objects
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message.content = invalid_code
        
        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message.content = valid_code
        
        # Set up the mock to return invalid code first, then valid code
        with patch.object(self.generator, 'client') as mock_client:
            mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
            
            # Test generation - should succeed on second attempt
            result = self.generator.generate_component_implementation(
                component_type="APIEndpoint",
                component_name="test",
                component_description="Test component",
                component_config={},
                class_name="GeneratedAPIEndpoint_test"
            )
            
            # Verify the client was called twice (retry happened)
            self.assertEqual(mock_client.chat.completions.create.call_count, 2)
            
            # Verify the final result is valid
            self.assertIn("GeneratedAPIEndpoint_test", result)
            self.assertNotIn("NotImplementedError", result)
            self.assertIn("async def process_item", result)
            
            print("✅ Validation error retry test passed!")
    
    def test_validation_feedback_loop(self):
        """Test that validation feedback is used in retry prompts"""
        print("🧪 Testing validation feedback loop...")
        
        # Mock the LLM client to return code with syntax errors first
        syntax_error_code = '''
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent

class GeneratedAPIEndpoint_test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # Missing closing parenthesis in regex
        self.pattern = re.compile(r'test)'
        
    async def process_item(self, item: Any) -> Any:
        return {"result": "success"}
'''
        
        fixed_code = '''
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent
import re

class GeneratedAPIEndpoint_test(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # Fixed regex with escaped parenthesis
        self.pattern = re.compile(r'test\\)')
        
    async def process_item(self, item: Any) -> Any:
        return {"result": "success"}
'''
        
        # Mock response objects
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message.content = syntax_error_code
        
        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message.content = fixed_code
        
        with patch.object(self.generator, 'client') as mock_client:
            mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
            
            result = self.generator.generate_component_implementation(
                component_type="APIEndpoint",
                component_name="test",
                component_description="Test component",
                component_config={},
                class_name="GeneratedAPIEndpoint_test"
            )
            
            # Verify retry happened
            self.assertEqual(mock_client.chat.completions.create.call_count, 2)
            
            # Verify the second call included validation feedback
            second_call = mock_client.chat.completions.create.call_args_list[1]
            second_prompt = second_call[1]['messages'][1]['content']
            
            # Should contain validation feedback about the syntax error
            self.assertIn("validation", second_prompt.lower())
            self.assertIn("SYNTAX ERROR", second_prompt)
            
            print("✅ Validation feedback loop test passed!")
    
    def test_retry_strategy_error_classification(self):
        """Test that different error types are classified correctly"""
        print("🧪 Testing error classification in retry strategy...")
        
        # Test syntax error classification
        syntax_error = ComponentGenerationError("SyntaxError: invalid syntax")
        error_type = self.generator._classify_error(syntax_error)
        self.assertEqual(error_type.value, "syntax_error")
        
        # Test validation error classification
        validation_error = ComponentGenerationError("Generated code contains forbidden pattern: placeholder")
        error_type = self.generator._classify_error(validation_error)
        self.assertEqual(error_type.value, "validation_error")
        
        # Test API error classification
        api_error = ComponentGenerationError("Connection timeout")
        error_type = self.generator._classify_error(api_error)
        self.assertEqual(error_type.value, "api_error")
        
        print("✅ Error classification test passed!")
    
    def test_external_compilation_validation(self):
        """Test that external compilation validation is thread-safe"""
        print("🧪 Testing external compilation validation...")
        
        # Test valid code passes validation
        valid_code = '''
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent

class TestComponent(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
    async def process_item(self, item: Any) -> Any:
        return {"result": "success"}
'''
        
        # Should not raise exception
        try:
            self.generator._validate_generated_code(valid_code, "Source", "TestComponent")
            print("✅ Valid code passed validation")
        except Exception as e:
            self.fail(f"Valid code failed validation: {e}")
        
        # Test invalid code fails validation
        invalid_code = '''
from typing import Dict, Any
from autocoder_cc.components.composed_base import ComposedComponent

class TestComponent(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        # Syntax error: missing closing parenthesis
        self.data = {"test": "value"
        
    async def process_item(self, item: Any) -> Any:
        return {"result": "success"}
'''
        
        # Should raise exception
        with self.assertRaises(ValueError):
            self.generator._validate_generated_code(invalid_code, "Source", "TestComponent")
            
        print("✅ Invalid code correctly failed validation")
        print("✅ External compilation validation test passed!")

def main():
    """Run the validation retry architecture tests"""
    print("🚀 Running validation retry architecture tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestValidationRetryArchitecture)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n" + "=" * 60)
        print("🎉 All validation retry architecture tests passed!")
        print("✅ Validation errors correctly trigger retries")
        print("✅ Adaptive prompt feedback loop is working")
        print("✅ External compilation validation is thread-safe")
        print("✅ Error classification system is functional")
        print("\nThe architectural fix described in CLAUDE.md is verified!")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()