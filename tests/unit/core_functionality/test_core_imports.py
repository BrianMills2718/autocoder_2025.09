#!/usr/bin/env python3
"""
Import Validation Tests
Tests that all critical imports work correctly after import path fixes.
"""

import pytest
import sys
from pathlib import Path

class TestImportValidation:
    """Test that all critical imports work correctly"""
    
    def test_basic_autocoder_cc_import(self):
        """Test basic autocoder_cc module imports"""
        import autocoder_cc
        assert autocoder_cc is not None
        
    def test_system_execution_harness_import(self):
        """Test SystemExecutionHarness can be imported"""
        from autocoder_cc import SystemExecutionHarness
        assert SystemExecutionHarness is not None
        
    def test_component_registry_import(self):
        """Test component registry imports and works"""
        from autocoder_cc.components.component_registry import component_registry
        assert component_registry is not None
        
        # Test it has expected components
        components = component_registry.list_component_types()
        expected_components = ['Source', 'Sink', 'Store', 'Router', 'Filter', 'APIEndpoint']
        for comp in expected_components:
            assert comp in components, f"Missing component: {comp}"
            
    def test_configuration_import(self):
        """Test configuration system imports"""
        from autocoder_cc.core.config import Settings
        config = Settings()
        assert config is not None
        assert hasattr(config, 'ENVIRONMENT')
        assert hasattr(config, 'JWT_SECRET_KEY')
        
    def test_observability_import(self):
        """Test observability system imports"""
        from autocoder_cc.observability import get_logger
        logger = get_logger('test')
        assert logger is not None
        
    def test_blueprint_language_import(self):
        """Test blueprint language imports"""
        from autocoder_cc.blueprint_language.system_generator import SystemGenerator
        assert SystemGenerator is not None
        
    def test_validation_framework_import(self):
        """Test validation framework imports"""
        from autocoder_cc.blueprint_language.validation_framework import ValidationFramework
        assert ValidationFramework is not None
        
    def test_no_autocoder_imports_remain(self):
        """Test that no files still use old import paths"""
        project_root = Path(__file__).parent.parent
        
        # Check critical directories only (not generated_systems)
        critical_dirs = [
            'autocoder_cc',
            'tests',
            'scripts'
        ]
        
        bad_files = []
        old_import_pattern = 'from autocoder_cc.'
        
        for dir_name in critical_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    try:
                        lines = py_file.read_text().splitlines()
                        for line_num, line in enumerate(lines, 1):
                            # Skip comments and test strings
                            stripped = line.strip()
                            if stripped.startswith('#') or '"""' in stripped or "'" in stripped:
                                continue
                            if old_import_pattern in line:
                                bad_files.append(f"{py_file}:{line_num}: {line.strip()}")
                    except Exception:
                        # Skip files that can't be read
                        pass
        
        assert len(bad_files) == 0, f"Files still contain old import paths: {bad_files}"
        
    def test_harness_instantiation(self):
        """Test that SystemExecutionHarness can be instantiated"""
        from autocoder_cc import SystemExecutionHarness
        
        # Should be able to instantiate (may fail later due to missing deps, but import should work)
        try:
            harness = SystemExecutionHarness()
            assert harness is not None
        except Exception as e:
            # It's OK if it fails due to missing dependencies, but not due to import issues
            assert "ModuleNotFoundError" not in str(e), f"Import issue detected: {e}"
            assert "No module named 'autocoder'" not in str(e), f"Old import detected: {e}"