"""
AnyIO to HTTP Bridge Implementation

This module bridges AnyIO streams with HTTP-based service communication.
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

from ..protocols.http_protocol import HTTPProtocol
from ..protocols.message_format import StandardMessage

logger = logging.getLogger(__name__)


class AnyIOHTTPBridge:
    """Bridge between AnyIO streams and HTTP-based service communication"""
    
    def __init__(self, service_name: str, host: str = "localhost", port: int = 8080):
        if anyio is None:
            raise ImportError("anyio is required for AnyIO bridge support. Install with: pip install anyio")
        
        self.service_name = service_name
        self.host = host
        self.port = port
        
        self.protocol = HTTPProtocol(host, port)
        self.input_send_channel = None
        self.input_receive_channel = None
        self.output_send_channel = None
        self.output_receive_channel = None
        
        self.is_running = False
        self.bridge_tasks = []
        self.service_registry = {}  # service_name -> service_url mapping
        
    async def initialize(self) -> None:
        """Initialize the bridge with AnyIO streams"""
        try:
            logger.info(f"Initializing AnyIO-HTTP bridge for service {self.service_name}")
            
            # Create AnyIO streams
            self.input_send_channel, self.input_receive_channel = create_memory_object_stream(100)
            self.output_send_channel, self.output_receive_channel = create_memory_object_stream(100)
            
            # Setup HTTP protocol
            await self.protocol.start_server()
            await self.protocol.start_client()
            
            # Register message handlers
            self.protocol.register_message_handler("data", self._handle_data_message)
            self.protocol.register_message_handler("request", self._handle_request_message)
            self.protocol.register_message_handler("response", self._handle_response_message)
            
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
            logger.info(f"Starting AnyIO-HTTP bridge for {self.service_name}")
            
            # Start bridge tasks
            self.bridge_tasks = [
                asyncio.create_task(self._anyio_to_http_task()),
                asyncio.create_task(self._http_to_anyio_task())
            ]
            
            self.is_running = True
            logger.info(f"Bridge started for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            raise RuntimeError(f"Failed to start bridge: {e}")
    
    async def stop(self) -> None:
        """Stop the bridge operations"""
        try:
            logger.info(f"Stopping AnyIO-HTTP bridge for {self.service_name}")
            
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
            
            # Stop HTTP protocol
            await self.protocol.stop_server()
            await self.protocol.stop_client()
            
            logger.info(f"Bridge stopped for service {self.service_name}")
            
        except Exception as e:
            logger.error(f"Error stopping bridge: {e}")
    
    async def _anyio_to_http_task(self) -> None:
        """Task to forward messages from AnyIO stream to HTTP endpoints"""
        try:
            logger.info(f"Starting AnyIO → HTTP forwarding for {self.service_name}")
            
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
                        
                        # Send to destination service
                        await self._send_to_destination(std_message)
                        
                        logger.debug(f"Forwarded message {std_message.id} via HTTP")
                        
                    except Exception as e:
                        logger.error(f"Error forwarding message via HTTP: {e}")
                        # Continue processing other messages
                        continue
                        
        except Exception as e:
            logger.error(f"AnyIO → HTTP task failed: {e}")
            raise
    
    async def _http_to_anyio_task(self) -> None:
        """Task to handle HTTP requests and forward them to AnyIO stream"""
        try:
            logger.info(f"Starting HTTP → AnyIO forwarding for {self.service_name}")
            
            # This task mainly ensures the HTTP server is running
            # The actual message forwarding happens in the HTTP message handlers
            while self.is_running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"HTTP → AnyIO task failed: {e}")
            raise
    
    async def _send_to_destination(self, message: StandardMessage) -> None:
        """Send message to destination service via HTTP"""
        try:
            destination_service = message.destination_service
            
            if destination_service == "unknown":
                logger.warning(f"Unknown destination for message {message.id}")
                return
            
            # Get destination URL
            destination_url = self.service_registry.get(destination_service)
            if not destination_url:
                logger.warning(f"No URL registered for service {destination_service}")
                return
            
            # Send message
            response = await self.protocol.send_message_with_retry(message, destination_url)
            
            if response:
                # Forward response back to AnyIO stream
                await self.input_send_channel.send(response)
                logger.debug(f"Received response for message {message.id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to destination: {e}")
            raise
    
    async def _handle_data_message(self, message: StandardMessage) -> Optional[StandardMessage]:
        """Handle incoming data messages"""
        try:
            # Forward to AnyIO stream
            await self.input_send_channel.send(message)
            logger.debug(f"Handled data message {message.id}")
            
            # Return acknowledgment
            return message.create_reply({"status": "received"}, "data_ack")
            
        except Exception as e:
            logger.error(f"Error handling data message: {e}")
            return message.create_reply({"error": str(e)}, "error")
    
    async def _handle_request_message(self, message: StandardMessage) -> Optional[StandardMessage]:
        """Handle incoming request messages"""
        try:
            # Forward to AnyIO stream
            await self.input_send_channel.send(message)
            logger.debug(f"Handled request message {message.id}")
            
            # For requests, we don't return immediate response
            # The response will be sent asynchronously through the output stream
            return None
            
        except Exception as e:
            logger.error(f"Error handling request message: {e}")
            return message.create_reply({"error": str(e)}, "error")
    
    async def _handle_response_message(self, message: StandardMessage) -> Optional[StandardMessage]:
        """Handle incoming response messages"""
        try:
            # Forward to AnyIO stream
            await self.input_send_channel.send(message)
            logger.debug(f"Handled response message {message.id}")
            
            # Return acknowledgment
            return message.create_reply({"status": "received"}, "response_ack")
            
        except Exception as e:
            logger.error(f"Error handling response message: {e}")
            return message.create_reply({"error": str(e)}, "error")
    
    async def send_message(self, message: Any) -> None:
        """Send a message through the bridge (AnyIO → HTTP)"""
        try:
            if not self.is_running:
                raise RuntimeError("Bridge is not running")
            
            await self.output_send_channel.send(message)
            logger.debug(f"Sent message through bridge: {type(message).__name__}")
            
        except Exception as e:
            logger.error(f"Failed to send message through bridge: {e}")
            raise RuntimeError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Any:
        """Receive a message through the bridge (HTTP → AnyIO)"""
        try:
            if not self.is_running:
                raise RuntimeError("Bridge is not running")
            
            message = await self.input_receive_channel.receive()
            logger.debug(f"Received message through bridge: {type(message).__name__}")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to receive message through bridge: {e}")
            raise RuntimeError(f"Failed to receive message: {e}")
    
    def register_service(self, service_name: str, service_url: str) -> None:
        """Register a service URL for message routing"""
        self.service_registry[service_name] = service_url
        logger.info(f"Registered service {service_name} at {service_url}")
    
    def unregister_service(self, service_name: str) -> None:
        """Unregister a service"""
        if service_name in self.service_registry:
            del self.service_registry[service_name]
            logger.info(f"Unregistered service {service_name}")
    
    async def discover_services(self, service_registry_url: str) -> None:
        """Discover services from a service registry"""
        try:
            services = await self.protocol.discover_services(service_registry_url)
            
            for service in services:
                service_name = service.get("name")
                service_url = service.get("url")
                if service_name and service_url:
                    self.register_service(service_name, service_url)
            
            logger.info(f"Discovered {len(services)} services")
            
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
    
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
            http_healthy = await self.protocol.health_check()
            
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "http_healthy": http_healthy,
                "host": self.host,
                "port": self.port,
                "registered_services": len(self.service_registry),
                "tasks_running": len([t for t in self.bridge_tasks if not t.done()]),
                "status": "healthy" if self.is_running and http_healthy else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service_name": self.service_name,
                "bridge_running": self.is_running,
                "http_healthy": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            return {
                "service_name": self.service_name,
                "host": self.host,
                "port": self.port,
                "registered_services": dict(self.service_registry),
                "bridge_tasks": len(self.bridge_tasks),
                "is_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
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