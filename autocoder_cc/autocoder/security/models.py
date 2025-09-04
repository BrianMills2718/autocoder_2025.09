#!/usr/bin/env python3
"""
Security Models
===============

Pydantic models for RBAC permissions, roles, and authentication.
Used by generated systems for security configuration and validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    """Standard CRUD actions for permissions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXECUTE = "execute"


class Permission(BaseModel):
    """Permission model for RBAC."""
    resource: str = Field(..., description="Resource identifier (e.g., 'orders', 'users')")
    action: ActionType = Field(..., description="Action type (create, read, update, delete, etc.)")
    conditions: Optional[Dict[str, Any]] = Field(default=None, description="Optional conditions for permission")
    
    @property
    def permission_string(self) -> str:
        """Get permission as string format 'resource:action'."""
        return f"{self.resource}:{self.action}"
    
    def __str__(self) -> str:
        return self.permission_string


class Role(BaseModel):
    """Role model for RBAC."""
    name: str = Field(..., description="Role name (e.g., 'admin', 'user', 'moderator')")
    description: Optional[str] = Field(default=None, description="Role description")
    permissions: List[Permission] = Field(default_factory=list, description="List of permissions")
    inherits_from: Optional[List[str]] = Field(default=None, description="Parent roles to inherit permissions from")
    
    def get_all_permissions(self, role_registry: Dict[str, 'Role'] = None) -> List[Permission]:
        """Get all permissions including inherited ones."""
        all_permissions = self.permissions.copy()
        
        if self.inherits_from and role_registry:
            for parent_role_name in self.inherits_from:
                if parent_role_name in role_registry:
                    parent_role = role_registry[parent_role_name]
                    parent_permissions = parent_role.get_all_permissions(role_registry)
                    all_permissions.extend(parent_permissions)
        
        # Remove duplicates
        unique_permissions = {}
        for perm in all_permissions:
            unique_permissions[perm.permission_string] = perm
        
        return list(unique_permissions.values())


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(default=None, description="User email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    roles: List[str] = Field(default_factory=list, description="Assigned role names")
    permissions: List[str] = Field(default_factory=list, description="Explicit permissions as 'resource:action'")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[str] = Field(default=None, description="Account creation timestamp")
    last_login: Optional[str] = Field(default=None, description="Last login timestamp")


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserProfile = Field(..., description="User profile information")


class TokenValidationResponse(BaseModel):
    """Token validation response."""
    valid: bool = Field(..., description="Whether token is valid")
    user: Optional[UserProfile] = Field(default=None, description="User profile if token is valid")
    error: Optional[str] = Field(default=None, description="Error message if token is invalid")


class RBACConfig(BaseModel):
    """RBAC configuration model."""
    roles: Dict[str, Role] = Field(default_factory=dict, description="Available roles")
    default_role: str = Field(default="user", description="Default role for new users")
    admin_role: str = Field(default="admin", description="Administrator role name")
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        return self.roles.get(role_name)
    
    def add_role(self, role: Role) -> None:
        """Add a new role."""
        self.roles[role.name] = role
    
    def get_user_permissions(self, user_roles: List[str]) -> List[Permission]:
        """Get all permissions for a user based on their roles."""
        all_permissions = []
        
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role:
                role_permissions = role.get_all_permissions(self.roles)
                all_permissions.extend(role_permissions)
        
        # Remove duplicates
        unique_permissions = {}
        for perm in all_permissions:
            unique_permissions[perm.permission_string] = perm
        
        return list(unique_permissions.values())


# Default RBAC configuration
DEFAULT_RBAC_CONFIG = RBACConfig(
    roles={
        "admin": Role(
            name="admin",
            description="Administrator with full access",
            permissions=[
                Permission(resource="*", action=ActionType.CREATE),
                Permission(resource="*", action=ActionType.READ),
                Permission(resource="*", action=ActionType.UPDATE),
                Permission(resource="*", action=ActionType.DELETE),
                Permission(resource="*", action=ActionType.LIST),
                Permission(resource="*", action=ActionType.EXECUTE),
            ]
        ),
        "user": Role(
            name="user",
            description="Standard user with limited access",
            permissions=[
                Permission(resource="profile", action=ActionType.READ),
                Permission(resource="profile", action=ActionType.UPDATE),
                Permission(resource="orders", action=ActionType.CREATE),
                Permission(resource="orders", action=ActionType.READ),
                Permission(resource="orders", action=ActionType.LIST),
            ]
        ),
        "readonly": Role(
            name="readonly",
            description="Read-only access to most resources",
            permissions=[
                Permission(resource="*", action=ActionType.READ),
                Permission(resource="*", action=ActionType.LIST),
            ]
        )
    },
    default_role="user",
    admin_role="admin"
)