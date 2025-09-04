"""
Standard Message Format for Service Communication

This module defines the standard message format used across all service communication protocols.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime, timezone


@dataclass
class StandardMessage:
    """Standard message format for all service communication"""
    id: str
    source_service: str
    destination_service: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure timestamp is timezone-aware"""
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
    
    def to_json(self) -> str:
        """Serialize message to JSON for network transmission"""
        try:
            message_dict = {
                'id': self.id,
                'source_service': self.source_service,
                'destination_service': self.destination_service,
                'message_type': self.message_type,
                'payload': self.payload,
                'timestamp': self.timestamp.isoformat(),
                'correlation_id': self.correlation_id
            }
            return json.dumps(message_dict, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize message to JSON: {e}")
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StandardMessage':
        """Deserialize message from JSON"""
        try:
            message_dict = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['id', 'source_service', 'destination_service', 'message_type', 'payload', 'timestamp']
            for field in required_fields:
                if field not in message_dict:
                    raise ValueError(f"Missing required field: {field}")
            
            # Parse timestamp
            timestamp_str = message_dict['timestamp']
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            return cls(
                id=message_dict['id'],
                source_service=message_dict['source_service'],
                destination_service=message_dict['destination_service'],
                message_type=message_dict['message_type'],
                payload=message_dict['payload'],
                timestamp=timestamp,
                correlation_id=message_dict.get('correlation_id')
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to deserialize message from JSON: {e}")
    
    @classmethod
    def create_new(cls, source_service: str, destination_service: str, 
                   message_type: str, payload: Dict[str, Any], 
                   correlation_id: Optional[str] = None) -> 'StandardMessage':
        """Create a new message with auto-generated ID and timestamp"""
        return cls(
            id=str(uuid.uuid4()),
            source_service=source_service,
            destination_service=destination_service,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id
        )
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes for network transmission"""
        return self.to_json().encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'StandardMessage':
        """Create message from bytes"""
        try:
            json_str = data.decode('utf-8')
            return cls.from_json(json_str)
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode message bytes: {e}")
    
    def create_reply(self, payload: Dict[str, Any], message_type: str = None) -> 'StandardMessage':
        """Create a reply message maintaining correlation"""
        return self.create_new(
            source_service=self.destination_service,
            destination_service=self.source_service,
            message_type=message_type or f"{self.message_type}_reply",
            payload=payload,
            correlation_id=self.correlation_id or self.id
        )
    
    def validate(self) -> None:
        """Validate message format and required fields"""
        if not self.id:
            raise ValueError("Message ID cannot be empty")
        if not self.source_service:
            raise ValueError("Source service cannot be empty")
        if not self.destination_service:
            raise ValueError("Destination service cannot be empty")
        if not self.message_type:
            raise ValueError("Message type cannot be empty")
        if not isinstance(self.payload, dict):
            raise ValueError("Payload must be a dictionary")
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")