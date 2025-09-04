"""
Integration tests for Istio configuration validation

Tests the complete validation of generated Istio configurations
including deployment testing and real-world scenarios.
"""

import pytest
import asyncio
import yaml
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging

from autocoder_cc.autocoder.generators.service_deployment_generator import (
    ServiceDeploymentGenerator,
    ProductionIstioServiceMesh
)
from autocoder_cc.autocoder.validation.istio_configuration_validator import (
    ProductionIstioConfigurationValidator,
    ValidationResult,
    IstioInstallationValidator
)

logger = logging.getLogger(__name__)


# Mock system blueprint for testing
class MockComponent:
    def __init__(self, name: str):
        self.name = name
        self.type = "service"


class MockSystem:
    def __init__(self, name: str, namespace: str = "default"):
        self.name = name
        self.namespace = namespace
        self.components = [
            MockComponent("api-gateway"),
            MockComponent("user-service"),
            MockComponent("order-service"),
            MockComponent("payment-service")
        ]


class MockSystemBlueprint:
    def __init__(self):
        self.system = MockSystem("test-ecommerce", "production")


class TestIstioValidationIntegration:
    """Integration tests for Istio configuration validation"""
    
    @pytest.fixture
    def system_blueprint(self):
        """Create mock system blueprint"""
        return MockSystemBlueprint()
    
    @pytest.fixture
    def deployment_generator(self, tmp_path):
        """Create deployment generator"""
        return ServiceDeploymentGenerator(tmp_path)
    
    @pytest.fixture
    def istio_validator(self):
        """Create Istio configuration validator"""
        return ProductionIstioConfigurationValidator()
    
    @pytest.mark.asyncio
    async def test_validate_generated_production_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test validation of complete production-generated Istio configurations"""
        
        # Generate production service mesh deployment
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        
        # Filter YAML files only (exclude README.md and install script)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Validate all generated configurations
        validation_result = await istio_validator.validate_complete_service_mesh_configuration(yaml_configs)
        
        # Log validation summary
        logger.info(f"Validation completed: {validation_result.resources_validated} resources validated")
        logger.info(f"Errors: {validation_result.error_count}, Warnings: {validation_result.warning_count}")
        
        # Assert basic validation passed
        assert validation_result.is_valid, f"Validation failed with {validation_result.error_count} errors"
        assert validation_result.resources_validated > 0, "No resources were validated"
        
        # Check specific resource types were generated and validated
        all_resources = []
        for content in yaml_configs.values():
            try:
                resources = list(yaml.safe_load_all(content))
                all_resources.extend([r for r in resources if r])
            except:
                pass
        
        resource_kinds = {r.get("kind") for r in all_resources if r}
        
        # Verify essential resource types
        essential_resources = {
            "Gateway", "VirtualService", "DestinationRule", 
            "PeerAuthentication", "AuthorizationPolicy"
        }
        assert essential_resources.issubset(resource_kinds), f"Missing essential resources: {essential_resources - resource_kinds}"
        
        # Check for production features
        has_circuit_breaker = any(
            "circuitBreaker" in r.get("spec", {}).get("trafficPolicy", {})
            for r in all_resources
            if r.get("kind") == "DestinationRule"
        )
        assert has_circuit_breaker, "No circuit breaker configuration found"
        
        has_mtls_strict = any(
            r.get("spec", {}).get("mtls", {}).get("mode") == "STRICT"
            for r in all_resources
            if r.get("kind") == "PeerAuthentication"
        )
        assert has_mtls_strict, "No STRICT mTLS configuration found"
    
    @pytest.mark.asyncio
    async def test_validate_security_configurations(self, system_blueprint, deployment_generator, istio_validator):
        """Test security-specific validations"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Validate
        validation_result = await istio_validator.validate_complete_service_mesh_configuration(yaml_configs)
        
        # Check for security warnings
        security_warnings = [
            issue for issue in validation_result.issues
            if issue.resource_type in ["Security", "PeerAuthentication", "AuthorizationPolicy"]
        ]
        
        # Log security issues for debugging
        for issue in security_warnings:
            logger.info(f"Security issue: {issue.severity} - {issue.message}")
        
        # Should have minimal security warnings in production config
        critical_security_errors = [
            issue for issue in security_warnings
            if issue.severity == "error"
        ]
        assert len(critical_security_errors) == 0, f"Found {len(critical_security_errors)} critical security errors"
    
    @pytest.mark.asyncio
    async def test_validate_traffic_management(self, system_blueprint, deployment_generator, istio_validator):
        """Test traffic management validations"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Validate
        validation_result = await istio_validator.validate_complete_service_mesh_configuration(yaml_configs)
        
        # Check for traffic management best practices
        traffic_issues = [
            issue for issue in validation_result.issues
            if issue.resource_type in ["VirtualService", "DestinationRule"]
            and issue.severity != "info"
        ]
        
        # Should have minimal traffic management issues
        assert len(traffic_issues) < 5, f"Too many traffic management issues: {len(traffic_issues)}"
        
        # Verify retries and timeouts are configured
        missing_retries = [
            issue for issue in validation_result.issues
            if issue.issue_type == "missing_retries"
        ]
        assert len(missing_retries) == 0, "Some VirtualServices missing retry configuration"
        
        missing_timeouts = [
            issue for issue in validation_result.issues
            if issue.issue_type == "missing_timeout"
        ]
        assert len(missing_timeouts) == 0, "Some VirtualServices missing timeout configuration"
    
    @pytest.mark.asyncio
    async def test_validate_observability_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test observability configuration validation"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Parse observability configs
        observability_content = yaml_configs.get("istio-observability.yaml", "")
        observability_resources = list(yaml.safe_load_all(observability_content)) if observability_content else []
        
        # Check for Telemetry configuration
        telemetry_configs = [r for r in observability_resources if r and r.get("kind") == "Telemetry"]
        assert len(telemetry_configs) > 0, "No Telemetry configuration found"
        
        # Verify telemetry has metrics, tracing, and logging
        for telemetry in telemetry_configs:
            spec = telemetry.get("spec", {})
            assert "metrics" in spec, "Telemetry missing metrics configuration"
            assert "tracing" in spec, "Telemetry missing tracing configuration"
            assert "accessLogging" in spec, "Telemetry missing access logging configuration"
    
    @pytest.mark.asyncio
    async def test_validate_multi_cluster_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test multi-cluster configuration validation"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Parse multi-cluster configs
        multi_cluster_content = yaml_configs.get("istio-multi-cluster.yaml", "")
        multi_cluster_resources = list(yaml.safe_load_all(multi_cluster_content)) if multi_cluster_content else []
        
        # Check for cross-cluster gateway
        gateways = [r for r in multi_cluster_resources if r and r.get("kind") == "Gateway"]
        cross_cluster_gateways = [
            g for g in gateways
            if g.get("metadata", {}).get("name") == "cross-network-gateway"
        ]
        assert len(cross_cluster_gateways) > 0, "No cross-cluster gateway found"
        
        # Check for ServiceEntry resources
        service_entries = [r for r in multi_cluster_resources if r and r.get("kind") == "ServiceEntry"]
        assert len(service_entries) > 0, "No ServiceEntry resources for multi-cluster"
    
    @pytest.mark.asyncio
    async def test_validate_canary_deployment_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test canary deployment configuration validation"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Parse canary configs
        canary_content = yaml_configs.get("istio-canary.yaml", "")
        canary_resources = list(yaml.safe_load_all(canary_content)) if canary_content else []
        
        # Check for Flagger Canary resources
        canary_configs = [r for r in canary_resources if r and r.get("kind") == "Canary"]
        assert len(canary_configs) > 0, "No Canary configurations found"
        
        # Verify canary analysis configuration
        for canary in canary_configs:
            analysis = canary.get("spec", {}).get("analysis", {})
            assert "metrics" in analysis, "Canary missing metrics configuration"
            assert "threshold" in analysis, "Canary missing threshold configuration"
            assert "webhooks" in analysis, "Canary missing webhook configuration"
    
    @pytest.mark.asyncio
    async def test_validate_chaos_engineering_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test chaos engineering configuration validation"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Parse chaos engineering configs
        chaos_content = yaml_configs.get("istio-chaos-engineering.yaml", "")
        chaos_resources = list(yaml.safe_load_all(chaos_content)) if chaos_content else []
        
        # Check for different chaos experiment types
        chaos_kinds = {r.get("kind") for r in chaos_resources if r}
        expected_chaos_types = {"NetworkChaos", "PodChaos", "StressChaos", "Workflow"}
        
        found_chaos_types = chaos_kinds.intersection(expected_chaos_types)
        assert len(found_chaos_types) >= 3, f"Missing chaos experiment types: {expected_chaos_types - found_chaos_types}"
    
    @pytest.mark.asyncio
    async def test_deployment_validation(self, system_blueprint, deployment_generator, istio_validator, tmp_path):
        """Test deployment validation with kubectl dry-run"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Test deployment (will use dry-run if kubectl available)
        deployment_result = await istio_validator.test_deployment(yaml_configs)
        
        # Should complete without critical errors
        deployment_errors = [
            issue for issue in deployment_result.issues
            if issue.severity == "error" and issue.issue_type != "deployment_test_error"
        ]
        
        # Log any deployment errors for debugging
        for error in deployment_errors:
            logger.error(f"Deployment error: {error.message}")
        
        # If kubectl is available, there should be no deployment errors
        # If not available, we should get an info message
        if deployment_errors:
            # Check if it's just kubectl not being available
            kubectl_not_found = any(
                "kubectl" in issue.message.lower()
                for issue in deployment_result.issues
            )
            assert kubectl_not_found, f"Unexpected deployment errors: {[e.message for e in deployment_errors]}"
    
    @pytest.mark.asyncio
    async def test_validate_edge_cases(self, istio_validator):
        """Test validation of edge cases and malformed configurations"""
        
        edge_case_configs = {
            "empty.yaml": "",
            "invalid_yaml.yaml": "invalid: yaml: content:\n  - no proper",
            "missing_apiversion.yaml": """
kind: VirtualService
metadata:
  name: test
spec:
  hosts: ["test"]
""",
            "duplicate_resources.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
spec:
  hosts: ["test1"]
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs  # Duplicate name
spec:
  hosts: ["test2"]
"""
        }
        
        validation_result = await istio_validator.validate_complete_service_mesh_configuration(edge_case_configs)
        
        # Should have errors for invalid configurations
        assert validation_result.error_count > 0, "Should have errors for invalid configurations"
        assert not validation_result.is_valid, "Should not be valid with errors"
        
        # Check specific error types
        parse_errors = [i for i in validation_result.issues if i.issue_type in ["parse_error", "yaml_syntax"]]
        assert len(parse_errors) >= 1, "Should have parse errors for invalid YAML"
    
    @pytest.mark.asyncio
    async def test_performance_with_large_configs(self, system_blueprint, deployment_generator, istio_validator):
        """Test validation performance with large configuration sets"""
        
        # Generate configurations
        generated_configs = deployment_generator.generate_production_service_mesh_deployment(system_blueprint)
        yaml_configs = {k: v for k, v in generated_configs.items() if k.endswith('.yaml')}
        
        # Duplicate configs to simulate larger deployment
        large_configs = {}
        for i in range(10):
            for key, value in yaml_configs.items():
                large_configs[f"{i}_{key}"] = value
        
        # Time the validation
        import time
        start_time = time.time()
        
        validation_result = await istio_validator.validate_complete_service_mesh_configuration(large_configs)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Validated {validation_result.resources_validated} resources in {duration:.2f} seconds")
        
        # Should complete in reasonable time (< 10 seconds for ~500 resources)
        assert duration < 10, f"Validation took too long: {duration:.2f} seconds"
        assert validation_result.validation_duration_seconds > 0, "Duration not recorded"


class TestIstioInstallationValidation:
    """Test Istio installation validation integration"""
    
    @pytest.fixture
    def installation_validator(self):
        return IstioInstallationValidator()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not Path("/usr/local/bin/istioctl").exists() and not Path("/usr/bin/istioctl").exists(),
        reason="istioctl not installed"
    )
    async def test_validate_actual_installation(self, installation_validator):
        """Test validation against actual Istio installation (if available)"""
        
        result = await installation_validator.validate_istio_installation()
        
        # Should complete without critical errors
        assert isinstance(result, ValidationResult)
        
        # Log any issues found
        for issue in result.issues:
            logger.info(f"{issue.severity}: {issue.message}")
        
        # If istioctl is available, check basic functionality
        istioctl_issues = [i for i in result.issues if i.issue_type == "missing_istioctl"]
        assert len(istioctl_issues) == 0, "istioctl should be available"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])