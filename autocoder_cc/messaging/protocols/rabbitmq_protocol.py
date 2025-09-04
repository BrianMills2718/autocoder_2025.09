"""
RabbitMQ Protocol Implementation for Service Communication

This module provides RabbitMQ connection management and protocol handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager

try:
    import aio_pika
    from aio_pika import Message, DeliveryMode
    from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractRobustQueue
except ImportError:
    aio_pika = None

from .message_format import StandardMessage

logger = logging.getLogger(__name__)


class MessagingError(Exception):
    """Base exception for messaging operations"""
    pass


class ConnectionError(MessagingError):
    """Connection-related messaging errors"""
    pass


class SerializationError(MessagingError):
    """Message serialization/deserialization errors"""
    pass


class ValidationError(MessagingError):
    """Message validation errors"""
    pass


class QueueError(MessagingError):
    """Queue-related messaging errors"""
    pass


class PublishError(MessagingError):
    """Message publishing errors"""
    pass


class ConsumerError(MessagingError):
    """Message consumption errors"""
    pass


class RabbitMQProtocol:
    """RabbitMQ protocol implementation with connection management"""
    
    def __init__(self, connection_url: str, exchange_name: str = "autocoder_exchange"):
        if aio_pika is None:
            raise ImportError("aio_pika is required for RabbitMQ support. Install with: pip install aio_pika")
        
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange = None
        self.queues: Dict[str, AbstractRobustQueue] = {}
        self.is_connected = False
        
    async def connect(self) -> None:
        """Establish connection with sophisticated error handling"""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.connection_url}")
            self.connection = await aio_pika.connect_robust(
                self.connection_url,
                timeout=30,
                retry_delay=5,
                client_properties={"connection_name": "autocoder_cc"}
            )
            self.channel = await self.connection.channel()
            
            # Set QoS to ensure fair distribution
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            self.is_connected = True
            logger.info("Successfully connected to RabbitMQ")
            
        except aio_pika.exceptions.AMQPConnectionError as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to RabbitMQ at {self.connection_url}: {e}")
        except asyncio.TimeoutError:
            self.is_connected = False
            raise ConnectionError(f"Connection timeout to RabbitMQ at {self.connection_url}")
        except aio_pika.exceptions.AMQPChannelError as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to create channel: {e}")
        except aio_pika.exceptions.AMQPError as e:
            self.is_connected = False
            raise ConnectionError(f"AMQP error during connection: {e}")
        except (OSError, asyncio.TimeoutError) as e:
            self.is_connected = False
            logger.error(f"Network error during RabbitMQ connection: {e}", exc_info=True)
            raise ConnectionError(f"Network error during connection: {e}")
        except ImportError as e:
            self.is_connected = False
            logger.error(f"Missing RabbitMQ dependencies: {e}", exc_info=True)
            raise ConnectionError(f"Missing aio_pika dependency: {e}")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Unexpected connection error: {e}", exc_info=True)
            raise ConnectionError(f"Connection failed with unexpected error: {type(e).__name__}: {e}")
    
    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error during disconnect: {e}", exc_info=True)
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error during disconnect: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error during disconnect: {type(e).__name__}: {e}", exc_info=True)
    
    async def declare_queue(self, queue_name: str, routing_key: str = None, 
                          durable: bool = True) -> AbstractRobustQueue:
        """Declare a queue and bind it to the exchange"""
        if not self.is_connected:
            await self.connect()
        
        try:
            queue = await self.channel.declare_queue(
                queue_name,
                durable=durable,
                arguments={
                    "x-message-ttl": 3600000,  # 1 hour TTL
                    "x-max-length": 10000       # Max 10k messages
                }
            )
            
            # Bind queue to exchange
            routing_key = routing_key or queue_name
            await queue.bind(self.exchange, routing_key)
            
            self.queues[queue_name] = queue
            logger.info(f"Declared queue {queue_name} with routing key {routing_key}")
            
            return queue
            
        except aio_pika.exceptions.AMQPChannelError as e:
            raise QueueError(f"Channel error declaring queue {queue_name}: {e}")
        except aio_pika.exceptions.AMQPError as e:
            raise QueueError(f"AMQP error declaring queue {queue_name}: {e}")
        except ValueError as e:
            logger.error(f"Invalid queue configuration for {queue_name}: {e}", exc_info=True)
            raise QueueError(f"Invalid queue configuration: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout declaring queue {queue_name}", exc_info=True)
            raise QueueError(f"Timeout declaring queue {queue_name} after 30s")
        except Exception as e:
            logger.error(f"Unexpected error declaring queue {queue_name}: {type(e).__name__}: {e}", exc_info=True)
            raise QueueError(f"Queue declaration failed: {type(e).__name__}: {e}")
    
    async def publish_message(self, message: StandardMessage, routing_key: str) -> None:
        """Publish a message to the exchange"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Validate message
            message.validate()
            
            # Create AMQP message
            amqp_message = Message(
                message.to_bytes(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "message_type": message.message_type,
                    "source_service": message.source_service,
                    "destination_service": message.destination_service,
                    "correlation_id": message.correlation_id
                },
                message_id=message.id,
                timestamp=message.timestamp,
                correlation_id=message.correlation_id
            )
            
            await self.exchange.publish(amqp_message, routing_key=routing_key)
            logger.debug(f"Published message {message.id} to {routing_key}")
            
        except ValueError as e:
            raise SerializationError(f"Message validation failed for {message.id}: {e}")
        except aio_pika.exceptions.AMQPChannelError as e:
            raise PublishError(f"Channel error publishing message {message.id}: {e}")
        except aio_pika.exceptions.AMQPConnectionError as e:
            raise ConnectionError(f"Connection error publishing message {message.id}: {e}")
        except aio_pika.exceptions.AMQPError as e:
            raise PublishError(f"AMQP error publishing message {message.id}: {e}")
        except ValidationError as e:
            logger.error(f"Message validation failed for {message.id}: {e}", exc_info=True)
            raise PublishError(f"Message validation failed: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout publishing message {message.id}", exc_info=True)
            raise PublishError(f"Timeout publishing message {message.id} after 30s")
        except Exception as e:
            logger.error(f"Unexpected error publishing message {message.id}: {type(e).__name__}: {e}", exc_info=True)
            raise PublishError(f"Message publish failed: {type(e).__name__}: {e}")
    
    async def consume_messages(self, queue_name: str, 
                             callback: Callable[[StandardMessage], None]) -> None:
        """Consume messages from a queue"""
        if queue_name not in self.queues:
            raise ValueError(f"Queue {queue_name} not declared")
        
        queue = self.queues[queue_name]
        
        async def process_message(message: aio_pika.IncomingMessage):
            try:
                # Parse message
                std_message = StandardMessage.from_bytes(message.body)
                
                # Process message
                await callback(std_message)
                
                # Acknowledge message
                await message.ack()
                logger.debug(f"Processed message {std_message.id}")
                
            except ValueError as e:
                logger.error(f"Message serialization error: {e}")
                await message.nack(requeue=False)
                raise SerializationError(f"Failed to deserialize message: {e}")
            except KeyError as e:
                logger.error(f"Missing required message field: {e}", exc_info=True)
                await message.nack(requeue=False)
                raise ConsumerError(f"Invalid message format: missing field {e}")
            except ValueError as e:
                logger.error(f"Invalid message data: {e}", exc_info=True)
                await message.nack(requeue=False)
                raise ConsumerError(f"Invalid message data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing message: {type(e).__name__}: {e}", exc_info=True)
                await message.nack(requeue=False)
                raise ConsumerError(f"Message processing failed: {type(e).__name__}: {e}")
                raise ConsumerError(f"Message processing failed: {e}")
        
        try:
            await queue.consume(process_message)
            logger.info(f"Started consuming messages from queue {queue_name}")
            
        except aio_pika.exceptions.AMQPChannelError as e:
            raise ConsumerError(f"Channel error consuming from {queue_name}: {e}")
        except aio_pika.exceptions.AMQPConnectionError as e:
            raise ConnectionError(f"Connection error consuming from {queue_name}: {e}")
        except aio_pika.exceptions.AMQPError as e:
            raise ConsumerError(f"AMQP error consuming from {queue_name}: {e}")
        except ValueError as e:
            logger.error(f"Invalid consumer configuration for {queue_name}: {e}", exc_info=True)
            raise ConsumerError(f"Invalid consumer configuration: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout starting consumer for {queue_name}", exc_info=True)
            raise ConsumerError(f"Consumer startup timeout for {queue_name}")
        except Exception as e:
            logger.error(f"Unexpected error starting consumer for {queue_name}: {type(e).__name__}: {e}", exc_info=True)
            raise ConsumerError(f"Consumer startup failed: {type(e).__name__}: {e}")
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for RabbitMQ connection"""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()
    
    async def health_check(self) -> bool:
        """Check if RabbitMQ connection is healthy"""
        try:
            if not self.is_connected or not self.connection:
                return False
            
            # Test connection by declaring a temporary queue
            temp_queue = await self.channel.declare_queue(
                f"health_check_{asyncio.get_event_loop().time()}",
                exclusive=True,
                auto_delete=True
            )
            await temp_queue.delete()
            
            return True
            
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error during health check: {e}", exc_info=True)
            return False
        except (OSError, asyncio.TimeoutError) as e:
            logger.error(f"Network error during health check: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during health check: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get queue information"""
        if queue_name not in self.queues:
            raise ValueError(f"Queue {queue_name} not declared")
        
        queue = self.queues[queue_name]
        try:
            # Get queue declaration info
            info = await queue.channel.queue_declare(queue_name, passive=True)
            return {
                "name": queue_name,
                "message_count": info.message_count,
                "consumer_count": info.consumer_count,
                "durable": True
            }
        except aio_pika.exceptions.AMQPChannelError as e:
            raise QueueError(f"Channel error getting queue info for {queue_name}: {e}")
        except aio_pika.exceptions.AMQPError as e:
            raise QueueError(f"AMQP error getting queue info for {queue_name}: {e}")
        except ValueError as e:
            logger.error(f"Invalid queue name {queue_name}: {e}", exc_info=True)
            raise QueueError(f"Invalid queue name: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting queue info for {queue_name}", exc_info=True)
            raise QueueError(f"Timeout getting queue info for {queue_name}")
        except Exception as e:
            logger.error(f"Unexpected error getting queue info for {queue_name}: {type(e).__name__}: {e}", exc_info=True)
            raise QueueError(f"Queue info retrieval failed: {type(e).__name__}: {e}")