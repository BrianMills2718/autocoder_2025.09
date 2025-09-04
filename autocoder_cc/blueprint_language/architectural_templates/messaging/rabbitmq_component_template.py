"""
RabbitMQ Component Template
Provides architectural guidance for LLM generation of RabbitMQ-integrated components
"""

import time
import uuid

RABBITMQ_COMPONENT_TEMPLATE = '''
# RabbitMQ Integration Template - Use this pattern for components that require messaging

import pika
import json
import logging
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

class RabbitMQMixin:
    """Mixin to add RabbitMQ capabilities to any component"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None
        self.channel = None
        self.rabbitmq_url = self.config.get("rabbitmq_url", "amqp://guest:guest@rabbitmq:5672/")
        self.queue_name = self.config.get("queue_name", f"{self.name}_queue")
        self.exchange_name = self.config.get("exchange_name", f"{self.name}_exchange")
        
    async def setup_rabbitmq(self):
        """Initialize RabbitMQ connection and declare queue/exchange"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            
            # Declare exchange (topic exchange for routing)
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue with durability
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Bind queue to exchange
            routing_key = self.config.get("routing_key", f"{self.name}.#")
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=routing_key
            )
            
            self.logger.info(f"✅ RabbitMQ connection established for {self.name}")
            self.logger.info(f"   - Exchange: {self.exchange_name}")
            self.logger.info(f"   - Queue: {self.queue_name}")
            self.logger.info(f"   - Routing Key: {routing_key}")
            
        except Exception as e:
            self.handle_error(e, "RabbitMQ connection setup")
            raise RuntimeError(f"Failed to initialize RabbitMQ: {e}")
            
    async def publish_message(self, message: Dict[str, Any], routing_key: str = None):
        """Publish message to RabbitMQ exchange"""
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized - call setup_rabbitmq() first")
        
        try:
            routing_key = routing_key or f"{self.name}.message"
            message_body = json.dumps(message, default=str)
            
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent messages
                    content_type='application/json',
                    timestamp=int(time.time()),
                    message_id=str(uuid.uuid4())
                )
            )
            
            self.logger.info(f"📤 Published message to {self.exchange_name} with routing key {routing_key}")
            self.increment_processed()
            
        except Exception as e:
            self.handle_error(e, "Message publishing")
            raise
            
    async def consume_messages(self, callback: Callable[[Dict[str, Any]], None]):
        """Start consuming messages from RabbitMQ queue"""
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized - call setup_rabbitmq() first")
        
        try:
            def message_handler(ch, method, properties, body):
                try:
                    message = json.loads(body.decode('utf-8'))
                    self.logger.debug(f"📥 Received message: {message}")
                    
                    # Process message with callback
                    callback(message)
                    
                    # Acknowledge successful processing
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self.increment_processed()
                    
                except Exception as e:
                    self.handle_error(e, "Message processing")
                    # Reject message and don't requeue on processing error
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            # Set up consumer with QoS
            self.channel.basic_qos(prefetch_count=1)  # Process one message at a time
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=message_handler
            )
            
            self.logger.info(f"🔄 Starting message consumption from {self.queue_name}")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            self.logger.info("Message consumption stopped by user")
            self.channel.stop_consuming()
        except Exception as e:
            self.handle_error(e, "Message consumption")
            raise
            
    async def cleanup_rabbitmq(self):
        """Clean up RabbitMQ connections"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.logger.info("🔌 RabbitMQ connections closed")
        except Exception as e:
            self.logger.warning(f"Error during RabbitMQ cleanup: {e}")

# REQUIREMENTS: Add these to requirements.txt when using this template
RABBITMQ_REQUIREMENTS = [
    "pika>=1.3.0",
    "aio-pika>=9.0.0"  # Alternative async implementation
]

# ENVIRONMENT VARIABLES: Add these to docker-compose.yml
RABBITMQ_ENV_VARS = {
    "RABBITMQ_HOST": "rabbitmq",
    "RABBITMQ_PORT": "5672", 
    "RABBITMQ_URL": "amqp://guest:guest@rabbitmq:5672/",
    "RABBITMQ_EXCHANGE": "${COMPONENT_NAME}_exchange",
    "RABBITMQ_QUEUE": "${COMPONENT_NAME}_queue",
    "RABBITMQ_ROUTING_KEY": "${COMPONENT_NAME}.#"
}
'''

def get_rabbitmq_template() -> str:
    """Get the RabbitMQ component template"""
    return RABBITMQ_COMPONENT_TEMPLATE

def get_rabbitmq_requirements() -> list:
    """Get required dependencies for RabbitMQ components"""
    return ["pika>=1.3.0", "aio-pika>=9.0.0"]

def get_rabbitmq_env_vars(component_name: str) -> dict:
    """Get required environment variables for RabbitMQ components"""
    return {
        "RABBITMQ_HOST": "rabbitmq",
        "RABBITMQ_PORT": "5672",
        "RABBITMQ_URL": "amqp://guest:guest@rabbitmq:5672/",
        "RABBITMQ_EXCHANGE": f"{component_name}_exchange",
        "RABBITMQ_QUEUE": f"{component_name}_queue",
        "RABBITMQ_ROUTING_KEY": f"{component_name}.#"
    }