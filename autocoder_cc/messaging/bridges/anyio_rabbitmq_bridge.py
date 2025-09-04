"""
AnyIO to RabbitMQ Bridge Implementation

This module bridges AnyIO streams with RabbitMQ queues for service communication.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager

try:
    import anyio
    from anyio import create_memory_object_stream
except ImportError:
    anyio = None
    create_memory_object_stream = None

from ..protocols.rabbitmq_protocol import RabbitMQProtocol
from ..protocols.message_format import StandardMessage

logger = logging.getLogger(__name__)


class AnyIORabbitMQBridge:
    """Bridge between AnyIO streams and RabbitMQ queues"""
    
    def __init__(self, rabbitmq_url: str, service_name: str, queue_name: str = None):
        if anyio is None:
            raise ImportError("anyio is required for AnyIO bridge support. Install with: pip install anyio")
        
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.queue_name = queue_name or f"{service_name}_queue"
        
        self.protocol = RabbitMQProtocol(rabbitmq_url)
        self.input_send_channel = None
        self.input_receive_channel = None
        self.output_send_channel = None
        self.output_receive_channel = None
        
        self.is_running = False
        self.bridge_tasks = []
        
    async def initialize(self) -> None:
        """Initialize the bridge with AnyIO streams"""
        try:
            logger.info(f"Initializing AnyIO-RabbitMQ bridge for service {self.service_name}")
            
            # Create AnyIO streams
            self.input_send_channel, self.input_receive_channel = create_memory_object_stream(100)
            self.output_send_channel, self.output_receive_channel = create_memory_object_stream(100)
            
            # Connect to RabbitMQ
            await self.protocol.connect()
            
            # Declare queues
            await self.protocol.declare_queue(self.queue_name)
            await self.protocol.declare_queue(f"{self.queue_name}_output")
            
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
            logger.info(f"Starting AnyIO-RabbitMQ bridge for {self.service_name}")
            
            # Start bridge tasks
            self.bridge_tasks = [
                asyncio.create_task(self._anyio_to_rabbitmq_task()),
                asyncio.create_task(self._rabbitmq_to_anyio_task())
            ]
            
            self.is_running = True
            logger.info(f"Bridge started for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            raise RuntimeError(f"Failed to start bridge: {e}")
    
    async def stop(self) -> None:
        """Stop the bridge operations"""
        try:
            logger.info(f"Stopping AnyIO-RabbitMQ bridge for {self.service_name}")
            
            self.is_running = False
            
            # Cancel bridge tasks
            for task in self.bridge_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close channels
            if self.input_send_channel:
                await self.input_send_channel.aclose()
            if self.output_send_channel:
                await self.output_send_channel.aclose()
            
            # Disconnect from RabbitMQ
            await self.protocol.disconnect()
            
            logger.info(f"Bridge stopped for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Error stopping bridge: {e}")
    
    async def _anyio_to_rabbitmq_task(self) -> None:
        """Task to forward messages from AnyIO stream to RabbitMQ queue"""
        try:
            logger.info(f"Starting AnyIO → RabbitMQ forwarding for {self.service_name}")
            
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
                        
                        # Publish to RabbitMQ
                        routing_key = f"{self.queue_name}_output"
                        await self.protocol.publish_message(std_message, routing_key)
                        
                        logger.debug(f"Forwarded message {std_message.id} to RabbitMQ")
                        
                    except Exception as e:
                        logger.error(f"Error forwarding message to RabbitMQ: {e}")
                        # Continue processing other messages
                        continue
                        
        except Exception as e:
            logger.error(f"AnyIO → RabbitMQ task failed: {e}")
            raise
    
    async def _rabbitmq_to_anyio_task(self) -> None:
        """Task to forward messages from RabbitMQ queue to AnyIO stream"""
        try:
            logger.info(f"Starting RabbitMQ → AnyIO forwarding for {self.service_name}")
            
            async def message_callback(message: StandardMessage) -> None:
                """Callback for processing RabbitMQ messages"""
                try:
                    # Forward to AnyIO stream
                    await self.input_send_channel.send(message)
                    logger.debug(f"Forwarded message {message.id} to AnyIO stream")
                    
                except Exception as e:
                    logger.error(f"Error forwarding message to AnyIO: {e}")
                    # Let RabbitMQ handle the error (message will be nacked)
                    raise
            
            # Start consuming messages
            await self.protocol.consume_messages(self.queue_name, message_callback)
            
        except Exception as e:
            logger.error(f"RabbitMQ → AnyIO task failed: {e}")
            raise
    
    async def send_message(self, message: Any) -> None:
        """Send a message through the bridge (AnyIO → RabbitMQ)"""
        try:
            if not self.is_running:
                raise RuntimeError("Bridge is not running")
            
            await self.output_send_channel.send(message)
            logger.debug(f"Sent message through bridge: {type(message).__name__}")
            
        except Exception as e:
            logger.error(f"Failed to send message through bridge: {e}")
            raise RuntimeError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Any:
        """Receive a message through the bridge (RabbitMQ → AnyIO)"""
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
            rabbitmq_healthy = await self.protocol.health_check()
            
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "rabbitmq_healthy": rabbitmq_healthy,
                "queue_name": self.queue_name,
                "tasks_running": len([t for t in self.bridge_tasks if not t.done()]),
                "status": "healthy" if self.is_running and rabbitmq_healthy else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "rabbitmq_healthy": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            input_queue_info = await self.protocol.get_queue_info(self.queue_name)
            output_queue_info = await self.protocol.get_queue_info(f"{self.queue_name}_output")
            
            return {
                "service_name": self.service_name,
                "input_queue": input_queue_info,
                "output_queue": output_queue_info,
                "bridge_tasks": len(self.bridge_tasks),
                "is_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                "service_name": self.service_name,
                "error": str(e),
                "is_running": self.is_running
            }
    
    def get_anyio_channels(self) -> Dict[str, Any]:
        """Get AnyIO channels for direct component integration"""
        return {
            "input_sender": self.input_send_channel,
            "input_receiver": self.input_receive_channel,
            "output_sender": self.output_send_channel,
            "output_receiver": self.output_receive_channel
        }