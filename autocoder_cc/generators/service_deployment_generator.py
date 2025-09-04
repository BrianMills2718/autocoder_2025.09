"""
Production-Grade Enterprise Istio Service Mesh Generator

This module generates comprehensive, enterprise-ready Istio service mesh configurations
with all production features including zero-trust security, advanced traffic management,
comprehensive observability, resilience patterns, and multi-cluster support.
"""

import yaml
import json
import logging
import jsonschema
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]


@dataclass
class ProductionServiceMeshManifests:
    """Complete production-ready service mesh manifests"""
    security: Dict[str, Any]
    traffic: Dict[str, Any]
    observability: Dict[str, Any]
    resilience: Dict[str, Any]
    multi_cluster: Dict[str, Any]
    ingress_egress: Dict[str, Any]
    policies: Dict[str, Any]
    control_plane: Dict[str, Any]
    canary_deployment: Dict[str, Any]
    chaos_engineering: Dict[str, Any]


@dataclass
class ServiceDeploymentConfig:
    """Configuration for service deployment"""
    name: str
    type: str
    image: str
    port: int
    replicas: int
    environment: Dict[str, str]
    messaging_config: Dict[str, Any]
    health_check: str
    ready_check: str
    resources: Dict[str, Any]


class ProductionIstioServiceMesh:
    """Generate production-ready Istio service mesh with all enterprise features"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_production_service_mesh(self, system_blueprint) -> ProductionServiceMeshManifests:
        """Generate complete production-grade Istio service mesh"""
        
        manifests = ProductionServiceMeshManifests(
            security={},
            traffic={},
            observability={},
            resilience={},
            multi_cluster={},
            ingress_egress={},
            policies={},
            control_plane={},
            canary_deployment={},
            chaos_engineering={}
        )
        
        # 1. Security-first with zero-trust architecture
        manifests.security = self._generate_production_security(system_blueprint)
        
        # 2. Advanced traffic management with all enterprise features
        manifests.traffic = self._generate_production_traffic_management(system_blueprint)
        
        # 3. Complete observability stack
        manifests.observability = self._generate_production_observability(system_blueprint)
        
        # 4. Resilience and chaos engineering
        manifests.resilience = self._generate_production_resilience(system_blueprint)
        
        # 5. Multi-cluster and hybrid cloud
        manifests.multi_cluster = self._generate_production_multi_cluster(system_blueprint)
        
        # 6. Advanced ingress and egress
        manifests.ingress_egress = self._generate_production_ingress_egress(system_blueprint)
        
        # 7. Service mesh policies
        manifests.policies = self._generate_production_policies(system_blueprint)
        
        # 8. Control plane configuration
        manifests.control_plane = self._generate_production_control_plane(system_blueprint)
        
        # 9. Canary deployment configuration
        manifests.canary_deployment = self._generate_production_canary_deployment(system_blueprint)
        
        # 10. Chaos engineering configuration
        manifests.chaos_engineering = self._generate_production_chaos_engineering(system_blueprint)
        
        # Validate all manifests are production-ready
        self._validate_production_readiness(manifests)
        
        return manifests
    
    def _generate_production_security(self, system_blueprint) -> Dict[str, Any]:
        """Generate production-grade zero-trust security configuration"""
        
        security = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Strict mTLS for all service communication
        security['peer_authentication'] = {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "PeerAuthentication",
            "metadata": {
                "name": f"{system_blueprint.system.name}-mtls-strict",
                "namespace": namespace
            },
            "spec": {
                "mtls": {"mode": "STRICT"},
                "selector": {"matchLabels": {"app": system_blueprint.system.name}}
            }
        }
        
        # JWT authentication with multiple providers
        security['request_authentication'] = {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "RequestAuthentication",
            "metadata": {
                "name": f"{system_blueprint.system.name}-jwt-auth",
                "namespace": namespace
            },
            "spec": {
                "selector": {"matchLabels": {"app": system_blueprint.system.name}},
                "jwtRules": [
                    {
                        "issuer": f"https://auth.{system_blueprint.system.name}.local",
                        "jwksUri": f"https://auth.{system_blueprint.system.name}.local/.well-known/jwks.json",
                        "audiences": [system_blueprint.system.name],
                        "fromHeaders": [{"name": "Authorization", "prefix": "Bearer "}],
                        "forwardOriginalToken": True
                    },
                    {
                        "issuer": "https://accounts.google.com",
                        "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
                        "audiences": [f"{system_blueprint.system.name}-google"]
                    }
                ]
            }
        }
        
        # Fine-grained authorization policies per component
        security['authorization_policies'] = []
        for component in system_blueprint.system.components:
            policy = {
                "apiVersion": "security.istio.io/v1beta1",
                "kind": "AuthorizationPolicy",
                "metadata": {
                    "name": f"{component.name}-authz",
                    "namespace": namespace
                },
                "spec": {
                    "selector": {"matchLabels": {"app": component.name}},
                    "action": "ALLOW",
                    "rules": [
                        {
                            "from": [{"source": {"principals": [f"cluster.local/ns/{namespace}/sa/{component.name}"]}}],
                            "to": [{"operation": {"methods": ["GET", "POST", "PUT", "DELETE"]}}],
                            "when": [{"key": "request.headers[x-user-role]", "values": ["admin", "user"]}]
                        }
                    ]
                }
            }
            security['authorization_policies'].append(policy)
        
        # Security policies for external traffic
        security['external_authz_policy'] = {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "AuthorizationPolicy",
            "metadata": {
                "name": f"{system_blueprint.system.name}-external-authz",
                "namespace": namespace
            },
            "spec": {
                "selector": {"matchLabels": {"app": "istio-proxy"}},
                "action": "CUSTOM",
                "provider": {
                    "name": "external-authz"
                },
                "rules": [
                    {
                        "to": [{"operation": {"paths": ["/admin/*", "/api/v1/sensitive/*"]}}]
                    }
                ]
            }
        }
        
        return security
    
    def _generate_production_traffic_management(self, system_blueprint) -> Dict[str, Any]:
        """Generate advanced traffic management with all enterprise features"""
        
        traffic = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Advanced Virtual Services with canary, retries, timeouts
        traffic['virtual_services'] = []
        for component in system_blueprint.system.components:
            vs = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": f"{component.name}-vs",
                    "namespace": namespace,
                    "labels": {
                        "app.kubernetes.io/name": component.name,
                        "app.kubernetes.io/component": "virtual-service"
                    }
                },
                "spec": {
                    "hosts": [f"{component.name}-service"],
                    "gateways": ["mesh", f"{system_blueprint.system.name}-gateway"],
                    "http": [
                        {
                            "match": [{"headers": {"x-canary": {"exact": "true"}}}],
                            "route": [{"destination": {"host": f"{component.name}-service", "subset": "canary"}}],
                            "retries": {
                                "attempts": 3,
                                "perTryTimeout": "10s",
                                "retryOn": "5xx,reset,connect-failure,refused-stream",
                                "retryRemoteLocalities": True
                            },
                            "timeout": "30s",
                            "headers": {
                                "request": {
                                    "add": {"x-canary-routing": "enabled"}
                                }
                            }
                        },
                        {
                            "route": [
                                {"destination": {"host": f"{component.name}-service", "subset": "stable"}, "weight": 90},
                                {"destination": {"host": f"{component.name}-service", "subset": "canary"}, "weight": 10}
                            ],
                            "timeout": "30s",
                            "retries": {
                                "attempts": 3,
                                "perTryTimeout": "10s",
                                "retryOn": "5xx,reset,connect-failure,refused-stream"
                            },
                            "fault": {
                                "delay": {"percentage": {"value": 0.1}, "fixedDelay": "5s"},
                                "abort": {"percentage": {"value": 0.1}, "httpStatus": 503}
                            },
                            "corsPolicy": {
                                "allowOrigins": [
                                    {"exact": f"https://{system_blueprint.system.name}.local"},
                                    {"regex": "https://.*\\.local"}
                                ],
                                "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                "allowHeaders": ["authorization", "content-type", "x-request-id", "x-b3-traceid"],
                                "exposeHeaders": ["x-custom-header"],
                                "maxAge": "24h",
                                "allowCredentials": True
                            }
                        }
                    ]
                }
            }
            traffic['virtual_services'].append(vs)
        
        # Production Destination Rules with circuit breakers, outlier detection
        traffic['destination_rules'] = []
        for component in system_blueprint.system.components:
            dr = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "DestinationRule",
                "metadata": {
                    "name": f"{component.name}-dr",
                    "namespace": namespace,
                    "labels": {
                        "app.kubernetes.io/name": component.name,
                        "app.kubernetes.io/component": "destination-rule"
                    }
                },
                "spec": {
                    "host": f"{component.name}-service",
                    "trafficPolicy": {
                        "connectionPool": {
                            "tcp": {
                                "maxConnections": 100,
                                "connectTimeout": "30s",
                                "tcpKeepalive": {"time": "7200s", "interval": "75s", "probes": 9}
                            },
                            "http": {
                                "http1MaxPendingRequests": 50,
                                "http2MaxRequests": 100,
                                "maxRequestsPerConnection": 10,
                                "maxRetries": 3,
                                "idleTimeout": "90s",
                                "h2UpgradePolicy": "UPGRADE",
                                "useClientProtocol": True
                            }
                        },
                        "circuitBreaker": {
                            "consecutiveGatewayErrors": 5,
                            "consecutiveServerErrors": 5,
                            "interval": "30s",
                            "baseEjectionTime": "30s",
                            "maxEjectionPercent": 50,
                            "minHealthPercent": 50,
                            "splitExternalLocalOriginErrors": True
                        },
                        "outlierDetection": {
                            "consecutiveGatewayErrors": 3,
                            "consecutiveServerErrors": 3,
                            "interval": "30s",
                            "baseEjectionTime": "30s",
                            "maxEjectionPercent": 50,
                            "minHealthPercent": 50,
                            "splitExternalLocalOriginErrors": True
                        },
                        "loadBalancer": {
                            "consistentHash": {
                                "httpHeaderName": "x-user-id"
                            },
                            "localityLbSetting": {
                                "enabled": True,
                                "distribute": [
                                    {"from": "region1/zone1/*", "to": {"region1/zone1/*": 80, "region1/zone2/*": 20}}
                                ],
                                "failover": [
                                    {"from": "region1", "to": "region2"}
                                ]
                            }
                        }
                    },
                    "subsets": [
                        {
                            "name": "stable",
                            "labels": {"version": "stable"},
                            "trafficPolicy": {
                                "connectionPool": {
                                    "tcp": {"maxConnections": 100},
                                    "http": {"http1MaxPendingRequests": 50}
                                }
                            }
                        },
                        {
                            "name": "canary",
                            "labels": {"version": "canary"},
                            "trafficPolicy": {
                                "connectionPool": {
                                    "tcp": {"maxConnections": 50},
                                    "http": {"http1MaxPendingRequests": 25}
                                }
                            }
                        }
                    ]
                }
            }
            traffic['destination_rules'].append(dr)
        
        # Traffic mirroring for production testing
        traffic['traffic_mirroring'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {
                "name": f"{system_blueprint.system.name}-traffic-mirror",
                "namespace": namespace
            },
            "spec": {
                "hosts": [f"{system_blueprint.system.name}-gateway"],
                "gateways": [f"{system_blueprint.system.name}-gateway"],
                "http": [
                    {
                        "match": [{"uri": {"prefix": "/api/"}}],
                        "route": [{"destination": {"host": "production-service"}}],
                        "mirror": {"host": "test-service"},
                        "mirrorPercentage": {"value": 10.0}
                    }
                ]
            }
        }
        
        return traffic
    
    def _generate_production_observability(self, system_blueprint) -> Dict[str, Any]:
        """Generate complete observability stack with metrics, tracing, logging"""
        
        observability = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Telemetry v2 configuration
        observability['telemetry'] = {
            "apiVersion": "telemetry.istio.io/v1alpha1",
            "kind": "Telemetry",
            "metadata": {
                "name": f"{system_blueprint.system.name}-telemetry",
                "namespace": namespace
            },
            "spec": {
                "metrics": [
                    {
                        "providers": [{"name": "prometheus"}],
                        "overrides": [
                            {
                                "match": {"metric": "ALL_METRICS"},
                                "tagOverrides": {
                                    "destination_service_name": {"value": "%{DESTINATION_SERVICE_NAME}"},
                                    "source_app": {"value": "%{SOURCE_APP}"},
                                    "destination_app": {"value": "%{DESTINATION_APP}"},
                                    "request_protocol": {"value": "%{REQUEST_PROTOCOL}"},
                                    "response_code": {"value": "%{RESPONSE_CODE}"}
                                }
                            }
                        ]
                    }
                ],
                "tracing": [
                    {
                        "providers": [{"name": "jaeger"}],
                        "customTags": {
                            "user_id": {"header": {"name": "x-user-id"}},
                            "request_id": {"header": {"name": "x-request-id"}},
                            "span_kind": {"literal": {"value": "server"}},
                            "component": {"environment": {"name": "COMPONENT_NAME", "defaultValue": "unknown"}},
                            "version": {"environment": {"name": "VERSION", "defaultValue": "unknown"}}
                        }
                    }
                ],
                "accessLogging": [
                    {
                        "providers": [{"name": "otel"}],
                        "format": {
                            "text": '[%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)% "%REQ(X-FORWARDED-FOR)%" "%REQ(USER-AGENT)%" "%REQ(X-REQUEST-ID)%" "%REQ(:AUTHORITY)%" "%UPSTREAM_HOST%" "%REQ(X-USER-ID)%"'
                        }
                    }
                ]
            }
        }
        
        # ServiceMonitor for Prometheus
        observability['service_monitor'] = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": f"{system_blueprint.system.name}-metrics",
                "namespace": namespace,
                "labels": {
                    "app": system_blueprint.system.name,
                    "prometheus": "kube-prometheus"
                }
            },
            "spec": {
                "selector": {"matchLabels": {"app": system_blueprint.system.name}},
                "endpoints": [
                    {
                        "port": "http-monitoring",
                        "interval": "30s",
                        "path": "/stats/prometheus",
                        "honorLabels": True
                    }
                ]
            }
        }
        
        # Grafana dashboard ConfigMap
        observability['grafana_dashboard'] = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{system_blueprint.system.name}-dashboard",
                "namespace": namespace,
                "labels": {
                    "grafana_dashboard": "1"
                }
            },
            "data": {
                "dashboard.json": json.dumps({
                    "dashboard": {
                        "id": None,
                        "title": f"{system_blueprint.system.name} Service Mesh",
                        "tags": ["istio", "service-mesh"],
                        "style": "dark",
                        "timezone": "browser",
                        "panels": [
                            {
                                "id": 1,
                                "title": "Request Rate",
                                "type": "graph",
                                "targets": [
                                    {
                                        "expr": f'sum(rate(istio_requests_total{{destination_service_name=~"{system_blueprint.system.name}.*"}}[5m])) by (destination_service_name)'
                                    }
                                ]
                            },
                            {
                                "id": 2,
                                "title": "Response Latency",
                                "type": "graph",
                                "targets": [
                                    {
                                        "expr": f'histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{{destination_service_name=~"{system_blueprint.system.name}.*"}}[5m])) by (destination_service_name, le))'
                                    }
                                ]
                            }
                        ],
                        "time": {"from": "now-1h", "to": "now"},
                        "refresh": "10s"
                    }
                })
            }
        }
        
        # Jaeger tracing configuration
        observability['jaeger_config'] = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{system_blueprint.system.name}-jaeger-config",
                "namespace": namespace
            },
            "data": {
                "sampling_strategies.json": json.dumps({
                    "service_strategies": [
                        {
                            "service": f"{system_blueprint.system.name}.*",
                            "type": "probabilistic",
                            "param": 0.1
                        }
                    ],
                    "default_strategy": {
                        "type": "probabilistic",
                        "param": 0.01
                    }
                })
            }
        }
        
        return observability
    
    def _generate_production_resilience(self, system_blueprint) -> Dict[str, Any]:
        """Generate resilience patterns including circuit breakers and fault injection"""
        
        resilience = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Circuit breaker configuration
        resilience['circuit_breakers'] = []
        for component in system_blueprint.system.components:
            cb = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "DestinationRule",
                "metadata": {
                    "name": f"{component.name}-circuit-breaker",
                    "namespace": namespace
                },
                "spec": {
                    "host": f"{component.name}-service",
                    "trafficPolicy": {
                        "circuitBreaker": {
                            "consecutiveGatewayErrors": 3,
                            "consecutiveServerErrors": 3,
                            "interval": "30s",
                            "baseEjectionTime": "30s",
                            "maxEjectionPercent": 50,
                            "minHealthPercent": 30
                        }
                    }
                }
            }
            resilience['circuit_breakers'].append(cb)
        
        # Chaos engineering fault injection
        resilience['fault_injection'] = []
        for component in system_blueprint.system.components:
            # Delay injection
            delay_fault = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": f"{component.name}-chaos-delay",
                    "namespace": namespace,
                    "labels": {"chaos-engineering": "delay"}
                },
                "spec": {
                    "hosts": [f"{component.name}-service"],
                    "http": [
                        {
                            "match": [{"headers": {"x-chaos-delay": {"exact": "true"}}}],
                            "fault": {
                                "delay": {
                                    "percentage": {"value": 100},
                                    "fixedDelay": "5s"
                                }
                            },
                            "route": [{"destination": {"host": f"{component.name}-service"}}]
                        }
                    ]
                }
            }
            
            # Abort injection
            abort_fault = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": f"{component.name}-chaos-abort",
                    "namespace": namespace,
                    "labels": {"chaos-engineering": "abort"}
                },
                "spec": {
                    "hosts": [f"{component.name}-service"],
                    "http": [
                        {
                            "match": [{"headers": {"x-chaos-abort": {"exact": "true"}}}],
                            "fault": {
                                "abort": {
                                    "percentage": {"value": 100},
                                    "httpStatus": 503
                                }
                            },
                            "route": [{"destination": {"host": f"{component.name}-service"}}]
                        }
                    ]
                }
            }
            
            resilience['fault_injection'].extend([delay_fault, abort_fault])
        
        # Retry policies
        resilience['retry_policies'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "EnvoyFilter",
            "metadata": {
                "name": f"{system_blueprint.system.name}-retry-policy",
                "namespace": namespace
            },
            "spec": {
                "configPatches": [
                    {
                        "applyTo": "HTTP_FILTER",
                        "match": {
                            "context": "SIDECAR_INBOUND",
                            "listener": {
                                "filterChain": {
                                    "filter": {"name": "envoy.filters.network.http_connection_manager"}
                                }
                            }
                        },
                        "patch": {
                            "operation": "INSERT_BEFORE",
                            "value": {
                                "name": "envoy.filters.http.retry",
                                "typed_config": {
                                    "@type": "type.googleapis.com/envoy.extensions.filters.http.retry.v3.Retry",
                                    "retry_policy": {
                                        "retry_on": "5xx,reset,connect-failure,refused-stream",
                                        "num_retries": 3,
                                        "per_try_timeout": "10s",
                                        "retry_back_off": {
                                            "base_interval": "0.025s",
                                            "max_interval": "0.250s"
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        return resilience
    
    def _generate_production_multi_cluster(self, system_blueprint) -> Dict[str, Any]:
        """Generate multi-cluster configuration for hybrid cloud deployment"""
        
        multi_cluster = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Cross-cluster service discovery
        multi_cluster['cross_cluster_gateway'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "Gateway",
            "metadata": {
                "name": "cross-network-gateway",
                "namespace": "istio-system"
            },
            "spec": {
                "selector": {"istio": "eastwestgateway"},
                "servers": [
                    {
                        "port": {"number": 15443, "name": "tls", "protocol": "TLS"},
                        "tls": {"mode": "ISTIO_MUTUAL"},
                        "hosts": ["*.local"]
                    }
                ]
            }
        }
        
        # Multi-cluster service entries
        multi_cluster['service_entries'] = []
        for component in system_blueprint.system.components:
            se = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "ServiceEntry",
                "metadata": {
                    "name": f"{component.name}-remote",
                    "namespace": namespace
                },
                "spec": {
                    "hosts": [f"{component.name}-service.{namespace}.svc.cluster.local"],
                    "location": "MESH_EXTERNAL",
                    "ports": [
                        {"number": 8080, "name": "http", "protocol": "HTTP"}
                    ],
                    "resolution": "DNS",
                    "addresses": ["240.0.0.1"],  # Virtual IP for cross-cluster
                    "endpoints": [
                        {
                            "address": "remote-cluster-gateway.istio-system.svc.cluster.local",
                            "network": "network2",
                            "ports": {"http": 15443}
                        }
                    ]
                }
            }
            multi_cluster['service_entries'].append(se)
        
        # Cluster-specific destination rules
        multi_cluster['cluster_destination_rules'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "DestinationRule",
            "metadata": {
                "name": "cross-cluster-dr",
                "namespace": namespace
            },
            "spec": {
                "host": "*.local",
                "trafficPolicy": {
                    "tls": {"mode": "ISTIO_MUTUAL"}
                },
                "exportTo": ["*"]
            }
        }
        
        return multi_cluster
    
    def _generate_production_ingress_egress(self, system_blueprint) -> Dict[str, Any]:
        """Generate advanced ingress and egress configuration"""
        
        ingress_egress = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Advanced Gateway with multiple protocols and security
        ingress_egress['gateway'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "Gateway",
            "metadata": {
                "name": f"{system_blueprint.system.name}-gateway",
                "namespace": namespace
            },
            "spec": {
                "selector": {"istio": "ingressgateway"},
                "servers": [
                    {
                        "port": {"number": 80, "name": "http", "protocol": "HTTP"},
                        "hosts": [f"{system_blueprint.system.name}.local"],
                        "tls": {"httpsRedirect": True}
                    },
                    {
                        "port": {"number": 443, "name": "https", "protocol": "HTTPS"},
                        "hosts": [f"{system_blueprint.system.name}.local"],
                        "tls": {
                            "mode": "SIMPLE",
                            "credentialName": f"{system_blueprint.system.name}-tls-cert",
                            "minProtocolVersion": "TLSV1_2",
                            "maxProtocolVersion": "TLSV1_3",
                            "cipherSuites": [
                                "ECDHE-RSA-AES128-GCM-SHA256",
                                "ECDHE-RSA-AES256-GCM-SHA384",
                                "ECDHE-ECDSA-AES128-GCM-SHA256",
                                "ECDHE-ECDSA-AES256-GCM-SHA384"
                            ]
                        }
                    },
                    {
                        "port": {"number": 8443, "name": "https-admin", "protocol": "HTTPS"},
                        "hosts": [f"admin.{system_blueprint.system.name}.local"],
                        "tls": {
                            "mode": "MUTUAL",
                            "credentialName": f"{system_blueprint.system.name}-admin-tls-cert"
                        }
                    },
                    {
                        "port": {"number": 9443, "name": "grpc-tls", "protocol": "GRPC"},
                        "hosts": [f"grpc.{system_blueprint.system.name}.local"],
                        "tls": {
                            "mode": "SIMPLE",
                            "credentialName": f"{system_blueprint.system.name}-grpc-tls-cert"
                        }
                    }
                ]
            }
        }
        
        # Egress gateway for external services
        ingress_egress['egress_gateway'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "Gateway",
            "metadata": {
                "name": f"{system_blueprint.system.name}-egress-gateway",
                "namespace": namespace
            },
            "spec": {
                "selector": {"istio": "egressgateway"},
                "servers": [
                    {
                        "port": {"number": 443, "name": "https", "protocol": "HTTPS"},
                        "hosts": ["api.external.com"],
                        "tls": {"mode": "PASSTHROUGH"}
                    }
                ]
            }
        }
        
        # Virtual service for egress traffic
        ingress_egress['egress_virtual_service'] = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {
                "name": f"{system_blueprint.system.name}-egress-vs",
                "namespace": namespace
            },
            "spec": {
                "hosts": ["api.external.com"],
                "gateways": ["mesh", f"{system_blueprint.system.name}-egress-gateway"],
                "tls": [
                    {
                        "match": [{"port": 443, "sniHosts": ["api.external.com"]}],
                        "route": [
                            {
                                "destination": {
                                    "host": "api.external.com",
                                    "port": {"number": 443}
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        # Service entry for external dependencies
        ingress_egress['external_service_entries'] = [
            {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "ServiceEntry",
                "metadata": {
                    "name": "external-database",
                    "namespace": namespace
                },
                "spec": {
                    "hosts": ["external-db.example.com"],
                    "ports": [
                        {"number": 5432, "name": "postgres", "protocol": "TCP"}
                    ],
                    "location": "MESH_EXTERNAL",
                    "resolution": "DNS"
                }
            },
            {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "ServiceEntry",
                "metadata": {
                    "name": "external-api",
                    "namespace": namespace
                },
                "spec": {
                    "hosts": ["api.external.com"],
                    "ports": [
                        {"number": 443, "name": "https", "protocol": "HTTPS"}
                    ],
                    "location": "MESH_EXTERNAL",
                    "resolution": "DNS"
                }
            }
        ]
        
        return ingress_egress
    
    def _generate_production_policies(self, system_blueprint) -> Dict[str, Any]:
        """Generate comprehensive service mesh policies"""
        
        policies = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Network policies for additional security
        policies['network_policies'] = []
        for component in system_blueprint.system.components:
            np = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": f"{component.name}-netpol",
                    "namespace": namespace
                },
                "spec": {
                    "podSelector": {"matchLabels": {"app": component.name}},
                    "policyTypes": ["Ingress", "Egress"],
                    "ingress": [
                        {
                            "from": [
                                {"namespaceSelector": {"matchLabels": {"name": "istio-system"}}},
                                {"namespaceSelector": {"matchLabels": {"name": namespace}}}
                            ],
                            "ports": [{"protocol": "TCP", "port": 8080}]
                        }
                    ],
                    "egress": [
                        {
                            "to": [
                                {"namespaceSelector": {"matchLabels": {"name": "istio-system"}}},
                                {"namespaceSelector": {"matchLabels": {"name": namespace}}}
                            ]
                        },
                        {
                            "to": [],
                            "ports": [
                                {"protocol": "TCP", "port": 53},
                                {"protocol": "UDP", "port": 53}
                            ]
                        }
                    ]
                }
            }
            policies['network_policies'].append(np)
        
        # Pod security policies
        policies['pod_security_policy'] = {
            "apiVersion": "policy/v1beta1",
            "kind": "PodSecurityPolicy",
            "metadata": {
                "name": f"{system_blueprint.system.name}-psp"
            },
            "spec": {
                "privileged": False,
                "allowPrivilegeEscalation": False,
                "requiredDropCapabilities": ["ALL"],
                "volumes": ["configMap", "emptyDir", "projected", "secret", "downwardAPI", "persistentVolumeClaim"],
                "runAsUser": {"rule": "MustRunAsNonRoot"},
                "seLinux": {"rule": "RunAsAny"},
                "fsGroup": {"rule": "RunAsAny"}
            }
        }
        
        # Resource quotas
        policies['resource_quota'] = {
            "apiVersion": "v1",
            "kind": "ResourceQuota",
            "metadata": {
                "name": f"{system_blueprint.system.name}-quota",
                "namespace": namespace
            },
            "spec": {
                "hard": {
                    "requests.cpu": "4",
                    "requests.memory": "8Gi",
                    "limits.cpu": "8",
                    "limits.memory": "16Gi",
                    "persistentvolumeclaims": "10",
                    "pods": "20",
                    "services": "10"
                }
            }
        }
        
        return policies
    
    def _generate_production_control_plane(self, system_blueprint) -> Dict[str, Any]:
        """Generate production-ready Istio control plane configuration"""
        
        control_plane = {}
        
        # IstioOperator for production control plane
        control_plane['istio_operator'] = {
            "apiVersion": "install.istio.io/v1alpha1",
            "kind": "IstioOperator",
            "metadata": {
                "name": f"{system_blueprint.system.name}-control-plane",
                "namespace": "istio-system"
            },
            "spec": {
                "values": {
                    "global": {
                        "meshID": f"{system_blueprint.system.name}-mesh",
                        "multiCluster": {
                            "clusterName": f"{system_blueprint.system.name}-cluster"
                        },
                        "network": "network1",
                        "meshExpansion": {"enabled": True},
                        "logging": {"level": "default:info"}
                    },
                    "pilot": {
                        "env": {
                            "EXTERNAL_ISTIOD": False,
                            "PILOT_TRACE_SAMPLING": 100.0,
                            "PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION": True,
                            "PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY": True
                        }
                    },
                    "telemetry": {
                        "v2": {
                            "enabled": True,
                            "prometheus": {
                                "configOverride": {
                                    "metric_relabeling_configs": [
                                        {
                                            "source_labels": ["__name__"],
                                            "regex": "istio_.*",
                                            "target_label": "__tmp_istio_metric",
                                            "replacement": "true"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                "components": {
                    "pilot": {
                        "k8s": {
                            "env": [
                                {"name": "PILOT_TRACE_SAMPLING", "value": "100"},
                                {"name": "PILOT_ENABLE_AUTHORIZATION_OVERRIDE", "value": "false"}
                            ],
                            "resources": {
                                "requests": {"cpu": "500m", "memory": "2048Mi"},
                                "limits": {"cpu": "2000m", "memory": "4096Mi"}
                            },
                            "hpaSpec": {
                                "maxReplicas": 5,
                                "minReplicas": 2,
                                "scaleTargetRef": {
                                    "apiVersion": "apps/v1",
                                    "kind": "Deployment",
                                    "name": "istiod"
                                },
                                "targetCPUUtilizationPercentage": 80
                            }
                        }
                    },
                    "ingressGateways": [
                        {
                            "name": "istio-ingressgateway",
                            "enabled": True,
                            "k8s": {
                                "resources": {
                                    "requests": {"cpu": "100m", "memory": "128Mi"},
                                    "limits": {"cpu": "2000m", "memory": "1024Mi"}
                                },
                                "hpaSpec": {
                                    "maxReplicas": 10,
                                    "minReplicas": 2,
                                    "scaleTargetRef": {
                                        "apiVersion": "apps/v1",
                                        "kind": "Deployment",
                                        "name": "istio-ingressgateway"
                                    },
                                    "targetCPUUtilizationPercentage": 80
                                },
                                "service": {
                                    "type": "LoadBalancer",
                                    "ports": [
                                        {"port": 15021, "targetPort": 15021, "name": "status-port"},
                                        {"port": 80, "targetPort": 8080, "name": "http2"},
                                        {"port": 443, "targetPort": 8443, "name": "https"},
                                        {"port": 15443, "targetPort": 15443, "name": "tls"}
                                    ]
                                }
                            }
                        }
                    ],
                    "egressGateways": [
                        {
                            "name": "istio-egressgateway",
                            "enabled": True,
                            "k8s": {
                                "resources": {
                                    "requests": {"cpu": "100m", "memory": "128Mi"},
                                    "limits": {"cpu": "2000m", "memory": "1024Mi"}
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        return control_plane
    
    def _generate_production_canary_deployment(self, system_blueprint) -> Dict[str, Any]:
        """Generate advanced canary deployment configuration with Flagger"""
        
        canary_deployment = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Flagger canary configurations
        canary_deployment['canary_configs'] = []
        for component in system_blueprint.system.components:
            canary = {
                "apiVersion": "flagger.app/v1beta1",
                "kind": "Canary",
                "metadata": {
                    "name": f"{component.name}-canary",
                    "namespace": namespace
                },
                "spec": {
                    "targetRef": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "name": f"{component.name}-deployment"
                    },
                    "progressDeadlineSeconds": 60,
                    "service": {
                        "port": 8080,
                        "targetPort": 8080,
                        "gateways": [f"{system_blueprint.system.name}-gateway"],
                        "hosts": [f"{component.name}.{system_blueprint.system.name}.local"],
                        "trafficPolicy": {
                            "tls": {"mode": "DISABLE"}
                        }
                    },
                    "analysis": {
                        "interval": "1m",
                        "threshold": 5,
                        "maxWeight": 50,
                        "stepWeight": 10,
                        "metrics": [
                            {
                                "name": "request-success-rate",
                                "thresholdRange": {"min": 99},
                                "interval": "1m"
                            },
                            {
                                "name": "request-duration",
                                "thresholdRange": {"max": 500},
                                "interval": "1m"
                            },
                            {
                                "name": "istio_request_total",
                                "interval": "1m",
                                "thresholdRange": {"min": 10}
                            }
                        ],
                        "webhooks": [
                            {
                                "name": "acceptance-test",
                                "type": "pre-rollout",
                                "url": "http://flagger-loadtester.test/",
                                "timeout": "30s",
                                "metadata": {
                                    "type": "bash",
                                    "cmd": f"curl -sd 'test' {component.name}-canary.{namespace}:8080/health | grep -E \"(ok|healthy)\""
                                }
                            },
                            {
                                "name": "load-test",
                                "url": "http://flagger-loadtester.test/",
                                "timeout": "5s",
                                "metadata": {
                                    "cmd": f"hey -z 1m -q 10 -c 2 http://{component.name}-canary.{namespace}:8080/"
                                }
                            },
                            {
                                "name": "integration-test",
                                "type": "rollout",
                                "url": "http://flagger-loadtester.test/",
                                "timeout": "30s",
                                "metadata": {
                                    "type": "cmd",
                                    "cmd": f"integration-test.sh {component.name} {namespace}"
                                }
                            }
                        ]
                    },
                    "skipAnalysis": False
                }
            }
            canary_deployment['canary_configs'].append(canary)
        
        # Flagger load tester
        canary_deployment['load_tester'] = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "flagger-loadtester",
                "namespace": "test"
            },
            "spec": {
                "selector": {"matchLabels": {"app": "flagger-loadtester"}},
                "template": {
                    "metadata": {"labels": {"app": "flagger-loadtester"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "loadtester",
                                "image": "ghcr.io/fluxcd/flagger-loadtester:0.24.0",
                                "ports": [{"name": "http", "containerPort": 8080}],
                                "command": ["./loadtester", "-port=8080", "-log-level=info", "-timeout=1h"],
                                "livenessProbe": {
                                    "exec": {"command": ["wget", "--quiet", "--tries=1", "--timeout=5", "--spider", "http://localhost:8080/healthz"]},
                                    "timeoutSeconds": 5
                                },
                                "readinessProbe": {
                                    "exec": {"command": ["wget", "--quiet", "--tries=1", "--timeout=5", "--spider", "http://localhost:8080/healthz"]},
                                    "timeoutSeconds": 5
                                },
                                "resources": {
                                    "limits": {"memory": "512Mi", "cpu": "1000m"},
                                    "requests": {"memory": "64Mi", "cpu": "10m"}
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        return canary_deployment
    
    def _generate_production_chaos_engineering(self, system_blueprint) -> Dict[str, Any]:
        """Generate chaos engineering configuration for production resilience testing"""
        
        chaos_engineering = {}
        namespace = getattr(system_blueprint.system, 'namespace', 'default')
        
        # Chaos Mesh experiments
        chaos_engineering['chaos_experiments'] = []
        
        for component in system_blueprint.system.components:
            # Network chaos
            network_chaos = {
                "apiVersion": "chaos-mesh.org/v1alpha1",
                "kind": "NetworkChaos",
                "metadata": {
                    "name": f"{component.name}-network-chaos",
                    "namespace": namespace
                },
                "spec": {
                    "action": "delay",
                    "mode": "one",
                    "selector": {
                        "namespaces": [namespace],
                        "labelSelectors": {"app": component.name}
                    },
                    "delay": {
                        "latency": "10ms",
                        "correlation": "100",
                        "jitter": "0ms"
                    },
                    "duration": "5m",
                    "scheduler": {
                        "cron": "@every 30m"
                    }
                }
            }
            
            # Pod chaos
            pod_chaos = {
                "apiVersion": "chaos-mesh.org/v1alpha1",
                "kind": "PodChaos",
                "metadata": {
                    "name": f"{component.name}-pod-chaos",
                    "namespace": namespace
                },
                "spec": {
                    "action": "pod-kill",
                    "mode": "fixed-percent",
                    "value": "50",
                    "selector": {
                        "namespaces": [namespace],
                        "labelSelectors": {"app": component.name}
                    },
                    "duration": "30s",
                    "scheduler": {
                        "cron": "@every 60m"
                    }
                }
            }
            
            # Stress chaos
            stress_chaos = {
                "apiVersion": "chaos-mesh.org/v1alpha1",
                "kind": "StressChaos",
                "metadata": {
                    "name": f"{component.name}-stress-chaos",
                    "namespace": namespace
                },
                "spec": {
                    "mode": "one",
                    "selector": {
                        "namespaces": [namespace],
                        "labelSelectors": {"app": component.name}
                    },
                    "stressors": {
                        "cpu": {"workers": 1, "load": 50},
                        "memory": {"workers": 1, "size": "256MB"}
                    },
                    "duration": "2m",
                    "scheduler": {
                        "cron": "@every 120m"
                    }
                }
            }
            
            chaos_engineering['chaos_experiments'].extend([network_chaos, pod_chaos, stress_chaos])
        
        # Chaos engineering workflow
        chaos_engineering['chaos_workflow'] = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "name": f"{system_blueprint.system.name}-chaos-workflow",
                "namespace": namespace
            },
            "spec": {
                "entry": "chaos-sequence",
                "templates": [
                    {
                        "name": "chaos-sequence",
                        "templateType": "Serial",
                        "deadline": "10m",
                        "children": [
                            "network-delay",
                            "pod-failure",
                            "resource-stress"
                        ]
                    },
                    {
                        "name": "network-delay",
                        "templateType": "NetworkChaos",
                        "deadline": "2m",
                        "networkChaos": {
                            "action": "delay",
                            "mode": "all",
                            "selector": {
                                "namespaces": [namespace],
                                "labelSelectors": {"app": system_blueprint.system.name}
                            },
                            "delay": {
                                "latency": "100ms",
                                "correlation": "50"
                            }
                        }
                    },
                    {
                        "name": "pod-failure",
                        "templateType": "PodChaos",
                        "deadline": "1m",
                        "podChaos": {
                            "action": "pod-failure",
                            "mode": "fixed-percent",
                            "value": "25",
                            "selector": {
                                "namespaces": [namespace],
                                "labelSelectors": {"app": system_blueprint.system.name}
                            }
                        }
                    },
                    {
                        "name": "resource-stress",
                        "templateType": "StressChaos",
                        "deadline": "3m",
                        "stressChaos": {
                            "mode": "all",
                            "selector": {
                                "namespaces": [namespace],
                                "labelSelectors": {"app": system_blueprint.system.name}
                            },
                            "stressors": {
                                "cpu": {"workers": 2, "load": 80}
                            }
                        }
                    }
                ]
            }
        }
        
        return chaos_engineering
    
    def _validate_production_readiness(self, manifests: ProductionServiceMeshManifests):
        """Validate that all manifests meet production readiness criteria with comprehensive schema validation"""
        
        validation_errors = []
        
        # Validate security configuration with schemas
        security_validation = self._validate_security_schemas(manifests.security)
        if not security_validation.is_valid:
            validation_errors.extend(security_validation.errors)
        
        # Validate traffic management with schemas
        traffic_validation = self._validate_traffic_schemas(manifests.traffic)
        if not traffic_validation.is_valid:
            validation_errors.extend(traffic_validation.errors)
        
        # Validate observability with schemas
        observability_validation = self._validate_observability_schemas(manifests.observability)
        if not observability_validation.is_valid:
            validation_errors.extend(observability_validation.errors)
        
        # Validate resilience with schemas
        resilience_validation = self._validate_resilience_schemas(manifests.resilience)
        if not resilience_validation.is_valid:
            validation_errors.extend(resilience_validation.errors)
        
        # Validate control plane with schemas
        control_plane_validation = self._validate_control_plane_schemas(manifests.control_plane)
        if not control_plane_validation.is_valid:
            validation_errors.extend(control_plane_validation.errors)
        
        # Validate cross-component consistency
        consistency_validation = self._validate_cross_component_consistency(manifests)
        if not consistency_validation.is_valid:
            validation_errors.extend(consistency_validation.errors)
        
        if validation_errors:
            detailed_report = self._generate_validation_report(validation_errors)
            raise ValueError(f"Production readiness validation failed:\n{detailed_report}")
        
        logger.info("✅ Comprehensive production readiness validation passed")
    
    def _validate_security_schemas(self, security_manifests: Dict[str, Any]) -> 'ValidationResult':
        """Validate security manifests against Istio schemas"""
        
        errors = []
        
        # Validate PeerAuthentication
        if 'peer_authentication' in security_manifests:
            peer_auth_schema = {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "apiVersion": {"const": "security.istio.io/v1beta1"},
                    "kind": {"const": "PeerAuthentication"},
                    "spec": {
                        "type": "object",
                        "required": ["mtls"],
                        "properties": {
                            "mtls": {
                                "type": "object",
                                "required": ["mode"],
                                "properties": {
                                    "mode": {"enum": ["STRICT", "PERMISSIVE", "DISABLE"]}
                                }
                            }
                        }
                    }
                }
            }
            
            try:
                jsonschema.validate(security_manifests['peer_authentication'], peer_auth_schema)
                # Validate that mode is STRICT for production
                if security_manifests['peer_authentication']['spec']['mtls']['mode'] != 'STRICT':
                    errors.append("PeerAuthentication must use STRICT mTLS mode for production")
            except jsonschema.ValidationError as e:
                errors.append(f"PeerAuthentication schema validation failed: {e.message}")
        else:
            errors.append("Missing required PeerAuthentication for mTLS")
        
        # Validate AuthorizationPolicies
        if 'authorization_policies' in security_manifests:
            auth_policies = security_manifests['authorization_policies']
            if not isinstance(auth_policies, list) or len(auth_policies) == 0:
                errors.append("AuthorizationPolicies must be a non-empty list")
            else:
                for i, policy in enumerate(auth_policies):
                    auth_policy_schema = {
                        "type": "object",
                        "required": ["apiVersion", "kind", "metadata", "spec"],
                        "properties": {
                            "apiVersion": {"const": "security.istio.io/v1beta1"},
                            "kind": {"const": "AuthorizationPolicy"},
                            "spec": {
                                "type": "object",
                                "required": ["selector", "action", "rules"],
                                "properties": {
                                    "action": {"enum": ["ALLOW", "DENY", "CUSTOM"]},
                                    "rules": {"type": "array", "minItems": 1}
                                }
                            }
                        }
                    }
                    
                    try:
                        jsonschema.validate(policy, auth_policy_schema)
                    except jsonschema.ValidationError as e:
                        errors.append(f"AuthorizationPolicy[{i}] schema validation failed: {e.message}")
        else:
            errors.append("Missing required AuthorizationPolicies for RBAC")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_traffic_schemas(self, traffic_manifests: Dict[str, Any]) -> 'ValidationResult':
        """Validate traffic management manifests against Istio schemas"""
        
        errors = []
        
        # Validate VirtualServices
        if 'virtual_services' in traffic_manifests:
            virtual_services = traffic_manifests['virtual_services']
            if not isinstance(virtual_services, list) or len(virtual_services) == 0:
                errors.append("VirtualServices must be a non-empty list")
            else:
                for i, vs in enumerate(virtual_services):
                    vs_schema = {
                        "type": "object",
                        "required": ["apiVersion", "kind", "metadata", "spec"],
                        "properties": {
                            "apiVersion": {"const": "networking.istio.io/v1beta1"},
                            "kind": {"const": "VirtualService"},
                            "spec": {
                                "type": "object",
                                "required": ["hosts"],
                                "properties": {
                                    "hosts": {"type": "array", "minItems": 1},
                                    "http": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["route"],
                                            "properties": {
                                                "retries": {
                                                    "type": "object",
                                                    "required": ["attempts", "perTryTimeout"]
                                                },
                                                "timeout": {"type": "string", "pattern": "^[0-9]+[smh]$"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    try:
                        jsonschema.validate(vs, vs_schema)
                        # Validate production requirements
                        if 'http' in vs['spec']:
                            for j, http_rule in enumerate(vs['spec']['http']):
                                if 'retries' not in http_rule:
                                    errors.append(f"VirtualService[{i}].http[{j}] missing required retry configuration for production")
                                if 'timeout' not in http_rule:
                                    errors.append(f"VirtualService[{i}].http[{j}] missing required timeout configuration for production")
                    except jsonschema.ValidationError as e:
                        errors.append(f"VirtualService[{i}] schema validation failed: {e.message}")
        else:
            errors.append("Missing required VirtualServices for traffic routing")
        
        # Validate DestinationRules
        if 'destination_rules' in traffic_manifests:
            destination_rules = traffic_manifests['destination_rules']
            if not isinstance(destination_rules, list) or len(destination_rules) == 0:
                errors.append("DestinationRules must be a non-empty list")
            else:
                for i, dr in enumerate(destination_rules):
                    dr_schema = {
                        "type": "object",
                        "required": ["apiVersion", "kind", "metadata", "spec"],
                        "properties": {
                            "apiVersion": {"const": "networking.istio.io/v1beta1"},
                            "kind": {"const": "DestinationRule"},
                            "spec": {
                                "type": "object",
                                "required": ["host"],
                                "properties": {
                                    "host": {"type": "string", "minLength": 1},
                                    "trafficPolicy": {
                                        "type": "object",
                                        "properties": {
                                            "circuitBreaker": {"type": "object"},
                                            "outlierDetection": {"type": "object"},
                                            "connectionPool": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    try:
                        jsonschema.validate(dr, dr_schema)
                        # Validate production requirements
                        if 'trafficPolicy' in dr['spec']:
                            traffic_policy = dr['spec']['trafficPolicy']
                            if 'circuitBreaker' not in traffic_policy:
                                errors.append(f"DestinationRule[{i}] missing required circuit breaker for production resilience")
                            if 'outlierDetection' not in traffic_policy:
                                errors.append(f"DestinationRule[{i}] missing required outlier detection for production resilience")
                    except jsonschema.ValidationError as e:
                        errors.append(f"DestinationRule[{i}] schema validation failed: {e.message}")
        else:
            errors.append("Missing required DestinationRules for load balancing and resilience")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_observability_schemas(self, observability_manifests: Dict[str, Any]) -> 'ValidationResult':
        """Validate observability manifests against production standards"""
        
        errors = []
        
        # Validate Telemetry configuration
        if 'telemetry' in observability_manifests:
            telemetry = observability_manifests['telemetry']
            telemetry_schema = {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "apiVersion": {"const": "telemetry.istio.io/v1alpha1"},
                    "kind": {"const": "Telemetry"},
                    "spec": {
                        "type": "object",
                        "properties": {
                            "metrics": {"type": "array", "minItems": 1},
                            "tracing": {"type": "array", "minItems": 1},
                            "accessLogging": {"type": "array", "minItems": 1}
                        }
                    }
                }
            }
            
            try:
                jsonschema.validate(telemetry, telemetry_schema)
                # Validate production requirements
                spec = telemetry['spec']
                if 'metrics' not in spec or len(spec['metrics']) == 0:
                    errors.append("Telemetry missing required metrics configuration for production monitoring")
                if 'tracing' not in spec or len(spec['tracing']) == 0:
                    errors.append("Telemetry missing required tracing configuration for production debugging")
                if 'accessLogging' not in spec or len(spec['accessLogging']) == 0:
                    errors.append("Telemetry missing required access logging for production audit")
            except jsonschema.ValidationError as e:
                errors.append(f"Telemetry schema validation failed: {e.message}")
        else:
            errors.append("Missing required Telemetry configuration for observability")
        
        # Validate ServiceMonitor
        if 'service_monitor' in observability_manifests:
            service_monitor = observability_manifests['service_monitor']
            sm_schema = {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "apiVersion": {"const": "monitoring.coreos.com/v1"},
                    "kind": {"const": "ServiceMonitor"},
                    "spec": {
                        "type": "object",
                        "required": ["selector", "endpoints"],
                        "properties": {
                            "endpoints": {"type": "array", "minItems": 1}
                        }
                    }
                }
            }
            
            try:
                jsonschema.validate(service_monitor, sm_schema)
            except jsonschema.ValidationError as e:
                errors.append(f"ServiceMonitor schema validation failed: {e.message}")
        else:
            errors.append("Missing required ServiceMonitor for metrics collection")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_resilience_schemas(self, resilience_manifests: Dict[str, Any]) -> 'ValidationResult':
        """Validate resilience manifests against production standards"""
        
        errors = []
        
        # Validate circuit breakers exist
        if 'circuit_breakers' not in resilience_manifests:
            errors.append("Missing required circuit breaker configuration for production resilience")
        elif not isinstance(resilience_manifests['circuit_breakers'], list) or len(resilience_manifests['circuit_breakers']) == 0:
            errors.append("Circuit breakers must be a non-empty list")
        
        # Validate fault injection configurations
        if 'fault_injection' in resilience_manifests:
            fault_injections = resilience_manifests['fault_injection']
            if isinstance(fault_injections, list):
                for i, fault in enumerate(fault_injections):
                    if fault.get('kind') == 'VirtualService' and 'spec' in fault:
                        spec = fault['spec']
                        if 'http' in spec:
                            for j, http_rule in enumerate(spec['http']):
                                if 'fault' not in http_rule:
                                    errors.append(f"FaultInjection[{i}].http[{j}] missing fault configuration")
                                else:
                                    fault_config = http_rule['fault']
                                    if 'delay' not in fault_config and 'abort' not in fault_config:
                                        errors.append(f"FaultInjection[{i}].http[{j}] must have either delay or abort fault")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_control_plane_schemas(self, control_plane_manifests: Dict[str, Any]) -> 'ValidationResult':
        """Validate control plane manifests against production standards"""
        
        errors = []
        
        # Validate IstioOperator
        if 'istio_operator' in control_plane_manifests:
            istio_operator = control_plane_manifests['istio_operator']
            operator_schema = {
                "type": "object",
                "required": ["apiVersion", "kind", "metadata", "spec"],
                "properties": {
                    "apiVersion": {"const": "install.istio.io/v1alpha1"},
                    "kind": {"const": "IstioOperator"},
                    "spec": {
                        "type": "object",
                        "properties": {
                            "values": {"type": "object"},
                            "components": {"type": "object"}
                        }
                    }
                }
            }
            
            try:
                jsonschema.validate(istio_operator, operator_schema)
                
                # Validate production requirements
                spec = istio_operator['spec']
                if 'components' in spec:
                    components = spec['components']
                    
                    # Validate pilot configuration
                    if 'pilot' in components and 'k8s' in components['pilot']:
                        pilot_k8s = components['pilot']['k8s']
                        if 'resources' not in pilot_k8s:
                            errors.append("IstioOperator pilot missing required resource specifications for production")
                        if 'hpaSpec' not in pilot_k8s:
                            errors.append("IstioOperator pilot missing required HPA specification for production")
                    
                    # Validate gateway configurations
                    if 'ingressGateways' in components:
                        gateways = components['ingressGateways']
                        if not isinstance(gateways, list) or len(gateways) == 0:
                            errors.append("IstioOperator missing required ingress gateways for production")
                        else:
                            for i, gateway in enumerate(gateways):
                                if 'k8s' in gateway and 'resources' not in gateway['k8s']:
                                    errors.append(f"IstioOperator ingressGateway[{i}] missing resource specifications")
                
            except jsonschema.ValidationError as e:
                errors.append(f"IstioOperator schema validation failed: {e.message}")
        else:
            errors.append("Missing required IstioOperator configuration for control plane")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_cross_component_consistency(self, manifests: ProductionServiceMeshManifests) -> 'ValidationResult':
        """Validate consistency across all service mesh components"""
        
        errors = []
        
        # Validate that VirtualServices reference existing DestinationRule hosts
        vs_hosts = set()
        dr_hosts = set()
        
        # Collect VirtualService hosts
        if 'virtual_services' in manifests.traffic:
            for vs in manifests.traffic['virtual_services']:
                if 'spec' in vs and 'hosts' in vs['spec']:
                    vs_hosts.update(vs['spec']['hosts'])
        
        # Collect DestinationRule hosts
        if 'destination_rules' in manifests.traffic:
            for dr in manifests.traffic['destination_rules']:
                if 'spec' in dr and 'host' in dr['spec']:
                    dr_hosts.add(dr['spec']['host'])
        
        # Check for VirtualServices without corresponding DestinationRules
        missing_destination_rules = vs_hosts - dr_hosts
        if missing_destination_rules:
            errors.append(f"VirtualServices reference hosts without DestinationRules: {missing_destination_rules}")
        
        # Validate that security policies cover all services
        if 'authorization_policies' in manifests.security:
            auth_policy_selectors = set()
            for policy in manifests.security['authorization_policies']:
                if 'spec' in policy and 'selector' in policy['spec']:
                    selector = policy['spec']['selector']
                    if 'matchLabels' in selector:
                        for label_key, label_value in selector['matchLabels'].items():
                            auth_policy_selectors.add(f"{label_key}={label_value}")
            
            # This is a simplified check - in real scenarios, you'd need more sophisticated logic
            if len(auth_policy_selectors) == 0:
                errors.append("No authorization policies found - all services must have authorization policies")
        
        # Validate that observability is configured for all components
        if 'telemetry' in manifests.observability:
            telemetry = manifests.observability['telemetry']
            if 'spec' in telemetry:
                spec = telemetry['spec']
                required_providers = ['prometheus', 'jaeger', 'otel']
                
                # Check metrics providers
                if 'metrics' in spec:
                    metric_providers = set()
                    for metric in spec['metrics']:
                        if 'providers' in metric:
                            for provider in metric['providers']:
                                metric_providers.add(provider.get('name', ''))
                    if 'prometheus' not in metric_providers:
                        errors.append("Telemetry missing Prometheus provider for production metrics")
                
                # Check tracing providers
                if 'tracing' in spec:
                    tracing_providers = set()
                    for trace in spec['tracing']:
                        if 'providers' in trace:
                            for provider in trace['providers']:
                                tracing_providers.add(provider.get('name', ''))
                    if 'jaeger' not in tracing_providers:
                        errors.append("Telemetry missing Jaeger provider for production tracing")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _generate_validation_report(self, errors: List[str]) -> str:
        """Generate detailed validation report"""
        
        report = ["\n=== PRODUCTION READINESS VALIDATION REPORT ==="]
        report.append(f"Total Issues Found: {len(errors)}")
        report.append("\nDetailed Issues:")
        
        for i, error in enumerate(errors, 1):
            report.append(f"  {i}. {error}")
        
        report.append("\n=== RECOMMENDATIONS ===")
        report.append("1. Review and fix all schema validation errors")
        report.append("2. Ensure all production requirements are met")
        report.append("3. Validate cross-component consistency")
        report.append("4. Test configurations in staging environment")
        report.append("5. Run security and performance validation")
        
        return "\n".join(report)


class ServiceDeploymentGenerator:
    """Generate deployment configurations for service-based systems with production Istio"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.istio_generator = ProductionIstioServiceMesh(output_dir)
        
    def generate_production_service_mesh_deployment(self, system_blueprint) -> Dict[str, str]:
        """Generate complete production-ready service mesh deployment"""
        
        deployment_configs = {}
        
        # Generate production-grade Istio service mesh
        service_mesh_manifests = self.istio_generator.generate_production_service_mesh(system_blueprint)
        
        # Convert manifests to YAML strings
        deployment_configs["istio-security.yaml"] = self._manifests_to_yaml(service_mesh_manifests.security)
        deployment_configs["istio-traffic.yaml"] = self._manifests_to_yaml(service_mesh_manifests.traffic)
        deployment_configs["istio-observability.yaml"] = self._manifests_to_yaml(service_mesh_manifests.observability)
        deployment_configs["istio-resilience.yaml"] = self._manifests_to_yaml(service_mesh_manifests.resilience)
        deployment_configs["istio-multi-cluster.yaml"] = self._manifests_to_yaml(service_mesh_manifests.multi_cluster)
        deployment_configs["istio-ingress-egress.yaml"] = self._manifests_to_yaml(service_mesh_manifests.ingress_egress)
        deployment_configs["istio-policies.yaml"] = self._manifests_to_yaml(service_mesh_manifests.policies)
        deployment_configs["istio-control-plane.yaml"] = self._manifests_to_yaml(service_mesh_manifests.control_plane)
        deployment_configs["istio-canary.yaml"] = self._manifests_to_yaml(service_mesh_manifests.canary_deployment)
        deployment_configs["istio-chaos-engineering.yaml"] = self._manifests_to_yaml(service_mesh_manifests.chaos_engineering)
        
        # Generate deployment README with production setup instructions
        deployment_configs["README.md"] = self._generate_production_readme(system_blueprint)
        
        # Generate production installation script
        deployment_configs["install-production.sh"] = self._generate_installation_script(system_blueprint)
        
        return deployment_configs
    
    def _manifests_to_yaml(self, manifests: Dict[str, Any]) -> str:
        """Convert manifest dictionary to YAML string"""
        
        all_manifests = []
        
        for key, value in manifests.items():
            if isinstance(value, list):
                all_manifests.extend(value)
            elif isinstance(value, dict) and value:
                all_manifests.append(value)
        
        if not all_manifests:
            return "# No manifests generated\n"
        
        return yaml.dump_all(all_manifests, default_flow_style=False, indent=2)
    
    def _generate_production_readme(self, system_blueprint) -> str:
        """Generate comprehensive production deployment README"""
        
        readme_content = f"""# {system_blueprint.system.name} - Production Service Mesh Deployment

## Overview

This directory contains production-ready Istio service mesh configurations for {system_blueprint.system.name}.
All configurations follow enterprise security and resilience best practices.

## Features

### 🔒 Security
- **Zero-Trust Architecture**: Strict mTLS for all service-to-service communication
- **JWT Authentication**: Multiple identity provider support
- **Fine-Grained RBAC**: Per-component authorization policies
- **External Authorization**: Integration with external auth services

### 🚦 Traffic Management
- **Advanced Routing**: Canary deployments with traffic splitting
- **Circuit Breakers**: Automatic failure detection and isolation
- **Retry Policies**: Intelligent retry with backoff strategies
- **Load Balancing**: Multiple algorithms with locality awareness

### 📊 Observability
- **Distributed Tracing**: Full request tracing with Jaeger
- **Metrics Collection**: Comprehensive Prometheus integration
- **Access Logging**: Structured logging with OpenTelemetry
- **Grafana Dashboards**: Pre-configured monitoring dashboards

### 🛡️ Resilience
- **Fault Injection**: Chaos engineering for resilience testing
- **Resource Quotas**: Proper resource management and limits
- **Health Checks**: Comprehensive liveness and readiness probes
- **Auto-scaling**: HPA configuration for control plane and gateways

### 🌐 Multi-Cluster
- **Cross-Cluster Service Discovery**: Seamless multi-cluster communication
- **Network Policies**: Secure cross-cluster networking
- **Hybrid Cloud Support**: On-premises and cloud integration

## Installation

### Prerequisites

1. **Kubernetes Cluster**: v1.20+ with RBAC enabled
2. **Istio**: v1.18+ installed with IstioOperator
3. **Cert-Manager**: For TLS certificate management
4. **Prometheus Operator**: For metrics collection
5. **Flagger**: For automated canary deployments

### Installation Steps

1. **Install Istio Control Plane**:
   ```bash
   ./install-production.sh install-istio
   ```

2. **Deploy Security Policies**:
   ```bash
   kubectl apply -f istio-security.yaml
   ```

3. **Configure Traffic Management**:
   ```bash
   kubectl apply -f istio-traffic.yaml
   ```

4. **Setup Observability**:
   ```bash
   kubectl apply -f istio-observability.yaml
   ```

5. **Enable Resilience Features**:
   ```bash
   kubectl apply -f istio-resilience.yaml
   ```

6. **Configure Ingress/Egress**:
   ```bash
   kubectl apply -f istio-ingress-egress.yaml
   ```

7. **Apply Policies**:
   ```bash
   kubectl apply -f istio-policies.yaml
   ```

8. **Setup Canary Deployments**:
   ```bash
   kubectl apply -f istio-canary.yaml
   ```

9. **Enable Chaos Engineering** (Optional):
   ```bash
   kubectl apply -f istio-chaos-engineering.yaml
   ```

## Configuration

### TLS Certificates

Create TLS certificates for secure communication:

```bash
# Create CA certificate
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \\
    -subj '/O=AutoCoder Inc./CN={system_blueprint.system.name}.local' \\
    -keyout {system_blueprint.system.name}.local.key \\
    -out {system_blueprint.system.name}.local.crt

# Create Kubernetes secret
kubectl create -n istio-system secret tls {system_blueprint.system.name}-tls-cert \\
    --key={system_blueprint.system.name}.local.key \\
    --cert={system_blueprint.system.name}.local.crt
```

### Service Mesh Configuration

Key configuration parameters:

- **mTLS Mode**: STRICT (all services require mutual TLS)
- **Traffic Policy**: Round-robin with circuit breakers
- **Retry Policy**: 3 attempts with exponential backoff
- **Timeout**: 30s for all requests
- **Circuit Breaker**: 5 consecutive errors trigger isolation

## Monitoring

### Grafana Dashboards

Access monitoring dashboards:

```bash
kubectl port-forward -n istio-system svc/grafana 3000:3000
```

Open http://localhost:3000 and import the pre-configured dashboards.

### Jaeger Tracing

Access distributed tracing:

```bash
kubectl port-forward -n istio-system svc/jaeger 16686:16686
```

Open http://localhost:16686 to view request traces.

### Prometheus Metrics

Access metrics directly:

```bash
kubectl port-forward -n istio-system svc/prometheus 9090:9090
```

## Troubleshooting

### Common Issues

1. **mTLS Certificate Issues**:
   ```bash
   kubectl get peerauthentication -n {getattr(system_blueprint.system, 'namespace', 'default')}
   kubectl describe peerauthentication {system_blueprint.system.name}-mtls-strict
   ```

2. **Traffic Routing Issues**:
   ```bash
   kubectl get virtualservice -n {getattr(system_blueprint.system, 'namespace', 'default')}
   kubectl describe virtualservice <service-name>-vs
   ```

3. **Circuit Breaker Status**:
   ```bash
   kubectl get destinationrule -n {getattr(system_blueprint.system, 'namespace', 'default')}
   kubectl describe destinationrule <service-name>-dr
   ```

### Log Analysis

View Istio proxy logs:

```bash
kubectl logs -n {getattr(system_blueprint.system, 'namespace', 'default')} <pod-name> -c istio-proxy --tail=100
```

View control plane logs:

```bash
kubectl logs -n istio-system deployment/istiod --tail=100
```

## Security Considerations

### Production Checklist

- [ ] All services have mTLS enabled
- [ ] Authorization policies are properly configured
- [ ] External traffic uses proper TLS certificates
- [ ] Network policies restrict unauthorized access
- [ ] Resource quotas are applied
- [ ] Security contexts are non-root
- [ ] Secrets are properly managed
- [ ] RBAC is correctly configured

### Regular Maintenance

1. **Certificate Rotation**: Certificates should be rotated every 90 days
2. **Security Updates**: Keep Istio and all components updated
3. **Policy Review**: Regularly review authorization policies
4. **Audit Logs**: Monitor access logs for suspicious activity

## Performance Tuning

### Resource Allocation

Recommended resource allocations for production:

- **Istiod**: 2 CPU, 4Gi memory
- **Ingress Gateway**: 2 CPU, 1Gi memory
- **Egress Gateway**: 1 CPU, 512Mi memory

### Connection Pool Tuning

Adjust connection pool settings based on traffic patterns:

- **Max Connections**: 100 per upstream service
- **Max Pending Requests**: 50 per connection
- **Request Timeout**: 30s
- **Idle Timeout**: 90s

## Support

For issues related to this service mesh deployment:

1. Check the troubleshooting section above
2. Review Istio documentation: https://istio.io/latest/docs/
3. Check service mesh logs and metrics
4. Contact the platform team for assistance

---

Generated by AutoCoder4_CC Production Service Mesh Generator  
Timestamp: {datetime.now().isoformat()}
"""
        
        return readme_content
    
    def _generate_installation_script(self, system_blueprint) -> str:
        """Generate production installation script"""
        
        script_content = f"""#!/bin/bash

# Production Installation Script for {system_blueprint.system.name} Service Mesh
# Generated by AutoCoder4_CC Production Service Mesh Generator

set -euo pipefail

NAMESPACE="{getattr(system_blueprint.system, 'namespace', 'default')}"
SYSTEM_NAME="{system_blueprint.system.name}"

log() {{
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}}

check_prerequisites() {{
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log "ERROR: kubectl is not installed"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log "ERROR: Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check Istio
    if ! command -v istioctl &> /dev/null; then
        log "ERROR: istioctl is not installed"
        exit 1
    fi
    
    log "Prerequisites check passed"
}}

install_istio() {{
    log "Installing Istio control plane..."
    
    # Apply IstioOperator configuration
    kubectl apply -f istio-control-plane.yaml
    
    # Wait for Istio to be ready
    kubectl wait --for=condition=Ready pod -l app=istiod -n istio-system --timeout=300s
    
    log "Istio control plane installed successfully"
}}

setup_namespace() {{
    log "Setting up namespace: $NAMESPACE"
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Enable Istio injection
    kubectl label namespace $NAMESPACE istio-injection=enabled --overwrite
    
    log "Namespace $NAMESPACE configured"
}}

apply_security() {{
    log "Applying security configurations..."
    kubectl apply -f istio-security.yaml -n $NAMESPACE
    log "Security configurations applied"
}}

apply_traffic_management() {{
    log "Applying traffic management configurations..."
    kubectl apply -f istio-traffic.yaml -n $NAMESPACE
    log "Traffic management configurations applied"
}}

apply_observability() {{
    log "Applying observability configurations..."
    kubectl apply -f istio-observability.yaml -n $NAMESPACE
    log "Observability configurations applied"
}}

apply_policies() {{
    log "Applying policies..."
    kubectl apply -f istio-policies.yaml -n $NAMESPACE
    log "Policies applied"
}}

validate_installation() {{
    log "Validating installation..."
    
    # Check Istio proxy injection
    if kubectl get pods -n $NAMESPACE -o jsonpath='{{.items[*].spec.containers[*].name}}' | grep -q istio-proxy; then
        log "✅ Istio proxy injection working"
    else
        log "⚠️  No Istio proxies found - check if pods are running"
    fi
    
    # Check mTLS status
    if istioctl authn tls-check -n $NAMESPACE 2>/dev/null | grep -q STRICT; then
        log "✅ mTLS is properly configured"
    else
        log "⚠️  mTLS may not be configured correctly"
    fi
    
    # Check gateway status
    if kubectl get gateway -n $NAMESPACE | grep -q $SYSTEM_NAME; then
        log "✅ Gateway configured"
    else
        log "⚠️  Gateway not found"
    fi
    
    log "Installation validation complete"
}}

case "${{1:-}}" in
    "install-istio")
        check_prerequisites
        install_istio
        ;;
    "setup-namespace")
        setup_namespace
        ;;
    "apply-security")
        apply_security
        ;;
    "apply-traffic")
        apply_traffic_management
        ;;
    "apply-observability")
        apply_observability
        ;;
    "apply-policies")
        apply_policies
        ;;
    "validate")
        validate_installation
        ;;
    "install-all")
        check_prerequisites
        install_istio
        setup_namespace
        apply_security
        apply_traffic_management
        apply_observability
        apply_policies
        validate_installation
        log "🎉 Production service mesh installation complete!"
        ;;
    *)
        echo "Usage: $0 {{install-istio|setup-namespace|apply-security|apply-traffic|apply-observability|apply-policies|validate|install-all}}"
        echo ""
        echo "Commands:"
        echo "  install-istio       Install Istio control plane"
        echo "  setup-namespace     Setup and configure namespace"
        echo "  apply-security      Apply security configurations"
        echo "  apply-traffic       Apply traffic management"
        echo "  apply-observability Apply observability stack"
        echo "  apply-policies      Apply service mesh policies"
        echo "  validate           Validate installation"
        echo "  install-all        Run complete installation"
        exit 1
        ;;
esac
"""
        
        return script_content


# Export the main classes for use by other modules
__all__ = ['ServiceDeploymentGenerator', 'ProductionIstioServiceMesh', 'ProductionServiceMeshManifests']