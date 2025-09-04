#!/usr/bin/env python3
"""
Integration Validation Gate - Tests components as integrated systems
"""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from autocoder_cc.tests.tools.integration_test_harness import IntegrationTestHarness
from autocoder_cc.observability import get_logger

@dataclass
class IntegrationValidationResult:
    """Result of integration validation"""
    system_name: str
    total_components: int
    passed_components: int
    failed_components: int
    success_rate: float
    can_proceed: bool
    details: Dict[str, Any]

class IntegrationValidationGate:
    """Validation gate using true integration testing"""
    
    def __init__(self):
        self.logger = get_logger("IntegrationValidationGate")
        self.harness = IntegrationTestHarness()
        # Make threshold configurable via environment variable
        self.threshold = float(os.getenv('VALIDATION_THRESHOLD', '90.0'))
        self.logger.info(f"Validation threshold set to {self.threshold}%")
    
    async def validate_system(self, components_dir: Path, system_name: str) -> IntegrationValidationResult:
        """Validate a system using integration testing"""
        self.logger.info(f"Starting integration validation for {system_name}")
        
        # Load the entire system
        if not await self.harness.load_system(components_dir):
            return IntegrationValidationResult(
                system_name=system_name,
                total_components=0,
                passed_components=0,
                failed_components=0,
                success_rate=0.0,
                can_proceed=False,
                details={"error": "Failed to load system"}
            )
        
        # Test each component in the live system
        results = {}
        for component_name in self.harness.components.keys():
            test_data = self._generate_test_data_for_component(component_name)
            result = await self.harness.test_component_in_system(component_name, test_data)
            results[component_name] = result
        
        # Clean up
        await self.harness.cleanup()
        
        # Calculate overall results
        total = len(results)
        passed = sum(1 for r in results.values() if r["success_rate"] >= 66.7)  # 2/3 tests pass
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return IntegrationValidationResult(
            system_name=system_name,
            total_components=total,
            passed_components=passed,
            failed_components=failed,
            success_rate=success_rate,
            can_proceed=success_rate >= self.threshold,
            details=results
        )
    
    def _generate_test_data_for_component(self, component_name: str) -> List[Dict[str, Any]]:
        """Generate appropriate test data for component type"""
        if "controller" in component_name.lower():
            return [
                {"action": "add_task", "payload": {"title": "Test 1", "description": "Desc 1"}},
                {"action": "get_all_tasks", "payload": {}},
                {"action": "add_task", "payload": {"title": "Test 2", "description": "Desc 2"}}
            ]
        elif "store" in component_name.lower():
            return [
                {"action": "add_item", "title": "Test Item 1", "description": "Test Desc 1"},
                {"action": "list_items"},
                {"action": "add_item", "title": "Test Item 2", "description": "Test Desc 2"}
            ]
        elif "api" in component_name.lower() or "endpoint" in component_name.lower():
            return [
                {"method": "POST", "path": "/todos", "body": {"title": "Test", "description": "Test"}},
                {"method": "GET", "path": "/todos", "body": {}},
                {"method": "GET", "path": "/todos/1", "body": {}}
            ]
        elif "sink" in component_name.lower() or "log" in component_name.lower():
            # Sinks expect MessageEnvelope-like structure
            from dataclasses import dataclass
            import time
            
            @dataclass
            class TestMessage:
                message_id: str
                source_component: str
                payload: dict
            
            return [
                TestMessage(message_id=f"test_{int(time.time()*1000)}_1", 
                           source_component="test_source", 
                           payload={"message": "Test log 1"}),
                TestMessage(message_id=f"test_{int(time.time()*1000)}_2", 
                           source_component="test_source", 
                           payload={"message": "Test log 2"}),
                TestMessage(message_id=f"test_{int(time.time()*1000)}_3", 
                           source_component="test_source", 
                           payload={"message": "Test log 3"})
            ]
        else:
            return [
                {"test": "data1"},
                {"test": "data2"},
                {"test": "data3"}
            ]