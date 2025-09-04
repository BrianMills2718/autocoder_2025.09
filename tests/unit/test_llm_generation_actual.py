import pytest
"""
Test actual LLM generation to verify ComposedComponent usage.
This test actually calls the LLM to ensure templates work.
"""

import unittest
import tempfile
import os
import ast
from pathlib import Path
from unittest.mock import MagicMock

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
from autocoder_cc.validation.integration_validator import IntegrationValidator


class TestActualLLMGeneration(unittest.TestCase):
    """Test that LLM actually generates correct components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = LLMComponentGenerator()
        self.validator = IntegrationValidator()
        
    def test_store_generation_uses_composed_component(self):
        """Test actual Store generation uses ComposedComponent."""
        # Create blueprint component
        blueprint_component = MagicMock()
        blueprint_component.name = "RealStore"
        blueprint_component.type = "Store"
        blueprint_component.bindings = []
        blueprint_component.functions = [{
            'name': 'store_item',
            'inputs': ['item_data'],
            'outputs': ['item_id'],
            'business_logic': 'Store an item and return its unique ID'
        }]
        
        try:
            # Generate actual component
            result = self.generator.generate_component_logic(
                blueprint_component,
                output_dir=self.temp_dir
            )
            
            # If result is a dict, get the implementation
            if isinstance(result, dict):
                component_code = result.get('implementation', '')
            else:
                component_code = result
                
            # Save for debugging
            debug_file = os.path.join(self.temp_dir, "generated_store.py")
            with open(debug_file, 'w') as f:
                f.write(component_code)
            print(f"Generated Store saved to: {debug_file}")
            
            # Validate structure
            self.assertIn("ComposedComponent", component_code)
            self.assertNotIn("StandaloneComponentBase", component_code)
            
            # Parse and validate AST
            try:
                tree = ast.parse(component_code)
                
                # Find class definition
                class_found = False
                uses_composed = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_found = True
                        # Check base class
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id == 'ComposedComponent':
                                uses_composed = True
                                
                self.assertTrue(class_found, "No class definition found")
                self.assertTrue(uses_composed, "Class does not inherit from ComposedComponent")
                
                # Validate with integration validator
                validation_result = self.validator.validate_component_integration(
                    component_code, 
                    'Store'
                )
                
                if not validation_result['valid']:
                    print(f"Validation errors: {validation_result['errors']}")
                    
                self.assertTrue(
                    validation_result['valid'],
                    f"Component failed validation: {validation_result['errors']}"
                )
                
            except SyntaxError as e:
                self.fail(f"Generated code has syntax error: {e}")
                
        except Exception as e:
            # If LLM is not configured, skip test
            if "API key" in str(e) or "credentials" in str(e).lower():
                self.skipTest(f"LLM not configured: {e}")
            else:
                raise
                
    def test_api_generation_uses_composed_component(self):
        """Test actual API generation uses ComposedComponent."""
        blueprint_component = MagicMock()
        blueprint_component.name = "RealAPI"
        blueprint_component.type = "API"
        blueprint_component.bindings = ["RealStore"]
        blueprint_component.functions = [{
            'name': 'handle_request',
            'inputs': ['request_data'],
            'outputs': ['response_data'],
            'business_logic': 'Process HTTP request and return response'
        }]
        
        try:
            # Generate actual component
            result = self.generator.generate_component_logic(
                blueprint_component,
                output_dir=self.temp_dir
            )
            
            # Extract code
            if isinstance(result, dict):
                component_code = result.get('implementation', '')
            else:
                component_code = result
                
            # Save for debugging
            debug_file = os.path.join(self.temp_dir, "generated_api.py")
            with open(debug_file, 'w') as f:
                f.write(component_code)
            print(f"Generated API saved to: {debug_file}")
            
            # Basic checks
            self.assertIn("ComposedComponent", component_code)
            self.assertNotIn("StandaloneComponentBase", component_code)
            
            # Check for binding method
            if "set_store_component" not in component_code:
                print("Warning: API component missing set_store_component method")
                
            # Validate with integration validator
            validation_result = self.validator.validate_component_integration(
                component_code,
                'API'
            )
            
            if validation_result['warnings']:
                print(f"Validation warnings: {validation_result['warnings']}")
                
            self.assertTrue(
                validation_result['valid'],
                f"Component failed validation: {validation_result['errors']}"
            )
            
        except Exception as e:
            if "API key" in str(e) or "credentials" in str(e).lower():
                self.skipTest(f"LLM not configured: {e}")
            else:
                raise
                
    @pytest.mark.asyncio
    async def test_generated_methods_correct(self):
        """Test that generated components have correct methods."""
        blueprint_component = MagicMock()
        blueprint_component.name = "MethodTest"
        blueprint_component.type = "Processing"
        blueprint_component.bindings = []
        blueprint_component.functions = []
        
        try:
            result = self.generator.generate_component_logic(
                blueprint_component,
                output_dir=self.temp_dir
            )
            
            if isinstance(result, dict):
                component_code = result.get('implementation', '')
            else:
                component_code = result
                
            # Check for correct methods
            self.assertIn("def setup(self)", component_code)
            self.assertIn("async def process_item(self", component_code)
            self.assertIn("def cleanup(self)", component_code)
            
            # Should NOT have old methods
            self.assertNotIn("def teardown(", component_code)
            
            # Validate lifecycle
            lifecycle_valid, lifecycle_errors = self.validator.validate_lifecycle(component_code)
            self.assertTrue(
                lifecycle_valid,
                f"Lifecycle validation failed: {lifecycle_errors}"
            )
            
        except Exception as e:
            if "API key" in str(e) or "credentials" in str(e).lower():
                self.skipTest(f"LLM not configured: {e}")
            else:
                raise
                
    @pytest.mark.asyncio
    async def test_no_imports_in_generated_code(self):
        """Test that generated code doesn't include imports."""
        blueprint_component = MagicMock()
        blueprint_component.name = "NoImportTest"
        blueprint_component.type = "Store"
        blueprint_component.bindings = []
        blueprint_component.functions = []
        
        try:
            result = self.generator.generate_component_logic(
                blueprint_component,
                output_dir=self.temp_dir
            )
            
            if isinstance(result, dict):
                component_code = result.get('implementation', '')
            else:
                component_code = result
                
            # Check first line is not an import
            lines = component_code.strip().split('\n')
            if lines:
                first_non_empty = next((l for l in lines if l.strip()), '')
                
                # First line should be class definition or comment
                self.assertFalse(
                    first_non_empty.startswith('from '),
                    "Generated code should not start with imports"
                )
                self.assertFalse(
                    first_non_empty.startswith('import '),
                    "Generated code should not start with imports"
                )
                
        except Exception as e:
            if "API key" in str(e) or "credentials" in str(e).lower():
                self.skipTest(f"LLM not configured: {e}")
            else:
                raise
                
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            # Keep temp dir for debugging if test fails
            if hasattr(self, '_outcome'):
                if not self._outcome.success:
                    print(f"Test failed. Generated files kept in: {self.temp_dir}")
                    return
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)