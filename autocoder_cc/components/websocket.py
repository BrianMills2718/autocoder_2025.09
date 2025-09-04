"""
WebSocket component for real-time bidirectional communication.
Implements the ComposedComponent interface.
"""
import anyio
import json
import websockets
from typing import Any, Dict, Set, Optional, List
from ..components.composed_base import ComposedComponent
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class WebSocketComponent(ComposedComponent):
    """WebSocket server component for real-time communication"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize WebSocket component with configuration"""
        super().__init__(name, config)
        
        # WebSocket configuration
        self.port = config.get('port', 8080)
        self.host = config.get('host', '0.0.0.0')
        self.max_connections = config.get('max_connections', 100)
        self.heartbeat_interval = config.get('heartbeat_interval', 30)
        
        # Connection tracking
        self._connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self._server = None
        self._heartbeat_task = None
        
        self.logger.info(f"WebSocket component initialized on {self.host}:{self.port}")
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        # Check max connections limit
        if len(self._connected_clients) >= self.max_connections:
            self.logger.warning(f"Max connections ({self.max_connections}) reached, rejecting new connection")
            await websocket.close(code=1008, reason="Max connections reached")
            return
        
        # Add to connected clients
        self._connected_clients.add(websocket)
        self.logger.info(f"Client connected from {websocket.remote_address}. Total clients: {len(self._connected_clients)}")
        
        try:
            # Handle incoming messages
            async for message in websocket:
                self.logger.debug(f"Received message: {message[:100]}...")
                # Echo or process message as needed
                # Could emit to process_item for further processing
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Client connection closed normally")
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
        finally:
            # Clean up on disconnect
            self._connected_clients.discard(websocket)
            self.logger.info(f"Client disconnected. Total clients: {len(self._connected_clients)}")
    
    async def _send_heartbeat(self):
        """Send periodic heartbeat to all connected clients"""
        while True:
            try:
                await anyio.sleep(self.heartbeat_interval)
                if self._connected_clients:
                    # Send ping to all clients
                    disconnected = set()
                    for client in self._connected_clients:
                        try:
                            await client.ping()
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.add(client)
                    
                    # Clean up disconnected clients
                    self._connected_clients -= disconnected
                    
                    if disconnected:
                        self.logger.info(f"Cleaned up {len(disconnected)} disconnected clients")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat: {e}")
    
    async def process_item(self, item: Any) -> Any:
        """Process item by broadcasting to all connected WebSocket clients"""
        try:
            # Convert item to JSON if needed
            if isinstance(item, str):
                message = item
            else:
                message = json.dumps(item)
            
            # Broadcast to all connected clients
            if self._connected_clients:
                # Send to all clients, tracking disconnected ones
                disconnected = set()
                sent_count = 0
                
                for client in self._connected_clients:
                    try:
                        await client.send(message)
                        sent_count += 1
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)
                    except Exception as e:
                        self.logger.error(f"Error sending to client: {e}")
                        disconnected.add(client)
                
                # Clean up disconnected clients
                self._connected_clients -= disconnected
                
                self.logger.debug(f"Broadcast message to {sent_count} clients")
                self.increment_processed()
                
                return {
                    "broadcast_to": sent_count,
                    "disconnected": len(disconnected),
                    "message": item
                }
            else:
                self.logger.debug("No connected clients to broadcast to")
                return {
                    "broadcast_to": 0,
                    "disconnected": 0,
                    "message": item
                }
                
        except Exception as e:
            self.handle_error(e, "broadcasting message")
            return {"error": str(e), "broadcast_to": 0}
    
    async def _handle_new_connection(self, websocket: websockets.WebSocketServerProtocol):
        """Internal method for testing connection limits"""
        if len(self._connected_clients) >= self.max_connections:
            raise Exception(f"Max connections ({self.max_connections}) reached")
        self._connected_clients.add(websocket)

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for WebSocket component"""
        return [
            ConfigRequirement(
                name="websocket_url",
                type="str",
                description="WebSocket endpoint URL",
                required=True,
                semantic_type=ConfigType.WEBSOCKET_URL,
                example="ws://localhost:8080/stream"
            ),
            ConfigRequirement(
                name="reconnect_interval",
                type="int",
                description="Reconnection interval in seconds",
                required=False,
                default=5,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="message_format",
                type="str",
                description="Format of WebSocket messages",
                required=False,
                default="json",
                options=["json", "text", "binary"],
                semantic_type=ConfigType.STRING
            )
        ]

    
    @classmethod
    def get_required_config_fields(cls) -> list:
        """Return required configuration fields"""
        return []  # All fields have defaults
    
    @classmethod
    def get_required_dependencies(cls) -> list:
        """Return required dependencies"""
        return ["websockets"]
    
    async def start_server(self):
        """Start the WebSocket server (for standalone usage)"""
        self._server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        # Start heartbeat in background (websockets handles its own event loop)
        self._heartbeat_task = None  # Will be started when first client connects
        self.logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            
        # Close all client connections
        for client in self._connected_clients:
            await client.close()
        
        self._connected_clients.clear()
        self.logger.info("WebSocket server stopped")