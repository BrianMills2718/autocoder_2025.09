from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Secure Secrets Manager for Autocoder v5.0

Handles secure generation and management of secrets for production deployments.
Ensures no placeholder secrets make it to production manifests.
"""

import os
import secrets
import string
import base64
import hashlib
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import json


@dataclass
class SecretSpec:
    """Specification for a secret"""
    name: str
    type: str  # password, api_key, jwt_secret, database_url, etc.
    description: str
    required: bool = True
    length: int = 32
    charset: Optional[str] = None
    prefix: Optional[str] = None


class SecretsManager:
    """
    Manages secure generation and validation of secrets for production deployments.
    
    Key features:
    - Generates cryptographically secure secrets
    - Validates no placeholder values in production
    - Integrates with K8s secrets and CI/CD
    - Supports various secret types
    """
    
    def __init__(self):
        self.logger = get_logger("SecretsManager")
        self.placeholder_patterns = [
            "your-api-key",
            "your-secret-key", 
            "your-secret-key-here",
            "your-api-key-here",
            "your-connection-string",
            "placeholder",
            "changeme",
            "password123",
            "secret123",
            "api-key-here",
            "replace-me",
            "update-me",
            "example",
            "sample",
            "demo",
            "test-key",
            "development-secret-key",
            "changeme",
            "password",
            "secret",
            "12345",
            "admin",
            "test",
            "demo",
            "${",  # Template variable
            "{{",  # Template variable
        ]
    
    def generate_secrets_manifest(self, system_name: str, required_secrets: List[SecretSpec]) -> Dict[str, str]:
        """
        Generate a secrets manifest with secure values.
        
        Args:
            system_name: Name of the system
            required_secrets: List of required secrets
            
        Returns:
            Dict of secret name to value
        """
        secrets_dict = {}
        
        for spec in required_secrets:
            value = self._generate_secret(spec)
            secrets_dict[spec.name] = value
            self.logger.info(f"Generated {spec.type} secret: {spec.name}")
        
        # Add standard secrets
        if "DATABASE_PASSWORD" not in secrets_dict:
            secrets_dict["DATABASE_PASSWORD"] = self._generate_password(32)
        
        if "REDIS_PASSWORD" not in secrets_dict:
            secrets_dict["REDIS_PASSWORD"] = self._generate_password(32)
        
        if "API_SECRET_KEY" not in secrets_dict:
            secrets_dict["API_SECRET_KEY"] = self._generate_api_key()
        
        if "JWT_SECRET" not in secrets_dict:
            secrets_dict["JWT_SECRET"] = self._generate_jwt_secret()
        
        return secrets_dict
    
    def validate_secrets(self, secrets_dict: Dict[str, str]) -> List[str]:
        """
        Validate that secrets don't contain placeholder values.
        
        Args:
            secrets_dict: Dictionary of secret values
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for name, value in secrets_dict.items():
            # Check for empty values
            if not value or value.strip() == "":
                errors.append(f"Secret '{name}' is empty")
                continue
            
            # Check for placeholder patterns
            value_lower = value.lower()
            for pattern in self.placeholder_patterns:
                if pattern.lower() in value_lower:
                    errors.append(f"Secret '{name}' contains placeholder value: {pattern}")
            
            # Check for weak passwords
            if "password" in name.lower():
                if len(value) < 16:
                    errors.append(f"Password '{name}' is too short (minimum 16 characters)")
                if not any(c.isupper() for c in value):
                    errors.append(f"Password '{name}' must contain uppercase letters")
                if not any(c.islower() for c in value):
                    errors.append(f"Password '{name}' must contain lowercase letters")
                if not any(c.isdigit() for c in value):
                    errors.append(f"Password '{name}' must contain digits")
        
        return errors
    
    def generate_k8s_secret_manifest(self, namespace: str, system_name: str, 
                                   secrets_dict: Dict[str, str]) -> str:
        """
        Generate Kubernetes Secret manifest with base64 encoded values.
        
        CRITICAL: This method generates production-ready secrets with no placeholder values.
        
        Args:
            namespace: K8s namespace
            system_name: System name
            secrets_dict: Dictionary of secrets
            
        Returns:
            K8s Secret manifest YAML
        """
        # Validate no placeholder secrets before generating manifest
        validation_errors = self.validate_secrets(secrets_dict)
        if validation_errors:
            raise ValueError(f"CRITICAL: Cannot generate secrets manifest with placeholder values: {validation_errors}")
        
        # Base64 encode all values
        encoded_secrets = {}
        for key, value in secrets_dict.items():
            encoded_secrets[key] = base64.b64encode(value.encode()).decode()
        
        manifest = f"""apiVersion: v1
kind: Secret
metadata:
  name: {system_name}-secrets
  namespace: {namespace}
  labels:
    app: {system_name}
    component: secrets
    managed-by: autocoder
    generated-at: "{hashlib.sha256(str(secrets_dict).encode()).hexdigest()[:16]}"
type: Opaque
data:
"""
        
        for key, encoded_value in encoded_secrets.items():
            manifest += f"  {key}: {encoded_value}\n"
        
        # Add comment indicating secure generation
        manifest += f"""# SECURITY: All secrets generated with cryptographically secure random values
# Generated by Autocoder SecretsManager - no placeholder values present
# To rotate secrets, regenerate the system or update with external secret management
"""
        
        return manifest
    
    def generate_sealed_secret_template(self, namespace: str, system_name: str,
                                      required_secrets: List[SecretSpec]) -> str:
        """
        Generate a Sealed Secrets template for secure GitOps.
        
        Args:
            namespace: K8s namespace
            system_name: System name
            required_secrets: List of required secrets
            
        Returns:
            Sealed Secrets template YAML
        """
        template = f"""apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: {system_name}-secrets
  namespace: {namespace}
spec:
  encryptedData:
"""
        
        for spec in required_secrets:
            template += f"    {spec.name}: # Encrypt actual value with: echo -n 'value' | kubeseal --raw --from-file=/dev/stdin --namespace {namespace} --name {system_name}-secrets\n"
        
        template += f"""  template:
    metadata:
      name: {system_name}-secrets
      namespace: {namespace}
    type: Opaque
"""
        
        return template
    
    def generate_env_template(self, required_secrets: List[SecretSpec]) -> str:
        """
        Generate .env.template file for local development.
        
        Args:
            required_secrets: List of required secrets
            
        Returns:
            Environment template content
        """
        template = """# Environment template for local development
# Copy this file to .env and fill in actual values
# NEVER commit the actual .env file to version control

# Database
database_url=postgresql://{postgres_host}:{postgres_port}/dev_db
DATABASE_PASSWORD=changeme

# Redis
redis_url=redis://{redis_host}:{redis_port}/0
REDIS_PASSWORD=changeme

# API Security
API_SECRET_KEY=changeme
JWT_SECRET=changeme

# Component-specific secrets
"""
        
        for spec in required_secrets:
            if spec.name not in ["DATABASE_PASSWORD", "REDIS_PASSWORD", "API_SECRET_KEY", "JWT_SECRET"]:
                template += f"\n# {spec.description}\n"
                template += f"{spec.name}=changeme\n"
        
        # Substitute template variables with generator_settings
        from autocoder_cc.generators.config import generator_settings
        template = template.format(
            postgres_host=generator_settings.postgres_host,
            postgres_port=generator_settings.postgres_port,
            redis_host=generator_settings.redis_host,
            redis_port=generator_settings.redis_port
        )
        
        return template
    
    def _generate_secret(self, spec: SecretSpec) -> str:
        """Generate a secret based on its specification"""
        if spec.type == "password":
            return self._generate_password(spec.length)
        elif spec.type == "api_key":
            return self._generate_api_key(spec.length, spec.prefix)
        elif spec.type == "jwt_secret":
            return self._generate_jwt_secret()
        elif spec.type == "encryption_key":
            return self._generate_encryption_key()
        else:
            # Default to secure random string
            return self._generate_secure_string(spec.length)
    
    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure password"""
        # Use all character types for maximum entropy
        charset = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(charset) for _ in range(length))
        
        # Ensure it has at least one of each type
        if not any(c.isupper() for c in password):
            password = secrets.choice(string.ascii_uppercase) + password[1:]
        if not any(c.islower() for c in password):
            password = password[0] + secrets.choice(string.ascii_lowercase) + password[2:]
        if not any(c.isdigit() for c in password):
            password = password[:2] + secrets.choice(string.digits) + password[3:]
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:3] + secrets.choice("!@#$%^&*") + password[4:]
        
        return password
    
    def _generate_api_key(self, length: int = 32, prefix: Optional[str] = None) -> str:
        """Generate an API key"""
        key = secrets.token_urlsafe(length)
        if prefix:
            return f"{prefix}_{key}"
        return key
    
    def _generate_jwt_secret(self) -> str:
        """Generate a JWT secret"""
        # Use 256 bits of entropy for HS256
        return secrets.token_hex(32)
    
    def _generate_encryption_key(self) -> str:
        """Generate an encryption key"""
        # 32 bytes for AES-256
        return base64.b64encode(secrets.token_bytes(32)).decode()
    
    def _generate_secure_string(self, length: int = 32) -> str:
        """Generate a secure random string"""
        return secrets.token_urlsafe(length)


def create_production_secrets(system_name: str, components: List[Any]) -> Dict[str, Any]:
    """
    Create production-ready secrets for a system.
    
    Args:
        system_name: Name of the system
        components: List of system components
        
    Returns:
        Dictionary containing all secrets and manifests
    """
    manager = SecretsManager()
    
    # Determine required secrets based on components
    required_secrets = [
        SecretSpec("DATABASE_PASSWORD", "password", "PostgreSQL password"),
        SecretSpec("REDIS_PASSWORD", "password", "Redis password"),
        SecretSpec("API_SECRET_KEY", "api_key", "API authentication key"),
        SecretSpec("JWT_SECRET", "jwt_secret", "JWT signing secret"),
    ]
    
    # Add component-specific secrets
    for component in components:
        if component.type == "APIEndpoint":
            required_secrets.append(
                SecretSpec(f"{component.name.upper()}_API_KEY", "api_key", 
                          f"API key for {component.name}")
            )
        elif component.configuration.get("requires_encryption"):
            required_secrets.append(
                SecretSpec(f"{component.name.upper()}_ENCRYPTION_KEY", "encryption_key",
                          f"Encryption key for {component.name}")
            )
    
    # Generate secrets
    secrets_dict = manager.generate_secrets_manifest(system_name, required_secrets)
    
    # Validate secrets
    errors = manager.validate_secrets(secrets_dict)
    if errors:
        raise ValueError(f"Secret validation failed: {errors}")
    
    # Generate manifests
    k8s_manifest = manager.generate_k8s_secret_manifest(system_name, system_name, secrets_dict)
    sealed_template = manager.generate_sealed_secret_template(system_name, system_name, required_secrets)
    env_template = manager.generate_env_template(required_secrets)
    
    return {
        "secrets": secrets_dict,
        "k8s_manifest": k8s_manifest,
        "sealed_template": sealed_template,
        "env_template": env_template,
        "required_secrets": required_secrets
    }


if __name__ == "__main__":
    # Test the secrets manager
    manager = SecretsManager()
    
    test_secrets = [
        SecretSpec("DATABASE_PASSWORD", "password", "Database password"),
        SecretSpec("API_KEY", "api_key", "API key", prefix="myapp"),
        SecretSpec("JWT_SECRET", "jwt_secret", "JWT secret"),
    ]
    
    # Generate secrets
    secrets = manager.generate_secrets_manifest("test-system", test_secrets)
    print("Generated secrets:")
    for name, value in secrets.items():
        print(f"  {name}: {value[:10]}... (length: {len(value)})")
    
    # Validate good secrets
    errors = manager.validate_secrets(secrets)
    print(f"\nValidation errors: {errors if errors else 'None'}")
    
    # Test with bad secrets
    bad_secrets = {
        "PASSWORD": "password123",
        "API_KEY": "your-api-key-here",
        "SECRET": "changeme"
    }
    
    errors = manager.validate_secrets(bad_secrets)
    print(f"\nBad secrets validation errors: {errors}")