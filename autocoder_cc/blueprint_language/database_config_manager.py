#!/usr/bin/env python3
"""
Database Configuration Manager for Phase 2C Implementation
=========================================================

Provides consistent database configuration across all system components.
Eliminates configuration inconsistencies and ensures proper database connectivity.

Key Features:
- Unified database configuration schema
- Automatic configuration validation and normalization
- Environment-aware database connection details
- Consistent defaults and connection pooling parameters
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class DatabaseConnectionConfig:
    """Standardized database connection configuration"""
    database_type: str  # postgresql, mysql, sqlite, etc.
    host: str
    port: int
    database_name: str
    username: str
    password: Optional[str] = None  # Required for production, optional for dev
    
    # Connection pool settings
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    
    # Additional database-specific settings
    ssl_mode: str = "prefer"  # PostgreSQL SSL mode
    charset: str = "utf8mb4"  # MySQL charset
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for component configuration"""
        return {
            "database_type": self.database_type,
            "db_host": self.host,
            "db_port": self.port,
            "db_name": self.database_name,
            "db_user": self.username,
            "db_password": self.password,
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "ssl_mode": self.ssl_mode,
            "charset": self.charset
        }
    
    def get_connection_string(self) -> str:
        """Generate database connection string"""
        if self.database_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == "mysql":
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == "sqlite":
            return f"sqlite:///{self.database_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")


@dataclass
class SystemDatabaseConfig:
    """System-wide database configuration management"""
    default_database: DatabaseConnectionConfig
    component_databases: Dict[str, DatabaseConnectionConfig] = field(default_factory=dict)
    environment: str = "development"
    
    def get_database_config(self, component_name: str) -> DatabaseConnectionConfig:
        """Get database configuration for specific component"""
        return self.component_databases.get(component_name, self.default_database)
    
    def add_component_database(self, component_name: str, config: DatabaseConnectionConfig):
        """Add component-specific database configuration"""
        self.component_databases[component_name] = config
    
    def to_system_config(self) -> Dict[str, Any]:
        """Convert to system configuration format"""
        config = {
            "database": {
                "default": self.default_database.to_dict(),
                "environment": self.environment
            }
        }
        
        if self.component_databases:
            config["database"]["components"] = {
                name: db_config.to_dict() 
                for name, db_config in self.component_databases.items()
            }
        
        return config


