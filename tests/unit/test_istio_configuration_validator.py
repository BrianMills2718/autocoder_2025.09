"""
Unit tests for Istio Configuration Validator

Tests comprehensive validation of Istio configurations including
schema validation, security checks, and best practices.
"""

import pytest
import yaml
import json
from typing import Dict, Any
from datetime import datetime
import asyncio

from autocoder_cc.validation.istio_configuration_validator import (
    ProductionIstioConfigurationValidator,
    IstioSchemaValidator,
    ValidationIssue,
    ValidationResult,
    IstioInstallationValidator
)


class TestIstioSchemaValidator:
    """Test Istio schema validation"""
    
    @pytest.fixture
    def schema_validator(self):
        return IstioSchemaValidator()
    
    def test_validate_valid_virtual_service(self, schema_validator):
        """Test validation of valid VirtualService"""
        virtual_service = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {"name": "test-vs"},
            "spec": {
                "hosts": ["test-service"],
                "http": [{
                    "route": [{
                        "destination": {"host": "test-service"}
                    }]
                }]
            }
        }
        
        issues = schema_validator.validate_resource_schema(virtual_service)
        assert len(issues) == 0
    
    def test_validate_invalid_virtual_service_missing_hosts(self, schema_validator):
        """Test validation catches missing required fields"""
        virtual_service = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {"name": "test-vs"},
            "spec": {
                # Missing required 'hosts' field
                "http": [{
                    "route": [{
                        "destination": {"host": "test-service"}
                    }]
                }]
            }
        }
        
        issues = schema_validator.validate_resource_schema(virtual_service)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "hosts" in issues[0].message
    
    def test_validate_valid_destination_rule(self, schema_validator):
        """Test validation of valid DestinationRule"""
        destination_rule = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "DestinationRule",
            "metadata": {"name": "test-dr"},
            "spec": {
                "host": "test-service",
                "trafficPolicy": {
                    "connectionPool": {
                        "tcp": {"maxConnections": 100}
                    }
                }
            }
        }
        
        issues = schema_validator.validate_resource_schema(destination_rule)
        assert len(issues) == 0
    
    def test_validate_valid_gateway(self, schema_validator):
        """Test validation of valid Gateway"""
        gateway = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "Gateway",
            "metadata": {"name": "test-gateway"},
            "spec": {
                "selector": {"istio": "ingressgateway"},
                "servers": [{
                    "port": {
                        "number": 80,
                        "name": "http",
                        "protocol": "HTTP"
                    },
                    "hosts": ["*.example.com"]
                }]
            }
        }
        
        issues = schema_validator.validate_resource_schema(gateway)
        assert len(issues) == 0
    
    def test_validate_valid_peer_authentication(self, schema_validator):
        """Test validation of valid PeerAuthentication"""
        peer_auth = {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "PeerAuthentication",
            "metadata": {"name": "test-pa"},
            "spec": {
                "mtls": {"mode": "STRICT"}
            }
        }
        
        issues = schema_validator.validate_resource_schema(peer_auth)
        assert len(issues) == 0
    
    def test_validate_unknown_resource_type(self, schema_validator):
        """Test handling of unknown resource types"""
        unknown_resource = {
            "apiVersion": "unknown.istio.io/v1beta1",
            "kind": "UnknownResource",
            "metadata": {"name": "test"},
            "spec": {}
        }
        
        issues = schema_validator.validate_resource_schema(unknown_resource)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "No schema found" in issues[0].message


