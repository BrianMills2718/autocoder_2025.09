"""
Core Prompt Engine - UPDATED TO USE CENTRALIZED PROMPTS

This module has been updated to use the centralized prompts system to address
Root Cause #1 (contradictory instructions) and Root Cause #7 (missing project imports).

Key Changes:
- Uses PromptLoader for centralized template management
- Eliminates contradictory f-string instructions
- Consistent prompt composition from external templates
- Maintains backward compatibility with existing interface

Legacy Features (now centralized):
- System prompt generation with embedded base classes
- Component-specific prompt templates  
- Docker networking configuration prompts
- Standalone component pattern enforcement
"""

import json
from typing import Dict, Any, Optional
from ..prompt_loader import get_prompt_loader


class PromptEngine:
    """
    Core prompt generation engine for LLM component generation - UPDATED
    
    Now uses centralized prompt templates to eliminate contradictory instructions
    and provide consistent, maintainable prompt composition.
    
    Key improvements:
    - Centralized template management via PromptLoader
    - Elimination of contradictory f-string instructions
    - Project-specific import mappings for self-healing
    - Template composition with validation
    """
    
    def __init__(self):
        self.prompt_loader = get_prompt_loader()
        
        # Validate prompt consistency on initialization
        validation_issues = self.prompt_loader.validate_prompts()
        if validation_issues:
            print(f"⚠️  Prompt validation issues found: {validation_issues}")
        else:
            print("✅ Centralized prompts loaded successfully - no contradictions found")
    
    def _get_shared_module_info(self) -> str:
        """Get information about shared modules available to components"""
        return '''
SHARED MODULES AVAILABLE (automatically imported by system):

1. observability.py - Contains all observability infrastructure:
   - ComposedComponent: Base class with metrics, tracing, health checks
   - StandaloneMetricsCollector: Metrics collection (counter, gauge, histogram)
   - StandaloneTracer: Distributed tracing support
   - StandaloneSpan: Span implementation for tracing
   - ComponentStatus: Component state tracking
   - get_logger(): Configured logger function

2. communication.py - Contains inter-component communication:
   - ComponentCommunicator: Message routing between components
   - ComponentRegistry: Component discovery and lookup
   - Real data flow implementation (no simulation)

USAGE IN YOUR COMPONENT:
- Your component automatically inherits from ComposedComponent
- Use self.logger for logging
- Use self.metrics_collector for metrics (increment, gauge, histogram)
- Use self.tracer for distributed tracing
- Use self.handle_error() for error management
- Use self.send_to_component() for inter-component communication
- Use self.query_component() for querying other components
'''
    
    def get_system_prompt(self, component_type: str, reasoning_prefix: str = "") -> str:
        """
        Get system prompt for component generation using centralized templates
        
        Args:
            component_type: Type of component to generate
            reasoning_prefix: Optional reasoning prefix for specialized models
            
        Returns:
            System prompt for component-only generation (from centralized templates)
        """
        try:
            # Use centralized prompt loader to compose system prompt
            return self.prompt_loader.load_component_system_prompt(
                component_type=component_type,
                reasoning_prefix=reasoning_prefix
            )
        except Exception as e:
            # Fallback to prevent system failure if prompts are not yet migrated
            print(f"⚠️  Centralized prompt loading failed: {e}")
            print("🔄 Using fallback system prompt")
            return f"""{reasoning_prefix}You are an expert Python developer generating ONLY component class implementations.

CRITICAL INSTRUCTION - YOU MUST FOLLOW THIS EXACTLY:
Generate ONLY the component class. The system will automatically add all imports and base classes from shared modules.

Component Type: {component_type}

Generate ONLY the class. Start directly with "class Generated{component_type}_..."."""
    
    def _inject_blueprint_context(self, component_name: str, blueprint: Dict[str, Any] = None) -> str:
        """Extract and format component connections from blueprint"""
        if not blueprint or 'bindings' not in blueprint:
            return "No blueprint context available - component operates independently."
        
        connections = []
        inputs = []
        outputs = []
        
        # Find connections where this component receives data
        for binding in blueprint.get('bindings', []):
            if component_name in binding.get('to_components', []):
                source = binding.get('from_component')
                source_port = binding.get('from_port', 'output')
                connections.append(f"Receives data from: {source} (via {source_port} port)")
                inputs.append(source)
        
        # Find connections where this component sends data
        for binding in blueprint.get('bindings', []):
            if binding.get('from_component') == component_name:
                targets = binding.get('to_components', [])
                target_ports = binding.get('to_ports', ['input'])
                for target, port in zip(targets, target_ports):
                    connections.append(f"Sends data to: {target} (via {port} port)")
                    outputs.append(target)
        
        if not connections:
            return f"Component '{component_name}' has no explicit data flow connections in blueprint."
        
        context = f"""
BLUEPRINT CONNECTION CONTEXT for {component_name}:
{chr(10).join(f"- {conn}" for conn in connections)}

Data Flow Summary:
- Input sources: {inputs if inputs else ['None - this is a source component']}
- Output targets: {outputs if outputs else ['None - this is a sink component']}

IMPLEMENTATION REQUIREMENTS:
- Your component MUST handle data flow as specified above
- Input data will arrive via process_item(item) method parameter
- Output data should be returned from process_item() method
- Design your interfaces to match the expected data flow patterns
"""
        return context
    
    def build_component_prompt(
        self, 
        component_type: str,
        component_name: str,
        component_description: str,
        component_config: Dict[str, Any],
        class_name: str,
        blueprint: Dict[str, Any] = None,
        allocated_port: Optional[int] = None
    ) -> str:
        """
        Build component-specific prompt with strict type enforcement
        
        Args:
            component_type: Type of component (Source, Sink, etc.)
            component_name: Name of the specific component
            component_description: Description of component functionality
            component_config: Configuration for the component
            class_name: Generated class name
            
        Returns:
            Component-specific prompt string
        """
        
        # Handle special cases for Store, Sink, and Controller components
        if component_type == "Store":
            return self._build_store_prompt(component_name, component_description, component_config, class_name, blueprint)
        elif component_type == "Sink":
            return self._build_sink_prompt(component_name, component_description, component_config, class_name, blueprint)
        elif component_type == "Controller":
            return self._build_controller_prompt(component_name, component_description, component_config, class_name, blueprint)
        
        # Inject blueprint connection context
        blueprint_context = self._inject_blueprint_context(component_name, blueprint)
        
        # Prepare enhanced configuration with allocated port
        enhanced_config = component_config.copy() if component_config else {}
        if allocated_port:
            enhanced_config['port'] = allocated_port
            
        # Build port instruction based on allocated port
        port_instruction = ""
        if allocated_port:
            port_instruction = f"\n- CRITICAL: Use allocated port {allocated_port} from configuration, NOT hardcoded values"
        
        # Use centralized prompt templates for component requirements
        try:
            base_requirements = self.prompt_loader.load_component_requirements(component_type)
            
            # Compose main prompt with centralized templates and component details
            prompt = f"""Generate a complete STANDALONE {component_type} component implementation.

{blueprint_context}

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description or f'A {component_type} component for data processing'}
- Configuration: {json.dumps(enhanced_config, indent=2) if enhanced_config else 'Default configuration'}{port_instruction}

{base_requirements}

FINAL REMINDER - YOUR OUTPUT MUST:
1. Start with: class Generated{component_type}_{component_name}(ComposedComponent):
2. Contain ONLY the class and its methods
3. NO imports, NO base classes, NO comments before the class
4. NO markdown, NO explanations, NO ```python blocks

Generate ONLY the component class now:
"""
        except Exception as e:
            print(f"⚠️  Failed to load centralized component requirements: {e}")
            print("🔄 Using legacy component requirements")
            
            # Fallback to legacy method
            prompt = f"""Generate a complete STANDALONE {component_type} component implementation.

{blueprint_context}

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description or f'A {component_type} component for data processing'}
- Configuration: {json.dumps(enhanced_config, indent=2) if enhanced_config else 'Default configuration'}{port_instruction}

CRITICAL REQUIREMENTS:
1. Generate ONLY the component class - no imports or base classes
2. Class must inherit from ComposedComponent
3. Implement ALL required methods with REAL logic (no placeholders)

Generate ONLY the component class now:
"""
        
        return prompt
    
    def _build_store_prompt(self, component_name: str, component_description: str, 
                           component_config: Dict[str, Any], class_name: str, blueprint: Dict[str, Any] = None) -> str:
        """Build specialized prompt for Store components using centralized templates"""
        blueprint_context = self._inject_blueprint_context(component_name, blueprint)
        
        # Try to load detailed Store requirements from file
        store_requirements = ""
        try:
            import os
            requirements_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "prompts", "component_generation", "store_requirements.txt"
            )
            if os.path.exists(requirements_path):
                with open(requirements_path, 'r') as f:
                    store_requirements = f.read()
                print(f"✅ Loaded detailed Store requirements from {requirements_path}")
            else:
                # Try centralized loader as fallback
                store_requirements = self.prompt_loader.load_component_requirements("Store")
        except Exception as e:
            print(f"⚠️  Failed to load Store requirements: {e}")
            # Use inline requirements as final fallback
            store_requirements = """
STORE REQUIREMENTS:
- Implement async def process_item(self, item) that routes actions
- Handle actions: add_item, get_item, update_item, delete_item, list_items
- Each action returns: {"status": "success|error", "message": "...", "data": ...}
- Use in-memory storage: self.items = {}
- Generate unique IDs with uuid.uuid4()
- All methods must be async
"""
        
        return f"""You are generating a STORE component class.

{blueprint_context}

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description or f'A Store component for data storage'}
- Configuration: {json.dumps(component_config, indent=2) if component_config else 'Default configuration'}

{store_requirements}

IMPORTANT: Generate ONLY the class implementation. No imports, no comments before the class.
Start directly with: class {class_name}(ComposedComponent):

Generate ONLY the component class now.
"""
    
    def _build_controller_prompt(self, component_name: str, component_description: str,
                                component_config: Dict[str, Any], class_name: str, blueprint: Dict[str, Any] = None) -> str:
        """Build specialized prompt for Controller components with correct parameter mappings"""
        blueprint_context = self._inject_blueprint_context(component_name, blueprint)
        
        # Load controller requirements if available
        controller_requirements = """
CONTROLLER REQUIREMENTS:
- Receive requests from API in format: {"action": "...", "payload": {...}}
- Send to Store with correct action names:
  * API "add_task" → Store "add_item"
  * API "update_task" → Store "update_item" with {"action": "update_item", "item_id": id, "update_data": {...}}
  * API "delete_task" → Store "delete_item" with {"action": "delete_item", "item_id": id}
  * API "get_task" → Store "get_item"
  * API "get_all_tasks" → Store "list_items"
- Extract task_id from payload when needed
- Return structured responses: {"status": "success|error", "message": "...", "result": ...}
"""
        
        try:
            # Try to load from file if available
            import os
            prompts_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "prompts", "component_generation", "controller_requirements.txt"
            )
            if os.path.exists(prompts_path):
                with open(prompts_path, 'r') as f:
                    controller_requirements = f.read()
        except:
            pass  # Use default requirements above
        
        return f"""You are generating a CONTROLLER component class.

{blueprint_context}

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description or 'A Controller component for business logic orchestration'}
- Configuration: {json.dumps(component_config, indent=2) if component_config else 'Default configuration'}

{controller_requirements}

Generate ONLY the component class now.
"""
    
    def _build_sink_prompt(self, component_name: str, component_description: str,
                          component_config: Dict[str, Any], class_name: str, blueprint: Dict[str, Any] = None) -> str:
        """Build specialized prompt for Sink components"""
        blueprint_context = self._inject_blueprint_context(component_name, blueprint)
        return f"""
You are generating a SINK component class.

{blueprint_context}

REQUIREMENTS:
- Class name: {class_name}
- Inherits from: ComposedComponent
- Purpose: Data consumption and processing

IMPLEMENTATION:
- process_item() method for data consumption
- Real data processing logic
- Output handling (file, API, console, etc.)

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description or f'A Sink component for data consumption'}
- Configuration: {json.dumps(component_config, indent=2) if component_config else 'Default configuration'}
"""
    
    def _get_component_specific_requirements(self, component_type: str) -> str:
        """Get component-specific requirements and patterns"""
        if component_type == "Source":
            return """
Source-specific requirements:
- Inherit from ComposedComponent 
- Constructor signature: def __init__(self, name: str, config: Dict[str, Any] = None):
- Call parent constructor: super().__init__(name, config)
- Implement async def process_item(self, item: Any = None) -> Any method
- IGNORE input_data parameter for source components (sources generate data)
- Return ONE data item per call - the framework handles iteration
- Use component configuration to determine data generation behavior

CRITICAL DOCKER NETWORKING CONFIGURATION:
- NEVER use localhost or 127.0.0.1 for inter-service communication
- ALWAYS use Docker service names as hostnames (e.g., "app", "postgres", "kafka")
- Use allocated port from configuration if available, otherwise use internal port numbers (e.g., 8080, 5432, 9092) NOT mapped external ports
- Get connection details from config with Docker-compatible defaults
- Use component-specific service names and appropriate internal ports
- Extract host and port values using config.get with sensible defaults for the service type
- Database components should use database service names and database ports
- Kafka components should use kafka service names and kafka ports
- Web components should use web service names and web ports

HTTP/API SOURCE COMPONENTS MUST:
- Initialize host from config using appropriate service name for this component
- Initialize port from config using appropriate internal port for this service
- Use httpx client for HTTP requests: httpx.AsyncClient()
- Make requests using the configured host and port values
- NEVER use localhost URLs in Docker environment

NETWORKING INITIALIZATION REQUIREMENTS:
- Extract host and port from component configuration
- Use service-specific defaults appropriate for the component type
- Avoid hardcoded values like "app" or generic port numbers
- Use the actual component name or service type for meaningful hostnames
        
    async def process_item(self, item: Any = None) -> Any:
        # Use Docker networking for HTTP requests
        url = f"http://{self.host}:{self.port}/messages"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

- Data should be based on the component description and configuration
- If it's an API source, implement real HTTP calls with httpx using Docker networking
- If it's a data generator, generate meaningful test data
- Use embedded observability: self.logger, self.metrics_collector, self.tracer
"""
        elif component_type == "Transformer":
            return """
Transformer-specific requirements:
- Inherit from ComposedComponent
- Constructor signature: def __init__(self, name: str, config: Dict[str, Any] = None):
- Call parent constructor: super().__init__(name, config)
- Implement async def process_item(self, item: Any) -> Any method
- Transform item based on the component description and configuration
- Return the transformed data
- Preserve input data structure while adding transformations
- Handle edge cases and invalid inputs
- Use embedded observability: self.logger, self.metrics_collector, self.tracer
- Handle errors with self.handle_error()
- Update processed count with self.metrics_collector.increment("items_processed")
"""
        elif component_type == "APIEndpoint":
            return """
APIEndpoint-specific requirements (FastAPI):
- Inherit from ComposedComponent
- Constructor signature: def __init__(self, name: str, config: Dict[str, Any] = None):
- Call parent constructor: super().__init__(name, config)
- CRITICAL: NEVER call anyio.run() or asyncio.run() in __init__ method
- Initialize port and host variables in __init__
- Implement async def process_item(self, item: Any) -> Any method for handling HTTP requests
- Implement proper error handling and validation
- The process_item method should handle HTTP request processing
- Use embedded observability: self.logger, self.metrics_collector, self.tracer
- Handle errors with self.handle_error()
- Update processed count with self.metrics_collector.increment("items_processed")

CRITICAL DOCKER NETWORKING CONFIGURATION FOR API ENDPOINTS:
- Use allocated port from config.get('port') as primary choice, fallback to 8080 if not available
- Listen on 0.0.0.0 to accept connections from other Docker containers
- API endpoints should be accessible via Docker service name
- Database connections must use Docker service names (postgres, mysql, etc.)
- External service calls must use Docker service names when applicable

Implementation Pattern:
- CONFIGURATION: Extract host/port from config, use Docker-compatible defaults
- INITIALIZATION: Set up component state but avoid blocking operations in __init__
- REQUEST PROCESSING: Handle HTTP requests via process_item() method
- RESPONSE FORMAT: Return structured responses with status, data, timestamp
- ERROR HANDLING: Catch exceptions and return error responses
- OBSERVABILITY: Log requests and update metrics for processed items
"""
        elif component_type == "WebSocket":
            return """
WebSocket-specific requirements:
- Inherit from ComposedComponent
- Constructor signature: def __init__(self, name: str, config: Dict[str, Any] = None):
- Call parent constructor: super().__init__(name, config)
- Initialize WebSocket server configuration in __init__:
  - self.port = config.get('port', 8080)  # Use allocated port or fallback to 8080
  - self.max_connections = config.get('max_connections') or 100
  - self.heartbeat_interval = config.get('heartbeat_interval') or 30
  - self._connected_clients = set()
- Implement async def process_item(self, item: Any) -> Any for broadcasting messages
- Include connection handling logic for WebSocket server
- Track connected clients and enforce max_connections limit
- Implement heartbeat mechanism to keep connections alive
- Handle disconnections gracefully without crashing

CRITICAL IMPLEMENTATION DETAILS:
- Use asyncio and websockets library
- Handle JSON serialization for messages
- Clean up clients on disconnect
- Use embedded observability for tracking connections

Implementation Requirements:
- CONNECTION MANAGEMENT: Track connected clients, enforce max_connections limit
- CONNECTION LIFECYCLE: Handle connect/disconnect events with proper cleanup
- MESSAGE HANDLING: Process incoming messages from clients asynchronously  
- BROADCAST CAPABILITY: Send messages to all connected clients via process_item()
- ERROR HANDLING: Handle disconnections gracefully without crashing server
- LOGGING: Track connection events and client count changes
- DATA SERIALIZATION: Convert data to JSON format for transmission
"""
        else:
            return f"""
{component_type}-specific requirements:
- Inherit from ComposedComponent
- Constructor signature: def __init__(self, name: str, config: Dict[str, Any] = None):
- Call parent constructor: super().__init__(name, config)
- Implement async def process_item(self, item: Any) -> Any method
- Use embedded observability: self.logger, self.metrics_collector, self.tracer
- Handle errors with self.handle_error()
- Update processed count with self.metrics_collector.increment("items_processed")
"""
    
    def enhance_component_prompt(self, component_type: str, component_name: str) -> str:
        """Enhanced prompt to prevent placeholder generation"""
        return f"""
CRITICAL: Generate complete, functional code with NO placeholders.

FORBIDDEN PATTERNS:
- TODO comments
- placeholder values like "your_database_url"
- NotImplementedError exceptions
- pass statements in functional methods
- Generic return statements like "return {{{{}}}}"

REQUIRED IMPLEMENTATION:
- All methods must have functional implementations
- Use realistic default values, not placeholders
- Include proper error handling
- Implement actual business logic

Component Type: {component_type}
Component Name: {component_name}

Generate production-ready code that passes validation.
"""