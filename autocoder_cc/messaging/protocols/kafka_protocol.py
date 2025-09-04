"""
Kafka Protocol Implementation for Service Communication

This module provides Kafka connection management and protocol handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from contextlib import asynccontextmanager

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from kafka.errors import KafkaError
except ImportError:
    AIOKafkaProducer = None
    AIOKafkaConsumer = None
    KafkaError = None

from .message_format import StandardMessage

logger = logging.getLogger(__name__)


class MessagingError(Exception):
    """Base exception for messaging operations"""
    pass


class ConnectionError(MessagingError):
    """Connection-related messaging errors"""
    pass


class TopicError(MessagingError):
    """Topic-related messaging errors"""
    pass


class PublishError(MessagingError):
    """Message publishing errors"""
    pass


class ConsumerError(MessagingError):
    """Message consumption errors"""
    pass


class SerializationError(MessagingError):
    """Message serialization/deserialization errors"""
    pass


class TopicError(MessagingError):
    """Topic-related messaging errors"""
    pass


class ProducerError(MessagingError):
    """Message producer errors"""
    pass


class ConsumerError(MessagingError):
    """Message consumer errors"""
    pass


class KafkaProtocol:
    """Kafka protocol implementation with connection management"""
    
    def __init__(self, bootstrap_servers: str, client_id: str = "autocoder_cc"):
        if AIOKafkaProducer is None:
            raise ImportError("aiokafka is required for Kafka support. Install with: pip install aiokafka")
        
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.is_connected = False
        
    async def connect(self) -> None:
        """Establish Kafka connection"""
        try:
            logger.info(f"Connecting to Kafka at {self.bootstrap_servers}")
            
            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}_producer",
                value_serializer=lambda v: v if isinstance(v, bytes) else v.encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=30000,
                compression_type='gzip'
            )
            
            await self.producer.start()
            self.is_connected = True
            logger.info("Successfully connected to Kafka")
            
        except ImportError as e:
            logger.error(f"Missing Kafka dependencies: {e}", exc_info=True)
            self.is_connected = False
            raise ConnectionError(f"Missing aiokafka dependency: {e}")
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error connecting to Kafka: {e}", exc_info=True)
            self.is_connected = False
            raise ConnectionError(f"Network error during connection: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Kafka: {type(e).__name__}: {e}", exc_info=True)
            self.is_connected = False
            raise ConnectionError(f"Kafka connection failed: {type(e).__name__}: {e}")
            raise ConnectionError(f"Failed to connect to Kafka: {e}")
    
    async def disconnect(self) -> None:
        """Close Kafka connections"""
        try:
            # Stop all consumers
            for consumer in self.consumers.values():
                await consumer.stop()
            self.consumers.clear()
            
            # Stop producer
            if self.producer:
                await self.producer.stop()
            
            self.is_connected = False
            logger.info("Disconnected from Kafka")
            
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error during Kafka disconnect: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error during Kafka disconnect: {type(e).__name__}: {e}", exc_info=True)
    
    async def create_topic(self, topic_name: str, num_partitions: int = 1, 
                          replication_factor: int = 1) -> None:
        """Create a Kafka topic"""
        try:
            from kafka.admin import KafkaAdminClient, NewTopic
            
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}_admin"
            )
            
            topic = NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            
            admin_client.create_topics([topic])
            logger.info(f"Created topic {topic_name}")
            
        except ValueError as e:
            logger.error(f"Invalid topic configuration for {topic_name}: {e}", exc_info=True)
            raise TopicError(f"Invalid topic configuration: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout creating topic {topic_name}", exc_info=True)
            raise TopicError(f"Timeout creating topic {topic_name}")
        except Exception as e:
            if "TopicExistsError" in str(e) or "already exists" in str(e).lower():
                logger.info(f"Topic {topic_name} already exists")
            else:
                logger.error(f"Unexpected error creating topic {topic_name}: {type(e).__name__}: {e}", exc_info=True)
                raise TopicError(f"Topic creation failed: {type(e).__name__}: {e}")
    
    async def publish_message(self, message: StandardMessage, topic: str, 
                            key: Optional[str] = None) -> None:
        """Publish a message to a Kafka topic"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Validate message
            message.validate()
            
            # Use destination service as key if not provided
            message_key = key or message.destination_service
            
            # Add headers
            headers = {
                "message_type": message.message_type.encode('utf-8'),
                "source_service": message.source_service.encode('utf-8'),
                "destination_service": message.destination_service.encode('utf-8'),
                "correlation_id": (message.correlation_id or "").encode('utf-8')
            }
            
            # Send message
            await self.producer.send(
                topic,
                value=message.to_bytes(),
                key=message_key,
                headers=headers.items(),
                timestamp_ms=int(message.timestamp.timestamp() * 1000)
            )
            
            logger.debug(f"Published message {message.id} to topic {topic}")
            
        except ValueError as e:
            logger.error(f"Invalid message data for {message.id}: {e}", exc_info=True)
            raise PublishError(f"Invalid message data: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout publishing message {message.id}", exc_info=True)
            raise PublishError(f"Timeout publishing message {message.id}")
        except Exception as e:
            logger.error(f"Unexpected error publishing message {message.id}: {type(e).__name__}: {e}", exc_info=True)
            raise PublishError(f"Message publish failed: {type(e).__name__}: {e}")
    
    async def create_consumer(self, topics: List[str], group_id: str,
                            callback: Callable[[StandardMessage], None]) -> str:
        """Create a consumer for specific topics"""
        consumer_id = f"{group_id}_{len(self.consumers)}"
        
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}_consumer_{consumer_id}",
                group_id=group_id,
                value_deserializer=lambda m: m,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            await consumer.start()
            self.consumers[consumer_id] = consumer
            
            logger.info(f"Created consumer {consumer_id} for topics {topics}")
            
            # Start consuming in background
            asyncio.create_task(self._consume_messages(consumer_id, callback))
            
            return consumer_id
            
        except ValueError as e:
            logger.error(f"Invalid consumer configuration for topics {topics}: {e}", exc_info=True)
            raise ConsumerError(f"Invalid consumer configuration: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout creating consumer for topics {topics}", exc_info=True)
            raise ConsumerError(f"Consumer creation timeout for topics {topics}")
        except Exception as e:
            logger.error(f"Unexpected error creating consumer for topics {topics}: {type(e).__name__}: {e}", exc_info=True)
            raise ConsumerError(f"Consumer creation failed: {type(e).__name__}: {e}")
    
    async def _consume_messages(self, consumer_id: str, 
                              callback: Callable[[StandardMessage], None]) -> None:
        """Internal method to consume messages"""
        consumer = self.consumers[consumer_id]
        
        try:
            async for message in consumer:
                try:
                    # Parse message
                    std_message = StandardMessage.from_bytes(message.value)
                    
                    # Process message
                    await callback(std_message)
                    
                    logger.debug(f"Processed message {std_message.id}")
                    
                except KeyError as e:
                    logger.error(f"Missing required message field: {e}", exc_info=True)
                    continue  # Skip malformed message
                except ValueError as e:
                    logger.error(f"Invalid message data: {e}", exc_info=True)
                    continue  # Skip invalid message
                except Exception as e:
                    logger.error(f"Unexpected error processing message: {type(e).__name__}: {e}", exc_info=True)
                    continue  # Continue consuming other messages
                    
        except asyncio.CancelledError:
            logger.info(f"Consumer {consumer_id} was cancelled")
            raise
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error in consumer {consumer_id}: {e}", exc_info=True)
            raise ConsumerError(f"Network error in consumer: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in consumer {consumer_id}: {type(e).__name__}: {e}", exc_info=True)
            raise ConsumerError(f"Consumer failed: {type(e).__name__}: {e}")
    
    async def stop_consumer(self, consumer_id: str) -> None:
        """Stop a specific consumer"""
        if consumer_id in self.consumers:
            try:
                await self.consumers[consumer_id].stop()
                del self.consumers[consumer_id]
                logger.info(f"Stopped consumer {consumer_id}")
            except (OSError, asyncio.TimeoutError) as e:
                logger.error(f"Network error stopping consumer {consumer_id}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error stopping consumer {consumer_id}: {type(e).__name__}: {e}", exc_info=True)
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for Kafka connection"""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()
    
    async def health_check(self) -> bool:
        """Check if Kafka connection is healthy"""
        try:
            if not self.is_connected or not self.producer:
                return False
            
            # Test connection by getting metadata
            metadata = await self.producer.client.fetch_metadata()
            return len(metadata.brokers) > 0
            
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error during health check: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during health check: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    async def get_topic_info(self, topic_name: str) -> Dict[str, Any]:
        """Get topic information"""
        try:
            if not self.producer:
                await self.connect()
            
            metadata = await self.producer.client.fetch_metadata()
            
            if topic_name in metadata.topics:
                topic_metadata = metadata.topics[topic_name]
                return {
                    "name": topic_name,
                    "partitions": len(topic_metadata.partitions),
                    "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                    "error": topic_metadata.error
                }
            else:
                raise ValueError(f"Topic {topic_name} not found")
                
        except ValueError as e:
            logger.error(f"Invalid topic name {topic_name}: {e}", exc_info=True)
            raise TopicError(f"Invalid topic name: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting topic info for {topic_name}", exc_info=True)
            raise TopicError(f"Timeout getting topic info for {topic_name}")
        except Exception as e:
            logger.error(f"Unexpected error getting topic info for {topic_name}: {type(e).__name__}: {e}", exc_info=True)
            raise TopicError(f"Topic info retrieval failed: {type(e).__name__}: {e}")
    
    async def list_topics(self) -> List[str]:
        """List all available topics"""
        try:
            if not self.producer:
                await self.connect()
            
            metadata = await self.producer.client.fetch_metadata()
            return list(metadata.topics.keys())
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout listing topics", exc_info=True)
            raise TopicError(f"Timeout listing topics")
        except Exception as e:
            logger.error(f"Unexpected error listing topics: {type(e).__name__}: {e}", exc_info=True)
            raise TopicError(f"Topic listing failed: {type(e).__name__}: {e}")