#!/usr/bin/env python3
"""
System Scaffold Generator - Phase 1 of Two-Phase Generation
Generates main.py files with SystemExecutionHarness setup based on parsed system blueprints
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent, ParsedBinding
from autocoder_cc.resource_orchestrator import ResourceOrchestrator, ResourceRequirement, ResourceType
from autocoder_cc.generators.config import generator_settings
from autocoder_cc.observability.structured_logging import get_logger
from autocoder_cc.core.config import settings
from autocoder_cc.blueprint_language.database_config_manager import DatabaseConfigManager


@dataclass
class GeneratedScaffold:
    """Generated system scaffold files"""
    main_py: str
    config_yaml: str
    requirements_txt: str
    dockerfile: str


class SystemScaffoldGenerator:
    """
    Generates system scaffolds (main.py + config) that use SystemExecutionHarness.
    
    This is Phase 1 of two-phase generation:
    1. Generate scaffold (main.py) - this class
    2. Generate component logic - ComponentLogicGenerator
    
    Key principles:
    - Creates harness-based main.py files
    - Handles component registration and connections
    - Generates proper configuration structure
    - Ensures non-blocking patterns
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resource_orchestrator = ResourceOrchestrator()
    
    def generate_system(self, system_blueprint: ParsedSystemBlueprint, enable_metrics: bool = True) -> GeneratedScaffold:
        """Generate complete system scaffold from blueprint"""

        # Feature flag: if USE_TYPED_IR is enabled, we expect a compiler-based flow (not implemented yet)
        if settings.USE_TYPED_IR:
            raise NotImplementedError(
                "IR → code compilation path is not implemented yet (Phase 2)."
            )

        # Use ResourceOrchestrator for centralized resource allocation
        resource_requirements = []
        
        # Add component-specific resource requirements
        for component in system_blueprint.system.components:
            if component.type == "APIEndpoint":
                req = ResourceRequirement(
                    component_name=component.name,
                    component_type=component.type,
                    resource_type=ResourceType.NETWORK_PORT,
                    priority=1
                )
                resource_requirements.append(req)
        
        # Add metrics endpoint requirement if enabled
        if enable_metrics:
            metrics_req = ResourceRequirement(
                component_name="metrics",
                component_type="MetricsEndpoint", 
                resource_type=ResourceType.NETWORK_PORT,
                priority=1
            )
            resource_requirements.append(metrics_req)
        
        # Allocate resources using orchestrator
        self.resource_manifest = self.resource_orchestrator.allocate_resources(
            resource_requirements, 
            system_blueprint.system.name
        )
        
        # Filter bindings to only include connections between supported component types
        filtered_bindings = self._filter_bindings_for_supported_components(system_blueprint)
        
        # Generate all scaffold files with allocated resources
        main_py = self._generate_main_py(system_blueprint, enable_metrics, filtered_bindings)
        config_yaml = self._generate_config_yaml(system_blueprint, enable_metrics)
        requirements_txt = self._generate_requirements_txt(system_blueprint)
        dockerfile = self._generate_dockerfile(system_blueprint)
        component_manifest = self._generate_component_manifest(system_blueprint.system.components, enable_metrics)
        rbac_config = self._generate_rbac_config(system_blueprint)
        security_middleware = self._generate_security_middleware(system_blueprint)
        
        # Write files to output directory
        files_to_write = {
            'main.py': main_py,
            'config/system_config.yaml': config_yaml,
            'requirements.txt': requirements_txt,
            'Dockerfile': dockerfile,
            'components/manifest.yaml': component_manifest,
            'rbac.yaml': rbac_config,
            'security_middleware.py': security_middleware
        }
        
        # No more Gunicorn config - we use uvicorn for FastAPI
        
        self._write_files(system_blueprint.system.name, files_to_write)
        
        # After writing scaffold files – emit Typed IR if flag enabled (Phase 0.5)
        if settings.EMIT_TYPED_IR:
            try:
                import json
                from autocoder_cc.ir.builder import build_ir
                ir_dict = build_ir(system_blueprint)
                generated_dir = Path("generated")
                generated_dir.mkdir(parents=True, exist_ok=True)
                ir_file = generated_dir / f"ir.{ir_dict['ir_version']}.json"
                with ir_file.open("w", encoding="utf-8") as fp:
                    json.dump(ir_dict, fp, indent=2)
                # Optionally validate IR (non-blocking unless STRICT_IR)
                if settings.STRICT_IR or settings.CI_BLOCK_ON_IR:
                    try:
                        import subprocess, sys
                        subprocess.run([
                            sys.executable,
                            str(Path(__file__).parents[2] / "tools" / "validate_ir.py"),
                            str(ir_file)
                        ], check=settings.CI_BLOCK_ON_IR)
                    except subprocess.CalledProcessError as ir_err:
                        if settings.STRICT_IR:
                            raise RuntimeError("IR validation failed in STRICT_IR mode") from ir_err
                        # else: non-blocking – just print warning
            except Exception as emit_err:
                print(f"[warning] Failed to emit typed IR: {emit_err}")

        return GeneratedScaffold(
            main_py=main_py,
            config_yaml=config_yaml,
            requirements_txt=requirements_txt,
            dockerfile=dockerfile
        )
    
    def _generate_main_py(self, system_blueprint: ParsedSystemBlueprint, enable_metrics: bool = True, filtered_bindings: List[ParsedBinding] = None) -> str:
        """Generate main.py file - always uses FastAPI with native async, NO Flask"""
        
        system = system_blueprint.system
        
        # Always use FastAPI - no more Flask or hybrid architectures
        # This follows Enterprise Roadmap v2: NO lazy bridges, NO Flask
        return self._generate_fastapi_main(system_blueprint, enable_metrics, filtered_bindings)
    
    def _generate_fastapi_main(self, system_blueprint: ParsedSystemBlueprint, enable_metrics: bool = True, filtered_bindings: List[ParsedBinding] = None) -> str:
        """
        Generate FastAPI-based main.py with DYNAMIC LOADING support.
        NO Flask, NO hardcoded imports - only dynamic manifest-based loading.
        Following Enterprise Roadmap v3: NO HARDCODED IMPORTS.
        """
        system = system_blueprint.system
        
        # Use dynamic loading generator instead of hardcoded approach
        from autocoder_cc.generators.scaffold.main_generator_dynamic import DynamicMainPyGenerator
        
        # Convert ParsedSystemBlueprint to dict format for dynamic generator
        blueprint_dict = {
            'system': {
                'name': system.name,
                'description': system.description,
                'version': system.version,
                'components': [
                    {
                        'name': comp.name,
                        'type': comp.type,
                        'config': comp.config
                    }
                    for comp in system.components
                ],
                'bindings': [
                    {
                        'source': {
                            'component': binding.from_component,
                            'stream': binding.from_port
                        },
                        'target': {
                            'component': binding.to_components[0] if binding.to_components else "",
                            'stream': binding.to_ports[0] if binding.to_ports else ""
                        }
                    }
                    for binding in (filtered_bindings if filtered_bindings is not None else system.bindings)
                ]
            }
        }
        
        # Generate using dynamic loading approach (NO hardcoded imports)
        dynamic_generator = DynamicMainPyGenerator()
        return dynamic_generator.generate(blueprint_dict, enable_metrics)
    
    def _build_fastapi_imports(self, components: List[ParsedComponent], enable_metrics: bool = True) -> str:
        """Build import statements for dynamic component loading FastAPI application."""
        imports = [
            "# Core imports for dynamic component loading",
            "from autocoder_cc.orchestration.harness import SystemExecutionHarness",
            "from autocoder_cc.orchestration.component_manifest import ComponentManifest",
            "from autocoder_cc.generators.config import generator_settings",
            "",
            "# Standard library imports",
            "import yaml",
            "from datetime import datetime",
            "",
            "# CQRS support imports", 
            "# CommandHandler and QueryHandler will be loaded dynamically from manifest",
            "",
            "# Add metrics endpoint if enabled"
        ]
        
        if enable_metrics:
            imports.append("from autocoder_cc.components.metrics_endpoint import MetricsEndpoint")
        
        imports.extend([
            "",
            "# NO HARDCODED COMPONENT IMPORTS - Components loaded dynamically from manifest",
            "# All component classes are discovered and loaded at runtime via importlib"
        ])
        
        return "\n".join(imports)
    
    def _build_fastapi_routes(self, api_components: List[ParsedComponent]) -> str:
        """Build dynamic FastAPI routes that dispatch to loaded components."""
        # Use dynamic routing instead of hardcoded routes per component
        # This follows the dynamic loading principle - NO hardcoded component routes
        
        dynamic_routes = f'''
# Dynamic routing for ALL APIEndpoint components (loaded from manifest)
@app.post("/api/{{component_name}}", response_model=ResponseModel)
async def handle_component_request(component_name: str, request: RequestModel, background_tasks: BackgroundTasks):
    """
    Dynamic POST endpoint for any APIEndpoint component.
    Routes requests to the appropriate component loaded from manifest.
    NO hardcoded component imports - all components loaded dynamically.
    """
    try:
        # Get the component from harness (loaded dynamically via manifest)
        component = harness.get_component(component_name) if harness else None
        if not component:
            raise HTTPException(status_code=404, detail=f"Component '{{component_name}}' not found")
        
        # Send data to component via stream (async communication)
        if hasattr(component, 'send_streams') and 'output' in component.send_streams:
            await component.send_streams['output'].send(request.data)
            result = {{"status": "processed", "component": component_name}}
        elif hasattr(component, 'handle_http_request'):
            result = await component.handle_http_request(request.data)
        else:
            result = {{"status": "accepted", "component": component_name, "data": request.data}}
        
        return ResponseModel(
            status="accepted",
            message=f"Data sent to {{component_name}} component",
            data=result
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dynamic endpoint for {{component_name}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {{str(e)}}")

@app.get("/api/{{component_name}}/status")
async def get_component_status(component_name: str):
    """Get status of any dynamically loaded component."""
    try:
        component = harness.get_component(component_name) if harness else None
        if component:
            return {{
                "status": "active", 
                "component": component_name, 
                "type": getattr(component, 'type', 'unknown'),
                "loaded_dynamically": True
            }}
        else:
            raise HTTPException(status_code=404, detail=f"Component '{{component_name}}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/components")
async def list_components():
    """List all dynamically loaded components."""
    try:
        components = harness.list_components() if harness else {{}}
        return {{
            "components": [
                {{
                    "name": name,
                    "type": getattr(comp, 'type', 'unknown'),
                    "status": "active"
                }}
                for name, comp in components.items()
            ],
            "total": len(components),
            "loaded_dynamically": True,
            "manifest_based": True
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CQRS-specific endpoints for command/query separation
@app.post("/commands/{{command_name}}", response_model=ResponseModel)
async def handle_command(command_name: str, request: RequestModel, background_tasks: BackgroundTasks):
    """
    CQRS Command endpoint - handles write operations.
    Commands modify state and publish events, but don't return data.
    """
    try:
        # Find CommandHandler components
        command_handlers = {{name: comp for name, comp in (harness.list_components() if harness else {{}}).items() 
                           if getattr(comp, 'type', '').lower() == 'commandhandler'}}
        
        if not command_handlers:
            raise HTTPException(status_code=503, detail="No command handlers available")
        
        # Route to appropriate command handler (first available for now)
        handler_name, handler = next(iter(command_handlers.items()))
        
        # Execute command - commands don't return data, they publish events
        command_data = {{
            "command": command_name,
            "data": request.data,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": request.metadata or {{}}
        }}
        
        if hasattr(handler, 'handle_command'):
            await handler.handle_command(command_data)
        elif hasattr(handler, 'send_streams') and 'output' in handler.send_streams:
            await handler.send_streams['output'].send(command_data)
        
        return ResponseModel(
            status="accepted",
            message=f"Command '{{command_name}}' accepted for processing",
            data={{"command": command_name, "timestamp": datetime.utcnow().isoformat()}}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing command {{command_name}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Command processing failed: {{str(e)}}")

@app.get("/queries/{{query_name}}")
async def handle_query(query_name: str, skip: int = 0, limit: int = 100):
    """
    CQRS Query endpoint - handles read operations.
    Queries read from optimized read stores and return data.
    """
    try:
        # Find QueryHandler components
        query_handlers = {{name: comp for name, comp in (harness.list_components() if harness else {{}}).items() 
                         if getattr(comp, 'type', '').lower() == 'queryhandler'}}
        
        if not query_handlers:
            raise HTTPException(status_code=503, detail="No query handlers available")
        
        # Route to appropriate query handler (first available for now)
        handler_name, handler = next(iter(query_handlers.items()))
        
        # Execute query - queries return data from read stores
        query_data = {{
            "query": query_name,
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }}
        
        result = None
        if hasattr(handler, 'handle_query'):
            result = await handler.handle_query(query_data)
        elif hasattr(handler, 'query_read_store'):
            result = await handler.query_read_store(query_data)
        else:
            # Fallback to basic data structure
            result = {{
                "query": query_name,
                "data": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query {{query_name}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {{str(e)}}")

@app.get("/cqrs/status")
async def get_cqrs_status():
    """Get CQRS architecture status and available handlers."""
    try:
        components = harness.list_components() if harness else {{}}
        
        command_handlers = [name for name, comp in components.items() 
                          if getattr(comp, 'type', '').lower() == 'commandhandler']
        query_handlers = [name for name, comp in components.items() 
                        if getattr(comp, 'type', '').lower() == 'queryhandler']
        
        return {{
            "cqrs_enabled": True,
            "architecture": "Command Query Responsibility Segregation",
            "command_handlers": command_handlers,
            "query_handlers": query_handlers,
            "total_command_handlers": len(command_handlers),
            "total_query_handlers": len(query_handlers),
            "separation_enforced": True
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        
        return dynamic_routes
    
    def _build_fastapi_routes_OLD_DEPRECATED(self, api_components: List[ParsedComponent]) -> str:
        """DEPRECATED: Build hardcoded routes - replaced with dynamic routing above"""
        # This old method generated hardcoded routes for each component
        # It violated the dynamic loading principle and is now replaced
        
        routes = []
        
        for comp in api_components:
            comp_name = comp.name
            
            # Build route with proper async handling
            route_code = f'''
