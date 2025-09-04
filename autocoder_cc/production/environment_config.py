from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Environment-Aware Configuration Manager for Autocoder v5.0

Handles configuration differences between development, staging, and production environments.
Ensures proper service discovery, resource allocation, and environment-specific settings.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
from autocoder_cc.generators.config import generator_settings


class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class ServiceEndpoint:
    """Configuration for a service endpoint"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    path: str = "/"
    
    @property
    def url(self) -> str:
        """Get full URL for the service"""
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"


@dataclass
class ResourceLimits:
    """Resource limits for containers"""
    cpu: str
    memory: str
    
    
@dataclass
class ResourceRequests:
    """Resource requests for containers"""
    cpu: str
    memory: str


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment"""
    name: Environment
    service_endpoints: Dict[str, ServiceEndpoint] = field(default_factory=dict)
    resource_requests: ResourceRequests = None
    resource_limits: ResourceLimits = None
    replicas: int = 1
    debug_enabled: bool = False
    log_level: str = "INFO"
    features: Dict[str, bool] = field(default_factory=dict)
    custom_config: Dict[str, Any] = field(default_factory=dict)


class EnvironmentConfigManager:
    """
    Manages environment-specific configurations for systems.
    
    Key features:
    - Service discovery configuration per environment
    - Resource allocation based on environment
    - Feature flags and toggles
    - Environment-specific secrets and variables
    """
    
    def __init__(self):
        self.logger = get_logger("EnvironmentConfigManager")
        self.environments = {}
        self._init_default_environments()
    
    def _init_default_environments(self):
        """Initialize default environment configurations"""
        
        # Development environment
        self.environments[Environment.DEVELOPMENT] = EnvironmentConfig(
            name=Environment.DEVELOPMENT,
            service_endpoints={
                "postgres": ServiceEndpoint("postgres", generator_settings.postgres_host, generator_settings.postgres_port, "postgresql"),
                "redis": ServiceEndpoint("redis", generator_settings.redis_host, generator_settings.redis_port, "redis"),
                "kafka": ServiceEndpoint("kafka", generator_settings.kafka_host, generator_settings.kafka_port, "tcp"),
            },
            resource_requests=ResourceRequests("100m", "128Mi"),
            resource_limits=ResourceLimits("500m", "512Mi"),
            replicas=1,
            debug_enabled=True,
            log_level="DEBUG",
            features={
                "detailed_logging": True,
                "debug_endpoints": True,
                "mock_external_services": True,
            }
        )
        
        # Staging environment
        self.environments[Environment.STAGING] = EnvironmentConfig(
            name=Environment.STAGING,
            service_endpoints={
                "postgres": ServiceEndpoint("postgres", "postgres.staging.svc.cluster.local", 5432, "postgresql"),
                "redis": ServiceEndpoint("redis", "redis.staging.svc.cluster.local", 6379, "redis"),
                "kafka": ServiceEndpoint("kafka", "kafka.staging.svc.cluster.local", 9092, "tcp"),
            },
            resource_requests=ResourceRequests("200m", "256Mi"),
            resource_limits=ResourceLimits("1000m", "1Gi"),
            replicas=2,
            debug_enabled=False,
            log_level="INFO",
            features={
                "detailed_logging": True,
                "debug_endpoints": False,
                "mock_external_services": False,
            }
        )
        
        # Production environment
        self.environments[Environment.PRODUCTION] = EnvironmentConfig(
            name=Environment.PRODUCTION,
            service_endpoints={
                "postgres": ServiceEndpoint("postgres", "postgres.prod.svc.cluster.local", 5432, "postgresql"),
                "redis": ServiceEndpoint("redis", "redis.prod.svc.cluster.local", 6379, "redis"),
                "kafka": ServiceEndpoint("kafka", "kafka.prod.svc.cluster.local", 9092, "tcp"),
            },
            resource_requests=ResourceRequests("500m", "512Mi"),
            resource_limits=ResourceLimits("2000m", "2Gi"),
            replicas=3,
            debug_enabled=False,
            log_level="WARNING",
            features={
                "detailed_logging": False,
                "debug_endpoints": False,
                "mock_external_services": False,
            }
        )
    
    def get_config(self, environment: Environment) -> EnvironmentConfig:
        """Get configuration for a specific environment"""
        return self.environments.get(environment, self.environments[Environment.DEVELOPMENT])
    
    def generate_config_map(self, system_name: str, environment: Environment) -> str:
        """
        Generate Kubernetes ConfigMap for environment-specific configuration.
        
        Args:
            system_name: Name of the system
            environment: Target environment
            
        Returns:
            ConfigMap manifest YAML
        """
        config = self.get_config(environment)
        
        # Build configuration data
        config_data = {
            "ENVIRONMENT": environment.value,
            "LOG_LEVEL": config.log_level,
            "DEBUG_ENABLED": str(config.debug_enabled).lower(),
            "REPLICAS": str(config.replicas),
        }
        
        # Add service endpoints
        for service_name, endpoint in config.service_endpoints.items():
            config_data[f"{service_name.upper()}_HOST"] = endpoint.host
            config_data[f"{service_name.upper()}_PORT"] = str(endpoint.port)
            config_data[f"{service_name.upper()}_URL"] = endpoint.url
        
        # Add feature flags
        for feature, enabled in config.features.items():
            config_data[f"FEATURE_{feature.upper()}"] = str(enabled).lower()
        
        # Add custom configuration
        for key, value in config.custom_config.items():
            config_data[key] = str(value)
        
        manifest = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {system_name}-config
  namespace: {system_name}
  labels:
    app: {system_name}
    environment: {environment.value}
