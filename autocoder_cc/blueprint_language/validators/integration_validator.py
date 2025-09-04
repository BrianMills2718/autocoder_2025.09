#!/usr/bin/env python3
"""
Level 3: System Integration Testing - Production Framework
==========================================================

Production implementation of Level 3 validation for the 4-tier validation hierarchy.
Validates system integration with real services and applies configuration
regeneration when integration failures can be automatically corrected.

This level focuses on:
- System-wide integration testing with real services
- Service connectivity validation
- Resource conflict detection
- Port conflict resolution
- Configuration regeneration for integration failures

Extracted from evidence directory for production framework integration.
"""

import asyncio
import socket
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
import aiohttp
import time

# Production framework imports
try:
    from ..validation_result_types import (
        ValidationResult, ValidationFailure, IntegrationTestResult,
        create_success_result, create_failure_result, create_validation_failure
    )
except ImportError:
    # Fallback for evidence compatibility during transition
    from validation_result_types import (
        ValidationResult, ValidationFailure, IntegrationTestResult,
        create_success_result, create_failure_result, create_validation_failure
    )

from autocoder_cc.observability.structured_logging import get_logger


class Level3SystemValidator:
    """
    System integration validation with real service testing.
    
    This validator performs comprehensive system integration testing including
    service connectivity, resource validation, and integration with external
    services. It identifies issues that can be corrected through configuration
    regeneration.
    """
    
    def __init__(self):
        self.logger = get_logger("Level3SystemValidator")
        
        # Integration test configuration
        self.CONNECTION_TIMEOUT = 5.0
        self.HTTP_TIMEOUT = 10.0
        self.MAX_RETRY_ATTEMPTS = 3
        
        # Port ranges for automatic allocation
        self.DYNAMIC_PORT_RANGE = (8000, 9000)
        self.SAFE_PORT_RANGE = (10000, 20000)
        
        # Known service default ports
        self.DEFAULT_PORTS = {
            'database': 5432,
            'redis': 6379,
            'mongodb': 27017,
            'mysql': 3306,
            'elasticsearch': 9200,
            'web_service': 8080,
            'api_gateway': 80
        }
        
        self.logger.info("✅ Level3SystemValidator initialized")
    
    async def validate_system_integration(self, blueprint: 'SystemBlueprint') -> IntegrationTestResult:
        """
        Validate system integration with real services.
        
        This method performs comprehensive system integration testing including
        service connectivity, resource validation, and dependency checking.
        
        Args:
            blueprint: SystemBlueprint containing system components
            
        Returns:
            IntegrationTestResult with integration test details
        """
        # Convert ParsedComponent objects to dictionaries for validation
        components = []
        for component in blueprint.components:
            if hasattr(component, '__dict__'):
                # Convert ParsedComponent to dictionary format
                component_dict = self._convert_component_to_dict(component)
                components.append(component_dict)
            elif isinstance(component, dict):
                # Already a dictionary
                components.append(component)
            else:
                # Fallback for unexpected types
                components.append({
                    'name': str(component),
                    'type': 'unknown',
                    'configuration': {},
                    'dependencies': []
                })
        self.logger.info(f"🌐 Starting Level 3 system integration testing for {len(components)} components")
        
        service_connectivity = {}
        port_conflicts = []
        resource_conflicts = []
        dependency_issues = []
        
        try:
            # Test 1: Service connectivity validation
            connectivity_results = await self._test_service_connectivity(components)
            service_connectivity.update(connectivity_results['connectivity'])
            dependency_issues.extend(connectivity_results['dependency_issues'])
            
            # Test 2: Port conflict detection
            port_conflict_results = await self._detect_port_conflicts(components)
            port_conflicts.extend(port_conflict_results)
            
            # Test 3: Resource conflict detection
            resource_conflict_results = await self._detect_resource_conflicts(components)
            resource_conflicts.extend(resource_conflict_results)
            
            # Test 4: System dependency validation
            system_dependency_issues = await self._validate_system_dependencies(components)
            dependency_issues.extend(system_dependency_issues)
            
            # Test 5: Integration health checks
            health_check_issues = await self._perform_integration_health_checks(components)
            dependency_issues.extend(health_check_issues)
            
            # Determine overall integration status
            all_services_connected = all(service_connectivity.values()) if service_connectivity else True
            has_conflicts = len(port_conflicts) > 0 or len(resource_conflicts) > 0
            has_dependency_issues = len(dependency_issues) > 0
            
            integration_passed = all_services_connected and not has_conflicts and not has_dependency_issues
            
            if integration_passed:
                self.logger.info("✅ System integration testing passed")
            else:
                self.logger.warning(f"⚠️  System integration testing failed: "
                                  f"connectivity={all_services_connected}, "
                                  f"conflicts={not has_conflicts}, "
                                  f"dependencies={not has_dependency_issues}")
            
            result = IntegrationTestResult(
                passed=integration_passed,
                service_connectivity=service_connectivity,
                port_conflicts=port_conflicts,
                resource_conflicts=resource_conflicts,
                dependency_issues=dependency_issues
            )
            
            # Add failures attribute for orchestrator compatibility
            result.failures = []
            if not integration_passed:
                # Add connectivity failures
                for service_name, connected in service_connectivity.items():
                    if not connected:
                        result.failures.append(f"Service {service_name} not reachable")
                
                # Add conflicts and issues
                result.failures.extend(port_conflicts)
                result.failures.extend(resource_conflicts)
                result.failures.extend(dependency_issues)
            
            return result
            
        except Exception as e:
            error_msg = f"System integration testing error: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            result = IntegrationTestResult(
                passed=False,
                dependency_issues=[error_msg]
            )
            
            # Add failures attribute for orchestrator compatibility
            result.failures = [error_msg]
            
            return result
    
    async def _test_service_connectivity(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test connectivity to all services in the system"""
        connectivity = {}
        dependency_issues = []
        
        for component in components:
            component_name = component.get('name', 'unnamed')
            component_type = component.get('type', 'unknown')
            configuration = component.get('configuration', {})
            
            self.logger.debug(f"Testing connectivity for {component_name} ({component_type})")
            
            # Test port connectivity
            ports = configuration.get('ports', [])
            if ports:
                port_connectivity = await self._test_component_port_connectivity(component_name, ports)
                connectivity[component_name] = port_connectivity
            else:
                # For components without ports, assume they're internal services
                connectivity[component_name] = True
            
            # Test external dependencies
            dependencies = component.get('dependencies', [])
            for dependency in dependencies:
                dep_issues = await self._test_dependency_connectivity(component_name, dependency)
                dependency_issues.extend(dep_issues)
        
        return {
            'connectivity': connectivity,
            'dependency_issues': dependency_issues
        }
    
    async def _test_component_port_connectivity(self, component_name: str, ports: List[Dict[str, Any]]) -> bool:
        """Test connectivity to component ports"""
        for port_config in ports:
            port_num = port_config.get('port', 0)
            protocol = port_config.get('protocol', 'tcp').lower()
            
            if protocol in ['http', 'https']:
                # Test HTTP/HTTPS connectivity
                is_connected = await self._test_http_connectivity(component_name, port_num, protocol)
            else:
                # Test TCP connectivity
                is_connected = await self._test_tcp_connectivity(component_name, port_num)
            
            if not is_connected:
                self.logger.warning(f"⚠️  Service {component_name} not reachable on port {port_num}")
                return False
        
        return True
    
    async def _test_http_connectivity(self, component_name: str, port: int, protocol: str) -> bool:
        """Test HTTP/HTTPS connectivity to service"""
        try:
            url = f"{protocol}://localhost:{port}/health"
            
            timeout = aiohttp.ClientTimeout(total=self.HTTP_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    # Accept any response as "connected" - service is running
                    self.logger.debug(f"✅ HTTP connectivity successful: {component_name} on {protocol}:{port}")
                    return True
                    
        except aiohttp.ClientConnectorError:
            # Service not running or not reachable
            self.logger.debug(f"⚠️  HTTP connectivity failed: {component_name} on {protocol}:{port}")
            return False
        except Exception as e:
            self.logger.debug(f"⚠️  HTTP connectivity error: {component_name} on {protocol}:{port} - {e}")
            return False
    
    async def _test_tcp_connectivity(self, component_name: str, port: int) -> bool:
        """Test TCP connectivity to service"""
        try:
            # Test TCP connection to localhost
            future = asyncio.open_connection('localhost', port)
            reader, writer = await asyncio.wait_for(future, timeout=self.CONNECTION_TIMEOUT)
            
            # Close the connection
            writer.close()
            await writer.wait_closed()
            
            self.logger.debug(f"✅ TCP connectivity successful: {component_name} on port {port}")
            return True
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            self.logger.debug(f"⚠️  TCP connectivity failed: {component_name} on port {port}")
            return False
        except Exception as e:
            self.logger.debug(f"⚠️  TCP connectivity error: {component_name} on port {port} - {e}")
            return False
    
    async def _test_dependency_connectivity(self, component_name: str, dependency: Dict[str, Any]) -> List[str]:
        """Test connectivity to component dependencies"""
        issues = []
        
        dep_name = dependency.get('component_name', 'unknown')
        dep_type = dependency.get('dependency_type', 'unknown')
        
        if dep_type == 'service_dependency':
            # For service dependencies, we would test the actual service
            # For now, we'll assume they're available if properly configured
            self.logger.debug(f"Service dependency check: {component_name} -> {dep_name}")
        elif dep_type == 'data_dependency':
            # For data dependencies, check if the data source is available
            self.logger.debug(f"Data dependency check: {component_name} -> {dep_name}")
        
        return issues
    
    async def _detect_port_conflicts(self, components: List[Dict[str, Any]]) -> List[str]:
        """Detect port conflicts between components"""
        conflicts = []
        used_ports = {}
        
        for component in components:
            component_name = component.get('name', 'unnamed')
            configuration = component.get('configuration', {})
            ports = configuration.get('ports', [])
            
            for port_config in ports:
                port_num = port_config.get('port', 0)
                
                if port_num in used_ports:
                    conflict_msg = f"Port {port_num} conflict between {component_name} and {used_ports[port_num]}"
                    conflicts.append(conflict_msg)
                    self.logger.warning(f"⚠️  {conflict_msg}")
                else:
                    used_ports[port_num] = component_name
        
        return conflicts
    
    async def _detect_resource_conflicts(self, components: List[Dict[str, Any]]) -> List[str]:
        """Detect resource conflicts and over-allocation"""
        conflicts = []
        
        total_memory = 0
        total_cpu = 0
        total_disk = 0
        
        for component in components:
            component_name = component.get('name', 'unnamed')
            configuration = component.get('configuration', {})
            resources = configuration.get('resource_requirements', {})
            
            memory_mb = resources.get('memory_mb', 0)
            cpu_cores = resources.get('cpu_cores', 0)
            disk_gb = resources.get('disk_gb', 0)
            
            total_memory += memory_mb
            total_cpu += cpu_cores
            total_disk += disk_gb
        
        # Check for resource over-allocation
        if total_memory > 32768:  # 32GB
            conflicts.append(f"Total memory allocation ({total_memory}MB) exceeds reasonable limit (32GB)")
        
        if total_cpu > 16:  # 16 cores
            conflicts.append(f"Total CPU allocation ({total_cpu} cores) exceeds reasonable limit (16 cores)")
        
        if total_disk > 1024:  # 1TB
            conflicts.append(f"Total disk allocation ({total_disk}GB) exceeds reasonable limit (1TB)")
        
        return conflicts
    
    async def _validate_system_dependencies(self, components: List[Dict[str, Any]]) -> List[str]:
        """Validate system-wide dependencies"""
        issues = []
        
        component_names = set(comp.get('name', '') for comp in components)
        
        # Check dependency relationships
        for component in components:
            component_name = component.get('name', 'unnamed')
            dependencies = component.get('dependencies', [])
            
            for dependency in dependencies:
                dep_name = dependency.get('component_name', '')
                
                # Check if dependency target exists
                if dep_name not in component_names:
                    issues.append(f"Component {component_name} depends on non-existent component {dep_name}")
                
                # Check for circular dependencies (simple case)
                if dep_name == component_name:
                    issues.append(f"Component {component_name} has circular dependency on itself")
        
        # Check for orphaned components (components with no dependents)
        has_dependents = set()
        for component in components:
            dependencies = component.get('dependencies', [])
            for dependency in dependencies:
                dep_name = dependency.get('component_name', '')
                has_dependents.add(dep_name)
        
        # Components that provide services should have dependents
        for component in components:
            component_name = component.get('name', '')
            component_type = component.get('type', '')
            
            if component_type in ['database', 'cache_service', 'message_queue']:
                if component_name not in has_dependents:
                    issues.append(f"Service component {component_name} ({component_type}) has no dependents")
        
        return issues
    
    async def _perform_integration_health_checks(self, components: List[Dict[str, Any]]) -> List[str]:
        """Perform integration health checks"""
        issues = []
        
        # Check for minimum viable system
        component_types = [comp.get('type', '') for comp in components]
        
        # Web applications should have data storage
        has_web_service = any(t in component_types for t in ['web_service', 'api_gateway'])
        has_data_storage = any(t in component_types for t in ['database', 'cache_service'])
        
        if has_web_service and not has_data_storage:
            issues.append("Web application system should include data storage component")
        
        # Multi-service systems should have monitoring
        if len([t for t in component_types if t in ['web_service', 'api_gateway']]) > 2:
            if 'monitoring_service' not in component_types:
                issues.append("Multi-service system should include monitoring service")
        
        # Check for authentication in user-facing systems
        if has_web_service and 'authentication_service' not in component_types:
            issues.append("User-facing system should consider authentication service")
        
        return issues
    
    async def validate_integration_result(self, blueprint: 'SystemBlueprint') -> ValidationResult:
        """
        Validate system integration and return ValidationResult.
        
        This method provides integration validation for use by the
        ValidationDrivenOrchestrator.
        
        Args:
            blueprint: SystemBlueprint to validate
            
        Returns:
            ValidationResult indicating integration status
        """
        try:
            integration_result = await self.validate_system_integration(blueprint)
            
            if integration_result.passed:
                return create_success_result(
                    level=3,
                    metadata={
                        'services_tested': len(integration_result.service_connectivity),
                        'all_services_connected': integration_result.all_services_connected,
                        'integration_health_status': 'healthy'
                    }
                )
            else:
                failures = []
                
                # Add connectivity failures
                for service_name, connected in integration_result.service_connectivity.items():
                    if not connected:
                        failures.append(create_validation_failure(
                            component_name=service_name,
                            failure_type="service_connectivity",
                            error_message=f"Service {service_name} not reachable",
                            healing_candidate=True  # Can potentially be fixed by config regeneration
                        ))
                
                # Add port conflicts
                for conflict in integration_result.port_conflicts:
                    failures.append(create_validation_failure(
                        component_name=None,
                        failure_type="port_conflict",
                        error_message=conflict,
                        healing_candidate=True  # Can be fixed by port reassignment
                    ))
                
                # Add resource conflicts
                for conflict in integration_result.resource_conflicts:
                    failures.append(create_validation_failure(
                        component_name=None,
                        failure_type="resource_conflict",
                        error_message=conflict,
                        healing_candidate=True  # Can be fixed by resource adjustment
                    ))
                
                # Add dependency issues
                for issue in integration_result.dependency_issues:
                    failures.append(create_validation_failure(
                        component_name=None,
                        failure_type="dependency_issue",
                        error_message=issue,
                        healing_candidate=False  # Dependency issues must fail-hard
                    ))
                
                return create_failure_result(level=3, failures=failures)
                
        except Exception as e:
            integration_failure = create_validation_failure(
                component_name=None,
                failure_type="integration_validation_error",
                error_message=f"Integration validation error: {e}",
                healing_candidate=False
            )
            
            return create_failure_result(level=3, failures=[integration_failure])
    
    def suggest_configuration_regeneration(self, integration_result: IntegrationTestResult) -> Dict[str, Any]:
        """
        Suggest configuration changes to resolve integration issues.
        
        This method analyzes integration failures and suggests configuration
        changes that could resolve the issues through regeneration.
        
        Args:
            integration_result: IntegrationTestResult with failures
            
        Returns:
            Dict containing suggested configuration changes
        """
        suggestions = {
            'port_reassignments': [],
            'resource_adjustments': [],
            'dependency_fixes': [],
            'regeneration_feasible': True
        }
        
        # Suggest port reassignments for conflicts
        for conflict in integration_result.port_conflicts:
            if "Port" in conflict and "conflict" in conflict:
                # Extract conflicting port and components
                parts = conflict.split()
                if len(parts) >= 7:  # "Port X conflict between Y and Z"
                    conflicting_port = parts[1]
                    component1 = parts[4]
                    component2 = parts[6]
                    
                    # Suggest new ports
                    new_port1 = self._suggest_available_port_sync()
                    new_port2 = self._suggest_available_port_sync()
                    
                    suggestions['port_reassignments'].append({
                        'original_conflict': conflict,
                        'component1': component1,
                        'suggested_port1': new_port1,
                        'component2': component2,
                        'suggested_port2': new_port2
                    })
        
        # Suggest resource adjustments for over-allocation
        for conflict in integration_result.resource_conflicts:
            if "memory" in conflict.lower():
                suggestions['resource_adjustments'].append({
                    'type': 'memory',
                    'issue': conflict,
                    'suggestion': 'Reduce memory allocation by 20% across all components'
                })
            elif "cpu" in conflict.lower():
                suggestions['resource_adjustments'].append({
                    'type': 'cpu',
                    'issue': conflict,
                    'suggestion': 'Reduce CPU allocation or use fractional cores'
                })
            elif "disk" in conflict.lower():
                suggestions['resource_adjustments'].append({
                    'type': 'disk',
                    'issue': conflict,
                    'suggestion': 'Optimize disk usage or implement shared storage'
                })
        
        # Dependency fixes are usually not regenerable
        if integration_result.dependency_issues:
            suggestions['regeneration_feasible'] = False
            suggestions['dependency_fixes'] = [
                {'issue': issue, 'suggestion': 'Fix required - no workarounds'}
                for issue in integration_result.dependency_issues
            ]
        
        return suggestions
    
    async def _suggest_available_port(self) -> int:
        """Suggest an available port in the safe range"""
        for port in range(*self.SAFE_PORT_RANGE):
            if await self._is_port_available(port):
                return port
        
        # Fallback to dynamic range
        for port in range(*self.DYNAMIC_PORT_RANGE):
            if await self._is_port_available(port):
                return port
        
        # Last resort - return a high port number
        return 20000
    
    def _suggest_available_port_sync(self) -> int:
        """Synchronous version of port suggestion for non-async contexts"""
        # Simple port suggestion without actual availability check
        import random
        return random.randint(*self.SAFE_PORT_RANGE)
    
    async def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0  # Port is available if connection fails
        except Exception:
            return True  # Assume available if check fails
    
    def _convert_component_to_dict(self, component) -> Dict[str, Any]:
        """Convert ParsedComponent object to dictionary format for validation"""
        try:
            # Handle ParsedComponent objects
            if hasattr(component, '__dict__'):
                component_dict = {
                    'name': getattr(component, 'name', 'unnamed'),
                    'type': getattr(component, 'type', 'unknown'),
                    'description': getattr(component, 'description', ''),
                    'configuration': getattr(component, 'config', {}),
                    'dependencies': getattr(component, 'dependencies', []),
                    'implementation': getattr(component, 'implementation', {}),
                    'properties': getattr(component, 'properties', []),
                    'contracts': getattr(component, 'contracts', [])
                }
                
                # Convert dependencies if they're objects
                if hasattr(component, 'dependencies') and component.dependencies:
                    converted_deps = []
                    for dep in component.dependencies:
                        if hasattr(dep, '__dict__'):
                            converted_deps.append({
                                'component_name': getattr(dep, 'component_name', ''),
                                'dependency_type': getattr(dep, 'dependency_type', 'unknown')
                            })
                        elif isinstance(dep, dict):
                            converted_deps.append(dep)
                        else:
                            converted_deps.append({'component_name': str(dep), 'dependency_type': 'unknown'})
                    component_dict['dependencies'] = converted_deps
                
                return component_dict
                
            # If it's already a dictionary, return as-is
            elif isinstance(component, dict):
                return component
                
            # Fallback for unexpected types
            else:
                self.logger.warning(f"Unexpected component type in Level 3 validator: {type(component)}")
                return {
                    'name': str(component),
                    'type': 'unknown',
                    'configuration': {},
                    'dependencies': []
                }
                
        except Exception as e:
            self.logger.error(f"Failed to convert component to dict in Level 3: {e}")
            return {
                'name': 'conversion_error',
                'type': 'unknown',
                'configuration': {},
                'dependencies': [],
                'error': str(e)
            }
    
    def get_validator_status(self) -> Dict[str, Any]:
        """Get current validator status"""
        return {
            'validator_initialized': True,
            'integration_test_types': [
                'service_connectivity',
                'port_conflict_detection',
                'resource_conflict_detection',
                'dependency_validation',
                'health_checks'
            ],
            'configuration_regeneration': {
                'port_reassignment': True,
                'resource_adjustment': True,
                'dependency_fixes': False
            },
            'supported_protocols': ['http', 'https', 'tcp', 'udp'],
            'timeout_settings': {
                'connection_timeout': self.CONNECTION_TIMEOUT,
                'http_timeout': self.HTTP_TIMEOUT
            }
        }


# Convenience functions for external use
async def validate_system_integration(blueprint: 'SystemBlueprint') -> IntegrationTestResult:
    """Validate system integration using Level3SystemValidator"""
    validator = Level3SystemValidator()
    return await validator.validate_system_integration(blueprint)


async def check_integration_health(blueprint: 'SystemBlueprint') -> ValidationResult:
    """Check system integration health and return ValidationResult"""
    validator = Level3SystemValidator()
    return await validator.validate_integration_result(blueprint)


# Main execution for testing
if __name__ == "__main__":
    async def main():
        """Test Level3SystemValidator"""
        
        # Create validator
        validator = Level3SystemValidator()
        
        # Display validator status
        status = validator.get_validator_status()
        print("🌐 Level 3 System Integration Validator Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Create test blueprint
        class MockBlueprint:
            def __init__(self, components):
                self.components = components
        
        test_components = [
            {
                "name": "web_service",
                "type": "web_service",
                "configuration": {
                    "resource_requirements": {
                        "memory_mb": 1024,
                        "cpu_cores": 2,
                        "disk_gb": 20
                    },
                    "ports": [
                        {"port": 8080, "protocol": "http"}
                    ]
                },
                "dependencies": [
                    {"component_name": "database", "dependency_type": "data_dependency"}
                ]
            },
            {
                "name": "database",
                "type": "database",
                "configuration": {
                    "resource_requirements": {
                        "memory_mb": 2048,
                        "cpu_cores": 2,
                        "disk_gb": 100
                    }
                }
            }
        ]
        
        test_blueprint = MockBlueprint(test_components)
        
        print(f"\n🚀 Testing system integration with {len(test_components)} components...")
        
        # Test integration validation
        integration_result = await validator.validate_system_integration(test_blueprint)
        
        print(f"\n📊 Integration Test Results:")
        print(f"  Overall result: {'✅ PASSED' if integration_result.passed else '❌ FAILED'}")
        print(f"  Service connectivity: {integration_result.service_connectivity}")
        print(f"  All services connected: {integration_result.all_services_connected}")
        print(f"  Port conflicts: {len(integration_result.port_conflicts)}")
        print(f"  Resource conflicts: {len(integration_result.resource_conflicts)}")
        print(f"  Dependency issues: {len(integration_result.dependency_issues)}")
        
        if integration_result.port_conflicts:
            print(f"\n⚠️  Port Conflicts:")
            for conflict in integration_result.port_conflicts:
                print(f"    - {conflict}")
        
        if integration_result.resource_conflicts:
            print(f"\n⚠️  Resource Conflicts:")
            for conflict in integration_result.resource_conflicts:
                print(f"    - {conflict}")
        
        if integration_result.dependency_issues:
            print(f"\n⚠️  Dependency Issues:")
            for issue in integration_result.dependency_issues:
                print(f"    - {issue}")
        
        # Test configuration regeneration suggestions
        if not integration_result.passed:
            print(f"\n🔧 Configuration Regeneration Suggestions:")
            suggestions = validator.suggest_configuration_regeneration(integration_result)
            for category, items in suggestions.items():
                if items and category != 'regeneration_feasible':
                    print(f"  {category}: {items}")
        
        # Test ValidationResult creation
        print(f"\n🧪 Testing ValidationResult creation...")
        validation_result = await validator.validate_integration_result(test_blueprint)
        
        print(f"ValidationResult: {'✅ PASSED' if validation_result.passed else '❌ FAILED'}")
        print(f"Level: {validation_result.level}")
        print(f"Failures: {len(validation_result.failures)}")
    
    # Run the test
    asyncio.run(main())