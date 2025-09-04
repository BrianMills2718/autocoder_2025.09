from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import pathlib
import os
import sys

class Settings(BaseSettings):
    """Centralized configuration for Autocoder V5.2 - Enterprise Edition
    
    This configuration follows the Enterprise Roadmap v2 requirements:
    - NO hardcoded values in the codebase
    - All configuration loaded from environment or .env file
    - Validated using Pydantic for type safety
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "o3"  # Use O3 reasoning model for production
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # GitHub API Configuration
    GITHUB_TOKEN: Optional[str] = Field(
        default=None,
        description="GitHub API token for system generation - REQUIRED for full functionality",
        env="GITHUB_TOKEN"
    )

    # AWS Cost Explorer API Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID for Cost Explorer API - Optional for enhanced observability",
        env="AWS_ACCESS_KEY_ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key for Cost Explorer API - Optional for enhanced observability",
        env="AWS_SECRET_ACCESS_KEY"
    )

    # Datadog API Configuration
    DATADOG_API_KEY: Optional[str] = Field(
        default=None,
        description="Datadog API key for monitoring cost data - Optional for enhanced observability",
        env="DATADOG_API_KEY"
    )
    DATADOG_APP_KEY: Optional[str] = Field(
        default=None,
        description="Datadog Application key for monitoring cost data - Optional for enhanced observability",
        env="DATADOG_APP_KEY"
    )

    # Port Configuration
    PORT_RANGE_START: int = 8000
    PORT_RANGE_END: int = 8100
    
    # Infrastructure Service Ports
    REDIS_PORT: Optional[int] = Field(default=None, env="REDIS_PORT")
    POSTGRES_PORT: Optional[int] = Field(default=None, env="POSTGRES_PORT") 
    KAFKA_PORT: Optional[int] = Field(default=None, env="KAFKA_PORT")
    ZOOKEEPER_PORT: Optional[int] = Field(default=None, env="ZOOKEEPER_PORT")

    # Database Configuration - Environment variables required for security
    DEFAULT_POSTGRES_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection URL - MUST be provided via POSTGRES_URL environment variable",
        env="POSTGRES_URL"
    )
    DEFAULT_MYSQL_URL: Optional[str] = Field(
        default=None,
        description="MySQL connection URL - MUST be provided via MYSQL_URL environment variable",
        env="MYSQL_URL"
    )
    DEFAULT_REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL - MUST be provided via REDIS_URL environment variable",
        env="REDIS_URL"
    )
    
    # Message Bus Configuration - Environment variables required for security
    DEFAULT_RABBITMQ_URL: Optional[str] = Field(
        default=None,
        description="RabbitMQ connection URL - MUST be provided via RABBITMQ_URL environment variable",
        env="RABBITMQ_URL"
    )
    DEFAULT_KAFKA_BROKERS: Optional[str] = Field(
        default=None,
        description="Kafka broker addresses - MUST be provided via KAFKA_BROKERS environment variable",
        env="KAFKA_BROKERS"
    )
    
    # Security Configuration - NO hardcoded secrets
    DEFAULT_JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="JWT secret key for token signing - MUST be provided via JWT_SECRET_KEY environment variable",
        env="JWT_SECRET_KEY"
    )
    DEFAULT_API_KEY_HEADER: str = "X-API-Key"
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG_MODE: bool = True

    # File System
    TEMP_DIR: str = str(pathlib.Path.cwd() / 'temp')
    OUTPUT_DIR: str = str(pathlib.Path.cwd() / 'generated_systems')

    # Validation Settings
    ENABLE_SEMANTIC_VALIDATION: bool = True
    ENABLE_INTEGRATION_VALIDATION: bool = True
    VALIDATION_TIMEOUT: int = 30
    VALIDATION_STRICT_MODE: bool = True  # Fail fast on any validation error

    # --- IR Feature Flags (Experimental – Phase 0.5) ---
    EMIT_TYPED_IR: bool = Field(default=False, env="EMIT_TYPED_IR", description="Emit typed IR file during generation")
    USE_TYPED_IR: bool = Field(default=False, env="USE_TYPED_IR", description="Consume typed IR as primary input (compiler mode)")
    CI_BLOCK_ON_IR: bool = Field(default=False, env="CI_BLOCK_ON_IR", description="Fail CI if IR validation fails")
    STRICT_IR: bool = Field(default=False, env="STRICT_IR", description="Abort generation on IR validation error, even outside CI")
    
    # Simplified main.py generation
    # Changed to False: Use proper SystemExecutionHarness instead of broken manual loading
    # The simple approach is incompatible with Phase 2A shared module relative imports
    SIMPLE_MAIN_PY: bool = Field(default=False, env="SIMPLE_MAIN_PY", description="Generate simplified main.py with minimal complexity (incompatible with shared modules)")

    # Component Generation
    MAX_RETRIES: int = 5  # Increased for better reliability with API timeouts
    RETRY_DELAY: float = 1.0
    COMPONENT_GENERATION_TIMEOUT: int = 60
    DEFAULT_COMPONENT_TIMEOUT: int = 30
    
    # Timeout Configuration (P1.0 Enhancement)
    RETRY_TIMEOUT_MULTIPLIER: Optional[float] = Field(default=None, env="RETRY_TIMEOUT_MULTIPLIER", description="Multiplier for progressive timeout scaling on retries")
    MAX_RETRY_TIMEOUT: Optional[int] = Field(default=None, env="MAX_RETRY_TIMEOUT", description="Maximum timeout for retry operations (seconds)")
    HEALTH_CHECK_TIMEOUT: Optional[int] = Field(default=None, env="HEALTH_CHECK_TIMEOUT", description="Timeout for provider health checks (seconds)")
    HEALTH_CHECK_CACHE_TTL: Optional[int] = Field(default=None, env="HEALTH_CHECK_CACHE_TTL", description="TTL for health check cache (seconds)")
    CIRCUIT_BREAKER_THRESHOLD: Optional[int] = Field(default=None, env="CIRCUIT_BREAKER_THRESHOLD", description="Failures before circuit opens")
    CIRCUIT_BREAKER_RECOVERY_TIME: Optional[int] = Field(default=None, env="CIRCUIT_BREAKER_RECOVERY_TIME", description="Time before attempting recovery (seconds)")
    ERROR_CONTEXT_MAX_LENGTH: Optional[int] = Field(default=None, env="ERROR_CONTEXT_MAX_LENGTH", description="Maximum length for error context strings")
    
    # Docker and Deployment Settings
    DOCKER_REGISTRY: str = "docker.io"
    DOCKER_IMAGE_PREFIX: str = "autocoder"
    K8S_NAMESPACE: str = "default"
    
    # API Settings
    DEFAULT_API_PREFIX: str = "/api/v1"
    API_VERSION: str = "1.0.0"
    SERVICE_NAME: str = "autocoder-generated-system"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    STRUCTURED_LOGGING: bool = True
    
    # Testing Settings
    TEST_TIMEOUT: int = 60
    ENABLE_CONTRACT_TESTING: bool = True
    
    # Monitoring and Observability
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_TRACING: bool = True
    TRACING_ENDPOINT: Optional[str] = Field(default=None, env="TRACING_ENDPOINT")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: Optional[int] = Field(default=None, env="JAEGER_AGENT_PORT")
    PROMETHEUS_URL: Optional[str] = Field(
        default=None,
        env="PROMETHEUS_URL",
        description="Prometheus server URL for metrics data - Optional for enhanced observability"
    )
    MONITORING_INTERVAL: int = 30  # seconds
    ERROR_MONITORING_INTERVAL: int = 5  # seconds for error recovery
    
    # Pipeline Robustness Configuration (NEW - Fix AutoCoder Pipeline Robustness)
    # REMOVED: ENABLE_GRACEFUL_DEGRADATION - Violates fail-fast principles
    SKIP_TEST_GENERATION: bool = Field(
        default=False,
        env="AUTOCODER_SKIP_TESTS",
        description="Skip test generation entirely"
    )
    AST_VALIDATION_MODE: Optional[str] = Field(
        default=None,
        env="AUTOCODER_AST_MODE",
        description="AST validation mode: strict, permissive, or disabled"
    )
    CONTINUE_ON_TEST_FAILURE: bool = Field(
        default=True,
        env="AUTOCODER_CONTINUE_ON_TEST_FAILURE",
        description="Continue pipeline execution when test generation fails"
    )
    CONTINUE_ON_SCHEMA_FAILURE: bool = Field(
        default=True,
        env="AUTOCODER_CONTINUE_ON_SCHEMA_FAILURE",
        description="Continue pipeline execution when schema generation fails"
    )
    PIPELINE_FAIL_FAST: bool = Field(
        default=False,
        env="AUTOCODER_PIPELINE_FAIL_FAST",
        description="Fail pipeline immediately on any error (disables graceful degradation)"
    )
    
    # --- Healing and Categorization Flags (ADR 033) ---
    HEAL_STORE_AS_SINK: bool = Field(
        default=True,  # Stop-gap enabled by default per ADR 033
        env="HEAL_STORE_AS_SINK",
        description="Stop-gap: Treat Store components as Sinks in blueprint healer"
    )
    CATEGORIZATION_UNIFIED: bool = Field(
        default=False,  # Unified categorization off by default for gradual rollout
        env="CATEGORIZATION_UNIFIED",
        description="Enable unified topology-first component categorization (ADR 033)"
    )
    RECONCILIATION_USE_CONTENTION_TERM: bool = Field(
        default=False,  # Contention term off by default for simplicity
        env="RECONCILIATION_USE_CONTENTION_TERM",
        description="Include terminal contention term in reconciliation cost function"
    )
    SHOW_DELTAS_IN_STOPGAP: bool = Field(
        default=False,
        env="SHOW_DELTAS_IN_STOPGAP",
        description="Show role delta warnings in CLI during stop-gap mode"
    )
    BOUNDARY_TERMINATION_ENABLED: bool = Field(
        default=False,  # Staged rollout
        env="BOUNDARY_TERMINATION_ENABLED",
        description="Enable boundary-terminal arc validation (VR1) instead of node-terminalism"
    )
    
    # --- VR1 Boundary-Termination Validation Settings ---
    ENABLE_VR1_VALIDATION: bool = Field(
        default=False,
        env="ENABLE_VR1_VALIDATION",
        description="Enable VR1 boundary-termination validation in system generation pipeline"
    )
    VR1_ENFORCEMENT_MODE: str = Field(
        default="warning",  # Options: disabled, warning, strict
        env="VR1_ENFORCEMENT_MODE", 
        description="VR1 validation enforcement mode: disabled, warning (show but don't block), strict (block on failures)"
    )
    FORCE_VR1_COMPLIANCE: bool = Field(
        default=False,
        env="FORCE_VR1_COMPLIANCE",
        description="Force all blueprints to VR1 compliance via auto-migration"
    )
    VR1_AUTO_HEALING: bool = Field(
        default=True,
        env="VR1_AUTO_HEALING",
        description="Enable automatic healing of VR1 validation failures"
    )
    VR1_TELEMETRY_ENABLED: bool = Field(
        default=True,
        env="VR1_TELEMETRY_ENABLED",
        description="Enable VR1 validation telemetry and metrics collection"
    )
    VR1_MAX_HOP_LIMIT: int = Field(
        default=10,
        env="VR1_MAX_HOP_LIMIT",
        description="Maximum hops allowed in VR1 path traversal"
    )
    VR1_MIGRATION_CONFIDENCE_THRESHOLD: float = Field(
        default=0.75,
        env="VR1_MIGRATION_CONFIDENCE_THRESHOLD",
        description="Confidence threshold for VR1 auto-migration decisions"
    )
    VR1_REPORT_PATH: Optional[str] = Field(
        default=None,
        env="VR1_REPORT_PATH",
        description="Path to save VR1 validation reports (optional)"
    )

    def __init__(self, **kwargs):
        """Initialize settings with development defaults only when explicitly in development mode."""
        super().__init__(**kwargs)
        # Development defaults ONLY when explicitly in development mode
        if self.ENVIRONMENT == "development" and not os.getenv("STRICT_CONFIG"):
            self._apply_development_defaults()
    
    def _apply_development_defaults(self):
        """Apply development-only default values for convenience."""
        # Infrastructure ports
        if self.REDIS_PORT is None:
            self.REDIS_PORT = 6379
        if self.POSTGRES_PORT is None:
            self.POSTGRES_PORT = 5432
        if self.KAFKA_PORT is None:
            self.KAFKA_PORT = 9092
        if self.ZOOKEEPER_PORT is None:
            self.ZOOKEEPER_PORT = 2181
            
        # Timeout configuration defaults
        if self.RETRY_TIMEOUT_MULTIPLIER is None:
            self.RETRY_TIMEOUT_MULTIPLIER = 1.5
        if self.MAX_RETRY_TIMEOUT is None:
            self.MAX_RETRY_TIMEOUT = 300
        if self.HEALTH_CHECK_TIMEOUT is None:
            self.HEALTH_CHECK_TIMEOUT = 5
        if self.HEALTH_CHECK_CACHE_TTL is None:
            self.HEALTH_CHECK_CACHE_TTL = 60
        if self.CIRCUIT_BREAKER_THRESHOLD is None:
            self.CIRCUIT_BREAKER_THRESHOLD = 5
        if self.CIRCUIT_BREAKER_RECOVERY_TIME is None:
            self.CIRCUIT_BREAKER_RECOVERY_TIME = 30
        if self.ERROR_CONTEXT_MAX_LENGTH is None:
            self.ERROR_CONTEXT_MAX_LENGTH = 1000
            
        # Monitoring endpoints
        if self.TRACING_ENDPOINT is None:
            self.TRACING_ENDPOINT = "http://localhost:4317"
        if self.JAEGER_AGENT_HOST is None:
            self.JAEGER_AGENT_HOST = "localhost"
        if self.JAEGER_AGENT_PORT is None:
            self.JAEGER_AGENT_PORT = 14268
        if self.PROMETHEUS_URL is None:
            self.PROMETHEUS_URL = "http://localhost:9090"
            
        # AST validation mode
        if self.AST_VALIDATION_MODE is None:
            self.AST_VALIDATION_MODE = "permissive"

    def get_hash_based_port(self, component_name: str, system_name: str) -> int:
        """Deterministically allocate a port based on hashes within configured range."""
        port_span = self.PORT_RANGE_END - self.PORT_RANGE_START
        return self.PORT_RANGE_START + (hash(f"{system_name}:{component_name}") % port_span)

    def get_llm_api_key(self) -> Optional[str]:
        """Return the API key for the configured LLM provider."""
        provider = self.get_llm_provider()
        
        if provider == "gemini":
            return os.getenv("GEMINI_API_KEY") or self.GEMINI_API_KEY
        elif provider == "openai":
            return os.getenv("OPENAI_API_KEY") or self.OPENAI_API_KEY
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY") or self.ANTHROPIC_API_KEY
        
        return None

    def get_llm_model(self) -> str:
        """Return the configured LLM model based on selected provider."""
        provider = self.get_llm_provider()
        
        if provider == "gemini":
            return os.getenv("GEMINI_MODEL") or self.GEMINI_MODEL
        elif provider == "openai":
            return os.getenv("OPENAI_MODEL") or self.OPENAI_MODEL
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL") or self.ANTHROPIC_MODEL
        else:
            return self.GEMINI_MODEL  # default to gemini for speed

    def get_llm_provider(self) -> str:
        """Return the configured LLM provider based on available API keys."""
        # Check which API key is actually available
        if os.getenv("GEMINI_API_KEY") or self.GEMINI_API_KEY:
            return "gemini"  # Use Gemini when it's configured
        elif os.getenv("OPENAI_API_KEY") or self.OPENAI_API_KEY:
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY") or self.ANTHROPIC_API_KEY:
            return "anthropic"
        
        # If no API key is found, raise an error instead of defaulting
        raise ValueError(
            "No LLM API key configured. Please set one of: "
            "GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env file"
        )
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        """Return the configured JWT secret key."""
        secret_key = os.getenv("JWT_SECRET_KEY", self.DEFAULT_JWT_SECRET_KEY)
        
        # For development, provide a fallback
        if not secret_key:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "JWT_SECRET_KEY environment variable is required for production. "
                    "No hardcoded fallback is provided for security reasons."
                )
            else:
                secret_key = "dev-jwt-secret-key-change-in-production"
        
        # Validate that it's not a common test/default value (only in production)
        if self.ENVIRONMENT == "production" and secret_key in [
            "your-super-secret-key", 
            "secret", 
            "test",
            "jwt_secret",
            "default",
            "changeme"
        ]:
            raise ValueError(
                f"JWT_SECRET_KEY appears to be a test/default value: '{secret_key}'. "
                "Please provide a secure, randomly generated secret for production."
            )
        
        return secret_key
    
    @property
    def KAFKA_BROKERS(self) -> str:
        """Return the configured Kafka broker addresses."""
        kafka_brokers = os.getenv("KAFKA_BROKERS", self.DEFAULT_KAFKA_BROKERS)
        
        # For development, provide a fallback
        if not kafka_brokers:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "KAFKA_BROKERS environment variable is required for production. "
                    "No hardcoded fallback is provided for configuration consistency."
                )
            else:
                kafka_brokers = "localhost:9092"
        
        return kafka_brokers
    
    def get_github_token(self) -> str:
        """Return the configured GitHub API token with validation."""
        token = self.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
        
        if not token:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "GITHUB_TOKEN environment variable is required for production. "
                    "Get from: https://github.com/settings/tokens"
                )
            else:
                raise ValueError(
                    "GITHUB_TOKEN is required for system generation. "
                    "Set GITHUB_TOKEN environment variable with your GitHub personal access token."
                )
        
        # Validate GitHub token format
        if not token.startswith("ghp_") or len(token) < 40:
            raise ValueError(
                f"Invalid GitHub token format: '{token[:10]}...'. "
                "Expected format: 'ghp_' followed by at least 36 characters."
            )
        
        return token
    
    def get_aws_credentials(self) -> tuple[str, str]:
        """Return AWS credentials with validation."""
        access_key = self.AWS_ACCESS_KEY_ID or os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = self.AWS_SECRET_ACCESS_KEY or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not access_key or not secret_key:
            raise ValueError(
                "AWS credentials not configured. Both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY required. "
                "Get from: AWS Console → IAM → Create user with Cost Explorer permissions"
            )
        
        # Validate AWS access key format
        if not access_key.startswith("AKIA") or len(access_key) != 20:
            raise ValueError(f"Invalid AWS Access Key ID format: '{access_key[:10]}...'")
        
        if len(secret_key) != 40:
            raise ValueError("Invalid AWS Secret Access Key format: expected 40 characters")
        
        return access_key, secret_key
    
    def has_aws_credentials(self) -> bool:
        """Check if AWS credentials are available without throwing errors."""
        try:
            self.get_aws_credentials()
            return True
        except ValueError:
            return False
    
    def get_datadog_credentials(self) -> tuple[str, str]:
        """Return Datadog credentials with validation."""
        api_key = self.DATADOG_API_KEY or os.getenv("DATADOG_API_KEY")
        app_key = self.DATADOG_APP_KEY or os.getenv("DATADOG_APP_KEY")
        
        if not api_key or not app_key:
            raise ValueError(
                "Datadog credentials not configured. Both DATADOG_API_KEY and DATADOG_APP_KEY required. "
                "Get from: Datadog → Organization Settings → API Keys"
            )
        
        # Validate Datadog API key format (32 hex characters)
        if len(api_key) != 32 or not all(c in '0123456789abcdef' for c in api_key.lower()):
            raise ValueError(f"Invalid Datadog API key format: '{api_key[:10]}...'")
        
        # Validate Datadog App key format (40 hex characters)
        if len(app_key) != 40 or not all(c in '0123456789abcdef' for c in app_key.lower()):
            raise ValueError(f"Invalid Datadog Application key format: '{app_key[:10]}...'")
        
        return api_key, app_key
    
    def has_datadog_credentials(self) -> bool:
        """Check if Datadog credentials are available without throwing errors."""
        try:
            self.get_datadog_credentials()
            return True
        except ValueError:
            return False
    
    def get_prometheus_url(self) -> str:
        """Return Prometheus URL with validation."""
        url = self.PROMETHEUS_URL
        
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid Prometheus URL format: '{url}'. Must start with http:// or https://")
        
        return url
    
    def get_pipeline_config(self) -> dict:
        """Get configuration for pipeline robustness"""
        return {
            "skip_test_generation": self.SKIP_TEST_GENERATION,
            "ast_validation_mode": self.AST_VALIDATION_MODE,
            "continue_on_test_failure": self.CONTINUE_ON_TEST_FAILURE,
            "continue_on_schema_failure": self.CONTINUE_ON_SCHEMA_FAILURE,
            "pipeline_fail_fast": self.PIPELINE_FAIL_FAST,
        }

    def get_retry_timeout(self, attempt: int, base_timeout: int = None) -> int:
        """Calculate progressive timeout for retry attempt.
        
        Args:
            attempt: The retry attempt number (0-based)
            base_timeout: Base timeout in seconds (defaults to COMPONENT_GENERATION_TIMEOUT)
            
        Returns:
            Timeout in seconds for this retry attempt
        """
        if base_timeout is None:
            base_timeout = self.COMPONENT_GENERATION_TIMEOUT
            
        # Calculate timeout with exponential backoff
        timeout = int(base_timeout * (self.RETRY_TIMEOUT_MULTIPLIER ** attempt))
        
        # Cap at maximum retry timeout
        return min(timeout, self.MAX_RETRY_TIMEOUT)
    
    def validate_production_settings(self):
        """Validate that production deployments don't use insecure defaults."""
        if self.ENVIRONMENT == "production":
            # Check for required production values
            if hasattr(self, 'DEFAULT_JWT_SECRET_KEY') and (
                not self.DEFAULT_JWT_SECRET_KEY or 
                self.DEFAULT_JWT_SECRET_KEY == "your-super-secret-key"
            ):
                raise ValueError("JWT_SECRET_KEY must be set for production deployments")
                
            # Ensure debug is off in production
            if self.DEBUG_MODE:
                raise ValueError("DEBUG_MODE must be False in production")
                
            # Check for secure database URLs (not using default passwords)
            if hasattr(self, 'DEFAULT_POSTGRES_URL') and self.DEFAULT_POSTGRES_URL:
                if "postgres:postgres" in self.DEFAULT_POSTGRES_URL:
                    raise ValueError("Production POSTGRES_URL must not use default credentials")
                
            if hasattr(self, 'DEFAULT_RABBITMQ_URL') and self.DEFAULT_RABBITMQ_URL:
                if "guest:guest" in self.DEFAULT_RABBITMQ_URL:
                    raise ValueError("Production RABBITMQ_URL must not use default credentials")


# Create settings instance
settings = Settings()

# Validate production settings on startup
try:
    settings.validate_production_settings()
except ValueError as e:
    print(f"Configuration Error: {e}", file=sys.stderr)
    if settings.ENVIRONMENT == "production":
        sys.exit(1) 