class TestProductionIstioConfigurationValidator:
    """Test production Istio configuration validation"""
    
    @pytest.fixture
    def validator(self):
        return ProductionIstioConfigurationValidator()
    
    @pytest.mark.asyncio
    async def test_validate_complete_configuration(self, validator):
        """Test validation of complete Istio configuration"""
        manifests = {
            "security.yaml": """
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: test-namespace
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: test-authz
  namespace: test-namespace
spec:
  selector:
    matchLabels:
      app: test-app
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/test-namespace/sa/test-sa"]
    to:
    - operation:
        methods: ["GET", "POST"]
""",
            "traffic.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-service-vs
  namespace: test-namespace
spec:
  hosts:
  - test-service
  http:
  - route:
    - destination:
        host: test-service
        subset: stable
      weight: 90
    - destination:
        host: test-service
        subset: canary
      weight: 10
    retries:
      attempts: 3
      perTryTimeout: 10s
    timeout: 30s
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-service-dr
  namespace: test-namespace
spec:
  host: test-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
    circuitBreaker:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
    outlierDetection:
      consecutiveGatewayErrors: 3
      interval: 30s
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
""",
            "gateway.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: test-gateway
  namespace: test-namespace
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - test.example.com
    tls:
      mode: SIMPLE
      credentialName: test-tls-cert
      minProtocolVersion: TLSV1_2
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        assert isinstance(result, ValidationResult)
        assert result.resources_validated == 5  # 5 resources across all manifests
        assert result.error_count == 0  # No errors in valid configuration
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_missing_retries(self, validator):
        """Test detection of missing retry configuration"""
        manifests = {
            "virtualservice.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
spec:
  hosts:
  - test-service
  http:
  - route:
    - destination:
        host: test-service
    # Missing retries configuration
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        retry_issues = [i for i in result.issues if i.issue_type == "missing_retries"]
        assert len(retry_issues) == 1
        assert retry_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_missing_timeout(self, validator):
        """Test detection of missing timeout configuration"""
        manifests = {
            "virtualservice.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
spec:
  hosts:
  - test-service
  http:
  - route:
    - destination:
        host: test-service
    # Missing timeout configuration
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        timeout_issues = [i for i in result.issues if i.issue_type == "missing_timeout"]
        assert len(timeout_issues) == 1
        assert timeout_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_missing_circuit_breaker(self, validator):
        """Test detection of missing circuit breaker"""
        manifests = {
            "destinationrule.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-dr
spec:
  host: test-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
    # Missing circuit breaker and outlier detection
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        cb_issues = [i for i in result.issues if i.issue_type == "missing_circuit_breaker"]
        assert len(cb_issues) == 1
        assert cb_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_excessive_connections(self, validator):
        """Test detection of excessive connection limits"""
        manifests = {
            "destinationrule.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-dr
spec:
  host: test-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 5000  # Too high
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        conn_issues = [i for i in result.issues if i.issue_type == "high_max_connections"]
        assert len(conn_issues) == 1
        assert conn_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_missing_tls_on_https(self, validator):
        """Test detection of missing TLS on HTTPS gateway"""
        manifests = {
            "gateway.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: test-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - test.example.com
    # Missing TLS configuration for HTTPS
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        tls_issues = [i for i in result.issues if i.issue_type == "missing_tls"]
        assert len(tls_issues) == 1
        assert tls_issues[0].severity == "error"
    
    @pytest.mark.asyncio
    async def test_validate_weak_tls_version(self, validator):
        """Test detection of weak TLS version"""
        manifests = {
            "gateway.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: test-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - test.example.com
    tls:
      mode: SIMPLE
      credentialName: test-cert
      minProtocolVersion: TLSV1_0  # Too old
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        tls_issues = [i for i in result.issues if i.issue_type == "weak_tls_version"]
        assert len(tls_issues) == 1
        assert tls_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_permissive_mtls(self, validator):
        """Test detection of permissive mTLS"""
        manifests = {
            "peerauth.yaml": """
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: test-pa
spec:
  mtls:
    mode: PERMISSIVE  # Should be STRICT for production
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        mtls_issues = [i for i in result.issues if i.issue_type == "permissive_mtls"]
        assert len(mtls_issues) == 1
        assert mtls_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_permissive_authorization(self, validator):
        """Test detection of overly permissive authorization"""
        manifests = {
            "authz.yaml": """
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: test-authz
spec:
  action: ALLOW
  # No rules - allows all traffic
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        authz_issues = [i for i in result.issues if i.issue_type == "permissive_authorization"]
        assert len(authz_issues) == 1
        assert authz_issues[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_validate_service_mesh_completeness(self, validator):
        """Test detection of missing service mesh components"""
        # Minimal configuration missing several components
        manifests = {
            "minimal.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
spec:
  hosts:
  - test-service
  http:
  - route:
    - destination:
        host: test-service
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        # Should detect missing Gateway, PeerAuthentication, etc.
        missing_issues = [i for i in result.issues if i.issue_type == "missing_resource_type"]
        assert len(missing_issues) > 0
        
        # Gateway and PeerAuthentication should be errors
        gateway_issues = [i for i in missing_issues if "Gateway" in i.message]
        assert len(gateway_issues) == 1
        assert gateway_issues[0].severity == "error"
        
        peer_auth_issues = [i for i in missing_issues if "PeerAuthentication" in i.message]
        assert len(peer_auth_issues) == 1
        assert peer_auth_issues[0].severity == "error"
    
    @pytest.mark.asyncio
    async def test_validate_yaml_parse_error(self, validator):
        """Test handling of YAML parse errors"""
        manifests = {
            "invalid.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
spec:
  hosts:
  - test-service
  http:  # Missing colon causes parse error
  - route
    - destination:
        host: test-service
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        parse_errors = [i for i in result.issues if i.issue_type == "yaml_syntax"]
        assert len(parse_errors) == 1
        assert parse_errors[0].severity == "error"
        assert result.is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_naming_conventions(self, validator):
        """Test detection of naming convention violations"""
        manifests = {
            "naming.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-service  # Should end with -vs
spec:
  hosts:
  - test-service
  http:
  - route:
    - destination:
        host: test-service
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-service  # Should end with -dr
spec:
  host: test-service
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        naming_issues = [i for i in result.issues if i.issue_type == "naming_convention"]
        assert len(naming_issues) == 2
        assert all(i.severity == "info" for i in naming_issues)
    
    @pytest.mark.asyncio
    async def test_validate_canary_deployment_setup(self, validator):
        """Test detection of canary deployment configuration"""
        manifests = {
            "canary.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-dr
spec:
  host: test-service
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
"""
        }
        
        result = await validator.validate_complete_service_mesh_configuration(manifests)
        
        # Should not have missing canary setup issue
        canary_issues = [i for i in result.issues if i.issue_type == "missing_canary_setup"]
        assert len(canary_issues) == 0


class TestValidationResult:
    """Test ValidationResult class functionality"""
    
    def test_add_issue_updates_counts(self):
        """Test that adding issues updates counts correctly"""
        result = ValidationResult(
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            issues=[]
        )
        
        # Add error issue
        result.add_issue(ValidationIssue(
            severity="error",
            resource_type="Test",
            resource_name="test",
            issue_type="test_error",
            message="Test error",
            suggestion="Fix it"
        ))
        
        assert result.error_count == 1
        assert result.is_valid is False
        
        # Add warning issue
        result.add_issue(ValidationIssue(
            severity="warning",
            resource_type="Test",
            resource_name="test",
            issue_type="test_warning",
            message="Test warning",
            suggestion="Consider fixing"
        ))
        
        assert result.warning_count == 1
        assert result.error_count == 1
        
        # Add info issue
        result.add_issue(ValidationIssue(
            severity="info",
            resource_type="Test",
            resource_name="test",
            issue_type="test_info",
            message="Test info",
            suggestion="FYI"
        ))
        
        assert result.info_count == 1
        assert len(result.issues) == 3


class TestIstioInstallationValidator:
    """Test Istio installation validation"""
    
    @pytest.fixture
    def installation_validator(self):
        return IstioInstallationValidator()
    
    @pytest.mark.asyncio
    async def test_validate_istio_installation_no_istioctl(self, installation_validator, monkeypatch):
        """Test handling when istioctl is not available"""
        # Mock subprocess to simulate missing istioctl
        async def mock_subprocess(*args, **kwargs):
            class MockProcess:
                returncode = 1
                async def communicate(self):
                    return b"", b"command not found"
            
            return MockProcess()
        
        monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_subprocess)
        
        result = await installation_validator.validate_istio_installation()
        
        istioctl_issues = [i for i in result.issues if i.issue_type == "missing_istioctl"]
        assert len(istioctl_issues) == 1
        assert istioctl_issues[0].severity == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])