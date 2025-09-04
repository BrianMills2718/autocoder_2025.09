"""
Comprehensive Exception Hierarchy for AutoCoder4_CC Messaging

This module implements the specific exception hierarchy required by CLAUDE.md Task 5
to eliminate all generic exception handling patterns.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class MessagingError(Exception):
    """Base exception for all messaging operations with structured error information"""
    
    def __init__(self, message: str, error_code: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and debugging"""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "error_code": self.error_code,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class ConnectionError(MessagingError):
    """Network and connection-related errors with connection details"""
    
    def __init__(self, message: str, connection_url: str, timeout: float = None, **kwargs):
        super().__init__(message, "CONNECTION_ERROR", {
            "connection_url": connection_url,
            "timeout": timeout,
            **kwargs
        })


class ValidationError(MessagingError):
    """Message validation errors with specific field information"""
    
    def __init__(self, message: str, invalid_field: str = None, expected_format: str = None, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", {
            "invalid_field": invalid_field,
            "expected_format": expected_format,
            **kwargs
        })


class ServiceDiscoveryError(MessagingError):
    """Service discovery errors with service context"""
    
    def __init__(self, message: str, service_name: str = None, consul_host: str = None, **kwargs):
        super().__init__(message, "SERVICE_DISCOVERY_ERROR", {
            "service_name": service_name,
            "consul_host": consul_host,
            **kwargs
        })


class ServiceRegistrationError(MessagingError):
    """Service registration errors with registration context"""
    
    def __init__(self, message: str, service_name: str = None, metadata: Dict[str, Any] = None, **kwargs):
        super().__init__(message, "SERVICE_REGISTRATION_ERROR", {
            "service_name": service_name,
            "metadata": metadata,
            **kwargs
        })


class NetworkTimeoutError(MessagingError):
    """Network timeout errors with timing information"""
    
    def __init__(self, message: str, timeout_seconds: float, operation: str = None, **kwargs):
        super().__init__(message, "NETWORK_TIMEOUT_ERROR", {
            "timeout_seconds": timeout_seconds,
            "operation": operation,
            **kwargs
        })


class ConfigurationError(MessagingError):
    """Configuration validation errors with config context"""
    
    def __init__(self, message: str, config_field: str = None, config_value: Any = None, **kwargs):
        super().__init__(message, "CONFIGURATION_ERROR", {
            "config_field": config_field,
            "config_value": config_value,
            **kwargs
        })


class ComponentRegistryError(MessagingError):
    """Component registry errors with component context"""
    
    def __init__(self, message: str, component_type: str = None, component_name: str = None, **kwargs):
        super().__init__(message, "COMPONENT_REGISTRY_ERROR", {
            "component_type": component_type,
            "component_name": component_name,
            **kwargs
        })


class SignatureMismatch(MessagingError):
    """Cryptographic signature verification errors"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message, "SIGNATURE_MISMATCH", {
            "file_path": file_path,
            **kwargs
        })


# Protocol-specific exceptions
class RabbitMQError(MessagingError):
    """RabbitMQ-specific messaging errors"""
    
    def __init__(self, message: str, queue_name: str = None, exchange: str = None, **kwargs):
        super().__init__(message, "RABBITMQ_ERROR", {
            "queue_name": queue_name,
            "exchange": exchange,
            **kwargs
        })


class KafkaError(MessagingError):
    """Kafka-specific messaging errors"""
    
    def __init__(self, message: str, topic: str = None, partition: int = None, **kwargs):
        super().__init__(message, "KAFKA_ERROR", {
            "topic": topic,
            "partition": partition,
            **kwargs
        })


class HTTPProtocolError(MessagingError):
    """HTTP protocol-specific messaging errors"""
    
    def __init__(self, message: str, url: str = None, status_code: int = None, **kwargs):
        super().__init__(message, "HTTP_PROTOCOL_ERROR", {
            "url": url,
            "status_code": status_code,
            **kwargs
        })


# Serialization and format errors
class SerializationError(MessagingError):
    """Message serialization/deserialization errors"""
    
    def __init__(self, message: str, data_type: str = None, serialization_format: str = None, **kwargs):
        super().__init__(message, "SERIALIZATION_ERROR", {
            "data_type": data_type,
            "serialization_format": serialization_format,
            **kwargs
        })


class QueueError(MessagingError):
    """Queue management errors"""
    
    def __init__(self, message: str, queue_name: str = None, operation: str = None, **kwargs):
        super().__init__(message, "QUEUE_ERROR", {
            "queue_name": queue_name,
            "operation": operation,
            **kwargs
        })


class PublishError(MessagingError):
    """Message publishing errors"""
    
    def __init__(self, message: str, destination: str = None, message_id: str = None, **kwargs):
        super().__init__(message, "PUBLISH_ERROR", {
            "destination": destination,
            "message_id": message_id,
            **kwargs
        })