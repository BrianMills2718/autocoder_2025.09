"""
Environment file generator for deployment artifacts.
Generates .env files with all required configuration variables.
"""
import secrets
import string
from typing import Dict, Any, List
from autocoder_cc.core.config import settings
from autocoder_cc.generators.config import generator_settings


class EnvFileGenerator:
    """Generates environment files for containerized deployments."""
    
    @staticmethod
    def _generate_secure_password(length: int = 32) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def _generate_jwt_secret(length: int = 64) -> str:
        """Generate a secure JWT secret key."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate(self, blueprint: Dict[str, Any]) -> str:
        """Generate .env file content based on system blueprint."""
        system = blueprint.get('system', {})
        components = system.get('components', [])
        
        env_vars = []
        
        # Core application settings
        env_vars.extend([
            "# Core Application Settings",
            f"ENVIRONMENT={settings.ENVIRONMENT}",
            f"LOG_LEVEL={settings.LOG_LEVEL}",
            f"DEBUG_MODE={str(settings.DEBUG_MODE).lower()}",
            "",
            "# API Configuration", 
            f"API_PORT={generator_settings.api_port}",
            f"API_HOST={generator_settings.api_host}",
            f"API_PREFIX={generator_settings.api_prefix}",
            "",
            "# Security Settings",
            f"JWT_SECRET_KEY={self._generate_jwt_secret()}",
            "",
        ])
        
        # Database configuration
        if self._needs_postgres(components):
            env_vars.extend([
                "# PostgreSQL Configuration",
                f"POSTGRES_USER={generator_settings.postgres_user}",
                f"POSTGRES_PASSWORD={self._generate_secure_password()}",
                f"POSTGRES_DB={generator_settings.postgres_db}",
                f"DATABASE_URL=postgresql://{generator_settings.postgres_user}:${{POSTGRES_PASSWORD}}@postgres:{generator_settings.postgres_port}/{generator_settings.postgres_db}",
                "",
            ])
        
        # Redis configuration
        if self._needs_redis(components):
            env_vars.extend([
                "# Redis Configuration",
                f"REDIS_URL=redis://redis:{generator_settings.redis_port}/0",
                "",
            ])
        
        # RabbitMQ configuration
        if self._needs_rabbitmq(components):
            env_vars.extend([
                "# RabbitMQ Configuration",
                f"RABBITMQ_USER={generator_settings.rabbitmq_user}",
                f"RABBITMQ_PASSWORD={self._generate_secure_password()}",
                f"RABBITMQ_URL=amqp://{generator_settings.rabbitmq_user}:${{RABBITMQ_PASSWORD}}@rabbitmq:{generator_settings.rabbitmq_port}",
                "",
            ])
        
        # Kafka configuration
        if self._needs_kafka(components):
            env_vars.extend([
                "# Kafka Configuration",
                f"KAFKA_BROKERS=kafka:{generator_settings.kafka_port}",
                f"ZOOKEEPER_URL=zookeeper:{generator_settings.zookeeper_port}",
                "",
            ])
        
        # Monitoring configuration
        if self._needs_monitoring(blueprint):
            env_vars.extend([
                "# Monitoring Configuration",
                f"PROMETHEUS_PORT={generator_settings.prometheus_port}",
                f"GRAFANA_PORT={generator_settings.grafana_port}",
                "GRAFANA_USER=admin",
                f"GRAFANA_PASSWORD={self._generate_secure_password()}",
                "",
            ])
        
        # LLM Configuration (if needed)
        if self._needs_llm(components):
            env_vars.extend([
                "# LLM Configuration",
                "OPENAI_API_KEY=your_openai_api_key_here",
                f"OPENAI_MODEL={settings.OPENAI_MODEL}",
                "# ANTHROPIC_API_KEY=your_anthropic_api_key_here",
                "",
            ])
        
        env_vars.extend([
            "# Production Security Notes:",
            "# 1. Secure random passwords have been automatically generated",
            "# 2. Use environment-specific values for different deployments", 
            "# 3. Never commit production secrets to version control",
            "# 4. Consider using Docker secrets or Kubernetes secrets",
            "# 5. Rotate secrets regularly in production environments",
        ])
        
        return "\n".join(env_vars)
    
    def _needs_postgres(self, components: List[Dict[str, Any]]) -> bool:
        """Check if PostgreSQL is needed."""
        return any(comp.get('type') == 'Store' for comp in components)
    
    def _needs_redis(self, components: List[Dict[str, Any]]) -> bool:
        """Check if Redis is needed."""
        return any(comp.get('type') in ['Accumulator', 'Cache'] for comp in components)
    
    def _needs_rabbitmq(self, components: List[Dict[str, Any]]) -> bool:
        """Check if RabbitMQ is needed."""
        return any(comp.get('type') == 'MessageBus' for comp in components)
    
    def _needs_kafka(self, components: List[Dict[str, Any]]) -> bool:
        """Check if Kafka is needed."""
        return any(comp.get('type') in ['StreamProcessor', 'EventStream', 'KafkaSource'] for comp in components)
    
    def _needs_monitoring(self, blueprint: Dict[str, Any]) -> bool:
        """Check if monitoring services are needed."""
        return settings.ENABLE_METRICS or any(
            comp.get('type') == 'MetricsEndpoint' 
            for comp in blueprint.get('system', {}).get('components', [])
        )
    
    def _needs_llm(self, components: List[Dict[str, Any]]) -> bool:
        """Check if LLM integration is needed."""
        return any(comp.get('type') in ['LLMProcessor', 'AIModel'] for comp in components)