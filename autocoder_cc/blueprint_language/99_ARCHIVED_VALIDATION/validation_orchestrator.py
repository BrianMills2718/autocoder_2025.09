#!/usr/bin/env python3
"""
Validation Orchestrator - Emergency Refactoring from system_generator.py

Extracted from system_generator.py:
- validate_generated_system (lines 2409-2463)
- _are_schemas_compatible (lines 2465-2485)
- _validate_pre_generation (lines 2487-2699)

Validation coordination and compatibility checking.
"""

from typing import List
from pathlib import Path

from ..system_blueprint_parser import ParsedSystemBlueprint
from autocoder_cc.components.component_registry import component_registry


class ValidationOrchestrator:
    """Orchestrates validation of generated systems and pre-generation validation"""
    
    def __init__(self):
        pass
    
    def validate_generated_system(self, generated_system) -> List[str]:
        """Validate that the generated system is correct and complete"""
        
        validation_errors = []
        system_dir = generated_system.output_directory
        
        # Check required files exist
        required_files = [
            "main.py",
            "config/system_config.yaml", 
            "requirements.txt",
            "components/__init__.py"
        ]
        
        # Add test files if any tests were generated
        if generated_system.tests:
            required_files.append("tests/conftest.py")
            for test in generated_system.tests:
                required_files.append(test.test_file_path)
        
        for file_path in required_files:
            full_path = system_dir / file_path
            if not full_path.exists():
                validation_errors.append(f"Missing required file: {file_path}")
        
        # Check component files exist
        for comp in generated_system.components:
            comp_file = system_dir / "components" / f"{comp.name}.py"
            if not comp_file.exists():
                validation_errors.append(f"Missing component file: components/{comp.name}.py")
        
        # Check that autocoder dependency is properly configured
        requirements_file = system_dir / "requirements.txt"
        if requirements_file.exists():
            requirements_content = requirements_file.read_text()
            if "autocoder" not in requirements_content:
                validation_errors.append("Missing autocoder dependency in requirements.txt")
        else:
            validation_errors.append("Missing requirements.txt file")
        
        # Check that setup.py exists for proper packaging
        setup_py_file = system_dir / "setup.py"
        if not setup_py_file.exists():
            validation_errors.append("Missing setup.py for proper Python packaging")
        
        # Basic syntax check on main.py
        try:
            main_py_content = (system_dir / "main.py").read_text()
            compile(main_py_content, "main.py", "exec")
        except SyntaxError as e:
            validation_errors.append(f"Syntax error in main.py: {e}")
        except Exception as e:
            validation_errors.append(f"Error reading main.py: {e}")
        
        return validation_errors
    
    def _are_schemas_compatible(self, from_schema: str, to_schema: str) -> bool:
        """Check if two schemas are compatible for binding connections"""
        # Exact match is always compatible
        if from_schema == to_schema:
            return True
        
        # Compatible conversions based on AutoCoder architecture
        compatible_pairs = [
            ('common_string_schema', 'common_object_schema'),  # string can be wrapped in object
            ('string', 'object'),  # string can be wrapped in object  
            ('array', 'object'),   # array can be wrapped in object
            ('object', 'array'),   # object can be placed in array
            ('number', 'object'),  # number can be wrapped in object
            ('integer', 'number'), # integer is a number
            ('boolean', 'object'), # boolean can be wrapped in object
            ('common_number_schema', 'common_object_schema'),  # number to object
            ('common_boolean_schema', 'common_object_schema'), # boolean to object
            ('common_array_schema', 'common_object_schema'),   # array to object
        ]
        
        return (from_schema, to_schema) in compatible_pairs

    def _validate_pre_generation(self, system_blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Validate blueprint using ComponentRegistry with multi-stage validation lifecycle.
        
        Enterprise Roadmap v3 Phase 0: Registry-driven validation with fail-hard enforcement.
        """
        validation_errors = []
        system = system_blueprint.system
        
        # PHASE 0: ComponentRegistry validation - fail hard on registry issues
        try:
            # Convert ParsedSystemBlueprint to dict for registry validation
            blueprint_dict = {
                'system': {
                    'name': system.name,
                    'components': [
                        {
                            'name': comp.name,
                            'type': comp.type,
                            'config': comp.config or {}
                        }
                        for comp in system.components
                    ],
                    'bindings': [
                        {
                            'from_component': binding.from_component,
                            'from_port': binding.from_port,
                            'to_components': binding.to_components,
                            'to_ports': binding.to_ports
                        }
                        for binding in system.bindings
                    ]
                },
                'policy': system_blueprint.policy
            }
            
            # Validate all components can be created via registry
            for component_config in blueprint_dict['system']['components']:
                try:
                    # Validate component type is registered
                    component_type = component_config['type']
                    if not component_registry._component_classes.get(component_type):
                        validation_errors.append(
                            f"Component type '{component_type}' not registered in ComponentRegistry. "
                            f"Available types: {list(component_registry._component_classes.keys())}"
                        )
                        continue
                    
                    # Stage 1: Implementation Validation
                    # Stage 2: Configuration Validation  
                    component_registry._validate_component_config(component_type, component_config['config'])
                    
                    # Stage 3: Dependency Validation (lightweight check)
                    component_registry._validate_external_dependencies(
                        component_config['name'], 
                        component_config['config']
                    )
                    
                except Exception as e:
                    validation_errors.append(f"ComponentRegistry validation failed for '{component_config['name']}': {e}")
            
            # System-level policy validation
            if hasattr(component_registry, 'validate_system_against_blueprint_policy'):
                try:
                    component_registry.validate_system_against_blueprint_policy(blueprint_dict)
                except Exception as e:
                    validation_errors.append(f"System policy validation failed: {e}")
                    
        except Exception as e:
            validation_errors.append(f"ComponentRegistry pre-generation validation failed: {e}")
        
        # 1. Check for dangling components (components with no connections)
        connected_components = set()
        
        # Find components referenced in bindings
        for binding in system.bindings:
            connected_components.add(binding.from_component)
            connected_components.update(binding.to_components)
        
        # Check for components that have inputs/outputs but aren't connected
        for comp in system.components:
            # Sources and Sinks are allowed to be "dangling" - they're endpoints
            # Store components are terminal components like Sinks - they receive data but don't output it
            if comp.type in ['Source', 'Sink', 'EventSource', 'Store']:
                continue
            
            # APIEndpoints are also allowed to be unconnected (external interface)
            if comp.type == 'APIEndpoint':
                continue
            
            # Controllers can be unconnected if they provide services (like auth/authorization)
            if comp.type == 'Controller':
                continue
                
            # Other components should be connected if they have inputs/outputs
            if comp.name not in connected_components:
                if comp.inputs or comp.outputs:
                    validation_errors.append(
                        f"Component '{comp.name}' has inputs/outputs but is not connected to any other components"
                    )
        
        # 2. Check for circular dependencies in bindings
        def has_circular_dependency(bindings):
            # Build adjacency list
            graph = {}
            for binding in bindings:
                if binding.from_component not in graph:
                    graph[binding.from_component] = []
                graph[binding.from_component].extend(binding.to_components)
            
            # Check for cycles using DFS
            visited = set()
            rec_stack = set()
            
            def dfs(node):
                if node in rec_stack:
                    return True  # Cycle detected
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if dfs(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            for node in graph:
                if node not in visited:
                    if dfs(node):
                        return True
            return False
        
        # Note: Circular dependencies are allowed in V5.2 stream-based architecture
        # Components communicate via queues and the SystemExecutionHarness manages cycles
        # Commenting out this validation as it incorrectly blocks valid stream architectures
        # if has_circular_dependency(system.bindings):
        #     validation_errors.append(
        #         "Circular dependency detected in component bindings - this would create infinite loops"
        #     )
        
        # 3. Check for missing critical configurations
        for comp in system.components:
            # Store components should have database type specified (Phase 2C: Updated validation)
            if comp.type == 'Store':
                component_config = comp.config or {}
                # Check for any valid database configuration format
                has_db_config = (
                    component_config.get('storage_type') or  # Legacy format
                    component_config.get('database_type') or  # Current format
                    (isinstance(component_config.get('_database'), dict) and 
                     component_config.get('_database', {}).get('type'))  # V5.0+ format
                )
                if not has_db_config:
                    validation_errors.append(
                        f"Store component '{comp.name}' missing database configuration. "
                        f"Provide one of: 'database_type', 'storage_type', or '_database.type'"
                    )
            
            # APIEndpoint components should have port specified
            elif comp.type == 'APIEndpoint':
                if not comp.config.get('port'):
                    validation_errors.append(
                        f"APIEndpoint component '{comp.name}' missing required 'port' configuration"
                    )
            
            # Model components should have model-related configuration
            elif comp.type == 'Model':
                model_configs = ['model_path', 'model_type', 'inference_type']
                if not any(comp.config.get(config) for config in model_configs):
                    validation_errors.append(
                        f"Model component '{comp.name}' missing model configuration (model_path, model_type, or inference_type)"
                    )
        
        # 4. Check for incompatible component type combinations
        component_types = [comp.type for comp in system.components]
        
        # Systems with Models should have at least one Source or APIEndpoint for input
        if 'Model' in component_types:
            input_types = ['Source', 'APIEndpoint', 'EventSource']
            if not any(comp_type in component_types for comp_type in input_types):
                validation_errors.append(
                    "System contains Model components but no input components (Source, APIEndpoint, EventSource)"
                )
        
        # 5. Check for resource conflicts
        api_ports = []
        for comp in system.components:
            if comp.type == 'APIEndpoint':
                port = comp.config.get('port')
                if port:
                    if port in api_ports:
                        validation_errors.append(
                            f"Port conflict: Multiple APIEndpoint components using port {port}"
                        )
                    api_ports.append(port)
        
        # 6. Check for schema mismatches in bindings (if schemas are defined)
        if system_blueprint.schemas:
            for binding in system.bindings:
                # Find source component output schema
                from_comp = next((c for c in system.components if c.name == binding.from_component), None)
                if from_comp:
                    from_output = next((o for o in from_comp.outputs if o.name == binding.from_port), None)
                    if from_output:
                        from_schema = from_output.schema
                        
                        # Check each target component input schema
                        for i, to_component in enumerate(binding.to_components):
                            to_comp = next((c for c in system.components if c.name == to_component), None)
                            if to_comp and i < len(binding.to_ports):
                                to_input = next((inp for inp in to_comp.inputs if inp.name == binding.to_ports[i]), None)
                                if to_input and not self._are_schemas_compatible(from_schema, to_input.schema):
                                    validation_errors.append(
                                        f"Schema mismatch in binding: {binding.from_component}.{binding.from_port} "
                                        f"({from_schema}) -> {to_component}.{binding.to_ports[i]} ({to_input.schema})"
                                    )
        
        return validation_errors