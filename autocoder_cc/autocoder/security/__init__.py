#!/usr/bin/env python3
"""
Security Module
===============

RBAC and JWT authentication components for generated systems.
"""

from .decorators import (
    requires_role,
    requires_permission, 
    requires_any_role,
    get_current_user,
    generate_token,
    User
)

from .models import (
    Permission,
    Role,
    UserProfile,
    LoginRequest,
    LoginResponse,
    TokenValidationResponse,
    RBACConfig,
    DEFAULT_RBAC_CONFIG,
    ActionType
)

from .rbac_generator import RBACConfigGenerator
from .sealed_secrets import (
    SealedSecretsManager,
    SecretField,
    SealedSecretManifest,
    create_sealed_secrets_for_system
)

__all__ = [
    # Decorators
    'requires_role',
    'requires_permission',
    'requires_any_role',
    'get_current_user',
    'generate_token',
    'User',
    
    # Models
    'Permission',
    'Role',
    'UserProfile',
    'LoginRequest',
    'LoginResponse',
    'TokenValidationResponse',
    'RBACConfig',
    'DEFAULT_RBAC_CONFIG',
    'ActionType',
    
    # Generators
    'RBACConfigGenerator',
    
    # Sealed Secrets
    'SealedSecretsManager',
    'SecretField',
    'SealedSecretManifest',
    'create_sealed_secrets_for_system'
]