class DatabaseConfigManager:
    """
    Phase 2C Database Configuration Manager
    
    Centralizes database configuration management and ensures consistency
    across all system components and deployment environments.
    """
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
        # Default database configurations by environment
        self.environment_defaults = {
            "development": {
                "host": "localhost",
                "port": 5432,
                "database_name": "dev_db",
                "username": "dev_user",
                "password": "dev_password",
                "ssl_mode": "disable"
            },
            "production": {
                "host": "postgres",  # Docker service name
                "port": 5432,
                "database_name": "app_db",
                "username": "postgres",
                "password": None,  # Must be provided via environment
                "ssl_mode": "require"
            },
            "test": {
                "host": "localhost",
                "port": 5432,
                "database_name": "test_db",
                "username": "test_user",
                "password": "test_password",
                "ssl_mode": "disable"
            }
        }
    
    def create_database_config(
        self, 
        database_type: str = "postgresql",
        component_name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> DatabaseConnectionConfig:
        """
        Create standardized database configuration
        
        Args:
            database_type: Type of database (postgresql, mysql, sqlite)
            component_name: Optional component-specific configuration
            custom_config: Override specific configuration values
            
        Returns:
            DatabaseConnectionConfig: Standardized database configuration
        """
        # Get environment defaults
        env_defaults = self.environment_defaults.get(self.environment, self.environment_defaults["development"])
        
        # Create base configuration
        config_dict = {
            "database_type": database_type,
            **env_defaults
        }
        
        # Apply custom configuration overrides
        if custom_config:
            config_dict.update(custom_config)
        
        # Component-specific adjustments
        if component_name:
            config_dict["database_name"] = f"{config_dict['database_name']}_{component_name}"
        
        # Handle database type specific defaults
        if database_type == "mysql":
            config_dict["port"] = config_dict.get("port", 3306)
        elif database_type == "sqlite":
            config_dict["host"] = ""
            config_dict["port"] = 0
            config_dict["username"] = ""
            config_dict["password"] = ""
        
        return DatabaseConnectionConfig(
            database_type=config_dict["database_type"],
            host=config_dict["host"],
            port=config_dict["port"],
            database_name=config_dict["database_name"],
            username=config_dict["username"],
            password=config_dict["password"],
            ssl_mode=config_dict.get("ssl_mode", "prefer"),
            charset=config_dict.get("charset", "utf8mb4")
        )
    
    def normalize_component_config(self, component_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize component database configuration to standard format
        
        Handles legacy configuration formats and ensures consistency.
        
        Args:
            component_config: Raw component configuration
            
        Returns:
            Dict[str, Any]: Normalized configuration with standard database fields
        """
        normalized = component_config.copy()
        
        # Extract database type from various possible fields
        database_type = self._extract_database_type(component_config)
        
        # Create standardized database configuration
        db_config = self.create_database_config(database_type)
        
        # Merge with existing configuration, preferring explicit values
        db_dict = db_config.to_dict()
        for key, value in db_dict.items():
            if key not in normalized or normalized[key] is None:
                normalized[key] = value
        
        # Clean up legacy fields
        legacy_fields = ["storage_type", "_database"]
        for field in legacy_fields:
            if field in normalized:
                self.logger.warning(f"Removing legacy database field: {field}")
                del normalized[field]
        
        return normalized
    
    def _extract_database_type(self, config: Dict[str, Any]) -> str:
        """Extract database type from various configuration formats"""
        
        # Check V5.0+ database configuration format
        if "_database" in config and isinstance(config["_database"], dict):
            db_config = config["_database"]
            if "type" in db_config:
                return db_config["type"].lower()
        
        # Check explicit database_type field
        if "database_type" in config:
            return config["database_type"].lower()
        
        # Check legacy storage_type field
        if "storage_type" in config:
            storage_type = config["storage_type"].lower()
            if storage_type in ["postgresql", "postgres"]:
                return "postgresql"
            elif storage_type in ["mysql"]:
                return "mysql"
            elif storage_type in ["sqlite"]:
                return "sqlite"
            return storage_type
        
        # Default to PostgreSQL
        return "postgresql"
    
    def generate_system_database_config(
        self, 
        components: List[Dict[str, Any]]
    ) -> SystemDatabaseConfig:
        """
        Generate system-wide database configuration
        
        Args:
            components: List of component configurations
            
        Returns:
            SystemDatabaseConfig: Complete system database configuration
        """
        # Create default database configuration
        default_db = self.create_database_config()
        
        system_config = SystemDatabaseConfig(
            default_database=default_db,
            environment=self.environment
        )
        
        # Process each component that requires database access
        for component in components:
            component_name = component.get("name", "unknown")
            component_type = component.get("type", "").lower()
            
            # Only configure database for Store components
            if component_type in ["store", "database", "repository"]:
                # Normalize component configuration
                normalized_config = self.normalize_component_config(component.get("config", {}))
                
                # Create component-specific database configuration
                db_config = self.create_database_config(
                    database_type=normalized_config.get("database_type", "postgresql"),
                    component_name=component_name,
                    custom_config=normalized_config
                )
                
                system_config.add_component_database(component_name, db_config)
        
        return system_config
    
    def validate_database_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate database configuration for completeness and consistency
        
        Args:
            config: Database configuration to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields for production environment
        if self.environment == "production":
            required_fields = ["db_host", "db_port", "db_name", "db_user"]
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"Missing required database field for production: {field}")
            
            # Password is required for production
            if not config.get("db_password"):
                errors.append("db_password is required for production environment")
        
        # Validate database type
        database_type = config.get("database_type", "").lower()
        supported_types = ["postgresql", "mysql", "sqlite"]
        if database_type not in supported_types:
            errors.append(f"Unsupported database type: {database_type}. Supported types: {supported_types}")
        
        # Validate port numbers
        port = config.get("db_port")
        if port and (not isinstance(port, int) or port <= 0 or port > 65535):
            errors.append(f"Invalid database port: {port}. Must be integer between 1-65535")
        
        return errors
    
    def update_system_config_file(self, config_file: Path, system_db_config: SystemDatabaseConfig):
        """
        Update system configuration file with database configuration
        
        Args:
            config_file: Path to system configuration YAML file
            system_db_config: System database configuration to apply
        """
        # Load existing configuration
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing_config = yaml.safe_load(f) or {}
        else:
            existing_config = {}
        
        # Merge database configuration
        db_config = system_db_config.to_system_config()
        existing_config.update(db_config)
        
        # Apply component-specific database configurations
        for component_name, db_config in system_db_config.component_databases.items():
            if component_name not in existing_config:
                existing_config[component_name] = {}
            existing_config[component_name].update(db_config.to_dict())
        
        # Write updated configuration
        with open(config_file, 'w') as f:
            yaml.dump(existing_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Updated system configuration file: {config_file}")


def get_database_config_manager(environment: str = "development") -> DatabaseConfigManager:
    """Factory function to create DatabaseConfigManager instance"""
    return DatabaseConfigManager(environment=environment)


# Example usage for testing
if __name__ == "__main__":
    import sys
    
    # Test database configuration manager
    manager = DatabaseConfigManager(environment="development")
    
    # Create sample component configurations
    components = [
        {
            "name": "task_store",
            "type": "Store",
            "config": {
                "database_type": "postgresql",
                "storage_type": "postgresql",  # Legacy field
                "table_name": "tasks"
            }
        },
        {
            "name": "user_store", 
            "type": "Store",
            "config": {
                "_database": {"type": "mysql"},  # V5.0+ format
                "table_name": "users"
            }
        }
    ]
    
    # Generate system database configuration
    system_config = manager.generate_system_database_config(components)
    
    print("=== System Database Configuration ===")
    print(f"Environment: {system_config.environment}")
    print(f"Default Database: {system_config.default_database}")
    print(f"Component Databases: {len(system_config.component_databases)}")
    
    for name, config in system_config.component_databases.items():
        print(f"  {name}: {config.database_type} at {config.host}:{config.port}")
        
        # Validate configuration
        errors = manager.validate_database_config(config.to_dict())
        if errors:
            print(f"    Validation errors: {errors}")
        else:
            print(f"    ✅ Configuration valid")