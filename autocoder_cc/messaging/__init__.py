"""
Service Communication Layer for AutoCoder4_CC

This module provides the infrastructure for bridging AnyIO component streams
with production messaging systems (RabbitMQ, Kafka, HTTP APIs).
"""

from .bridges.anyio_rabbitmq_bridge import AnyIORabbitMQBridge
from .bridges.anyio_kafka_bridge import AnyIOKafkaBridge
from .bridges.anyio_http_bridge import AnyIOHTTPBridge
from .protocols.message_format import StandardMessage
from .connectors.message_bus_connector import MessageBusConnector
from .connectors.service_connector import ServiceConnector

__all__ = [
    'AnyIORabbitMQBridge',
    'AnyIOKafkaBridge', 
    'AnyIOHTTPBridge',
    'StandardMessage',
    'MessageBusConnector',
    'ServiceConnector'
]