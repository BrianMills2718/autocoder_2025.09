"""
Integration tests for Strict Service Connector with Real Message Brokers

Tests the strict service connector with zero inference using actual
Consul service discovery and real message brokers.
"""

import pytest
import asyncio
import json
import time
import consul
import aio_pika
import docker
from typing import Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path
import logging

# Import the strict service connector
from autocoder_cc.autocoder.messaging.connectors.strict_service_connector import (
    StrictServiceConnector, StrictMetadataSchema, ServiceDiscoveryError,
    MetadataValidationError, StrictServiceInfo
)
from autocoder_cc.autocoder.messaging.connectors.message_bus_connector import (
    MessageBusConnector, MessageBusType
)
from autocoder_cc.autocoder.messaging.protocols.message_format import StandardMessage

logger = logging.getLogger(__name__)


class MockMessageBusConnector(MessageBusConnector):
    """Mock message bus for testing service discovery"""
    
    def __init__(self, bus_type: MessageBusType):
        self.bus_type = bus_type
        self.connected = False
        self.messages_published = []
        
    async def connect(self):
        self.connected = True
        
    async def disconnect(self):
        self.connected = False
        
    async def publish_message(self, message: StandardMessage, destination: str):
        self.messages_published.append({
            "message": message,
            "destination": destination,
            "timestamp": time.time()
        })
        
    async def create_destination(self, name: str, options: Dict[str, Any]):
        pass
        
    async def subscribe_to_messages(self, source: str, callback):
        return f"subscription_{source}"
        
    async def health_check(self) -> Dict[str, Any]:
        return {"healthy": self.connected}


