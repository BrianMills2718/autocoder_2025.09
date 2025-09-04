#!/usr/bin/env python3
"""
Test System Startup - Verify basic system functionality
Part of the CLAUDE.md critical fixes verification
"""
import pytest
import sys
import os
import asyncio

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSystemStartup:
    """Verify basic system can start and function"""
    
    def test_system_execution_harness_creation(self):
        """Test SystemExecutionHarness can be created"""
        from autocoder_cc import SystemExecutionHarness
        
        harness = SystemExecutionHarness()
        assert harness is not None
        assert hasattr(harness, 'components')
        assert hasattr(harness, 'bindings')
        assert hasattr(harness, 'run')
        
    def test_blueprint_parser_works(self):
        """Test blueprint parser can parse basic blueprint"""
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        
        parser = BlueprintParser()
        
        # Test with minimal blueprint
        test_blueprint = """
        version: 1.0
        name: test_system
        components:
          - name: test_source
            type: Source
            config:
              interval: 1
        """
        
        parsed = parser.parse(test_blueprint)
        assert parsed is not None
        assert parsed.name == "test_system"
        assert len(parsed.components) == 1
        
    def test_system_generator_initialization(self):
        """Test system generator can be initialized"""
        from autocoder_cc.blueprint_language.system_generator import SystemGenerator
        
        generator = SystemGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate')
        
    def test_llm_component_generator_initialization(self):
        """Test LLM component generator initializes"""
        from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator
        
        generator = LLMComponentGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_component')
        
    def test_validation_framework_initialization(self):
        """Test validation framework initializes"""
        from autocoder_cc.blueprint_language.validation_framework import ValidationFramework
        
        framework = ValidationFramework()
        assert framework is not None
        assert hasattr(framework, 'validate')
        
    def test_async_component_operation(self):
        """Test basic async component operation"""
        from autocoder_cc.components.composed_base import ComposedComponent
        
        class TestAsyncComponent(ComposedComponent):
            async def setup(self):
                self.setup_called = True
                
            async def process(self):
                self.process_called = True
                
            async def cleanup(self):
                self.cleanup_called = True
        
        async def run_test():
            component = TestAsyncComponent(name="test", config={})
            await component.setup()
            await component.process()
            await component.cleanup()
            
            assert component.setup_called
            assert component.process_called
            assert component.cleanup_called
            
        # Run the async test
        asyncio.run(run_test())
        
    def test_logger_creation(self):
        """Test logger can be created and used"""
        from autocoder_cc.observability import get_logger
        
        logger = get_logger("test_logger")
        assert logger is not None
        
        # Test logging doesn't crash
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
    def test_metrics_collector_creation(self):
        """Test metrics collector can be created"""
        from autocoder_cc.observability.metrics import MetricsCollector
        
        collector = MetricsCollector("test_component")
        assert collector is not None
        
        # Test basic metric operations
        collector.counter("test_counter", 1)
        collector.gauge("test_gauge", 42.0)
        collector.histogram("test_histogram", 100)
        
    def test_health_check_system(self):
        """Test health check system works"""
        from autocoder_cc.observability.health_checks import HealthChecker
        
        checker = HealthChecker()
        assert checker is not None
        
        # Test basic health check
        health_status = checker.check_health()
        assert isinstance(health_status, dict)
        assert 'status' in health_status
        
    def test_error_handler_creation(self):
        """Test error handler can be created"""
        from autocoder_cc.error_handling.consistent_handler import ErrorHandler
        
        handler = ErrorHandler()
        assert handler is not None
        
        # Test error handling
        test_error = ValueError("Test error")
        formatted = handler.format_error(test_error)
        assert isinstance(formatted, dict)
        assert 'error' in formatted
        
    def test_port_based_components(self):
        """Test port-based component functionality"""
        from autocoder_cc.components.port_based_components.port_component import PortBasedComponent
        
        # Create test component
        class TestPortComponent(PortBasedComponent):
            def define_ports(self):
                self.add_input_port("input", required=True)
                self.add_output_port("output")
                
        component = TestPortComponent(name="test_port", config={})
        assert len(component.input_ports) == 1
        assert len(component.output_ports) == 1
        assert "input" in component.input_ports
        assert "output" in component.output_ports


if __name__ == "__main__":
    pytest.main([__file__, "-v"])