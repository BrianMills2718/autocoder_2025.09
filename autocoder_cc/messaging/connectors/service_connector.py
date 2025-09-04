"""
Service Connector for Service Discovery and Communication

This module provides service discovery and connection management capabilities.
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


class MessagingError(Exception):
    """Base exception for messaging operations"""
    pass


class ConnectionError(MessagingError):
    """Connection-related messaging errors"""
    pass


class ServiceDiscoveryError(MessagingError):
    """Service discovery-related errors"""
    pass


class ServiceRegistrationError(MessagingError):
    """Service registration-related errors"""
    pass


class ConsulSchemaValidator:
    """Tool to validate and enforce Consul service metadata schema"""
    
    REQUIRED_METADATA = {
        "messaging_type": {"type": str, "values": ["rabbitmq", "kafka", "http"]},
        "health_endpoint": {"type": str, "format": "url_path"},
        "version": {"type": str, "format": "semver"},
        "environment": {"type": str, "values": ["dev", "staging", "prod"]}
    }
    
    def validate_service_registration(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service data before Consul registration"""
        
        # Extract metadata from service data
        metadata = service_data.get('metadata', {})
        
        validation_errors = []
        
        # Validate required fields
        for field_name, requirements in self.REQUIRED_METADATA.items():
            if field_name not in metadata:
                validation_errors.append(f"Required metadata field '{field_name}' missing")
                continue
            
            field_value = metadata[field_name]
            
            # Type validation
            if not isinstance(field_value, requirements["type"]):
                validation_errors.append(
                    f"Metadata field '{field_name}' must be {requirements['type'].__name__}, "
                    f"got {type(field_value).__name__}"
                )
                continue
            
            # Value validation
            if "values" in requirements and field_value not in requirements["values"]:
                validation_errors.append(
                    f"Metadata field '{field_name}' value '{field_value}' not in "
                    f"allowed values: {requirements['values']}"
                )
            
            # Format validation
            if "format" in requirements:
                if requirements["format"] == "url_path" and not field_value.startswith("/"):
                    validation_errors.append(
                        f"Metadata field '{field_name}' must be a valid URL path starting with '/'"
                    )
                elif requirements["format"] == "semver":
                    import re
                    semver_pattern = r'^\d+\.\d+\.\d+$'
                    if not re.match(semver_pattern, field_value):
                        validation_errors.append(
                            f"Metadata field '{field_name}' must follow semantic versioning (x.y.z)"
                        )
        
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors,
                "service_name": service_data.get('name', 'unknown')
            }
        
        return {
            "valid": True,
            "metadata": metadata,
            "service_name": service_data.get('name'),
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }


class ServiceInfo:
    """Information about a service"""
    
    def __init__(self, name: str, url: str, message_bus_type: MessageBusType,
                 metadata: Dict[str, Any] = None, health_endpoint: str = None,
                 consul_service_id: str = None):
        self.name = name
        self.url = url
        self.message_bus_type = message_bus_type
        self.metadata = metadata or {}
        self.health_endpoint = health_endpoint or "/health"
        self.consul_service_id = consul_service_id
        self.registered_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_healthy = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert service info to dictionary"""
        return {
            "name": self.name,
            "url": self.url,
            "message_bus_type": self.message_bus_type.value,
            "metadata": self.metadata,
            "health_endpoint": self.health_endpoint,
            "consul_service_id": self.consul_service_id,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_healthy": self.is_healthy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create service info from dictionary"""
        service = cls(
            name=data["name"],
            url=data["url"],
            message_bus_type=MessageBusType(data["message_bus_type"]),
            metadata=data.get("metadata", {}),
            health_endpoint=data.get("health_endpoint", "/health"),
            consul_service_id=data.get("consul_service_id")
        )
        
        if "registered_at" in data:
            service.registered_at = datetime.fromisoformat(data["registered_at"])
        if "last_heartbeat" in data:
            service.last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        if "is_healthy" in data:
            service.is_healthy = data["is_healthy"]
            
        return service


