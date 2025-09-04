"""
Message Bus Connector for Service Communication

This module provides a generic interface for connecting to different message bus systems.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from contextlib import asynccontextmanager

from ..protocols.message_format import StandardMessage
from ..protocols.rabbitmq_protocol import RabbitMQProtocol
from ..protocols.kafka_protocol import KafkaProtocol
from ..protocols.http_protocol import HTTPProtocol

logger = logging.getLogger(__name__)


class MessageBusType(Enum):
    """Supported message bus types"""
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    HTTP = "http"


class MessageBusConnector:
    """Generic message bus connector that supports multiple protocols"""
    
    def __init__(self, bus_type: MessageBusType, config: Dict[str, Any]):
        self.bus_type = bus_type
        self.config = config
        self.protocol = None
        self.is_connected = False
        
        # Initialize protocol based on type
        self._initialize_protocol()
    
    def _initialize_protocol(self) -> None:
        """Initialize the appropriate protocol based on bus type"""
        try:
            if self.bus_type == MessageBusType.RABBITMQ:
                connection_url = self.config.get("connection_url", "amqp://localhost")
                exchange_name = self.config.get("exchange_name", "autocoder_exchange")
                self.protocol = RabbitMQProtocol(connection_url, exchange_name)
                
            elif self.bus_type == MessageBusType.KAFKA:
                bootstrap_servers = self.config.get("bootstrap_servers", "localhost:9092")
                client_id = self.config.get("client_id", "autocoder_cc")
                self.protocol = KafkaProtocol(bootstrap_servers, client_id)
                
            elif self.bus_type == MessageBusType.HTTP:
                host = self.config.get("host", "localhost")
                port = self.config.get("port", 8080)
                self.protocol = HTTPProtocol(host, port)
                
            else:
                raise ValueError(f"Unsupported message bus type: {self.bus_type}")
                
            logger.info(f"Initialized {self.bus_type.value} protocol")
            
        except Exception as e:
            logger.error(f"Failed to initialize protocol: {e}")
            raise RuntimeError(f"Failed to initialize protocol: {e}")
    
    async def connect(self) -> None:
        """Connect to the message bus"""
        try:
            logger.info(f"Connecting to {self.bus_type.value} message bus")
            
            if self.bus_type == MessageBusType.RABBITMQ:
                await self.protocol.connect()
                
            elif self.bus_type == MessageBusType.KAFKA:
                await self.protocol.connect()
                
            elif self.bus_type == MessageBusType.HTTP:
                await self.protocol.start_server()
                await self.protocol.start_client()
            
            self.is_connected = True
            logger.info(f"Connected to {self.bus_type.value} message bus")
            
        except Exception as e:
            logger.error(f"Failed to connect to message bus: {e}")
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to message bus: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the message bus"""
        try:
            logger.info(f"Disconnecting from {self.bus_type.value} message bus")
            
            if self.bus_type == MessageBusType.RABBITMQ:
                await self.protocol.disconnect()
                
            elif self.bus_type == MessageBusType.KAFKA:
                await self.protocol.disconnect()
                
            elif self.bus_type == MessageBusType.HTTP:
                await self.protocol.stop_server()
                await self.protocol.stop_client()
            
            self.is_connected = False
            logger.info(f"Disconnected from {self.bus_type.value} message bus")
            
        except Exception as e:
            logger.error(f"Error disconnecting from message bus: {e}")
    
    async def publish_message(self, message: StandardMessage, 
                            destination: str = None) -> None:
        """Publish a message to the message bus"""
        if not self.is_connected:
            await self.connect()
        
        try:
            if self.bus_type == MessageBusType.RABBITMQ:
                routing_key = destination or message.destination_service
                await self.protocol.publish_message(message, routing_key)
                
            elif self.bus_type == MessageBusType.KAFKA:
                topic = destination or f"{message.destination_service}_topic"
                await self.protocol.publish_message(message, topic)
                
            elif self.bus_type == MessageBusType.HTTP:
                if destination:
                    # Send directly to HTTP endpoint
                    await self.protocol.send_message(message, destination)
                else:
                    # Use service registry
                    logger.warning("HTTP messaging requires destination URL")
                    
            logger.debug(f"Published message {message.id} to {destination}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise RuntimeError(f"Failed to publish message: {e}")
    
    async def subscribe_to_messages(self, source: str, 
                                  callback: callable) -> str:
        """Subscribe to messages from a specific source"""
        if not self.is_connected:
            await self.connect()
        
        try:
            if self.bus_type == MessageBusType.RABBITMQ:
                # Declare and bind queue
                queue = await self.protocol.declare_queue(source)
                await self.protocol.consume_messages(source, callback)
                subscription_id = source
                
            elif self.bus_type == MessageBusType.KAFKA:
                # Create consumer
                topics = [source]
                group_id = f"{source}_consumers"
                subscription_id = await self.protocol.create_consumer(
                    topics, group_id, callback
                )
                
            elif self.bus_type == MessageBusType.HTTP:
                # Register message handler
                message_type = source
                self.protocol.register_message_handler(message_type, callback)
                subscription_id = message_type
                
            logger.info(f"Subscribed to {source} with ID {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to subscribe to messages: {e}")
            raise RuntimeError(f"Failed to subscribe to messages: {e}")
    
    async def unsubscribe_from_messages(self, subscription_id: str) -> None:
        """Unsubscribe from messages"""
        try:
            if self.bus_type == MessageBusType.RABBITMQ:
                # RabbitMQ subscriptions are handled by connection lifecycle
                logger.info(f"Unsubscribed from {subscription_id}")
                
            elif self.bus_type == MessageBusType.KAFKA:
                await self.protocol.stop_consumer(subscription_id)
                
            elif self.bus_type == MessageBusType.HTTP:
                # HTTP subscriptions are handled by server lifecycle
                logger.info(f"Unsubscribed from {subscription_id}")
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
    
    async def create_destination(self, destination_name: str, 
                               config: Dict[str, Any] = None) -> None:
        """Create a destination (queue/topic) if it doesn't exist"""
        if not self.is_connected:
            await self.connect()
        
        try:
            if self.bus_type == MessageBusType.RABBITMQ:
                durable = config.get("durable", True) if config else True
                await self.protocol.declare_queue(destination_name, durable=durable)
                
            elif self.bus_type == MessageBusType.KAFKA:
                num_partitions = config.get("partitions", 1) if config else 1
                replication_factor = config.get("replication_factor", 1) if config else 1
                await self.protocol.create_topic(
                    destination_name, num_partitions, replication_factor
                )
                
            elif self.bus_type == MessageBusType.HTTP:
                # HTTP doesn't require destination creation
                pass
                
            logger.info(f"Created destination {destination_name}")
            
        except Exception as e:
            logger.error(f"Failed to create destination: {e}")
            raise RuntimeError(f"Failed to create destination: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check message bus health"""
        try:
            if not self.protocol:
                return {"status": "unhealthy", "error": "Protocol not initialized"}
            
            healthy = await self.protocol.health_check()
            
            return {
                "bus_type": self.bus_type.value,
                "connected": self.is_connected,
                "healthy": healthy,
                "status": "healthy" if self.is_connected and healthy else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "bus_type": self.bus_type.value,
                "connected": self.is_connected,
                "healthy": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def get_info(self) -> Dict[str, Any]:
        """Get message bus information"""
        try:
            info = {
                "bus_type": self.bus_type.value,
                "connected": self.is_connected,
                "config": self.config
            }
            
            if self.bus_type == MessageBusType.RABBITMQ:
                # Add RabbitMQ-specific info
                info["exchange"] = self.protocol.exchange_name
                info["queues"] = list(self.protocol.queues.keys())
                
            elif self.bus_type == MessageBusType.KAFKA:
                # Add Kafka-specific info
                info["bootstrap_servers"] = self.protocol.bootstrap_servers
                info["client_id"] = self.protocol.client_id
                
            elif self.bus_type == MessageBusType.HTTP:
                # Add HTTP-specific info
                info["host"] = self.protocol.host
                info["port"] = self.protocol.port
                info["running"] = self.protocol.is_running
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get info: {e}")
            return {
                "bus_type": self.bus_type.value,
                "connected": self.is_connected,
                "error": str(e)
            }
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for message bus connection"""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()
    
    @classmethod
    def create_rabbitmq_connector(cls, connection_url: str, 
                                 exchange_name: str = "autocoder_exchange") -> 'MessageBusConnector':
        """Create a RabbitMQ connector"""
        config = {
            "connection_url": connection_url,
            "exchange_name": exchange_name
        }
        return cls(MessageBusType.RABBITMQ, config)
    
    @classmethod
    def create_kafka_connector(cls, bootstrap_servers: str, 
                              client_id: str = "autocoder_cc") -> 'MessageBusConnector':
        """Create a Kafka connector"""
        config = {
            "bootstrap_servers": bootstrap_servers,
            "client_id": client_id
        }
        return cls(MessageBusType.KAFKA, config)
    
    @classmethod
    def create_http_connector(cls, host: str = "localhost", 
                             port: int = 8080) -> 'MessageBusConnector':
        """Create an HTTP connector"""
        config = {
            "host": host,
            "port": port
        }
        return cls(MessageBusType.HTTP, config)