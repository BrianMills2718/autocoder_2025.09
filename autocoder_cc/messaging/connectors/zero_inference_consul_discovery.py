#!/usr/bin/env python3
"""
Zero-Inference Consul Service Discovery
Service discovery that requires explicit metadata - no inference allowed
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass

try:
    import consul
except ImportError:
    consul = None

logger = logging.getLogger(__name__)


class ServiceDiscoveryError(Exception):
    """Service discovery-related errors"""
    pass


@dataclass
class ValidationResult:
    """Result of metadata validation"""
    is_complete: bool
    missing_fields: List[str]
    invalid_fields: List[str]
    validation_errors: List[str]


@dataclass
class ServiceInfo:
    """Service information with explicit metadata only"""
    name: str
    messaging_type: str
    health_endpoint: str
    version: str
    metadata_source: str
    validation_result: ValidationResult


class StrictMetadataValidator:
    """Validates that all required metadata is explicitly present"""
    
    REQUIRED_METADATA_SCHEMA = {
        "messaging_type": {
            "type": str,
            "values": ["rabbitmq", "kafka", "http"],
            "description": "Explicit messaging protocol type"
        },
        "health_endpoint": {
            "type": str,
            "format": "url",
            "description": "Health check endpoint URL"
        },
        "version": {
            "type": str,
            "format": "semver",
            "description": "Service version (semantic versioning)"
        },
        "environment": {
            "type": str,
            "values": ["dev", "staging", "prod"],
            "description": "Deployment environment"
        }
    }
    
    def validate_service_metadata(self, consul_data: Dict) -> ValidationResult:
        """Validate that all required metadata is explicitly present"""
        
        meta = consul_data.get("Meta", {})
        missing_fields = []
        invalid_fields = []
        
        for field_name, schema in self.REQUIRED_METADATA_SCHEMA.items():
            if field_name not in meta:
                missing_fields.append(field_name)
            else:
                value = meta[field_name]
                if not self._validate_field_value(value, schema):
                    invalid_fields.append(f"{field_name}={value}")
        
        validation_errors = self._generate_validation_errors(missing_fields, invalid_fields)
        
        return ValidationResult(
            is_complete=len(missing_fields) == 0 and len(invalid_fields) == 0,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            validation_errors=validation_errors
        )
    
    def _validate_field_value(self, value: Any, schema: Dict[str, Any]) -> bool:
        """Validate field value against schema"""
        
        # Type validation
        if not isinstance(value, schema["type"]):
            return False
        
        # Value validation
        if "values" in schema and value not in schema["values"]:
            return False
        
        # Format validation
        if "format" in schema:
            if schema["format"] == "url" and not value.startswith("/"):
                return False
            elif schema["format"] == "semver":
                import re
                semver_pattern = r'^\d+\.\d+\.\d+$'
                if not re.match(semver_pattern, value):
                    return False
        
        return True
    
    def _generate_validation_errors(self, missing_fields: List[str], invalid_fields: List[str]) -> List[str]:
        """Generate detailed validation error messages"""
        
        errors = []
        
        for field in missing_fields:
            schema = self.REQUIRED_METADATA_SCHEMA[field]
            if "values" in schema:
                errors.append(
                    f"Missing required field '{field}': {schema['description']}. "
                    f"Must be one of: {schema['values']}"
                )
            else:
                errors.append(
                    f"Missing required field '{field}': {schema['description']}"
                )
        
        for field_value in invalid_fields:
            field_name = field_value.split("=")[0]
            schema = self.REQUIRED_METADATA_SCHEMA[field_name]
            if "values" in schema:
                errors.append(
                    f"Invalid field '{field_value}': must be one of {schema['values']}"
                )
            else:
                errors.append(f"Invalid field '{field_value}': {schema['description']}")
        
        return errors


class ZeroInferenceConsulDiscovery:
    """Service discovery that requires explicit metadata - no inference allowed"""
    
    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.consul_client = None
        self.validator = StrictMetadataValidator()
        
        # Initialize Consul client
        if consul is None:
            raise ImportError("python-consul package is required for service discovery")
        
        try:
            self.consul_client = consul.Consul(host=consul_host, port=consul_port)
        except Exception as e:
            raise ServiceDiscoveryError(f"Failed to initialize Consul client at {consul_host}:{consul_port}: {e}")
    
    async def find_service_strict(self, service_name: str) -> ServiceInfo:
        """Find service using only explicit metadata - fail if incomplete"""
        
        consul_data = await self._get_consul_service_data(service_name)
        
        # Validate required metadata exists
        validation_result = self.validator.validate_service_metadata(consul_data)
        if not validation_result.is_complete:
            raise ServiceDiscoveryError(
                f"Service {service_name} missing required metadata: {validation_result.missing_fields}. "
                f"Required: messaging_type, health_endpoint, version. "
                f"Add to Consul with: consul kv put service/{service_name}/config "
                f"'{{\"messaging_type\": \"rabbitmq\"}}'"
            )
        
        # Extract messaging type from explicit metadata only
        messaging_type = self._extract_messaging_type_explicit_only(consul_data)
        
        meta = consul_data["Meta"]
        
        return ServiceInfo(
            name=service_name,
            messaging_type=messaging_type,
            health_endpoint=meta["health_endpoint"],
            version=meta["version"],
            metadata_source="consul_explicit_only",
            validation_result=validation_result
        )
    
    async def _get_consul_service_data(self, service_name: str) -> Dict:
        """Get service data from Consul"""
        
        try:
            # Query Consul for healthy service instances
            _, service_data = await asyncio.get_event_loop().run_in_executor(
                None, self.consul_client.health.service, service_name, True  # passing=True for healthy only
            )
            
            if not service_data:
                raise ServiceDiscoveryError(f"No healthy instances found for service {service_name}")
            
            # Use first healthy instance
            instance = service_data[0]
            return instance['Service']
            
        except consul.ConsulException as e:
            raise ServiceDiscoveryError(f"Failed to query Consul for service {service_name}: {e}")
        except Exception as e:
            raise ServiceDiscoveryError(f"Service discovery error for {service_name}: {e}")
    
    def _extract_messaging_type_explicit_only(self, consul_data: Dict) -> str:
        """Extract messaging type using explicit metadata only - no inference"""
        
        meta = consul_data.get("Meta", {})
        
        # Check explicit metadata field (primary source)
        if "messaging_type" in meta:
            messaging_type = meta["messaging_type"]
            if messaging_type in ["rabbitmq", "kafka", "http"]:
                return messaging_type
            else:
                raise ServiceDiscoveryError(
                    f"Invalid messaging_type '{messaging_type}'. Must be: rabbitmq, kafka, http"
                )
        
        # Check explicit service tags (secondary source)
        tags = consul_data.get("Tags", [])
        for tag in tags:
            if tag.startswith("messaging_type="):
                messaging_type = tag.split("=", 1)[1]
                if messaging_type in ["rabbitmq", "kafka", "http"]:
                    return messaging_type
        
        # NO INFERENCE - fail immediately
        raise ServiceDiscoveryError(
            f"Service has no explicit messaging_type metadata. "
            f"Add to Consul: messaging_type=rabbitmq|kafka|http"
        )
    
    async def validate_all_services(self) -> Dict[str, ValidationResult]:
        """Validate all services in Consul registry"""
        
        try:
            # Get all services from Consul
            _, services = await asyncio.get_event_loop().run_in_executor(
                None, self.consul_client.catalog.services
            )
            
            validation_results = {}
            
            for service_name in services:
                try:
                    consul_data = await self._get_consul_service_data(service_name)
                    validation_result = self.validator.validate_service_metadata(consul_data)
                    validation_results[service_name] = validation_result
                    
                except Exception as e:
                    validation_results[service_name] = ValidationResult(
                        is_complete=False,
                        missing_fields=["all"],
                        invalid_fields=[],
                        validation_errors=[f"Service discovery failed: {e}"]
                    )
            
            return validation_results
            
        except consul.ConsulException as e:
            raise ServiceDiscoveryError(f"Failed to list services from Consul: {e}")
        except Exception as e:
            raise ServiceDiscoveryError(f"Validation error: {e}")
    
    async def register_service_with_metadata(self, service_name: str, host: str, port: int,
                                           messaging_type: str, health_endpoint: str, 
                                           version: str, environment: str = "dev") -> None:
        """Register service with complete required metadata"""
        
        # Validate input parameters first
        if messaging_type not in ["rabbitmq", "kafka", "http"]:
            raise ValueError(f"Invalid messaging_type: {messaging_type}")
        
        if environment not in ["dev", "staging", "prod"]:
            raise ValueError(f"Invalid environment: {environment}")
        
        if not health_endpoint.startswith("/"):
            raise ValueError(f"Health endpoint must start with '/': {health_endpoint}")
        
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ValueError(f"Version must follow semantic versioning (x.y.z): {version}")
        
        # Prepare complete metadata
        metadata = {
            "messaging_type": messaging_type,
            "health_endpoint": health_endpoint,
            "version": version,
            "environment": environment,
            "registered_by": "zero_inference_discovery",
            "schema_validated": "true",
            "registration_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Prepare service tags
        tags = [
            f"messaging_type={messaging_type}",
            f"version={version}",
            f"environment={environment}",
            "zero_inference_compliant"
        ]
        
        try:
            # Register service with Consul
            service_id = f"{service_name}_{host}_{port}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.agent.service.register,
                service_name,
                service_id,
                host,
                port,
                tags,
                consul.Check.http(f"http://{host}:{port}{health_endpoint}", interval="10s"),
                None,  # token
                metadata,
                None   # enable_tag_override
            )
            
            logger.info(
                f"Registered service {service_name} with complete metadata at {host}:{port} "
                f"using {messaging_type} messaging"
            )
            
        except consul.ConsulException as e:
            raise ServiceDiscoveryError(f"Failed to register service with Consul: {e}")
        except Exception as e:
            raise ServiceDiscoveryError(f"Service registration error: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Consul connection"""
        
        try:
            # Test Consul connectivity
            await asyncio.get_event_loop().run_in_executor(
                None, self.consul_client.status.leader
            )
            
            # Validate all services
            validation_results = await self.validate_all_services()
            
            total_services = len(validation_results)
            valid_services = sum(1 for result in validation_results.values() if result.is_complete)
            
            return {
                "consul_healthy": True,
                "consul_host": self.consul_host,
                "consul_port": self.consul_port,
                "total_services": total_services,
                "valid_services": valid_services,
                "invalid_services": total_services - valid_services,
                "validation_results": {
                    name: {
                        "is_complete": result.is_complete,
                        "missing_fields": result.missing_fields,
                        "invalid_fields": result.invalid_fields
                    }
                    for name, result in validation_results.items()
                },
                "status": "healthy" if total_services == valid_services else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "consul_healthy": False,
                "consul_host": self.consul_host,
                "consul_port": self.consul_port,
                "error": str(e),
                "status": "unhealthy"
            }


# Integration with existing service connector
def create_zero_inference_discovery(consul_host: str = "localhost", 
                                   consul_port: int = 8500) -> ZeroInferenceConsulDiscovery:
    """Create zero-inference service discovery instance"""
    return ZeroInferenceConsulDiscovery(consul_host, consul_port)


async def main():
    """Test zero-inference service discovery"""
    
    # Create discovery instance
    discovery = ZeroInferenceConsulDiscovery()
    
    try:
        # Test health check
        health = await discovery.health_check()
        print(f"Consul Health: {health}")
        
        # Test service registration with complete metadata
        await discovery.register_service_with_metadata(
            service_name="test_service",
            host="localhost",
            port=8080,
            messaging_type="rabbitmq",
            health_endpoint="/health",
            version="1.0.0",
            environment="dev"
        )
        
        # Test service discovery
        service_info = await discovery.find_service_strict("test_service")
        print(f"Found service: {service_info}")
        
        # Test validation
        validation_results = await discovery.validate_all_services()
        print(f"Validation results: {validation_results}")
        
    except ServiceDiscoveryError as e:
        print(f"Service discovery error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())