class ServiceConnector:
    """Service discovery and connection management with Consul integration"""
    
    def __init__(self, service_name: str, message_bus_connector: MessageBusConnector, 
                 consul_host: str = "localhost", consul_port: int = 8500):
        self.service_name = service_name
        self.message_bus = message_bus_connector
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.consul_client = None
        self.service_id = f"{service_name}_{uuid.uuid4().hex[:8]}"
        self.health_check_interval = 30  # seconds
        self.health_check_task = None
        self.is_running = False
        
        # Initialize Consul client
        if consul is None:
            raise ImportError("python-consul package is required for distributed service discovery")
        
        try:
            self.consul_client = consul.Consul(host=consul_host, port=consul_port)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Consul client at {consul_host}:{consul_port}: {e}")
        
    async def start(self) -> None:
        """Start the service connector"""
        try:
            logger.info(f"Starting service connector for {self.service_name}")
            
            # Connect to message bus
            await self.message_bus.connect()
            
            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.is_running = True
            logger.info(f"Service connector started for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to start service connector: {e}")
            raise RuntimeError(f"Failed to start service connector: {e}")
    
    async def stop(self) -> None:
        """Stop the service connector"""
        try:
            logger.info(f"Stopping service connector for {self.service_name}")
            
            self.is_running = False
            
            # Cancel health check task
            if self.health_check_task and not self.health_check_task.done():
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect from message bus
            await self.message_bus.disconnect()
            
            logger.info(f"Service connector stopped for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Error stopping service connector: {e}")
    
    async def register_service(self, service_info: ServiceInfo) -> None:
        """Register a service with distributed Consul registry with validated metadata schema"""
        try:
            # CRITICAL: Validate metadata schema before registration
            schema_validator = ConsulSchemaValidator()
            
            # Prepare service data for validation
            service_data = {
                'name': service_info.name,
                'metadata': {
                    'messaging_type': service_info.message_bus_type.value,
                    'health_endpoint': service_info.health_endpoint,
                    'version': service_info.metadata.get('version', '1.0.0'),
                    'environment': service_info.metadata.get('environment', 'dev'),
                    **service_info.metadata
                }
            }
            
            # Validate before registration
            validation_result = schema_validator.validate_service_registration(service_data)
            
            if not validation_result["valid"]:
                error_msg = f"Service registration validation failed: {validation_result['errors']}"
                logger.error(error_msg)
                raise ServiceRegistrationError(error_msg)
            
            logger.info(f"Service {service_info.name} metadata validation passed: {validation_result}")
            
            # Extract host and port from URL
            url_parts = service_info.url.replace("://", "").split(":")
            if len(url_parts) >= 2:
                host = url_parts[0].split("/")[0]
                port = int(url_parts[1].split("/")[0])
            else:
                host = "localhost"
                port = 8080
            
            # Prepare service tags with explicit messaging type
            service_tags = [
                f"messaging_type={service_info.message_bus_type.value}",
                f"version={validation_result['metadata']['version']}",
                f"environment={validation_result['metadata']['environment']}"
            ]
            
            # Add component-specific tags if available
            if 'component_type' in service_info.metadata:
                service_tags.append(f"type:{service_info.metadata['component_type']}")
            
            # Use validated metadata for Consul registration
            consul_meta = validation_result['metadata']
            consul_meta.update({
                'registered_by': 'autocoder_cc',
                'schema_validated': 'true',
                'validation_timestamp': validation_result['validation_timestamp']
            })
            
            # Register service with Consul with validated metadata
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.agent.service.register,
                service_info.name,
                self.service_id,
                host,
                port,
                service_tags,
                consul.Check.http(f"{service_info.url}{service_info.health_endpoint}", interval="10s"),
                None,  # token
                consul_meta,  # validated metadata
                None   # enable_tag_override
            )
            
            # Create destination for service if needed
            await self.message_bus.create_destination(
                f"{service_info.name}_queue",
                {"durable": True}
            )
            
            logger.info(
                f"Registered service {service_info.name} with Consul at {host}:{port} "
                f"using {service_info.message_bus_type.value} with validated metadata schema"
            )
            
        except ServiceRegistrationError:
            # Re-raise validation errors
            raise
        except consul.ConsulException as e:
            raise ServiceRegistrationError(f"Failed to register service with Consul: {e}")
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise ServiceRegistrationError(f"Failed to register service: {e}")
    
    async def unregister_service(self, service_name: str) -> None:
        """Unregister a service from Consul registry"""
        try:
            # Deregister from Consul
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.agent.service.deregister,
                self.service_id
            )
            
            logger.info(f"Unregistered service {service_name} from Consul")
            
        except consul.ConsulException as e:
            raise ServiceRegistrationError(f"Failed to unregister service from Consul: {e}")
        except Exception as e:
            logger.error(f"Failed to unregister service: {e}")
            raise ServiceRegistrationError(f"Failed to unregister service: {e}")
    
    async def discover_services(self) -> List[ServiceInfo]:
        """Discover all registered services from Consul"""
        try:
            # Get all services from Consul
            _, services = await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.catalog.services
            )
            
            service_list = []
            for service_name in services:
                service_info = await self.find_service(service_name)
                if service_info:
                    service_list.append(service_info)
            
            return service_list
            
        except consul.ConsulException as e:
            raise ServiceDiscoveryError(f"Failed to discover services from Consul: {e}")
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            raise ServiceDiscoveryError(f"Failed to discover services: {e}")
    
    async def find_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Find service using ONLY explicit metadata - immediate failure if incomplete"""
        try:
            # Query Consul for healthy service instances
            _, service_data = await asyncio.get_event_loop().run_in_executor(
                None, self.consul_client.health.service, service_name, True  # passing=True for healthy only
            )
            
            if not service_data:
                raise ServiceDiscoveryError(f"No healthy instances found for service {service_name}")
            
            # Use first healthy instance
            instance = service_data[0]
            service_def = instance['Service']
            
            # Extract service metadata from Consul - NO TAG PROCESSING
            service_meta = service_def.get('Meta', {})
            
            # IMMEDIATE FAILURE if metadata incomplete - no processing beyond this point
            try:
                validation_result = self.validate_service_metadata_schema(service_meta)
                logger.info(f"Service {service_name} complete metadata validation passed")
            except ServiceDiscoveryError as e:
                # Enhance error message with registration instructions
                enhanced_error = (
                    f"Service '{service_name}' metadata validation failed: {e}\n\n"
                    f"REQUIRED: Complete metadata registration in Consul:\n"
                    f"consul_client.agent.service.register(\n"
                    f"    name='{service_name}',\n"
                    f"    service_id='unique_id',\n"
                    f"    address='host',\n"
                    f"    port=port,\n"
                    f"    meta={{\n"
                    f"        'messaging_type': 'rabbitmq|kafka|http',\n"
                    f"        'health_endpoint': '/health',\n"
                    f"        'version': 'x.y.z',\n"
                    f"        'environment': 'dev|staging|prod'\n"
                    f"    }}\n"
                    f")\n\n"
                    f"NO inference or fallbacks allowed."
                )
                logger.error(enhanced_error)
                raise ServiceDiscoveryError(enhanced_error)
            
            # Extract messaging type using ONLY explicit metadata - zero inference
            message_bus_type = self._extract_message_bus_type_from_consul([], service_meta)
            
            # Construct service URL using ONLY explicit metadata
            service_url = self._construct_service_url_from_metadata(service_def, service_meta)
            
            # Extract health endpoint from ONLY explicit metadata - no defaults
            if 'health_endpoint' not in service_meta:
                raise ServiceDiscoveryError(
                    f"Service '{service_name}' missing required 'health_endpoint' metadata. "
                    f"Add explicit health_endpoint to service registration."
                )
            health_endpoint = service_meta['health_endpoint']
            
            return ServiceInfo(
                name=service_name,
                url=service_url,
                message_bus_type=message_bus_type,
                health_endpoint=health_endpoint,
                metadata={
                    **service_meta,
                    "metadata_source": "consul_zero_inference",
                    "validation_passed": True,
                    "validation_timestamp": validation_result["validation_timestamp"],
                    "inference_free": True
                },
                consul_service_id=service_def['ID']
            )
            
        except ServiceDiscoveryError:
            # Re-raise service discovery errors with full context
            raise
        except Exception as e:
            logger.error(f"Failed to find service {service_name} in Consul: {e}")
            raise ServiceDiscoveryError(f"Service discovery failed for {service_name}: {e}")
    
    async def send_message_to_service(self, service_name: str, 
                                    message: StandardMessage) -> None:
        """Send a message to a specific service"""
        try:
            service_info = await self.find_service(service_name)
            if not service_info:
                raise ValueError(f"Service {service_name} not found")
            
            if not service_info.is_healthy:
                raise RuntimeError(f"Service {service_name} is not healthy")
            
            # Update message destination
            message.destination_service = service_name
            
            # Send message through message bus
            destination = f"{service_name}_queue"
            await self.message_bus.publish_message(message, destination)
            
            logger.debug(f"Sent message {message.id} to service {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to send message to service: {e}")
            raise RuntimeError(f"Failed to send message to service: {e}")
    
    async def broadcast_message(self, message: StandardMessage, 
                              exclude_services: List[str] = None) -> None:
        """Broadcast a message to all healthy services discovered from Consul"""
        try:
            exclude_services = exclude_services or []
            
            # Get all services from Consul
            services = await self.discover_services()
            
            for service_info in services:
                if service_info.name in exclude_services:
                    continue
                    
                if not service_info.is_healthy:
                    continue
                
                try:
                    # Create a copy of the message for each service
                    service_message = StandardMessage.create_new(
                        source_service=message.source_service,
                        destination_service=service_info.name,
                        message_type=message.message_type,
                        payload=message.payload,
                        correlation_id=message.correlation_id
                    )
                    
                    await self.send_message_to_service(service_info.name, service_message)
                    
                except Exception as e:
                    logger.error(f"Failed to broadcast to {service_info.name}: {e}")
                    continue
            
            logger.debug(f"Broadcasted message {message.id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            raise MessagingError(f"Failed to broadcast message: {e}")
    
    async def subscribe_to_service_messages(self, callback: callable) -> str:
        """Subscribe to messages for this service"""
        try:
            source = f"{self.service_name}_queue"
            subscription_id = await self.message_bus.subscribe_to_messages(
                source, callback
            )
            
            logger.info(f"Subscribed to messages for {self.service_name}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to subscribe to messages: {e}")
            raise RuntimeError(f"Failed to subscribe to messages: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background task to check service health"""
        try:
            while self.is_running:
                await asyncio.sleep(self.health_check_interval)
                
                if not self.is_running:
                    break
                
                # Check health of all registered services
                await self._check_services_health()
                
        except Exception as e:
            logger.error(f"Health check loop failed: {e}")
    
    async def _check_services_health(self) -> None:
        """Check health of all registered services using Consul health checks"""
        try:
            # Get all services from Consul
            services = await self.discover_services()
            
            for service_info in services:
                try:
                    # Consul already provides health checking via HTTP checks
                    # This is a lightweight check to verify service is still responding
                    health_message = StandardMessage.create_new(
                        source_service=self.service_name,
                        destination_service=service_info.name,
                        message_type="health_check",
                        payload={"timestamp": datetime.now(timezone.utc).isoformat()}
                    )
                    
                    # Send health check (with timeout)
                    await asyncio.wait_for(
                        self.send_message_to_service(service_info.name, health_message),
                        timeout=5.0
                    )
                    
                    # Update health status
                    service_info.is_healthy = True
                    service_info.last_heartbeat = datetime.now(timezone.utc)
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Health check timeout for service {service_info.name}")
                    service_info.is_healthy = False
                    
                except Exception as e:
                    logger.warning(f"Health check failed for service {service_info.name}: {e}")
                    service_info.is_healthy = False
                    
        except Exception as e:
            logger.error(f"Error checking services health: {e}")
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics from Consul"""
        try:
            services = await self.discover_services()
            total_services = len(services)
            healthy_services = sum(1 for s in services if s.is_healthy)
            
            return {
                "service_name": self.service_name,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "services": [s.to_dict() for s in services],
                "message_bus_type": self.message_bus.bus_type.value,
                "is_running": self.is_running,
                "consul_host": self.consul_host,
                "consul_port": self.consul_port
            }
            
        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {
                "service_name": self.service_name,
                "error": str(e),
                "is_running": self.is_running,
                "consul_host": self.consul_host,
                "consul_port": self.consul_port
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check connector health with Consul integration"""
        try:
            message_bus_health = await self.message_bus.health_check()
            
            # Check Consul connectivity
            consul_healthy = False
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.consul_client.status.leader
                )
                consul_healthy = True
            except Exception as e:
                logger.warning(f"Consul health check failed: {e}")
            
            services = await self.discover_services()
            registered_services = len(services)
            healthy_services = sum(1 for s in services if s.is_healthy)
            
            return {
                "service_name": self.service_name,
                "connector_running": self.is_running,
                "message_bus_healthy": message_bus_health.get("healthy", False),
                "consul_healthy": consul_healthy,
                "consul_host": self.consul_host,
                "consul_port": self.consul_port,
                "registered_services": registered_services,
                "healthy_services": healthy_services,
                "status": "healthy" if self.is_running and message_bus_health.get("healthy", False) and consul_healthy else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service_name": self.service_name,
                "connector_running": self.is_running,
                "error": str(e),
                "status": "unhealthy"
            }
    
    def _extract_message_bus_type_from_consul(self, tags: List[str], meta: Dict[str, str]) -> MessageBusType:
        """Extract message bus type using ONLY explicit metadata - zero inference"""
        
        # ONLY check explicit metadata field - no tag fallback
        if 'messaging_type' not in meta:
            raise ServiceDiscoveryError(
                f"Service missing required 'messaging_type' metadata field. "
                f"Explicit metadata required: {{\"messaging_type\": \"rabbitmq|kafka|http\"}}. "
                f"Available metadata: {meta}. "
                f"NO inference allowed - add complete metadata to Consul service registration."
            )
        
        messaging_type = meta['messaging_type'].lower()
        
        # Validate messaging type value
        if messaging_type not in ['rabbitmq', 'kafka', 'http']:
            raise ServiceDiscoveryError(
                f"Invalid messaging_type '{messaging_type}' in Consul metadata. "
                f"Must be exactly one of: rabbitmq, kafka, http. "
                f"Current value: '{meta['messaging_type']}'"
            )
        
        # Convert to enum
        messaging_type_map = {
            'rabbitmq': MessageBusType.RABBITMQ,
            'kafka': MessageBusType.KAFKA,
            'http': MessageBusType.HTTP
        }
        
        return messaging_type_map[messaging_type]
    
    def validate_service_metadata_schema(self, meta: Dict[str, str]) -> Dict[str, Any]:
        """Validate service metadata against required schema - all fields mandatory"""
        
        REQUIRED_METADATA = {
            "messaging_type": {"type": str, "values": ["rabbitmq", "kafka", "http"]},
            "health_endpoint": {"type": str, "format": "url_path"},
            "version": {"type": str, "format": "semver"},
            "environment": {"type": str, "values": ["dev", "staging", "prod"]},
            "protocol": {"type": str, "values": ["http", "https"]}
        }
        
        validation_errors = []
        
        for field_name, requirements in REQUIRED_METADATA.items():
            if field_name not in meta:
                validation_errors.append(f"Required field '{field_name}' missing from metadata")
                continue
            
            field_value = meta[field_name]
            
            # Check type
            if not isinstance(field_value, requirements["type"]):
                validation_errors.append(
                    f"Field '{field_name}' must be {requirements['type'].__name__}, got {type(field_value).__name__}"
                )
                continue
            
            # Check values if specified
            if "values" in requirements and field_value not in requirements["values"]:
                validation_errors.append(
                    f"Field '{field_name}' value '{field_value}' not in allowed values: {requirements['values']}"
                )
            
            # Check format if specified
            if "format" in requirements:
                if requirements["format"] == "url_path" and not field_value.startswith("/"):
                    validation_errors.append(
                        f"Field '{field_name}' must be a valid URL path starting with '/'"
                    )
                elif requirements["format"] == "semver":
                    import re
                    semver_pattern = r'^\d+\.\d+\.\d+$'
                    if not re.match(semver_pattern, field_value):
                        validation_errors.append(
                            f"Field '{field_name}' must follow semantic versioning (x.y.z)"
                        )
        
        if validation_errors:
            raise ServiceDiscoveryError(
                f"Service metadata validation failed: {'; '.join(validation_errors)}"
            )
        
        return {
            "valid": True,
            "metadata": meta,
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _construct_service_url_from_metadata(self, service_def: Dict[str, Any], meta: Dict[str, str]) -> str:
        """Construct service URL using ONLY explicit metadata - no inference"""
        
        # Get address and port from Consul service definition
        address = service_def.get('Address')
        port = service_def.get('Port')
        
        if not address:
            raise ServiceDiscoveryError(
                f"Service missing Address in Consul registration. "
                f"Consul service definition incomplete."
            )
        
        if not port:
            raise ServiceDiscoveryError(
                f"Service missing Port in Consul registration. "
                f"Consul service definition incomplete."
            )
        
        # Check for explicit protocol in metadata - NO INFERENCE
        if 'protocol' not in meta:
            raise ServiceDiscoveryError(
                f"Service missing required 'protocol' metadata field. "
                f"Add explicit protocol metadata: {{\"protocol\": \"http|https\"}} "
                f"to Consul service registration."
            )
        
        protocol = meta['protocol'].lower()
        
        # Validate protocol value
        if protocol not in ['http', 'https']:
            raise ServiceDiscoveryError(
                f"Invalid protocol '{protocol}' in metadata. "
                f"Must be exactly 'http' or 'https'. "
                f"Current value: '{meta['protocol']}'"
            )
        
        return f"{protocol}://{address}:{port}"
    
    def _construct_service_url(self, service_def: Dict[str, Any]) -> str:
        """Legacy method - deprecated in favor of metadata-only construction"""
        # This method is kept for backward compatibility but should not be used
        # in zero-inference mode
        raise ServiceDiscoveryError(
            "Legacy URL construction not allowed in zero-inference mode. "
            "Use _construct_service_url_from_metadata with explicit metadata."
        )
    
    # Removed _extract_health_endpoint_from_consul method
    # Health endpoint now comes from explicit metadata only
    
    @asynccontextmanager
    async def connector_context(self):
        """Context manager for service connector"""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()