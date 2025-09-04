"""
Autocoder v5.0 Production Deployment Tools

Provides production-ready deployment generation with:
- Complete K8s manifests including Kafka and Redis
- Secure secrets management
- Environment-aware configuration
"""

from .secrets_manager import SecretsManager, SecretSpec, create_production_secrets
from .environment_config import (
    Environment,
    EnvironmentConfig,
    EnvironmentConfigManager,
    ServiceEndpoint,
    ResourceLimits,
    ResourceRequests,
    create_environment_configs
)

__all__ = [
    'SecretsManager',
    'SecretSpec',
    'create_production_secrets',
    'Environment',
    'EnvironmentConfig', 
    'EnvironmentConfigManager',
    'ServiceEndpoint',
    'ResourceLimits',
    'ResourceRequests',
    'create_environment_configs'
]