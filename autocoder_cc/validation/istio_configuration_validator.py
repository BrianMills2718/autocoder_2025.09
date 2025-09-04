"""
Production Istio Configuration Validator

This module provides comprehensive validation of generated Istio configurations
against production standards, schemas, and best practices as required by CLAUDE.md.
"""

import yaml
import json
import jsonschema
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import re
import subprocess
import tempfile
import asyncio
import aiofiles
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    HAS_KUBERNETES = True
except ImportError:
    # Kubernetes client not available - will be handled gracefully in code
    HAS_KUBERNETES = False
    client = None
    config = None
    ApiException = Exception

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Single validation issue found in configuration"""
    severity: str  # error, warning, info
    resource_type: str
    resource_name: str
    issue_type: str
    message: str
    suggestion: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    
    @property
    def is_error(self) -> bool:
        return self.severity == "error"


@dataclass
class ValidationResult:
    """Complete validation result for Istio configurations"""
    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue]
    validation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resources_validated: int = 0
    validation_duration_seconds: float = 0
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue and update counts"""
        self.issues.append(issue)
        if issue.severity == "error":
            self.error_count += 1
            self.is_valid = False
        elif issue.severity == "warning":
            self.warning_count += 1
        elif issue.severity == "info":
            self.info_count += 1


