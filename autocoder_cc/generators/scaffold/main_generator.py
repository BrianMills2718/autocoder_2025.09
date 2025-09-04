"""
Main.py generator plugin for the scaffold generation system.
Generates FastAPI-based main.py files following Enterprise Roadmap v2.
NO Flask, NO queue bridges - only native async with FastAPI.
"""
from typing import Dict, Any, List, Optional
from jinja2 import Template
from autocoder_cc.core.config import settings
from autocoder_cc.generators.config import generator_settings


class MainPyGenerator:
    """Generates main.py files for autocoder systems using FastAPI."""
    
    def generate(self, blueprint: Dict[str, Any], enable_metrics: bool = True) -> str:
        """Generate main.py with FastAPI and native async support."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        components = system.get('components', [])
        bindings = system.get('bindings', [])
        
        # Separate components by type
        api_components = [c for c in components if c.get('type') == 'APIEndpoint']
        data_components = [c for c in components if c.get('type') != 'APIEndpoint']
        
        # Generate imports
        imports = self._generate_imports(components, enable_metrics)
        
        # Generate FastAPI app setup
        fastapi_setup = self._generate_fastapi_setup(api_components, data_components, bindings, system_name)
        
        # Generate main function
        main_function = self._generate_main_function(system_name, enable_metrics)
        
        return f'''#!/usr/bin/env python3
"""
Generated main.py for {system_name}
Using SystemExecutionHarness with FastAPI integration
Production-ready architecture following Enterprise Roadmap v3
"""
{imports}

{fastapi_setup}

{main_function}

if __name__ == "__main__":
    asyncio.run(main())
'''

    def _generate_imports(self, components: List[Dict[str, Any]], enable_metrics: bool) -> str:
        """Generate import statements."""
        imports = [
            "import asyncio",
            "import logging",
            "import sys",
            "from pathlib import Path",
            "from contextlib import asynccontextmanager",
            "from typing import Dict, Any, Optional",
            "",
            "from fastapi import FastAPI, HTTPException, Depends",
            "from pydantic import BaseModel",
            "import anyio",
            "import uvicorn",
            "",
            "from autocoder_cc.core.config import settings",
            "from autocoder_cc.orchestration.harness import SystemExecutionHarness",
            "",
            "# Observability stack imports (Enterprise Roadmap v3 Phase 1)",
            "from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer",
        ]
        
        if enable_metrics:
            imports.append("from prometheus_client import make_asgi_app")
        
        return "\n".join(imports)
    
    def _generate_component_creation(self, components: List[Dict[str, Any]]) -> str:
        """Generate component instantiation code."""
        lines = []
        
        for comp in components:
            name = comp.get('name', '')
            comp_type = comp.get('type', '')
            config = comp.get('config', {})
            
            if comp_type == 'APIEndpoint':
                # API endpoints are handled differently in FastAPI
                continue
            
            config_str = self._format_config(config)
            lines.append(f'{name} = {comp_type}("{name}", {config_str})')
        
        return "\n".join(lines) if lines else "# No data components to create"
    
    def _generate_fastapi_setup(self, api_components: List[Dict[str, Any]], 
                                data_components: List[Dict[str, Any]], 
                                bindings: List[Dict[str, Any]], 
                                system_name: str) -> str:
        """Generate FastAPI app setup with proper async handling."""
        
        # Generate Pydantic models for API components
        models = self._generate_pydantic_models(api_components)
        
        # Generate lifespan context manager
        lifespan = self._generate_lifespan(system_name)
        
        # Generate API routes
        routes = self._generate_api_routes(api_components)
        
        return f"""{models}

{lifespan}

# Create FastAPI app
app = FastAPI(
    title="{settings.DOCKER_IMAGE_PREFIX} API",
    version="{settings.API_VERSION}",
    lifespan=lifespan
)

{routes}

@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint.\"\"\"
    return {{"status": "healthy", "version": "{settings.API_VERSION}"}}

