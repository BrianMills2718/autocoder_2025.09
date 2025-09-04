"""Configuration Protocol Interfaces

Defines protocol interfaces for dependency injection of configuration services.
This eliminates the need for function-level imports by providing clear contracts
for configuration access throughout the system.
"""

from typing import Protocol, Optional


class ConfigProtocol(Protocol):
    """Protocol interface for configuration services
    
    This protocol defines the configuration interface that components can depend on
    through dependency injection, eliminating the need for direct imports of
    the settings object inside function bodies.
    """
    
    # Core Configuration Properties
    @property
    def ENVIRONMENT(self) -> str: ...
    
    @property
    def DEBUG_MODE(self) -> bool: ...
    
    # Infrastructure Service Ports
    @property
    def REDIS_PORT(self) -> int: ...
    
    @property
    def POSTGRES_PORT(self) -> int: ...
    
    @property
    def KAFKA_PORT(self) -> int: ...
    
    @property
    def ZOOKEEPER_PORT(self) -> int: ...
    
    # Monitoring and Observability
    @property
    def JAEGER_AGENT_HOST(self) -> str: ...
    
    @property
    def JAEGER_AGENT_PORT(self) -> int: ...
    
    @property
    def METRICS_PORT(self) -> int: ...
    
    @property
    def PROMETHEUS_URL(self) -> str: ...
    
    # Database Configuration
    @property
    def DEFAULT_POSTGRES_URL(self) -> Optional[str]: ...
    
    @property
    def DEFAULT_REDIS_URL(self) -> Optional[str]: ...
    
    # Message Bus Configuration
    @property
    def DEFAULT_KAFKA_BROKERS(self) -> Optional[str]: ...
    
    @property
    def KAFKA_BROKERS(self) -> str: ...
    
    # Security Configuration
    @property
    def JWT_SECRET_KEY(self) -> str: ...
    
    # LLM Configuration
    @property
    def OPENAI_API_KEY(self) -> Optional[str]: ...
    
    @property
    def ANTHROPIC_API_KEY(self) -> Optional[str]: ...
    
    @property
    def GEMINI_API_KEY(self) -> Optional[str]: ...
    
    # Component Generation
    @property
    def MAX_RETRIES(self) -> int: ...
    
    @property
    def COMPONENT_GENERATION_TIMEOUT(self) -> int: ...
    
    @property
    def DEFAULT_COMPONENT_TIMEOUT(self) -> int: ...
    
    # Methods for dynamic configuration access
    def get_hash_based_port(self, component_name: str, system_name: str) -> int: ...
    
    def get_llm_api_key(self) -> Optional[str]: ...
    
    def get_llm_model(self) -> str: ...
    
    def get_llm_provider(self) -> str: ...
    
    def get_github_token(self) -> str: ...
    
    def has_aws_credentials(self) -> bool: ...
    
    def has_datadog_credentials(self) -> bool: ...
    
    def get_prometheus_url(self) -> str: ...
    
    def get_pipeline_config(self) -> dict: ...