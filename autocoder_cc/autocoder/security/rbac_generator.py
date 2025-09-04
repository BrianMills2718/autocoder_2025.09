from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
RBAC Configuration Generator
============================

Generates RBAC configuration files for generated systems.
Creates roles, permissions, and default security policies.
"""
import yaml
from typing import Dict, Any, List
from .models import RBACConfig, Role, Permission, ActionType, DEFAULT_RBAC_CONFIG


class RBACConfigGenerator:
    """Generates RBAC configuration files for systems."""
    
    def generate_rbac_config(self, system_name: str, components: List[Dict[str, Any]]) -> str:
        """
        Generate RBAC configuration YAML file for a system.
        
        Args:
            system_name: Name of the system
            components: List of system components to generate permissions for
            
        Returns:
            RBAC configuration as YAML string
        """
        # Start with default config
        rbac_config = DEFAULT_RBAC_CONFIG.dict()
        
        # Generate resource-specific permissions based on components
        resources = self._extract_resources_from_components(components)
        
        # Create resource-specific roles
        resource_roles = self._generate_resource_roles(resources)
        
        # Add generated roles to config
        rbac_config['roles'].update(resource_roles)
        
        # Add system-specific metadata
        rbac_config['system'] = {
            'name': system_name,
            'version': '1.0.0',
            'generated_at': '2025-01-13T00:00:00Z',
            'description': f'RBAC configuration for {system_name}'
        }
        
        return yaml.dump(rbac_config, default_flow_style=False, sort_keys=True)
    
    def _extract_resources_from_components(self, components: List[Dict[str, Any]]) -> List[str]:
        """Extract resource names from system components."""
        resources = set()
        
        for component in components:
            # Extract resource name from component name or type
            comp_name = component.get('name', '')
            comp_type = component.get('type', '')
            
            # Convert component names to resource names
            if 'api' in comp_name.lower() or comp_type == 'APIEndpoint':
                # API components can manage multiple resources
                if 'user' in comp_name.lower():
                    resources.add('users')
                elif 'order' in comp_name.lower():
                    resources.add('orders')
                elif 'product' in comp_name.lower():
                    resources.add('products')
                elif 'customer' in comp_name.lower():
                    resources.add('customers')
                else:
                    # Generic resource based on component name
                    resource_name = comp_name.replace('_api', '').replace('_endpoint', '')
                    resources.add(resource_name)
            
            # Store components represent data resources
            elif comp_type == 'Store':
                resource_name = comp_name.replace('_store', '').replace('_db', '')
                resources.add(resource_name)
        
        # Add common system resources
        resources.update(['system', 'health', 'metrics'])
        
        return list(resources)
    
    def _generate_resource_roles(self, resources: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate resource-specific roles."""
        roles = {}
        
        # Create manager roles for each resource
        for resource in resources:
            if resource in ['system', 'health', 'metrics']:
                continue  # Skip system resources
                
            # Resource manager role
            manager_role_name = f"{resource}_manager"
            roles[manager_role_name] = {
                'name': manager_role_name,
                'description': f'Manager for {resource} resource',
                'permissions': [
                    {'resource': resource, 'action': 'create'},
                    {'resource': resource, 'action': 'read'},
                    {'resource': resource, 'action': 'update'},
                    {'resource': resource, 'action': 'delete'},
                    {'resource': resource, 'action': 'list'},
                ],
                'inherits_from': None
            }
            
            # Resource viewer role
            viewer_role_name = f"{resource}_viewer"
            roles[viewer_role_name] = {
                'name': viewer_role_name,
                'description': f'Read-only access to {resource} resource',
                'permissions': [
                    {'resource': resource, 'action': 'read'},
                    {'resource': resource, 'action': 'list'},
                ],
                'inherits_from': None
            }
        
        # Service account role for internal operations
        roles['service_account'] = {
            'name': 'service_account',
            'description': 'Service account for inter-service communication',
            'permissions': [
                {'resource': 'health', 'action': 'read'},
                {'resource': 'metrics', 'action': 'read'},
                {'resource': '*', 'action': 'read'},  # Read access to all resources
            ],
            'inherits_from': None
        }
        
        return roles
    
    def generate_user_examples(self) -> str:
        """Generate example user configurations."""
        users = {
            'users': {
                'admin_user': {
                    'user_id': 'admin_001',
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'full_name': 'System Administrator',
                    'roles': ['admin'],
                    'permissions': [],
                    'is_active': True
                },
                'regular_user': {
                    'user_id': 'user_001',
                    'username': 'user',
                    'email': 'user@example.com',
                    'full_name': 'Regular User',
                    'roles': ['user'],
                    'permissions': [],
                    'is_active': True
                },
                'readonly_user': {
                    'user_id': 'readonly_001',
                    'username': 'readonly',
                    'email': 'readonly@example.com',
                    'full_name': 'Read-Only User',
                    'roles': ['readonly'],
                    'permissions': [],
                    'is_active': True
                }
            },
            'note': 'Example users for testing. In production, users should be managed through secure user management system.'
        }
        
        return yaml.dump(users, default_flow_style=False, sort_keys=True)
    
    def generate_security_middleware(self, system_name: str) -> str:
        """Generate security middleware code for FastAPI."""
        return f'''#!/usr/bin/env python3
"""
Security Middleware for {system_name}
====================================

Automatically generated security middleware that enforces RBAC policies.
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import List, Optional
import logging

from autocoder_cc.security.decorators import get_current_user, User
from autocoder_cc.security.models import RBACConfig
import yaml


logger = get_logger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """RBAC enforcement middleware for FastAPI."""
    
    def __init__(self, app: FastAPI, rbac_config_path: str = "rbac.yaml"):
        super().__init__(app)
        self.rbac_config = self._load_rbac_config(rbac_config_path)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {{
            "/health",
            "/docs", 
            "/openapi.json",
            "/redoc",
            "/login",
            "/register"
        }}
    
    def _load_rbac_config(self, config_path: str) -> RBACConfig:
        """Load RBAC configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return RBACConfig(**config_data)
        except Exception as e:
            logger.error(f"Failed to load RBAC config: {{e}}")
            # Return default config as fallback
            from autocoder_cc.security.models import DEFAULT_RBAC_CONFIG
            return DEFAULT_RBAC_CONFIG
    
    async def dispatch(self, request: Request, call_next):
        """Process request through RBAC middleware."""
        # Skip public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)
        
        # Skip preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Extract and validate user from token
            # This will raise HTTPException if invalid
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header",
                    headers={{"WWW-Authenticate": "Bearer"}},
                )
            
            # User validation handled by get_current_user dependency
            # Middleware just ensures token is present
            logger.debug(f"Processing authenticated request to {{request.url.path}}")
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Authentication error: {{e}}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={{"WWW-Authenticate": "Bearer"}},
            )
        
        # Continue to endpoint (where RBAC decorators will handle authorization)
        return await call_next(request)


def setup_security_middleware(app: FastAPI, rbac_config_path: str = "rbac.yaml") -> None:
    """Set up security middleware for the FastAPI app."""
    logger.info("Setting up RBAC security middleware")
    app.add_middleware(RBACMiddleware, rbac_config_path=rbac_config_path)
'''