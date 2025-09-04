"""Message bus for inter-component communication in tests."""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict
from autocoder_cc.observability import get_logger

class MessageBus:
    """Central message bus for component communication."""
    
    def __init__(self):
        self.logger = get_logger("MessageBus")
        self.topics: Dict[str, List[Callable]] = defaultdict(list)
        self.messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'topics_created': 0
        }
        
    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to topic."""
        self.logger.debug(f"Publishing to {topic}: {message.get('id', 'unknown')}")
        
        # Store message
        self.messages[topic].append(message)
        self.stats['messages_sent'] += 1
        
        # Notify subscribers
        for subscriber in self.topics[topic]:
            try:
                await subscriber(message)
                self.stats['messages_received'] += 1
            except Exception as e:
                self.logger.error(f"Subscriber error on {topic}: {e}")
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic."""
        self.topics[topic].append(callback)
        if len(self.topics[topic]) == 1:
            self.stats['topics_created'] += 1
        self.logger.debug(f"Subscribed to {topic}")
    
    def get_messages(self, topic: str) -> List[Dict[str, Any]]:
        """Get all messages for a topic."""
        return self.messages.get(topic, [])
    
    def clear(self):
        """Clear all messages and subscriptions."""
        self.topics.clear()
        self.messages.clear()
        self.logger.info("Message bus cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Get bus statistics."""
        return self.stats.copy()