"""
AnyIO to Kafka Bridge Implementation

This module bridges AnyIO streams with Kafka topics for service communication.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

try:
    import anyio
    from anyio import create_memory_object_stream
except ImportError:
    anyio = None
    create_memory_object_stream = None

from ..protocols.kafka_protocol import KafkaProtocol
from ..protocols.message_format import StandardMessage

logger = logging.getLogger(__name__)


class AnyIOKafkaBridge:
    """Bridge between AnyIO streams and Kafka topics"""
    
    def __init__(self, bootstrap_servers: str, service_name: str, topic_name: str = None):
        if anyio is None:
            raise ImportError("anyio is required for AnyIO bridge support. Install with: pip install anyio")
        
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.topic_name = topic_name or f"{service_name}_topic"
        self.consumer_group = f"{service_name}_group"
        
        self.protocol = KafkaProtocol(bootstrap_servers, client_id=service_name)
        self.input_send_channel = None
        self.input_receive_channel = None
        self.output_send_channel = None
        self.output_receive_channel = None
        
        self.is_running = False
        self.bridge_tasks = []
        self.consumer_id = None
        
    async def initialize(self) -> None:
        """Initialize the bridge with AnyIO streams"""
        try:
            logger.info(f"Initializing AnyIO-Kafka bridge for service {self.service_name}")
            
            # Create AnyIO streams
            self.input_send_channel, self.input_receive_channel = create_memory_object_stream(100)
            self.output_send_channel, self.output_receive_channel = create_memory_object_stream(100)
            
            # Connect to Kafka
            await self.protocol.connect()
            
            # Create topics
            await self.protocol.create_topic(self.topic_name)
            await self.protocol.create_topic(f"{self.topic_name}_output")
            
            logger.info(f"Bridge initialized for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize bridge: {e}")
            raise RuntimeError(f"Failed to initialize bridge: {e}")
    
    async def start(self) -> None:
        """Start the bridge operations"""
        if self.is_running:
            logger.warning("Bridge is already running")
            return
        
        try:
            logger.info(f"Starting AnyIO-Kafka bridge for {self.service_name}")
            
            # Start bridge tasks
            self.bridge_tasks = [
                asyncio.create_task(self._anyio_to_kafka_task()),
                asyncio.create_task(self._kafka_to_anyio_task())
            ]
            
            self.is_running = True
            logger.info(f"Bridge started for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            raise RuntimeError(f"Failed to start bridge: {e}")
    
    async def stop(self) -> None:
        """Stop the bridge operations"""
        try:
            logger.info(f"Stopping AnyIO-Kafka bridge for {self.service_name}")
            
            self.is_running = False
            
            # Cancel bridge tasks
            for task in self.bridge_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Stop consumer
            if self.consumer_id:
                await self.protocol.stop_consumer(self.consumer_id)
            
            # Close channels
            if self.input_send_channel:
                await self.input_send_channel.aclose()
            if self.output_send_channel:
                await self.output_send_channel.aclose()
            
            # Disconnect from Kafka
            await self.protocol.disconnect()
            
            logger.info(f"Bridge stopped for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Error stopping bridge: {e}")
    
    async def _anyio_to_kafka_task(self) -> None:
        """Task to forward messages from AnyIO stream to Kafka topic"""
        try:
            logger.info(f"Starting AnyIO → Kafka forwarding for {self.service_name}")
            
            async with self.output_receive_channel:
                async for message in self.output_receive_channel:
                    if not self.is_running:
                        break
                    
                    try:
                        # Convert to StandardMessage if needed
                        if isinstance(message, dict):
                            std_message = StandardMessage.create_new(
                                source_service=self.service_name,
                                destination_service=message.get("destination_service", "unknown"),
                                message_type=message.get("message_type", "data"),
                                payload=message.get("payload", message)
                            )
                        elif isinstance(message, StandardMessage):
                            std_message = message
                        else:
                            # Wrap arbitrary data
                            std_message = StandardMessage.create_new(
                                source_service=self.service_name,
                                destination_service="unknown",
                                message_type="data",
                                payload={"data": message}
                            )
                        
                        # Publish to Kafka
                        topic = f"{self.topic_name}_output"
                        await self.protocol.publish_message(std_message, topic)
                        
                        logger.debug(f"Forwarded message {std_message.id} to Kafka")
                        
                    except Exception as e:
                        logger.error(f"Error forwarding message to Kafka: {e}")
                        # Continue processing other messages
                        continue
                        
        except Exception as e:
            logger.error(f"AnyIO → Kafka task failed: {e}")
            raise
    
    async def _kafka_to_anyio_task(self) -> None:
        """Task to forward messages from Kafka topic to AnyIO stream"""
        try:
            logger.info(f"Starting Kafka → AnyIO forwarding for {self.service_name}")
            
            async def message_callback(message: StandardMessage) -> None:
                """Callback for processing Kafka messages"""
                try:
                    # Forward to AnyIO stream
                    await self.input_send_channel.send(message)
                    logger.debug(f"Forwarded message {message.id} to AnyIO stream")
                    
                except Exception as e:
                    logger.error(f"Error forwarding message to AnyIO: {e}")
                    # Let Kafka handle the error (message will be processed again)
                    raise
            
            # Start consuming messages
            topics = [self.topic_name]
            self.consumer_id = await self.protocol.create_consumer(
                topics, self.consumer_group, message_callback
            )
            
            # Keep task alive while consuming
            while self.is_running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Kafka → AnyIO task failed: {e}")
            raise
    
    async def send_message(self, message: Any) -> None:
        """Send a message through the bridge (AnyIO → Kafka)"""
        try:
            if not self.is_running:
                raise RuntimeError("Bridge is not running")
            
            await self.output_send_channel.send(message)
            logger.debug(f"Sent message through bridge: {type(message).__name__}")
            
        except Exception as e:
            logger.error(f"Failed to send message through bridge: {e}")
            raise RuntimeError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Any:
        """Receive a message through the bridge (Kafka → AnyIO)"""
        try:
            if not self.is_running:
                raise RuntimeError("Bridge is not running")
            
            message = await self.input_receive_channel.receive()
            logger.debug(f"Received message through bridge: {type(message).__name__}")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to receive message through bridge: {e}")
            raise RuntimeError(f"Failed to receive message: {e}")
    
    @asynccontextmanager
    async def bridge_context(self):
        """Context manager for bridge lifecycle"""
        try:
            await self.initialize()
            await self.start()
            yield self
        finally:
            await self.stop()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check bridge health"""
        try:
            kafka_healthy = await self.protocol.health_check()
            
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "kafka_healthy": kafka_healthy,
                "topic_name": self.topic_name,
                "consumer_group": self.consumer_group,
                "tasks_running": len([t for t in self.bridge_tasks if not t.done()]),
                "status": "healthy" if self.is_running and kafka_healthy else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "kafka_healthy": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def get_topic_stats(self) -> Dict[str, Any]:
        """Get topic statistics"""
        try:
            input_topic_info = await self.protocol.get_topic_info(self.topic_name)
            output_topic_info = await self.protocol.get_topic_info(f"{self.topic_name}_output")
            
            return {
                "service_name": self.service_name,
                "input_topic": input_topic_info,
                "output_topic": output_topic_info,
                "consumer_group": self.consumer_group,
                "bridge_tasks": len(self.bridge_tasks),
                "is_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"Failed to get topic stats: {e}")
            return {
                "service_name": self.service_name,
                "error": str(e),
                "is_running": self.is_running
            }
    
    async def list_available_topics(self) -> List[str]:
        """List all available topics"""
        try:
            return await self.protocol.list_topics()
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []
    
    def get_anyio_channels(self) -> Dict[str, Any]:
        """Get AnyIO channels for direct component integration"""
        return {
            "input_sender": self.input_send_channel,
            "input_receiver": self.input_receive_channel,
            "output_sender": self.output_send_channel,
            "output_receiver": self.output_receive_channel
        }