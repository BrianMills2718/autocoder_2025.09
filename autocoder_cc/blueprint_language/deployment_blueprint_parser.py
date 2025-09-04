#!/usr/bin/env python3
"""
Deployment Blueprint Parser
Parses deployment and runtime configuration specifications
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re

from .blueprint_parser import ValidationError

@dataclass
class DeploymentConfiguration:
    """Parsed deployment configuration"""
    platform: str = "docker"
    target_environment: str = "development"
    container: Dict[str, Any] = field(default_factory=dict)
    kubernetes: Dict[str, Any] = field(default_factory=dict)
    cloud: Dict[str, Any] = field(default_factory=dict)
    external_services: List[Dict[str, Any]] = field(default_factory=list)
    networking: Dict[str, Any] = field(default_factory=dict)
    scaling: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeConfiguration:
    """Parsed runtime configuration"""
    timeouts: Dict[str, int] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnvironmentConfiguration:
    """Parsed environment configuration"""
    environment_variables: Dict[str, str] = field(default_factory=dict)
    config_files: List[Dict[str, Any]] = field(default_factory=list)
    secrets: List[Dict[str, Any]] = field(default_factory=list)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    database_connections: List[Dict[str, Any]] = field(default_factory=list)
    message_queue_connections: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ComponentRuntimeOverride:
    """Parsed component runtime override"""
    ports: List[Dict[str, Any]] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    resource_overrides: Dict[str, Any] = field(default_factory=dict)
    health_check: Dict[str, Any] = field(default_factory=dict)
    scaling: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentBlueprint:
    """Complete parsed deployment blueprint"""
    system_name: str
    architecture_version: str = "1.0.0"
    deployment: DeploymentConfiguration = field(default_factory=DeploymentConfiguration)
    runtime: RuntimeConfiguration = field(default_factory=RuntimeConfiguration)
    environment: EnvironmentConfiguration = field(default_factory=EnvironmentConfiguration)
    component_overrides: Dict[str, ComponentRuntimeOverride] = field(default_factory=dict)
    source_file: Optional[str] = None
    raw_blueprint: Dict[str, Any] = field(default_factory=dict)

class DeploymentBlueprintParser:
    """
    Parses deployment blueprints containing only runtime and deployment configuration
    No architectural design elements allowed
    """
    
    def __init__(self, schema_file: Optional[Path] = None):
        """Initialize parser with deployment schema"""
        self.schema_file = schema_file or Path(__file__).parent.parent.parent / "schemas" / "deployment_blueprint.schema.yaml"
        self.validation_errors: List[ValidationError] = []
        
    def parse_file(self, deployment_file: Path) -> DeploymentBlueprint:
        """Parse a deployment blueprint file"""
        self.validation_errors.clear()
        
        try:
            with open(deployment_file, 'r') as f:
                raw_blueprint = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML from {deployment_file}: {e}")
        
        # Validate basic structure
        self._validate_deployment_structure(raw_blueprint)
        
        # Parse into structured objects
        blueprint = self._parse_deployment_blueprint(raw_blueprint)
        blueprint.source_file = str(deployment_file)
        blueprint.raw_blueprint = raw_blueprint
        
        # Perform deployment validation
        self._validate_deployment_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Deployment blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def parse_string(self, deployment_yaml: str) -> DeploymentBlueprint:
        """Parse deployment blueprint from YAML string"""
        self.validation_errors.clear()
        
        try:
            raw_blueprint = yaml.safe_load(deployment_yaml)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML string: {e}")
        
        # Validate and parse
        self._validate_deployment_structure(raw_blueprint)
        blueprint = self._parse_deployment_blueprint(raw_blueprint)
        blueprint.raw_blueprint = raw_blueprint
        
        self._validate_deployment_semantics(blueprint)
        
        if self.validation_errors:
            error_summary = f"Deployment blueprint validation failed with {len(self.validation_errors)} errors"
            for error in self.validation_errors:
                error_summary += f"\n  {error.path}: {error.message}"
            raise ValueError(error_summary)
        
        return blueprint
    
    def _validate_deployment_structure(self, blueprint: Dict[str, Any]) -> None:
        """Validate deployment blueprint basic structure"""
        
        # Validate schema version
        if 'schema_version' not in blueprint:
            self.validation_errors.append(
                ValidationError("root", "Missing required 'schema_version' field")
            )
        
        if 'system_name' not in blueprint:
            self.validation_errors.append(
                ValidationError("root", "Missing required 'system_name' field")
            )
        
        if 'deployment' not in blueprint:
            self.validation_errors.append(
                ValidationError("root", "Missing required 'deployment' section")
            )
        
        # System name validation
        system_name = blueprint.get('system_name', '')
        if not re.match(r'^[a-z][a-z0-9_]*$', system_name):
            self.validation_errors.append(
                ValidationError(
                    "system_name",
                    f"System name '{system_name}' must be snake_case (lowercase letters, numbers, underscores)"
                )
            )
        
        # Validate no architectural configuration present
        self._validate_no_architectural_config(blueprint)
    
    def _validate_no_architectural_config(self, blueprint: Dict[str, Any]) -> None:
        """Ensure no architectural configuration is present"""
        
        # Check for architectural configuration in root
        forbidden_root_fields = ['system', 'components', 'bindings', 'patterns', 'schemas']
        for field in forbidden_root_fields:
            if field in blueprint:
                self.validation_errors.append(
                    ValidationError(
                        f"root.{field}",
                        f"Architectural field '{field}' not allowed in deployment blueprint"
                    )
                )
        
        # Check for architectural configuration in deployment
        deployment = blueprint.get('deployment', {})
        if 'architecture' in deployment:
            self.validation_errors.append(
                ValidationError(
                    "deployment.architecture",
                    "Architectural configuration not allowed in deployment blueprint"
                )
            )
    
    def _parse_deployment_blueprint(self, raw: Dict[str, Any]) -> DeploymentBlueprint:
        """Parse raw YAML into structured deployment blueprint"""
        
        # Parse deployment configuration
        deployment_data = raw.get('deployment', {})
        deployment_config = DeploymentConfiguration(
            platform=deployment_data.get('platform', 'docker'),
            target_environment=deployment_data.get('target_environment', 'development'),
            container=deployment_data.get('container', {}),
            kubernetes=deployment_data.get('kubernetes', {}),
            cloud=deployment_data.get('cloud', {}),
            external_services=deployment_data.get('external_services', []),
            networking=deployment_data.get('networking', {}),
            scaling=deployment_data.get('scaling', {}),
            security=deployment_data.get('security', {})
        )
        
        # Parse runtime configuration
        runtime_data = raw.get('runtime', {})
        runtime_config = RuntimeConfiguration(
            timeouts=runtime_data.get('timeouts', {}),
            resource_limits=runtime_data.get('resource_limits', {}),
            logging=runtime_data.get('logging', {}),
            monitoring=runtime_data.get('monitoring', {}),
            error_handling=runtime_data.get('error_handling', {})
        )
        
        # Parse environment configuration
        environment_data = raw.get('environment', {})
        environment_config = EnvironmentConfiguration(
            environment_variables=environment_data.get('environment_variables', {}),
            config_files=environment_data.get('config_files', []),
            secrets=environment_data.get('secrets', []),
            feature_flags=environment_data.get('feature_flags', {}),
            database_connections=environment_data.get('database_connections', []),
            message_queue_connections=environment_data.get('message_queue_connections', [])
        )
        
        # Parse component overrides
        component_overrides = {}
        for comp_name, override_data in raw.get('component_overrides', {}).items():
            component_overrides[comp_name] = ComponentRuntimeOverride(
                ports=override_data.get('ports', []),
                environment_variables=override_data.get('environment_variables', {}),
                resource_overrides=override_data.get('resource_overrides', {}),
                health_check=override_data.get('health_check', {}),
                scaling=override_data.get('scaling', {})
            )
        
        # Create deployment blueprint
        blueprint = DeploymentBlueprint(
            system_name=raw.get('system_name', ''),
            architecture_version=raw.get('architecture_version', '1.0.0'),
            deployment=deployment_config,
            runtime=runtime_config,
            environment=environment_config,
            component_overrides=component_overrides
        )
        
        return blueprint
    
    def _validate_deployment_semantics(self, blueprint: DeploymentBlueprint) -> None:
        """Perform comprehensive deployment validation"""
        
        # 1. Validate platform and environment consistency
        self._validate_platform_environment_consistency(blueprint)
        
        # 2. Validate external service connections
        self._validate_external_service_connections(blueprint)
        
        # 3. Validate resource limits
        self._validate_resource_limits(blueprint)
        
        # 4. Validate networking configuration
        self._validate_networking_configuration(blueprint)
        
        # 5. Validate security configuration
        self._validate_security_configuration(blueprint)
        
        # 6. Validate component overrides
        self._validate_component_overrides(blueprint)
    
    def _validate_platform_environment_consistency(self, blueprint: DeploymentBlueprint) -> None:
        """Validate platform and environment configuration consistency"""
        
        deployment = blueprint.deployment
        
        # Validate platform-specific configuration
        if deployment.platform == 'kubernetes':
            if not deployment.kubernetes:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.kubernetes",
                        "Kubernetes configuration required when platform is 'kubernetes'"
                    )
                )
        
        elif deployment.platform in ['aws_lambda', 'azure_functions', 'google_cloud_functions']:
            if not deployment.cloud:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.cloud",
                        f"Cloud configuration required when platform is '{deployment.platform}'"
                    )
                )
        
        # Validate environment-specific settings
        if deployment.target_environment == 'production':
            # Production environment checks
            if not deployment.security:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.security",
                        "Security configuration required for production environment"
                    )
                )
            
            if not blueprint.runtime.monitoring:
                self.validation_errors.append(
                    ValidationError(
                        "runtime.monitoring",
                        "Monitoring configuration required for production environment"
                    )
                )
    
    def _validate_external_service_connections(self, blueprint: DeploymentBlueprint) -> None:
        """Validate external service connections"""
        
        for service in blueprint.deployment.external_services:
            if 'name' not in service:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.external_services",
                        "External service missing required 'name' field"
                    )
                )
            
            if 'type' not in service:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.external_services",
                        "External service missing required 'type' field"
                    )
                )
            
            if 'connection' not in service:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.external_services",
                        "External service missing required 'connection' field"
                    )
                )
            
            # Validate connection configuration
            connection = service.get('connection', {})
            if 'host' not in connection:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.external_services.connection",
                        "Service connection missing required 'host' field"
                    )
                )
            
            if 'port' not in connection:
                self.validation_errors.append(
                    ValidationError(
                        "deployment.external_services.connection",
                        "Service connection missing required 'port' field"
                    )
                )
    
    def _validate_resource_limits(self, blueprint: DeploymentBlueprint) -> None:
        """Validate resource limits configuration"""
        
        resource_limits = blueprint.runtime.resource_limits
        
        # Validate memory limits
        if 'max_memory_mb' in resource_limits:
            memory_mb = resource_limits['max_memory_mb']
            if not isinstance(memory_mb, int) or memory_mb < 64 or memory_mb > 32768:
                self.validation_errors.append(
                    ValidationError(
                        "runtime.resource_limits.max_memory_mb",
                        f"Memory limit must be between 64 and 32768 MB, got {memory_mb}"
                    )
                )
        
        # Validate CPU limits
        if 'max_cpu_cores' in resource_limits:
            cpu_cores = resource_limits['max_cpu_cores']
            if not isinstance(cpu_cores, (int, float)) or cpu_cores < 0.1 or cpu_cores > 16.0:
                self.validation_errors.append(
                    ValidationError(
                        "runtime.resource_limits.max_cpu_cores",
                        f"CPU limit must be between 0.1 and 16.0 cores, got {cpu_cores}"
                    )
                )
        
        # Validate connection limits
        if 'max_connections' in resource_limits:
            connections = resource_limits['max_connections']
            if not isinstance(connections, int) or connections < 10 or connections > 10000:
                self.validation_errors.append(
                    ValidationError(
                        "runtime.resource_limits.max_connections",
                        f"Connection limit must be between 10 and 10000, got {connections}"
                    )
                )
    
    def _validate_networking_configuration(self, blueprint: DeploymentBlueprint) -> None:
        """Validate networking configuration"""
        
        networking = blueprint.deployment.networking
        
        # Validate port mappings
        if 'port_mappings' in networking:
            for port_mapping in networking['port_mappings']:
                if 'internal_port' not in port_mapping:
                    self.validation_errors.append(
                        ValidationError(
                            "deployment.networking.port_mappings",
                            "Port mapping missing required 'internal_port' field"
                        )
                    )
                
                if 'external_port' not in port_mapping:
                    self.validation_errors.append(
                        ValidationError(
                            "deployment.networking.port_mappings",
                            "Port mapping missing required 'external_port' field"
                        )
                    )
                
                # Validate port ranges
                for port_type in ['internal_port', 'external_port']:
                    if port_type in port_mapping:
                        port = port_mapping[port_type]
                        if not isinstance(port, int) or port < 1 or port > 65535:
                            self.validation_errors.append(
                                ValidationError(
                                    f"deployment.networking.port_mappings.{port_type}",
                                    f"Port must be between 1 and 65535, got {port}"
                                )
                            )
    
    def _validate_security_configuration(self, blueprint: DeploymentBlueprint) -> None:
        """Validate security configuration"""
        
        security = blueprint.deployment.security
        
        # Validate authentication configuration
        if 'authentication' in security:
            auth = security['authentication']
            
            # Validate JWT configuration
            if 'jwt' in auth:
                jwt_config = auth['jwt']
                if jwt_config.get('enabled', False):
                    algorithm = jwt_config.get('algorithm', 'RS256')
                    
                    if algorithm == 'HS256':
                        if 'secret_key' not in jwt_config:
                            self.validation_errors.append(
                                ValidationError(
                                    "deployment.security.authentication.jwt.secret_key",
                                    "JWT secret key required for HS256 algorithm"
                                )
                            )
                    
                    elif algorithm in ['RS256', 'ES256']:
                        if 'public_key' not in jwt_config:
                            self.validation_errors.append(
                                ValidationError(
                                    "deployment.security.authentication.jwt.public_key",
                                    f"JWT public key required for {algorithm} algorithm"
                                )
                            )
                        
                        if 'private_key' not in jwt_config:
                            self.validation_errors.append(
                                ValidationError(
                                    "deployment.security.authentication.jwt.private_key",
                                    f"JWT private key required for {algorithm} algorithm"
                                )
                            )
    
    def _validate_component_overrides(self, blueprint: DeploymentBlueprint) -> None:
        """Validate component runtime overrides"""
        
        for comp_name, override in blueprint.component_overrides.items():
            # Validate component name
            if not re.match(r'^[a-z][a-z0-9_]*$', comp_name):
                self.validation_errors.append(
                    ValidationError(
                        f"component_overrides.{comp_name}",
                        f"Component name '{comp_name}' must be snake_case"
                    )
                )
            
            # Validate port assignments
            for port_config in override.ports:
                if 'name' not in port_config:
                    self.validation_errors.append(
                        ValidationError(
                            f"component_overrides.{comp_name}.ports",
                            "Port configuration missing required 'name' field"
                        )
                    )
                
                if 'port' not in port_config:
                    self.validation_errors.append(
                        ValidationError(
                            f"component_overrides.{comp_name}.ports",
                            "Port configuration missing required 'port' field"
                        )
                    )
                
                # Validate port number
                if 'port' in port_config:
                    port = port_config['port']
                    if not isinstance(port, int) or port < 1024 or port > 65535:
                        self.validation_errors.append(
                            ValidationError(
                                f"component_overrides.{comp_name}.ports.port",
                                f"Port must be between 1024 and 65535, got {port}"
                            )
                        )
            
            # Validate resource overrides
            resource_overrides = override.resource_overrides
            if 'memory_mb' in resource_overrides:
                memory_mb = resource_overrides['memory_mb']
                if not isinstance(memory_mb, int) or memory_mb < 64:
                    self.validation_errors.append(
                        ValidationError(
                            f"component_overrides.{comp_name}.resource_overrides.memory_mb",
                            f"Memory override must be at least 64 MB, got {memory_mb}"
                        )
                    )
            
            if 'cpu_cores' in resource_overrides:
                cpu_cores = resource_overrides['cpu_cores']
                if not isinstance(cpu_cores, (int, float)) or cpu_cores < 0.1:
                    self.validation_errors.append(
                        ValidationError(
                            f"component_overrides.{comp_name}.resource_overrides.cpu_cores",
                            f"CPU override must be at least 0.1 cores, got {cpu_cores}"
                        )
                    )

def main():
    """Test the deployment blueprint parser"""
    parser = DeploymentBlueprintParser()
    
    # Test with a simple deployment blueprint
    test_blueprint = {
        'schema_version': '1.0.0',
        'system_name': 'test_system',
        'architecture_version': '1.0.0',
        'deployment': {
            'platform': 'docker',
            'target_environment': 'development',
            'container': {
                'base_image': 'python:3.11-slim'
            },
            'networking': {
                'port_mappings': [
                    {
                        'internal_port': 8000,
                        'external_port': 8080,
                        'protocol': 'TCP'
                    }
                ]
            },
            'security': {
                'authentication': {
                    'jwt': {
                        'enabled': True,
                        'algorithm': 'HS256',
                        'secret_key': 'dev-secret-key'
                    }
                }
            }
        },
        'runtime': {
            'timeouts': {
                'startup_timeout_ms': 30000,
                'request_timeout_ms': 30000
            },
            'resource_limits': {
                'max_memory_mb': 512,
                'max_cpu_cores': 1.0
            },
            'logging': {
                'level': 'INFO',
                'format': 'json'
            }
        },
        'environment': {
            'environment_variables': {
                'NODE_ENV': 'development',
                'DEBUG': 'true'
            },
            'feature_flags': {
                'new_feature': True
            }
        },
        'component_overrides': {
            'api_server': {
                'ports': [
                    {
                        'name': 'http',
                        'port': 8000,
                        'protocol': 'HTTP'
                    }
                ],
                'health_check': {
                    'enabled': True,
                    'path': '/health',
                    'interval_seconds': 30
                }
            }
        }
    }
    
    try:
        blueprint = parser.parse_string(yaml.dump(test_blueprint))
        print(f"✅ Successfully parsed deployment blueprint: {blueprint.system_name}")
        print(f"   Architecture version: {blueprint.architecture_version}")
        print(f"   Platform: {blueprint.deployment.platform}")
        print(f"   Environment: {blueprint.deployment.target_environment}")
        print(f"   Component overrides: {len(blueprint.component_overrides)}")
        
        # Show component overrides
        if blueprint.component_overrides:
            print(f"\n🔧 Component overrides:")
            for comp_name, override in blueprint.component_overrides.items():
                print(f"   - {comp_name}: {len(override.ports)} ports, {len(override.environment_variables)} env vars")
        
    except Exception as e:
        print(f"❌ Failed to parse deployment blueprint: {e}")

if __name__ == "__main__":
    main()