@app.get("/metrics")
async def metrics():
    \"\"\"Prometheus metrics endpoint.\"\"\"
    # Metrics are exposed via middleware
    pass"""

    def _generate_pydantic_models(self, api_components: List[Dict[str, Any]]) -> str:
        """Generate Pydantic models for API request/response validation."""
        if not api_components:
            return "# No API components - no models needed"
        
        models = ["# Pydantic models for API validation"]
        
        for comp in api_components:
            name = comp.get('name', '')
            config = comp.get('config', {})
            
            # Generate request model
            models.append(f"""
class {name.title()}Request(BaseModel):
    \"\"\"Request model for {name}.\"\"\"
    data: Dict[str, Any]
    
class {name.title()}Response(BaseModel):
    \"\"\"Response model for {name}.\"\"\"
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None""")
        
        return "\n".join(models)
    
    def _generate_lifespan(self, system_name: str) -> str:
        """Generate lifespan context manager for background tasks."""
        return f"""# Global reference to harness
harness: Optional[SystemExecutionHarness] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"
    Lifespan context manager for FastAPI.
    Uses SystemExecutionHarness.create_simple_harness for automatic setup.
    \"\"\"
    global harness
    
    # Initialize observability stack (Enterprise Roadmap v3 Phase 1)
    system_logger = get_logger("system.main", component="SystemMain")
    system_logger.info(
        "Initializing system with simplified harness",
        operation="system_init",
        tags={{"system_name": "{system_name}", "harness_mode": "simple"}}
    )
    
    try:
        # Use simplified harness creation - automatically discovers components and blueprint
        blueprint_file = Path(__file__).parent / "blueprint.yaml"
        component_dir = Path(__file__).parent / "components"
        
        harness = SystemExecutionHarness.create_simple_harness(
            blueprint_file=str(blueprint_file) if blueprint_file.exists() else None,
            component_dir=str(component_dir) if component_dir.exists() else None,
            system_name="{system_name}"
        )
        
        # Start harness in background
        await harness.start()
        system_logger.info("SystemExecutionHarness started successfully")
        
        yield  # FastAPI runs here
        
    except Exception as e:
        system_logger.error(f"Failed to initialize harness: {{e}}")
        # FAIL-FAST: System must not continue without properly initialized harness
        raise RuntimeError(f"System startup failed due to harness initialization error: {{e}}")
        
    finally:
        # Shutdown harness gracefully
        if harness:
            try:
                system_logger.info("Shutting down SystemExecutionHarness...")
                await harness.stop()
                system_logger.info("SystemExecutionHarness stopped successfully")
            except Exception as e:
                system_logger.error(f"Error during harness shutdown: {{e}}")
                # FAIL-FAST: Propagate shutdown errors instead of silent failure
                raise RuntimeError(f"System shutdown failed during harness cleanup: {{e}}")"""

    def _generate_harness_registration(self, components: List[Dict[str, Any]]) -> str:
        """Generate component registration code for harness."""
        lines = []
        for comp in components:
            name = comp.get('name', '')
            lines.append(f'    harness.register_component("{name}", {name})')
        return "\n".join(lines) if lines else "    # No components to register"
    
    def _generate_harness_connections(self, bindings: List[Dict[str, Any]]) -> str:
        """Generate component connection code for harness."""
        lines = []
        for binding in bindings:
            source = binding.get('source', {})
            target = binding.get('target', {})
            
            source_str = f"{source.get('component', '')}.{source.get('stream', '')}"
            target_str = f"{target.get('component', '')}.{target.get('stream', '')}"
            
            lines.append(f'    harness.connect("{source_str}", "{target_str}")')
        
        return "\n".join(lines) if lines else "    # No connections to make"
    
    def _generate_api_routes(self, api_components: List[Dict[str, Any]]) -> str:
        """Generate FastAPI routes with proper async stream communication."""
        if not api_components:
            return "# No API routes to generate"
        
        routes = []
        
        for comp in api_components:
            name = comp.get('name', '')
            config = comp.get('config', {})
            route = config.get('route', f'/{name}')
            methods = config.get('methods', ['POST'])
            
            for method in methods:
                route_func = self._generate_route_function(name, route, method)
                routes.append(route_func)
        
        return "\n\n".join(routes)
    
    def _generate_route_function(self, name: str, route: str, method: str) -> str:
        """Generate a single route function with async stream communication."""
        method_lower = method.lower()
        
        if method_lower == 'get':
            return f"""@app.get("{route}")