data:
"""
        
        for key, value in sorted(config_data.items()):
            manifest += f"  {key}: \"{value}\"\n"
        
        return manifest
    
    def generate_deployment_patch(self, environment: Environment) -> Dict[str, Any]:
        """
        Generate deployment patch for environment-specific settings.
        
        Args:
            environment: Target environment
            
        Returns:
            Deployment patch dictionary
        """
        config = self.get_config(environment)
        
        patch = {
            "spec": {
                "replicas": config.replicas,
                "template": {
                    "spec": {
                        "containers": [{
                            "resources": {
                                "requests": {
                                    "cpu": config.resource_requests.cpu,
                                    "memory": config.resource_requests.memory
                                },
                                "limits": {
                                    "cpu": config.resource_limits.cpu,
                                    "memory": config.resource_limits.memory
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        return patch
    
    def transform_for_environment(self, base_config: Dict[str, Any], 
                                environment: Environment) -> Dict[str, Any]:
        """
        Transform a base configuration for a specific environment.
        
        Args:
            base_config: Base system configuration
            environment: Target environment
            
        Returns:
            Transformed configuration
        """
        config = self.get_config(environment)
        transformed = base_config.copy()
        
        # Replace localhost references
        if environment != Environment.DEVELOPMENT:
            config_str = json.dumps(transformed)
            
            # Replace service references
            for service_name, endpoint in config.service_endpoints.items():
                config_str = config_str.replace(f"localhost:{endpoint.port}", 
                                              f"{endpoint.host}:{endpoint.port}")
                config_str = config_str.replace("127.0.0.1", endpoint.host)
            
            transformed = json.loads(config_str)
        
        # Update resource allocations
        if "resources" in transformed:
            transformed["resources"]["requests"] = {
                "cpu": config.resource_requests.cpu,
                "memory": config.resource_requests.memory
            }
            transformed["resources"]["limits"] = {
                "cpu": config.resource_limits.cpu,
                "memory": config.resource_limits.memory
            }
        
        # Update replicas
        if "replicas" in transformed:
            transformed["replicas"] = config.replicas
        
        # Apply feature flags
        if "features" in transformed:
            transformed["features"].update(config.features)
        
        return transformed
    
    def validate_for_environment(self, config: Dict[str, Any], 
                                environment: Environment) -> List[str]:
        """
        Validate configuration for a specific environment.
        
        Args:
            config: Configuration to validate
            environment: Target environment
            
        Returns:
            List of validation errors
        """
        errors = []
        env_config = self.get_config(environment)
        
        # Check for localhost references in non-dev environments
        if environment != Environment.DEVELOPMENT:
            config_str = json.dumps(config)
            if "localhost" in config_str or "127.0.0.1" in config_str:
                errors.append(f"Localhost references found in {environment.value} configuration")
        
        # Check resource limits
        if "resources" in config:
            if environment == Environment.PRODUCTION:
                # Ensure production has proper resource limits
                if "limits" not in config["resources"]:
                    errors.append("Production environment must have resource limits")
                if "requests" not in config["resources"]:
                    errors.append("Production environment must have resource requests")
        
        # Check debug settings
        if environment == Environment.PRODUCTION:
            if config.get("debug_enabled", False):
                errors.append("Debug mode must be disabled in production")
            if config.get("log_level", "INFO") == "DEBUG":
                errors.append("Debug logging should not be enabled in production")
        
        # Check replica count
        if environment == Environment.PRODUCTION:
            replicas = config.get("replicas", 1)
            if replicas < 2:
                errors.append("Production should have at least 2 replicas for high availability")
        
        return errors


def create_environment_configs(system_name: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create environment-specific configurations for all environments.
    
    Args:
        system_name: Name of the system
        base_config: Base system configuration
        
    Returns:
        Dictionary of environment configurations
    """
    manager = EnvironmentConfigManager()
    configs = {}
    
    for env in Environment:
        # Transform base config for environment
        env_config = manager.transform_for_environment(base_config, env)
        
        # Validate configuration
        errors = manager.validate_for_environment(env_config, env)
        if errors and env == Environment.PRODUCTION:
            raise ValueError(f"Production validation failed: {errors}")
        
        # Generate ConfigMap
        config_map = manager.generate_config_map(system_name, env)
        
        # Generate deployment patch
        deployment_patch = manager.generate_deployment_patch(env)
        
        configs[env.value] = {
            "config": env_config,
            "config_map": config_map,
            "deployment_patch": deployment_patch,
            "validation_errors": errors
        }
    
    return configs


if __name__ == "__main__":
    # Test environment configuration manager
    manager = EnvironmentConfigManager()
    
    # Test getting configurations
    for env in Environment:
        config = manager.get_config(env)
        print(f"\n{env.value.upper()} Configuration:")
        print(f"  Replicas: {config.replicas}")
        print(f"  Resources: {config.resource_requests.cpu}/{config.resource_requests.memory}")
        print(f"  Debug: {config.debug_enabled}")
        print(f"  Services:")
        for service, endpoint in config.service_endpoints.items():
            print(f"    {service}: {endpoint.url}")
    
    # Test configuration transformation
    base_config = {
        "database_url": generator_settings.get_postgres_url("mydb"),
        "redis_url": generator_settings.get_redis_url(),
        "replicas": 1,
        "resources": {},
        "debug_enabled": True
    }
    
    print("\n\nConfiguration Transformations:")
    for env in [Environment.DEVELOPMENT, Environment.PRODUCTION]:
        transformed = manager.transform_for_environment(base_config, env)
        print(f"\n{env.value}: {json.dumps(transformed, indent=2)}")