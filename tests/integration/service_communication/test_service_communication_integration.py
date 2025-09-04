"""
Service Communication Integration Tests for AutoCoder4_CC Phase 2

This module contains comprehensive integration tests for the service communication layer,
including RabbitMQ, Kafka, and HTTP bridges.
"""

import pytest
import asyncio
import docker
import time
import json
from pathlib import Path
from typing import Dict, Any, List

from autocoder_cc.messaging.bridges.anyio_rabbitmq_bridge import AnyIORabbitMQBridge
from autocoder_cc.messaging.bridges.anyio_kafka_bridge import AnyIOKafkaBridge
from autocoder_cc.messaging.bridges.anyio_http_bridge import AnyIOHTTPBridge
from autocoder_cc.messaging.protocols.message_format import StandardMessage
from autocoder_cc.messaging.connectors.message_bus_connector import MessageBusConnector, MessageBusType
from autocoder_cc.messaging.connectors.service_connector import ServiceConnector, ServiceInfo
from autocoder_cc.components.composed_base import ComposedComponent


class TestServiceCommunicationIntegration:
    """Integration tests for service communication"""
    
    @pytest.fixture
    async def rabbitmq_container(self):
        """Start RabbitMQ container for testing"""
        try:
            client = docker.from_env()
            
            # Check if container already exists
            try:
                container = client.containers.get("test_rabbitmq")
                if container.status != "running":
                    container.start()
            except docker.errors.NotFound:
                container = client.containers.run(
                    "rabbitmq:3-management",
                    name="test_rabbitmq",
                    ports={'5672/tcp': 5672, '15672/tcp': 15672},
                    environment={
                        "RABBITMQ_DEFAULT_USER": "guest",
                        "RABBITMQ_DEFAULT_PASS": "guest"
                    },
                    detach=True,
                    remove=True
                )
            
            # Wait for RabbitMQ to be ready
            await asyncio.sleep(10)
            
            yield container
            
        except Exception as e:
            pytest.skip(f"Docker not available or RabbitMQ failed to start: {e}")
        finally:
            try:
                container.stop()
            except:
                pass
    
    @pytest.fixture
    async def kafka_container(self):
        """Start Kafka container for testing"""
        try:
            client = docker.from_env()
            
            # Start Zookeeper first
            try:
                zk_container = client.containers.get("test_zookeeper")
                if zk_container.status != "running":
                    zk_container.start()
            except docker.errors.NotFound:
                zk_container = client.containers.run(
                    "confluentinc/cp-zookeeper:latest",
                    name="test_zookeeper",
                    ports={'2181/tcp': 2181},
                    environment={
                        "ZOOKEEPER_CLIENT_PORT": "2181",
                        "ZOOKEEPER_TICK_TIME": "2000"
                    },
                    detach=True,
                    remove=True
                )
            
            # Wait for Zookeeper
            await asyncio.sleep(5)
            
            # Start Kafka
            try:
                kafka_container = client.containers.get("test_kafka")
                if kafka_container.status != "running":
                    kafka_container.start()
            except docker.errors.NotFound:
                kafka_container = client.containers.run(
                    "confluentinc/cp-kafka:latest",
                    name="test_kafka",
                    ports={'9092/tcp': 9092},
                    environment={
                        "KAFKA_ZOOKEEPER_CONNECT": "test_zookeeper:2181",
                        "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://localhost:9092",
                        "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                        "KAFKA_AUTO_CREATE_TOPICS_ENABLE": "true"
                    },
                    detach=True,
                    remove=True,
                    links={"test_zookeeper": "test_zookeeper"}
                )
            
            # Wait for Kafka to be ready
            await asyncio.sleep(15)
            
            yield kafka_container
            
        except Exception as e:
            pytest.skip(f"Docker not available or Kafka failed to start: {e}")
        finally:
            try:
                kafka_container.stop()
                zk_container.stop()
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_rabbitmq_bridge_integration(self, rabbitmq_container):
        """Test RabbitMQ bridge integration"""
        rabbitmq_url = "amqp://guest:guest@localhost:5672/"
        service_name = "test_service"
        
        # Create bridge
        bridge = AnyIORabbitMQBridge(rabbitmq_url, service_name)
        
        try:
            # Test initialization
            await bridge.initialize()
            assert bridge.protocol.is_connected
            
            # Test bridge startup
            await bridge.start()
            assert bridge.is_running
            
            # Test health check
            health = await bridge.health_check()
            assert health["status"] == "healthy"
            assert health["bridge_running"] == True
            
            # Test message sending and receiving
            test_message = StandardMessage.create_new(
                source_service="test_sender",
                destination_service="test_receiver",
                message_type="test_data",
                payload={"data": "test_payload", "timestamp": time.time()}
            )
            
            # Send message
            await bridge.send_message(test_message)
            
            # Receive message
            received_message = await asyncio.wait_for(
                bridge.receive_message(), 
                timeout=10.0
            )
            
            assert received_message is not None
            assert isinstance(received_message, StandardMessage)
            assert received_message.message_type == "test_data"
            assert received_message.payload["data"] == "test_payload"
            
            # Test queue stats
            stats = await bridge.get_queue_stats()
            assert stats["service_name"] == service_name
            assert "input_queue" in stats
            assert "output_queue" in stats
            
        finally:
            await bridge.stop()
    
    @pytest.mark.asyncio
    async def test_kafka_bridge_integration(self, kafka_container):
        """Test Kafka bridge integration"""
        bootstrap_servers = "localhost:9092"
        service_name = "test_kafka_service"
        
        # Create bridge
        bridge = AnyIOKafkaBridge(bootstrap_servers, service_name)
        
        try:
            # Test initialization
            await bridge.initialize()
            assert bridge.protocol.is_connected
            
            # Test bridge startup
            await bridge.start()
            assert bridge.is_running
            
            # Test health check
            health = await bridge.health_check()
            assert health["status"] == "healthy"
            assert health["bridge_running"] == True
            
            # Test message sending and receiving
            test_message = StandardMessage.create_new(
                source_service="test_kafka_sender",
                destination_service="test_kafka_receiver",
                message_type="kafka_test_data",
                payload={"kafka_data": "test_kafka_payload", "timestamp": time.time()}
            )
            
            # Send message
            await bridge.send_message(test_message)
            
            # Give Kafka time to process
            await asyncio.sleep(2)
            
            # Receive message
            received_message = await asyncio.wait_for(
                bridge.receive_message(), 
                timeout=15.0
            )
            
            assert received_message is not None
            assert isinstance(received_message, StandardMessage)
            assert received_message.message_type == "kafka_test_data"
            assert received_message.payload["kafka_data"] == "test_kafka_payload"
            
            # Test topic stats
            stats = await bridge.get_topic_stats()
            assert stats["service_name"] == service_name
            assert "input_topic" in stats
            assert "output_topic" in stats
            
        finally:
            await bridge.stop()
    
    @pytest.mark.asyncio
    async def test_http_bridge_integration(self):
        """Test HTTP bridge integration"""
        service_name = "test_http_service"
        host = "localhost"
        port = 8081
        
        # Create bridge
        bridge = AnyIOHTTPBridge(service_name, host, port)
        
        try:
            # Test initialization
            await bridge.initialize()
            assert bridge.protocol.is_running
            
            # Test bridge startup
            await bridge.start()
            assert bridge.is_running
            
            # Test health check
            health = await bridge.health_check()
            assert health["status"] == "healthy"
            assert health["bridge_running"] == True
            
            # Register test service
            bridge.register_service("test_target", f"http://{host}:{port}")
            
            # Test message sending and receiving
            test_message = StandardMessage.create_new(
                source_service="test_http_sender",
                destination_service="test_target",
                message_type="http_test_data",
                payload={"http_data": "test_http_payload", "timestamp": time.time()}
            )
            
            # Send message
            await bridge.send_message(test_message)
            
            # Receive message
            received_message = await asyncio.wait_for(
                bridge.receive_message(), 
                timeout=10.0
            )
            
            assert received_message is not None
            assert isinstance(received_message, StandardMessage)
            
            # Test service stats
            stats = await bridge.get_service_stats()
            assert stats["service_name"] == service_name
            assert stats["host"] == host
            assert stats["port"] == port
            
        finally:
            await bridge.stop()
    
    @pytest.mark.asyncio
    async def test_message_bus_connector_integration(self, rabbitmq_container):
        """Test MessageBusConnector integration"""
        
        # Test RabbitMQ connector
        rabbitmq_connector = MessageBusConnector.create_rabbitmq_connector(
            "amqp://guest:guest@localhost:5672/"
        )
        
        try:
            # Test connection
            await rabbitmq_connector.connect()
            assert rabbitmq_connector.is_connected
            
            # Test health check
            health = await rabbitmq_connector.health_check()
            assert health["status"] == "healthy"
            assert health["bus_type"] == "rabbitmq"
            
            # Test destination creation
            await rabbitmq_connector.create_destination("test_queue")
            
            # Test message publishing
            test_message = StandardMessage.create_new(
                source_service="test_publisher",
                destination_service="test_consumer",
                message_type="connector_test",
                payload={"connector_data": "test_connector_payload"}
            )
            
            await rabbitmq_connector.publish_message(test_message, "test_queue")
            
            # Test message subscription
            received_messages = []
            
            async def message_handler(message):
                received_messages.append(message)
            
            subscription_id = await rabbitmq_connector.subscribe_to_messages(
                "test_queue", message_handler
            )
            
            # Give time for message processing
            await asyncio.sleep(2)
            
            assert len(received_messages) > 0
            received_message = received_messages[0]
            assert received_message.message_type == "connector_test"
            assert received_message.payload["connector_data"] == "test_connector_payload"
            
            # Test unsubscription
            await rabbitmq_connector.unsubscribe_from_messages(subscription_id)
            
        finally:
            await rabbitmq_connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_service_connector_integration(self, rabbitmq_container):
        """Test ServiceConnector integration"""
        
        # Create message bus connector
        message_bus = MessageBusConnector.create_rabbitmq_connector(
            "amqp://guest:guest@localhost:5672/"
        )
        
        # Create service connector
        service_connector = ServiceConnector("test_service_registry", message_bus)
        
        try:
            # Test service connector startup
            await service_connector.start()
            assert service_connector.is_running
            
            # Test service registration
            service_info = ServiceInfo(
                name="test_component",
                url="http://localhost:8080",
                message_bus_type=MessageBusType.RABBITMQ,
                metadata={"version": "1.0", "type": "test"}
            )
            
            await service_connector.register_service(service_info)
            
            # Test service discovery
            services = await service_connector.discover_services()
            assert len(services) > 0
            
            found_service = next((s for s in services if s.name == "test_component"), None)
            assert found_service is not None
            assert found_service.url == "http://localhost:8080"
            
            # Test service lookup
            found_service = await service_connector.find_service("test_component")
            assert found_service is not None
            assert found_service.name == "test_component"
            
            # Test message sending to service
            test_message = StandardMessage.create_new(
                source_service="test_sender",
                destination_service="test_component",
                message_type="service_test",
                payload={"service_data": "test_service_payload"}
            )
            
            await service_connector.send_message_to_service("test_component", test_message)
            
            # Test health check
            health = await service_connector.health_check()
            assert health["status"] == "healthy"
            assert health["connector_running"] == True
            
            # Test service stats
            stats = await service_connector.get_service_stats()
            assert stats["service_name"] == "test_service_registry"
            assert stats["total_services"] > 0
            
        finally:
            await service_connector.stop()
    
    @pytest.mark.asyncio
    async def test_composed_component_messaging_integration(self, rabbitmq_container):
        """Test ComposedComponent messaging integration"""
        
        # Create component with messaging configuration
        messaging_config = {
            "bridge_type": "anyio_rabbitmq",
            "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
            "queue_name": "test_component_queue"
        }
        
        component_config = {
            "messaging": messaging_config,
            "type": "TestComponent"
        }
        
        component = ComposedComponent("test_messaging_component", component_config)
        
        try:
            # Test messaging capability creation
            assert component.has_capability("messaging")
            assert component.messaging_config == messaging_config
            
            # Test messaging setup
            await component.setup_messaging()
            assert component.message_bridge is not None
            
            # Test message sending
            test_message = StandardMessage.create_new(
                source_service="test_messaging_component",
                destination_service="test_receiver",
                message_type="component_test",
                payload={"component_data": "test_component_payload"}
            )
            
            await component.send_message(test_message)
            
            # Test message receiving
            received_message = await asyncio.wait_for(
                component.receive_message(), 
                timeout=10.0
            )
            
            assert received_message is not None
            assert isinstance(received_message, StandardMessage)
            
            # Test messaging health
            messaging_health = await component.get_messaging_health()
            assert messaging_health["status"] == "healthy"
            
            # Test messaging channels
            channels = component.get_messaging_channels()
            assert channels is not None
            assert "input_sender" in channels
            assert "input_receiver" in channels
            assert "output_sender" in channels
            assert "output_receiver" in channels
            
        finally:
            if component.message_bridge:
                await component.message_bridge.stop()
    
    @pytest.mark.asyncio
    async def test_complete_service_communication_pipeline(self, rabbitmq_container):
        """Test complete service communication pipeline"""
        
        # Create multiple components with messaging
        component_configs = [
            {
                "name": "source_component",
                "messaging": {
                    "bridge_type": "anyio_rabbitmq",
                    "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
                    "queue_name": "source_queue"
                }
            },
            {
                "name": "processor_component",
                "messaging": {
                    "bridge_type": "anyio_rabbitmq",
                    "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
                    "queue_name": "processor_queue"
                }
            },
            {
                "name": "sink_component",
                "messaging": {
                    "bridge_type": "anyio_rabbitmq",
                    "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
                    "queue_name": "sink_queue"
                }
            }
        ]
        
        components = []
        
        try:
            # Create and setup components
            for config in component_configs:
                component = ComposedComponent(config["name"], config)
                await component.setup_messaging()
                components.append(component)
            
            # Test pipeline: source -> processor -> sink
            source_component = components[0]
            processor_component = components[1]
            sink_component = components[2]
            
            # Source sends message to processor
            source_message = StandardMessage.create_new(
                source_service="source_component",
                destination_service="processor_component",
                message_type="pipeline_data",
                payload={"data": "pipeline_test_data", "step": 1}
            )
            
            await source_component.send_message(source_message)
            
            # Processor receives, processes, and forwards
            processor_received = await asyncio.wait_for(
                processor_component.receive_message(), 
                timeout=10.0
            )
            
            assert processor_received is not None
            assert processor_received.payload["data"] == "pipeline_test_data"
            
            # Processor sends to sink
            processed_message = StandardMessage.create_new(
                source_service="processor_component",
                destination_service="sink_component",
                message_type="processed_data",
                payload={"data": "processed_pipeline_data", "step": 2}
            )
            
            await processor_component.send_message(processed_message)
            
            # Sink receives final message
            sink_received = await asyncio.wait_for(
                sink_component.receive_message(), 
                timeout=10.0
            )
            
            assert sink_received is not None
            assert sink_received.payload["data"] == "processed_pipeline_data"
            assert sink_received.payload["step"] == 2
            
            # Verify all components are healthy
            for component in components:
                health = await component.get_messaging_health()
                assert health["status"] == "healthy"
            
        finally:
            # Cleanup components
            for component in components:
                if component.message_bridge:
                    await component.message_bridge.stop()


