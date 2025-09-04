#!/usr/bin/env python3
"""
System Documentation Generator
==============================

Automatically generates comprehensive documentation and visualizations for generated systems:
- Component diagrams (system structure)
- API documentation (Swagger UI)
- Infrastructure diagrams (K8s deployment)
- Sequence diagrams (interaction flows)

This module is integrated into every generated system to provide /docs/* endpoints.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from autocoder_cc.generators.config import generator_settings


@dataclass
class ComponentInfo:
    """Information about a system component"""
    name: str
    type: str  # APIEndpoint, Store, Controller, etc.
    ports: Dict[str, Any]
    config: Dict[str, Any]
    description: str


@dataclass
class APIEndpoint:
    """Information about an API endpoint"""
    path: str
    method: str
    description: str
    parameters: Dict[str, Any]
    responses: Dict[str, Any]


class SystemDocumentationGenerator:
    """
    Generates comprehensive documentation and visualizations for generated systems
    """
    
    def __init__(self, system_dir: Path, system_blueprint: Dict[str, Any] = None):
        """
        Initialize documentation generator
        
        Args:
            system_dir: Path to the generated system directory
            system_blueprint: Optional system blueprint data
        """
        self.system_dir = Path(system_dir)
        self.system_blueprint = system_blueprint or {}
        self.components = []
        self.api_endpoints = []
        
        # Auto-discover system information
        self._discover_system_info()
    
    def _discover_system_info(self):
        """Auto-discover components, APIs, and configuration from generated system"""
        
        # Load system config
        config_file = self.system_dir / "config" / "system_config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                self.system_config = yaml.safe_load(f)
        
        # Discover components
        components_dir = self.system_dir / "components"
        if components_dir.exists():
            for component_file in components_dir.glob("*.py"):
                if component_file.name != "__init__.py":
                    component_info = self._analyze_component(component_file)
                    if component_info:
                        self.components.append(component_info)
        
        # Discover API endpoints
        self._discover_api_endpoints()
    
    def _analyze_component(self, component_file: Path) -> Optional[ComponentInfo]:
        """Analyze a component file to extract information"""
        try:
            content = component_file.read_text()
            
            # Extract component name and type from class definition
            component_name = component_file.stem
            component_type = "Unknown"
            description = ""
            
            # Parse component type from class inheritance
            if "APIEndpoint" in content:
                component_type = "APIEndpoint"
            elif "Store" in content:
                component_type = "Store"  
            elif "Controller" in content:
                component_type = "Controller"
            elif "Transformer" in content:
                component_type = "Transformer"
            elif "Sink" in content:
                component_type = "Sink"
            elif "Source" in content:
                component_type = "Source"
            
            # Extract description from docstring
            if '"""' in content:
                doc_start = content.find('"""') + 3
                doc_end = content.find('"""', doc_start)
                if doc_end > doc_start:
                    description = content[doc_start:doc_end].strip()
            
            # Get component config from system config
            config = self.system_config.get(component_name, {})
            
            return ComponentInfo(
                name=component_name,
                type=component_type,
                ports={},  # Will be populated from blueprint if available
                config=config,
                description=description
            )
            
        except Exception as e:
            print(f"Warning: Could not analyze component {component_file}: {e}")
            return None
    
    def _discover_api_endpoints(self):
        """Discover API endpoints from components and main.py"""
        
        # Look for FastAPI routes in main.py
        main_file = self.system_dir / "main.py"
        if main_file.exists():
            try:
                content = main_file.read_text()
                self._extract_fastapi_routes(content)
            except Exception as e:
                print(f"Warning: Could not analyze main.py: {e}")
        
        # Look for blueprint routes in APIEndpoint components
        for component in self.components:
            if component.type == "APIEndpoint":
                component_file = self.system_dir / "components" / f"{component.name}.py"
                if component_file.exists():
                    try:
                        content = component_file.read_text()
                        self._extract_blueprint_routes(content, component.name)
                    except Exception as e:
                        print(f"Warning: Could not analyze {component.name}: {e}")
    
    def _extract_fastapi_routes(self, content: str):
        """Extract FastAPI routes from main.py content"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for FastAPI route decorators
            fastapi_methods = ["@app.get(", "@app.post(", "@app.put(", "@app.delete(", "@app.patch("]
            
            for method_decorator in fastapi_methods:
                if method_decorator in line:
                    # Extract route info
                    route_info = self._parse_fastapi_decorator(line, method_decorator)
                    if route_info:
                        # Look for function definition on next line
                        if i + 1 < len(lines):
                            func_line = lines[i + 1]
                            if "def " in func_line:
                                func_name = func_line.split("def ")[1].split("(")[0]
                                
                                # Extract docstring
                                description = self._extract_function_docstring(lines, i + 1)
                                
                                endpoint = APIEndpoint(
                                    path=route_info['path'],
                                    method=route_info['method'],
                                    description=description or f"{func_name} endpoint",
                                    parameters={},
                                    responses={"200": {"description": "Success"}}
                                )
                                self.api_endpoints.append(endpoint)
                    break
    
    def _extract_blueprint_routes(self, content: str, component_name: str):
        """Extract blueprint routes from component content"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if any(method in line for method in ["@self.router.get(", "@self.router.post(", "@self.router.put(", "@self.router.delete(", "@self.router.patch("]):
                # Extract route info
                route_info = self._parse_route_decorator(line)
                if route_info:
                    # Look for function definition
                    if i + 1 < len(lines):
                        func_line = lines[i + 1]
                        if "def " in func_line:
                            func_name = func_line.split("def ")[1].split("(")[0]
                            
                            # Extract docstring
                            description = self._extract_function_docstring(lines, i + 1)
                            
                            # Add component prefix to path
                            path = f"/{component_name}{route_info['path']}"
                            
                            endpoint = APIEndpoint(
                                path=path,
                                method=route_info['method'],
                                description=description or f"{func_name} endpoint",
                                parameters={},
                                responses={"200": {"description": "Success"}}
                            )
                            self.api_endpoints.append(endpoint)
    
    def _parse_fastapi_decorator(self, line: str, method_decorator: str) -> Optional[Dict[str, str]]:
        """Parse FastAPI route decorator to extract path and methods"""
        try:
            # Extract method from decorator
            method = method_decorator.replace("@app.", "").replace("(", "").upper()
            
            # Extract path
            if "'" in line:
                path = line.split("'")[1]
            elif '"' in line:
                path = line.split('"')[1]
            else:
                return None
            
            return {"path": path, "method": method}
        except Exception:
            return None
    
    def _parse_route_decorator(self, line: str) -> Optional[Dict[str, str]]:
        """Parse Flask route decorator to extract path and methods (legacy)"""
        try:
            # Extract path
            if "'" in line:
                path = line.split("'")[1]
            elif '"' in line:
                path = line.split('"')[1]
            else:
                return None
            
            # Extract methods
            method = "GET"  # default
            if "methods=" in line:
                methods_part = line.split("methods=")[1]
                if "[" in methods_part and "]" in methods_part:
                    methods_str = methods_part.split("[")[1].split("]")[0]
                    if "'" in methods_str:
                        method = methods_str.split("'")[1]
                    elif '"' in methods_str:
                        method = methods_str.split('"')[1]
            
            return {"path": path, "method": method}
            
        except Exception:
            return None
    
    def _extract_function_docstring(self, lines: List[str], func_line_idx: int) -> Optional[str]:
        """Extract docstring from function definition"""
        try:
            # Look for docstring in next few lines
            for i in range(func_line_idx + 1, min(func_line_idx + 5, len(lines))):
                line = lines[i].strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # Single line docstring
                    if line.count('"""') == 2 or line.count("'''") == 2:
                        return line.strip('"""').strip("'''").strip()
                    # Multi-line docstring start
                    else:
                        quote = '"""' if '"""' in line else "'''"
                        docstring = line.replace(quote, "")
                        # Find end of docstring
                        for j in range(i + 1, min(i + 10, len(lines))):
                            if quote in lines[j]:
                                docstring += " " + lines[j].replace(quote, "")
                                return docstring.strip()
                            else:
                                docstring += " " + lines[j].strip()
                        return docstring.strip()
            return None
        except Exception:
            return None
    
    def generate_component_diagram(self) -> str:
        """Generate interactive component diagram using vis.js"""
        
        # Create nodes for each component
        nodes = []
        edges = []
        
        for i, component in enumerate(self.components):
            color = {
                "APIEndpoint": "#4CAF50",  # Green
                "Store": "#FF9800",        # Orange  
                "Controller": "#2196F3",   # Blue
                "Transformer": "#9C27B0",  # Purple
                "Sink": "#F44336",         # Red
                "Source": "#00BCD4"        # Cyan
            }.get(component.type, "#757575")  # Grey default
            
            nodes.append({
                "id": component.name,
                "label": f"{component.name}\\n({component.type})",
                "color": color,
                "shape": "box",
                "font": {"size": 14},
                "margin": 10
            })
        
        # Create edges from blueprint bindings if available
        if self.system_blueprint and "bindings" in self.system_blueprint:
            for binding in self.system_blueprint["bindings"]:
                source = binding.get("source", {}).get("component")
                target = binding.get("target", {}).get("component")
                if source and target:
                    edges.append({
                        "from": source,
                        "to": target,
                        "arrows": "to",
                        "label": binding.get("source", {}).get("port", "data"),
                        "font": {"size": 12}
                    })
        
        # Generate HTML with vis.js
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Component Diagram</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        #network {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
        .info {{ margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="info">
        <h1>System Component Architecture</h1>
        <p><strong>System:</strong> {self.system_dir.name}</p>
        <p><strong>Components:</strong> {len(self.components)}</p>
        <p><strong>Types:</strong> {', '.join(set(c.type for c in self.components))}</p>
    </div>
    
    <div id="network"></div>
    
    <script>
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            layout: {{
                hierarchical: {{
                    direction: 'LR',
                    sortMethod: 'directed'
                }}
            }},
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200
            }}
        }};
        
        var network = new vis.Network(container, data, options);
        
        // Add click handler for component details
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var component = {json.dumps({c.name: {"type": c.type, "description": c.description, "config": c.config} for c in self.components})}[nodeId];
                alert("Component: " + nodeId + "\\nType: " + component.type + "\\nDescription: " + component.description);
            }}
        }});
    </script>
