"""
Protocol Bridges for Service Communication

This module contains bridges that connect AnyIO streams with various messaging protocols.
"""

from .anyio_rabbitmq_bridge import AnyIORabbitMQBridge
from .anyio_kafka_bridge import AnyIOKafkaBridge
from .anyio_http_bridge import AnyIOHTTPBridge

__all__ = [
    'AnyIORabbitMQBridge',
    'AnyIOKafkaBridge',
    'AnyIOHTTPBridge'
]