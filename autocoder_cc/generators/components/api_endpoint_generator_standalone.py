"""
Standalone API Endpoint Generator
Generates APIEndpoint components that work without autocoder framework.
Part of Enterprise Roadmap v3 - standalone systems.
"""
from typing import Dict, Any, List, Optional
from jinja2 import Template
from .base_generator import BaseComponentGenerator


class StandaloneAPIEndpointGenerator(BaseComponentGenerator):
    """Generates standalone APIEndpoint components."""
    
    COMPONENT_TEMPLATE = """{{ imports }}

{{ base_class }}

# Request/Response models
class RequestData(BaseModel):
    \"\"\"Generic request data model.\"\"\"
    data: Dict[str, Any] = Field(..., description="Request payload")
    request_id: Optional[str] = Field(default=None, description="Optional request ID")

class ResponseData(BaseModel):
    \"\"\"Generic response data model.\"\"\"
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Response payload")
    message: Optional[str] = Field(default=None, description="Optional response message")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")

{{ component_class }}

{{ setup_routes }}

{{ main_block }}"""
    
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """Generate a standalone APIEndpoint component."""
        name = component_spec.get('name', 'api_endpoint')
        config = component_spec.get('config', {})
        
        # Extract configuration
        routes = config.get('routes', [{'path': f'/{name}', 'methods': ['GET', 'POST']}])
        auth_required = config.get('auth_required', False)
        rate_limit = config.get('rate_limit', 0)
        
        # Determine capabilities
        capabilities = []
        if auth_required:
            capabilities.append('auth')
        if rate_limit > 0:
            capabilities.append('rate_limit')
        
        # Generate imports
        additional_imports = []
        if auth_required:
            additional_imports.extend([
                "import jwt",
                "from datetime import datetime, timedelta",
            ])
        
        imports = self._generate_imports(
            component_type="APIEndpoint",
            capabilities=capabilities,
            additional_imports=additional_imports
        )
        
        # Generate base class if needed
        base_class = self._generate_base_class()
        
        # Generate route handlers
        route_handlers = self._generate_route_handlers(name, routes, auth_required)
        
        # Generate process implementation
        process_impl = self._generate_process_implementation(name, auth_required, rate_limit)
        
        # Generate additional methods
        additional_methods = self._generate_additional_methods(auth_required, rate_limit)
        
        # Generate component class
        component_class = self._generate_component_class(
            name=name,
            component_type="APIEndpoint",
            config=config,
            process_implementation=process_impl,
            additional_methods=additional_methods
        )
        
        # Generate setup routes method
        setup_routes = self._generate_setup_routes(name, routes, auth_required)
        
        # Generate main block
        main_block = self._generate_api_main_block(name, config.get('port', 8000))
        
        # Combine all parts using Jinja2 template
        template = Template(self.COMPONENT_TEMPLATE)
        return template.render(
            imports=imports,
            base_class=base_class,
            component_class=component_class,
            setup_routes=setup_routes,
            main_block=main_block
        )
    
    def _generate_route_handlers(self, name: str, routes: List[Dict], auth_required: bool) -> str:
        """Generate FastAPI route handler functions."""
        handlers = []
        
        for route in routes:
            path = route.get('path', f'/{name}')
            methods = route.get('methods', ['GET'])
            
            for method in methods:
                handler = self._generate_single_route_handler(name, path, method, auth_required)
                handlers.append(handler)
        
        return "\n\n".join(handlers)
    
    def _generate_single_route_handler(self, name: str, path: str, method: str, auth_required: bool) -> str:
        """Generate a single route handler."""
        method_lower = method.lower()
        auth_dep = ", auth: dict = Depends(verify_token)" if auth_required else ""
        
        # Use Jinja2 template for route handler generation
        if method_lower == 'get':
            get_handler_template = Template("""async def {{ name }}_{{ method_lower }}_handler(request: Request{{ auth_dep }}):
    \"\"\"Handle {{ method }} {{ path }}\"\"\"
    try:
        # Get component instance from app state
        component = request.app.state.component
        
        # Process GET request
        result = await component.handle_get_request()
        
        return ResponseData(status="success", data=result)
    except Exception as e:
        logging.error(f"Error in {{ name }} {{ method }}: {e}")
        raise HTTPException(status_code=500, detail=str(e))""")
        
            return get_handler_template.render(
                name=name,
                method_lower=method_lower,
                method=method,
                path=path,
                auth_dep=auth_dep
            )
        else:
            post_handler_template = Template("""async def {{ name }}_{{ method_lower }}_handler(request: Request, data: RequestData{{ auth_dep }}):
    \"\"\"Handle {{ method }} {{ path }}\"\"\"
    try:
        # Get component instance from app state
        component = request.app.state.component
        
        # Process request
        result = await component.handle_{{ method_lower }}_request(data.data)
        
        return ResponseData(status="success", data=result)
    except Exception as e:
        logging.error(f"Error in {{ name }} {{ method }}: {e}")
        raise HTTPException(status_code=500, detail=str(e))""")
        
            return post_handler_template.render(
                name=name,
                method_lower=method_lower,
                method=method,
                path=path,
                auth_dep=auth_dep
            )
    
    def _generate_process_implementation(self, name: str, auth_required: bool, rate_limit: int) -> str:
        """Generate the process method implementation."""
        return '''            # APIEndpoint components typically don't have a continuous process loop
            # They handle requests via HTTP endpoints
            # This method can be used for background tasks if needed
            
            while self._status.is_running:
                # Perform any background processing
                await anyio.sleep(60)  # Check every minute
                
                # Example: Clean up old sessions, refresh caches, etc.
                await self._perform_maintenance()'''
    
    def _generate_additional_methods(self, auth_required: bool, rate_limit: int) -> str:
        """Generate additional methods for the component."""
        methods = []
        
        # Maintenance method
        methods.append('''
    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks."""
        # TODO: Add maintenance logic
        pass''')
        
        # Request handlers
        methods.append('''
    async def handle_get_request(self) -> Dict[str, Any]:
        """Handle GET request."""
        self.increment_processed()
        
        # TODO: Implement GET logic
        return {
            "message": f"Response from {self.name}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_post_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request."""
        self.increment_processed()
        
        # Send to connected streams if any
        for stream_name, stream in self.send_streams.items():
            if stream:
                await stream.send(data)
        
        return {
            "message": "Data processed",
            "timestamp": datetime.utcnow().isoformat()
        }''')
        
        # Auth methods if needed
        if auth_required:
            methods.append(self._generate_auth_methods())
        
        return "\n".join(methods)
    
    def _generate_auth_methods(self) -> str:
        """Generate authentication methods with crypto policy enforcement."""
        return '''
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token using environment-appropriate algorithms."""
        try:
            # Use configured secret key from settings
            jwt_secret = self.config.get('jwt_secret') or settings.JWT_SECRET_KEY
            
            # Load crypto policy enforcer for environment-specific JWT algorithms
            from autocoder_cc.security.crypto_policy_enforcer import get_jwt_decode_algorithms
            allowed_algorithms = get_jwt_decode_algorithms()
            
            payload = jwt.decode(token, jwt_secret, algorithms=allowed_algorithms)
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")'''
    
    def _generate_setup_routes(self, name: str, routes: List[Dict], auth_required: bool) -> str:
        """Generate setup_routes method for dynamic route registration."""
        route_setup = []
        
        for route in routes:
            path = route.get('path', f'/{name}')
            methods = route.get('methods', ['GET'])
            
            for method in methods:
                method_lower = method.lower()
                handler_name = f"{name}_{method_lower}_handler"
                
                route_setup.append(
                    f'    app.{method_lower}("{path}", response_model=ResponseData)({handler_name})'
                )
        
        return f'''
    def setup_routes(self, app: FastAPI):
        """Register routes with FastAPI app."""
        # Store component reference in app state
        app.state.component = self
        
        # Register routes
{chr(10).join(route_setup)}'''
    
    def _generate_api_main_block(self, name: str, port: int) -> str:
        """Generate main block for running as standalone API."""
        return f'''

# Global auth dependency
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    \"\"\"Verify bearer token.\"\"\"
    # TODO: Implement proper token verification
    return {{"user": "test"}}


if __name__ == "__main__":
    # Run as standalone API server
    app = FastAPI(title="{name} API")
    
    # Create and setup component
    component = GeneratedAPIEndpoint_{name}()
    component.setup_routes(app)
    
    @app.on_event("startup")
    async def startup():
        await component.setup()
    
    @app.on_event("shutdown")
    async def shutdown():
        await component.cleanup()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port={port})
'''