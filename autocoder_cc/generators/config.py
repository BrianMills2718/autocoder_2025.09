"""
Generator Configuration Settings
Enterprise Roadmap v3 Phase 0: Centralized Configuration System
Inherits from core config, NO duplicate hardcoded values.
"""
from typing import Optional, Dict, Any
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from autocoder_cc.core.config import settings as core_settings


class GeneratorSettings(BaseSettings):
    """Settings for code generators - inherits from centralized core config"""
    
    model_config = SettingsConfigDict(
        env_prefix="GENERATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Generator-specific settings (not in core config)
    default_api_port: int = Field(default=8000, env="DEFAULT_API_PORT", description="Default API port for generators")
    api_base_url: str = Field(default="http://localhost", env="API_BASE_URL", description="Base URL for API endpoints")
    api_host: str = Field(default="0.0.0.0", description="Default API host")
    
    # Use core config values - NO duplication
    @property
    def api_prefix(self) -> str:
        """Get API prefix from core configuration"""
        return core_settings.DEFAULT_API_PREFIX
    
    @property 
    def api_port(self) -> int:
        """Get API port from core configuration or fallback"""
        return getattr(core_settings, 'DEFAULT_API_PORT', self.default_api_port)
    
    # Generator-specific settings (minimal duplication)
    postgres_test_db: str = Field(default="test_db", env="POSTGRES_TEST_DB", description="PostgreSQL test database name")
    
    # All service URLs use core configuration - NO hardcoded values
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL URL from core configuration"""
        return core_settings.DEFAULT_POSTGRES_URL
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL from core configuration"""
        return core_settings.DEFAULT_REDIS_URL
    
    @property
    def rabbitmq_url(self) -> str:
        """Get RabbitMQ URL from core configuration"""
        return core_settings.DEFAULT_RABBITMQ_URL
    
    @property
    def kafka_brokers(self) -> str:
        """Get Kafka brokers from core configuration"""
        return core_settings.DEFAULT_KAFKA_BROKERS
    
    @property
    def metrics_port(self) -> int:
        """Get metrics port from core configuration"""
        return core_settings.METRICS_PORT
    
    @property
    def postgres_port(self) -> int:
        """Get PostgreSQL port from core configuration"""
        return getattr(core_settings, 'POSTGRES_PORT', 5432)
    
    @property
    def redis_port(self) -> int:
        """Get Redis port from core configuration"""
        return getattr(core_settings, 'REDIS_PORT', 6379)
    
    @property
    def kafka_port(self) -> int:
        """Get Kafka port from core configuration"""
        return getattr(core_settings, 'KAFKA_PORT', 9092)
    
    @property
    def zookeeper_port(self) -> int:
        """Get Zookeeper port from core configuration"""
        return getattr(core_settings, 'ZOOKEEPER_PORT', 2181)
    
    # Generator-specific overrides (use core config as much as possible)
    base_domain: str = Field(default="example.com", description="Base domain for services")
    
    # All other settings use core configuration
    @property
    def docker_registry(self) -> str:
        """Get Docker registry from core configuration"""
        return core_settings.DOCKER_REGISTRY
    
    @property
    def default_timeout_seconds(self) -> int:
        """Get default timeout from core configuration"""
        return core_settings.DEFAULT_COMPONENT_TIMEOUT
    
    @property
    def jwt_secret_key(self) -> str:
        """Get JWT secret key from core configuration"""
        return core_settings.DEFAULT_JWT_SECRET_KEY
    
    @model_validator(mode='after')
    def validate_centralized_config(self) -> 'GeneratorSettings':
        """Validate that generator config properly uses centralized configuration"""
        # Core configuration is validated in autocoder.core.config
        # This generator config should delegate all validation to core
        try:
            core_settings.validate_production_settings()
        except Exception as e:
            raise ValueError(f"Core configuration validation failed: {e}")
        
        return self
    
    # Utility methods using centralized configuration
    def get_postgres_url(self, db_name: Optional[str] = None) -> str:
        """Get PostgreSQL connection URL from centralized config"""
        if db_name:
            # Parse base URL and replace database name
            base_url = self.postgres_url
            if '/' in base_url:
                return base_url.rsplit('/', 1)[0] + '/' + db_name
        return self.postgres_url
    
    def get_redis_url(self, db: Optional[int] = None) -> str:
        """Get Redis connection URL from centralized config"""
        if db is not None:
            # Parse base URL and replace database number
            base_url = self.redis_url
            if '/' in base_url:
                return base_url.rsplit('/', 1)[0] + '/' + str(db)
        return self.redis_url
    
    def get_rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL from centralized config"""
        return self.rabbitmq_url
    
    def get_service_url(self, service_name: str, port: Optional[int] = None) -> str:
        """Get URL for a service using centralized config"""
        service_port = port or self.api_port
        return f"http://{service_name}:{service_port}"


# Global instance - will load from environment
generator_settings = GeneratorSettings()