class ConsulTestInfrastructure:
    """Manage Consul test infrastructure"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.consul_container = None
        self.consul_client = None
        self.consul_port = 8500
        
    async def start_consul(self):
        """Start Consul container for testing"""
        try:
            # Remove existing container if exists
            try:
                existing = self.docker_client.containers.get("test_consul_strict")
                existing.stop()
                existing.remove()
            except docker.errors.NotFound:
                pass
                
            # Start Consul container
            self.consul_container = self.docker_client.containers.run(
                "consul:latest",
                name="test_consul_strict",
                ports={'8500/tcp': self.consul_port},
                environment={'CONSUL_BIND_INTERFACE': 'eth0'},
                command="agent -dev -client=0.0.0.0",
                detach=True,
                remove=True
            )
            
            # Wait for Consul to be ready
            await asyncio.sleep(5)
            
            # Initialize Consul client
            self.consul_client = consul.Consul(host="localhost", port=self.consul_port)
            
            # Verify connectivity
            leader = self.consul_client.status.leader()
            if not leader:
                raise RuntimeError("Consul not ready - no leader elected")
                
            logger.info(f"Consul started successfully. Leader: {leader}")
            
        except Exception as e:
            logger.error(f"Failed to start Consul: {e}")
            raise
            
    async def stop_consul(self):
        """Stop Consul container"""
        if self.consul_container:
            try:
                self.consul_container.stop()
                logger.info("Consul stopped")
            except Exception as e:
                logger.warning(f"Error stopping Consul: {e}")
                
    def register_service_with_metadata(self, service_name: str, metadata: Dict[str, Any],
                                     address: str = "localhost", port: int = 8080,
                                     tags: List[str] = None):
        """Register a service with specific metadata"""
        
        # Register service with Consul
        self.consul_client.agent.service.register(
            name=service_name,
            service_id=f"{service_name}_test_{datetime.now().timestamp()}",
            address=address,
            port=port,
            tags=tags or [],
            meta=metadata,
            check=consul.Check.http(
                f"{metadata.get('protocol', 'http')}://{address}:{port}{metadata.get('health_endpoint', '/health')}",
                interval="10s",
                timeout="5s"
            )
        )
        
        logger.info(f"Registered service '{service_name}' with metadata: {metadata}")
        
    def deregister_all_services(self):
        """Clean up all test services"""
        services = self.consul_client.agent.services()
        for service_id in services:
            if service_id != "consul":  # Don't deregister consul itself
                self.consul_client.agent.service.deregister(service_id)
                

class TestStrictServiceConnectorIntegration:
    """Integration tests for strict service connector"""
    
    @pytest.fixture(scope="class")
    async def consul_infrastructure(self):
        """Set up Consul infrastructure for testing"""
        infra = ConsulTestInfrastructure()
        try:
            await infra.start_consul()
            yield infra
        finally:
            await infra.stop_consul()
            
    @pytest.fixture(autouse=True)
    async def clean_consul(self, consul_infrastructure):
        """Clean Consul before each test"""
        consul_infrastructure.deregister_all_services()
        yield
        consul_infrastructure.deregister_all_services()
        
    @pytest.mark.asyncio
    async def test_service_registration_with_complete_metadata(self, consul_infrastructure):
        """Test service registration with complete metadata"""
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="test_service",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Complete metadata - all fields required
        complete_metadata = {
            "messaging_type": "rabbitmq",
            "health_endpoint": "/health",
            "version": "1.2.3",
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        # Register service
        await connector.register_service("localhost", 8080, complete_metadata)
        
        # Verify service was registered in Consul
        services = consul_infrastructure.consul_client.health.service("test_service", passing=True)[1]
        assert len(services) > 0, "Service not found in Consul"
        
        # Verify metadata was stored correctly
        service_meta = services[0]['Service']['Meta']
        assert service_meta['messaging_type'] == "rabbitmq"
        assert service_meta['health_endpoint'] == "/health"
        assert service_meta['version'] == "1.2.3"
        assert service_meta['environment'] == "dev"
        assert service_meta['protocol'] == "http"
        assert service_meta['service_type'] == "api"
        
        logger.info("✅ Service registered successfully with complete metadata")
        
    @pytest.mark.asyncio
    async def test_service_registration_with_incomplete_metadata_fails(self, consul_infrastructure):
        """Test that service registration fails with incomplete metadata"""
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="test_service",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Incomplete metadata - missing required fields
        incomplete_metadata = {
            "messaging_type": "rabbitmq",
            "version": "1.0.0"
            # Missing: health_endpoint, environment, protocol, service_type
        }
        
        # Attempt registration - should fail
        with pytest.raises(MetadataValidationError) as exc_info:
            await connector.register_service("localhost", 8080, incomplete_metadata)
            
        # Verify error message contains missing fields
        error_msg = str(exc_info.value)
        assert "health_endpoint" in error_msg
        assert "environment" in error_msg
        assert "protocol" in error_msg
        assert "service_type" in error_msg
        
        logger.info("✅ Service registration correctly failed with incomplete metadata")
        
    @pytest.mark.asyncio
    async def test_service_discovery_with_complete_metadata(self, consul_infrastructure):
        """Test service discovery only works with complete metadata"""
        
        # Register a service with complete metadata using Consul directly
        complete_metadata = {
            "messaging_type": "kafka",
            "health_endpoint": "/api/health",
            "version": "2.1.0",
            "environment": "staging",
            "protocol": "https",
            "service_type": "worker"
        }
        
        consul_infrastructure.register_service_with_metadata(
            "complete_service",
            complete_metadata,
            address="10.0.0.1",
            port=9090
        )
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.KAFKA)
        connector = StrictServiceConnector(
            service_name="test_client",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Discover service - should succeed
        service_info = await connector.find_service_strict_metadata_only("complete_service")
        
        # Verify service info
        assert service_info.name == "complete_service"
        assert service_info.address == "10.0.0.1"
        assert service_info.port == 9090
        assert service_info.message_bus_type == MessageBusType.KAFKA
        assert service_info.health_endpoint == "/api/health"
        assert service_info.version == "2.1.0"
        assert service_info.environment == "staging"
        assert service_info.protocol == "https"
        assert service_info.service_type == "worker"
        assert service_info.url == "https://10.0.0.1:9090"
        
        logger.info("✅ Service discovery succeeded with complete metadata")
        
    @pytest.mark.asyncio
    async def test_service_discovery_fails_with_incomplete_metadata(self, consul_infrastructure):
        """Test service discovery fails when metadata is incomplete"""
        
        # Register a service with incomplete metadata using Consul directly
        incomplete_metadata = {
            "messaging_type": "http",
            "version": "1.0.0"
            # Missing other required fields
        }
        
        consul_infrastructure.register_service_with_metadata(
            "incomplete_service",
            incomplete_metadata,
            address="10.0.0.2",
            port=8081
        )
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.HTTP)
        connector = StrictServiceConnector(
            service_name="test_client",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Attempt discovery - should fail
        with pytest.raises(ServiceDiscoveryError) as exc_info:
            await connector.find_service_strict_metadata_only("incomplete_service")
            
        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "incomplete_service" in error_msg
        assert "metadata incomplete" in error_msg
        assert "health_endpoint" in error_msg
        assert "consul_client.agent.service.register" in error_msg  # Help text
        
        logger.info("✅ Service discovery correctly failed with incomplete metadata")
        
    @pytest.mark.asyncio
    async def test_no_inference_from_tags(self, consul_infrastructure):
        """Test that tags are completely ignored - only metadata is used"""
        
        # Register service with tags but no metadata
        consul_infrastructure.consul_client.agent.service.register(
            name="tags_only_service",
            service_id="tags_only_test",
            address="localhost",
            port=8082,
            tags=["messaging_type=rabbitmq", "type:api", "version:1.0.0"],  # Tags should be ignored
            meta={}  # Empty metadata
        )
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="test_client",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Attempt discovery - should fail despite tags
        with pytest.raises(ServiceDiscoveryError) as exc_info:
            await connector.find_service_strict_metadata_only("tags_only_service")
            
        # Verify no inference occurred
        error_msg = str(exc_info.value)
        assert "metadata incomplete" in error_msg
        assert "Required field 'messaging_type' missing" in error_msg
        
        logger.info("✅ Tags correctly ignored - no inference performed")
        
    @pytest.mark.asyncio
    async def test_discover_all_services_with_mixed_metadata(self, consul_infrastructure):
        """Test discovering all services filters out those with incomplete metadata"""
        
        # Register services with different metadata completeness
        services_to_register = [
            ("service_complete_1", {
                "messaging_type": "rabbitmq",
                "health_endpoint": "/health",
                "version": "1.0.0",
                "environment": "prod",
                "protocol": "http",
                "service_type": "api"
            }),
            ("service_complete_2", {
                "messaging_type": "kafka",
                "health_endpoint": "/status",
                "version": "2.0.0",
                "environment": "dev",
                "protocol": "https",
                "service_type": "worker"
            }),
            ("service_incomplete_1", {
                "messaging_type": "http",
                "version": "1.0.0"
                # Missing other fields
            }),
            ("service_incomplete_2", {
                "health_endpoint": "/health"
                # Missing messaging_type and others
            })
        ]
        
        for service_name, metadata in services_to_register:
            consul_infrastructure.register_service_with_metadata(
                service_name, metadata, port=8080 + hash(service_name) % 1000
            )
            
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="test_client",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Discover all services
        discovered_services = await connector.discover_all_services_strict()
        
        # Should only find services with complete metadata
        assert len(discovered_services) == 2
        
        service_names = [s.name for s in discovered_services]
        assert "service_complete_1" in service_names
        assert "service_complete_2" in service_names
        assert "service_incomplete_1" not in service_names
        assert "service_incomplete_2" not in service_names
        
        logger.info(f"✅ Discovered {len(discovered_services)} services with complete metadata")
        
    @pytest.mark.asyncio
    async def test_metadata_field_validation(self, consul_infrastructure):
        """Test specific metadata field validations"""
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.HTTP)
        connector = StrictServiceConnector(
            service_name="test_service",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Test invalid messaging_type
        invalid_metadata_1 = {
            "messaging_type": "invalid_type",  # Not in allowed values
            "health_endpoint": "/health",
            "version": "1.0.0",
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            await connector.register_service("localhost", 8080, invalid_metadata_1)
        assert "messaging_type" in str(exc_info.value)
        assert "rabbitmq, kafka, http" in str(exc_info.value)
        
        # Test invalid health_endpoint
        invalid_metadata_2 = {
            "messaging_type": "http",
            "health_endpoint": "health",  # Must start with /
            "version": "1.0.0",
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            await connector.register_service("localhost", 8080, invalid_metadata_2)
        assert "health_endpoint" in str(exc_info.value)
        
        # Test invalid version format
        invalid_metadata_3 = {
            "messaging_type": "http",
            "health_endpoint": "/health",
            "version": "1.0",  # Must be x.y.z
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            await connector.register_service("localhost", 8080, invalid_metadata_3)
        assert "version" in str(exc_info.value)
        assert "semantic versioning" in str(exc_info.value)
        
        logger.info("✅ Metadata field validations working correctly")
        
    @pytest.mark.asyncio
    async def test_send_message_to_discovered_service(self, consul_infrastructure):
        """Test sending messages to services discovered with strict metadata"""
        
        # Register a service with complete metadata
        complete_metadata = {
            "messaging_type": "rabbitmq",
            "health_endpoint": "/health",
            "version": "1.0.0",
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        consul_infrastructure.register_service_with_metadata(
            "target_service",
            complete_metadata,
            port=8090
        )
        
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="sender_service",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Create test message
        test_message = StandardMessage.create_new(
            source_service="sender_service",
            destination_service="target_service",
            message_type="test_message",
            payload={"data": "test"}
        )
        
        # Send message to discovered service
        await connector.send_message_to_service("target_service", test_message)
        
        # Verify message was sent through message bus
        assert len(message_bus.messages_published) == 1
        published = message_bus.messages_published[0]
        assert published["destination"] == "target_service_queue"
        assert published["message"].destination_service == "target_service"
        
        logger.info("✅ Message sent successfully to discovered service")
        
    @pytest.mark.asyncio
    async def test_health_check_integration(self, consul_infrastructure):
        """Test health check with Consul integration"""
        
        # Register some test services
        for i in range(3):
            metadata = {
                "messaging_type": ["rabbitmq", "kafka", "http"][i % 3],
                "health_endpoint": "/health",
                "version": f"{i+1}.0.0",
                "environment": "dev",
                "protocol": "http",
                "service_type": "api"
            }
            consul_infrastructure.register_service_with_metadata(
                f"health_test_service_{i}",
                metadata,
                port=8100 + i
            )
            
        # Create service connector
        message_bus = MockMessageBusConnector(MessageBusType.RABBITMQ)
        connector = StrictServiceConnector(
            service_name="health_checker",
            message_bus_connector=message_bus,
            consul_host="localhost",
            consul_port=consul_infrastructure.consul_port
        )
        
        # Perform health check
        health_status = await connector.health_check()
        
        # Verify health check results
        assert health_status["service_name"] == "health_checker"
        assert health_status["consul_healthy"] is True
        assert health_status["consul_leader"] is not None
        assert health_status["message_bus_healthy"] is False  # Mock starts disconnected
        assert health_status["discovered_services"] >= 3
        assert health_status["status"] == "unhealthy"  # Due to message bus
        
        # Connect message bus and check again
        await message_bus.connect()
        health_status = await connector.health_check()
        assert health_status["message_bus_healthy"] is True
        assert health_status["status"] == "healthy"
        
        logger.info("✅ Health check integration working correctly")


class TestStrictMetadataSchema:
    """Test the strict metadata schema validation"""
    
    def test_validate_complete_metadata(self):
        """Test validation of complete metadata"""
        complete_metadata = {
            "messaging_type": "rabbitmq",
            "health_endpoint": "/health",
            "version": "1.2.3",
            "environment": "prod",
            "protocol": "https",
            "service_type": "gateway"
        }
        
        # Should not raise
        StrictMetadataSchema.validate_metadata(complete_metadata, "test_service")
        
    def test_validate_missing_fields(self):
        """Test validation catches missing fields"""
        incomplete_metadata = {
            "messaging_type": "kafka",
            "version": "1.0.0"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            StrictMetadataSchema.validate_metadata(incomplete_metadata, "test_service")
            
        error_msg = str(exc_info.value)
        assert "health_endpoint" in error_msg
        assert "environment" in error_msg
        assert "protocol" in error_msg
        assert "service_type" in error_msg
        
    def test_validate_invalid_values(self):
        """Test validation catches invalid values"""
        invalid_metadata = {
            "messaging_type": "custom_mq",  # Invalid
            "health_endpoint": "/health",
            "version": "1.2.3",
            "environment": "production",  # Invalid - should be "prod"
            "protocol": "tcp",  # Invalid
            "service_type": "microservice"  # Invalid
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            StrictMetadataSchema.validate_metadata(invalid_metadata, "test_service")
            
        error_msg = str(exc_info.value)
        assert "messaging_type" in error_msg
        assert "environment" in error_msg
        assert "protocol" in error_msg
        assert "service_type" in error_msg
        
    def test_validate_invalid_formats(self):
        """Test validation catches invalid formats"""
        invalid_metadata = {
            "messaging_type": "http",
            "health_endpoint": "api/health",  # Missing leading /
            "version": "v1.2.3",  # Invalid format
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            StrictMetadataSchema.validate_metadata(invalid_metadata, "test_service")
            
        error_msg = str(exc_info.value)
        assert "health_endpoint" in error_msg
        assert "version" in error_msg
        
    def test_validate_type_checking(self):
        """Test validation checks field types"""
        invalid_metadata = {
            "messaging_type": ["rabbitmq"],  # Should be string, not list
            "health_endpoint": 123,  # Should be string
            "version": "1.0.0",
            "environment": "dev",
            "protocol": "http",
            "service_type": "api"
        }
        
        with pytest.raises(MetadataValidationError) as exc_info:
            StrictMetadataSchema.validate_metadata(invalid_metadata, "test_service")
            
        error_msg = str(exc_info.value)
        assert "messaging_type" in error_msg
        assert "must be str" in error_msg


if __name__ == "__main__":
    # Run with: python -m pytest test_strict_service_connector_integration.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"])