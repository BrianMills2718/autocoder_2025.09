from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Security Authorization Decorators
=================================

Implements role-based access control (RBAC) decorators for FastAPI endpoints.
Used by generated API endpoints to enforce permission-based authorization.
"""
import functools
import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

from autocoder_cc.generators.config import generator_settings


logger = get_logger(__name__)


class RBACError(Exception):
    """Exception raised for RBAC-related errors."""
    pass


class User:
    """User model with permissions and roles."""
    
    def __init__(self, user_id: str, username: str, roles: List[str] = None, permissions: List[str] = None):
        self.user_id = user_id
        self.username = username
        self.roles = roles or []
        self.permissions = permissions or []
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles or "admin" in self.roles  # admin has all roles
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has permission for a resource action."""
        # Admin has all permissions
        if "admin" in self.roles:
            return True
        
        # Check explicit permissions
        permission = f"{resource}:{action}"
        if permission in self.permissions:
            return True
        
        # Check wildcard permissions
        if f"{resource}:*" in self.permissions or f"*:{action}" in self.permissions:
            return True
        
        return False


# Security instance for token verification
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Extract and validate JWT token, return User object.
    Used as FastAPI dependency for authenticated endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            generator_settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        
        # Check token expiration
        if "exp" in payload:
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Extract user information
        user_id = payload.get("sub")
        username = payload.get("username", user_id)
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = User(user_id, username, roles, permissions)
        logger.debug(f"Authenticated user: {user.username} with roles: {user.roles}")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def requires_role(required_role: str):
    """
    Decorator that requires a specific role.
    
    Usage:
        @requires_role("admin")
        async def admin_endpoint(user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find user parameter
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # Also check kwargs for user
            if not user:
                user = kwargs.get('user')
            
            if not user or not isinstance(user, User):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User not found in request - ensure get_current_user dependency is used"
                )
            
            if not user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role '{required_role}' not found. User roles: {user.roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def requires_permission(resource: str, action: str):
    """
    Decorator that requires a specific permission.
    
    Usage:
        @requires_permission("orders", "create")
        async def create_order(user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find user parameter
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # Also check kwargs for user
            if not user:
                user = kwargs.get('user')
            
            if not user or not isinstance(user, User):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User not found in request - ensure get_current_user dependency is used"
                )
            
            if not user.has_permission(resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {resource}:{action}. User permissions: {user.permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def requires_any_role(*roles: str):
    """
    Decorator that requires any of the specified roles.
    
    Usage:
        @requires_any_role("admin", "moderator")
        async def moderation_endpoint(user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find user parameter
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # Also check kwargs for user
            if not user:
                user = kwargs.get('user')
            
            if not user or not isinstance(user, User):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User not found in request - ensure get_current_user dependency is used"
                )
            
            if not any(user.has_role(role) for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required one of roles {list(roles)}, but user has: {user.roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def generate_token(user_id: str, username: str, roles: List[str] = None, 
                  permissions: List[str] = None, expires_hours: int = 24) -> str:
    """
    Generate JWT token for authenticated user.
    
    Args:
        user_id: Unique user identifier
        username: Human-readable username
        roles: List of user roles
        permissions: List of explicit permissions
        expires_hours: Token expiration in hours
    
    Returns:
        JWT token string
    """
    from datetime import timedelta
    
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles or [],
        "permissions": permissions or [],
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(payload, generator_settings.jwt_secret_key, algorithm="HS256")