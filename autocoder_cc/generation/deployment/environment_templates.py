"""
Environment Configuration Templates for Dynamic Configuration Management
GREEN Phase: Minimum implementation to pass tests
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EnvironmentTemplate:
    """Data class representing an environment configuration template"""
    environment: str
    config: Dict[str, Any]
    security: Dict[str, Any]  
    resources: Dict[str, Any]
    metadata: Dict[str, Any]


class EnvironmentTemplateManager:
    """
    Manages environment-specific configuration templates
    
    Provides structured templates for test, development, and production environments
    with appropriate configurations, security settings, and resource limits.
    """
    
    SUPPORTED_ENVIRONMENTS = {"test", "dev", "prod"}
    TEMPLATE_VERSION = "1.0.0"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = self._build_templates()
    
    def _build_templates(self) -> Dict[str, EnvironmentTemplate]:
        """Build environment-specific configuration templates using centralized value generation"""
        templates = {}
        
        # Test environment template
        templates["test"] = EnvironmentTemplate(
            environment="test",
            config=self._get_base_config("test"),
            security=self._get_security_config("test"),
            resources=self._get_resource_config("test"),
            metadata={
                "created_at": datetime.now().isoformat(),
                "version": self.TEMPLATE_VERSION,
                "description": "Test environment with minimal resources"
            }
        )
        
        # Development environment template
        templates["dev"] = EnvironmentTemplate(
            environment="dev", 
            config=self._get_base_config("dev"),
            security=self._get_security_config("dev"),
            resources=self._get_resource_config("dev"),
            metadata={
                "created_at": datetime.now().isoformat(),
                "version": self.TEMPLATE_VERSION,
                "description": "Development environment with moderate resources"
            }
        )
        
        # Production environment template
        templates["prod"] = EnvironmentTemplate(
            environment="prod",
            config=self._get_base_config("prod"),
            security=self._get_security_config("prod"),
            resources=self._get_resource_config("prod"),
            metadata={
                "created_at": datetime.now().isoformat(),
                "version": self.TEMPLATE_VERSION,
                "description": "Production environment with high availability"
            }
        )
        
        return templates
    
    def _get_base_config(self, environment: str) -> Dict[str, Any]:
        """Get base configuration values for an environment - SINGLE SOURCE OF TRUTH"""
        if environment == "test":
            return {
                "db_connection_string": "sqlite:///test.db",
                "debug": True,
                "log_level": "DEBUG"
            }
        elif environment == "dev":
            return {
                "db_connection_string": "postgresql://localhost:5432/dev_db",
                "debug": True,
                "log_level": "INFO"
            }
        elif environment == "prod":
            return {
                "db_connection_string": "${DB_CONNECTION_STRING}",
                "debug": False,
                "log_level": "WARNING"
            }
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    def _get_security_config(self, environment: str) -> Dict[str, Any]:
        """Get security configuration for an environment"""
        if environment == "test":
            return {
                "ssl_enabled": False,
                "ssl_cert_path": "",
                "auth_required": False
            }
        elif environment == "dev":
            return {
                "ssl_enabled": False,
                "ssl_cert_path": "",
                "auth_required": True
            }
        elif environment == "prod":
            return {
                "ssl_enabled": True,
                "ssl_cert_path": "${SSL_CERT_PATH}",
                "auth_required": True
            }
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    def _get_resource_config(self, environment: str) -> Dict[str, Any]:
        """Get resource configuration for an environment"""
        if environment == "test":
            return {
                "memory_limit": "512Mi",
                "cpu_limit": "0.5",
                "replicas": 1
            }
        elif environment == "dev":
            return {
                "memory_limit": "1Gi",
                "cpu_limit": "1",
                "replicas": 1
            }
        elif environment == "prod":
            return {
                "memory_limit": "2Gi",
                "cpu_limit": "2",
                "replicas": 3
            }
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    def get_template(self, environment: str) -> Dict[str, Any]:
        """
        Get environment template by name
        
        Args:
            environment: Environment name (test, dev, prod)
            
        Returns:
            Environment template as dictionary
            
        Raises:
            ValueError: If environment is not supported
        """
        if environment not in self.SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Unsupported environment: {environment}. "
                           f"Supported: {', '.join(self.SUPPORTED_ENVIRONMENTS)}")
        
        template = self.templates[environment]
        self.logger.info(f"Retrieved {environment} template")
        
        # Convert dataclass to dictionary for easier consumption
        return {
            "environment": template.environment,
            "config": template.config.copy(),
            "security": template.security.copy(),
            "resources": template.resources.copy(),
            "metadata": template.metadata.copy()
        }
    
    def resolve_template(self, environment: str, requirements: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve template with specific requirements
        
        Args:
            environment: Target environment
            requirements: Configuration requirements from analysis
            
        Returns:
            Resolved configuration dictionary
        """
        template = self.get_template(environment)
        base_config = template["config"]
        resolved_config = base_config.copy()
        
        # Add requirements not covered by base template
        for key, requirement in requirements.items():
            if key not in resolved_config:
                resolved_config[key] = self._resolve_requirement(key, requirement, environment)
        
        self.logger.info(f"Resolved template for {environment} with {len(resolved_config)} config values")
        return resolved_config
    
    def _resolve_requirement(self, key: str, requirement: Dict[str, Any], environment: str) -> Any:
        """Resolve a single configuration requirement based on environment"""
        if requirement.get("required", False):
            return self._generate_environment_value(key, environment)
        else:
            return requirement.get("default")
    
    def _generate_environment_value(self, key: str, environment: str) -> Any:
        """
        Generate environment-appropriate value for a configuration key
        Uses the centralized configuration methods to maintain single source of truth
        """
        # First, check if this key matches any known configuration patterns
        base_config = self._get_base_config(environment)
        
        # Check for direct matches in base config
        if key in base_config:
            return base_config[key]
            
        # For unknown keys, generate based on key patterns and environment
        key_lower = key.lower()
        
        if environment == "prod":
            # Production always uses environment variables for unknown configs
            return f"${{{key.upper()}}}"
        
        # For test/dev, generate appropriate values based on key patterns
        if "db_connection_string" in key_lower or "database_url" in key_lower:
            return base_config["db_connection_string"]
        elif "db_port" in key_lower:
            if environment == "test":
                return 5432  # Default PostgreSQL port for test
            else:
                return 5432
        elif "db_host" in key_lower:
            if environment == "test":
                return "localhost"
            else:
                return "localhost"
        elif "db_name" in key_lower:
            if environment == "test":
                return "test_db"
            else:
                return f"{environment}_db"
        elif "db_user" in key_lower:
            if environment == "test":
                return "test_user"
            else:
                return f"{environment}_user"
        elif "db_password" in key_lower:
            if environment == "test":
                return "test_password"
            else:
                return f"{environment}_password"
        elif any(term in key_lower for term in ["secret_key", "secret"]) and "api" not in key_lower:
            return f"{environment}-secret-key"
        elif "port" in key_lower:
            return 8080
        elif "host" in key_lower:
            return "localhost"
        else:
            return f"{environment}-{key}"