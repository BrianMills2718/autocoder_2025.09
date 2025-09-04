#!/usr/bin/env python3
"""
Configuration Manager - Manages configuration across environments

Simple configuration management for deployment contexts.
"""
from typing import Dict, Any, Optional
from .config import Settings


class ConfigManager:
    """
    Manages configuration for deployments.
    
    This wraps the Settings class and provides additional
    configuration management capabilities.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize configuration manager"""
        self.settings = settings or Settings()
        self._overrides: Dict[str, Any] = {}
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check overrides first
        if key in self._overrides:
            return self._overrides[key]
            
        # Check settings
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
            
        return default
    
    def set_override(self, key: str, value: Any):
        """
        Set a configuration override.
        
        Args:
            key: Configuration key
            value: Override value
        """
        self._overrides[key] = value
    
    def clear_overrides(self):
        """Clear all configuration overrides"""
        self._overrides.clear()
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Get configuration for a specific environment.
        
        Args:
            environment: Environment name (development/staging/production)
            
        Returns:
            Environment-specific configuration
        """
        base_config = {
            "environment": environment,
            "openai_api_key": self.get("OPENAI_API_KEY"),
            "openai_model": self.get("OPENAI_MODEL", "o3"),
            "log_level": self.get("LOG_LEVEL", "INFO"),
        }
        
        # Environment-specific overrides
        if environment == "development":
            base_config.update({
                "debug": True,
                "log_level": "DEBUG",
                "enable_profiling": True,
            })
        elif environment == "production":
            base_config.update({
                "debug": False,
                "log_level": "WARNING",
                "enable_monitoring": True,
            })
            
        return base_config