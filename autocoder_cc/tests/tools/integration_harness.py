"""Complete integration test harness."""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from autocoder_cc.tests.tools.port_test_runner import PortBasedTestRunner
from autocoder_cc.tests.tools.pipeline_test_runner import PipelineTestRunner
from autocoder_cc.tests.tools.test_data_generator import TestDataGenerator
from autocoder_cc.tests.tools.message_bus import MessageBus
from autocoder_cc.tests.tools.component_loader import ComponentLoader
from autocoder_cc.observability import get_logger

class IntegrationTestHarness:
    """Complete integration test harness."""
    
    def __init__(self):
        self.logger = get_logger("IntegrationTestHarness")
        self.message_bus = MessageBus()
        self.component_loader = ComponentLoader(self.message_bus)
        self.port_runner = PortBasedTestRunner()
        self.pipeline_runner = PipelineTestRunner()
        self.test_results = []
        
    async def test_single_component(self, 
                                   component: Any,
                                   test_data_type: str = 'api',
                                   count: int = 100) -> bool:
        """Test a single component."""
        self.logger.info(f"Testing single component: {component.name}")
        
        # Generate test data
        test_data = TestDataGenerator.generate_for_component_type(
            test_data_type, count
        )
        
        # Run test
        result = await self.port_runner.test_component(component, test_data)
        self.test_results.append(result)
        
        return result.success
    
    async def test_two_component_pipeline(self,
                                         source: Any,
                                         sink: Any,
                                         count: int = 100) -> bool:
        """Test a 2-component pipeline."""
        self.logger.info("Testing 2-component pipeline")
        
        test_data = TestDataGenerator.generate_api_requests(count)
        result = await self.pipeline_runner.test_pipeline(
            [source, sink], test_data
        )
        self.test_results.append(result)
        
        return result.success
    
    async def test_full_system(self,
                              api_source: Any,
                              controller: Any,
                              store: Any,
                              response_sink: Any,
                              count: int = 1000) -> bool:
        """Test full 4-component system."""
        self.logger.info("Testing full 4-component system")
        
        # Generate diverse test data
        test_data = []
        test_data.extend(TestDataGenerator.generate_api_requests(count // 3))
        test_data.extend(TestDataGenerator.generate_transaction_data(count // 3))
        test_data.extend(TestDataGenerator.generate_log_entries(count // 3))
        
        # Test the pipeline
        components = [api_source, controller, store, response_sink]
        result = await self.pipeline_runner.test_pipeline(
            components, test_data, timeout=60.0
        )
        self.test_results.append(result)
        
        # Verify results
        success = (
            result.success and
            result.messages_received >= (count * 0.95) and  # 95% delivery
            result.latency_ms < 5000  # Under 5 seconds total
        )
        
        self.logger.info(f"Full system test: {'PASSED' if success else 'FAILED'}")
        self.logger.info(f"  Messages: {result.messages_received}/{result.messages_sent}")
        self.logger.info(f"  Latency: {result.latency_ms:.2f}ms")
        
        return success
    
    def generate_full_report(self) -> str:
        """Generate comprehensive test report."""
        report = ["# Integration Test Report\n"]
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.success)
        
        report.append(f"## Summary")
        report.append(f"- Total Tests: {total}")
        report.append(f"- Passed: {passed}")
        report.append(f"- Failed: {total - passed}")
        if total > 0:
            report.append(f"- Success Rate: {(passed/total)*100:.1f}%\n")
        else:
            report.append(f"- Success Rate: N/A (no tests run)\n")
        
        report.append(f"## Message Bus Stats")
        stats = self.message_bus.get_stats()
        for key, value in stats.items():
            report.append(f"- {key}: {value}")
        
        report.append(f"\n## Test Results")
        for result in self.test_results:
            report.append(f"\n### {result.test_name}")
            report.append(f"- Component: {result.component_name}")
            report.append(f"- Success: {'✅' if result.success else '❌'}")
            report.append(f"- Messages: {result.messages_received}/{result.messages_sent}")
            report.append(f"- Latency: {result.latency_ms:.2f}ms")
            if result.errors:
                report.append(f"- Errors: {', '.join(result.errors)}")
        
        return '\n'.join(report)