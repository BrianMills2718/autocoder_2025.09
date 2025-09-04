"""
Strict Service Connector with Zero Inference
Only uses explicit metadata - no fallback mechanisms
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from ..protocols.message_format import StandardMessage
from .message_bus_connector import MessageBusConnector, MessageBusType

try:
    import consul
except ImportError:
    consul = None

logger = logging.getLogger(__name__)


class ServiceDiscoveryError(Exception):
    """Service discovery errors with detailed context"""
    pass


class ServiceRegistrationError(Exception):
    """Service registration errors"""
    pass


class MetadataValidationError(Exception):
    """Metadata validation errors"""
    pass


class StrictMetadataSchema:
    """Strict metadata schema with zero tolerance for missing fields"""
    
    # ALL fields are required - no defaults, no inference
    REQUIRED_FIELDS = {
        "messaging_type": {
            "type": str,
            "allowed_values": ["rabbitmq", "kafka", "http"],
            "description": "Explicit messaging protocol type"
        },
        "health_endpoint": {
            "type": str,
            "validation": lambda x: x.startswith("/"),
            "description": "Complete health check endpoint URL path"
        },
        "version": {
            "type": str,
            "validation": lambda x: len(x.split(".")) == 3 and all(p.isdigit() for p in x.split(".")),
            "description": "Service version in semantic versioning format (x.y.z)"
        },
        "environment": {
            "type": str,
            "allowed_values": ["dev", "staging", "prod"],
            "description": "Deployment environment"
        },
        "protocol": {
            "type": str,
            "allowed_values": ["http", "https"],
            "description": "Service protocol"
        },
        "service_type": {
            "type": str,
            "allowed_values": ["api", "worker", "gateway", "service"],
            "description": "Type of service"
        }
    }
    
    @classmethod
    def validate_metadata(cls, metadata: Dict[str, Any], service_name: str) -> None:
        """
        Validate metadata with zero tolerance - all fields required
        Raises MetadataValidationError on any missing or invalid field
        """
        if not metadata:
            raise MetadataValidationError(
                f"Service '{service_name}' has no metadata. "
                f"Required fields: {list(cls.REQUIRED_FIELDS.keys())}"
            )
        
        errors = []
        
        # Check all required fields exist
        for field_name, requirements in cls.REQUIRED_FIELDS.items():
            if field_name not in metadata:
                errors.append(
                    f"Missing required field '{field_name}': {requirements['description']}"
                )
                continue
            
            value = metadata[field_name]
            
            # Type validation
            if not isinstance(value, requirements["type"]):
                errors.append(
                    f"Field '{field_name}' must be {requirements['type'].__name__}, "
                    f"got {type(value).__name__}"
                )
                continue
            
            # Value validation
            if "allowed_values" in requirements:
                if value not in requirements["allowed_values"]:
                    errors.append(
                        f"Field '{field_name}' value '{value}' not allowed. "
                        f"Must be one of: {requirements['allowed_values']}"
                    )
            
            # Custom validation
            if "validation" in requirements:
                try:
                    if not requirements["validation"](value):
                        errors.append(
                            f"Field '{field_name}' value '{value}' failed validation. "
                            f"Requirement: {requirements['description']}"
                        )
                except Exception as e:
                    errors.append(
                        f"Field '{field_name}' validation error: {str(e)}"
                    )
        
        if errors:
            raise MetadataValidationError(
                f"Service '{service_name}' metadata validation failed:\n" + 
                "\n".join(f"  - {error}" for error in errors) +
                f"\n\nProvided metadata: {metadata}"
            )


class StrictServiceInfo:
    """Service info with validated metadata only"""
    
    def __init__(self, name: str, address: str, port: int, 
                 metadata: Dict[str, Any], consul_service_id: str):
        self.name = name
        self.address = address
        self.port = port
        self.metadata = metadata  # Already validated
        self.consul_service_id = consul_service_id
        self.registered_at = datetime.now(timezone.utc)
        
        # Extract from validated metadata
        self.message_bus_type = self._get_message_bus_type(metadata["messaging_type"])
        self.health_endpoint = metadata["health_endpoint"]
        self.version = metadata["version"]
        self.environment = metadata["environment"]
        self.protocol = metadata["protocol"]
        self.service_type = metadata["service_type"]
        
        # Construct URL from validated data
        self.url = f"{self.protocol}://{self.address}:{self.port}"
    
    def _get_message_bus_type(self, messaging_type: str) -> MessageBusType:
        """Convert string to MessageBusType enum"""
        mapping = {
            "rabbitmq": MessageBusType.RABBITMQ,
            "kafka": MessageBusType.KAFKA,
            "http": MessageBusType.HTTP
        }
        return mapping[messaging_type]


class StrictServiceConnector:
    """
    Service connector with absolutely zero inference
    All metadata must be explicitly provided - no fallbacks
    """
    
    def __init__(self, service_name: str, message_bus_connector: MessageBusConnector,
                 consul_host: str = "localhost", consul_port: int = 8500):
        self.service_name = service_name
        self.message_bus = message_bus_connector
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.service_id = f"{service_name}_{uuid.uuid4().hex[:8]}"
        
        if consul is None:
            raise ImportError("python-consul package is required for service discovery")
        
        try:
            self.consul_client = consul.Consul(host=consul_host, port=consul_port)
            # Test connection
            self.consul_client.agent.self()
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Consul at {consul_host}:{consul_port}: {e}"
            )
    
    async def register_service(self, 
                             address: str,
                             port: int,
                             metadata: Dict[str, Any]) -> None:
        """
        Register service with strict metadata validation
        NO defaults, NO inference - all fields required
        """
        try:
            # Validate metadata BEFORE any processing
            StrictMetadataSchema.validate_metadata(metadata, self.service_name)
            
            logger.info(
                f"Registering service {self.service_name} with validated metadata: {metadata}"
            )
            
            # All metadata is now validated
            health_url = f"{metadata['protocol']}://{address}:{port}{metadata['health_endpoint']}"
            
            # Register with Consul using validated metadata
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.agent.service.register,
                self.service_name,      # name
                self.service_id,        # service_id
                address,                # address
                port,                   # port
                [],                     # tags (not used - metadata only)
                consul.Check.http(health_url, interval="10s", timeout="5s"),
                None,                   # token
                metadata,               # validated metadata
                None                    # enable_tag_override
            )
            
            logger.info(
                f"Successfully registered service {self.service_name} "
                f"at {address}:{port} with messaging type {metadata['messaging_type']}"
            )
            
        except MetadataValidationError:
            # Re-raise validation errors with full context
            raise
        except Exception as e:
            raise ServiceRegistrationError(
                f"Failed to register service {self.service_name}: {e}"
            )
    
    async def find_service_strict_metadata_only(self, service_name: str) -> StrictServiceInfo:
        """
        Find service using ONLY explicit metadata
        NO inference, NO fallbacks, NO tag checking
        """
        try:
            # Query Consul for service
            _, service_data = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.consul_client.health.service, 
                service_name, 
                True  # healthy only
            )
            
            if not service_data:
                raise ServiceDiscoveryError(
                    f"No healthy instances found for service '{service_name}'"
                )
            
            # Use first healthy instance
            instance = service_data[0]
            service_def = instance['Service']
            
            # Extract metadata
            metadata = service_def.get('Meta', {})
            
            # Validate metadata - will raise if incomplete
            try:
                StrictMetadataSchema.validate_metadata(metadata, service_name)
            except MetadataValidationError as e:
                # Provide helpful error for incomplete services
                raise ServiceDiscoveryError(
                    f"Service '{service_name}' found but metadata incomplete:\n{str(e)}\n\n"
                    f"To fix: Update service registration with complete metadata:\n"
                    f"consul_client.agent.service.register(\n"
                    f"    name='{service_name}',\n"
                    f"    ...,\n"
                    f"    meta={{\n"
                    f"        'messaging_type': 'rabbitmq|kafka|http',\n"
                    f"        'health_endpoint': '/health',\n"
                    f"        'version': '1.0.0',\n"
                    f"        'environment': 'dev|staging|prod',\n"
                    f"        'protocol': 'http|https',\n"
                    f"        'service_type': 'api|worker|gateway|service'\n"
                    f"    }}\n"
                    f")"
                )
            
            # Create service info from validated metadata
            return StrictServiceInfo(
                name=service_name,
                address=service_def.get('Address', 'localhost'),
                port=service_def.get('Port', 8080),
                metadata=metadata,
                consul_service_id=service_def['ID']
            )
            
        except ServiceDiscoveryError:
            # Re-raise with context
            raise
        except Exception as e:
            raise ServiceDiscoveryError(
                f"Failed to discover service '{service_name}': {e}"
            )
    
    async def discover_all_services_strict(self) -> List[StrictServiceInfo]:
        """Discover all services with strict metadata validation"""
        try:
            # Get all service names
            _, services = await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.catalog.services
            )
            
            discovered_services = []
            validation_failures = []
            
            for service_name in services:
                if service_name == "consul":  # Skip consul itself
                    continue
                
                try:
                    service_info = await self.find_service_strict_metadata_only(service_name)
                    discovered_services.append(service_info)
                except ServiceDiscoveryError as e:
                    validation_failures.append({
                        "service": service_name,
                        "error": str(e)
                    })
            
            # Log validation failures
            if validation_failures:
                logger.warning(
                    f"Found {len(validation_failures)} services with invalid metadata:\n" +
                    "\n".join(f"  - {f['service']}: {f['error']}" for f in validation_failures)
                )
            
            logger.info(
                f"Discovered {len(discovered_services)} valid services "
                f"({len(validation_failures)} failed validation)"
            )
            
            return discovered_services
            
        except Exception as e:
            raise ServiceDiscoveryError(f"Failed to discover services: {e}")
    
    async def send_message_to_service(self, 
                                    service_name: str,
                                    message: StandardMessage) -> None:
        """Send message to service discovered with strict metadata"""
        try:
            # Find service with strict validation
            service_info = await self.find_service_strict_metadata_only(service_name)
            
            # Update message destination
            message.destination_service = service_name
            
            # Send through appropriate message bus
            destination = f"{service_name}_queue"
            await self.message_bus.publish_message(message, destination)
            
            logger.debug(
                f"Sent message {message.id} to service {service_name} "
                f"via {service_info.message_bus_type.value}"
            )
            
        except Exception as e:
            raise ServiceDiscoveryError(
                f"Failed to send message to service '{service_name}': {e}"
            )
    
    async def unregister_service(self) -> None:
        """Unregister this service from Consul"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.agent.service.deregister,
                self.service_id
            )
            logger.info(f"Unregistered service {self.service_name}")
        except Exception as e:
            raise ServiceRegistrationError(
                f"Failed to unregister service: {e}"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check connector health"""
        try:
            # Check Consul connectivity
            consul_leader = await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.status.leader
            )
            consul_healthy = bool(consul_leader)
            
            # Check message bus
            message_bus_health = await self.message_bus.health_check()
            
            # Count services
            services = await self.discover_all_services_strict()
            
            return {
                "service_name": self.service_name,
                "consul_healthy": consul_healthy,
                "consul_leader": consul_leader if consul_healthy else None,
                "message_bus_healthy": message_bus_health.get("healthy", False),
                "discovered_services": len(services),
                "status": "healthy" if consul_healthy and message_bus_health.get("healthy", False) else "unhealthy"
            }
            
        except Exception as e:
            return {
                "service_name": self.service_name,
                "status": "unhealthy",
                "error": str(e)
            }


# Example of proper service registration with complete metadata
def example_service_registration():
    """Example showing how to register a service with complete metadata"""
    
    connector = StrictServiceConnector(
        service_name="my-service",
        message_bus_connector=None,  # Would be actual connector
        consul_host="localhost",
        consul_port=8500
    )
    
    # Complete metadata - all fields required
    complete_metadata = {
        "messaging_type": "rabbitmq",      # Required: rabbitmq, kafka, or http
        "health_endpoint": "/health",       # Required: must start with /
        "version": "1.2.3",                # Required: semantic versioning
        "environment": "prod",              # Required: dev, staging, or prod
        "protocol": "http",                 # Required: http or https
        "service_type": "api"               # Required: api, worker, gateway, or service
    }
    
    # This would succeed
    # await connector.register_service("localhost", 8080, complete_metadata)
    
    # This would fail - missing required fields
    incomplete_metadata = {
        "messaging_type": "rabbitmq",
        "version": "1.0.0"
        # Missing: health_endpoint, environment, protocol, service_type
    }
    
    # This would raise MetadataValidationError
    # await connector.register_service("localhost", 8080, incomplete_metadata)