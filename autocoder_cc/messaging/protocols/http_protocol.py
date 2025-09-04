"""
HTTP Protocol Implementation for Service Communication

This module provides HTTP-based communication for service messaging.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from contextlib import asynccontextmanager

try:
    import aiohttp
    from aiohttp import web, ClientSession, ClientTimeout
except ImportError:
    aiohttp = None
    web = None
    ClientSession = None
    ClientTimeout = None

from .message_format import StandardMessage

logger = logging.getLogger(__name__)


class MessagingError(Exception):
    """Base exception for messaging operations"""
    pass


class ConnectionError(MessagingError):
    """Connection-related messaging errors"""
    pass


class PublishError(MessagingError):
    """Message publishing errors"""
    pass


class HTTPProtocol:
    """HTTP protocol implementation for service communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        if aiohttp is None:
            raise ImportError("aiohttp is required for HTTP support. Install with: pip install aiohttp")
        
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.session: Optional[ClientSession] = None
        self.message_handlers: Dict[str, Callable[[StandardMessage], StandardMessage]] = {}
        self.is_running = False
        
    async def start_server(self) -> None:
        """Start HTTP server"""
        try:
            logger.info(f"Starting HTTP server on {self.host}:{self.port}")
            
            # Setup routes
            self.app.router.add_post('/message', self._handle_message)
            self.app.router.add_get('/health', self._health_check)
            self.app.router.add_get('/status', self._get_status)
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            self.is_running = True
            logger.info(f"HTTP server started on {self.host}:{self.port}")
            
        except OSError as e:
            logger.error(f"Network error starting HTTP server: {e}", exc_info=True)
            raise ConnectionError(f"Network error starting server: {e}")
        except ImportError as e:
            logger.error(f"Missing HTTP dependencies: {e}", exc_info=True)
            raise ConnectionError(f"Missing aiohttp dependency: {e}")
        except Exception as e:
            logger.error(f"Unexpected error starting HTTP server: {type(e).__name__}: {e}", exc_info=True)
            raise ConnectionError(f"Server startup failed: {type(e).__name__}: {e}")
    
    async def stop_server(self) -> None:
        """Stop HTTP server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            self.is_running = False
            logger.info("HTTP server stopped")
            
        except OSError as e:
            logger.error(f"Network error stopping HTTP server: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error stopping HTTP server: {type(e).__name__}: {e}", exc_info=True)
    
    async def start_client(self) -> None:
        """Start HTTP client session"""
        try:
            timeout = ClientTimeout(total=30, connect=5)
            self.session = ClientSession(
                timeout=timeout,
                headers={"User-Agent": "AutoCoder4_CC/1.0"}
            )
            logger.info("HTTP client session started")
            
        except ImportError as e:
            logger.error(f"Missing HTTP client dependencies: {e}", exc_info=True)
            raise ConnectionError(f"Missing aiohttp dependency: {e}")
        except Exception as e:
            logger.error(f"Unexpected error starting HTTP client: {type(e).__name__}: {e}", exc_info=True)
            raise ConnectionError(f"Client startup failed: {type(e).__name__}: {e}")
    
    async def stop_client(self) -> None:
        """Stop HTTP client session"""
        try:
            if self.session:
                await self.session.close()
            logger.info("HTTP client session stopped")
            
        except Exception as e:
            logger.error(f"Unexpected error stopping HTTP client: {type(e).__name__}: {e}", exc_info=True)
    
    def register_message_handler(self, message_type: str, 
                                handler: Callable[[StandardMessage], StandardMessage]) -> None:
        """Register a message handler for a specific message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def _handle_message(self, request: web.Request) -> web.Response:
        """Handle incoming HTTP message"""
        try:
            # Parse request
            body = await request.read()
            message = StandardMessage.from_bytes(body)
            
            logger.debug(f"Received message {message.id} of type {message.message_type}")
            
            # Find handler
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                logger.warning(f"No handler for message type: {message.message_type}")
                return web.Response(
                    status=404,
                    text=f"No handler for message type: {message.message_type}"
                )
            
            # Process message
            try:
                response_message = await handler(message)
                
                if response_message:
                    return web.Response(
                        body=response_message.to_bytes(),
                        content_type='application/json',
                        headers={
                            'X-Message-ID': response_message.id,
                            'X-Correlation-ID': response_message.correlation_id or ""
                        }
                    )
                else:
                    return web.Response(status=200, text="Message processed")
                    
            except KeyError as e:
                logger.error(f"Missing required message field in {message.id}: {e}", exc_info=True)
                return web.Response(status=400, text=f"Missing required field: {e}")
            except ValueError as e:
                logger.error(f"Invalid message data in {message.id}: {e}", exc_info=True)
                return web.Response(status=400, text=f"Invalid data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing message {message.id}: {type(e).__name__}: {e}", exc_info=True)
                return web.Response(status=500, text=f"Processing error: {type(e).__name__}: {e}")
                
        except ValueError as e:
            logger.error(f"Invalid HTTP message format: {e}", exc_info=True)
            return web.Response(status=400, text=f"Invalid message format: {e}")
        except KeyError as e:
            logger.error(f"Missing required HTTP message field: {e}", exc_info=True)
            return web.Response(status=400, text=f"Missing required field: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling HTTP message: {type(e).__name__}: {e}", exc_info=True)
            return web.Response(status=500, text=f"Server error: {type(e).__name__}: {e}")
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.Response(
            body='{"status": "healthy", "service": "autocoder_cc_messaging"}',
            content_type='application/json'
        )
    
    async def _get_status(self, request: web.Request) -> web.Response:
        """Status endpoint"""
        status = {
            "status": "running" if self.is_running else "stopped",
            "host": self.host,
            "port": self.port,
            "handlers": list(self.message_handlers.keys())
        }
        return web.Response(
            body=StandardMessage.create_new(
                source_service="http_protocol",
                destination_service="client",
                message_type="status_response",
                payload=status
            ).to_json(),
            content_type='application/json'
        )
    
    async def send_message(self, message: StandardMessage, target_url: str) -> Optional[StandardMessage]:
        """Send message to another service via HTTP"""
        if not self.session:
            await self.start_client()
        
        try:
            # Validate message
            message.validate()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Message-ID': message.id,
                'X-Message-Type': message.message_type,
                'X-Source-Service': message.source_service,
                'X-Destination-Service': message.destination_service,
                'X-Correlation-ID': message.correlation_id or ""
            }
            
            # Send request
            async with self.session.post(
                f"{target_url}/message",
                data=message.to_bytes(),
                headers=headers
            ) as response:
                
                if response.status == 200:
                    response_body = await response.read()
                    if response_body:
                        return StandardMessage.from_bytes(response_body)
                    else:
                        logger.debug(f"Message {message.id} processed successfully")
                        return None
                        
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status}: {error_text}")
                    raise RuntimeError(f"HTTP error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error sending message {message.id}: {e}", exc_info=True)
            raise PublishError(f"HTTP client error: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout sending message {message.id}", exc_info=True)
            raise PublishError(f"Timeout sending message {message.id}")
        except Exception as e:
            logger.error(f"Unexpected error sending message {message.id}: {type(e).__name__}: {e}", exc_info=True)
            raise PublishError(f"Message send failed: {type(e).__name__}: {e}")
    
    async def send_message_with_retry(self, message: StandardMessage, target_url: str,
                                    max_retries: int = 3, retry_delay: float = 1.0) -> Optional[StandardMessage]:
        """Send message with retry logic"""
        for attempt in range(max_retries):
            try:
                return await self.send_message(message, target_url)
                
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"HTTP client error after {max_retries} attempts: {e}", exc_info=True)
                    raise PublishError(f"HTTP client error after retries: {e}")
            except asyncio.TimeoutError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Timeout after {max_retries} attempts", exc_info=True)
                    raise PublishError(f"Timeout after {max_retries} attempts")
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Unexpected error after {max_retries} attempts: {type(e).__name__}: {e}", exc_info=True)
                    raise PublishError(f"Send failed after retries: {type(e).__name__}: {e}")
                    raise
                else:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
    
    @asynccontextmanager
    async def server_context(self):
        """Context manager for HTTP server"""
        try:
            await self.start_server()
            yield self
        finally:
            await self.stop_server()
    
    @asynccontextmanager
    async def client_context(self):
        """Context manager for HTTP client"""
        try:
            await self.start_client()
            yield self
        finally:
            await self.stop_client()
    
    async def health_check(self) -> bool:
        """Check if HTTP service is healthy"""
        try:
            if not self.session:
                await self.start_client()
            
            async with self.session.get(f"http://{self.host}:{self.port}/health") as response:
                return response.status == 200
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error during health check: {e}", exc_info=True)
            return False
        except asyncio.TimeoutError:
            logger.error(f"Timeout during health check", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during health check: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    async def discover_services(self, service_registry_url: str) -> List[Dict[str, Any]]:
        """Discover available services from registry"""
        try:
            if not self.session:
                await self.start_client()
            
            async with self.session.get(f"{service_registry_url}/services") as response:
                if response.status == 200:
                    services_data = await response.json()
                    return services_data.get("services", [])
                else:
                    logger.error(f"Failed to discover services: HTTP {response.status}")
                    return []
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error during service discovery: {e}", exc_info=True)
            return []
        except asyncio.TimeoutError:
            logger.error(f"Timeout during service discovery", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error during service discovery: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    async def register_service(self, service_registry_url: str, 
                             service_info: Dict[str, Any]) -> bool:
        """Register this service with service registry"""
        try:
            if not self.session:
                await self.start_client()
            
            registration_data = {
                "name": service_info.get("name", "unknown"),
                "url": f"http://{self.host}:{self.port}",
                "health_check_url": f"http://{self.host}:{self.port}/health",
                "metadata": service_info.get("metadata", {})
            }
            
            async with self.session.post(
                f"{service_registry_url}/register",
                json=registration_data
            ) as response:
                
                if response.status == 200:
                    logger.info(f"Service registered successfully: {service_info.get('name')}")
                    return True
                else:
                    logger.error(f"Failed to register service: HTTP {response.status}")
                    return False
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error during service registration: {e}", exc_info=True)
            return False
        except asyncio.TimeoutError:
            logger.error(f"Timeout during service registration", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during service registration: {type(e).__name__}: {e}", exc_info=True)
            return False