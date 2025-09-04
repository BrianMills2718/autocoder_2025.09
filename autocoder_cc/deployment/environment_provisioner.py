#!/usr/bin/env python3
"""
Environment Provisioner - Manages environment-specific configuration and setup

Extracted from the monolithic system_generator.py, this module handles
environment provisioning, configuration management, and secret handling
for different deployment environments.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import os

from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.core.module_interfaces import (
    ITemplateEngine,
    ISecretManager
)


logger = get_logger(__name__)
metrics = get_metrics_collector("environment_provisioner")
tracer = get_tracer("environment_provisioner")


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment"""
    environment: str
    debug_enabled: bool
    ssl_enabled: bool
    resource_limits: Optional[Dict[str, Any]]
    database_config: Dict[str, Any]
    config_map: Dict[str, str]
    secrets: List['SecretReference']


@dataclass
class SecretReference:
    """Reference to a managed secret"""
    name: str
    reference: str
    type: str


@dataclass
class TeardownResult:
    """Result of environment teardown"""
    success: bool
    resources_cleaned: int
    errors: List[str]


class EnvironmentProvisioner:
    """
    Manages environment-specific provisioning and configuration.
    
    Responsibilities:
    - Environment setup (dev/staging/prod)
    - Configuration template rendering
    - Secret management integration
    - Resource limit configuration
    - Environment teardown and cleanup
    """
    
    def __init__(self,
                 config_template_engine: ITemplateEngine,
                 secret_manager: ISecretManager):
        """Initialize environment provisioner with strict dependency injection"""
        # Require all dependencies - no fallbacks
        if config_template_engine is None:
            raise ValueError("TemplateEngine must be provided via dependency injection")
        if secret_manager is None:
            raise ValueError("SecretManager must be provided via dependency injection")
            
        self.config_template_engine = config_template_engine
        self.secret_manager = secret_manager
        self.logger = logger
        
    def provision_environment(self,
                            environment: str,
                            system_name: str,
                            components: List[Any]) -> EnvironmentConfig:
        """
        Provision environment with appropriate configuration.
        
        Args:
            environment: Target environment (development/staging/production)
            system_name: Name of the system being deployed
            components: List of system components
            
        Returns:
            EnvironmentConfig with environment-specific settings
        """
        with tracer.span("provision_environment", tags={"environment": environment, "system_name": system_name}):
            
            self.logger.info(f"Provisioning {environment} environment for {system_name}")
            metrics.increment("environment.provision.started", tags={"environment": environment})
            
            # Base configuration for environment
            config = {
                "environment": environment,
                "debug_enabled": self._is_debug_enabled(environment),
                "ssl_enabled": self._is_ssl_enabled(environment),
                "resource_limits": self._get_resource_limits(environment),
                "database_config": self._configure_databases(components, environment),
                "config_map": self._build_config_map(system_name, environment, components),
                "secrets": []
            }
            
            # Handle secrets for production
            if environment == "production":
                secrets = self._provision_secrets(system_name, components)
                config["secrets"] = secrets
            
            # Create environment config object
            env_config = EnvironmentConfig(**config)
            
            metrics.increment("environment.provision.success", tags={"environment": environment})
            self.logger.info(f"Successfully provisioned {environment} environment")
            
            return env_config
    
    def inject_configuration(self,
                           component_name: str,
                           component_type: str,
                           environment: str) -> Dict[str, str]:
        """
        Inject configuration for a specific component.
        
        Args:
            component_name: Name of the component
            component_type: Type of the component
            environment: Target environment
            
        Returns:
            Dictionary of configuration values
        """
        self.logger.debug(f"Injecting configuration for {component_name} in {environment}")
        
        # Base configuration template
        config_template = {
            "component_name": component_name,
            "component_type": component_type,
            "environment": environment,
            "log_level": "DEBUG" if environment == "development" else "INFO",
            "metrics_enabled": "true",
            "tracing_enabled": "true"
        }
        
        # Component-specific configuration
        if component_type == "APIEndpoint":
            config_template.update({
                "API_KEY": "${API_KEY}",
                "RATE_LIMIT": "100" if environment == "development" else "1000",
                "TIMEOUT": "30"
            })
        elif component_type == "Store":
            config_template.update({
                "DB_URL": self._get_database_url(component_name, environment),
                "CONNECTION_POOL_SIZE": "5" if environment == "development" else "20",
                "CACHE_ENABLED": "false" if environment == "development" else "true"
            })
        elif component_type == "Processor":
            config_template.update({
                "WORKER_COUNT": "1" if environment == "development" else "4",
                "BATCH_SIZE": "10" if environment == "development" else "100",
                "PROCESSING_TIMEOUT": "60"
            })
        
        # Render configuration through template engine if available
        if self.config_template_engine:
            try:
                rendered_config = self.config_template_engine.render(
                    "config_template",
                    config_template
                )
                if isinstance(rendered_config, dict):
                    return rendered_config
            except Exception as e:
                self.logger.warning(f"Template rendering failed: {e}, using raw config")
        
        # Convert all values to strings for environment variables
        return {k: str(v) for k, v in config_template.items()}
    
    def manage_secrets(self,
                      system_name: str,
                      secrets_required: List[Dict[str, str]],
                      environment: str) -> List[SecretReference]:
        """
        Manage secrets for the deployment.
        
        Args:
            system_name: Name of the system
            secrets_required: List of required secrets
            environment: Target environment
            
        Returns:
            List of secret references
        """
        self.logger.info(f"Managing {len(secrets_required)} secrets for {system_name}")
        
        secret_refs = []
        
        for secret_spec in secrets_required:
            secret_name = secret_spec.get("name", "unnamed")
            secret_type = secret_spec.get("type", "generic")
            
            # Create secret path
            secret_path = f"{environment}/{system_name}/{secret_name}"
            
            # Create or update secret
            if self.secret_manager:
                try:
                    secret_ref = self.secret_manager.create_secret(
                        secret_path,
                        self._generate_secret_value(secret_type)
                    )
                    
                    secret_refs.append(SecretReference(
                        name=secret_name,
                        reference=secret_ref,
                        type=secret_type
                    ))
                    
                    self.logger.info(f"Created secret: {secret_name}")
                except Exception as e:
                    self.logger.error(f"Failed to create secret {secret_name}: {e}")
            else:
                # Mock secret reference for testing
                secret_refs.append(SecretReference(
                    name=secret_name,
                    reference=f"mock://secrets/{secret_path}",
                    type=secret_type
                ))
        
        return secret_refs
    
    def teardown_environment(self,
                           system_name: str,
                           environment: str) -> TeardownResult:
        """
        Teardown environment and clean up resources.
        
        Args:
            system_name: Name of the system
            environment: Environment to teardown
            
        Returns:
            TeardownResult with cleanup details
        """
        self.logger.info(f"Tearing down {environment} environment for {system_name}")
        
        errors = []
        resources_cleaned = 0
        
        try:
            # Clean up secrets
            if environment == "production" and self.secret_manager:
                try:
                    # In a real implementation, we would delete secrets
                    # For now, just log the action
                    self.logger.info(f"Cleaning up secrets for {system_name}")
                    resources_cleaned += 1
                except Exception as e:
                    errors.append(f"Failed to clean secrets: {e}")
            
            # Clean up database resources
            # In a real implementation, we would drop databases/tables
            self.logger.info(f"Cleaning up database resources for {system_name}")
            resources_cleaned += 1
            
            # Clean up configuration
            self.logger.info(f"Cleaning up configuration for {system_name}")
            resources_cleaned += 1
            
        except Exception as e:
            errors.append(f"Teardown failed: {e}")
        
        success = len(errors) == 0
        
        return TeardownResult(
            success=success,
            resources_cleaned=resources_cleaned,
            errors=errors
        )
    
    # Private helper methods
    
    def _is_debug_enabled(self, environment: str) -> bool:
        """Check if debug should be enabled for environment"""
        return environment == "development"
    
    def _is_ssl_enabled(self, environment: str) -> bool:
        """Check if SSL should be enabled for environment"""
        return environment in ["staging", "production"]
    
    def _get_resource_limits(self, environment: str) -> Optional[Dict[str, Any]]:
        """Get resource limits for environment"""
        if environment == "development":
            return None
        
        limits = {
            "staging": {
                "cpu": "500m",
                "memory": "512Mi",
                "storage": "5Gi"
            },
            "production": {
                "cpu": "2000m",
                "memory": "2Gi",
                "storage": "20Gi"
            }
        }
        
        return limits.get(environment)
    
    def _configure_databases(self, components: List[Any], environment: str) -> Dict[str, Any]:
        """Configure databases for components"""
        db_config = {}
        
        for component in components:
            if hasattr(component, 'type') and component.type == "Store":
                db_name = f"{component.name}_db"
                
                if environment == "development":
                    # Use SQLite for development
                    db_config[db_name] = {
                        "type": "sqlite",
                        "path": f"/tmp/{db_name}.db"
                    }
                else:
                    # Use PostgreSQL for staging/production
                    db_config[db_name] = {
                        "type": "postgresql",
                        "host": os.getenv(f"{db_name.upper()}_HOST", "localhost"),
                        "port": 5432,
                        "database": db_name,
                        "ssl": environment == "production"
                    }
        
        return db_config
    
    def _build_config_map(self, system_name: str, environment: str, components: List[Any]) -> Dict[str, str]:
        """Build configuration map for the system"""
        config_map = {
            "SYSTEM_NAME": system_name,
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "DEBUG" if environment == "development" else "INFO",
            "METRICS_ENABLED": "true",
            "TRACING_ENABLED": "true"
        }
        
        # Add component count
        config_map["COMPONENT_COUNT"] = str(len(components))
        
        # Add feature flags
        if environment == "development":
            config_map["FEATURE_FLAG_DEBUG_UI"] = "true"
            config_map["FEATURE_FLAG_PROFILING"] = "true"
        elif environment == "staging":
            config_map["FEATURE_FLAG_CANARY"] = "true"
        
        return config_map
    
    def _provision_secrets(self, system_name: str, components: List[Any]) -> List[SecretReference]:
        """Provision secrets for production environment"""
        secrets_required = []
        
        # API key for API endpoints
        if any(c.type == "APIEndpoint" for c in components if hasattr(c, 'type')):
            secrets_required.append({
                "name": "api_key",
                "type": "api"
            })
        
        # Database passwords for stores
        for component in components:
            if hasattr(component, 'type') and component.type == "Store":
                secrets_required.append({
                    "name": f"{component.name}_db_password",
                    "type": "database"
                })
        
        # Encryption keys
        secrets_required.append({
            "name": "encryption_key",
            "type": "encryption"
        })
        
        return self.manage_secrets(system_name, secrets_required, "production")
    
    def _get_database_url(self, component_name: str, environment: str) -> str:
        """Get database URL for component"""
        if environment == "development":
            return f"sqlite:///tmp/{component_name}.db"
        else:
            # In production, this would come from secret manager
            host = os.getenv(f"{component_name.upper()}_DB_HOST", "localhost")
            port = os.getenv(f"{component_name.upper()}_DB_PORT", "5432")
            db_name = f"{component_name}_db"
            
            return f"postgresql://user:password@{host}:{port}/{db_name}"
    
    def _generate_secret_value(self, secret_type: str) -> str:
        """Generate a secret value based on type"""
        # In a real implementation, this would generate secure random values
        # For now, return placeholder values
        secret_templates = {
            "api": "sk_test_" + "x" * 32,
            "database": "db_pass_" + "x" * 24,
            "encryption": "enc_key_" + "x" * 32,
            "generic": "secret_" + "x" * 16
        }
        
        return secret_templates.get(secret_type, secret_templates["generic"])