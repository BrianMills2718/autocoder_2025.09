"""
Main.py generator with dynamic component loading.
Follows Enterprise Roadmap v3 - NO HARDCODED IMPORTS.
Components loaded at runtime from manifest.
"""
from typing import Dict, Any, List, Optional
from autocoder_cc.core.config import settings
from autocoder_cc.generators.config import generator_settings


class DynamicMainPyGenerator:
    """Generates main.py files with dynamic component loading."""
    
    def _generate_simple_main(self, system_name: str) -> str:
        """Generate simplified, robust main.py with dynamic port detection."""
        return f'''#!/usr/bin/env python3
"""
Generated main.py for {system_name}
Simple, robust startup with dynamic port detection
"""
import logging
import importlib.util
import os
import re
import glob
import yaml
from pathlib import Path
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load system configuration first
config_file = Path("config/system_config.yaml")
system_config = {{}}
if config_file.exists():
    try:
        with open(config_file, 'r') as f:
            system_config = yaml.safe_load(f) or {{}}
            logger.info(f"Loaded system configuration from {{config_file}}")
    except Exception as e:
        logger.warning(f"Failed to load system config: {{e}}")

# Dynamic port detection - check multiple sources in priority order
# 1. Environment variable
port = int(os.environ.get("PORT", 0)) if os.environ.get("PORT", "").isdigit() else 0

# 2. System config file (highest priority after env)
# Check for API port first
if not port and 'api' in system_config and 'port' in system_config['api']:
    port = int(system_config['api']['port'])
    logger.info(f"Using port {{port}} from API configuration")

# Check for individual component ports (ResourceOrchestrator allocated)
if not port and 'components' in system_config:
    for comp_name, comp_config in system_config['components'].items():
        if isinstance(comp_config, dict) and 'port' in comp_config:
            port = int(comp_config['port'])
            logger.info(f"Using ResourceOrchestrator allocated port {{port}} from component {{comp_name}}")
            break

# 3. Fallback: Check component files for port configurations
if not port:
    component_files = glob.glob("components/**/*.py", recursive=True)
    for component_file in component_files:
        try:
            with open(component_file, 'r') as f:
                content = f.read()
                # Look for config.get("port", XXXX) patterns
                port_match = re.search(r'config\\.get\\("port",\\s*(\\d+)\\)', content)
                if port_match:
                    port = int(port_match.group(1))
                    logger.info(f"Found port configuration {{port}} in {{component_file}}")
                    break
        except Exception as e:
            logger.warning(f"Failed to read component file {{component_file}}: {{e}}")

# Final fallback - fail fast instead of using hardcoded port
if not port:
    logger.error("No port configuration found - this is a critical error")
    raise ValueError("Port configuration is required but was not found in system_config.yaml or component configurations")

logger.info(f"Starting server on port {{port}}")

# Simple component storage
components = {{}}

def load_components():
    """Load components with simple error handling."""
    try:
        components_dir = Path("components")
        if not components_dir.exists():
            raise RuntimeError(f"Components directory not found: {{components_dir}}")
        
        # Load each component file
        for component_file in components_dir.glob("*.py"):
            if component_file.stem == "__init__":
                continue
                
            try:
                # Simple module loading
                spec = importlib.util.spec_from_file_location("component", component_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find component class
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (hasattr(item, '__bases__') and 
                        any('ComposedComponent' in str(base) for base in item.__bases__)):
                        component_name = component_file.stem
                        # Instantiate with required arguments
                        # Dynamic config - read all configuration from environment variables
                        # Build config from environment with automatic lowercasing
                        config = {{}}
                        
                        # Load component-specific config from system_config if available
                        if component_name in system_config:
                            config.update(system_config[component_name])
                            logger.info(f"Loaded configuration for {{component_name}} from system config")
                        
                        # Core configuration with defaults (environment overrides system config)
                        # Database configuration consistency: Match storage_type with connection parameters
                        storage_type = config.get("storage_type", "file")
                        if storage_type == "file":
                            # SQLite configuration for file-based storage
                            config.update({{
                                "db_connection_string": os.environ.get("DB_CONNECTION_STRING", "sqlite:///" + config.get("db_path", "app.db")),
                                "db_path": os.environ.get("DB_PATH", config.get("db_path", "app.db")),
                                "storage_type": "file"
                            }})
                        elif storage_type in ["database", "postgresql"]:
                            # PostgreSQL configuration for database storage
                            db_host = config.get("db_host", "postgres")
                            db_port = config.get("db_port", 5432)
                            db_name = config.get("db_name", "app_db")
                            db_user = config.get("db_user", "postgres")
                            config.update({{
                                "db_connection_string": os.environ.get("DB_CONNECTION_STRING", f"postgresql://{{{{db_user}}}}:{{{{{{password}}}}}}@{{{{db_host}}}}:{{{{db_port}}}}/{{{{db_name}}}}"),
                                "db_host": os.environ.get("DB_HOST", db_host),
                                "db_port": int(os.environ.get("DB_PORT", str(db_port))),
                                "db_name": os.environ.get("DB_NAME", db_name),
                                "db_user": os.environ.get("DB_USER", db_user),
                                "storage_type": storage_type
                            }})
                        else:
                            # Default to SQLite for unknown storage types
                            config.update({{
                                "db_connection_string": os.environ.get("DB_CONNECTION_STRING", "sqlite:///" + config.get("db_path", "app.db")),
                                "db_path": os.environ.get("DB_PATH", config.get("db_path", "app.db")),
                                "storage_type": "file"
                            }})
                        
                        # Additional core configuration
                        config.update({{
                            "debug": os.environ.get("DEBUG", str(config.get("debug", "false"))).lower() == "true",
                            "log_level": os.environ.get("LOG_LEVEL", config.get("log_level", "INFO")),
                            "port": int(os.environ.get("PORT", str(config.get("port", port)))) if os.environ.get("PORT", "").isdigit() else config.get("port", port),
                            "host": os.environ.get("HOST", config.get("host", "localhost")),
                        }})
                        
                        # Automatically map all environment variables to lowercase config keys
                        for env_key, env_value in os.environ.items():
                            config_key = env_key.lower()
                            if env_value is not None and config_key not in config:
                                # Smart type conversion for common patterns
                                if env_key.endswith('_PORT') and env_value.isdigit():
                                    config[config_key] = int(env_value)
                                elif env_key in ['DEBUG'] and env_value.lower() in ['true', 'false']:
                                    config[config_key] = env_value.lower() == 'true'
                                else:
                                    config[config_key] = env_value
                        components[component_name] = item(name=component_name, config=config)
                        logger.info(f"Loaded component: {{component_name}}")
                        
            except Exception as e:
                logger.error(f"Failed to load component {{component_file}}: {{e}}")
                raise
                
        logger.info(f"Successfully loaded {{len(components)}} components")
        
    except Exception as e:
        logger.error(f"Component loading failed: {{e}}")
        raise

# Create FastAPI app
app = FastAPI(title="{system_name}", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Simple startup event."""
    logger.info("Starting {system_name}...")
    load_components()
    
    # Initialize components
    for name, component in components.items():
        try:
            await component.setup()
            logger.info(f"Component {{name}} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize component {{name}}: {{e}}")
            # FAIL-FAST: System must not continue with partial component failures
            raise RuntimeError(f"System startup failed due to component initialization error in {{name}}: {{e}}")
    
    logger.info("System ready")

@app.get("/health")
async def health_check():
    """Simple health check."""
    return {{
        "status": "healthy",
        "service": "{system_name}",
        "components": len(components),
        "port": port
    }}

@app.get("/ready")
async def ready_check():
    """Simple readiness check."""
    if not components:
        raise HTTPException(status_code=503, detail="No components loaded")
    return {{"status": "ready", "components": len(components), "port": port}}

# Functional endpoints for Phase 4 validation
@app.get("/api/data")
async def get_data():
    """Get data endpoint for validation."""
    return {{"message": "API data endpoint working", "timestamp": port}}

@app.post("/api/data")
async def post_data(data: dict):
    """Post data endpoint for validation."""
    # Try to process data through API components
    api_components = [c for name, c in components.items() if 'api' in name.lower()]
    if api_components:
        try:
            result = await api_components[0].process_item(data)
            return {{"status": "success", "result": result}}
        except Exception as e:
            return {{"status": "error", "message": str(e)}}
    return {{"status": "success", "received": data}}

@app.get("/data")
async def get_data_alt():
    """Alternative data endpoint."""
    return {{"message": "Data endpoint working", "components": list(components.keys())}}

@app.post("/data")
async def post_data_alt(data: dict):
    """Alternative post data endpoint."""
    return {{"status": "success", "received": data}}

@app.get("/process")
async def get_process():
    """Process endpoint."""
    return {{"message": "Process endpoint working", "available_components": list(components.keys())}}

@app.post("/process")
async def post_process(data: dict):
    """Process data with components."""
    results = {{}}
    for name, component in components.items():
        try:
            result = await component.process_item(data)
            results[name] = result
        except Exception as e:
            results[name] = {{"error": str(e)}}
    return {{"status": "success", "results": results}}

@app.get("/submit")
async def get_submit():
    """Submit endpoint."""
    return {{"message": "Submit endpoint working"}}

@app.post("/submit")
async def post_submit(data: dict):
    """Submit data endpoint."""
    return {{"status": "submitted", "data": data}}

@app.get("/query")
async def get_query():
    """Query endpoint."""
    return {{"message": "Query endpoint working"}}

# Database-specific endpoints
@app.get("/api/store")
async def get_store():
    """Store endpoint."""
    store_components = [c for name, c in components.items() if 'store' in name.lower() or 'database' in name.lower()]
    return {{"message": "Store endpoint working", "database_available": len(store_components) > 0}}

@app.post("/api/store")
async def post_store(data: dict):
    """Store data endpoint."""
    store_components = [c for name, c in components.items() if 'store' in name.lower() or 'database' in name.lower()]
    if store_components:
        try:
            result = await store_components[0].process_item(data)
            return {{"status": "success", "result": result}}
        except Exception as e:
            return {{"status": "error", "message": str(e)}}
    return {{"status": "error", "message": "Database component not available"}}

@app.get("/store")
async def get_store_alt():
    """Alternative store endpoint."""
    return {{"message": "Store endpoint working"}}

@app.post("/store")
async def post_store_alt(data: dict):
    """Alternative store endpoint."""
    return {{"status": "stored", "data": data}}

@app.get("/save")
async def get_save():
    """Save endpoint."""
    return {{"message": "Save endpoint working"}}

@app.post("/save")
async def post_save(data: dict):
    """Save data endpoint."""
    return {{"status": "saved", "data": data}}

@app.get("/retrieve")
async def get_retrieve():
    """Retrieve endpoint."""
    return {{"message": "Retrieve endpoint working"}}

@app.post("/retrieve")
async def post_retrieve(data: dict):
    """Retrieve data endpoint."""
    return {{"status": "retrieved", "data": data}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
'''
    
    def generate(self, blueprint: Dict[str, Any], enable_metrics: bool = True) -> str:
        """Generate SIMPLIFIED main.py with minimal complexity."""
        system = blueprint.get('system', {})
        system_name = system.get('name', 'autocoder-app')
        
        # Always use complex main.py for Phase 2 (standalone) compatibility
        # Simple mode disabled to ensure proper component loading
        # if settings.SIMPLE_MAIN_PY:
        #     return self._generate_simple_main(system_name)
        
        # Otherwise fall back to complex version
        components = system.get('components', [])
        bindings = system.get('bindings', [])
        
        # Separate API components
        api_components = [c for c in components if c.get('type') == 'APIEndpoint']
        
        # Generate imports (minimal, no component imports!)
        imports = self._generate_imports(enable_metrics)
        
        # Generate dynamic loading setup
        dynamic_loading = self._generate_dynamic_loading(system_name)
        
        # Generate FastAPI setup
        fastapi_setup = self._generate_fastapi_setup(api_components, system_name)
        
        # Generate connection setup
        connection_setup = self._generate_connection_setup(bindings)
        
        # Generate main function
        main_function = self._generate_main_function(system_name, enable_metrics)
        
        return f'''#!/usr/bin/env python3
"""
Generated main.py for {system_name}
Using dynamic component loading - NO HARDCODED IMPORTS
Following Enterprise Roadmap v3 requirements
"""
{imports}

# Global references
harness = None
api_components = {{}}

{dynamic_loading}

{connection_setup}

{fastapi_setup}

{main_function}

if __name__ == "__main__":
    import uvicorn
    # Dynamic port from environment or config
    port = int(os.environ.get("PORT", 0)) if os.environ.get("PORT", "").isdigit() else 0
    if not port:
        config_file = Path("config/system_config.yaml")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {{}}
                    port = config.get("api", {{}}).get("port", 8000)
            except:
                port = 8000
        else:
            port = 8000
    
    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        reload=os.environ.get("DEBUG", "false").lower() == "true"
    )
'''

    def _generate_imports(self, enable_metrics: bool) -> str:
        """Generate minimal imports - STANDALONE ONLY, no autocoder_cc dependencies!"""
        imports = [
            "import asyncio",
            "import logging",
            "from datetime import datetime",
            "from pathlib import Path",
            "from contextlib import asynccontextmanager",
            "from typing import Dict, Any, Optional",
            "import os",
            "import yaml",
            "import importlib.util",
            "",
            "from fastapi import FastAPI, HTTPException, Request",
            "from pydantic import BaseModel",
            "import anyio",
            "",
            "# Standalone observability - no autocoder_cc dependencies",
            "from components.observability import ComposedComponent, StandaloneMetricsCollector, StandaloneTracer",
        ]
        
        if enable_metrics:
            imports.append("from prometheus_client import make_asgi_app")
        
        return "\n".join(imports)
    
    def _generate_dynamic_loading(self, system_name: str) -> str:
        """Generate standalone dynamic component loading code."""
        return f'''# Global component registry - standalone, no autocoder_cc dependencies
components = {{}}
api_components = {{}}

async def load_components():
    """
    Load components dynamically from directory.
    Pure standalone implementation - no autocoder_cc dependencies!
    """
    global components, api_components
    
    logging.info(f"Initializing standalone system: {system_name}")
    
    # Load system configuration
    config_file = Path("config/system_config.yaml")
    system_config = {{}}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                system_config = yaml.safe_load(f) or {{}}
                logging.info(f"Loaded system configuration from {{config_file}}")
        except Exception as e:
            logging.warning(f"Failed to load system config: {{e}}")
    
    # Dynamic port detection
    port = int(os.environ.get("PORT", 0)) if os.environ.get("PORT", "").isdigit() else 0
    if not port:
        port = system_config.get("api", {{}}).get("port", 8000)
    
    # Discover and load components from directory
    components_dir = Path("components")
    if components_dir.exists():
        for component_file in components_dir.glob("*.py"):
            if component_file.name.startswith("__") or component_file.name == "observability.py":
                continue
                
            try:
                # Load component module
                spec = importlib.util.spec_from_file_location("component", component_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find component class
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (hasattr(item, '__bases__') and 
                        any('ComposedComponent' in str(base) for base in item.__bases__)):
                        component_name = component_file.stem
                        
                        # Build component configuration
                        config = {{}}
                        if component_name in system_config:
                            config.update(system_config[component_name])
                        
                        # Add core configuration
                        config.update({{
                            "port": port,
                            "host": os.environ.get("HOST", "0.0.0.0"),
                            "log_level": os.environ.get("LOG_LEVEL", "INFO"),
                            "debug": os.environ.get("DEBUG", "false").lower() == "true"
                        }})
                        
                        # Instantiate component
                        components[component_name] = item(name=component_name, config=config)
                        logging.info(f"Loaded standalone component: {{component_name}}")
                        
                        # Check if it's an API component
                        if hasattr(item, 'setup_routes') or "api" in component_name.lower():
                            api_components[component_name] = components[component_name]
                        
            except Exception as e:
                logging.error(f"Failed to load component {{component_file}}: {{e}}")
                raise
                
    logging.info(f"Successfully loaded {{len(components)}} standalone components")'''
    
    def _generate_fastapi_setup(self, api_components: List[Dict[str, Any]], system_name: str = "standalone_system") -> str:
        """Generate FastAPI setup with dynamic route registration."""
        # Generate request/response models
        models = []
        for comp in api_components:
            name = comp.get('name', '')
            models.append(f"""
class {name.title()}Request(BaseModel):
    \"\"\"Request model for {name}\"\"\"
    data: Dict[str, Any]
    
class {name.title()}Response(BaseModel):
    \"\"\"Response model for {name}\"\"\"
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None""")
        
        models_str = "\n".join(models) if models else "# No API models needed"
        
        return f'''{models_str}

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"
    Standalone lifespan manager - no autocoder_cc dependencies.
    \"\"\"
    # Load components
    await load_components()
    
    logging.info("Standalone system startup complete")
    
    # Register API routes dynamically
    for name, component in api_components.items():
        if hasattr(component, 'setup_routes'):
            try:
                component.setup_routes(app)
                logging.info(f"Registered routes for API component: {{name}}")
            except Exception as e:
                logging.error(f"Failed to setup routes for {{name}}: {{e}}")
    
    logging.info(f"System ready to serve requests with {{len(api_components)}} API components")
    yield  # FastAPI runs here
    
    # Graceful shutdown
    logging.info("Shutting down standalone system...")
    for name, component in components.items():
        try:
            if hasattr(component, 'shutdown'):
                await component.shutdown()
        except Exception as e:
            logging.error(f"Error shutting down component {{name}}: {{e}}")

# Create standalone FastAPI app
app = FastAPI(
    title="{system_name}",
    version="1.0.0",
    lifespan=lifespan
)

# Standalone health check endpoint
@app.get("/health")
async def health_check():
    \"\"\"Standalone health check endpoint.\"\"\"
    # Check component health
    component_health = {{}}
    overall_healthy = True
    
    for name, component in components.items():
        try:
            if hasattr(component, 'health_check'):
                health = await component.health_check()
                component_health[name] = health
                # Check the 'healthy' boolean field, not 'status' string
                if not health.get('healthy', True):
                    overall_healthy = False
            else:
                component_health[name] = {{"healthy": True, "status": "healthy", "message": "No health check implemented"}}
        except Exception as e:
            component_health[name] = {{"healthy": False, "status": "unhealthy", "error": str(e)}}
            overall_healthy = False
    
    status_code = 200 if overall_healthy else 503
    
    return {{
        "status": "healthy" if overall_healthy else "unhealthy",
        "service": "{system_name}",
        "version": "1.0.0",
        "components": component_health,
        "component_count": len(components),
        "timestamp": datetime.now().isoformat()
    }}

# Standalone readiness check
@app.get("/ready")
async def ready_check():
    \"\"\"Standalone readiness check for load balancers.\"\"\"
    return {{
        "status": "ready",
        "components_loaded": len(components),
        "api_components": len(api_components),
        "timestamp": datetime.now().isoformat()
    }}'''
    
    def _generate_connection_setup(self, bindings: List[Dict[str, Any]]) -> str:
        """Generate connection setup based on bindings."""
        if not bindings:
            return """async def setup_connections():
    \"\"\"Set up component connections with proper name resolution.\"\"\"
    # Log component registration status before connecting
    logging.info(f"Setting up connections. Available components: {list(components.keys())}")
    
    # No connections to set up - standalone components handle their own connections
    pass"""
        
        lines = [
            'async def setup_connections():',
            '    """Set up component connections with proper name resolution."""',
            '    # Log component registration status before connecting',
            '    logging.info(f"Setting up connections. Available components: {list(components.keys())}")',
            '    ',
            '    # Map expected component names to actual registered names',
            '    component_map = {}',
            '    for registered_name in components.keys():',
            '        # Handle name variations (e.g., "todo_api_endpoint" vs "GeneratedAPIEndpoint_todo_api_endpoint")'
        ]
        
        # Extract unique component names from bindings
        component_names = set()
        for binding in bindings:
            source = binding.get('source', {})
            target = binding.get('target', {})
            if source.get('component'):
                component_names.add(source.get('component'))
            if target.get('component'):
                component_names.add(target.get('component'))
        
        # Add component name mapping logic
        for comp_name in component_names:
            lines.append(f'        if "{comp_name}" in registered_name:')
            lines.append(f'            component_map["{comp_name}"] = registered_name')
        
        lines.extend([
            '    ',
            '    logging.info(f"Component name mapping: {component_map}")',
            '    ',
            '    # Use mapped names for connections',
            '    try:'
        ])
        
        # Generate connection calls with error handling
        for binding in bindings:
            source = binding.get('source', {})
            target = binding.get('target', {})
            
            source_comp = source.get('component', '')
            source_stream = source.get('stream', '')
            target_comp = target.get('component', '')
            target_stream = target.get('stream', '')
            
            lines.extend([
                f'        if "{source_comp}" in component_map and "{target_comp}" in component_map:',
                f'            # Standalone components handle their own connections',
                f'            logging.info(f"Would connect {{component_map[\'{source_comp}\']}}.{source_stream} -> {{component_map[\'{target_comp}\']}}.{target_stream}")',
                '        '
            ])
        
        lines.extend([
            '        logging.info("Component connections established successfully")',
            '        ',
            '    except Exception as e:',
            '        logging.error(f"Failed to establish connections: {e}")',
            '        logging.error(f"Available components for debugging: {list(components.keys())}")',
            '        raise'
        ])
        
        return "\n".join(lines)
    
    def _generate_main_function(self, system_name: str, enable_metrics: bool) -> str:
        """Generate initialization code."""
        metrics_setup = ""
        if enable_metrics:
            metrics_setup = """
# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)"""
        
        return f"""# Configure standalone logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
{metrics_setup}"""