class TestServiceCommunicationPerformance:
    """Performance tests for service communication"""
    
    @pytest.mark.asyncio
    async def test_rabbitmq_throughput_performance(self, rabbitmq_container):
        """Test RabbitMQ bridge throughput performance"""
        rabbitmq_url = "amqp://guest:guest@localhost:5672/"
        service_name = "perf_test_service"
        
        bridge = AnyIORabbitMQBridge(rabbitmq_url, service_name)
        
        try:
            await bridge.initialize()
            await bridge.start()
            
            # Performance test parameters
            message_count = 1000
            start_time = time.time()
            
            # Send messages
            for i in range(message_count):
                test_message = StandardMessage.create_new(
                    source_service="perf_sender",
                    destination_service="perf_receiver",
                    message_type="perf_test",
                    payload={"message_id": i, "data": f"test_data_{i}"}
                )
                await bridge.send_message(test_message)
            
            # Receive messages
            received_count = 0
            receive_start = time.time()
            
            while received_count < message_count:
                try:
                    message = await asyncio.wait_for(
                        bridge.receive_message(), 
                        timeout=1.0
                    )
                    if message:
                        received_count += 1
                except asyncio.TimeoutError:
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate performance metrics
            throughput = message_count / total_time
            
            # Performance assertions
            assert received_count >= message_count * 0.95  # 95% delivery rate
            assert throughput >= 100  # Minimum 100 messages/second
            
            print(f"RabbitMQ Performance Results:")
            print(f"  Messages sent: {message_count}")
            print(f"  Messages received: {received_count}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} messages/second")
            print(f"  Delivery rate: {(received_count/message_count)*100:.1f}%")
            
        finally:
            await bridge.stop()
    
    @pytest.mark.asyncio
    async def test_message_serialization_performance(self):
        """Test message serialization/deserialization performance"""
        
        # Create test message
        test_message = StandardMessage.create_new(
            source_service="perf_test",
            destination_service="perf_target",
            message_type="serialization_test",
            payload={
                "data": "x" * 1000,  # 1KB of data
                "numbers": list(range(100)),
                "nested": {"key": "value", "list": [1, 2, 3, 4, 5]}
            }
        )
        
        # Test serialization performance
        iteration_count = 1000
        
        # JSON serialization
        start_time = time.time()
        for _ in range(iteration_count):
            json_str = test_message.to_json()
        json_serialize_time = time.time() - start_time
        
        # JSON deserialization
        start_time = time.time()
        for _ in range(iteration_count):
            deserialized = StandardMessage.from_json(json_str)
        json_deserialize_time = time.time() - start_time
        
        # Bytes serialization
        start_time = time.time()
        for _ in range(iteration_count):
            bytes_data = test_message.to_bytes()
        bytes_serialize_time = time.time() - start_time
        
        # Bytes deserialization
        start_time = time.time()
        for _ in range(iteration_count):
            deserialized = StandardMessage.from_bytes(bytes_data)
        bytes_deserialize_time = time.time() - start_time
        
        # Performance assertions
        assert json_serialize_time < 1.0  # Under 1 second for 1000 iterations
        assert json_deserialize_time < 1.0
        assert bytes_serialize_time < 1.0
        assert bytes_deserialize_time < 1.0
        
        print(f"Serialization Performance Results:")
        print(f"  JSON serialize: {json_serialize_time:.3f}s ({iteration_count/json_serialize_time:.0f} ops/sec)")
        print(f"  JSON deserialize: {json_deserialize_time:.3f}s ({iteration_count/json_deserialize_time:.0f} ops/sec)")
        print(f"  Bytes serialize: {bytes_serialize_time:.3f}s ({iteration_count/bytes_serialize_time:.0f} ops/sec)")
        print(f"  Bytes deserialize: {bytes_deserialize_time:.3f}s ({iteration_count/bytes_deserialize_time:.0f} ops/sec)")
    
    @pytest.mark.asyncio
    async def test_concurrent_component_communication(self, rabbitmq_container):
        """Test concurrent component communication performance"""
        
        # Create multiple components
        component_count = 10
        messages_per_component = 100
        
        components = []
        
        try:
            # Create components
            for i in range(component_count):
                config = {
                    "messaging": {
                        "bridge_type": "anyio_rabbitmq",
                        "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
                        "queue_name": f"concurrent_test_{i}"
                    }
                }
                component = ComposedComponent(f"concurrent_component_{i}", config)
                await component.setup_messaging()
                components.append(component)
            
            # Test concurrent message sending
            start_time = time.time()
            
            async def send_messages(component, message_count):
                for j in range(message_count):
                    message = StandardMessage.create_new(
                        source_service=component.name,
                        destination_service="test_receiver",
                        message_type="concurrent_test",
                        payload={"component_id": component.name, "message_id": j}
                    )
                    await component.send_message(message)
            
            # Send messages concurrently
            await asyncio.gather(*[
                send_messages(component, messages_per_component)
                for component in components
            ])
            
            end_time = time.time()
            total_time = end_time - start_time
            total_messages = component_count * messages_per_component
            concurrent_throughput = total_messages / total_time
            
            # Performance assertions
            assert concurrent_throughput >= 500  # Minimum 500 messages/second with concurrency
            
            print(f"Concurrent Communication Performance:")
            print(f"  Components: {component_count}")
            print(f"  Messages per component: {messages_per_component}")
            print(f"  Total messages: {total_messages}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Concurrent throughput: {concurrent_throughput:.2f} messages/second")
            
        finally:
            # Cleanup
            for component in components:
                if component.message_bridge:
                    await component.message_bridge.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])