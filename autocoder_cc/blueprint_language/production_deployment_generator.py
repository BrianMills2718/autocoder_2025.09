from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Production Deployment Generator - Phase 7 Implementation
Generates Kubernetes manifests, Docker Compose files, secrets management, and CI/CD pipelines
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent
from autocoder_cc.production.secrets_manager import SecretsManager, SecretSpec
from autocoder_cc.resource_orchestrator import ResourceOrchestrator, ResourceManifest
from autocoder_cc.generators.config import generator_settings
from autocoder_cc.autocoder.security.sealed_secrets import SealedSecretsManager, create_sealed_secrets_for_system


class ProductionDeploymentError(Exception):
    """Raised when production deployment generation fails - no fallbacks"""
    pass


@dataclass
class GeneratedDeployment:
    """Generated production deployment artifacts"""
    kubernetes_manifests: Dict[str, str]  # filename -> content
    docker_compose: str
    github_actions: str
    gitlab_ci: str
    secrets_config: str
    helm_chart: Dict[str, str]  # filename -> content
    sealed_secrets: Dict[str, str]  # filename -> sealed secret manifest


class ProductionDeploymentGenerator:
    """
    Generates production-ready deployment artifacts for generated systems.
    
    Capabilities:
    - Kubernetes manifests (Deployment, Service, ConfigMap, Ingress, Secrets)
    - Complete Docker Compose with real dependencies
    - CI/CD pipeline templates (GitHub Actions, GitLab CI)
    - Secrets management integration
    - Helm charts for production deployment
    - Health checks and monitoring configuration
    """
    
    def __init__(self, output_dir: Path, domain_config: Optional[Dict[str, str]] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_manager = SecretsManager()
        self.resource_orchestrator = ResourceOrchestrator()
        
        # Initialize Sealed Secrets Manager for secure secret handling
        self.sealed_secrets_manager = SealedSecretsManager(
            namespace="default",  # Can be configured per deployment
            kubeseal_binary="kubeseal"
        )
        
        # Domain configuration for production-ready deployments
        # Users can override these with their actual domains
        self.domain_config = domain_config or {
            'production': '{system_name}.{base_domain}',
            'staging': '{system_name}-staging.{base_domain}',
            'base_domain': generator_settings.base_domain,  # Configurable base domain
            'use_templating': True  # Enables Helm templating for real deployments
        }
        
        import logging
        self.logger = get_logger("ProductionDeploymentGenerator")
    
    def _get_domain(self, system_name: str, environment: str = 'production', use_helm_templating: bool = None) -> str:
        """Get domain for a given system and environment with optional templating support"""
        # If use_helm_templating is explicitly provided, use that; otherwise fall back to config
        should_template = use_helm_templating if use_helm_templating is not None else self.domain_config.get('use_templating', False)
        
        if should_template:
            # Use Helm templating for Helm charts
            if environment == 'production':
                return f"{{{{ .Values.ingress.host | default \"{system_name}.{self.domain_config['base_domain']}\" }}}}"
            elif environment == 'staging':
                return f"{{{{ .Values.ingress.stagingHost | default \"{system_name}-staging.{self.domain_config['base_domain']}\" }}}}"
        
        # Direct domain substitution
        template = self.domain_config.get(environment, self.domain_config['production'])
        return template.format(
            system_name=system_name,
            base_domain=self.domain_config['base_domain']
        )
    
    async def generate_production_deployment(self, system_blueprint: ParsedSystemBlueprint) -> GeneratedDeployment:
        """Generate complete production deployment artifacts"""
        
        system = system_blueprint.system
        self._current_system_blueprint = system_blueprint  # Store for fallback port allocation
        
        # Generate secure secrets for the entire system first
        from autocoder_cc.production.secrets_manager import SecretSpec
        required_secrets = [
            SecretSpec("DATABASE_PASSWORD", "password", description="PostgreSQL database password"),
            SecretSpec("REDIS_PASSWORD", "password", description="Redis password"),
            SecretSpec("API_SECRET_KEY", "api_key", description="API secret key"),
        ]
        self._system_secrets = self.secrets_manager.generate_secrets_manifest(system.name, required_secrets)
        
        # Use ResourceOrchestrator for centralized resource allocation
        component_dir = self.output_dir / "components"
        requirements = self.resource_orchestrator.scan_components(component_dir)
        
        # Add metrics endpoint as a resource requirement
        from autocoder_cc.resource_orchestrator import ResourceRequirement, ResourceType
        metrics_requirement = ResourceRequirement(
            component_name="metrics",
            component_type="MetricsEndpoint",
            resource_type=ResourceType.NETWORK_PORT,
            priority=1
        )
        requirements.append(metrics_requirement)
        
        self.resource_manifest = self.resource_orchestrator.allocate_resources(requirements, system.name)
        
        # Generate Kubernetes manifests
        # Generate direct K8s manifests (no templating - kubectl ready)
        k8s_manifests = self._generate_kubernetes_manifests(system_blueprint, use_helm_templating=False)
        
        # Generate Docker Compose with real dependencies
        docker_compose = self._generate_docker_compose(system_blueprint)
        
        # Generate CI/CD pipelines
        github_actions = self._generate_github_actions(system_blueprint)
        gitlab_ci = self._generate_gitlab_ci(system_blueprint)
        
        # Generate secrets configuration
        secrets_config = self._generate_secrets_config(system_blueprint)
        
        # Generate Helm chart
        helm_chart = self._generate_helm_chart(system_blueprint)
        
        # Generate sealed secrets using SealedSecretsManager
        sealed_secrets = await self._generate_sealed_secrets(system_blueprint)
        
        # Write all files to output directory
        self._write_deployment_files(system.name, {
            **{f"k8s/{name}": content for name, content in k8s_manifests.items()},
            **{f"k8s/sealed-secrets/{name}": content for name, content in sealed_secrets.items()},
            "docker-compose.yml": docker_compose,
            ".github/workflows/deploy.yml": github_actions,
            ".gitlab-ci.yml": gitlab_ci,
            "config/secrets.yaml": secrets_config,
            **{f"helm/{name}": content for name, content in helm_chart.items()}
        })
        
        return GeneratedDeployment(
            kubernetes_manifests=k8s_manifests,
            docker_compose=docker_compose,
            github_actions=github_actions,
            gitlab_ci=gitlab_ci,
            secrets_config=secrets_config,
            helm_chart=helm_chart,
            sealed_secrets=sealed_secrets
        )
    
    def _generate_kubernetes_manifests(self, system_blueprint: ParsedSystemBlueprint, use_helm_templating: bool = True) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        
        system = system_blueprint.system
        manifests = {}
        
        # 1. Namespace
        manifests["namespace.yaml"] = f"""apiVersion: v1
kind: Namespace
metadata:
  name: {system.name}
  labels:
    app: {system.name}
    version: "{system.version}"
    generated-by: autocoder-4.3
"""
        
        # 2. ConfigMap for system configuration
        config_data = self._build_k8s_config_data(system_blueprint)
        manifests["configmap.yaml"] = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {system.name}-config
  namespace: {system.name}
  labels:
    app: {system.name}
    component: config
data:
{config_data}
"""
        
        # 3. Secrets for sensitive configuration
        manifests["secrets.yaml"] = self._generate_secure_secrets_manifest(system_blueprint)
        
        # 4. Deployment for the main system
        manifests["deployment.yaml"] = self._generate_k8s_deployment(system_blueprint)
        
        # 5. Service for API endpoints
        api_components = [c for c in system.components if c.type == "APIEndpoint"]
        if api_components:
            manifests["service.yaml"] = self._generate_k8s_service(system_blueprint, api_components)
        
        # 6. Ingress for external access
        if api_components:
            manifests["ingress.yaml"] = self._generate_k8s_ingress(system_blueprint, api_components, use_helm_templating)
        
        # 7. External dependencies (PostgreSQL, Redis, etc.)
        dependency_manifests = self._generate_k8s_dependencies(system_blueprint)
        manifests.update(dependency_manifests)
        
        # 8. ServiceMonitor for Prometheus
        manifests["servicemonitor.yaml"] = f"""apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {system.name}-monitor
  namespace: {system.name}
  labels:
    app: {system.name}
    component: monitoring
spec:
  selector:
    matchLabels:
      app: {system.name}
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
"""
        
        return manifests
    
    def _generate_k8s_deployment(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate Kubernetes Deployment manifest"""
        
        system = system_blueprint.system
        
        # Determine resource requirements based on components
        resource_requests = self._calculate_resource_requirements(system_blueprint)
        
        # Build environment variables
        env_vars = self._build_k8s_env_vars(system_blueprint)
        
        # Determine exposed ports from ResourceOrchestrator
        ports = self._get_allocated_ports()
        
        deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {system.name}
  namespace: {system.name}
  labels:
    app: {system.name}
    version: "{system.version}"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {system.name}
  template:
    metadata:
      labels:
        app: {system.name}
        version: "{system.version}"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{self._get_metrics_port()}"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: {system.name}
        image: {system.name}:latest
        imagePullPolicy: IfNotPresent
        ports:
{self._format_container_ports(ports)}
        env:
{env_vars}
        envFrom:
        - configMapRef:
            name: {system.name}-config
        - secretRef:
            name: {system.name}-secrets
        resources:
          requests:
            memory: "{resource_requests['memory_request']}"
            cpu: "{resource_requests['cpu_request']}"
          limits:
            memory: "{resource_requests['memory_limit']}"
            cpu: "{resource_requests['cpu_limit']}"
        livenessProbe:
          httpGet:
            path: /health
            port: {ports[0] if ports else generator_settings.api_port}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: {ports[0] if ports else generator_settings.api_port}
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: {system.name}-config
      restartPolicy: Always
"""
        return deployment
    
    def _generate_k8s_service(self, system_blueprint: ParsedSystemBlueprint, api_components: List[ParsedComponent]) -> str:
        """Generate Kubernetes Service manifest"""
        
        system = system_blueprint.system
        ports = []
        
        # Add API endpoint ports
        for comp in api_components:
            port = comp.config.get('port', generator_settings.api_port)
            ports.append(f"""  - name: {comp.name}
    port: {port}
    targetPort: {port}
    protocol: TCP""")
        
        # Add metrics port
        metrics_port = self._get_metrics_port()
        ports.append(f"""  - name: metrics
    port: {metrics_port}
    targetPort: {metrics_port}
    protocol: TCP""")
        
        service = f"""apiVersion: v1
kind: Service
metadata:
  name: {system.name}
  namespace: {system.name}
  labels:
    app: {system.name}
    component: service
spec:
  selector:
    app: {system.name}
  ports:
{chr(10).join(ports)}
  type: ClusterIP
"""
        return service
    
    def _generate_k8s_ingress(self, system_blueprint: ParsedSystemBlueprint, api_components: List[ParsedComponent], use_helm_templating: bool = True) -> str:
        """Generate Kubernetes Ingress manifest"""
        
        system = system_blueprint.system
        production_domain = self._get_domain(system.name, 'production', use_helm_templating)
        
        # Build ingress rules
        rules = []
        for comp in api_components:
            port = comp.config.get('port', generator_settings.api_port)
            rules.append(f"""          - path: /{comp.name}
            pathType: Prefix
            backend:
              service:
                name: {system.name}
                port:
                  number: {port}""")
        
        ingress = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {system.name}
  namespace: {system.name}
  labels:
    app: {system.name}
    component: ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - {production_domain}
    secretName: {system.name}-tls
  rules:
  - host: {production_domain}
    http:
      paths:
{chr(10).join(rules)}
"""
        return ingress
    
    def _generate_k8s_dependencies(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, str]:
        """Generate Kubernetes manifests for external dependencies"""
        
        system = system_blueprint.system
        dependencies = {}
        
        # Check if any components need database
        needs_database = any(comp.type in ["Store", "Model"] for comp in system.components)
        
        if needs_database:
            dependencies["postgres.yaml"] = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: {system.name}
  labels:
    app: postgres
    component: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: {system.name}_db
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {system.name}-secrets
              key: DATABASE_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: {system.name}
  labels:
    app: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: {system.name}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
"""
        
        # Check if any components need Redis
        needs_redis = self._detect_redis_dependency(system_blueprint)
        
        if needs_redis:
            dependencies["redis.yaml"] = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: {system.name}
  labels:
    app: redis
    component: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --requirepass
        - "$(REDIS_PASSWORD)"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {system.name}-secrets
              key: REDIS_PASSWORD
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: {system.name}
  labels:
    app: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
"""
        
        # Check if any components need Kafka (Sources, Sinks, or Stream Processors)
        needs_kafka = any(
            comp.type in ["Source", "Sink", "StreamProcessor"] or
            comp.config.get('messaging_type') == 'kafka' or
            any('kafka' in str(inp.schema).lower() for inp in (comp.inputs or [])) or
            any('kafka' in str(out.schema).lower() for out in (comp.outputs or [])) or
            any(res.type == 'kafka' for res in comp.resources)
            for comp in system.components
        )
        
        if needs_kafka:
            # Kafka requires Zookeeper, so generate both
            dependencies["zookeeper.yaml"] = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: zookeeper
  namespace: {system.name}
  labels:
    app: zookeeper
    component: messaging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zookeeper
  template:
    metadata:
      labels:
        app: zookeeper
    spec:
      containers:
      - name: zookeeper
        image: confluentinc/cp-zookeeper:7.4.0
        ports:
        - containerPort: {generator_settings.zookeeper_port}
        env:
        - name: ZOOKEEPER_CLIENT_PORT
          value: "{generator_settings.zookeeper_port}"
        - name: ZOOKEEPER_TICK_TIME
          value: "2000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: zookeeper
  namespace: {system.name}
  labels:
    app: zookeeper
spec:
  selector:
    app: zookeeper
  ports:
  - port: {generator_settings.zookeeper_port}
    targetPort: {generator_settings.zookeeper_port}
  type: ClusterIP
"""
            
            dependencies["kafka.yaml"] = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
  namespace: {system.name}
  labels:
    app: kafka
    component: messaging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.4.0
        ports:
        - containerPort: {generator_settings.kafka_port}
        - containerPort: 29092
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper:{generator_settings.zookeeper_port}"
        - name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP
          value: "PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:29092,PLAINTEXT_HOST://kafka:{generator_settings.kafka_port}"
        - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
          value: "1"
        - name: KAFKA_TRANSACTION_STATE_LOG_MIN_ISR
          value: "1"
        - name: KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR
          value: "1"
        - name: KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS
          value: "0"
        - name: KAFKA_AUTO_CREATE_TOPICS_ENABLE
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: {system.name}
  labels:
    app: kafka
spec:
  selector:
    app: kafka
  ports:
  - name: plaintext
    port: {generator_settings.kafka_port}
    targetPort: {generator_settings.kafka_port}
  - name: internal
    port: 29092
    targetPort: 29092
  type: ClusterIP
"""
        
        return dependencies
    
    def _generate_production_security_config(self, system_name: str) -> Dict[str, Any]:
        """Generate production security configuration"""
        
        return {
            "ssl_enabled": True,
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst_limit": 200
            },
            "cors": {
                "enabled": True,
                "allowed_origins": [f"https://{system_name}.example.com"],
                "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
                "allowed_headers": ["Authorization", "Content-Type"]
            },
            "authentication": {
                "jwt_enabled": True,
                "token_expiry": "1h",
                "refresh_token_expiry": "7d"
            },
            "logging": {
                "level": "INFO",
                "audit_enabled": True,
                "log_requests": True,
                "log_responses": False
            },
            "security_headers": {
                "x_frame_options": "DENY",
                "x_content_type_options": "nosniff",
                "x_xss_protection": "1; mode=block",
                "strict_transport_security": "max-age=31536000; includeSubDomains",
                "content_security_policy": "default-src 'self'"
            },
            "container_security": {
                "read_only_filesystem": True,
                "non_root_user": True,
                "drop_capabilities": ["ALL"],
                "add_capabilities": ["NET_BIND_SERVICE"],
                "no_new_privileges": True
            }
        }
    
    def _generate_docker_compose(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate Docker Compose with real service dependencies"""
        
        system = system_blueprint.system
        
        # Use the secrets already generated in generate_production_deployment
        secrets_manifest = self._system_secrets
        
        # Main application service
        app_ports = self._get_allocated_ports()
        port_mappings = [f"      - \"{port}:{port}\"" for port in app_ports]
        
        # Check what dependencies are needed
        needs_postgres = any(comp.type in ["Store", "Model"] for comp in system.components)
        needs_redis = self._detect_redis_dependency(system_blueprint)
        
        # Build services with production security
        security_config = self._generate_production_security_config(system.name)
        
        services = {
            system.name: f"""
  {system.name}:
    build: .
    ports:
{chr(10).join(port_mappings)}
      - "{self._get_metrics_port()}:{self._get_metrics_port()}"  # metrics
    environment:
      # Database configuration using Docker service names
      - DB_HOST=postgres
      - DB_PORT={generator_settings.postgres_port}
      - DB_NAME={system.name}_db
      - DB_USER=postgres
      - DB_PASSWORD=${{DATABASE_PASSWORD}}
      - DATABASE_URL=postgresql://postgres:${{DATABASE_PASSWORD}}@postgres:{generator_settings.postgres_port}/{system.name}_db
      # Redis configuration using Docker service names
      - REDIS_HOST=redis
      - REDIS_PORT={generator_settings.redis_port}
      - REDIS_PASSWORD=${{REDIS_PASSWORD}}
      - REDIS_URL=redis://:${{REDIS_PASSWORD}}@redis:{generator_settings.redis_port}/0
      # Kafka configuration using Docker service names
      - KAFKA_HOST=kafka
      - KAFKA_PORT={generator_settings.kafka_port}
      - KAFKA_BROKERS=kafka:{generator_settings.kafka_port}
      # Message broker configuration using Docker service names
      - MESSAGING_TYPE=rabbitmq
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_PORT=5672
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      # API configuration
      - API_SECRET_KEY=${{API_SECRET_KEY}}
      - ENVIRONMENT=production
      - INTERNAL_PORT=8080
      # Security configuration
      - ENABLE_HTTPS=true
      - SSL_CERT_PATH=/certs/server.crt
      - SSL_KEY_PATH=/certs/server.key
      - JWT_SECRET=${{API_SECRET_KEY}}
      - RATE_LIMIT_ENABLED=true
      - RATE_LIMIT_REQUESTS=100
      - RATE_LIMIT_WINDOW=60
      - CORS_ENABLED=true
      - CORS_ORIGINS=https://{system.name}.example.com
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./certs:/certs:ro
      - ./security:/app/security:ro
    depends_on:
{self._get_docker_dependencies(system.name, needs_postgres, needs_redis)}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - {system.name}-network
    # Production security configurations
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
      nproc:
        soft: 4096
        hard: 4096"""
        }
        
        # Add PostgreSQL if needed
        if needs_postgres:
            services["postgres"] = f"""
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB={system.name}_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${{DATABASE_PASSWORD}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - {system.name}-network"""
        
        # Add Redis if needed
        if needs_redis:
            services["redis"] = f"""
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${{REDIS_PASSWORD}}
    ports:
      - "6379:{generator_settings.redis_port}"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${{REDIS_PASSWORD}}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - {system.name}-network"""
        
        # Check if Kafka is needed
        needs_kafka = any(
            comp.type in ["Source", "Sink", "StreamProcessor"] or
            comp.config.get('messaging_type') == 'kafka' or
            any('kafka' in str(inp.schema).lower() for inp in (comp.inputs or [])) or
            any('kafka' in str(out.schema).lower() for out in (comp.outputs or []))
            for comp in system.components
        )
        
        if needs_kafka:
            services["zookeeper"] = f"""
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    ports:
      - "{generator_settings.zookeeper_port}:{generator_settings.zookeeper_port}"
    environment:
      ZOOKEEPER_CLIENT_PORT: {generator_settings.zookeeper_port}
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log
    networks:
      - {system.name}-network"""
            
            services["kafka"] = f"""
  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "{generator_settings.kafka_port}:{generator_settings.kafka_port}"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:{generator_settings.zookeeper_port}'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://kafka:{generator_settings.kafka_port}
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_JMX_PORT: 9101
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - {system.name}-network"""
        
        # Add RabbitMQ (message broker that components expect)
        services["rabbitmq"] = f"""
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 30s
      timeout: 30s
      retries: 3
    restart: unless-stopped
    networks:
      - {system.name}-network"""

        # Add monitoring services - use ResourceOrchestrator for port allocation
        prometheus_port = self._get_or_allocate_port("prometheus", "PrometheusService")
        services[f"{system.name}-prometheus"] = f"""
  {system.name}-prometheus:
    image: prom/prometheus:latest
    ports:
      - "{prometheus_port}:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - {system.name}-network"""
        
        services[f"{system.name}-grafana"] = f"""
  {system.name}-grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD={secrets_manifest.get('GRAFANA_PASSWORD', secrets_manifest['DATABASE_PASSWORD'])}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - {system.name}-network"""
        
        # Build volumes
        volumes = ["prometheus_data:", "grafana_data:", "rabbitmq_data:"]
        if needs_postgres:
            volumes.append("postgres_data:")
        if needs_redis:
            volumes.append("redis_data:")
        if needs_kafka:
            volumes.append("zookeeper_data:")
            volumes.append("zookeeper_logs:")
            volumes.append("kafka_data:")
        
        docker_compose = f"""version: '3.8'

services:
{chr(10).join(services.values())}

volumes:
{chr(10).join(f"  {vol}" for vol in volumes)}

networks:
  {system.name}-network:
    driver: bridge
"""
        
        return docker_compose
    
    def _generate_github_actions(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate GitHub Actions CI/CD pipeline"""
        
        system = system_blueprint.system
        secrets_manifest = self._system_secrets
        
        return f"""name: Build and Deploy {system.name}

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}/{system.name}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli -a {secrets_manifest['REDIS_PASSWORD']} ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
          redis-server --requirepass {secrets_manifest['REDIS_PASSWORD']}
        ports:
          - 6379:{generator_settings.redis_port}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@postgres:{generator_settings.postgres_port}/{generator_settings.postgres_test_db}
        redis_url: redis://:{secrets_manifest['REDIS_PASSWORD']}@redis:{generator_settings.redis_port}/0
      run: |
        mkdir -p reports
        pytest tests/ -v --cov=./ --cov-report=xml --junitxml=reports/junit.xml
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: reports/junit.xml
        
    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: |
          reports/junit.xml
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{{{ env.REGISTRY }}}}
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{{{branch}}}}-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{{{ steps.meta.outputs.tags }}}}
        labels: ${{{{ steps.meta.outputs.labels }}}}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'latest'
    
    - name: Configure kubectl
      run: |
        echo "${{{{ secrets.KUBECONFIG }}}}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Update deployment image
      run: |
        export KUBECONFIG=kubeconfig
        kubectl set image deployment/{system.name} {system.name}=${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:main-${{{{ github.sha }}}} -n {system.name}
        kubectl rollout status deployment/{system.name} -n {system.name} --timeout=300s
    
    - name: Verify deployment
      run: |
        export KUBECONFIG=kubeconfig
        kubectl get pods -n {system.name}
        kubectl get services -n {system.name}
"""
    
    def _generate_gitlab_ci(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate GitLab CI pipeline"""
        
        system = system_blueprint.system
        secrets_manifest = self._system_secrets
        staging_domain = self._get_domain(system.name, 'staging', use_helm_templating=False)
        production_domain = self._get_domain(system.name, 'production', use_helm_templating=False)
        
        return f"""stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE/{system.name}:$CI_COMMIT_SHA

services:
  - docker:dind
  - postgres:15
  - redis:7-alpine

variables:
  POSTGRES_DB: test_db
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-secure_test_password}}
  POSTGRES_HOST_AUTH_METHOD: trust

test:
  stage: test
  image: python:3.11
  
  before_script:
    - pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install pytest pytest-asyncio pytest-cov
  
  script:
    - export DATABASE_URL="postgresql://postgres:postgres@postgres:{generator_settings.postgres_port}/test_db"
    - export redis_url="redis://:{secrets_manifest['REDIS_PASSWORD']}@redis:{generator_settings.redis_port}/0"
    - mkdir -p reports
    - pytest tests/ -v --cov=./ --cov-report=xml --cov-report=term --junitxml=reports/junit.xml
  
  coverage: '/TOTAL.*\\s+(\\d+%)$/'
  
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      junit: reports/junit.xml
    paths:
      - reports/
    expire_in: 1 week

build:
  stage: build
  image: docker:latest
  
  services:
    - docker:dind
  
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    - docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE/{system.name}:latest
    - docker push $CI_REGISTRY_IMAGE/{system.name}:latest
  
  only:
    - main
    - develop

deploy_staging:
  stage: deploy
  image: bitnami/kubectl:latest
  
  before_script:
    - echo "$KUBE_CONFIG" | base64 -d > kubeconfig
    - export KUBECONFIG=kubeconfig
  
  script:
    - kubectl set image deployment/{system.name} {system.name}=$IMAGE_TAG -n {system.name}-staging
    - kubectl rollout status deployment/{system.name} -n {system.name}-staging --timeout=300s
    - kubectl get pods -n {system.name}-staging
  
  environment:
    name: staging
    url: https://{staging_domain}
  
  only:
    - develop

deploy_production:
  stage: deploy
  image: bitnami/kubectl:latest
  
  before_script:
    - echo "$KUBE_CONFIG_PROD" | base64 -d > kubeconfig
    - export KUBECONFIG=kubeconfig
  
  script:
    - kubectl set image deployment/{system.name} {system.name}=$IMAGE_TAG -n {system.name}
    - kubectl rollout status deployment/{system.name} -n {system.name} --timeout=300s
    - kubectl get pods -n {system.name}
    - kubectl get services -n {system.name}
  
  environment:
    name: production
    url: https://{production_domain}
  
  when: manual
  only:
    - main
"""
    
    def _generate_secrets_config(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate secrets management configuration"""
        
        system = system_blueprint.system
        
        secrets_config = {
            'secrets': {
                'database': {
                    'url': '${{DATABASE_URL}}',
                    'password': '${{DATABASE_PASSWORD}}',
                    'user': '${{DATABASE_USER}}'
                },
                'api': {
                    'secret_key': '${{API_SECRET_KEY}}',
                    'jwt_secret': '${{JWT_SECRET}}'
                },
                'external_services': {}
            },
            'environment_mapping': {
                'development': {
                    'DATABASE_URL': 'postgresql://postgres:${{DATABASE_PASSWORD}}@postgres:{generator_settings.postgres_port}/dev_db',
                    'API_SECRET_KEY': '${{API_SECRET_KEY}}',
                    'REDIS_URL': 'redis://:${{REDIS_PASSWORD}}@redis:{generator_settings.redis_port}/0'
                },
                'staging': {
                    'DATABASE_URL': '${{STAGING_DATABASE_URL}}',
                    'API_SECRET_KEY': '${{STAGING_API_SECRET_KEY}}',
                    'REDIS_URL': '${{STAGING_REDIS_URL}}'
                },
                'production': {
                    'DATABASE_URL': '${{PROD_DATABASE_URL}}',
                    'API_SECRET_KEY': '${{PROD_API_SECRET_KEY}}',
                    'REDIS_URL': '${{PROD_REDIS_URL}}'
                }
            }
        }
        
        # Add component-specific secrets
        for comp in system.components:
            if comp.type == "Store":
                secrets_config['secrets']['storage'] = {
                    'connection_string': f'${{{{{comp.name.upper()}_CONNECTION_STRING}}}}',
                    'credentials': f'${{{{{comp.name.upper()}_CREDENTIALS}}}}'
                }
            elif comp.type == "Model":
                secrets_config['secrets']['models'] = {
                    'api_key': f'${{{{{comp.name.upper()}_API_KEY}}}}',
                    'model_path': f'${{{{{comp.name.upper()}_MODEL_PATH}}}}'
                }
        
        return yaml.dump(secrets_config, default_flow_style=False, sort_keys=False)
    
    def _generate_helm_chart(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, str]:
        """Generate Helm chart for production deployment"""
        
        system = system_blueprint.system
        chart_files = {}
        
        # Chart.yaml
        chart_files["Chart.yaml"] = f"""apiVersion: v2
name: {system.name}
description: A Helm chart for {system.name}
type: application
version: 0.1.0
appVersion: "{system.version}"
keywords:
  - autocoder
  - generated-system
home: https://github.com/ORGANIZATION/{system.name}
sources:
  - https://github.com/ORGANIZATION/{system.name}
maintainers:
  - name: Autocoder
    email: contact@autocoder.dev
"""
        
        # values.yaml
        api_ports = [comp.config.get('port', generator_settings.api_port) for comp in system.components if comp.type == "APIEndpoint"]
        # Generate port configs with consistent naming - first port is 'http', others are 'http-{port}'
        port_configs = []
        for i, port in enumerate(api_ports):
            if i == 0:
                port_configs.append(f"    - name: http{chr(10)}      port: {port}")
            else:
                port_configs.append(f"    - name: http-{port}{chr(10)}      port: {port}")
        
        # Generate domain configurations for Helm templating
        production_domain_default = f"{system.name}.{self.domain_config['base_domain']}"
        staging_domain_default = f"{system.name}-staging.{self.domain_config['base_domain']}"
        
        # Detect required dependencies based on components
        needs_postgres = self._detect_postgres_dependency(system_blueprint)
        needs_redis = self._detect_redis_dependency(system_blueprint)
        needs_rabbitmq = self._detect_rabbitmq_dependency(system_blueprint)
        needs_kafka = self._detect_kafka_dependency(system_blueprint)
        
        chart_files["values.yaml"] = f"""# Default values for {system.name}
# 
# PRODUCTION CONFIGURATION:
# Update ingress.host to your actual production domain before deploying
# Example: mycompany.com, app.mycompany.com, etc.
# 
# For staging: Update ingress.stagingHost for staging environment
# These defaults use example.com for demonstration only
#
replicaCount: 1

image:
  repository: {system.name}
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  ports:
{chr(10).join(port_configs)}
    - name: metrics
      port: {self._get_metrics_port()}

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  # Configure your production domain here
  host: {production_domain_default}
  stagingHost: {staging_domain_default}
  hosts:
    - host: "{{{{ .Values.ingress.host }}}}"
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: {system.name}-tls
      hosts:
        - "{{{{ .Values.ingress.host }}}}"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

nodeSelector: {{}}

tolerations: []

affinity: {{}}

postgresql:
  enabled: {str(needs_postgres).lower()}
  auth:
    database: {system.name}_db
    username: postgres
    postgresPassword: "{{ .Values.postgresql.auth.postgresPassword }}"
  primary:
    persistence:
      enabled: true
      size: 8Gi
      storageClass: ""
    resources:
      requests:
        memory: 256Mi
        cpu: 100m
      limits:
        memory: 512Mi
        cpu: 500m

redis:
  enabled: {str(needs_redis).lower()}
  auth:
    enabled: true
    password: "{{ .Values.redis.auth.password }}"
  master:
    persistence:
      enabled: true
      size: 8Gi
      storageClass: ""
    resources:
      requests:
        memory: 128Mi
        cpu: 100m
      limits:
        memory: 256Mi
        cpu: 250m

rabbitmq:
  enabled: {str(needs_rabbitmq).lower()}
  auth:
    username: user
    password: "{{ .Values.rabbitmq.auth.password }}"
  persistence:
    enabled: true
    size: 8Gi
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m

kafka:
  enabled: {str(needs_kafka).lower()}
  persistence:
    enabled: true
    size: 8Gi
  zookeeper:
    persistence:
      enabled: true
      size: 8Gi
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 500m

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
  prometheus:
    enabled: true
    server:
      persistentVolume:
        enabled: true
        size: 8Gi
  grafana:
    enabled: true
    persistence:
      enabled: true
      size: 1Gi
"""
        
        # templates/deployment.yaml
        chart_files["templates/deployment.yaml"] = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            {{- range .Values.service.ports }}
            - name: port-{{ .port }}
              containerPort: {{ .port }}
              protocol: TCP
            {{- end }}
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
"""
        
        return chart_files
    
    # Helper methods
    def _build_k8s_config_data(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Build ConfigMap data section with production-ready service DNS names"""
        config_lines = []
        system_name = system_blueprint.system.name
        
        for comp in system_blueprint.system.components:
            config_lines.append(f"  {comp.name}_config: |")
            for key, value in comp.config.items():
                # Transform localhost URLs to Kubernetes service DNS names for production
                if isinstance(value, str):
                    # Replace localhost with proper K8s service DNS
                    production_value = self._transform_localhost_to_k8s_service(value, system_name)
                    config_lines.append(f"    {key}: {production_value}")
                else:
                    config_lines.append(f"    {key}: {value}")
        return "\n".join(config_lines)
    
    def _transform_localhost_to_k8s_service(self, value: str, system_name: str) -> str:
        """Transform localhost URLs to Kubernetes service DNS names"""
        import re
        
        # Transform common localhost patterns to K8s service DNS
        transformations = [
            # PostgreSQL
            (r'postgresql://([^@]+)@localhost:{generator_settings.postgres_port}/([^/\s]+)', 
             f'postgresql://\\1@postgres.{system_name}.svc.cluster.local:{generator_settings.postgres_port}/\\2'),
            (r'postgres://([^@]+)@localhost:{generator_settings.postgres_port}/([^/\s]+)', 
             f'postgres://\\1@postgres.{system_name}.svc.cluster.local:{generator_settings.postgres_port}/\\2'),
            
            # Redis  
            (r'redis://localhost:{generator_settings.redis_port}/(\d+)', 
             f'redis://redis.{system_name}.svc.cluster.local:{generator_settings.redis_port}/\\1'),
            (r'redis://localhost:{generator_settings.redis_port}', 
             f'redis://redis.{system_name}.svc.cluster.local:{generator_settings.redis_port}'),
            
            # Redis standalone host (for redis_host: localhost)
            (r'^localhost$', 
             f'redis.{system_name}.svc.cluster.local'),
            
            # Kafka
            (r'localhost:{generator_settings.kafka_port}', 
             f'kafka.{system_name}.svc.cluster.local:{generator_settings.kafka_port}'),
             
            # RabbitMQ/AMQP
            (r'amqp://([^@]+)@localhost:5672/([^/\s]*)', 
             f'amqp://\\1@rabbitmq.{system_name}.svc.cluster.local:5672/\\2'),
             
            # HTTP localhost
            (r'http://localhost:(\d+)', 
             f'http://app.{system_name}.svc.cluster.local:\\1'),
             
            # Generic localhost:port (should be last to avoid conflicts)
            (r'localhost:(\d+)', 
             f'app.{system_name}.svc.cluster.local:\\1'),
        ]
        
        result = value
        for pattern, replacement in transformations:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def _generate_secure_secrets_manifest(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate real secrets manifest using SealedSecretsManager for security"""
        system_name = system_blueprint.system.name
        
        # Use SealedSecretsManager to generate proper K8s secret manifest
        return self.secrets_manager.generate_k8s_secret_manifest(
            namespace=system_name,
            system_name=system_name,
            secrets_dict=self._system_secrets
        )
    
    def _build_component_secrets(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Build component-specific secrets using SecretsManager"""
        from autocoder_cc.production.secrets_manager import SecretsManager, SecretSpec
        
        manager = SecretsManager()
        required_secrets = []
        
        for comp in system_blueprint.system.components:
            if comp.type == "Store":
                required_secrets.append(
                    SecretSpec(
                        name=f"{comp.name.upper()}_CONNECTION_STRING",
                        type="database_url",
                        description=f"Connection string for {comp.name} store",
                        length=64
                    )
                )
            elif comp.type == "Model":
                required_secrets.append(
                    SecretSpec(
                        name=f"{comp.name.upper()}_API_KEY",
                        type="api_key",
                        description=f"API key for {comp.name} model",
                        prefix=comp.name.lower()
                    )
                )
        
        # Generate actual secure secrets
        secrets_dict = manager.generate_secrets_manifest(
            system_blueprint.system.name, 
            required_secrets
        )
        
        # Format as YAML stringData entries
        secret_lines = []
        for name, value in secrets_dict.items():
            # Skip standard secrets already handled above
            if name not in ["DATABASE_PASSWORD", "API_SECRET_KEY", "JWT_SECRET", "REDIS_PASSWORD"]:
                secret_lines.append(f"  {name}: \"{value}\"")
        
        return "\n".join(secret_lines)
    
    async def _generate_sealed_secrets(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, str]:
        """Generate sealed secrets manifests using SealedSecretsManager"""
        sealed_secrets = {}
        
        # Skip sealed secrets generation in development/generation mode
        generation_mode = os.getenv('AUTOCODER_GENERATION_MODE', 'false').lower()
        self.logger.info(f"Checking AUTOCODER_GENERATION_MODE: {generation_mode}")
        if generation_mode == 'true':
            self.logger.info("Skipping sealed secrets generation in development mode")
            return sealed_secrets
        
        try:
            # Use the already generated secrets from the class instance
            secret_values = self._system_secrets
            
            # Generate sealed secrets for each secret
            namespace = system_blueprint.system.name
            self.sealed_secrets_manager.namespace = namespace
            
            if secret_values:
                # Create a single sealed secret with all the system secrets
                sealed_secret_manifest = await self.sealed_secrets_manager.create_sealed_secret(
                    secret_name=f"{system_blueprint.system.name}-secrets",
                    secret_data=secret_values
                )
                sealed_secrets[f"{system_blueprint.system.name}-sealedsecret.yaml"] = sealed_secret_manifest.raw_yaml
                
                self.logger.info(f"Generated sealed secret manifest for {len(secret_values)} secrets")
            
            # Generate component-specific sealed secrets
            for comp in system_blueprint.system.components:
                component_secrets = {}
                
                if comp.type == "Store":
                    # Database connection secrets
                    db_password_key = f"{comp.name.upper()}_PASSWORD"
                    if db_password_key not in secret_values:
                        # Generate a database password if not already present
                        import secrets
                        import string
                        alphabet = string.ascii_letters + string.digits
                        db_password = ''.join(secrets.choice(alphabet) for _ in range(32))
                        component_secrets[db_password_key] = db_password
                
                elif comp.type == "Model":
                    # Model API key secrets
                    api_key_name = f"{comp.name.upper()}_API_KEY"
                    if api_key_name not in secret_values:
                        # Generate an API key if not already present
                        import secrets
                        api_key = f"{comp.name.lower()}_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))}"
                        component_secrets[api_key_name] = api_key
                
                # Create sealed secret for this component if it has secrets
                if component_secrets:
                    component_sealed_secret = await self.sealed_secrets_manager.create_sealed_secret(
                        secret_name=f"{comp.name}-secrets",
                        secret_data=component_secrets
                    )
                    sealed_secrets[f"{comp.name}-sealedsecret.yaml"] = component_sealed_secret.raw_yaml
                    
                    self.logger.debug(f"Generated sealed secret for component {comp.name}")
            
            self.logger.info(f"Generated {len(sealed_secrets)} sealed secret manifests")
            
        except Exception as e:
            self.logger.error(f"Failed to generate sealed secrets: {e}")
            # FAIL HARD - NO FALLBACKS
            raise ProductionDeploymentError(
                f"Failed to generate sealed secrets for production deployment: {str(e)}. "
                f"NO FALLBACKS - System requires working sealed secrets manager for production deployment. "
                f"Ensure kubeseal is installed and configured properly."
            )
        
        return sealed_secrets
    
    def _calculate_resource_requirements(self, system_blueprint: ParsedSystemBlueprint) -> Dict[str, str]:
        """Calculate Kubernetes resource requirements based on component types and characteristics"""
        
        # Component-specific resource profiles (CPU in millicores, Memory in MB)
        component_profiles = {
            'APIEndpoint': {'cpu': 200, 'memory': 256},  # REST APIs need moderate resources
            'Model': {'cpu': 500, 'memory': 512},        # ML models need more CPU/memory
            'Store': {'cpu': 150, 'memory': 256},        # Database operations
            'Source': {'cpu': 100, 'memory': 128},       # Data ingestion
            'Sink': {'cpu': 100, 'memory': 128},         # Data output
            'Transformer': {'cpu': 200, 'memory': 256},  # Data processing
            'EventSource': {'cpu': 150, 'memory': 192},  # Event streaming
            'Queue': {'cpu': 100, 'memory': 128},        # Message queuing
            'default': {'cpu': 150, 'memory': 192}       # Default for unknown types
        }
        
        # Calculate total resource requirements
        total_cpu = 0
        total_memory = 0
        
        for comp in system_blueprint.system.components:
            profile = component_profiles.get(comp.type, component_profiles['default'])
            
            # Add component base requirements
            total_cpu += profile['cpu']
            total_memory += profile['memory']
            
            # Apply multipliers based on component configuration
            if comp.type == 'Model':
                # ML models may need more resources based on configuration
                if comp.config.get('model_size') == 'large':
                    total_cpu += 300
                    total_memory += 512
                elif comp.config.get('inference_type') == 'real_time':
                    total_cpu += 200
                    total_memory += 256
            
            elif comp.type == 'Store':
                # Database stores may need more resources for certain storage types
                storage_type = comp.config.get('storage_type', '')
                if storage_type in ['postgresql', 'mysql']:
                    total_cpu += 100
                    total_memory += 128
                elif storage_type == 'elasticsearch':
                    total_cpu += 200
                    total_memory += 512
            
            elif comp.type == 'APIEndpoint':
                # API endpoints may need more resources for high-throughput scenarios
                if comp.config.get('high_throughput', False):
                    total_cpu += 200
                    total_memory += 256
        
        # Add system overhead (base system requirements)
        total_cpu += 50   # Base system overhead
        total_memory += 64
        
        # Convert to Kubernetes resource strings with safety margins
        cpu_request = f"{total_cpu}m"
        cpu_limit = f"{min(total_cpu * 2, 2000)}m"  # Cap at 2 cores
        memory_request = f"{total_memory}Mi"
        memory_limit = f"{min(total_memory * 2, 4096)}Mi"  # Cap at 4GB
        
        return {
            'memory_request': memory_request,
            'memory_limit': memory_limit,
            'cpu_request': cpu_request,
            'cpu_limit': cpu_limit
        }
    
    def _build_k8s_env_vars(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Build environment variables for Kubernetes deployment"""
        env_vars = [
            "        - name: ENVIRONMENT",
            "          value: \"production\"",
            "        - name: LOG_LEVEL",
            "          value: \"INFO\"",
            "        - name: METRICS_ENABLED",
            "          value: \"true\""
        ]
        return "\n".join(env_vars)
    
    def _get_allocated_ports(self) -> List[int]:
        """Get all ports allocated by PortAllocator from component configs"""
        # First try to get ports from component configs (where PortAllocator puts them)
        if hasattr(self, '_current_system_blueprint') and self._current_system_blueprint:
            api_components = [c for c in self._current_system_blueprint.system.components 
                            if c.type in ["APIEndpoint", "MetricsEndpoint"]]
            ports = []
            for comp in api_components:
                if comp.config and 'port' in comp.config:
                    ports.append(comp.config['port'])
                    self.logger.info(f"Using allocated port {comp.config['port']} for {comp.name}")
            if ports:
                return sorted(set(ports))
        
        # Fallback: check resource manifest if available
        if hasattr(self, 'resource_manifest'):
            ports = []
            for allocation in self.resource_manifest.allocations:
                if allocation.resource_type.value == "network_port":
                    ports.append(allocation.allocated_value)
            if ports:
                return sorted(set(ports))
        
        # Final fallback: use generator settings default
        self.logger.warning("No allocated ports found - using default port from settings")
        return [generator_settings.api_port]
    
    def _get_metrics_port(self) -> int:
        """Get the allocated metrics port from ResourceOrchestrator"""
        if hasattr(self, 'resource_manifest'):
            for allocation in self.resource_manifest.allocations:
                if (allocation.component_name == "metrics" and 
                    allocation.resource_type.value == "network_port"):
                    return allocation.allocated_value
        
        # If ResourceOrchestrator didn't allocate metrics port, this indicates a configuration issue
        # Instead of using hardcoded fallback, request allocation from ResourceOrchestrator
        self.logger.warning("Metrics port not allocated by ResourceOrchestrator - requesting allocation")
        
        if hasattr(self, '_current_system_blueprint'):
            # Create a metrics requirement and request allocation from ResourceOrchestrator
            from autocoder_cc.resource_orchestrator import ResourceRequirement, ResourceType
            metrics_requirement = ResourceRequirement(
                component_name="metrics",
                component_type="MetricsEndpoint", 
                resource_type=ResourceType.NETWORK_PORT,
                priority=1
            )
            
            # Try to allocate through ResourceOrchestrator
            try:
                system_name = self._current_system_blueprint.system.name
                new_manifest = self.resource_orchestrator.allocate_resources([metrics_requirement], system_name)
                
                # Find the allocated metrics port
                for allocation in new_manifest.allocations:
                    if (allocation.component_name == "metrics" and 
                        allocation.resource_type.value == "network_port"):
                        self.logger.info(f"Successfully allocated metrics port {allocation.allocated_value} through ResourceOrchestrator")
                        return allocation.allocated_value
                        
            except Exception as e:
                self.logger.error(f"Failed to allocate metrics port through ResourceOrchestrator: {e}")
        
        # Only if ResourceOrchestrator allocation completely fails, raise an error instead of using hardcoded fallback
        raise RuntimeError("Unable to allocate metrics port - ResourceOrchestrator allocation failed and no hardcoded fallbacks allowed")
    
    def _get_or_allocate_port(self, component_name: str, component_type: str) -> int:
        """Get or allocate a port for a component through ResourceOrchestrator"""
        # First check if port is already allocated
        if hasattr(self, 'resource_manifest'):
            for allocation in self.resource_manifest.allocations:
                if (allocation.component_name == component_name and 
                    allocation.resource_type.value == "network_port"):
                    return allocation.allocated_value
        
        # Request allocation from ResourceOrchestrator
        from autocoder_cc.resource_orchestrator import ResourceRequirement, ResourceType
        requirement = ResourceRequirement(
            component_name=component_name,
            component_type=component_type,
            resource_type=ResourceType.NETWORK_PORT,
            priority=1
        )
        
        try:
            if hasattr(self, '_current_system_blueprint'):
                system_name = self._current_system_blueprint.system.name
                new_manifest = self.resource_orchestrator.allocate_resources([requirement], system_name)
                
                # Find the allocated port
                for allocation in new_manifest.allocations:
                    if (allocation.component_name == component_name and 
                        allocation.resource_type.value == "network_port"):
                        self.logger.info(f"Successfully allocated port {allocation.allocated_value} for {component_name}")
                        return allocation.allocated_value
                        
        except Exception as e:
            self.logger.error(f"Failed to allocate port for {component_name}: {e}")
        
        raise RuntimeError(f"Unable to allocate port for {component_name} - ResourceOrchestrator allocation failed")
    
    def _format_container_ports(self, ports: List[int]) -> str:
        """Format container ports for Kubernetes manifest"""
        port_lines = []
        for port in ports:
            if port == self._get_metrics_port():
                port_lines.append(f"        - name: metrics")
            else:
                port_lines.append(f"        - name: http-{port}")
            port_lines.append(f"          containerPort: {port}")
            port_lines.append(f"          protocol: TCP")
        return "\n".join(port_lines)
    
    def _detect_redis_dependency(self, system_blueprint: ParsedSystemBlueprint) -> bool:
        """
        Comprehensive Redis dependency detection.
        
        Checks for Redis usage patterns including:
        1. Store components with Redis storage type
        2. Accumulator components (typically use Redis)
        3. Environment variables referencing Redis
        4. Component configurations mentioning Redis
        5. Components with Redis resource requirements
        """
        system = system_blueprint.system
        
        # Check 1: Store components with explicit Redis storage type
        for comp in system.components:
            if comp.type == "Store" and comp.config.get('storage_type') == 'redis':
                self.logger.debug(f"Redis detected: Store component {comp.name} uses Redis storage")
                return True
        
        # Check 2: Accumulator components (typically use Redis for caching/aggregation)
        for comp in system.components:
            if comp.type == "Accumulator":
                self.logger.debug(f"Redis detected: Accumulator component {comp.name} typically requires Redis")
                return True
        
        # Check 3: Component configurations referencing Redis
        for comp in system.components:
            config = comp.config or {}
            
            # Check for Redis URLs in configuration
            for key, value in config.items():
                if isinstance(value, str) and ('redis://' in value.lower() or 'redis_url' in key.lower()):
                    self.logger.debug(f"Redis detected: Component {comp.name} has Redis URL in config: {key}")
                    return True
                    
                # Check for Redis-specific configuration keys
                if 'redis' in key.lower():
                    self.logger.debug(f"Redis detected: Component {comp.name} has Redis config key: {key}")
                    return True
        
        # Check 4: Environment variables that suggest Redis usage
        # Look for common Redis environment variable patterns in component configurations
        redis_env_patterns = ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'CACHE_URL']
        for comp in system.components:
            config = comp.config or {}
            
            # Check environment section if it exists
            env_section = config.get('environment', {})
            if isinstance(env_section, dict):
                for env_key in env_section.keys():
                    if any(pattern in env_key.upper() for pattern in redis_env_patterns):
                        self.logger.debug(f"Redis detected: Component {comp.name} has Redis env var: {env_key}")
                        return True
        
        # Check 5: Component resource requirements
        for comp in system.components:
            if hasattr(comp, 'resources'):
                for resource in comp.resources:
                    if hasattr(resource, 'type') and 'redis' in str(resource.type).lower():
                        self.logger.debug(f"Redis detected: Component {comp.name} has Redis resource requirement")
                        return True
        
        # Check 6: Docker Compose file references Redis (if we're generating for an existing system)
        # This catches cases where Redis is referenced in existing deployment but not explicitly configured
        try:
            # Check if the generated Docker Compose environment variables reference Redis
            # This is a bit recursive but catches the fraud detection system case
            env_vars = self._build_k8s_env_vars(system_blueprint)
            for env_var in env_vars:
                if 'redis' in env_var.lower():
                    self.logger.debug(f"Redis detected: Environment variable suggests Redis usage: {env_var}")
                    return True
        except Exception:
            # If environment variable building fails, that's ok - just continue with other checks
            pass
        
        self.logger.debug("No Redis dependency detected")
        return False
    
    def _detect_postgres_dependency(self, system_blueprint: ParsedSystemBlueprint) -> bool:
        """Detect if PostgreSQL is needed based on Store components and configurations."""
        system = system_blueprint.system
        
        # Check for Store components that typically use PostgreSQL
        for comp in system.components:
            if comp.type == "Store":
                storage_type = comp.config.get('storage_type', '')
                if storage_type in ['postgres', 'postgresql', 'sql', '']:  # Default to PostgreSQL
                    self.logger.debug(f"PostgreSQL detected: Store component {comp.name}")
                    return True
        
        # Check for PostgreSQL URLs in configurations
        for comp in system.components:
            config = comp.config or {}
            for key, value in config.items():
                if isinstance(value, str) and ('postgresql://' in value.lower() or 'postgres://' in value.lower()):
                    self.logger.debug(f"PostgreSQL detected: Component {comp.name} has PostgreSQL URL")
                    return True
        
        return False
    
    def _detect_rabbitmq_dependency(self, system_blueprint: ParsedSystemBlueprint) -> bool:
        """Detect if RabbitMQ is needed based on message queue components."""
        system = system_blueprint.system
        
        # Check for MessageBus or queue-related components
        for comp in system.components:
            if comp.type in ["MessageBus", "EventProcessor"]:
                self.logger.debug(f"RabbitMQ detected: Component {comp.name} type {comp.type}")
                return True
                
            # Check for AMQP URLs
            config = comp.config or {}
            for key, value in config.items():
                if isinstance(value, str) and 'amqp://' in value.lower():
                    self.logger.debug(f"RabbitMQ detected: Component {comp.name} has AMQP URL")
                    return True
        
        return False
    
    def _detect_kafka_dependency(self, system_blueprint: ParsedSystemBlueprint) -> bool:
        """Detect if Kafka is needed based on streaming components."""
        system = system_blueprint.system
        
        # Check for streaming/event processing components
        for comp in system.components:
            if comp.type in ["StreamProcessor", "EventStream", "KafkaSource"]:
                self.logger.debug(f"Kafka detected: Component {comp.name} type {comp.type}")
                return True
                
            # Check for Kafka brokers in configuration
            config = comp.config or {}
            for key, value in config.items():
                if isinstance(value, str) and ('kafka' in value.lower() or 'broker' in key.lower()):
                    self.logger.debug(f"Kafka detected: Component {comp.name} has Kafka config")
                    return True
        
        return False
    
    def _get_docker_dependencies(self, system_name: str, needs_postgres: bool, needs_redis: bool) -> str:
        """Get Docker Compose service dependencies"""
        deps = []
        if needs_postgres:
            deps.append(f"      {system_name}-postgres:")
            deps.append("        condition: service_healthy")
        if needs_redis:
            deps.append(f"      {system_name}-redis:")
            deps.append("        condition: service_healthy")
        
        return "\n".join(deps) if deps else "      []"
    
    def _write_deployment_files(self, system_name: str, files: Dict[str, str]) -> None:
        """Write deployment files to output directory"""
        
        system_dir = self.output_dir / system_name
        system_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in files.items():
            full_path = system_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)


def main():
    """Test the production deployment generator"""
    from .system_blueprint_parser import SystemBlueprintParser
    
    # Test with example system
    parser = SystemBlueprintParser()
    generator = ProductionDeploymentGenerator(Path("./generated_deployments"))
    
    # Create a test blueprint
    test_blueprint_yaml = """
system:
  name: production_test_system
  description: System for testing production deployment generation
  version: 1.0.0
  
  components:
    - name: api_server
      type: APIEndpoint
      description: Main API server
      configuration:
        port: {generator_settings.api_port}
        host: "0.0.0.0"
      inputs:
        - name: input
          schema: RequestData
          
    - name: data_processor
      type: Transformer
      description: Processes requests
      configuration:
        batch_size: 10
      inputs:
        - name: input
          schema: RequestData
      outputs:
        - name: output
          schema: ProcessedData
          
    - name: data_store
      type: Store
      description: Stores processed data
      configuration:
        storage_type: postgresql
      inputs:
        - name: input
          schema: ProcessedData
          
    - name: ml_model
      type: Model
      description: ML scoring model
      configuration:
        model_type: classifier
      inputs:
        - name: input
          schema: ProcessedData
      outputs:
        - name: output
          schema: ScoredData
  
  bindings:
    - from: api_server.output
      to: data_processor.input
    - from: data_processor.output
      to: data_store.input
    - from: data_processor.output
      to: ml_model.input

configuration:
  environment: production
"""
    
    try:
        # Parse blueprint
        system_blueprint = parser.parse_string(test_blueprint_yaml)
        print(f"✅ Parsed system blueprint: {system_blueprint.system.name}")
        
        # Generate production deployment
        deployment = generator.generate_production_deployment(system_blueprint)
        print(f"✅ Generated production deployment artifacts")
        print(f"   Kubernetes manifests: {len(deployment.kubernetes_manifests)} files")
        print(f"   Docker Compose: {len(deployment.docker_compose)} characters")
        print(f"   GitHub Actions: {len(deployment.github_actions)} characters")
        print(f"   GitLab CI: {len(deployment.gitlab_ci)} characters")
        print(f"   Helm chart: {len(deployment.helm_chart)} files")
        
        # Show some sample output
        print(f"\n📄 Sample Kubernetes Deployment (first 20 lines):")
        k8s_deployment = deployment.kubernetes_manifests.get("deployment.yaml", "")
        for i, line in enumerate(k8s_deployment.split('\n')[:20], 1):
            print(f"{i:2d}: {line}")
            
    except Exception as e:
        print(f"❌ Failed to generate deployment: {e}")
        raise


if __name__ == "__main__":
    main()