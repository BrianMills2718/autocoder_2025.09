"""
Production Istio Configuration Validator - FIX 4 Implementation

Comprehensive validation of generated Istio configurations against production standards.
Validates all aspects including security, performance, compliance, and operational requirements.
"""

import yaml
import json
import re
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    error_count: int
    warning_count: int
    errors: List['ValidationIssue']
    warnings: List['ValidationIssue']
    summary: str


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: str  # error, warning, info
    category: str  # security, performance, compliance, etc.
    rule_id: str
    resource_type: str
    resource_name: str
    field_path: str
    message: str
    suggestion: str
    documentation_url: Optional[str] = None


class ProductionIstioConfigurationValidator:
    """Validate generated Istio configurations against production standards"""
    
    # Kubernetes resource schemas for validation
    ISTIO_CONFIGURATION_SCHEMAS = {
        "VirtualService": {
            "type": "object",
            "required": ["apiVersion", "kind", "metadata", "spec"],
            "properties": {
                "apiVersion": {"const": "networking.istio.io/v1beta1"},
                "kind": {"const": "VirtualService"},
                "metadata": {
                    "type": "object",
                    "required": ["name", "namespace"],
                    "properties": {
                        "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
                        "namespace": {"type": "string", "pattern": "^[a-z0-9-]+$"},
                        "labels": {"type": "object"}
                    }
                },
                "spec": {
                    "type": "object",
                    "required": ["hosts"],
                    "properties": {
                        "hosts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1
                        },
                        "gateways": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "http": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "route": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                        "minItems": 1
                                    },
                                    "retries": {
                                        "type": "object",
                                        "required": ["attempts", "perTryTimeout"],
                                        "properties": {
                                            "attempts": {"type": "integer", "minimum": 1, "maximum": 10},
                                            "perTryTimeout": {"type": "string", "pattern": "^[0-9]+[smh]$"}
                                        }
                                    },
                                    "timeout": {"type": "string", "pattern": "^[0-9]+[smh]$"}
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
                "apiVersion": {"const": "networking.istio.io/v1beta1"},
                "kind": {"const": "DestinationRule"},
                "metadata": {
                    "type": "object",
                    "required": ["name", "namespace"]
                },
                "spec": {
                    "type": "object",
                    "required": ["host"],
                    "properties": {
                        "host": {"type": "string"},
                        "trafficPolicy": {
                            "type": "object",
                            "properties": {
                                "connectionPool": {
                                    "type": "object",
                                    "properties": {
                                        "tcp": {
                                            "type": "object",
                                            "properties": {
                                                "maxConnections": {"type": "integer", "minimum": 1, "maximum": 1000},
                                                "connectTimeout": {"type": "string", "pattern": "^[0-9]+[smh]$"}
                                            }
                                        },
                                        "http": {
                                            "type": "object",
                                            "properties": {
                                                "http1MaxPendingRequests": {"type": "integer", "minimum": 1, "maximum": 1000},
                                                "http2MaxRequests": {"type": "integer", "minimum": 1, "maximum": 1000}
                                            }
                                        }
                                    }
                                },
                                "circuitBreaker": {
                                    "type": "object",
                                    "properties": {
                                        "consecutiveGatewayErrors": {"type": "integer", "minimum": 1, "maximum": 50},
                                        "consecutiveServerErrors": {"type": "integer", "minimum": 1, "maximum": 50},
                                        "interval": {"type": "string", "pattern": "^[0-9]+[smh]$"},
                                        "baseEjectionTime": {"type": "string", "pattern": "^[0-9]+[smh]$"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "Gateway": {
            "type": "object",
            "required": ["apiVersion", "kind", "metadata", "spec"],
            "properties": {
                "apiVersion": {"const": "networking.istio.io/v1beta1"},
                "kind": {"const": "Gateway"},
                "spec": {
                    "type": "object",
                    "required": ["selector", "servers"],
                    "properties": {
                        "servers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["port", "hosts"],
                                "properties": {
                                    "port": {
                                        "type": "object",
                                        "required": ["number", "name", "protocol"],
                                        "properties": {
                                            "number": {"type": "integer", "minimum": 1, "maximum": 65535},
                                            "protocol": {"enum": ["HTTP", "HTTPS", "GRPC", "TCP", "TLS"]}
                                        }
                                    },
                                    "hosts": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "PeerAuthentication": {
            "type": "object",
            "required": ["apiVersion", "kind", "metadata", "spec"],
            "properties": {
                "apiVersion": {"const": "security.istio.io/v1beta1"},
                "kind": {"const": "PeerAuthentication"},
                "spec": {
                    "type": "object",
                    "properties": {
                        "mtls": {
                            "type": "object",
                            "properties": {
                                "mode": {"enum": ["UNSET", "DISABLE", "PERMISSIVE", "STRICT"]}
                            }
                        }
                    }
                }
            }
        },
        "AuthorizationPolicy": {
            "type": "object",
            "required": ["apiVersion", "kind", "metadata", "spec"],
            "properties": {
                "apiVersion": {"const": "security.istio.io/v1beta1"},
                "kind": {"const": "AuthorizationPolicy"},
                "spec": {
                    "type": "object",
                    "properties": {
                        "action": {"enum": ["ALLOW", "DENY", "AUDIT", "CUSTOM"]},
                        "rules": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                }
            }
        }
    }
    
    # Production validation rules
    PRODUCTION_RULES = {
        "SECURITY": {
            "SEC-001": {
                "name": "mTLS must be STRICT in production",
                "severity": "error",
                "check": "mtls_strict_mode",
                "message": "PeerAuthentication must use STRICT mTLS mode for production security"
            },
            "SEC-002": {
                "name": "Authorization policies must be defined",
                "severity": "error", 
                "check": "authorization_policies_present",
                "message": "All services must have authorization policies defined"
            },
            "SEC-003": {
                "name": "TLS configuration must be secure",
                "severity": "error",
                "check": "secure_tls_configuration",
                "message": "TLS configuration must use secure protocols and ciphers"
            },
            "SEC-004": {
                "name": "JWT authentication should be configured",
                "severity": "warning",
                "check": "jwt_authentication_configured",
                "message": "Consider enabling JWT authentication for external traffic"
            },
            "SEC-005": {
                "name": "Network policies should be defined",
                "severity": "warning",
                "check": "network_policies_present",
                "message": "Network policies provide defense in depth"
            }
        },
        "PERFORMANCE": {
            "PERF-001": {
                "name": "Connection pool limits must be configured",
                "severity": "error",
                "check": "connection_pool_configured",
                "message": "DestinationRule must have connection pool limits to prevent resource exhaustion"
            },
            "PERF-002": {
                "name": "Circuit breaker must be configured",
                "severity": "error",
                "check": "circuit_breaker_configured",
                "message": "Circuit breakers are required for production resilience"
            },
            "PERF-003": {
                "name": "Retry policy must be reasonable",
                "severity": "warning",
                "check": "reasonable_retry_policy",
                "message": "Retry attempts should be limited to prevent cascade failures"
            },
            "PERF-004": {
                "name": "Timeout values must be configured",
                "severity": "error",
                "check": "timeout_configured",
                "message": "All requests must have timeout configuration"
            },
            "PERF-005": {
                "name": "Load balancing algorithm should be specified",
                "severity": "warning",
                "check": "load_balancing_configured",
                "message": "Explicit load balancing improves predictability"
            }
        },
        "RELIABILITY": {
            "REL-001": {
                "name": "Health checks must be configured",
                "severity": "error",
                "check": "health_checks_configured",
                "message": "Health checks are required for automatic failover"
            },
            "REL-002": {
                "name": "Resource limits must be set",
                "severity": "error",
                "check": "resource_limits_set",
                "message": "All services must have CPU and memory limits"
            },
            "REL-003": {
                "name": "Multiple replicas for HA",
                "severity": "warning",
                "check": "multiple_replicas_configured",
                "message": "Production services should have multiple replicas for high availability"
            },
            "REL-004": {
                "name": "Anti-affinity rules recommended",
                "severity": "warning",
                "check": "anti_affinity_configured",
                "message": "Anti-affinity rules improve fault tolerance"
            }
        },
        "OBSERVABILITY": {
            "OBS-001": {
                "name": "Telemetry configuration must be present",
                "severity": "error",
                "check": "telemetry_configured",
                "message": "Telemetry configuration is required for production monitoring"
            },
            "OBS-002": {
                "name": "Distributed tracing should be enabled",
                "severity": "warning",
                "check": "tracing_enabled",
                "message": "Distributed tracing is essential for troubleshooting"
            },
            "OBS-003": {
                "name": "Access logging should be configured",
                "severity": "warning",
                "check": "access_logging_configured",
                "message": "Access logs are important for audit and debugging"
            },
            "OBS-004": {
                "name": "ServiceMonitor should be present",
                "severity": "warning",
                "check": "service_monitor_present",
                "message": "ServiceMonitor enables Prometheus metrics collection"
            }
        },
        "COMPLIANCE": {
            "COMP-001": {
                "name": "Resource names must follow naming conventions",
                "severity": "error",
                "check": "naming_conventions",
                "message": "Resource names must follow kebab-case convention"
            },
            "COMP-002": {
                "name": "Labels must be consistent",
                "severity": "warning",
                "check": "consistent_labels",
                "message": "All resources should have consistent labeling"
            },
            "COMP-003": {
                "name": "Annotations should include metadata",
                "severity": "info",
                "check": "metadata_annotations",
                "message": "Include deployment and contact information in annotations"
            }
        }
    }
    
    def __init__(self):
        self.validation_results = []
        self.resource_inventory = {}
    
    def validate_complete_service_mesh_configuration(self, 
                                                   generated_manifests: Dict[str, Any]) -> ValidationResult:
        """Validate all generated manifests against production standards"""
        
        validation_results = []
        
        # Track all resources for cross-validation
        self.resource_inventory = self._build_resource_inventory(generated_manifests)
        
        for manifest_name, manifest_content in generated_manifests.items():
            if isinstance(manifest_content, str):
                # Parse YAML content and validate each Kubernetes resource
                try:
                    parsed_manifests = list(yaml.safe_load_all(manifest_content))
                    
                    for resource in parsed_manifests:
                        if not resource:
                            continue
                        
                        resource_validation = self._validate_kubernetes_resource(manifest_name, resource)
                        validation_results.extend(resource_validation)
                        
                except yaml.YAMLError as e:
                    validation_results.append(ValidationIssue(
                        severity="error",
                        category="syntax",
                        rule_id="YAML-001",
                        resource_type="YAML",
                        resource_name=manifest_name,
                        field_path="",
                        message=f"YAML parsing error: {e}",
                        suggestion="Fix YAML syntax errors"
                    ))
        
        # Validate overall service mesh completeness and security configurations
        completeness_validation = self._validate_service_mesh_completeness(generated_manifests)
        security_validation = self._validate_security_configurations(generated_manifests)
        cross_reference_validation = self._validate_cross_references()
        
        validation_results.extend(completeness_validation)
        validation_results.extend(security_validation)
        validation_results.extend(cross_reference_validation)
        
        # Calculate summary statistics
        errors = [v for v in validation_results if v.severity == "error"]
        warnings = [v for v in validation_results if v.severity == "warning"]
        
        is_valid = len(errors) == 0
        summary = self._generate_validation_summary(validation_results)
        
        return ValidationResult(
            is_valid=is_valid,
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            summary=summary
        )
    
    def _build_resource_inventory(self, generated_manifests: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Build inventory of all resources for cross-validation"""
        
        inventory = {}
        
        for manifest_name, manifest_content in generated_manifests.items():
            if isinstance(manifest_content, str):
                try:
                    parsed_manifests = list(yaml.safe_load_all(manifest_content))
                    
                    for resource in parsed_manifests:
                        if not resource or not isinstance(resource, dict):
                            continue
                        
                        kind = resource.get("kind", "Unknown")
                        if kind not in inventory:
                            inventory[kind] = []
                        
                        inventory[kind].append({
                            "manifest_file": manifest_name,
                            "resource": resource
                        })
                        
                except yaml.YAMLError:
                    continue  # Error will be caught in main validation
        
        return inventory
    
    def _validate_kubernetes_resource(self, manifest_name: str, resource: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate individual Kubernetes resource"""
        
        issues = []
        
        if not isinstance(resource, dict):
            return issues
        
        kind = resource.get("kind")
        if not kind:
            issues.append(ValidationIssue(
                severity="error",
                category="schema",
                rule_id="SCH-001",
                resource_type="Unknown",
                resource_name=manifest_name,
                field_path="kind",
                message="Resource must have 'kind' field",
                suggestion="Add 'kind' field to resource definition"
            ))
            return issues
        
        resource_name = resource.get("metadata", {}).get("name", "unnamed")
        
        # Schema validation
        if kind in self.ISTIO_CONFIGURATION_SCHEMAS:
            schema_issues = self._validate_against_schema(resource, kind, resource_name)
            issues.extend(schema_issues)
        
        # Production rules validation
        production_issues = self._validate_production_rules(resource, kind, resource_name)
        issues.extend(production_issues)
        
        return issues
    
    def _validate_against_schema(self, resource: Dict[str, Any], kind: str, resource_name: str) -> List[ValidationIssue]:
        """Validate resource against JSON schema"""
        
        issues = []
        schema = self.ISTIO_CONFIGURATION_SCHEMAS.get(kind)
        
        if not schema:
            return issues
        
        try:
            validate(instance=resource, schema=schema)
        except ValidationError as e:
            # Convert JSONSchema validation error to ValidationIssue
            field_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            
            issues.append(ValidationIssue(
                severity="error",
                category="schema",
                rule_id="SCH-002",
                resource_type=kind,
                resource_name=resource_name,
                field_path=field_path,
                message=f"Schema validation failed: {e.message}",
                suggestion="Fix the schema violation according to Istio API specification",
                documentation_url=f"https://istio.io/latest/docs/reference/config/networking/v1beta1/{kind.lower()}/"
            ))
        
        return issues
    
    def _validate_production_rules(self, resource: Dict[str, Any], kind: str, resource_name: str) -> List[ValidationIssue]:
        """Validate resource against production rules"""
        
        issues = []
        
        # Apply rules based on resource type
        if kind == "PeerAuthentication":
            issues.extend(self._validate_peer_authentication(resource, resource_name))
        elif kind == "VirtualService":
            issues.extend(self._validate_virtual_service(resource, resource_name))
        elif kind == "DestinationRule":
            issues.extend(self._validate_destination_rule(resource, resource_name))
        elif kind == "Gateway":
            issues.extend(self._validate_gateway(resource, resource_name))
        elif kind == "AuthorizationPolicy":
            issues.extend(self._validate_authorization_policy(resource, resource_name))
        
        # Apply common rules to all resources
        issues.extend(self._validate_common_rules(resource, kind, resource_name))
        
        return issues
    
    def _validate_peer_authentication(self, resource: Dict[str, Any], resource_name: str) -> List[ValidationIssue]:
        """Validate PeerAuthentication resource"""
        
        issues = []
        
        # SEC-001: mTLS must be STRICT in production
        mtls_mode = resource.get("spec", {}).get("mtls", {}).get("mode")
        if mtls_mode != "STRICT":
            issues.append(ValidationIssue(
                severity="error",
                category="security",
                rule_id="SEC-001",
                resource_type="PeerAuthentication",
                resource_name=resource_name,
                field_path="spec.mtls.mode",
                message="mTLS mode must be STRICT for production security",
                suggestion="Set spec.mtls.mode to STRICT",
                documentation_url="https://istio.io/latest/docs/tasks/security/authentication/mtls-migration/"
            ))
        
        return issues
    
    def _validate_virtual_service(self, resource: Dict[str, Any], resource_name: str) -> List[ValidationIssue]:
        """Validate VirtualService resource"""
        
        issues = []
        
        spec = resource.get("spec", {})
        http_routes = spec.get("http", [])
        
        for i, route in enumerate(http_routes):
            route_path = f"spec.http[{i}]"
            
            # PERF-004: Timeout values must be configured
            if "timeout" not in route:
                issues.append(ValidationIssue(
                    severity="error",
                    category="performance",
                    rule_id="PERF-004",
                    resource_type="VirtualService",
                    resource_name=resource_name,
                    field_path=f"{route_path}.timeout",
                    message="HTTP route must have timeout configuration",
                    suggestion="Add timeout field to HTTP route (e.g., '30s')",
                    documentation_url="https://istio.io/latest/docs/reference/config/networking/virtual-service/#HTTPRoute"
                ))
            
            # PERF-003: Retry policy must be reasonable
            retries = route.get("retries", {})
            if retries:
                attempts = retries.get("attempts", 0)
                if attempts > 5:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="performance",
                        rule_id="PERF-003",
                        resource_type="VirtualService",
                        resource_name=resource_name,
                        field_path=f"{route_path}.retries.attempts",
                        message="Too many retry attempts can cause cascade failures",
                        suggestion="Limit retry attempts to 5 or fewer"
                    ))
            
            # Validate route destinations exist
            route_destinations = route.get("route", [])
            for j, destination in enumerate(route_destinations):
                dest_host = destination.get("destination", {}).get("host")
                if dest_host and not self._is_valid_destination(dest_host):
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="configuration",
                        rule_id="CONF-001",
                        resource_type="VirtualService",
                        resource_name=resource_name,
                        field_path=f"{route_path}.route[{j}].destination.host",
                        message=f"Destination host '{dest_host}' may not exist",
                        suggestion="Verify that the destination service exists"
                    ))
        
        return issues
    
    def _validate_destination_rule(self, resource: Dict[str, Any], resource_name: str) -> List[ValidationIssue]:
        """Validate DestinationRule resource"""
        
        issues = []
        
        spec = resource.get("spec", {})
        traffic_policy = spec.get("trafficPolicy", {})
        
        # PERF-001: Connection pool limits must be configured
        connection_pool = traffic_policy.get("connectionPool")
        if not connection_pool:
            issues.append(ValidationIssue(
                severity="error",
                category="performance",
                rule_id="PERF-001",
                resource_type="DestinationRule",
                resource_name=resource_name,
                field_path="spec.trafficPolicy.connectionPool",
                message="Connection pool must be configured to prevent resource exhaustion",
                suggestion="Add connectionPool configuration with tcp and http settings",
                documentation_url="https://istio.io/latest/docs/reference/config/networking/destination-rule/#ConnectionPoolSettings"
            ))
        else:
            # Validate connection pool settings
            tcp_settings = connection_pool.get("tcp", {})
            http_settings = connection_pool.get("http", {})
            
            if not tcp_settings.get("maxConnections"):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="performance",
                    rule_id="PERF-001",
                    resource_type="DestinationRule",
                    resource_name=resource_name,
                    field_path="spec.trafficPolicy.connectionPool.tcp.maxConnections",
                    message="TCP max connections should be configured",
                    suggestion="Set maxConnections limit (e.g., 100)"
                ))
            
            if not http_settings.get("http1MaxPendingRequests"):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="performance",
                    rule_id="PERF-001",
                    resource_type="DestinationRule",
                    resource_name=resource_name,
                    field_path="spec.trafficPolicy.connectionPool.http.http1MaxPendingRequests",
                    message="HTTP max pending requests should be configured",
                    suggestion="Set http1MaxPendingRequests limit (e.g., 50)"
                ))
        
        # PERF-002: Circuit breaker must be configured
        circuit_breaker = traffic_policy.get("circuitBreaker") or traffic_policy.get("outlierDetection")
        if not circuit_breaker:
            issues.append(ValidationIssue(
                severity="error",
                category="performance",
                rule_id="PERF-002",
                resource_type="DestinationRule",
                resource_name=resource_name,
                field_path="spec.trafficPolicy.circuitBreaker",
                message="Circuit breaker is required for production resilience",
                suggestion="Add circuitBreaker or outlierDetection configuration",
                documentation_url="https://istio.io/latest/docs/reference/config/networking/destination-rule/#OutlierDetection"
            ))
        
        return issues
    
    def _validate_gateway(self, resource: Dict[str, Any], resource_name: str) -> List[ValidationIssue]:
        """Validate Gateway resource"""
        
        issues = []
        
        spec = resource.get("spec", {})
        servers = spec.get("servers", [])
        
        for i, server in enumerate(servers):
            server_path = f"spec.servers[{i}]"
            
            # SEC-003: TLS configuration must be secure
            tls = server.get("tls", {})
            if tls:
                # Check TLS mode
                tls_mode = tls.get("mode")
                if tls_mode in ["PASSTHROUGH", "SIMPLE", "MUTUAL"]:
                    # Check for secure TLS versions
                    min_protocol = tls.get("minProtocolVersion")
                    if not min_protocol or min_protocol < "TLSV1_2":
                        issues.append(ValidationIssue(
                            severity="error",
                            category="security",
                            rule_id="SEC-003",
                            resource_type="Gateway",
                            resource_name=resource_name,
                            field_path=f"{server_path}.tls.minProtocolVersion",
                            message="TLS minimum version must be TLSv1.2 or higher",
                            suggestion="Set minProtocolVersion to TLSV1_2 or TLSV1_3"
                        ))
                    
                    # Check for secure cipher suites
                    cipher_suites = tls.get("cipherSuites", [])
                    if cipher_suites:
                        insecure_ciphers = [c for c in cipher_suites if "RC4" in c or "DES" in c or "MD5" in c]
                        if insecure_ciphers:
                            issues.append(ValidationIssue(
                                severity="error",
                                category="security",
                                rule_id="SEC-003",
                                resource_type="Gateway",
                                resource_name=resource_name,
                                field_path=f"{server_path}.tls.cipherSuites",
                                message=f"Insecure cipher suites detected: {insecure_ciphers}",
                                suggestion="Remove insecure cipher suites and use only modern, secure ciphers"
                            ))
            
            # Check port configuration
            port = server.get("port", {})
            port_number = port.get("number")
            if port_number:
                # Warn about non-standard ports
                if port_number not in [80, 443, 8080, 8443, 9090, 9443, 15443]:
                    issues.append(ValidationIssue(
                        severity="info",
                        category="configuration",
                        rule_id="CONF-002",
                        resource_type="Gateway",
                        resource_name=resource_name,
                        field_path=f"{server_path}.port.number",
                        message=f"Non-standard port {port_number} in use",
                        suggestion="Consider using standard ports for better compatibility"
                    ))
        
        return issues
    
    def _validate_authorization_policy(self, resource: Dict[str, Any], resource_name: str) -> List[ValidationIssue]:
        """Validate AuthorizationPolicy resource"""
        
        issues = []
        
        spec = resource.get("spec", {})
        
        # Check if action is specified
        action = spec.get("action", "ALLOW")  # Default is ALLOW
        
        # Validate rules exist for ALLOW policies
        rules = spec.get("rules", [])
        if action == "ALLOW" and not rules:
            issues.append(ValidationIssue(
                severity="warning",
                category="security",
                rule_id="SEC-002",
                resource_type="AuthorizationPolicy",
                resource_name=resource_name,
                field_path="spec.rules",
                message="ALLOW policy without rules grants access to all requests",
                suggestion="Add specific rules to restrict access appropriately"
            ))
        
        # Validate rule structure
        for i, rule in enumerate(rules):
            rule_path = f"spec.rules[{i}]"
            
            # Check for overly permissive rules
            from_sources = rule.get("from", [])
            to_operations = rule.get("to", [])
            when_conditions = rule.get("when", [])
            
            if not from_sources and not when_conditions:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="security",
                    rule_id="SEC-002",
                    resource_type="AuthorizationPolicy",
                    resource_name=resource_name,
                    field_path=rule_path,
                    message="Rule without source restrictions may be overly permissive",
                    suggestion="Add 'from' sources or 'when' conditions to restrict access"
                ))
        
        return issues
    
    def _validate_common_rules(self, resource: Dict[str, Any], kind: str, resource_name: str) -> List[ValidationIssue]:
        """Validate common rules that apply to all resources"""
        
        issues = []
        
        # COMP-001: Naming conventions
        if not re.match(r'^[a-z0-9-]+$', resource_name):
            issues.append(ValidationIssue(
                severity="error",
                category="compliance",
                rule_id="COMP-001",
                resource_type=kind,
                resource_name=resource_name,
                field_path="metadata.name",
                message="Resource name must follow kebab-case convention",
                suggestion="Use only lowercase letters, numbers, and hyphens"
            ))
        
        # COMP-002: Consistent labels
        metadata = resource.get("metadata", {})
        labels = metadata.get("labels", {})
        
        required_labels = ["app", "version"]
        for label in required_labels:
            if label not in labels:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="compliance",
                    rule_id="COMP-002",
                    resource_type=kind,
                    resource_name=resource_name,
                    field_path=f"metadata.labels.{label}",
                    message=f"Missing recommended label: {label}",
                    suggestion=f"Add '{label}' label for better resource management"
                ))
        
        return issues
    
    def _validate_service_mesh_completeness(self, generated_manifests: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate that the service mesh configuration is complete"""
        
        issues = []
        
        # Check for essential security components
        if "PeerAuthentication" not in self.resource_inventory:
            issues.append(ValidationIssue(
                severity="error",
                category="security",
                rule_id="SEC-001",
                resource_type="ServiceMesh",
                resource_name="complete_configuration",
                field_path="security",
                message="No PeerAuthentication resources found",
                suggestion="Add PeerAuthentication resources to enable mTLS"
            ))
        
        if "AuthorizationPolicy" not in self.resource_inventory:
            issues.append(ValidationIssue(
                severity="error",
                category="security",
                rule_id="SEC-002",
                resource_type="ServiceMesh",
                resource_name="complete_configuration",
                field_path="security",
                message="No AuthorizationPolicy resources found",
                suggestion="Add AuthorizationPolicy resources for access control"
            ))
        
        # Check for traffic management components
        if "VirtualService" not in self.resource_inventory:
            issues.append(ValidationIssue(
                severity="warning",
                category="configuration",
                rule_id="CONF-003",
                resource_type="ServiceMesh",
                resource_name="complete_configuration",
                field_path="traffic",
                message="No VirtualService resources found",
                suggestion="Add VirtualService resources for traffic routing"
            ))
        
        if "DestinationRule" not in self.resource_inventory:
            issues.append(ValidationIssue(
                severity="error",
                category="performance",
                rule_id="PERF-001",
                resource_type="ServiceMesh",
                resource_name="complete_configuration",
                field_path="traffic",
                message="No DestinationRule resources found",
                suggestion="Add DestinationRule resources for connection pooling and circuit breaking"
            ))
        
        # Check for observability components
        if "Telemetry" not in self.resource_inventory:
            issues.append(ValidationIssue(
                severity="error",
                category="observability",
                rule_id="OBS-001",
                resource_type="ServiceMesh",
                resource_name="complete_configuration",
                field_path="observability",
                message="No Telemetry resources found",
                suggestion="Add Telemetry resources for metrics and tracing"
            ))
        
        return issues
    
    def _validate_security_configurations(self, generated_manifests: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate security-specific configurations"""
        
        issues = []
        
        # Check for proper mTLS configuration across all PeerAuthentication resources
        peer_auths = self.resource_inventory.get("PeerAuthentication", [])
        strict_mtls_count = 0
        
        for peer_auth_info in peer_auths:
            peer_auth = peer_auth_info["resource"]
            mtls_mode = peer_auth.get("spec", {}).get("mtls", {}).get("mode")
            if mtls_mode == "STRICT":
                strict_mtls_count += 1
        
        if peer_auths and strict_mtls_count == 0:
            issues.append(ValidationIssue(
                severity="error",
                category="security",
                rule_id="SEC-001",
                resource_type="PeerAuthentication",
                resource_name="security_configuration",
                field_path="spec.mtls.mode",
                message="No PeerAuthentication resources have STRICT mTLS mode",
                suggestion="Set at least one PeerAuthentication to STRICT mode for production"
            ))
        
        # Check for gateway security
        gateways = self.resource_inventory.get("Gateway", [])
        insecure_gateways = 0
        
        for gateway_info in gateways:
            gateway = gateway_info["resource"]
            servers = gateway.get("spec", {}).get("servers", [])
            
            for server in servers:
                port = server.get("port", {})
                if port.get("protocol") == "HTTP" and port.get("number") not in [80]:
                    insecure_gateways += 1
        
        if insecure_gateways > 0:
            issues.append(ValidationIssue(
                severity="warning",
                category="security",
                rule_id="SEC-003",
                resource_type="Gateway",
                resource_name="security_configuration",
                field_path="spec.servers",
                message=f"{insecure_gateways} gateway(s) may be using insecure HTTP",
                suggestion="Configure HTTPS with proper TLS settings for production"
            ))
        
        return issues
    
    def _validate_cross_references(self) -> List[ValidationIssue]:
        """Validate cross-references between resources"""
        
        issues = []
        
        # Validate VirtualService -> DestinationRule relationships
        virtual_services = self.resource_inventory.get("VirtualService", [])
        destination_rules = self.resource_inventory.get("DestinationRule", [])
        
        # Build list of destination hosts from DestinationRules
        destination_hosts = set()
        for dr_info in destination_rules:
            dr = dr_info["resource"]
            host = dr.get("spec", {}).get("host")
            if host:
                destination_hosts.add(host)
        
        # Check that VirtualService destinations have corresponding DestinationRules
        for vs_info in virtual_services:
            vs = vs_info["resource"]
            vs_name = vs.get("metadata", {}).get("name", "unknown")
            
            http_routes = vs.get("spec", {}).get("http", [])
            for route in http_routes:
                route_destinations = route.get("route", [])
                for destination in route_destinations:
                    dest_host = destination.get("destination", {}).get("host")
                    if dest_host and dest_host not in destination_hosts:
                        issues.append(ValidationIssue(
                            severity="warning",
                            category="configuration",
                            rule_id="CONF-001",
                            resource_type="VirtualService",
                            resource_name=vs_name,
                            field_path="spec.http.route.destination.host",
                            message=f"VirtualService references host '{dest_host}' without corresponding DestinationRule",
                            suggestion=f"Add DestinationRule for host '{dest_host}' or verify the hostname"
                        ))
        
        return issues
    
    def _is_valid_destination(self, dest_host: str) -> bool:
        """Check if destination host is valid (simplified check)"""
        
        # Check if it's a service in the current namespace
        if dest_host.endswith('-service'):
            return True
        
        # Check if it's a FQDN
        if '.' in dest_host:
            return True
        
        # Check against known services in DestinationRules
        destination_rules = self.resource_inventory.get("DestinationRule", [])
        for dr_info in destination_rules:
            dr = dr_info["resource"]
            host = dr.get("spec", {}).get("host")
            if host == dest_host:
                return True
        
        return False
    
    def _generate_validation_summary(self, validation_results: List[ValidationIssue]) -> str:
        """Generate a summary of validation results"""
        
        if not validation_results:
            return "✅ All Istio configurations pass production validation"
        
        # Group issues by severity and category
        errors = [v for v in validation_results if v.severity == "error"]
        warnings = [v for v in validation_results if v.severity == "warning"]
        infos = [v for v in validation_results if v.severity == "info"]
        
        # Group by category
        categories = {}
        for issue in validation_results:
            if issue.category not in categories:
                categories[issue.category] = {"errors": 0, "warnings": 0, "infos": 0}
            categories[issue.category][f"{issue.severity}s"] += 1
        
        summary_lines = []
        
        if errors:
            summary_lines.append(f"❌ {len(errors)} error(s) found - configuration not ready for production")
        
        if warnings:
            summary_lines.append(f"⚠️ {len(warnings)} warning(s) found - review recommended")
        
        if infos:
            summary_lines.append(f"ℹ️ {len(infos)} info message(s)")
        
        if categories:
            summary_lines.append("\nIssues by category:")
            for category, counts in categories.items():
                category_summary = []
                if counts["errors"] > 0:
                    category_summary.append(f"{counts['errors']} errors")
                if counts["warnings"] > 0:
                    category_summary.append(f"{counts['warnings']} warnings")
                if counts["infos"] > 0:
                    category_summary.append(f"{counts['infos']} infos")
                
                if category_summary:
                    summary_lines.append(f"  {category}: {', '.join(category_summary)}")
        
        return "\n".join(summary_lines)


def validate_istio_deployment_configuration(deployment_configs: Dict[str, str]) -> ValidationResult:
    """
    Main function to validate Istio deployment configuration.
    This is the entry point for FIX 4 validation.
    """
    
    validator = ProductionIstioConfigurationValidator()
    
    # Validate the complete service mesh configuration
    result = validator.validate_complete_service_mesh_configuration(deployment_configs)
    
    # Log validation results
    logger.info(f"Istio configuration validation completed:")
    logger.info(f"  Errors: {result.error_count}")
    logger.info(f"  Warnings: {result.warning_count}")
    logger.info(f"  Valid: {result.is_valid}")
    
    # Log detailed issues
    for error in result.errors:
        logger.error(f"ERROR [{error.rule_id}] {error.resource_type}/{error.resource_name}: {error.message}")
    
    for warning in result.warnings:
        logger.warning(f"WARNING [{warning.rule_id}] {warning.resource_type}/{warning.resource_name}: {warning.message}")
    
    return result


if __name__ == "__main__":
    # Example usage
    import sys
    from pathlib import Path
    
    if len(sys.argv) != 2:
        print("Usage: python production_istio_validator.py <manifest_directory>")
        sys.exit(1)
    
    manifest_dir = Path(sys.argv[1])
    if not manifest_dir.exists():
        print(f"Directory {manifest_dir} does not exist")
        sys.exit(1)
    
    # Load all YAML files from directory
    manifests = {}
    for yaml_file in manifest_dir.glob("*.yaml"):
        manifests[yaml_file.name] = yaml_file.read_text()
    
    # Validate
    result = validate_istio_deployment_configuration(manifests)
    
    # Print results
    print(result.summary)
    
    if result.errors:
        print("\nDetailed Errors:")
        for error in result.errors:
            print(f"  {error.rule_id}: {error.message}")
            print(f"    Resource: {error.resource_type}/{error.resource_name}")
            print(f"    Field: {error.field_path}")
            print(f"    Suggestion: {error.suggestion}")
            if error.documentation_url:
                print(f"    Documentation: {error.documentation_url}")
            print()
    
    # Exit with error code if validation failed
    sys.exit(0 if result.is_valid else 1)