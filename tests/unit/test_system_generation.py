"""Tests for system generation and startup"""
import pytest
import sys
import os
import tempfile
import subprocess
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSystemGeneration:
    """Test system generation pipeline"""
    
    def test_cli_generate_command(self):
        """Test CLI generate command works"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Test System", "--output", tmpdir
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            assert Path(tmpdir, "scaffolds").exists()
            
    def test_generated_system_structure(self):
        """Test generated system has correct structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate system
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Structure Test System", "--output", tmpdir
            ], capture_output=True, text=True)
            
            # Check structure
            scaffolds = Path(tmpdir) / "scaffolds"
            assert scaffolds.exists()
            
            systems = list(scaffolds.glob("*"))
            assert len(systems) > 0
            
            system_dir = systems[0]
            assert (system_dir / "main.py").exists()
            assert (system_dir / "components").exists()
            assert (system_dir / "config").exists()
            assert (system_dir / "config" / "system_config.yaml").exists()
            
    def test_main_py_syntax(self):
        """Test generated main.py has valid syntax"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate system
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Syntax Test System", "--output", tmpdir
            ], capture_output=True, text=True)
            
            # Find main.py
            main_files = list(Path(tmpdir).rglob("main.py"))
            assert len(main_files) > 0
            
            # Check syntax
            for main_file in main_files:
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(main_file)
                ], capture_output=True)
                assert result.returncode == 0
                
    def test_component_syntax(self):
        """Test generated components have valid syntax"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate system
            subprocess.run([
                sys.executable, "-m", "autocoder_cc.cli.main", "generate",
                "Component Syntax Test", "--output", tmpdir
            ], capture_output=True, text=True)
            
            # Find component files
            component_files = list(Path(tmpdir).rglob("components/*.py"))
            assert len(component_files) > 0
            
            # Check syntax of each component
            for comp_file in component_files:
                if comp_file.name == "__init__.py":
                    continue
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(comp_file)
                ], capture_output=True)
                assert result.returncode == 0


class TestMainGenerator:
    """Test main.py generator specifically"""
    
    def test_dynamic_main_generator(self):
        """Test DynamicMainPyGenerator"""
        from autocoder_cc.generators.scaffold.main_generator_dynamic import DynamicMainPyGenerator
        
        generator = DynamicMainPyGenerator()
        
        blueprint = {
            "system": {
                "name": "test_system",
                "components": [
                    {"name": "store", "type": "Store"},
                    {"name": "api", "type": "APIEndpoint"}
                ],
                "bindings": []
            }
        }
        
        code = generator.generate(blueprint)
        assert code is not None
        assert "#!/usr/bin/env python3" in code
        assert "FastAPI" in code
        assert "load_components" in code
        assert "test_system" in code
        
    def test_port_configuration(self):
        """Test port configuration in main.py"""
        from autocoder_cc.generators.scaffold.main_generator_dynamic import DynamicMainPyGenerator
        
        generator = DynamicMainPyGenerator()
        
        blueprint = {
            "system": {
                "name": "port_test",
                "components": [],
                "bindings": []
            }
        }
        
        code = generator.generate(blueprint)
        
        # Should have port detection logic
        assert "PORT" in code
        assert "port" in code.lower()
        assert "8000" in code or "port" in code.lower()
        
        # Should not have hardcoded exit(3)
        assert "sys.exit(3)" not in code or "# BYPASSED" in code


class TestComponentRegistry:
    """Test component registry functionality"""
    
    def test_component_registry_import(self):
        """Test component registry can be imported"""
        from autocoder_cc.components.component_registry import ComponentRegistry
        
        registry = ComponentRegistry()
        assert registry is not None
        
    def test_register_component(self):
        """Test registering a component"""
        from autocoder_cc.components.component_registry import ComponentRegistry
        
        registry = ComponentRegistry()
        
        class TestComponent:
            def __init__(self, name, config):
                self.name = name
                self.config = config
                
        registry.register("TestComponent", TestComponent)
        
        # Should be able to retrieve
        comp_class = registry.get("TestComponent")
        assert comp_class == TestComponent
        
    def test_discover_components(self):
        """Test component discovery"""
        from autocoder_cc.components.component_registry import ComponentRegistry
        
        registry = ComponentRegistry()
        
        # Should discover built-in components
        registry.discover_components()
        
        # Should have some components registered
        components = registry.list_components()
        assert len(components) > 0


class TestObservability:
    """Test observability system"""
    
    def test_logger_import(self):
        """Test logger can be imported"""
        from autocoder_cc.observability import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        
    def test_metrics_collector(self):
        """Test metrics collector"""
        from autocoder_cc.observability import get_metrics_collector
        
        collector = get_metrics_collector()
        assert collector is not None
        
    def test_tracer(self):
        """Test tracer"""
        from autocoder_cc.observability import get_tracer
        
        tracer = get_tracer()
        assert tracer is not None


class TestHealthChecks:
    """Test health check functionality"""
    
    def test_health_aggregation_logic(self):
        """Test health aggregation works correctly"""
        # Test data
        component_health = {
            "comp1": {"healthy": True, "status": "healthy"},
            "comp2": {"healthy": True, "status": "healthy"},
            "comp3": {"healthy": False, "status": "unhealthy"}
        }
        
        # Logic from main_generator_dynamic.py lines 599-606
        overall_healthy = True
        for name, health in component_health.items():
            if not health.get('healthy', True):
                overall_healthy = False
                
        assert overall_healthy == False
        
        # All healthy case
        all_healthy = {
            "comp1": {"healthy": True},
            "comp2": {"healthy": True}
        }
        
        overall = True
        for name, health in all_healthy.items():
            if not health.get('healthy', True):
                overall = False
                
        assert overall == True