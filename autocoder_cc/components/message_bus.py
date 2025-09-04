from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Message Bus Source Component
============================

Handles RabbitMQ message consumption and publishing.
Integrates with CQRS architecture for command/event processing.

Implements Step 6 of Enterprise Roadmap v2: Full CQRS implementation.
"""
import anyio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from autocoder_cc.components.composed_base import ComposedComponent


class MessageBusSource(ComposedComponent):
    """
    Message bus integration component for CQRS architecture.
    
    Handles:
    - Consuming commands from message queues
    - Publishing events to message exchanges
    - Dead letter queue handling
    - Message routing and filtering
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "MessageBusSource"
        
        # RabbitMQ configuration
        self.rabbitmq_url = config.get('rabbitmq_url', 'amqp://guest:guest@rabbitmq:5672')
        self.queue_name = config.get('queue_name', f'{name}_queue')
        self.exchange_name = config.get('exchange_name', 'commands')
        self.routing_key = config.get('routing_key', '#')
        self.durable = config.get('durable', True)
        self.auto_ack = config.get('auto_ack', False)
        
        # Dead letter queue configuration
        self.dlq_enabled = config.get('dlq_enabled', True)
        self.dlq_name = config.get('dlq_name', f'{self.queue_name}_dlq')
        self.max_retries = config.get('max_retries', 3)
        
        # Message filtering
        self.message_filter = config.get('message_filter', {})
        
        # Statistics
        self.messages_consumed = 0
        self.messages_published = 0
        self.messages_failed = 0
        self.messages_retried = 0
        
        self.logger = get_logger(f"MessageBusSource.{self.name}")
    
    async def process(self) -> None:
        """Main processing loop for message bus operations"""
        try:
            # Connect to RabbitMQ
            import aio_pika
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=30,
                blocked_connection_timeout=300
            )
            self.channel = await self.connection.channel()
            
            # Set QoS for fair message distribution
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name, 
                aio_pika.ExchangeType.TOPIC, 
                durable=self.durable
            )
            
            # Set up dead letter queue if enabled
            dlq_args = {}
            if self.dlq_enabled:
                dlq_exchange = await self.channel.declare_exchange(
                    f"{self.exchange_name}_dlq",
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )
                
                dlq_queue = await self.channel.declare_queue(
                    self.dlq_name,
                    durable=True
                )
                await dlq_queue.bind(dlq_exchange, routing_key=self.dlq_name)
                
                dlq_args = {
                    'x-dead-letter-exchange': f"{self.exchange_name}_dlq",
                    'x-dead-letter-routing-key': self.dlq_name,
                    'x-max-retries': self.max_retries
                }
            
            # Declare main queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=self.durable,
                arguments=dlq_args
            )
            
            # Bind queue to exchange
            await self.queue.bind(self.exchange, routing_key=self.routing_key)
            
            self.logger.info(f"MessageBusSource {self.name} connected and ready")
            
            # Start consuming messages
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self._handle_message(message)
                    
        except Exception as e:
            self.logger.error(f"MessageBusSource {self.name} failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _handle_message(self, message) -> None:
        """Handle a single message from the queue"""
        message_id = message.message_id or f"msg_{anyio.get_cancelled_exc_class().time()}"
        
        try:
            # Decode message
            message_data = json.loads(message.body.decode())
            
            # Apply message filtering if configured
            if not self._should_process_message(message_data):
                await message.ack()
                return
            
            # Add message metadata
            message_data['_metadata'] = {
                'message_id': message_id,
                'exchange': message.exchange,
                'routing_key': message.routing_key,
                'timestamp': message.timestamp.isoformat() if message.timestamp else datetime.utcnow().isoformat(),
                'retry_count': message.headers.get('x-retry-count', 0) if message.headers else 0
            }
            
            self.logger.debug(f"Processing message {message_id}")
            
            # Send to output stream
            await self.send_streams['output'].send(message_data)
            
            # Acknowledge message
            await message.ack()
            self.messages_consumed += 1
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in message {message_id}: {e}")
            await self._handle_message_failure(message, f"JSON decode error: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing message {message_id}: {e}")
            await self._handle_message_failure(message, str(e))
    
    async def _handle_message_failure(self, message, error: str) -> None:
        """Handle message processing failure"""
        self.messages_failed += 1
        
        # Get retry count
        retry_count = 0
        if message.headers:
            retry_count = message.headers.get('x-retry-count', 0)
        
        if retry_count < self.max_retries:
            # Retry message
            self.messages_retried += 1
            await message.nack(requeue=True)
            self.logger.warning(f"Message requeued for retry {retry_count + 1}/{self.max_retries}")
        else:
            # Send to dead letter queue
            await message.nack(requeue=False)
            self.logger.error(f"Message sent to DLQ after {self.max_retries} retries: {error}")
    
    def _should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """Check if message should be processed based on filters"""
        if not self.message_filter:
            return True
        
        # Check message type filter
        if 'message_types' in self.message_filter:
            message_type = message_data.get('type') or message_data.get('command_type') or message_data.get('event_type')
            if message_type not in self.message_filter['message_types']:
                return False
        
        # Check source filter
        if 'sources' in self.message_filter:
            source = message_data.get('source')
            if source not in self.message_filter['sources']:
                return False
        
        # Check custom filter function
        if 'custom_filter' in self.message_filter:
            filter_func = self.message_filter['custom_filter']
            if callable(filter_func):
                return filter_func(message_data)
        
        return True
    
    async def cleanup(self):
        """Cleanup message bus resources"""
        try:
            # Close RabbitMQ channel
            if hasattr(self, 'channel') and self.channel:
                await self.channel.close()
                self.logger.debug("Message bus channel closed")
            
            # Close RabbitMQ connection
            if hasattr(self, 'connection') and self.connection:
                await self.connection.close()
                self.logger.debug("Message bus connection closed")
            
            self.logger.info(f"MessageBusSource {self.name} cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during message bus cleanup: {e}")
        finally:
            # Call parent cleanup
            await super().cleanup()
    
    async def publish_message(self, message_data: Dict[str, Any], routing_key: str = None) -> None:
        """Publish a message to the exchange"""
        try:
            # Use configured routing key if not provided
            if routing_key is None:
                routing_key = self.routing_key.replace('#', 'published')
            
            # Add metadata
            message_data['_metadata'] = {
                'publisher': self.name,
                'published_at': datetime.utcnow().isoformat()
            }
            
            # Create message
            import aio_pika
            message = aio_pika.Message(
                json.dumps(message_data).encode(),
                content_type='application/json',
                message_id=message_data.get('id', f"pub_{anyio.get_cancelled_exc_class().time()}"),
                timestamp=datetime.utcnow()
            )
            
            # Publish message
            await self.exchange.publish(message, routing_key=routing_key)
            self.messages_published += 1
            
            self.logger.debug(f"Published message with routing key: {routing_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            'component': self.name,
            'type': 'MessageBusSource',
            'messages_consumed': self.messages_consumed,
            'messages_published': self.messages_published,
            'messages_failed': self.messages_failed,
            'messages_retried': self.messages_retried,
            'success_rate': self.messages_consumed / (self.messages_consumed + self.messages_failed) if (self.messages_consumed + self.messages_failed) > 0 else 0
        }