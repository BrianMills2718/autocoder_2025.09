"""
API Endpoint component generator using composition pattern.
Generates FastAPI endpoints with all capabilities composed, not inherited.
"""
from typing import Dict, Any, Optional
from jinja2 import Template
from autocoder_cc.core.config import settings


class APIEndpointGenerator:
    """Generates API endpoint components using FastAPI and composition."""
    
    def __init__(self):
        self.api_version = "1"  # Default API version
    
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """Generate API endpoint component code."""
        name = component_spec.get('name', 'api_endpoint')
        config = component_spec.get('config', {})
        
        # Extract configuration
        route = config.get('route', f'/{name}')
        methods = config.get('methods', ['GET', 'POST'])
        auth_required = config.get('auth_required', True)  # Auto-enabled for security
        rbac_enabled = config.get('rbac_enabled', True)   # Auto-enabled RBAC
        required_roles = config.get('required_roles', ['user'])  # Default role requirements
        rate_limit = config.get('rate_limit', settings.RATE_LIMIT_REQUESTS)
        api_version = config.get('api_version', self.api_version)
        
        # Generate imports
        imports = self._generate_imports(auth_required, rbac_enabled, rate_limit)
        
        # Generate Pydantic models
        models = self._generate_models(name)
        
        # Generate component class
        component_class = self._generate_component_class(
            name, route, methods, auth_required, rbac_enabled, required_roles, rate_limit, api_version
        )
        
        return f'''{imports}

{models}

{component_class}'''

    def _generate_imports(self, auth_required: bool, rbac_enabled: bool, rate_limit: int) -> str:
        """Generate import statements."""
        imports = [
            "import logging",
            "from autocoder_cc.observability.structured_logging import get_logger",
            "import json",
            "import uuid",
            "from typing import Dict, Any, Optional",
            "from datetime import datetime",
            "from fastapi import FastAPI, HTTPException, Depends, status",
            "from pydantic import BaseModel, Field",
            "import anyio",
            "",
            "from autocoder_cc.components.composed_base import ComposedComponent",
            "from autocoder_cc.components.cqrs.command_handler import CommandHandler",
            "from autocoder_cc.components.cqrs.query_handler import QueryHandler",
            "from autocoder_cc.capabilities import (",
            "    SchemaValidator,",
            "    HealthChecker,",
            "    MetricsCollector,",
        ]
        
        if rate_limit:
            imports.append("    RateLimiter,")
        
        imports.append(")")
        
        if auth_required:
            imports.extend([
                "",
                "from typing import Annotated",
                "from autocoder_cc.security import (",
                "    requires_role,",
                "    requires_permission,",
                "    get_current_user,",
                "    generate_token,",
                "    User",
                ")",
                "from autocoder_cc.capabilities.input_sanitizer import InputSanitizer",
            ])
        
        return "\n".join(imports)
    
    def _generate_models(self, name: str) -> str:
        """Generate Pydantic models for CQRS commands and queries."""
        return f'''# CQRS Command/Query models
class {name.title()}Command(BaseModel):
    """Command model for {name} write operations."""
    command_type: str = Field(..., description="Type of command")
    aggregate_id: Optional[str] = Field(default=None, description="Target aggregate ID")
    data: Dict[str, Any] = Field(..., description="Command payload")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Optional metadata")


class {name.title()}Query(BaseModel):
    """Query model for {name} read operations."""
    query_type: str = Field(..., description="Type of query")
    params: Optional[Dict[str, Any]] = Field(default={{}}, description="Query parameters")
    limit: Optional[int] = Field(default=100, description="Result limit")
    offset: Optional[int] = Field(default=0, description="Result offset")


class CommandResponse(BaseModel):
    """Response for command operations."""
    command_id: str = Field(..., description="Command tracking ID")
    status: str = Field(..., description="Command status (accepted/rejected)")
    message: Optional[str] = Field(default=None, description="Status message")
    timestamp: str = Field(..., description="Processing timestamp")


class QueryResponse(BaseModel):
    """Response for query operations."""
    query_id: str = Field(..., description="Query tracking ID")
    success: bool = Field(..., description="Query success status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Query result data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Result metadata")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: str = Field(..., description="Processing timestamp")'''

    def _generate_component_class(self, name: str, route: str, methods: list,
                                 auth_required: bool, rbac_enabled: bool, required_roles: list, 
                                 rate_limit: int, api_version: str) -> str:
        """Generate the component class using composition."""
        
        # Generate auth dependency if needed
        auth_code = ""
        if auth_required:
            auth_code = '''
        # Security with cryptographic policy enforcement
        self.security = HTTPBearer()
        self.jwt_secret_key = settings.DEFAULT_JWT_SECRET_KEY
        
        # Load crypto policy enforcer for environment-specific JWT algorithms
        from autocoder_cc.security.crypto_policy_enforcer import get_crypto_enforcer
        self.crypto_enforcer = get_crypto_enforcer()
        self.allowed_algorithms = self.crypto_enforcer.get_jwt_decode_algorithms()
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Verify JWT token using environment-appropriate algorithms."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Decode and verify the token using policy-enforced algorithms
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret_key,
                algorithms=self.allowed_algorithms
            )
            
            # Check token expiration
            if "exp" in payload:
                if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            # Log successful authentication
            self.logger.info(f"Authenticated user: {payload.get('sub', 'unknown')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def generate_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Generate a JWT token for the given user."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    async def verify_role_access(self, required_roles: list, token_payload: dict) -> bool:
        """Verify if user has required roles for RBAC."""
        user_roles = token_payload.get('roles', [])
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            self.logger.warning(f"Access denied: User roles {user_roles} do not match required {required_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required roles: {required_roles}",
            )
        
        self.logger.info(f"RBAC access granted: User has role(s) {[r for r in user_roles if r in required_roles]}")
        return True
    
    async def require_roles(self, required_roles: list = None):
        """Dependency to require specific roles for endpoint access."""
        if not required_roles:
            required_roles = ['user']  # Default role requirement
            
        async def _verify_access(token_payload: dict = Depends(self.verify_token)):
            await self.verify_role_access(required_roles, token_payload)
            return token_payload
            
        return _verify_access'''
        
        # Generate CQRS route methods
        cqrs_routes = self._generate_cqrs_routes(name, route, auth_required, rbac_enabled, required_roles, rate_limit, api_version)
        
        # Generate health check endpoints
        health_endpoints = self._generate_health_endpoints(name)
        
        return f'''class {name.title()}Component(ComposedComponent):
    """
    CQRS API Endpoint component using composition pattern.
    Separates command (write) and query (read) operations.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Initialize capabilities via composition
        self.schema_validator = SchemaValidator(strict_mode=True)
        self.health_checker = HealthChecker()
        self.metrics = MetricsCollector(namespace=name)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            rate={rate_limit},
            per={settings.RATE_LIMIT_PERIOD}
        ) if {rate_limit} > 0 else None
        
        # CQRS Components
        self.command_handler = CommandHandler(f"{{name}}_commands", config.get('command_config', {{}}))
        self.query_handler = QueryHandler(f"{{name}}_queries", config.get('query_config', {{}}))
        
        # Message Bus Integration for CQRS
        from autocoder_cc.generators.config import generator_settings
        self.rabbitmq_url = config.get('rabbitmq_url', generator_settings.get_rabbitmq_url())
        self.message_bus_connection = None
        self.message_bus_channel = None
        
        # Configure schemas
        self.schema_validator.register_schema('command', {name.title()}Command)
        self.schema_validator.register_schema('query', {name.title()}Query)
        
        # Add health checks
        self.health_checker.add_check('api_ready', self._check_api_ready)
        self.health_checker.add_check('command_handler_ready', self._check_command_handler_ready)
        self.health_checker.add_check('query_handler_ready', self._check_query_handler_ready)
        
        # Logging
        self.logger = get_logger(f"{{__name__}}.{{name}}")
        
        # FastAPI app reference (will be set by harness)
        self.app: Optional[FastAPI] = None{auth_code}
    
    async def setup(self):
        """Initialize component."""
        await super().setup()
        
        # Connect to message bus for CQRS
        await self._connect_message_bus()
        
        # Start health monitoring
        await self.health_checker.start_monitoring()
        
        self.logger.info(f"{{self.name}} API endpoint initialized at {route}")
    
    async def cleanup(self):
        """Cleanup component resources."""
        await self.health_checker.stop_monitoring()
        
        # Close message bus connection
        if self.message_bus_connection:
            await self.message_bus_connection.close()
            
        await super().cleanup()
    
    def register_routes(self, app: FastAPI):
        """Register CQRS FastAPI routes."""
        self.app = app
        
{health_endpoints}
        
{cqrs_routes}
    
    async def _connect_message_bus(self):
        """Connect to message bus for CQRS operations."""
        try:
            import aio_pika
            self.message_bus_connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.message_bus_channel = await self.message_bus_connection.channel()
            
            # Declare command exchange
            self.command_exchange = await self.message_bus_channel.declare_exchange(
                'commands', aio_pika.ExchangeType.TOPIC, durable=True
            )
            
            self.logger.info("Connected to message bus for CQRS operations")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to message bus: {{e}}")
            raise
    
    async def _publish_command_to_message_bus(self, command_data: Dict[str, Any]):
        """Publish command to message bus for true CQRS processing."""
        try:
            import aio_pika
            import json
            
            # Create message
            message = aio_pika.Message(
                json.dumps(command_data).encode(),
                content_type='application/json',
                message_id=command_data.get('command_id'),
                timestamp=datetime.utcnow()
            )
            
            # Publish to command exchange
            routing_key = f"{{self.name}}.command.{{command_data.get('command_type', 'unknown')}}"
            await self.command_exchange.publish(message, routing_key=routing_key)
            
            self.logger.info(f"Command {{command_data.get('command_id')}} published to message bus")
            
        except Exception as e:
            self.logger.error(f"Failed to publish command to message bus: {{e}}")
            raise
    
    async def _check_api_ready(self) -> bool:
        """Health check for API readiness."""
        return self.app is not None
    
    async def process(self):
        """
        Main processing loop.
        For API endpoints, this handles incoming requests via streams.
        """
        try:
            async for request_data in self.receive_streams.get('input', []):
                # Process request through stream
                response = await self._handle_stream_request(request_data)
                
                # Send response to output stream
                if 'output' in self.send_streams:
                    await self.send_streams['output'].send(response)
                    
        except Exception as e:
            self.logger.error(f"Error in {{self.name}} process loop: {{e}}")
            raise
    
    async def _handle_stream_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request received via stream."""
        try:
            # Validate request
            validated = await self.schema_validator.validate('request', request_data)
            
            # Process based on method
            method = request_data.get('method', 'POST').upper()
            
            # Record metrics
            await self.metrics.increment(f"requests_total", labels={{"method": method}})
            
            # Process the validated request data
            # This is a generic handler - customize business logic as needed
            result = {{
                "processed": True, 
                "data": validated.data,
                "method": method,
                "timestamp": self._get_current_timestamp()
            }}
            
            return {{
                "status": "success",
                "result": result,
                "request_id": request_data.get('request_id')
            }}
            
        except Exception as e:
            self.logger.error(f"Error handling stream request: {{e}}")
            await self.metrics.increment("requests_failed_total")
            
            return {{
                "status": "error",
                "error": str(e),
                "request_id": request_data.get('request_id')
            }}'''


    def _generate_cqrs_routes(self, name: str, route: str, auth_required: bool, rbac_enabled: bool, required_roles: list, rate_limit: int, api_version: str) -> str:
        """Generate CQRS-specific command and query routes using Jinja2 template."""
        
        # Prepare template variables
        template_vars = {
            'name': name,
            'name_title': name.title(),
            'route': route,
            'api_version': api_version,
            'auth_required': auth_required,
            'rbac_enabled': rbac_enabled,
            'required_roles': required_roles,
            'rate_limit': rate_limit
        }
        
        # Generate auth and RBAC dependencies
        if auth_required and rbac_enabled:
            template_vars['auth_param'] = f", user_auth: dict = Depends(self.require_roles({required_roles}))"
            template_vars['write_permission'] = f"@requires_permission('{name}', 'create')"
            template_vars['read_permission'] = f"@requires_permission('{name}', 'read')"
        elif auth_required:
            template_vars['auth_param'] = ", user: User = Depends(get_current_user)"
            template_vars['write_permission'] = f"@requires_permission('{name}', 'create')"
            template_vars['read_permission'] = f"@requires_permission('{name}', 'read')"
        else:
            template_vars['auth_param'] = ""
            template_vars['write_permission'] = ""
            template_vars['read_permission'] = ""
        
        template_vars['rate_limit_check'] = '''
            # Check rate limit
            if self.rate_limiter and not await self.rate_limiter.acquire():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )''' if rate_limit else ""
        
        cqrs_template = Template('''
        # CQRS Command Endpoint (Write Path)
        @app.post("/api/v{{ api_version }}{{ route }}/commands", response_model=CommandResponse)
        {{ write_permission }}
        async def {{ name }}_execute_command(command: {{ name_title }}Command{{ auth_param }}):
            """Execute command (write operation) - sends to message bus."""
            async with self.metrics.timer("command_duration"):
                try:{{ rate_limit_check }}
                    
                    # Generate command ID
                    command_id = str(uuid.uuid4())
                    
                    # Prepare command for handler
                    command_data = {
                        "command_id": command_id,
                        "command_type": command.command_type,
                        "aggregate_id": command.aggregate_id,
                        "data": command.data,
                        "metadata": command.metadata or {},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Publish command to message bus (true CQRS pattern)
                    await self._publish_command_to_message_bus(command_data)
                    
                    await self.metrics.increment("commands_total")
                    self.logger.info(f"Command {command_id} accepted for processing")
                    
                    return CommandResponse(
                        command_id=command_id,
                        status="accepted",
                        message="Command submitted for processing",
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
                except HTTPException:
                    raise
                except Exception as e:
                    self.logger.error(f"Error executing command: {e}")
                    await self.metrics.increment("commands_failed_total")
                    
                    return CommandResponse(
                        command_id="error",
                        status="rejected",
                        message=f"Command failed: {str(e)}",
                        timestamp=datetime.utcnow().isoformat()
                    )
        
        # CQRS Query Endpoint (Read Path)
        @app.get("/api/v{{ api_version }}{{ route }}/queries", response_model=QueryResponse)
        {{ read_permission }}
        async def {{ name }}_execute_query(
            query_type: str = "default",
            limit: int = 100,
            offset: int = 0,
            params: Optional[str] = None{{ auth_param }}
        ):
            """Execute query (read operation) - reads from Redis projections."""
            async with self.metrics.timer("query_duration"):
                try:{{ rate_limit_check }}
                    
                    # Generate query ID
                    query_id = str(uuid.uuid4())
                    
                    # Parse query parameters
                    import json
                    query_params = {}
                    if params:
                        try:
                            query_params = json.loads(params)
                        except json.JSONDecodeError:
                            self.logger.warning(f"Invalid JSON in params: {params}")
                    
                    # Prepare query for handler
                    query_data = {
                        "query_id": query_id,
                        "query_type": query_type,
                        "params": query_params,
                        "limit": limit,
                        "offset": offset
                    }
                    
                    # Execute query via query handler (reads from Redis)
                    result = await self.query_handler._handle_query(query_data)
                    
                    await self.metrics.increment("queries_total")
                    self.logger.info(f"Query {query_id} executed successfully")
                    
                    return QueryResponse(**result)
                    
                except HTTPException:
                    raise
                except Exception as e:
                    self.logger.error(f"Error executing query: {e}")
                    await self.metrics.increment("queries_failed_total")
                    
                    return QueryResponse(
                        query_id="error",
                        success=False,
                        error=f"Query failed: {str(e)}",
                        timestamp=datetime.utcnow().isoformat()
                    )''')
        
        return cqrs_template.render(**template_vars)

    def _generate_health_endpoints(self, name: str) -> str:
        """Generate standardized health check endpoints."""
        return f'''        # Health check endpoints
        @app.get("/health")
        async def health_check():
            """System health check endpoint."""
            try:
                # Get component health status
                health_status = await self.health_checker.get_health_status()
                
                # Check all critical components
                component_statuses = await self._get_component_status()
                
                # Determine overall health
                is_healthy = all([
                    health_status.get('status') == 'healthy',
                    component_statuses.get('command_handler', False),
                    component_statuses.get('query_handler', False),
                    self.app is not None
                ])
                
                return {{
                    "status": "healthy" if is_healthy else "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "service": "{name}",
                    "components": component_statuses,
                    "uptime_seconds": health_status.get('uptime_seconds', 0),
                    "dependencies": await self._check_dependencies()
                }}
                
            except Exception as e:
                self.logger.error(f"Health check failed: {{e}}")
                return {{
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "service": "{name}",
                    "error": str(e)
                }}

        @app.get("/ready")
        async def readiness_check():
            """System readiness check for orchestration."""
            try:
                # Check if all critical services are ready
                await self._verify_dependencies()
                
                # Check component readiness
                component_ready = await self._check_component_readiness()
                
                if not component_ready:
                    raise HTTPException(
                        status_code=503, 
                        detail="Component not ready"
                    )
                
                return {{
                    "status": "ready",
                    "timestamp": datetime.now().isoformat(),
                    "service": "{name}",
                    "dependencies": "ok"
                }}
                
            except Exception as e:
                self.logger.error(f"Readiness check failed: {{e}}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Not ready: {{e}}"
                )

        @app.get("/metrics")
        async def metrics_endpoint():
            """Prometheus metrics endpoint."""
            try:
                # Get component metrics
                metrics_data = await self.metrics.get_all_metrics()
                
                return {{
                    "timestamp": datetime.now().isoformat(),
                    "service": "{name}",
                    "metrics": metrics_data
                }}
                
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {{e}}")
                return {{
                    "timestamp": datetime.now().isoformat(),
                    "service": "{name}",
                    "error": str(e),
                    "metrics": {{}}
                }}'''

    async def _get_component_status(self) -> Dict[str, bool]:
        """Get status of all system components."""
        try:
            return {{
                "command_handler": await self._check_command_handler_ready(),
                "query_handler": await self._check_query_handler_ready(),
                "api_ready": await self._check_api_ready(),
                "message_bus": self.message_bus_connection is not None,
                "health_checker": self.health_checker is not None,
                "metrics": self.metrics is not None
            }}
        except Exception as e:
            self.logger.error(f"Failed to get component status: {{e}}")
            return {{}}

    async def _check_dependencies(self) -> Dict[str, str]:
        """Check external dependencies are available."""
        dependencies = {{}}
        
        try:
            # Check message bus connection
            if self.message_bus_connection:
                dependencies["message_bus"] = "connected"
            else:
                dependencies["message_bus"] = "disconnected"
            
            # Check database (if configured)
            # Add other dependency checks as needed
            
        except Exception as e:
            self.logger.error(f"Dependency check failed: {{e}}")
            dependencies["error"] = str(e)
        
        return dependencies

    async def _verify_dependencies(self) -> None:
        """Verify external dependencies are available."""
        # Check message bus connection
        if not self.message_bus_connection:
            raise Exception("Message bus not connected")
        
        # Add other critical dependency verifications

    async def _check_component_readiness(self) -> bool:
        """Check if component is ready to handle requests."""
        try:
            # Check if all handlers are ready
            command_ready = await self._check_command_handler_ready()
            query_ready = await self._check_query_handler_ready()
            api_ready = await self._check_api_ready()
            
            return command_ready and query_ready and api_ready
            
        except Exception as e:
            self.logger.error(f"Component readiness check failed: {{e}}")
            return False

    async def _check_command_handler_ready(self) -> bool:
        """Health check for command handler readiness."""
        return hasattr(self, 'command_handler') and self.command_handler is not None
    
    async def _check_query_handler_ready(self) -> bool:
        """Health check for query handler readiness."""
        return hasattr(self, 'query_handler') and self.query_handler is not None
    
    async def handle_http_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bridge method to handle HTTP requests in the harness context.
        This allows the FastAPI endpoints to call the component directly.
        """
        try:
            # Create a fake stream request
            request_data = {{
                "method": "POST",
                "data": data,
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }}
            
            # Process via the component's stream handler
            response = await self._handle_stream_request(request_data)
            
            self.logger.info(f"HTTP request processed successfully via {{self.name}}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling HTTP request: {{e}}")
            return {{
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()