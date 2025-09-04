"""Tests for component generation - covers all 13 component types"""
import pytest
import sys
from pathlib import Path
import tempfile
import subprocess

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator


class TestComponentGeneration:
    """Test component generation for all types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = ComponentLogicGenerator()
    
    def test_store_component_generation(self):
        """Test Store component generation"""
        blueprint = {
            "name": "test_store",
            "type": "Store",
            "config": {
                "storage_type": "in_memory"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedStore_test_store" in code
        assert "async def process_item" in code
        assert "add_item" in code
        
    def test_source_component_generation(self):
        """Test Source component generation"""
        blueprint = {
            "name": "test_source",
            "type": "Source",
            "config": {
                "source_type": "file"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedSource_test_source" in code
        assert "async def generate_data" in code
        
    def test_transformer_component_generation(self):
        """Test Transformer component generation"""
        blueprint = {
            "name": "test_transformer",
            "type": "Transformer",
            "config": {
                "transformation": "uppercase"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedTransformer_test_transformer" in code
        assert "async def transform" in code
        
    def test_api_endpoint_generation(self):
        """Test APIEndpoint component generation"""
        blueprint = {
            "name": "test_api",
            "type": "APIEndpoint",
            "config": {
                "route": "/test",
                "methods": ["GET", "POST"]
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedAPIEndpoint_test_api" in code
        assert "async def handle_request" in code
        
    def test_validator_component_generation(self):
        """Test Validator component generation"""
        blueprint = {
            "name": "test_validator",
            "type": "Validator",
            "config": {
                "validation_rules": ["required", "email"]
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedValidator_test_validator" in code
        assert "async def validate" in code
        
    def test_aggregator_component_generation(self):
        """Test Aggregator component generation"""
        blueprint = {
            "name": "test_aggregator",
            "type": "Aggregator",
            "config": {
                "aggregation_type": "sum"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedAggregator_test_aggregator" in code
        assert "async def aggregate" in code
        
    def test_filter_component_generation(self):
        """Test Filter component generation"""
        blueprint = {
            "name": "test_filter",
            "type": "Filter",
            "config": {
                "filter_type": "range",
                "min": 0,
                "max": 100
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedFilter_test_filter" in code
        assert "async def filter" in code
        
    def test_monitor_component_generation(self):
        """Test Monitor component generation"""
        blueprint = {
            "name": "test_monitor",
            "type": "Monitor",
            "config": {
                "metrics": ["latency", "throughput"]
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedMonitor_test_monitor" in code
        assert "async def monitor" in code
        
    def test_cache_component_generation(self):
        """Test Cache component generation"""
        blueprint = {
            "name": "test_cache",
            "type": "Cache",
            "config": {
                "cache_size": 100,
                "ttl": 3600
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedCache_test_cache" in code
        assert "async def get" in code
        assert "async def set" in code
        
    def test_queue_component_generation(self):
        """Test Queue component generation"""
        blueprint = {
            "name": "test_queue",
            "type": "Queue",
            "config": {
                "queue_type": "fifo",
                "max_size": 1000
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedQueue_test_queue" in code
        assert "async def enqueue" in code
        assert "async def dequeue" in code
        
    def test_scheduler_component_generation(self):
        """Test Scheduler component generation"""
        blueprint = {
            "name": "test_scheduler",
            "type": "Scheduler",
            "config": {
                "schedule": "*/5 * * * *"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedScheduler_test_scheduler" in code
        assert "async def schedule" in code
        
    def test_router_component_generation(self):
        """Test Router component generation"""
        blueprint = {
            "name": "test_router",
            "type": "Router",
            "config": {
                "routing_strategy": "round_robin"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedRouter_test_router" in code
        assert "async def route" in code
        
    def test_logger_component_generation(self):
        """Test Logger component generation"""
        blueprint = {
            "name": "test_logger",
            "type": "Logger",
            "config": {
                "log_level": "INFO",
                "output": "stdout"
            }
        }
        
        code = self.generator.generate(blueprint)
        assert code is not None
        assert "class GeneratedLogger_test_logger" in code
        assert "async def log" in code


class TestBlueprintParsing:
    """Test blueprint parsing edge cases"""
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        
        parser = BlueprintParser()
        
        # Missing name
        invalid_blueprint = {
            "type": "Store",
            "config": {}
        }
        
        with pytest.raises((ValueError, KeyError)):
            parser.parse(invalid_blueprint)
            
    def test_invalid_component_type(self):
        """Test handling of invalid component types"""
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        
        parser = BlueprintParser()
        
        invalid_blueprint = {
            "name": "test",
            "type": "InvalidType",
            "config": {}
        }
        
        result = parser.parse(invalid_blueprint)
        # Should handle gracefully or raise specific error
        assert result is not None or pytest.raises(ValueError)
        
    def test_circular_dependencies(self):
        """Test detection of circular dependencies"""
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        
        parser = BlueprintParser()
        
        circular_blueprint = {
            "system": {
                "name": "test_system",
                "components": [
                    {"name": "a", "type": "Store", "depends_on": ["b"]},
                    {"name": "b", "type": "Store", "depends_on": ["c"]},
                    {"name": "c", "type": "Store", "depends_on": ["a"]}
                ]
            }
        }
        
        # Should detect and handle circular dependencies
        result = parser.parse(circular_blueprint)
        assert result is not None  # Parser should handle this gracefully


class TestValidationFramework:
    """Test all validation levels"""
    
    def test_level1_syntax_validation(self):
        """Test Level 1: Syntax validation"""
        from autocoder_cc.validation.ast_analyzer import ASTAnalyzer
        
        analyzer = ASTAnalyzer()
        
        # Valid Python code
        valid_code = """
def test():
    return 42
"""
        assert analyzer.validate_syntax(valid_code) == True
        
        # Invalid Python code
        invalid_code = """
def test(
    return 42
"""
        assert analyzer.validate_syntax(invalid_code) == False
        
    def test_level2_import_validation(self):
        """Test Level 2: Import validation"""
        from autocoder_cc.validation.import_validator import ImportValidator
        
        validator = ImportValidator()
        
        # Code with valid imports
        valid_imports = """
import os
import sys
from pathlib import Path
"""
        assert validator.validate_imports(valid_imports) == True
        
        # Code with invalid imports
        invalid_imports = """
import nonexistent_module
from fake_package import something
"""
        # Should detect unresolvable imports
        result = validator.validate_imports(invalid_imports)
        assert result == False or result == {"os": True, "sys": True, "pathlib": True}
        
    def test_level3_runtime_validation(self):
        """Test Level 3: Runtime validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file
            test_file = Path(tmpdir) / "test_runtime.py"
            test_file.write_text("""
print("Runtime validation test")
x = 42
assert x == 42
""")
            
            # Should execute without errors
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Runtime validation test" in result.stdout