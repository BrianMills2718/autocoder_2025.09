#!/usr/bin/env python3
"""
Accumulator component for Autocoder Production Architecture
"""
import anyio
from typing import Dict, Any, List
from .composed_base import ComposedComponent
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.core.dependency_injection import inject
from autocoder_cc.interfaces.config import ConfigProtocol
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Accumulator(ComposedComponent):
    """
    Accumulator components for numerical aggregation using direct Redis connections.
    
    This component connects directly to Redis for atomic accumulation operations,
    providing true production readiness with persistent state management.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "Accumulator"
        self.redis_client = None
        self.redis_url = None
        
        # Setup consistent error handling
        self.error_handler = ConsistentErrorHandler(self.name)
        
        # Get configuration service via dependency injection
        core_settings = inject(ConfigProtocol)
        
        # Parse Redis configuration from blueprint
        if config:
            # Use redis_url from configuration (lowercase standard)
            self.redis_url = config.get('redis_url')
            if not self.redis_url:
                # Build Redis URL from individual components (fallback)
                host = config.get('host', core_settings.JAEGER_AGENT_HOST or 'localhost')
                port = config.get('port', core_settings.REDIS_PORT)
                password = config.get('password', None)
                db = config.get('db', 0)
                
                if password:
                    self.redis_url = f"redis://:{password}@{host}:{port}/{db}"
                else:
                    self.redis_url = f"redis://{host}:{port}/{db}"
            
            # Extract individual components for direct connection (fallback mode)
            self.redis_config = {
                'host': config.get('host', core_settings.JAEGER_AGENT_HOST or 'localhost'),
                'port': config.get('port', core_settings.REDIS_PORT),
                'password': config.get('password', None),
                'db': config.get('db', 0),
                'decode_responses': True
            }
        else:
            # Default Redis configuration
            host = core_settings.JAEGER_AGENT_HOST or 'localhost'
            port = core_settings.REDIS_PORT
            self.redis_url = f"redis://{host}:{port}/0"
            self.redis_config = {
                'host': host,
                'port': port,
                'password': None,
                'db': 0,
                'decode_responses': True
            }
    
    async def setup(self, harness_context=None):
        """Setup accumulator - connect to Redis"""
        await super().setup(harness_context)
        await self._connect_redis()
    
    async def cleanup(self):
        """Cleanup accumulator - disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
        await super().cleanup()
    
    async def _connect_redis(self):
        """Initialize real Redis client connection"""
        try:
            import redis.asyncio as redis
            
            # Try to connect using URL first, fallback to individual parameters
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                self.logger.info(f"Connected to Redis using URL: {self.redis_url.split('@')[0] if '@' in self.redis_url else self.redis_url}")
            except Exception as url_error:
                self.logger.warning(f"Redis URL connection failed: {url_error}, trying individual parameters")
                # Fallback to individual parameters
                self.redis_client = redis.Redis(
                    host=self.redis_config['host'],
                    port=self.redis_config['port'],
                    password=self.redis_config['password'],
                    db=self.redis_config['db'],
                    decode_responses=self.redis_config['decode_responses']
                )
                # Test connection
                await self.redis_client.ping()
                self.logger.info(f"Connected to Redis at {self.redis_config['host']}:{self.redis_config['port']}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Accumulator component"""
        return [
            ConfigRequirement(
                name="batch_size",
                type="int",
                description="Number of items to accumulate before processing",
                required=True,
                semantic_type=ConfigType.INTEGER,
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="flush_interval",
                type="float",
                description="Maximum time in seconds before flushing",
                required=False,
                default=5.0,
                semantic_type=ConfigType.FLOAT,
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="accumulation_strategy",
                type="str",
                description="How to accumulate items",
                required=False,
                default="list",
                options=["list", "concat", "merge"],
                semantic_type=ConfigType.STRING
            )
        ]

    
    @handle_errors(component_name="Accumulator", operation="process")
    async def process(self) -> None:
        """Process data from input streams using direct Redis operations."""
        try:
            # Check if we have an input stream
            if 'input' in self.receive_streams:
                # Use idiomatic anyio stream consumption pattern
                async for data in self.receive_streams['input']:
                    # Perform accumulation using direct Redis operations
                    result = await self._accumulate_data(data)
                    self.increment_processed()
                    
                    # Send result to output streams if configured
                    if result and self.send_streams:
                        for stream_name, stream in self.send_streams.items():
                            await stream.send(result)
            else:
                self.logger.warning("No input stream configured")
                
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "redis_url": self.redis_url},
                operation="process"
            )
    
    async def _accumulate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accumulate data using direct Redis operations.
        This performs atomic accumulation operations for production readiness.
        """
        try:
            if not self.redis_client:
                raise RuntimeError("Redis client not connected")
            
            # Extract accumulation parameters
            key = data.get('key', 'default_accumulator')
            value = data.get('value', 0)
            operation = data.get('operation', 'add')  # add, multiply, etc.
            
            # Ensure value is numeric
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot accumulate non-numeric value: {value}")
            
            # Perform atomic Redis operations
            if operation == 'add':
                # Use Redis INCRBYFLOAT for atomic addition
                new_total = await self.redis_client.incrbyfloat(key, value)
                
            elif operation == 'multiply':
                # For multiplication, we need to use a Lua script for atomicity
                lua_script = """
                local current = redis.call('GET', KEYS[1])
                if current == false then
                    current = 0
                else
                    current = tonumber(current)
                end
                local new_value = current * tonumber(ARGV[1])
                redis.call('SET', KEYS[1], new_value)
                return new_value
                """
                new_total = await self.redis_client.eval(lua_script, 1, key, value)
                
            elif operation == 'get_total':
                # Get current total
                current_value = await self.redis_client.get(key)
                new_total = float(current_value) if current_value else 0.0
                
            elif operation == 'reset':
                # Reset accumulator to zero
                await self.redis_client.set(key, 0)
                new_total = 0.0
                
            else:
                raise ValueError(f"Unknown accumulation operation: {operation}")
            
            self.logger.info(f"Successfully performed {operation} on key {key}: {value} -> {new_total}")
            
            return {
                "operation": operation,
                "key": key,
                "input_value": value,
                "new_total": float(new_total),
                "success": True,
                "redis_host": self.redis_config['host'],
                "redis_port": self.redis_config['port'],
                "original_data": data
            }
            
        except Exception as e:
            self.logger.error(f"Redis accumulation operation failed: {e}")
            return {
                "operation": data.get('operation', 'unknown'),
                "success": False,
                "error": str(e),
                "original_data": data
            }