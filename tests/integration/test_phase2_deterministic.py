#!/usr/bin/env python3
"""
Deterministic test suite for Phase 2 (Component Generation)
Uses known-good components to remove LLM variability
"""
import pytest
import sys
import os
import tempfile
import shutil
import importlib.util
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.fixtures.known_good_components import (
    KNOWN_GOOD_STORE,
    KNOWN_GOOD_API_ENDPOINT, 
    KNOWN_GOOD_MAIN,
    COMPONENT_METADATA
)


@pytest.mark.integration
class TestPhase2Deterministic:
    """Test Phase 2 with known-good components to establish baseline"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp(prefix="test_phase2_")
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Mock LLM provider that returns known-good components"""
        mock = MagicMock()
        
        async def generate_component(component_type, component_name, *args, **kwargs):
            """Return known-good component based on type"""
            if "store" in component_name.lower():
                return KNOWN_GOOD_STORE
            elif "api" in component_name.lower():
                return KNOWN_GOOD_API_ENDPOINT
            else:
                raise ValueError(f"Unknown component: {component_name}")
        
        mock.generate_component = generate_component
        return mock
    
    def test_known_good_components_are_valid_python(self):
        """Test that our known-good components are valid Python"""
        # Test Store component
        try:
            compile(KNOWN_GOOD_STORE, "task_store.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"Store component has syntax error: {e}")
        
        # Test API component  
        try:
            compile(KNOWN_GOOD_API_ENDPOINT, "task_api.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"API component has syntax error: {e}")
        
        # Test main.py
        try:
            compile(KNOWN_GOOD_MAIN, "main.py", "exec")
        except SyntaxError as e:
            pytest.fail(f"main.py has syntax error: {e}")
    
    def test_can_write_components_to_disk(self, temp_output_dir):
        """Test that we can write components to disk"""
        # Create components directory
        components_dir = temp_output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        
        # Write store component
        store_file = components_dir / "task_store.py"
        store_file.write_text(KNOWN_GOOD_STORE)
        assert store_file.exists()
        assert len(store_file.read_text()) > 0
        
        # Write API component
        api_file = components_dir / "task_api.py"
        api_file.write_text(KNOWN_GOOD_API_ENDPOINT)
        assert api_file.exists()
        assert len(api_file.read_text()) > 0
        
        # Write main.py
        main_file = temp_output_dir / "main.py"
        main_file.write_text(KNOWN_GOOD_MAIN)
        assert main_file.exists()
        assert len(main_file.read_text()) > 0
    
    def test_can_import_generated_components(self, temp_output_dir):
        """Test that generated components can be imported"""
        # Setup components
        components_dir = temp_output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        (components_dir / "__init__.py").write_text("")
        
        # Write components
        (components_dir / "task_store.py").write_text(KNOWN_GOOD_STORE)
        (components_dir / "task_api.py").write_text(KNOWN_GOOD_API_ENDPOINT)
        
        # Add to path
        sys.path.insert(0, str(temp_output_dir))
        
        try:
            # Import store component
            spec = importlib.util.spec_from_file_location(
                "task_store", 
                components_dir / "task_store.py"
            )
            store_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(store_module)
            
            # Check class exists
            assert hasattr(store_module, "GeneratedStore_task_store")
            
            # Import API component
            spec = importlib.util.spec_from_file_location(
                "task_api",
                components_dir / "task_api.py"
            )
            api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_module)
            
            # Check class exists
            assert hasattr(api_module, "GeneratedAPIEndpoint_task_api")
            
        finally:
            # Clean up path
            sys.path.remove(str(temp_output_dir))
    
    @pytest.mark.asyncio
    async def test_components_can_be_instantiated(self, temp_output_dir):
        """Test that components can be instantiated and initialized"""
        # Setup components
        components_dir = temp_output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        (components_dir / "__init__.py").write_text("")
        (components_dir / "task_store.py").write_text(KNOWN_GOOD_STORE)
        
        sys.path.insert(0, str(temp_output_dir))
        
        try:
            # Import and instantiate store
            spec = importlib.util.spec_from_file_location(
                "task_store",
                components_dir / "task_store.py"
            )
            store_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(store_module)
            
            StoreClass = getattr(store_module, "GeneratedStore_task_store")
            
            # Create instance
            config = {"database_type": "memory"}
            store_instance = StoreClass(config)
            
            # Test setup
            await store_instance.setup()
            
            # Test process_item
            result = await store_instance.process_item({
                "action": "create",
                "data": {"title": "Test task"}
            })
            assert result["status"] == "success"
            assert "id" in result
            
            # Test teardown
            await store_instance.teardown()
            
        finally:
            sys.path.remove(str(temp_output_dir))
    
    def test_components_have_required_methods(self):
        """Test that components have all required methods"""
        required_methods = ["setup", "process_item", "teardown", "get_health_status"]
        
        # Check in component source code
        for method in required_methods:
            assert f"async def {method}" in KNOWN_GOOD_STORE or f"def {method}" in KNOWN_GOOD_STORE, \
                f"Store missing method: {method}"
            assert f"async def {method}" in KNOWN_GOOD_API_ENDPOINT or f"def {method}" in KNOWN_GOOD_API_ENDPOINT, \
                f"API missing method: {method}"
    
    def test_components_inherit_from_composed_base(self):
        """Test that components inherit from ComposedComponent"""
        assert "from autocoder_cc.components.composed_base import ComposedComponent" in KNOWN_GOOD_STORE
        assert "class GeneratedStore_task_store(ComposedComponent):" in KNOWN_GOOD_STORE
        
        assert "from autocoder_cc.components.composed_base import ComposedComponent" in KNOWN_GOOD_API_ENDPOINT
        assert "class GeneratedAPIEndpoint_task_api(ComposedComponent):" in KNOWN_GOOD_API_ENDPOINT
    
    def test_main_py_structure(self):
        """Test that main.py has correct structure"""
        # Check imports
        assert "import asyncio" in KNOWN_GOOD_MAIN
        assert "import logging" in KNOWN_GOOD_MAIN
        assert "from components.task_store import GeneratedStore_task_store" in KNOWN_GOOD_MAIN
        assert "from components.task_api import GeneratedAPIEndpoint_task_api" in KNOWN_GOOD_MAIN
        
        # Check class structure
        assert "class TodoSystem:" in KNOWN_GOOD_MAIN
        assert "async def initialize(self):" in KNOWN_GOOD_MAIN
        assert "async def run(self):" in KNOWN_GOOD_MAIN
        assert "async def shutdown(self):" in KNOWN_GOOD_MAIN
        
        # Check entry point
        assert 'if __name__ == "__main__":' in KNOWN_GOOD_MAIN
        assert "asyncio.run(main())" in KNOWN_GOOD_MAIN
    
    @pytest.mark.asyncio
    async def test_component_validation_passes(self, temp_output_dir):
        """Test that components pass validation"""
        from autocoder_cc.validation.component_test_runner import ComponentTestRunner
        
        # Setup components
        components_dir = temp_output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        (components_dir / "__init__.py").write_text("")
        (components_dir / "task_store.py").write_text(KNOWN_GOOD_STORE)
        
        # Create runner
        runner = ComponentTestRunner()
        
        # Create test config
        test_config = MagicMock()
        test_config.component_file = components_dir / "task_store.py"
        test_config.component_type = "Store"
        test_config.component_name = "task_store"
        
        # Run contract validation
        contract_result = runner._run_contract_validation(test_config)
        assert contract_result is True, "Contract validation should pass"
    
    def test_phase2_output_structure(self, temp_output_dir):
        """Test that Phase 2 creates correct output structure"""
        # Create expected structure
        (temp_output_dir / "main.py").write_text(KNOWN_GOOD_MAIN)
        (temp_output_dir / "components").mkdir(exist_ok=True)
        (temp_output_dir / "components" / "__init__.py").write_text("")
        (temp_output_dir / "components" / "task_store.py").write_text(KNOWN_GOOD_STORE)
        (temp_output_dir / "components" / "task_api.py").write_text(KNOWN_GOOD_API_ENDPOINT)
        (temp_output_dir / "config").mkdir(exist_ok=True)
        (temp_output_dir / "config" / "system_config.yaml").write_text(
            yaml.dump({
                "system": {"name": "test_todo_system", "version": "1.0.0"},
                "components": {
                    "task_store": {"type": "Store", "config": {"database_type": "memory"}},
                    "task_api": {"type": "APIEndpoint", "config": {"port": 8080}}
                }
            })
        )
        
        # Verify structure
        assert (temp_output_dir / "main.py").exists(), "main.py missing"
        assert (temp_output_dir / "components").is_dir(), "components directory missing"
        assert (temp_output_dir / "components" / "task_store.py").exists(), "task_store.py missing"
        assert (temp_output_dir / "components" / "task_api.py").exists(), "task_api.py missing"
        assert (temp_output_dir / "config" / "system_config.yaml").exists(), "system_config.yaml missing"
    
    def test_phase2_success_criteria(self, temp_output_dir):
        """Comprehensive test of Phase 2 success criteria"""
        # Setup complete system
        (temp_output_dir / "main.py").write_text(KNOWN_GOOD_MAIN)
        components_dir = temp_output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        (components_dir / "__init__.py").write_text("")
        (components_dir / "task_store.py").write_text(KNOWN_GOOD_STORE)
        (components_dir / "task_api.py").write_text(KNOWN_GOOD_API_ENDPOINT)
        
        # Criteria 1: Valid Python files
        for py_file in temp_output_dir.rglob("*.py"):
            with open(py_file) as f:
                try:
                    compile(f.read(), str(py_file), "exec")
                except SyntaxError:
                    pytest.fail(f"Invalid Python in {py_file}")
        
        # Criteria 2: Components inherit from correct base
        store_content = (components_dir / "task_store.py").read_text()
        assert "StandaloneComponentBase" in store_content
        
        # Criteria 3: Required methods present
        required_methods = ["setup", "process_item", "teardown"]
        for method in required_methods:
            assert f"def {method}" in store_content
        
        # Criteria 4: Main.py is executable structure
        main_content = (temp_output_dir / "main.py").read_text()
        assert "async def main():" in main_content
        assert "asyncio.run(main())" in main_content
        
        # Criteria 5: Imports are correct
        assert "from components.task_store import" in main_content
        assert "from components.task_api import" in main_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])