async def {name}_get():
    \"\"\"GET endpoint for {name}.\"\"\"
    # For GET requests, typically read from a store or cache
    try:
        # Direct async communication - no queues!
        result = await harness.query_component("{name}", {{"action": "get"}})
        return {name.title()}Response(status="success", result=result)
    except Exception as e:
        logging.error(f"Error in {name} GET: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))"""
        
        else:  # POST, PUT, DELETE
            return f"""@app.{method_lower}("{route}", response_model={name.title()}Response)
async def {name}_{method_lower}(request: {name.title()}Request):
    \"\"\"{method} endpoint for {name}.\"\"\"
    try:
        # Direct async stream communication - NO QUEUES!
        if not harness or not hasattr(harness, 'send_to_component'):
            # FAIL-FAST: System must not operate without properly initialized harness
            raise HTTPException(status_code=503, detail="System harness not properly initialized - cannot process requests")
        
        await harness.send_to_component("{name}", request.data)
        return {name.title()}Response(status="accepted")
    except Exception as e:
        logging.error(f"Error in {name} {method}: {{e}}")
        # FAIL-FAST: Propagate errors instead of masking them
        raise HTTPException(status_code=500, detail=f"Request processing failed: {{e}}")"""
    
    def _generate_main_function(self, system_name: str, enable_metrics: bool) -> str:
        """Generate the main function."""
        metrics_setup = ""
        if enable_metrics:
            metrics_setup = """
    # Add Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
"""
        
        return f"""async def main():
    \"\"\"
    Main entry point using SystemExecutionHarness.
    Generated system: {system_name}
    \"\"\"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting {system_name} system...")
    
    try:
        # Check if we're running in standalone mode (with harness only)
        if "--standalone" in sys.argv:
            logger.info("Running in standalone mode (harness only, no HTTP server)")
            
            # Use simplified harness creation
            blueprint_file = Path(__file__).parent / "blueprint.yaml"
            component_dir = Path(__file__).parent / "components"
            
            harness = SystemExecutionHarness.create_simple_harness(
                blueprint_file=str(blueprint_file) if blueprint_file.exists() else None,
                component_dir=str(component_dir) if component_dir.exists() else None,
                system_name="{system_name}"
            )
            
            logger.info("✅ {system_name} harness ready")
            logger.info("🔗 Health check available at: SystemExecutionHarness.get_system_health_summary()")
            
            # Start and wait for completion
            await harness.start()
            
            try:
                await harness.wait_for_completion()
            except KeyboardInterrupt:
                logger.info("\\n🛑 Shutdown requested...")
            finally:
                await harness.stop()
                logger.info("✅ System stopped gracefully")
        
        else:
            # Run with FastAPI server (default mode)
            logger.info("Running in HTTP server mode (FastAPI + harness)")
            
            # Add metrics if enabled
{metrics_setup}
            
            # Start the server
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=settings.PORT_RANGE_START,
                log_level=settings.LOG_LEVEL.lower(),
                reload=settings.DEBUG_MODE
            )
            server = uvicorn.Server(config)
            
            logger.info(f"✅ {system_name} system running")
            logger.info(f"🔗 API available at: http://localhost:{{settings.PORT_RANGE_START}}")
            logger.info(f"🔗 Health check: http://localhost:{{settings.PORT_RANGE_START}}/health")
            
            await server.serve()
            
    except Exception as e:
        logger.error(f"❌ System startup failed: {{e}}")
        sys.exit(1)"""
    
    def _format_config(self, config: Dict[str, Any]) -> str:
        """Format configuration dictionary as Python code."""
        if not config:
            return "{}"
        
        # Simple formatting - could be enhanced
        items = []
        for key, value in config.items():
            if isinstance(value, str):
                items.append(f'"{key}": "{value}"')
            else:
                items.append(f'"{key}": {value}')
        
        return "{" + ", ".join(items) + "}"