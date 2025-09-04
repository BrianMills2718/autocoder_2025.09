"""
Docker Compose generator plugin for the scaffold generation system.
Generates docker-compose.yml with all required services.
"""
from typing import Dict, Any, List, Optional
import yaml
from jinja2 import Template
from autocoder_cc.core.config import settings
from autocoder_cc.generators.config import generator_settings


class DockerComposeGenerator:
    """Generates docker-compose.yml for autocoder systems."""
    
    def generate(self, blueprint: Dict[str, Any]) -> str:
        """Generate docker-compose.yml content based on system blueprint."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        components = system.get('components', [])
        
        # Start with base services
        services = {
            system_name: self._generate_app_service(system_name, components)
        }
        
        # Add required infrastructure services
        if self._needs_postgres(components):
            services['postgres'] = self._generate_postgres_service()
        
        if self._needs_redis(components):
            services['redis'] = self._generate_redis_service()
            
        if self._needs_rabbitmq(components):
            services['rabbitmq'] = self._generate_rabbitmq_service()
            
        if self._needs_kafka(components):
            services['zookeeper'] = self._generate_zookeeper_service()
            services['kafka'] = self._generate_kafka_service()
        
        # Add monitoring services if metrics enabled
        if self._needs_monitoring(blueprint):
            services['prometheus'] = self._generate_prometheus_service()
            services['grafana'] = self._generate_grafana_service()
        
        # Build complete docker-compose structure
        compose = {
            'version': '3.8',
            'services': services,
            'networks': {
                'app-network': {
                    'driver': 'bridge'
                }
            }
        }
        
        # Add volumes if needed
        volumes = {}
        if 'postgres' in services:
            volumes['postgres_data'] = {}
        if 'redis' in services:
            volumes['redis_data'] = {}
        if 'rabbitmq' in services:
            volumes['rabbitmq_data'] = {}
        if 'kafka' in services:
            volumes['kafka_data'] = {}
            volumes['zookeeper_data'] = {}
        if 'prometheus' in services:
            volumes['prometheus_data'] = {}
            volumes['grafana_data'] = {}
            
        if volumes:
            compose['volumes'] = volumes
        
        # Convert to YAML with proper formatting
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def _generate_app_service(self, name: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the main application service."""
        # Use string formatting instead of f-strings for consistency
        api_port = generator_settings.api_port
        redis_url = generator_settings.get_redis_url()
        
        service = {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile'
            },
            'container_name': name,
            'ports': [
                f"{api_port}:{api_port}"
            ],
            'environment': [
                f"ENVIRONMENT={settings.ENVIRONMENT}",
                f"LOG_LEVEL={settings.LOG_LEVEL}",
                "DATABASE_URL=${DATABASE_URL:?Database URL must be set}",
                f"REDIS_URL=${{REDIS_URL:-{redis_url}}}",
                "RABBITMQ_URL=${RABBITMQ_URL}",
                "JWT_SECRET_KEY=${JWT_SECRET_KEY:?JWT secret key must be set}",
            ],
            'networks': ['app-network'],
            'depends_on': self._get_dependencies(components),
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', f'http://127.0.0.1:{api_port}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3,
                'start_period': '40s'
            }
        }
        
        # Add metrics port if enabled
        if settings.ENABLE_METRICS:
            service['ports'].append(f"{settings.METRICS_PORT}:9090")
        
        return service
    
    def _generate_postgres_service(self) -> Dict[str, Any]:
        """Generate PostgreSQL service configuration."""
        return {
            'image': 'postgres:16-alpine',
            'container_name': 'postgres',
            'environment': [
                'POSTGRES_USER=${POSTGRES_USER:-postgres}',
                'POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?PostgreSQL password must be set}',
                'POSTGRES_DB=${POSTGRES_DB:-app_db}'
            ],
            'ports': [f'{generator_settings.postgres_port}:{generator_settings.postgres_port}'],
            'volumes': [
                'postgres_data:/var/lib/postgresql/data'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD-SHELL', 'pg_isready -U postgres'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    
    def _generate_redis_service(self) -> Dict[str, Any]:
        """Generate Redis service configuration."""
        return {
            'image': 'redis:7-alpine',
            'container_name': 'redis',
            'command': 'redis-server --appendonly yes',
            'ports': [f'{generator_settings.redis_port}:{generator_settings.redis_port}'],
            'volumes': [
                'redis_data:/data'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'redis-cli', 'ping'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    
    def _generate_rabbitmq_service(self) -> Dict[str, Any]:
        """Generate RabbitMQ service configuration."""
        return {
            'image': 'rabbitmq:3.12-management',
            'container_name': 'rabbitmq',
            'hostname': 'rabbitmq',
            'environment': [
                f'RABBITMQ_DEFAULT_USER=${{RABBITMQ_USER:-{generator_settings.rabbitmq_user}}}',
                f'RABBITMQ_DEFAULT_PASS=${{RABBITMQ_PASSWORD:?RabbitMQ password must be set}}'
            ],
            'ports': [
                f'{generator_settings.rabbitmq_port}:{generator_settings.rabbitmq_port}',  # AMQP port
                f'{generator_settings.rabbitmq_management_port}:{generator_settings.rabbitmq_management_port}'  # Management UI
            ],
            'volumes': [
                'rabbitmq_data:/var/lib/rabbitmq'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'rabbitmq-diagnostics', 'ping'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    
    def _generate_zookeeper_service(self) -> Dict[str, Any]:
        """Generate Zookeeper service configuration for Kafka."""
        return {
            'image': 'confluentinc/cp-zookeeper:latest',
            'container_name': 'zookeeper',
            'environment': [
                'ZOOKEEPER_CLIENT_PORT=2181',
                'ZOOKEEPER_TICK_TIME=2000'
            ],
            'ports': [f'{generator_settings.zookeeper_port}:{generator_settings.zookeeper_port}'],
            'volumes': [
                'zookeeper_data:/var/lib/zookeeper/data'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'echo', 'ruok', '|', 'nc', 'localhost', '2181'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    
    def _generate_kafka_service(self) -> Dict[str, Any]:
        """Generate Kafka service configuration."""
        return {
            'image': 'confluentinc/cp-kafka:latest',
            'container_name': 'kafka',
            'depends_on': ['zookeeper'],
            'environment': [
                'KAFKA_BROKER_ID=1',
                f'KAFKA_ZOOKEEPER_CONNECT=zookeeper:{generator_settings.zookeeper_port}',
                f'KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:{generator_settings.kafka_port}',
                'KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1'
            ],
            'ports': [f'{generator_settings.kafka_port}:{generator_settings.kafka_port}'],
            'volumes': [
                'kafka_data:/var/lib/kafka/data'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'kafka-broker-api-versions', '--bootstrap-server', 'localhost:9092'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    
    def _generate_prometheus_service(self) -> Dict[str, Any]:
        """Generate Prometheus service configuration."""
        return {
            'image': 'prom/prometheus:latest',
            'container_name': 'prometheus',
            'command': [
                '--config.file=/etc/prometheus/prometheus.yml',
                '--storage.tsdb.path=/prometheus',
                '--web.console.libraries=/usr/share/prometheus/console_libraries',
                '--web.console.templates=/usr/share/prometheus/consoles'
            ],
            'ports': [f'{generator_settings.prometheus_port}:{generator_settings.prometheus_port}'],
            'volumes': [
                './prometheus.yml:/etc/prometheus/prometheus.yml:ro',
                'prometheus_data:/prometheus'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped'
        }
    
    def _generate_grafana_service(self) -> Dict[str, Any]:
        """Generate Grafana service configuration."""
        return {
            'image': 'grafana/grafana:latest',
            'container_name': 'grafana',
            'ports': [f'{generator_settings.grafana_port}:{generator_settings.grafana_port}'],
            'environment': [
                f'GF_SECURITY_ADMIN_USER=${{GRAFANA_USER:-{generator_settings.grafana_admin_user}}}',
                f'GF_SECURITY_ADMIN_PASSWORD=${{GRAFANA_PASSWORD:?Grafana admin password must be set}}',
                'GF_USERS_ALLOW_SIGN_UP=false'
            ],
            'volumes': [
                'grafana_data:/var/lib/grafana'
            ],
            'networks': ['app-network'],
            'depends_on': ['prometheus'],
            'restart': 'unless-stopped'
        }
    
    def _get_dependencies(self, components: List[Dict[str, Any]]) -> List[str]:
        """Determine service dependencies based on components."""
        deps = []
        
        if self._needs_postgres(components):
            deps.append('postgres')
        if self._needs_redis(components):
            deps.append('redis')
        if self._needs_rabbitmq(components):
            deps.append('rabbitmq')
        if self._needs_kafka(components):
            deps.extend(['zookeeper', 'kafka'])
            
        return deps
    
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