</body>
</html>
"""
        return html
    
    def generate_api_documentation(self) -> str:
        """Generate Swagger UI documentation for API endpoints"""
        
        # Create OpenAPI specification
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{self.system_dir.name} API",
                "description": f"Auto-generated API documentation for {self.system_dir.name}",
                "version": "1.0.0"
            },
            "servers": [
                {"url": f"{generator_settings.api_base_url}:{generator_settings.default_api_port}", "description": "Local development server"}
            ],
            "paths": {}
        }
        
        # Add endpoints to spec
        for endpoint in self.api_endpoints:
            if endpoint.path not in openapi_spec["paths"]:
                openapi_spec["paths"][endpoint.path] = {}
            
            openapi_spec["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.description,
                "description": endpoint.description,
                "responses": endpoint.responses
            }
            
            # Add parameters if this looks like a parameterized endpoint
            if "{" in endpoint.path and "}" in endpoint.path:
                param_name = endpoint.path.split("{")[1].split("}")[0]
                openapi_spec["paths"][endpoint.path][endpoint.method.lower()]["parameters"] = [
                    {
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": f"{param_name} identifier"
                    }
                ]
        
        # Generate Swagger UI HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - {self.system_dir.name}</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    <style>
        body {{ margin: 0; }}
        .info {{ padding: 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="info">
        <h1>API Documentation: {self.system_dir.name}</h1>
        <p>Auto-generated interactive API documentation. You can test all endpoints directly from this page.</p>
        <p><strong>Base URL:</strong> {generator_settings.api_base_url}:{generator_settings.default_api_port}</p>
        <p><strong>Endpoints:</strong> {len(self.api_endpoints)}</p>
    </div>
    
    <div id="swagger-ui"></div>
    
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
    <script>
        const ui = SwaggerUIBundle({{
            url: '#',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            spec: {json.dumps(openapi_spec, indent=2)}
        }});
    </script>
</body>
</html>
"""
        return html
    
    def generate_infrastructure_diagram(self) -> str:
        """Generate infrastructure diagram from K8s manifests"""
        
        # Discover K8s resources
        k8s_resources = []
        k8s_dir = self.system_dir / "k8s"
        
        if k8s_dir.exists():
            for manifest_file in k8s_dir.glob("*.yaml"):
                try:
                    with open(manifest_file) as f:
                        docs = yaml.safe_load_all(f)
                        for doc in docs:
                            if doc and "kind" in doc:
                                k8s_resources.append({
                                    "kind": doc["kind"],
                                    "name": doc.get("metadata", {}).get("name", "unknown"),
                                    "file": manifest_file.name
                                })
                except Exception as e:
                    print(f"Warning: Could not parse {manifest_file}: {e}")
        
        # Create infrastructure diagram
        nodes = []
        edges = []
        
        # Group resources by type
        resource_groups = {}
        for resource in k8s_resources:
            kind = resource["kind"]
            if kind not in resource_groups:
                resource_groups[kind] = []
            resource_groups[kind].append(resource)
        
        # Create nodes for each resource type
        colors = {
            "Namespace": "#E3F2FD",
            "Deployment": "#4CAF50", 
            "Service": "#2196F3",
            "Ingress": "#FF9800",
            "ConfigMap": "#9C27B0",
            "Secret": "#F44336",
            "PersistentVolume": "#795548"
        }
        
        y_offset = 0
        for kind, resources in resource_groups.items():
            for i, resource in enumerate(resources):
                nodes.append({
                    "id": f"{kind}_{resource['name']}",
                    "label": f"{resource['name']}\\n({kind})",
                    "color": colors.get(kind, "#757575"),
                    "shape": "box",
                    "x": i * 200,
                    "y": y_offset,
                    "font": {"size": 12}
                })
            y_offset += 100
        
        # Add logical connections
        deployment_nodes = [n for n in nodes if "Deployment_" in n["id"]]
        service_nodes = [n for n in nodes if "Service_" in n["id"]]
        ingress_nodes = [n for n in nodes if "Ingress_" in n["id"]]
        
        # Connect Ingress -> Service -> Deployment
        for ingress in ingress_nodes:
            for service in service_nodes:
                edges.append({
                    "from": ingress["id"],
                    "to": service["id"],
                    "arrows": "to",
                    "label": "routes"
                })
        
        for service in service_nodes:
            for deployment in deployment_nodes:
                edges.append({
                    "from": service["id"], 
                    "to": deployment["id"],
                    "arrows": "to",
                    "label": "targets"
                })
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Infrastructure Diagram</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        #network {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
        .info {{ margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        .resources {{ margin-top: 20px; }}
        .resource-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .resource-item {{ padding: 5px 10px; background: #e0e0e0; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="info">
        <h1>Infrastructure Architecture</h1>
        <p><strong>System:</strong> {self.system_dir.name}</p>
        <p><strong>Kubernetes Resources:</strong> {len(k8s_resources)}</p>
    </div>
    
    <div id="network"></div>
    
    <div class="resources">
        <h3>Generated Kubernetes Resources:</h3>
        <div class="resource-list">
            {''.join(f'<div class="resource-item">{r["kind"]}: {r["name"]}</div>' for r in k8s_resources)}
        </div>
    </div>
    
    <script>
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true
            }}
        }};
        
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
"""
        return html
    
    def generate_documentation_index(self) -> str:
        """Generate main documentation index page"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Documentation - {self.system_dir.name}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f8f9fa; 
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
        }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ 
            background: white; 
            border-radius: 10px; 
            padding: 25px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            transition: transform 0.2s; 
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .card h3 {{ 
            margin-top: 0; 
            color: #333; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
        }}
        .card p {{ color: #666; line-height: 1.6; }}
        .card a {{ 
            display: inline-block; 
            background: #667eea; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin-top: 15px; 
        }}
        .card a:hover {{ background: #5a6fd8; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
            margin-top: 20px; 
        }}
        .stat {{ text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; }}
        .stat-number {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 System Documentation</h1>
            <h2>{self.system_dir.name}</h2>
            <p>Auto-generated comprehensive documentation and visualizations</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{len(self.components)}</div>
                    <div class="stat-label">Components</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(self.api_endpoints)}</div>
                    <div class="stat-label">API Endpoints</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(list((self.system_dir / "k8s").glob("*.yaml")) if (self.system_dir / "k8s").exists() else [])}</div>
                    <div class="stat-label">K8s Resources</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(list((self.system_dir / "tests").glob("test_*.py")) if (self.system_dir / "tests").exists() else [])}</div>
                    <div class="stat-label">Test Files</div>
                </div>
            </div>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>🏗️ Component Architecture</h3>
                <p>Interactive diagram showing system components, their types, and relationships. 
                   Visualizes the complete system structure with data flow connections.</p>
                <a href="/docs/architecture">View Component Diagram</a>
            </div>
            
            <div class="card">
                <h3>📖 API Documentation</h3>
                <p>Interactive Swagger UI documentation for all API endpoints. 
                   Test endpoints directly from the browser with full request/response examples.</p>
                <a href="/docs/api">View API Docs</a>
            </div>
            
            <div class="card">
                <h3>☁️ Infrastructure</h3>
                <p>Kubernetes deployment architecture showing all generated resources, 
                   services, and deployment configurations.</p>
                <a href="/docs/infrastructure">View Infrastructure</a>
            </div>
            
            <div class="card">
                <h3>⚡ System Health</h3>
                <p>Real-time system health monitoring with component status, 
                   performance metrics, and operational insights.</p>
                <a href="/health">View Health Status</a>
            </div>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <p>Generated by Autocoder V5.2 • Natural Language to Complete System Pipeline</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def generate_all_documentation(self) -> Dict[str, str]:
        """Generate all documentation pages"""
        return {
            "index": self.generate_documentation_index(),
            "architecture": self.generate_component_diagram(),
            "api": self.generate_api_documentation(), 
            "infrastructure": self.generate_infrastructure_diagram()
        }


def add_documentation_routes(app, system_dir: Path, system_blueprint: Dict[str, Any] = None):
    """
    Add documentation routes to a FastAPI app
    
    This function should be called from the generated system's main.py to add /docs/* routes
    """
    from fastapi import Response
    
    doc_generator = SystemDocumentationGenerator(system_dir, system_blueprint)
    docs = doc_generator.generate_all_documentation()
    
    @app.get('/docs')
    @app.get('/docs/')
    async def docs_index():
        return Response(docs["index"], media_type='text/html')
    
    @app.get('/docs/architecture')
    async def docs_architecture():
        return Response(docs["architecture"], media_type='text/html')
    
    @app.get('/docs/api') 
    async def docs_api():
        return Response(docs["api"], media_type='text/html')
    
    @app.get('/docs/infrastructure')
    async def docs_infrastructure():
        return Response(docs["infrastructure"], media_type='text/html')
    
    return doc_generator