# Routes for {comp_name} APIEndpoint
@app.post("/{comp_name}", response_model=ResponseModel)
async def {comp_name}_post(request: RequestModel, background_tasks: BackgroundTasks):
    """
    POST endpoint for {comp_name}.
    Receives data and sends it to the processing pipeline via async streams.
    """
    try:
        if harness:
            # Send data to component via harness
            # Find the APIEndpoint component and call it directly
            component = harness.components.get("{comp_name}")
            if component and hasattr(component, 'handle_http_request'):
                result = await component.handle_http_request(request.data)
            else:
                # Fallback: process via stream if component has streams
                if component and hasattr(component, 'send_streams') and 'output' in component.send_streams:
                    await component.send_streams['output'].send(request.data)
                    result = {{"status": "processed", "data": request.data}}
                else:
                    result = {{"status": "accepted", "data": request.data}}
            
            return ResponseModel(
                status="accepted",
                message=f"Data sent to {comp_name} for processing",
                data=result
            )
        else:
            raise HTTPException(status_code=503, detail="System not ready")
            
    except Exception as e:
        logger.error(f"Error in {comp_name} POST: {{e}}")
        return ResponseModel(
            status="error",
            error=str(e)
        )

@app.get("/{comp_name}/status")
async def {comp_name}_status():
    """Get status of {comp_name} component."""
    try:
        if harness:
            component_status = await harness.get_component_status("{comp_name}")
            return {{
                "component": "{comp_name}",
                "status": component_status.get("status", "unknown"),
                "metrics": component_status.get("metrics", {{}})
            }}
        else:
            return {{"component": "{comp_name}", "status": "system not ready"}}
    except Exception as e:
        logger.error(f"Error getting {comp_name} status: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))'''
            
            routes.append(route_code)
        
        return "\n".join(routes)
    
    # Architecture detection removed - Enterprise Roadmap v2 mandates FastAPI only
    # All systems now use FastAPI with harness for unified async architecture
    
    # All Flask-related methods removed - Enterprise Roadmap v2 forbids Flask
    # Use _generate_fastapi_main() instead
    
    
    def _build_imports(self, components: List[ParsedComponent], system, enable_metrics: bool = True) -> str:
        """Build import statements for all components"""
        
        imports = []
        unique_types = set()
        supported_types = {"Source", "Transformer", "APIEndpoint", "Sink", "Model", "Store", "StreamProcessor", "Controller", "Router", "Accumulator", "CommandHandler", "QueryHandler"}
        
        # NO hardcoded component type imports - dynamic loading will handle this
        # Components are loaded dynamically from manifest.yaml using importlib
        
        # Add configuration import
        imports.append("import yaml")
        
        # NO hardcoded metrics endpoint import - metrics component loaded dynamically if enabled
        
        # NO hardcoded component imports - using dynamic loading instead
        imports.append("\n# Dynamic component loading imports")
        imports.append("# NO hardcoded component imports - components loaded dynamically from manifest.yaml")
        
        return "\n".join(imports)
    
    def _build_component_creation(self, components: List[ParsedComponent], enable_metrics: bool = True) -> str:
        """Build component instantiation code"""
        
        creation_lines = [
            "    # Load components dynamically from manifest using harness",
            "    manifest_path = Path(__file__).parent / 'components' / 'manifest.yaml'",
            "    await harness.load_components_from_manifest(manifest_path)",
            "    ",
            "    # Components are now loaded and registered automatically",
            "    # No need for manual component instantiation",
        ]
        
        # Add metrics endpoint if enabled
        if enable_metrics:
            # Get allocated metrics port from ResourceOrchestrator
            metrics_port = self._get_allocated_metrics_port()
            creation_lines.append(f'    # Production observability endpoint with ResourceOrchestrator-allocated port')
            creation_lines.append(f'    metrics_endpoint = MetricsEndpoint("metrics", {{"port": {metrics_port}}})')
            creation_lines.append(f'    # Set harness reference after creation')
            creation_lines.append(f'    metrics_endpoint.harness = harness')
        
        return "\n".join(creation_lines)
    
    def _get_allocated_metrics_port(self) -> int:
        """Get the allocated metrics port from ResourceOrchestrator"""
        if hasattr(self, 'resource_manifest') and self.resource_manifest:
            for allocation in self.resource_manifest.allocations:
                if (allocation.component_name == "metrics" and 
                    allocation.resource_type == ResourceType.NETWORK_PORT):
                    return allocation.allocated_value
        
        # Fallback if no allocation found (should not happen in normal operation)
        raise RuntimeError("No metrics port allocated by ResourceOrchestrator")
    
    def _build_component_registration(self, components: List[ParsedComponent], enable_metrics: bool = True) -> str:
        """Build component registration with harness"""
        
        registration_lines = [
            "    # Components are automatically registered by dynamic loader",
            "    # No manual registration needed for dynamically loaded components",
        ]
        
        # Register metrics endpoint if enabled (manually created component)
        if enable_metrics:
            registration_lines.append(f'    harness.register_component("metrics", metrics_endpoint)')
        
        return "\n".join(registration_lines)
    
    def _build_connections(self, bindings: List[ParsedBinding]) -> str:
        """Build component connection code - only for components that exist"""
        
        connection_lines = []
        
        for binding in bindings:
            from_spec = f"{binding.from_component}.{binding.from_port}"
            
            # Handle single or multiple targets
            for i, to_comp in enumerate(binding.to_components):
                to_port = binding.to_ports[i] if i < len(binding.to_ports) else binding.to_ports[0]
                to_spec = f"{to_comp}.{to_port}"
                
                connection_lines.append(f'    harness.connect("{from_spec}", "{to_spec}")')
        
        return "\n".join(connection_lines)
    
    def _build_config_loading(self, components: List[ParsedComponent]) -> str:
        """Build configuration loading code"""
        
        config_loading = '''    # Load configuration
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        logger.warning(f"Configuration file not found: {CONFIG_FILE}")'''
        
        return config_loading
    
    def _filter_bindings_for_supported_components(self, system_blueprint: ParsedSystemBlueprint) -> List[ParsedBinding]:
        """Filter bindings to only include connections between supported component types"""
        
        supported_types = {"Source", "Transformer", "Sink", "Model", "Store", "APIEndpoint", "StreamProcessor", "Controller", "Router", "Accumulator"}
        
        # Create a set of component names that will be generated (have supported types)
        generated_component_names = set()
        for comp in system_blueprint.system.components:
            if comp.type in supported_types:
                generated_component_names.add(comp.name)
        
        # Filter bindings to only include those between generated components
        filtered_bindings = []
        for binding in system_blueprint.system.bindings:
            # Check if from_component is supported
            if binding.from_component in generated_component_names:
                # Filter to_components to only include supported ones
                valid_to_components = []
                valid_to_ports = []
                
                for i, to_comp in enumerate(binding.to_components):
                    if to_comp in generated_component_names:
                        valid_to_components.append(to_comp)
                        to_port = binding.to_ports[i] if i < len(binding.to_ports) else binding.to_ports[0]
                        valid_to_ports.append(to_port)
                
                # Only include binding if there are valid target components
                if valid_to_components:
                    filtered_binding = ParsedBinding(
                        from_component=binding.from_component,
                        from_port=binding.from_port,
                        to_components=valid_to_components,
                        to_ports=valid_to_ports,
                        transformation=binding.transformation,
                        condition=binding.condition,
                        error_handling=binding.error_handling,
                        qos=binding.qos
                    )
                    filtered_bindings.append(filtered_binding)
        
        return filtered_bindings
    
    def _generate_config_yaml(self, system_blueprint: ParsedSystemBlueprint, enable_metrics: bool = True) -> str:
        """Generate system configuration YAML with consistent database configuration"""
        
        system = system_blueprint.system
        environment = system.configuration.environment
        
        # Initialize database configuration manager
        db_manager = DatabaseConfigManager(environment=environment)
        
        config = {
            'system': {
                'name': system.name,
                'version': system.version,
                'environment': environment
            }
        }
        
        # Generate system-wide database configuration
        components_data = []
        for comp in system.components:
            components_data.append({
                "name": comp.name,
                "type": comp.type,
                "config": comp.config
            })
        
        system_db_config = db_manager.generate_system_database_config(components_data)
        
        # Add database configuration to system config
        if system_db_config.component_databases:
            config.update(system_db_config.to_system_config())
        
        # Add component configurations with normalized database settings
        for comp in system.components:
            comp_config = comp.config.copy()
            
            # Normalize database configuration for Store components
            if comp.type.lower() in ["store", "database", "repository"]:
                comp_config = db_manager.normalize_component_config(comp_config)
            
            # Add type-specific defaults
            if comp.type == "APIEndpoint":
                # CRITICAL FIX: Only set default port if ResourceOrchestrator hasn't already allocated one
                if 'port' not in comp_config:
                    # Check if port is defined in resources first
                    port_from_resources = generator_settings.default_api_port  # default
                    if hasattr(comp, 'resources') and comp.resources:
                        for resource in comp.resources:
                            if hasattr(resource, 'type') and resource.type == 'ports':
                                if hasattr(resource, 'config') and 'port' in resource.config:
                                    port_from_resources = resource.config['port']
                                    break
                    
                    comp_config['port'] = port_from_resources
                    
                comp_config.setdefault('host', '0.0.0.0')
            elif comp.type == "Controller":
                # CRITICAL FIX: Controllers need to know which store to communicate with
                # Find store components in the system
                store_components = [c for c in system.components if c.type.lower() in ["store", "database", "repository"]]
                if store_components:
                    # Use the first store component as the default store
                    # In a more sophisticated system, this could be based on naming patterns or explicit relationships
                    comp_config['store_name'] = store_components[0].name
                # Also add controller-specific defaults
                comp_config.setdefault('max_retries', 3)
                comp_config.setdefault('timeout', 30)
            elif comp.type == "Source":
                comp_config.setdefault('data_count', 100)
                comp_config.setdefault('data_delay', 0.1)
            elif comp.type == "Transformer":
                comp_config.setdefault('batch_size', 10)
            elif comp.type == "Sink":
                comp_config.setdefault('output_format', 'json')
            
            config[comp.name] = comp_config
        
        # Add top-level API configuration for main uvicorn server
        api_components = [comp for comp in system.components if comp.type == "APIEndpoint"]
        if api_components:
            # Use the first API component's port as the main server port
            # Handle both dict and string configs
            comp_config = api_components[0].config
            if isinstance(comp_config, dict):
                main_port = comp_config.get('port', generator_settings.default_api_port)
            else:
                main_port = generator_settings.default_api_port
        else:
            # Use configuration default if no API components
            main_port = generator_settings.default_api_port
            
        config['api'] = {
            'port': main_port,
            'host': '0.0.0.0',
            'log_level': 'info'
        }
        
        # Add metrics endpoint configuration if enabled
        if enable_metrics:
            # CRITICAL FIX: Use ResourceOrchestrator allocated metrics port
            try:
                metrics_port = self._get_allocated_metrics_port()
                config['metrics'] = {
                    'port': metrics_port,  # Use ResourceOrchestrator allocated port
                    'host': '0.0.0.0',
                    'enabled': True
                }
            except RuntimeError:
                # Fallback to environment variable if allocation fails
                config['metrics'] = {
                    'port': '${METRICS_PORT}',  # Environment variable fallback
                    'host': '0.0.0.0',
                    'enabled': True
                }
        
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    def _generate_requirements_txt(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate requirements.txt file with production dependencies"""
        
        requirements = [
            "pyyaml>=6.0",
            "asyncio-extras>=1.3.0",
            # Always use FastAPI - NO Flask dependencies
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.22.0",
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
            # Async support
            "anyio>=3.7.0",
            "httpx>=0.24.0",
            # Monitoring
            "prometheus-client>=0.17.0",
        ]
        
        # Add type-specific requirements
        for comp in system_blueprint.system.components:
            if comp.type == "Store":
                # V5.2 Enhanced Database Driver Support: Auto-detect database type
                storage_type = self._get_database_type_for_store(comp)
                
                if storage_type == 'postgresql':
                    requirements.extend([
                        "databases>=0.7.0",
                        "asyncpg>=0.28.0",
                        "psycopg2-binary>=2.9.0"
                    ])
                elif storage_type == 'mysql':
                    requirements.extend([
                        "databases>=0.7.0", 
                        "aiomysql>=0.1.0",
                        "mysql-connector-python>=8.0.0"
                    ])
                elif storage_type == 'sqlite':
                    requirements.extend([
                        "databases>=0.7.0",
                        "aiosqlite>=0.17.0"
                    ])
                else:
                    # Default to PostgreSQL if type not specified
                    requirements.extend([
                        "databases>=0.7.0",
                        "asyncpg>=0.28.0",
                        "psycopg2-binary>=2.9.0"
                    ])
            elif comp.type == "Model":
                requirements.extend([
                    "scikit-learn>=1.3.0",
                    "numpy>=1.24.0"
                ])
        
        # Remove duplicates and sort
        unique_reqs = sorted(set(requirements))
        return "\n".join(unique_reqs)
    
    def _generate_dockerfile(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate Dockerfile for containerized deployment"""
        
        system = system_blueprint.system
        
        # Check if system has API endpoints to determine deployment strategy
        api_components = [comp for comp in system.components if comp.type == "APIEndpoint"]
        has_api_endpoints = len(api_components) > 0
        
        dockerfile = f"""# Generated Production Dockerfile for {system.name}
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for production
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create config and logs directories
RUN mkdir -p config logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose ports (if any API endpoints)
"""
        
        # Find API endpoint ports
        api_ports = []
        for comp in api_components:
            # Check resources for port first, then configuration, then default
            port = generator_settings.default_api_port
            if hasattr(comp, 'resources') and comp.resources:
                for resource in comp.resources:
                    if hasattr(resource, 'type') and resource.type == 'ports':
                        if hasattr(resource, 'config') and 'port' in resource.config:
                            port = resource.config['port']
                            break
            else:
                # Handle both dict and string configs
                if isinstance(comp.config, dict):
                    port = comp.config.get('port', generator_settings.default_api_port)
                else:
                    port = generator_settings.default_api_port
            api_ports.append(str(port))
        
        if api_ports:
            dockerfile += f"EXPOSE {' '.join(api_ports)}\n"
        
        # Always use uvicorn for FastAPI applications
        dockerfile += f"""
# Health check for production deployment
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://127.0.0.1:{api_ports[0] if api_ports else generator_settings.default_api_port}/health || exit 1

# Run with uvicorn for production-ready async server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{api_ports[0] if api_ports else generator_settings.default_api_port}"]
"""
        
        return dockerfile
    
    def _get_database_type_for_store(self, component: ParsedComponent) -> str:
        """
        V5.2 Enhanced Database Driver Support: Extract database type from Store component.
        
        Checks multiple configuration locations for database type:
        1. component.database.type (V5.0+ format)
        2. component.config.storage_type (legacy format)
        3. component.config.database_type (alternative format)
        
        Returns:
            str: Database type ('postgresql', 'mysql', 'sqlite', etc.)
        """
        # Check configuration for database info
        config = component.config or {}
        
        # Check V5.0+ database configuration format (stored in _database by parser)
        if '_database' in config and config['_database']:
            database_config = config['_database']
            if isinstance(database_config, dict) and 'type' in database_config:
                return database_config['type'].lower()
        
        # Check storage_type field
        if 'storage_type' in config:
            storage_type = config['storage_type'].lower()
            # Map storage_type values to database types
            if storage_type in ['postgresql', 'postgres']:
                return 'postgresql'
            elif storage_type in ['mysql']:
                return 'mysql'
            elif storage_type in ['sqlite']:
                return 'sqlite'
            return storage_type
        
        # Check database_type field
        if 'database_type' in config:
            return config['database_type'].lower()
        
        # Default to PostgreSQL
        return 'postgresql'
    
    # Flask hybrid methods removed - Enterprise Roadmap v2 forbids Flask

    def _write_files(self, system_name: str, files: Dict[str, str]) -> None:
        """Write generated files to output directory"""
        
        system_dir = self.output_dir / system_name
        system_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in files.items():
            full_path = system_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
    
    def _generate_component_manifest(self, components: List[ParsedComponent], enable_metrics: bool = True) -> str:
        """Generate component manifest YAML for dynamic loading"""
        import yaml
        
        manifest_data = {
            'components': []
        }
        
        supported_types = {"Source", "Transformer", "Sink", "Model", "Store", "APIEndpoint", "StreamProcessor", "Controller", "Router", "Accumulator"}
        
        for comp in components:
            if comp.type in supported_types:
                # Use clean component names instead of Generated{Type}_{name}
                class_name = f"{comp.name.title()}Component"
                
                manifest_data['components'].append({
                    'name': comp.name,
                    'module_path': f'components.{comp.name}',
                    'class_name': class_name,
                    'type': comp.type.lower(),
                    'config': comp.config.__dict__ if hasattr(comp.config, '__dict__') else {},
                    'dependencies': []  # Could be populated from component bindings
                })
        
        # Add metrics endpoint if enabled for dynamic loading
        if enable_metrics:
            manifest_data['components'].append({
                'name': 'metrics',
                'module_path': 'autocoder.components.metrics_endpoint',
                'class_name': 'MetricsEndpoint',
                'type': 'metrics',
                'config': {
                    'port': '${METRICS_PORT}',  # Will be resolved from environment/config
                    'host': '0.0.0.0'
                },
                'dependencies': []
            })
        
        return yaml.dump(manifest_data, default_flow_style=False, sort_keys=True)
    
    def _generate_rbac_config(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate RBAC configuration file for the system."""
        from autocoder_cc.autocoder.security.rbac_generator import RBACConfigGenerator
        
        # Extract component data for resource generation
        components = []
        for comp in system_blueprint.system.components:
            components.append({
                'name': comp.name,
                'type': comp.type,
                'config': comp.config.__dict__ if hasattr(comp.config, '__dict__') else {}
            })
        
        rbac_generator = RBACConfigGenerator()
        return rbac_generator.generate_rbac_config(
            system_name=system_blueprint.system.name,
            components=components
        )
    
    def _generate_security_middleware(self, system_blueprint: ParsedSystemBlueprint) -> str:
        """Generate security middleware for the system."""
        return '''#!/usr/bin/env python3
"""
Generated security middleware for system authentication and authorization.
Provides JWT authentication and RBAC for all API endpoints.
"""
import logging
from typing import Dict, Any, Optional
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import yaml
from pathlib import Path

# Security configuration
security = HTTPBearer()
logger = get_logger(__name__)

# Load RBAC configuration
def load_rbac_config() -> Dict[str, Any]:
    """Load RBAC configuration from rbac.yaml"""
    rbac_file = Path("rbac.yaml")
    if rbac_file.exists():
        with open(rbac_file, 'r') as f:
            return yaml.safe_load(f)
    return {"roles": {}, "permissions": {}}

rbac_config = load_rbac_config()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user information"""
    try:
        import os
        # Get JWT secret from environment - REQUIRED for production
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_SECRET_KEY environment variable not configured"
            )
        
        token = credentials.credentials
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def requires_permission(permission: str):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from function parameters or dependency injection
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user has required permission
            user_role = user.get('role', 'anonymous')
            user_permissions = rbac_config.get('roles', {}).get(user_role, {}).get('permissions', [])
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Utility functions for token generation (for testing/development)
def generate_token(user_data: Dict[str, Any]) -> str:
    """Generate JWT token for user (development/testing only)"""
    import os
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required for token generation")
    return jwt.encode(user_data, jwt_secret, algorithm="HS256")
'''


def main():
    """Test the system scaffold generator"""
    from .system_blueprint_parser import SystemBlueprintParser
    
    # Test with example system
    parser = SystemBlueprintParser()
    generator = SystemScaffoldGenerator(Path("./generated_scaffolds"))
    
    # Create a simple test blueprint
    test_blueprint_yaml = """
system:
  name: test_data_pipeline
  description: Simple data pipeline for testing
  version: 1.0.0
  
  components:
    - name: data_source
      type: Source
      description: Generates test data
      configuration:
        data_count: 50
        data_delay: 0.1
      outputs:
        - name: data
          schema: DataRecord
          
    - name: data_transformer  
      type: Transformer
      description: Transforms incoming data
      configuration:
        multiplier: 2
      inputs:
        - name: input
          schema: DataRecord
      outputs:
        - name: output
          schema: DataRecord
          
    - name: api_endpoint
      type: APIEndpoint
      description: Exposes transformed data via API
      configuration:
        port: {generator_settings.default_api_port}
      inputs:
        - name: input
          schema: DataRecord
      outputs:
        - name: output
          schema: DataRecord
          
    - name: data_sink
      type: Sink  
      description: Collects final results
      configuration:
        output_format: json
      inputs:
        - name: input
          schema: DataRecord
  
  bindings:
    - from: data_source.data
      to: data_transformer.input
    - from: data_transformer.output
      to: data_sink.input

configuration:
  environment: development
  timeouts:
    component_startup: 30
    graceful_shutdown: 10
"""
    
    try:
        # Parse blueprint
        system_blueprint = parser.parse_string(test_blueprint_yaml)
        print(f"✅ Parsed system blueprint: {system_blueprint.system.name}")
        
        # Generate scaffold
        scaffold = generator.generate_system(system_blueprint)
        print(f"✅ Generated system scaffold")
        print(f"   Main.py: {len(scaffold.main_py)} characters")
        print(f"   Config: {len(scaffold.config_yaml)} characters")
        print(f"   Requirements: {len(scaffold.requirements_txt)} characters")
        print(f"   Dockerfile: {len(scaffold.dockerfile)} characters")
        
        # Show generated main.py preview
        print(f"\n📄 Generated main.py preview:")
        lines = scaffold.main_py.split('\n')
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:2d}: {line}")
        if len(lines) > 30:
            print(f"... ({len(lines) - 30} more lines)")
            
    except Exception as e:
        print(f"❌ Failed to generate scaffold: {e}")
    
    # REMOVED: Duplicate _generate_component_manifest method



if __name__ == "__main__":
    main()