class IstioSchemaValidator:
    """Validate Istio resources against official schemas"""
    
    # Istio API versions and their schemas
    ISTIO_SCHEMAS = {
        "networking.istio.io/v1beta1": {
            "VirtualService": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "required": ["hosts"],
                        "properties": {
                            "hosts": {"type": "array", "items": {"type": "string"}},
                            "gateways": {"type": "array", "items": {"type": "string"}},
                            "http": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "match": {"type": "array"},
                                        "route": {"type": "array"},
                                        "retries": {
                                            "type": "object",
                                            "properties": {
                                                "attempts": {"type": "integer", "minimum": 1},
                                                "perTryTimeout": {"type": "string"},
                                                "retryOn": {"type": "string"}
                                            }
                                        },
                                        "timeout": {"type": "string"},
                                        "fault": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "DestinationRule": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "required": ["host"],
                        "properties": {
                            "host": {"type": "string"},
                            "trafficPolicy": {
                                "type": "object",
                                "properties": {
                                    "connectionPool": {"type": "object"},
                                    "circuitBreaker": {"type": "object"},
                                    "outlierDetection": {"type": "object"},
                                    "loadBalancer": {"type": "object"}
                                }
                            },
                            "subsets": {"type": "array"}
                        }
                    }
                }
            },
            "Gateway": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "required": ["selector", "servers"],
                        "properties": {
                            "selector": {"type": "object"},
                            "servers": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["port", "hosts"],
                                    "properties": {
                                        "port": {
                                            "type": "object",
                                            "required": ["number", "name", "protocol"]
                                        },
                                        "hosts": {"type": "array", "items": {"type": "string"}},
                                        "tls": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "ServiceEntry": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "required": ["hosts", "ports", "location"],
                        "properties": {
                            "hosts": {"type": "array", "items": {"type": "string"}},
                            "ports": {"type": "array"},
                            "location": {"type": "string", "enum": ["MESH_EXTERNAL", "MESH_INTERNAL"]},
                            "resolution": {"type": "string"}
                        }
                    }
                }
            }
        },
        "security.istio.io/v1beta1": {
            "PeerAuthentication": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "properties": {
                            "mtls": {
                                "type": "object",
                                "properties": {
                                    "mode": {"type": "string", "enum": ["STRICT", "PERMISSIVE", "DISABLE"]}
                                }
                            },
                            "selector": {"type": "object"}
                        }
                    }
                }
            },
            "AuthorizationPolicy": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "object"},
                            "action": {"type": "string", "enum": ["ALLOW", "DENY", "CUSTOM"]},
                            "rules": {"type": "array"}
                        }
                    }
                }
            },
            "RequestAuthentication": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "object"},
                            "jwtRules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["issuer"],
                                    "properties": {
                                        "issuer": {"type": "string"},
                                        "jwksUri": {"type": "string"},
                                        "audiences": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "telemetry.istio.io/v1alpha1": {
            "Telemetry": {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "spec": {
                        "type": "object",
                        "properties": {
                            "metrics": {"type": "array"},
                            "tracing": {"type": "array"},
                            "accessLogging": {"type": "array"}
                        }
                    }
                }
            }
        }
    }
    
    def validate_resource_schema(self, resource: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a single resource against its schema"""
        issues = []
        
        api_version = resource.get("apiVersion", "")
        kind = resource.get("kind", "")
        name = resource.get("metadata", {}).get("name", "unknown")
        
        # Find schema
        schema_group = self.ISTIO_SCHEMAS.get(api_version, {})
        schema = schema_group.get(kind)
        
        if not schema:
            issues.append(ValidationIssue(
                severity="warning",
                resource_type=kind,
                resource_name=name,
                issue_type="unknown_resource",
                message=f"No schema found for {api_version}/{kind}",
                suggestion="Ensure you're using a supported Istio API version"
            ))
            return issues
        
        # Validate against schema
        try:
            jsonschema.validate(resource, schema)
        except jsonschema.ValidationError as e:
            issues.append(ValidationIssue(
                severity="error",
                resource_type=kind,
                resource_name=name,
                issue_type="schema_validation",
                message=f"Schema validation failed: {e.message}",
                suggestion=f"Fix the resource structure at path: {'.'.join(str(p) for p in e.path)}"
            ))
        
        return issues


class ProductionIstioConfigurationValidator:
    """Comprehensive Istio configuration validator for production readiness"""
    
    def __init__(self):
        self.schema_validator = IstioSchemaValidator()
        self.k8s_client = None
        self._init_k8s_client()
    
    def _init_k8s_client(self):
        """Initialize Kubernetes client - REQUIRED for Istio validation"""
        if not HAS_KUBERNETES:
            # FAIL FAST - No graceful degradation
            raise RuntimeError(
                "CRITICAL: Kubernetes client not installed. "
                "Cannot validate Istio configuration without Kubernetes. "
                "Install kubernetes package: pip install kubernetes"
            )
            
        try:
            config.load_incluster_config()
            self.k8s_client = client.ApiClient()
        except:
            try:
                config.load_kube_config()
                self.k8s_client = client.ApiClient()
            except Exception as e:
                # FAIL FAST - No graceful degradation
                raise RuntimeError(
                    f"CRITICAL: Cannot initialize Kubernetes client: {e}. "
                    "Istio validation requires Kubernetes access. "
                    "Ensure kubeconfig is properly configured."
                ) from e
    
    async def validate_complete_service_mesh_configuration(self, 
                                                         generated_manifests: Dict[str, str]) -> ValidationResult:
        """Validate all generated manifests against production standards"""
        
        start_time = datetime.utcnow()
        result = ValidationResult(
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            issues=[]
        )
        
        # Parse and validate each manifest file
        for manifest_name, manifest_content in generated_manifests.items():
            if manifest_name.endswith('.yaml') or manifest_name.endswith('.yml'):
                issues = await self._validate_manifest_file(manifest_name, manifest_content)
                for issue in issues:
                    result.add_issue(issue)
                
                # Count resources
                try:
                    resources = list(yaml.safe_load_all(manifest_content))
                    result.resources_validated += len([r for r in resources if r])
                except Exception as e:
                    result.add_issue(ValidationIssue(
                        severity="error",
                        resource_type="YAML",
                        resource_name=manifest_name,
                        issue_type="parse_error",
                        message=f"Failed to parse YAML: {str(e)}",
                        suggestion="Ensure the YAML syntax is valid",
                        file_path=manifest_name
                    ))
        
        # Validate overall service mesh completeness
        completeness_issues = self._validate_service_mesh_completeness(generated_manifests)
        for issue in completeness_issues:
            result.add_issue(issue)
        
        # Validate security configurations
        security_issues = self._validate_security_configurations(generated_manifests)
        for issue in security_issues:
            result.add_issue(issue)
        
        # Validate production best practices
        best_practices_issues = self._validate_best_practices(generated_manifests)
        for issue in best_practices_issues:
            result.add_issue(issue)
        
        # Calculate duration
        end_time = datetime.utcnow()
        result.validation_duration_seconds = (end_time - start_time).total_seconds()
        
        return result
    
    async def _validate_manifest_file(self, file_name: str, content: str) -> List[ValidationIssue]:
        """Validate a single manifest file"""
        issues = []
        
        try:
            # Parse YAML documents
            documents = list(yaml.safe_load_all(content))
            
            for doc_index, document in enumerate(documents):
                if not document:
                    continue
                
                # Schema validation
                schema_issues = self.schema_validator.validate_resource_schema(document)
                for issue in schema_issues:
                    issue.file_path = file_name
                    issues.append(issue)
                
                # Resource-specific validation
                resource_issues = self._validate_resource_specific(document, file_name)
                issues.extend(resource_issues)
                
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                severity="error",
                resource_type="YAML",
                resource_name=file_name,
                issue_type="yaml_syntax",
                message=f"YAML syntax error: {str(e)}",
                suggestion="Fix the YAML syntax error",
                file_path=file_name
            ))
        
        return issues
    
    def _validate_resource_specific(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate resource-specific requirements"""
        issues = []
        
        kind = resource.get("kind", "")
        name = resource.get("metadata", {}).get("name", "unknown")
        
        # VirtualService validation
        if kind == "VirtualService":
            issues.extend(self._validate_virtual_service(resource, file_name))
        
        # DestinationRule validation
        elif kind == "DestinationRule":
            issues.extend(self._validate_destination_rule(resource, file_name))
        
        # Gateway validation
        elif kind == "Gateway":
            issues.extend(self._validate_gateway(resource, file_name))
        
        # PeerAuthentication validation
        elif kind == "PeerAuthentication":
            issues.extend(self._validate_peer_authentication(resource, file_name))
        
        # AuthorizationPolicy validation
        elif kind == "AuthorizationPolicy":
            issues.extend(self._validate_authorization_policy(resource, file_name))
        
        return issues
    
    def _validate_virtual_service(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate VirtualService specific requirements"""
        issues = []
        name = resource.get("metadata", {}).get("name", "unknown")
        spec = resource.get("spec", {})
        
        # Check for retries configuration
        http_routes = spec.get("http", [])
        for route_index, route in enumerate(http_routes):
            if "retries" not in route:
                issues.append(ValidationIssue(
                    severity="warning",
                    resource_type="VirtualService",
                    resource_name=name,
                    issue_type="missing_retries",
                    message=f"HTTP route {route_index} missing retry configuration",
                    suggestion="Add retry configuration for resilience",
                    file_path=file_name
                ))
            
            # Validate retry configuration
            if "retries" in route:
                retries = route["retries"]
                if retries.get("attempts", 0) > 5:
                    issues.append(ValidationIssue(
                        severity="warning",
                        resource_type="VirtualService",
                        resource_name=name,
                        issue_type="excessive_retries",
                        message=f"Retry attempts ({retries['attempts']}) may be too high",
                        suggestion="Consider reducing retry attempts to 3-5",
                        file_path=file_name
                    ))
            
            # Check for timeout configuration
            if "timeout" not in route:
                issues.append(ValidationIssue(
                    severity="warning",
                    resource_type="VirtualService",
                    resource_name=name,
                    issue_type="missing_timeout",
                    message=f"HTTP route {route_index} missing timeout configuration",
                    suggestion="Add timeout configuration to prevent hanging requests",
                    file_path=file_name
                ))
        
        return issues
    
    def _validate_destination_rule(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate DestinationRule specific requirements"""
        issues = []
        name = resource.get("metadata", {}).get("name", "unknown")
        spec = resource.get("spec", {})
        traffic_policy = spec.get("trafficPolicy", {})
        
        # Check for circuit breaker
        if "circuitBreaker" not in traffic_policy and "outlierDetection" not in traffic_policy:
            issues.append(ValidationIssue(
                severity="warning",
                resource_type="DestinationRule",
                resource_name=name,
                issue_type="missing_circuit_breaker",
                message="No circuit breaker or outlier detection configured",
                suggestion="Add circuit breaker configuration for resilience",
                file_path=file_name
            ))
        
        # Validate connection pool settings
        connection_pool = traffic_policy.get("connectionPool", {})
        tcp_settings = connection_pool.get("tcp", {})
        
        if tcp_settings.get("maxConnections", 0) > 1000:
            issues.append(ValidationIssue(
                severity="warning",
                resource_type="DestinationRule",
                resource_name=name,
                issue_type="high_max_connections",
                message=f"Max connections ({tcp_settings['maxConnections']}) may be too high",
                suggestion="Consider reducing max connections to prevent resource exhaustion",
                file_path=file_name
            ))
        
        return issues
    
    def _validate_gateway(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate Gateway specific requirements"""
        issues = []
        name = resource.get("metadata", {}).get("name", "unknown")
        spec = resource.get("spec", {})
        
        # Check for TLS configuration on HTTPS servers
        servers = spec.get("servers", [])
        for server_index, server in enumerate(servers):
            port = server.get("port", {})
            
            if port.get("protocol") == "HTTPS" and "tls" not in server:
                issues.append(ValidationIssue(
                    severity="error",
                    resource_type="Gateway",
                    resource_name=name,
                    issue_type="missing_tls",
                    message=f"HTTPS server {server_index} missing TLS configuration",
                    suggestion="Add TLS configuration for HTTPS servers",
                    file_path=file_name
                ))
            
            # Validate TLS configuration
            if "tls" in server:
                tls = server["tls"]
                
                # Check TLS mode
                if tls.get("mode") == "SIMPLE" and "credentialName" not in tls:
                    issues.append(ValidationIssue(
                        severity="error",
                        resource_type="Gateway",
                        resource_name=name,
                        issue_type="missing_tls_credential",
                        message="TLS mode SIMPLE requires credentialName",
                        suggestion="Specify the Kubernetes secret containing TLS certificates",
                        file_path=file_name
                    ))
                
                # Check minimum TLS version
                min_version = tls.get("minProtocolVersion", "")
                if min_version and min_version < "TLSV1_2":
                    issues.append(ValidationIssue(
                        severity="warning",
                        resource_type="Gateway",
                        resource_name=name,
                        issue_type="weak_tls_version",
                        message=f"Minimum TLS version {min_version} is below recommended TLSV1_2",
                        suggestion="Set minProtocolVersion to TLSV1_2 or higher",
                        file_path=file_name
                    ))
        
        return issues
    
    def _validate_peer_authentication(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate PeerAuthentication specific requirements"""
        issues = []
        name = resource.get("metadata", {}).get("name", "unknown")
        spec = resource.get("spec", {})
        
        # Check mTLS mode
        mtls = spec.get("mtls", {})
        mode = mtls.get("mode", "")
        
        if mode != "STRICT":
            issues.append(ValidationIssue(
                severity="warning",
                resource_type="PeerAuthentication",
                resource_name=name,
                issue_type="permissive_mtls",
                message=f"mTLS mode is {mode}, not STRICT",
                suggestion="Use STRICT mode for production zero-trust security",
                file_path=file_name
            ))
        
        return issues
    
    def _validate_authorization_policy(self, resource: Dict[str, Any], file_name: str) -> List[ValidationIssue]:
        """Validate AuthorizationPolicy specific requirements"""
        issues = []
        name = resource.get("metadata", {}).get("name", "unknown")
        spec = resource.get("spec", {})
        
        # Check for empty rules (allows all)
        rules = spec.get("rules", [])
        action = spec.get("action", "ALLOW")
        
        if action == "ALLOW" and not rules:
            issues.append(ValidationIssue(
                severity="warning",
                resource_type="AuthorizationPolicy",
                resource_name=name,
                issue_type="permissive_authorization",
                message="ALLOW policy with no rules permits all traffic",
                suggestion="Add specific rules to restrict access",
                file_path=file_name
            ))
        
        # Validate rules have proper constraints
        for rule_index, rule in enumerate(rules):
            if not any(k in rule for k in ["from", "to", "when"]):
                issues.append(ValidationIssue(
                    severity="warning",
                    resource_type="AuthorizationPolicy",
                    resource_name=name,
                    issue_type="unconstrained_rule",
                    message=f"Rule {rule_index} has no constraints",
                    suggestion="Add from, to, or when constraints to the rule",
                    file_path=file_name
                ))
        
        return issues
    
    def _validate_service_mesh_completeness(self, manifests: Dict[str, str]) -> List[ValidationIssue]:
        """Validate that all required service mesh components are present"""
        issues = []
        
        # Collect all resources
        all_resources = []
        for content in manifests.values():
            if content:
                try:
                    resources = list(yaml.safe_load_all(content))
                    all_resources.extend([r for r in resources if r])
                except:
                    pass
        
        # Check for required resource types
        resource_types = {r.get("kind", "") for r in all_resources}
        
        required_types = {
            "Gateway": "Ingress gateway for external traffic",
            "VirtualService": "Traffic routing configuration",
            "DestinationRule": "Load balancing and circuit breaking",
            "PeerAuthentication": "mTLS configuration",
            "AuthorizationPolicy": "Access control policies",
            "ServiceMonitor": "Prometheus metrics collection",
            "Telemetry": "Observability configuration"
        }
        
        for required_type, description in required_types.items():
            if required_type not in resource_types:
                severity = "error" if required_type in ["Gateway", "PeerAuthentication"] else "warning"
                issues.append(ValidationIssue(
                    severity=severity,
                    resource_type="ServiceMesh",
                    resource_name="Overall",
                    issue_type="missing_resource_type",
                    message=f"Missing {required_type} resources",
                    suggestion=f"Add {required_type} for {description}"
                ))
        
        return issues
    
    def _validate_security_configurations(self, manifests: Dict[str, str]) -> List[ValidationIssue]:
        """Validate security best practices"""
        issues = []
        
        # Collect all resources
        all_resources = []
        for content in manifests.values():
            if content:
                try:
                    resources = list(yaml.safe_load_all(content))
                    all_resources.extend([r for r in resources if r])
                except:
                    pass
        
        # Check for namespace-wide mTLS
        peer_auths = [r for r in all_resources if r.get("kind") == "PeerAuthentication"]
        namespace_mtls = False
        
        for pa in peer_auths:
            if not pa.get("spec", {}).get("selector"):
                # No selector means namespace-wide
                if pa.get("spec", {}).get("mtls", {}).get("mode") == "STRICT":
                    namespace_mtls = True
                    break
        
        if not namespace_mtls:
            issues.append(ValidationIssue(
                severity="warning",
                resource_type="Security",
                resource_name="mTLS",
                issue_type="missing_namespace_mtls",
                message="No namespace-wide STRICT mTLS policy found",
                suggestion="Add a PeerAuthentication with STRICT mode and no selector"
            ))
        
        # Check for JWT authentication
        request_auths = [r for r in all_resources if r.get("kind") == "RequestAuthentication"]
        if not request_auths:
            issues.append(ValidationIssue(
                severity="info",
                resource_type="Security",
                resource_name="JWT",
                issue_type="missing_jwt_auth",
                message="No JWT authentication configured",
                suggestion="Consider adding RequestAuthentication for API security"
            ))
        
        return issues
    
    def _validate_best_practices(self, manifests: Dict[str, str]) -> List[ValidationIssue]:
        """Validate against Istio best practices"""
        issues = []
        
        # Collect all resources
        all_resources = []
        for content in manifests.values():
            if content:
                try:
                    resources = list(yaml.safe_load_all(content))
                    all_resources.extend([r for r in resources if r])
                except:
                    pass
        
        # Check for resource naming conventions
        for resource in all_resources:
            name = resource.get("metadata", {}).get("name", "")
            kind = resource.get("kind", "")
            
            # Check naming convention
            if kind == "VirtualService" and not name.endswith("-vs"):
                issues.append(ValidationIssue(
                    severity="info",
                    resource_type=kind,
                    resource_name=name,
                    issue_type="naming_convention",
                    message=f"VirtualService '{name}' doesn't follow naming convention",
                    suggestion="Consider naming VirtualServices with '-vs' suffix"
                ))
            
            if kind == "DestinationRule" and not name.endswith("-dr"):
                issues.append(ValidationIssue(
                    severity="info",
                    resource_type=kind,
                    resource_name=name,
                    issue_type="naming_convention",
                    message=f"DestinationRule '{name}' doesn't follow naming convention",
                    suggestion="Consider naming DestinationRules with '-dr' suffix"
                ))
        
        # Check for canary deployment setup
        destination_rules = [r for r in all_resources if r.get("kind") == "DestinationRule"]
        canary_configured = False
        
        for dr in destination_rules:
            subsets = dr.get("spec", {}).get("subsets", [])
            subset_names = {s.get("name", "") for s in subsets}
            if "stable" in subset_names and "canary" in subset_names:
                canary_configured = True
                break
        
        if not canary_configured:
            issues.append(ValidationIssue(
                severity="info",
                resource_type="Deployment",
                resource_name="Canary",
                issue_type="missing_canary_setup",
                message="No canary deployment configuration found",
                suggestion="Consider setting up stable/canary subsets for progressive delivery"
            ))
        
        return issues
    
    async def test_deployment(self, manifests: Dict[str, str]) -> ValidationResult:
        """Test actual deployment of manifests to Kubernetes"""
        result = ValidationResult(
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            issues=[]
        )
        
        if not self.k8s_client:
            result.add_issue(ValidationIssue(
                severity="info",
                resource_type="Deployment",
                resource_name="Test",
                issue_type="no_k8s_access",
                message="Kubernetes cluster not available for deployment testing",
                suggestion="Run with cluster access for deployment validation"
            ))
            return result
        
        # Create temporary directory for manifests
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write manifests to files
            for file_name, content in manifests.items():
                if file_name.endswith('.yaml'):
                    file_path = temp_path / file_name
                    with open(file_path, 'w') as f:
                        f.write(content)
            
            # Test deployment with dry-run
            for file_path in temp_path.glob("*.yaml"):
                try:
                    # Run kubectl apply --dry-run
                    cmd = ["kubectl", "apply", "-f", str(file_path), "--dry-run=client", "-o", "yaml"]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        result.add_issue(ValidationIssue(
                            severity="error",
                            resource_type="Deployment",
                            resource_name=file_path.name,
                            issue_type="deployment_validation",
                            message=f"Deployment validation failed: {stderr.decode()}",
                            suggestion="Fix the Kubernetes resource configuration",
                            file_path=str(file_path)
                        ))
                    else:
                        result.add_issue(ValidationIssue(
                            severity="info",
                            resource_type="Deployment",
                            resource_name=file_path.name,
                            issue_type="deployment_ready",
                            message="Manifest validated successfully for deployment",
                            suggestion="Ready for deployment",
                            file_path=str(file_path)
                        ))
                        
                except Exception as e:
                    result.add_issue(ValidationIssue(
                        severity="error",
                        resource_type="Deployment",
                        resource_name=file_path.name,
                        issue_type="deployment_test_error",
                        message=f"Failed to test deployment: {str(e)}",
                        suggestion="Ensure kubectl is installed and configured",
                        file_path=str(file_path)
                    ))
        
        return result


class IstioInstallationValidator:
    """Validate actual Istio installation and configuration"""
    
    async def validate_istio_installation(self) -> ValidationResult:
        """Validate that Istio is properly installed and configured"""
        result = ValidationResult(
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            issues=[]
        )
        
        # Check istioctl availability
        istioctl_available = await self._check_istioctl()
        if not istioctl_available:
            result.add_issue(ValidationIssue(
                severity="error",
                resource_type="Installation",
                resource_name="istioctl",
                issue_type="missing_istioctl",
                message="istioctl command not found",
                suggestion="Install istioctl from https://istio.io/latest/docs/setup/getting-started/"
            ))
            return result
        
        # Run istioctl analyze
        analyze_issues = await self._run_istioctl_analyze()
        for issue in analyze_issues:
            result.add_issue(issue)
        
        # Check control plane status
        control_plane_issues = await self._check_control_plane()
        for issue in control_plane_issues:
            result.add_issue(issue)
        
        # Validate proxy configuration
        proxy_issues = await self._validate_proxy_configuration()
        for issue in proxy_issues:
            result.add_issue(issue)
        
        return result
    
    async def _check_istioctl(self) -> bool:
        """Check if istioctl is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                "istioctl", "version", "--short",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except:
            return False
    
    async def _run_istioctl_analyze(self) -> List[ValidationIssue]:
        """Run istioctl analyze to find configuration issues"""
        issues = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                "istioctl", "analyze", "--output", "json",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                try:
                    analysis_results = json.loads(stdout)
                    for message in analysis_results.get("messages", []):
                        severity_map = {
                            "ERROR": "error",
                            "WARNING": "warning",
                            "INFO": "info"
                        }
                        
                        issues.append(ValidationIssue(
                            severity=severity_map.get(message.get("level", "INFO"), "info"),
                            resource_type=message.get("origin", {}).get("kind", "Unknown"),
                            resource_name=message.get("origin", {}).get("name", "Unknown"),
                            issue_type="istio_analyze",
                            message=message.get("message", {}).get("message", "Unknown issue"),
                            suggestion=message.get("message", {}).get("documentation", "Check Istio documentation")
                        ))
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            issues.append(ValidationIssue(
                severity="error",
                resource_type="Installation",
                resource_name="analyze",
                issue_type="analyze_failed",
                message=f"Failed to run istioctl analyze: {str(e)}",
                suggestion="Ensure istioctl has access to the cluster"
            ))
        
        return issues
    
    async def _check_control_plane(self) -> List[ValidationIssue]:
        """Check Istio control plane health"""
        issues = []
        
        try:
            # Check istiod deployment
            process = await asyncio.create_subprocess_exec(
                "kubectl", "get", "deployment", "-n", "istio-system", "istiod", "-o", "json",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                deployment = json.loads(stdout)
                status = deployment.get("status", {})
                
                # Check replicas
                replicas = status.get("replicas", 0)
                ready_replicas = status.get("readyReplicas", 0)
                
                if ready_replicas < replicas:
                    issues.append(ValidationIssue(
                        severity="warning",
                        resource_type="ControlPlane",
                        resource_name="istiod",
                        issue_type="replicas_not_ready",
                        message=f"Only {ready_replicas}/{replicas} istiod replicas are ready",
                        suggestion="Check istiod pod logs for errors"
                    ))
                
                # Check for minimum replicas
                if replicas < 2:
                    issues.append(ValidationIssue(
                        severity="warning",
                        resource_type="ControlPlane",
                        resource_name="istiod",
                        issue_type="insufficient_replicas",
                        message=f"Only {replicas} istiod replica(s) configured",
                        suggestion="Increase istiod replicas to at least 2 for HA"
                    ))
                    
        except Exception as e:
            issues.append(ValidationIssue(
                severity="error",
                resource_type="ControlPlane",
                resource_name="istiod",
                issue_type="check_failed",
                message=f"Failed to check control plane: {str(e)}",
                suggestion="Ensure kubectl has access to istio-system namespace"
            ))
        
        return issues
    
    async def _validate_proxy_configuration(self) -> List[ValidationIssue]:
        """Validate Envoy proxy configuration"""
        issues = []
        
        try:
            # Get proxy configuration
            process = await asyncio.create_subprocess_exec(
                "istioctl", "proxy-config", "all", "deployment/istiod", "-n", "istio-system",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                issues.append(ValidationIssue(
                    severity="info",
                    resource_type="ProxyConfig",
                    resource_name="validation",
                    issue_type="proxy_config_check",
                    message="Unable to retrieve proxy configuration",
                    suggestion="This is normal if no workloads are deployed yet"
                ))
                
        except Exception as e:
            # This is often expected if no workloads are deployed
            pass
        
        return issues


# Example usage and testing
async def validate_istio_configurations(manifest_files: Dict[str, str]) -> ValidationResult:
    """Validate Istio configurations"""
    validator = ProductionIstioConfigurationValidator()
    return await validator.validate_complete_service_mesh_configuration(manifest_files)


if __name__ == "__main__":
    # Test validation with sample manifests
    import asyncio
    
    sample_manifests = {
        "virtualservice.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-service-vs
  namespace: default
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
""",
        "destinationrule.yaml": """
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-service-dr
  namespace: default
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
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
"""
    }
    
    async def test_validation():
        result = await validate_istio_configurations(sample_manifests)
        
        print(f"Validation Result: {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"Resources Validated: {result.resources_validated}")
        print(f"Errors: {result.error_count}")
        print(f"Warnings: {result.warning_count}")
        print(f"Info: {result.info_count}")
        print(f"Duration: {result.validation_duration_seconds:.2f}s")
        
        if result.issues:
            print("\nIssues Found:")
            for issue in result.issues:
                icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
                print(f"{icon} [{issue.severity.upper()}] {issue.resource_type}/{issue.resource_name}: {issue.message}")
                print(f"   Suggestion: {issue.suggestion}")
    
    asyncio.run(test_validation())