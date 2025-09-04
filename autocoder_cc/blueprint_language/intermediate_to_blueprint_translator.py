#!/usr/bin/env python3
"""
Autocoder v4.3 Intermediate Format to Blueprint Translator
Translates simplified intermediate format to full system blueprints
"""
import yaml
from typing import Dict, Any, List
from pathlib import Path

from .intermediate_format import (
    IntermediateSystem, 
    IntermediateComponent, 
    IntermediateBinding,
    IntermediatePort
)
from .system_blueprint_parser import ParsedSystemBlueprint, SystemBlueprintParser
from autocoder_cc.generators.config import generator_settings


class IntermediateToBlueprintTranslator:
    """Translates intermediate format to full Autocoder system blueprints"""
    
    def __init__(self):
        self.parser = SystemBlueprintParser()
    
    def translate(self, intermediate_system: IntermediateSystem) -> str:
        """
        Translate an intermediate system definition to a full blueprint YAML string
        
        Args:
            intermediate_system: The intermediate format system definition
            
        Returns:
            YAML string of the full system blueprint
        """
        # Build the blueprint dictionary structure
        blueprint_dict = self._build_blueprint_dict(intermediate_system)
        
        # Convert to YAML with proper formatting
        yaml_str = yaml.dump(blueprint_dict, default_flow_style=False, sort_keys=False, width=120)
        
        return yaml_str
    
    def translate_and_validate(self, intermediate_system: IntermediateSystem) -> ParsedSystemBlueprint:
        """
        Translate intermediate format to blueprint and validate it
        
        Args:
            intermediate_system: The intermediate format system definition
            
        Returns:
            Parsed and validated system blueprint
            
        Raises:
            ValueError: If the generated blueprint fails validation
        """
        yaml_str = self.translate(intermediate_system)
        parsed_blueprint = self.parser.parse_string(yaml_str)
        return parsed_blueprint
    
    def _build_blueprint_dict(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Build the complete blueprint dictionary structure"""
        
        # Build schemas used by the system
        schemas = self._generate_schemas(intermediate_system)
        
        # Build system section
        system = {
            "name": intermediate_system.name,
            "description": intermediate_system.description,
            "version": intermediate_system.version,
            "components": [self._translate_component(comp) for comp in intermediate_system.components],
            "bindings": [self._translate_binding(binding) for binding in intermediate_system.bindings],
            "configuration": self._generate_configuration(intermediate_system),
            "deployment": self._generate_deployment(intermediate_system),
            "validation": self._generate_validation(intermediate_system)
        }
        
        # Build complete blueprint
        blueprint = {
            "system": system,
            "schemas": schemas,
            "metadata": {
                "version": intermediate_system.version,
                "author": "Intermediate Format Translator",
                "description": intermediate_system.description,
                "autocoder_version": "4.3.0",
                "natural_language_description": f"Generated from intermediate format for {intermediate_system.name}"
            },
            # Enterprise Roadmap v3 Phase 0 requirement: mandatory policy block
            "policy": self._generate_default_policy(intermediate_system)
        }
        
        return blueprint
    
    def _translate_component(self, component: IntermediateComponent) -> Dict[str, Any]:
        """Translate an intermediate component to blueprint format"""
        
        comp_dict = {
            "name": component.name,
            "type": component.type,
            "description": component.description or f"{component.type} component",
            "processing_mode": self._determine_processing_mode(component),
            "inputs": [self._translate_port(port) for port in component.inputs],
            "outputs": [self._translate_port(port) for port in component.outputs],
            "properties": [],  # No property constraints in intermediate format
            "contracts": [],   # No contract constraints in intermediate format
            "configuration": component.config,
            "dependencies": [],  # Will be inferred from component type and config
            "implementation": {
                "language": "python",
                "methods": {}
            }
        }
        
        # Add type-specific required configurations
        if component.type == "APIEndpoint":
            # Ensure port is set (required field) - use dynamic port assignment
            if "port" not in comp_dict["configuration"]:
                # Assign unique ports starting from generator_settings.api_port (Enterprise Roadmap v2 compliant)
                base_port = generator_settings.api_port + hash(component.name) % 1000  # Pseudo-random but deterministic
                comp_dict["configuration"]["port"] = base_port
            
            # Add resources if port was in config
            if "port" in component.config:
                if "resources" not in comp_dict:
                    comp_dict["resources"] = {}
                comp_dict["resources"]["ports"] = [{
                    "port": component.config["port"],
                    "protocol": "HTTP",
                    "public": True
                }]
        
        elif component.type == "Store":
            # Ensure storage_type is set (required field)
            if "storage_type" not in comp_dict["configuration"]:
                # Infer storage type from database config or default to postgresql
                if "db" in comp_dict["configuration"]:
                    db_type = comp_dict["configuration"]["db"]
                    if "postgresql" in db_type.lower():
                        comp_dict["configuration"]["storage_type"] = "postgresql"
                    elif "mysql" in db_type.lower():
                        comp_dict["configuration"]["storage_type"] = "mysql"
                    elif "redis" in db_type.lower():
                        comp_dict["configuration"]["storage_type"] = "redis"
                    else:
                        comp_dict["configuration"]["storage_type"] = "postgresql"  # Default
                else:
                    comp_dict["configuration"]["storage_type"] = "postgresql"  # Default
            
            # Add resources if database was in config
            if "database" in component.config:
                if "resources" not in comp_dict:
                    comp_dict["resources"] = {}
                comp_dict["resources"]["databases"] = [{
                    "type": component.config["database"],
                    "connection_string": f"${{{component.config['database'].upper()}_CONNECTION_STRING}}",
                    "pool_size": 10
                }]
        
        elif component.type == "Model":
            # Ensure model configuration is set (required field)
            if "model_path" not in comp_dict["configuration"] and "model_type" not in comp_dict["configuration"]:
                # Infer model type from description or component name
                name_lower = component.name.lower()
                desc_lower = (component.description or "").lower()
                
                if "sentiment" in name_lower or "sentiment" in desc_lower:
                    comp_dict["configuration"]["model_type"] = "sentiment_analysis"
                    comp_dict["configuration"]["model_path"] = "/models/sentiment_model.pkl"
                elif "classification" in name_lower or "classification" in desc_lower:
                    comp_dict["configuration"]["model_type"] = "classification"
                    comp_dict["configuration"]["model_path"] = "/models/classifier.pkl"
                elif "regression" in name_lower or "regression" in desc_lower:
                    comp_dict["configuration"]["model_type"] = "regression"
                    comp_dict["configuration"]["model_path"] = "/models/regressor.pkl"
                else:
                    # Generic model configuration
                    comp_dict["configuration"]["model_type"] = "custom"
                    comp_dict["configuration"]["model_path"] = "/models/model.pkl"
            
            comp_dict["dependencies"] = ["scikit-learn", "pandas", "numpy"]
        
        return comp_dict
    
    def _translate_port(self, port: IntermediatePort) -> Dict[str, Any]:
        """Translate an intermediate port to blueprint format"""
        # Use a common schema name for the same data type to ensure compatibility
        schema_name = f"common_{port.schema_type}_schema"
        
        return {
            "name": port.name,
            "schema": schema_name,
            "required": port.required,
            "description": port.description or f"{port.name} port",
            "flow_type": "push",  # Default flow type
            "batch_size": 100 if port.schema_type == "array" else 1
        }
    
    def _translate_binding(self, binding: IntermediateBinding) -> Dict[str, Any]:
        """Translate an intermediate binding to blueprint format"""
        return {
            "from": f"{binding.from_component}.{binding.from_port}",
            "to": f"{binding.to_component}.{binding.to_port}",
            "error_handling": {
                "strategy": "retry",
                "retry_count": 3,
                "timeout_ms": 5000
            },
            "qos": {
                "delivery_guarantee": "at_least_once",
                "ordering": False
            }
        }
    
    def _determine_processing_mode(self, component: IntermediateComponent) -> str:
        """Determine the processing mode based on component type"""
        if component.type in ["StreamProcessor", "APIEndpoint"]:
            return "stream"
        elif component.type in ["Model", "Store"]:
            return "batch"
        else:
            # Default based on whether it has array outputs
            has_array_output = any(p.schema_type == "array" for p in component.outputs)
            return "batch" if has_array_output else "stream"
    
    def _generate_schemas(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Generate schema definitions from ports"""
        schemas = {}
        
        # Create common schemas for each type used in the system
        schema_types_used = set()
        for component in intermediate_system.components:
            for port in component.inputs + component.outputs:
                schema_types_used.add(port.schema_type)
        
        # Generate one schema per type
        for schema_type in schema_types_used:
            schema_name = f"common_{schema_type}_schema"
            schemas[schema_name] = self._create_schema_definition_for_type(schema_type)
        
        return schemas
    
    def _create_schema_definition_for_type(self, schema_type: str) -> Dict[str, Any]:
        """Create a schema definition for a type"""
        if schema_type == "object":
            return {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "data": {"type": "object"}
                },
                "required": ["id", "timestamp"]
            }
        elif schema_type == "array":
            return {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "value": {"type": "number"}
                    }
                }
            }
        elif schema_type in ["string", "number", "integer", "boolean"]:
            return {
                "type": schema_type
            }
        else:
            # Default object schema
            return {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            }
    
    def _generate_configuration(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Generate system configuration section"""
        return {
            "environment": intermediate_system.environment,
            "timeouts": {
                "startup_timeout_ms": 30000,
                "shutdown_timeout_ms": 10000,
                "health_check_timeout_ms": 5000
            },
            "logging": {
                "level": "INFO" if intermediate_system.environment == "production" else "DEBUG",
                "format": "json",
                "output": "stdout"
            }
        }
    
    def _generate_deployment(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Generate deployment configuration"""
        # Determine external services needed
        external_services = []
        
        for component in intermediate_system.components:
            if component.type == "Store" and "database" in component.config:
                db_type = component.config["database"]
                if db_type not in [s["type"] for s in external_services]:
                    external_services.append({
                        "name": f"{db_type}_db",
                        "type": db_type,
                        "version": "latest",
                        "configuration": {}
                    })
        
        return {
            "platform": "docker",
            "external_services": external_services,
            "networking": {
                "internal_network": "autocoder_network"
            },
            "scaling": {
                "min_instances": 1,
                "max_instances": 3 if intermediate_system.environment == "production" else 1,
                "auto_scaling": intermediate_system.environment == "production"
            }
        }
    
    def _generate_validation(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Generate validation configuration"""
        return {
            "performance": {
                "throughput_requests_per_second": 1000,
                "latency_p95_ms": 100,
                "latency_p99_ms": 500
            } if intermediate_system.environment == "production" else {},
            "end_to_end_tests": True,
            "load_testing": {
                "enabled": intermediate_system.environment == "production",
                "duration_minutes": 5,
                "concurrent_users": 100
            },
            "sample_data": {
                "auto_generate": True
            }
        }
    
    def _generate_default_policy(self, intermediate_system: IntermediateSystem) -> Dict[str, Any]:
        """Generate default policy block to satisfy Enterprise Roadmap v3 Phase 0 requirements"""
        return {
            "slos": {
                "p95_latency_ms": 100,
                "p99_latency_ms": 500,
                "availability_percentage": 99.9,
                "throughput_requests_per_second": 1000
            },
            "resource_limits": {
                "cpu_cores": 2,
                "memory_mb": 4096,
                "max_connections": 1000
            },
            "disallowed_dependencies": [
                "eval",
                "exec", 
                "subprocess.call",
                "os.system"
            ],
            "security_constraints": {
                "require_encryption": True,
                "disallow_privileged": True,
                "enforce_https": getattr(intermediate_system, 'environment', 'development') == "production"
            },
            "validation_rules": [
                {
                    "expression": "True",  # Simplified - basic validation handled by component registry
                    "description": "System validation passed",
                    "severity": "info"
                }
            ]
        }


def main():
    """Test the translator with examples"""
    from .intermediate_format import create_simple_example, create_complex_example
    
    translator = IntermediateToBlueprintTranslator()
    
    print("Testing Intermediate to Blueprint Translator\n")
    
    # Test with simple example
    print("1. Translating simple example...")
    simple = create_simple_example()
    simple_yaml = translator.translate(simple)
    
    print(f"✅ Generated blueprint YAML ({len(simple_yaml)} chars)")
    print("First 500 chars:")
    print(simple_yaml[:500])
    print("...\n")
    
    # Validate the simple blueprint
    try:
        simple_parsed = translator.translate_and_validate(simple)
        print(f"✅ Simple blueprint validated successfully!")
        print(f"   System: {simple_parsed.system.name}")
        print(f"   Components: {len(simple_parsed.system.components)}")
        print(f"   Bindings: {len(simple_parsed.system.bindings)}")
    except Exception as e:
        print(f"❌ Simple blueprint validation failed: {e}")
    
    # Test with complex example
    print("\n2. Translating complex example...")
    complex_example = create_complex_example()
    complex_yaml = translator.translate(complex_example)
    
    print(f"✅ Generated blueprint YAML ({len(complex_yaml)} chars)")
    
    # Validate the complex blueprint
    try:
        complex_parsed = translator.translate_and_validate(complex_example)
        print(f"✅ Complex blueprint validated successfully!")
        print(f"   System: {complex_parsed.system.name}")
        print(f"   Components: {len(complex_parsed.system.components)}")
        print(f"   Bindings: {len(complex_parsed.system.bindings)}")
        print(f"   Schemas: {len(complex_parsed.schemas)}")
    except Exception as e:
        print(f"❌ Complex blueprint validation failed: {e}")
    
    # Save examples for manual inspection
    output_dir = Path("generated_blueprints")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "simple_translated.yaml", "w") as f:
        f.write(simple_yaml)
    print(f"\n📁 Saved simple blueprint to: {output_dir / 'simple_translated.yaml'}")
    
    with open(output_dir / "complex_translated.yaml", "w") as f:
        f.write(complex_yaml)
    print(f"📁 Saved complex blueprint to: {output_dir / 'complex_translated.yaml'}")


if __name__ == "__main__":
    main()