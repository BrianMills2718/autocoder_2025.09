"""
Kubernetes manifest generator plugin for the scaffold generation system.
Follows Enterprise Roadmap v2 plugin architecture.
"""
from typing import Dict, Any, List
import yaml
from autocoder_cc.core.config import settings
from autocoder_cc.generators.config import generator_settings


class K8sManifestGenerator:
    """Generates Kubernetes manifests for autocoder systems."""
    
    def generate_deployment(self, blueprint: Dict[str, Any]) -> str:
        """Generate Kubernetes deployment manifest."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': system_name,
                'namespace': settings.K8S_NAMESPACE,
                'labels': {
                    'app': system_name,
                    'version': settings.API_VERSION
                }
            },
            'spec': {
                'replicas': 1,
                'selector': {
                    'matchLabels': {
                        'app': system_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': system_name,
                            'version': settings.API_VERSION
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': system_name,
                            'image': f"{settings.DOCKER_REGISTRY}/{settings.DOCKER_IMAGE_PREFIX}/{system_name}:{settings.API_VERSION}",
                            'ports': self._generate_container_ports(system),
                            'env': self._generate_env_vars(system),
                            'resources': {
                                'requests': {
                                    'memory': generator_settings.default_memory_request,
                                    'cpu': generator_settings.default_cpu_request
                                },
                                'limits': {
                                    'memory': generator_settings.default_memory_limit,
                                    'cpu': generator_settings.default_cpu_limit
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': generator_settings.api_port
                                },
                                'initialDelaySeconds': generator_settings.health_check_interval,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': generator_settings.api_port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        return yaml.dump(deployment, default_flow_style=False)
    
    def generate_service(self, blueprint: Dict[str, Any]) -> str:
        """Generate Kubernetes service manifest."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': system_name,
                'namespace': settings.K8S_NAMESPACE,
                'labels': {
                    'app': system_name
                }
            },
            'spec': {
                'type': 'ClusterIP',
                'selector': {
                    'app': system_name
                },
                'ports': self._generate_service_ports(system)
            }
        }
        
        return yaml.dump(service, default_flow_style=False)
    
    def generate_configmap(self, blueprint: Dict[str, Any]) -> str:
        """Generate Kubernetes ConfigMap for application configuration."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f"{system_name}-config",
                'namespace': settings.K8S_NAMESPACE
            },
            'data': {
                'ENVIRONMENT': settings.ENVIRONMENT,
                'LOG_LEVEL': settings.LOG_LEVEL,
                'API_PREFIX': settings.DEFAULT_API_PREFIX,
                'ENABLE_METRICS': str(settings.ENABLE_METRICS).lower(),
                'METRICS_PORT': str(settings.METRICS_PORT)
            }
        }
        
        return yaml.dump(configmap, default_flow_style=False)
    
    def _generate_container_ports(self, system: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate container port specifications."""
        ports = [{'containerPort': settings.PORT_RANGE_START, 'name': 'http'}]
        
        if settings.ENABLE_METRICS:
            ports.append({'containerPort': settings.METRICS_PORT, 'name': 'metrics'})
        
        return ports
    
    def _generate_service_ports(self, system: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate service port specifications."""
        ports = [{
            'port': 80,
            'targetPort': settings.PORT_RANGE_START,
            'protocol': 'TCP',
            'name': 'http'
        }]
        
        if settings.ENABLE_METRICS:
            ports.append({
                'port': settings.METRICS_PORT,
                'targetPort': settings.METRICS_PORT,
                'protocol': 'TCP',
                'name': 'metrics'
            })
        
        return ports
    
    def _generate_env_vars(self, system: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate environment variables for container."""
        env_vars = []
        
        # Add ConfigMap environment variables
        env_vars.append({
            'name': 'ENVIRONMENT',
            'valueFrom': {
                'configMapKeyRef': {
                    'name': f"{system.get('name', 'autocoder-app')}-config",
                    'key': 'ENVIRONMENT'
                }
            }
        })
        
        # Add secret environment variables
        components = system.get('components', [])
        
        if any(comp.get('type') == 'Store' for comp in components):
            env_vars.append({
                'name': 'DATABASE_URL',
                'valueFrom': {
                    'secretKeyRef': {
                        'name': f"{system.get('name', 'autocoder-app')}-secrets",
                        'key': 'database-url'
                    }
                }
            })
        
        if any(comp.get('type') == 'MessageBus' for comp in components):
            env_vars.append({
                'name': 'RABBITMQ_URL',
                'valueFrom': {
                    'secretKeyRef': {
                        'name': f"{system.get('name', 'autocoder-app')}-secrets",
                        'key': 'rabbitmq-url'
                    }
                }
            })
        
        return env_vars