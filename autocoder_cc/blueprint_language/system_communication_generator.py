#!/usr/bin/env python3
"""
System Communication Generator - Extracted from SystemGenerator
Handles messaging, service communication, and runtime connectivity configuration
"""
from typing import Dict, Any, List
from pathlib import Path
import yaml

class TransparentMessagingAnalyzer:
    """Analyzes system requirements to recommend optimal messaging patterns"""
    
    def __init__(self):
        pass
    
    def analyze_requirements(self, system_blueprint) -> Dict[str, Any]:
        """Analyze system to determine messaging requirements"""
        return {
            "messaging_type": "direct",
            "volume": "low",
            "latency": "standard",
            "durability": False,
            "ordering": False
        }


class SystemCommunicationGenerator:
    """
    Generates communication configuration for system components
    Extracted from SystemGenerator to reduce monolith size
    """
    
    def __init__(self):
        self.messaging_analyzer = self._create_messaging_requirements_analyzer()
    
    def generate_service_communication_config(self, system_blueprint) -> str:
        """
        Generate comprehensive service communication configuration
        
        Args:
            system_blueprint: Parsed system blueprint
            
        Returns:
            YAML configuration string for service communication
        """
        # Determine optimal messaging type
        messaging_type = self._determine_messaging_type(system_blueprint)
        
        # Generate comprehensive configuration
        config = {
            "messaging": {
                "type": messaging_type,
                "connection": self._generate_connection_config(messaging_type),
                "queues": self._generate_queue_config(system_blueprint),
                "services": self._generate_service_config(system_blueprint.system.components)
            },
            "service_discovery": {
                "type": "static",  # For generated systems
                "endpoints": self._generate_service_endpoints(system_blueprint)
            },
            "health_checks": {
                "interval": 30,
                "timeout": 5,
                "retries": 3
            }
        }
        
        return yaml.dump(config, default_flow_style=False, indent=2)
    
    def _determine_messaging_type(self, system_blueprint) -> str:
        """Determine optimal messaging type based on system characteristics"""
        components = system_blueprint.system.components
        num_components = len(components)
        
        # Simple heuristics for messaging type selection
        if num_components <= 3:
            return "direct"  # Direct HTTP calls for simple systems
        elif num_components <= 10:
            return "event_driven"  # Event-driven for medium complexity
        else:
            return "message_queue"  # Full message queue for complex systems
    
    def _create_messaging_requirements_analyzer(self) -> TransparentMessagingAnalyzer:
        """Create messaging requirements analyzer"""
        return TransparentMessagingAnalyzer()
    
    def _estimate_message_volume_by_type(self, component_type: str) -> int:
        """Estimate message volume based on component type"""
        volume_map = {
            "Source": 1000,      # High volume data generation
            "APIEndpoint": 500,  # Medium volume API requests
            "Controller": 300,   # Medium volume business logic
            "Transformer": 800,  # High volume data processing
            "Store": 200,        # Lower volume persistence
            "Sink": 100,         # Low volume final output
            "Model": 150         # Low-medium volume ML inference
        }
        return volume_map.get(component_type, 100)
    
    def _estimate_message_size_by_type(self, component_type: str) -> int:
        """Estimate average message size in bytes"""
        size_map = {
            "Source": 1024,      # 1KB data objects
            "APIEndpoint": 2048, # 2KB API payloads
            "Controller": 512,   # 512B control messages
            "Transformer": 1024, # 1KB processed data
            "Store": 256,        # 256B persistence confirmations
            "Sink": 128,         # 128B output confirmations
            "Model": 4096        # 4KB ML model outputs
        }
        return size_map.get(component_type, 512)
    
    def _estimate_latency_requirement_by_type(self, component_type: str) -> float:
        """Estimate latency requirement in seconds"""
        latency_map = {
            "Source": 1.0,       # 1s for data generation
            "APIEndpoint": 0.1,  # 100ms for API responses
            "Controller": 0.2,   # 200ms for business logic
            "Transformer": 0.5,  # 500ms for data processing
            "Store": 0.3,        # 300ms for persistence
            "Sink": 2.0,         # 2s for final output
            "Model": 1.0         # 1s for ML inference
        }
        return latency_map.get(component_type, 0.5)
    
    def _analyze_durability_requirements(self, system_blueprint) -> bool:
        """Analyze if system requires durable messaging"""
        # Check for Store components - they usually require durability
        for component in system_blueprint.system.components:
            if component.type == "Store":
                return True
        return False
    
    def _analyze_ordering_requirements(self, system_blueprint) -> bool:
        """Analyze if system requires ordered message processing"""
        # Check for sequential processing patterns
        for binding in system_blueprint.system.bindings:
            # If multiple components send to the same target, ordering may be important
            if len(binding.to_components) > 1:
                return True
        return False
    
    def _analyze_network_conditions(self, system_blueprint) -> str:
        """Analyze expected network conditions"""
        # For generated systems, assume reliable local network
        num_components = len(system_blueprint.system.components)
        if num_components > 10:
            return "variable"  # Larger systems may have network variability
        else:
            return "reliable"  # Smaller systems typically run locally
    
    def _analyze_component_coupling(self, system_blueprint) -> str:
        """Analyze coupling level between components"""
        num_bindings = len(system_blueprint.system.bindings)
        num_components = len(system_blueprint.system.components)
        
        if num_components == 0:
            return "loose"
        
        coupling_ratio = num_bindings / num_components
        
        if coupling_ratio > 2.0:
            return "tight"
        elif coupling_ratio > 1.0:
            return "medium"
        else:
            return "loose"
    
    def _analyze_failure_tolerance(self, system_blueprint) -> str:
        """Analyze failure tolerance requirements"""
        # Check for critical components
        for component in system_blueprint.system.components:
            if component.type in ["APIEndpoint", "Store"]:
                return "high"  # API and data components need high availability
        return "standard"
    
    def _generate_connection_config(self, messaging_type: str) -> Dict[str, Any]:
        """Generate connection configuration for messaging type"""
        configs = {
            "direct": {
                "protocol": "http",
                "timeout": 30,
                "retries": 3,
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_timeout": 60
                }
            },
            "event_driven": {
                "protocol": "websocket",
                "keepalive": 30,
                "reconnect_interval": 5,
                "max_reconnects": 10
            },
            "message_queue": {
                "protocol": "amqp",
                "host": "localhost",
                "port": 5672,
                "virtual_host": "/",
                "connection_timeout": 30
            }
        }
        return configs.get(messaging_type, configs["direct"])
    
    def _generate_queue_config(self, system_blueprint) -> Dict[str, Any]:
        """Generate queue configuration based on system components"""
        queues = {}
        
        for component in system_blueprint.system.components:
            queue_name = f"{component.name}_input"
            queues[queue_name] = {
                "durable": self._analyze_durability_requirements(system_blueprint),
                "auto_delete": False,
                "max_length": self._estimate_message_volume_by_type(component.type),
                "message_ttl": 3600000,  # 1 hour TTL
                "priority": self._get_component_priority(component.type)
            }
        
        return queues
    
    def _generate_service_config(self, components) -> Dict[str, Any]:
        """Generate service-specific configuration"""
        services = {}
        
        for component in components:
            services[component.name] = {
                "type": component.type,
                "scaling": {
                    "min_instances": 1,
                    "max_instances": self._get_max_instances(component.type),
                    "cpu_threshold": 70,
                    "memory_threshold": 80
                },
                "resources": {
                    "cpu_request": "100m",
                    "memory_request": "128Mi",
                    "cpu_limit": "500m",
                    "memory_limit": "512Mi"
                },
                "health_check": {
                    "path": "/health",
                    "port": component.config.get("port", 8080),
                    "initial_delay": 10,
                    "period": 30
                }
            }
        
        return services
    
    def _generate_service_endpoints(self, system_blueprint) -> Dict[str, str]:
        """Generate service endpoint mappings"""
        endpoints = {}
        
        for component in system_blueprint.system.components:
            port = component.config.get("port", 8080)
            endpoints[component.name] = f"http://localhost:{port}"
        
        return endpoints
    
    def _get_component_priority(self, component_type: str) -> int:
        """Get message priority for component type"""
        priority_map = {
            "APIEndpoint": 10,  # Highest priority for user-facing APIs
            "Controller": 8,    # High priority for business logic
            "Model": 6,         # Medium-high priority for ML processing
            "Transformer": 5,   # Medium priority for data processing
            "Store": 4,         # Medium-low priority for persistence
            "Source": 3,        # Low-medium priority for data generation
            "Sink": 1           # Lowest priority for final output
        }
        return priority_map.get(component_type, 5)
    
    def _get_max_instances(self, component_type: str) -> int:
        """Get maximum instances for component type"""
        instance_map = {
            "APIEndpoint": 5,   # Scale API endpoints for load
            "Controller": 3,    # Scale business logic moderately
            "Transformer": 4,   # Scale data processing
            "Model": 2,         # Limit ML model instances (resource intensive)
            "Store": 1,         # Typically don't scale storage components
            "Source": 1,        # Usually one data source
            "Sink": 1           # Usually one output destination
        }
        return instance_map.get(component_type, 2)
    
    def generate_service_containers(self, system_blueprint) -> Dict[str, str]:
        """Generate Docker container configurations for services"""
        containers = {}
        
        for component in system_blueprint.system.components:
            dockerfile_content = self._generate_service_dockerfile(component, system_blueprint)
            containers[f"{component.name}_dockerfile"] = dockerfile_content
            
            compose_definition = self._generate_service_compose_definition(component, system_blueprint)
            containers[f"{component.name}_compose"] = compose_definition
        
        return containers
    
    def _generate_service_dockerfile(self, component, system_blueprint) -> str:
        """Generate Dockerfile for a specific service component"""
        return f"""# Generated Dockerfile for {component.name}
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy component code
COPY components/{component.name}.py components/
COPY components/observability.py components/
COPY components/communication.py components/
COPY config/ config/

# Set environment variables
ENV COMPONENT_NAME={component.name}
ENV COMPONENT_TYPE={component.type}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:{component.config.get('port', 8080)}/health')"

# Run component
CMD ["python", "-m", "components.{component.name}"]
"""
    
    def _generate_service_compose_definition(self, component, system_blueprint) -> str:
        """Generate docker-compose service definition"""
        port = component.config.get("port", 8080)
        
        return f"""  {component.name}:
    build: .
    dockerfile: Dockerfile.{component.name}
    ports:
      - "{port}:{port}"
    environment:
      - COMPONENT_NAME={component.name}
      - COMPONENT_TYPE={component.type}
      - PORT={port}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - {system_blueprint.system.name}_network
"""