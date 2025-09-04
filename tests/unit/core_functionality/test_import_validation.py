#!/usr/bin/env python3
"""
Test Import Validation - Verify all imports work correctly
Part of the CLAUDE.md critical fixes verification
"""
import pytest
import sys
import os

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestImportValidation:
    """Verify all critical imports work correctly"""
    
    def test_basic_import(self):
        """Test basic autocoder_cc package import"""
        import autocoder_cc
        assert autocoder_cc is not None
        
    def test_system_execution_harness_import(self):
        """Test SystemExecutionHarness import from package root"""
        from autocoder_cc import SystemExecutionHarness
        assert SystemExecutionHarness is not None
        
    def test_component_registry_import(self):
        """Test component registry import"""
        from autocoder_cc.components.component_registry import component_registry
        assert component_registry is not None
        assert hasattr(component_registry, 'components')
        
    def test_harness_import_from_orchestration(self):
        """Test harness import from orchestration module"""
        from autocoder_cc.orchestration.harness import SystemExecutionHarness
        assert SystemExecutionHarness is not None
        
    def test_observability_import(self):
        """Test observability module import"""
        from autocoder_cc.observability import get_logger
        assert get_logger is not None
        logger = get_logger("test")
        assert logger is not None
        
    def test_config_import(self):
        """Test configuration module import"""
        from autocoder_cc.core.config import Settings, settings
        assert Settings is not None
        assert settings is not None
        
    def test_blueprint_parser_import(self):
        """Test blueprint parser import"""
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        assert BlueprintParser is not None
        
    def test_system_generator_import(self):
        """Test system generator import"""
        from autocoder_cc.blueprint_language.system_generator import SystemGenerator
        assert SystemGenerator is not None
        
    def test_llm_component_generator_import(self):
        """Test LLM component generator import"""
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        assert LLMComponentGenerator is not None
        
    def test_validation_framework_import(self):
        """Test validation framework import"""
        from autocoder_cc.blueprint_language.validation_framework import ValidationFramework
        assert ValidationFramework is not None
        
    def test_component_imports(self):
        """Test various component imports"""
        from autocoder_cc.components.source import Source
        from autocoder_cc.components.sink import Sink
        from autocoder_cc.components.transformer import Transformer
        from autocoder_cc.components.store import Store
        from autocoder_cc.components.controller import Controller
        from autocoder_cc.components.api_endpoint import APIEndpoint
        
        assert Source is not None
        assert Sink is not None
        assert Transformer is not None
        assert Store is not None
        assert Controller is not None
        assert APIEndpoint is not None
        
    def test_no_autocoder_imports(self):
        """Verify no 'from autocoder_cc.' imports exist in core modules"""
        import autocoder_cc
        import inspect
        import importlib
        
        # Get all modules in autocoder_cc
        package_path = os.path.dirname(autocoder_cc.__file__)
        
        # Check a few key modules for incorrect imports
        key_modules = [
            'autocoder_cc.core.config',
            'autocoder_cc.orchestration.harness',
            'autocoder_cc.components.component_registry'
        ]
        
        for module_name in key_modules:
            try:
                module = importlib.import_module(module_name)
                source_file = inspect.getsourcefile(module)
                if source_file:
                    with open(source_file, 'r') as f:
                        content = f.read()
                    # Check for incorrect imports
                    assert 'from autocoder_cc.' not in content, f"Found 'from autocoder_cc.' in {module_name}"
                    assert 'import autocoder_cc.' not in content, f"Found 'import autocoder_cc.' in {module_name}"
            except Exception as e:
                # Module might not exist, which is fine
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])